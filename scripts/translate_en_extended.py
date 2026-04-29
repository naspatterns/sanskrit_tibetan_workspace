"""P1-2 batch translator — extend Korean coverage to top-50K English-source.

Phase 2b filled top-10K (data/translations.jsonl, 9,995 entries).
Phase 3.7 P1-2 extends to top-10K..top-50K range using the same chunked
+ resume + rate-limit-graceful pattern as translate_eu.py.

Selection rules (mirrors translate_batch.py.collect_candidates but using
top50k.txt and skipping top10k overlap):
  - target_lang == "en" sources only
  - exclude_from_search dicts skipped
  - role in (equivalents, thesaurus) skipped
  - first matching entry per headword_norm in priority-ASC order wins
  - entries with non-empty body.ko already are skipped (covered)
  - entries already in data/translations.jsonl are skipped (Phase 2b
    covered top-10K canonical picks)

Cost: ~40K entries × avg ~150 chars input + 150 tokens output. Sonnet 4.5
batch (50% off): ~$30-40 estimated. Tracked in audit-A-summary.md as P1-2.

Usage (mirrors translate_eu.py):
    uv run python -m scripts.translate_en_extended prepare
    uv run python -m scripts.translate_en_extended submit
    uv run python -m scripts.translate_en_extended poll --wait
    uv run python -m scripts.translate_en_extended retrieve

Resume: rate-limit / spending-limit triggers exit code 2 + state save;
re-run any subcommand to continue from current position.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from scripts.lib.io import iter_jsonl, iter_slugs_by_priority, load_top10k


DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_WAIT = 24 * 60 * 60
CHUNK_SIZE = 100_000

SYSTEM_PROMPT = """You are an expert Sanskrit-English-Korean translator specializing in
academic dictionary definitions. Translate the following English dictionary
entry into concise, scholarly Korean. Preserve:
- All Sanskrit words in IAST (do not transliterate to Hangul)
- Grammatical abbreviations (m., f., n., cf., etc.)
- Citation references and abbreviations
- Numbered sense structure (1., 2., etc.)

Output: Korean translation only. No preamble, no commentary. Keep length
roughly proportional to input."""

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT_DIR = ROOT / "data" / "translations" / "en-extended"
DEFAULT_FINAL = ROOT / "data" / "translations-en-extended.jsonl"
DEFAULT_TOP10K = ROOT / "data" / "reports" / "top10k.txt"
DEFAULT_TOP50K = ROOT / "data" / "reports" / "top50k.txt"
DEFAULT_PHASE2_TRANSLATIONS = ROOT / "data" / "translations.jsonl"


def collect_candidates(
    sources: Path,
    jsonl_dir: Path,
    top10k: list[str],
    top50k: list[str],
    already_translated: set[str],
) -> list[dict]:
    """Pick top-50K-but-not-top-10K English-source entries that need ko."""
    extended_set = set(top50k) - set(top10k)  # 40K headwords
    selected_by_hw: dict[str, dict] = {}

    for _slug_dir, meta in iter_slugs_by_priority(sources):
        if meta.get("exclude_from_search"):
            continue
        if meta.get("target_lang") != "en":
            continue
        if meta.get("role") in ("equivalents", "thesaurus"):
            continue
        path = jsonl_dir / f"{meta['slug']}.jsonl"
        if not path.exists():
            continue

        for entry in iter_jsonl(path):
            hw = entry.get("headword_norm")
            if hw not in extended_set or hw in selected_by_hw:
                continue
            entry_id = entry["id"]
            if entry_id in already_translated:
                # Skip ids that Phase 2b already covered (rare overlap).
                continue
            plain = (entry.get("body") or {}).get("plain", "").strip()
            if not plain or len(plain) < 10:
                continue
            ko = (entry.get("body") or {}).get("ko", "").strip()
            if ko:
                selected_by_hw[hw] = {"__done__": True}
                continue
            selected_by_hw[hw] = {
                "custom_id": entry_id,
                "headword_iast": entry.get("headword_iast", entry.get("headword", "?")),
                "plain": plain[:4000],
            }

    return [c for c in selected_by_hw.values() if "__done__" not in c]


def build_request(c: dict, model: str) -> dict:
    return {
        "custom_id": c["custom_id"],
        "params": {
            "model": model,
            "max_tokens": 1024,
            "system": SYSTEM_PROMPT,
            "messages": [
                {
                    "role": "user",
                    "content": f"Headword: {c['headword_iast']}\n\nEntry:\n{c['plain']}",
                }
            ],
        },
    }


def load_state(state_path: Path) -> dict:
    if state_path.exists():
        return json.loads(state_path.read_text(encoding="utf-8"))
    return {"chunks": []}


def save_state(state_path: Path, state: dict) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = state_path.with_suffix(state_path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(state_path)


def require_client():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set. export it first.", file=sys.stderr)
        sys.exit(1)
    import anthropic
    return anthropic.Anthropic()


def is_limit_error(e: Exception) -> bool:
    name = type(e).__name__
    if name in ("RateLimitError", "PermissionDeniedError"):
        return True
    code = getattr(e, "status_code", None)
    if code in (429, 403):
        return True
    msg = str(e).lower()
    return any(kw in msg for kw in ("rate limit", "quota", "spending limit", "credit", "budget"))


def already_translated_ids(path: Path) -> set[str]:
    out: set[str] = set()
    if not path.exists():
        return out
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            eid = obj.get("entry_id") or obj.get("custom_id")
            if eid:
                out.add(eid)
    return out


def cmd_prepare(args) -> int:
    top10k = load_top10k(args.top10k)
    if not args.top50k.exists():
        print(f"ERROR: {args.top50k} missing. Run:\n  "
              f"uv run python -m scripts.frequency --top-n 50000 "
              f"--out-top {args.top50k}", file=sys.stderr)
        return 1
    top50k = load_top10k(args.top50k)

    phase2 = already_translated_ids(args.phase2)
    print(f"Phase 2b already translated ids: {len(phase2):,}", file=sys.stderr)

    candidates = collect_candidates(args.sources, args.jsonl, top10k, top50k, phase2)
    print(f"Collected {len(candidates):,} en-extended candidates", file=sys.stderr)
    if not candidates:
        print("Nothing to do.", file=sys.stderr)
        return 0

    args.out_dir.mkdir(parents=True, exist_ok=True)

    chunks_meta = []
    for chunk_n, start in enumerate(range(0, len(candidates), CHUNK_SIZE), start=1):
        chunk = candidates[start : start + CHUNK_SIZE]
        chunk_path = args.out_dir / f"requests-chunk-{chunk_n:04d}.jsonl"
        with chunk_path.open("w", encoding="utf-8") as f:
            for c in chunk:
                f.write(json.dumps(build_request(c, args.model), ensure_ascii=False))
                f.write("\n")
        chunks_meta.append({
            "n": chunk_n,
            "path": str(chunk_path.relative_to(ROOT)),
            "count": len(chunk),
            "status": "prepared",
        })
        print(f"  chunk {chunk_n}: {len(chunk):,} requests → {chunk_path.name}",
              file=sys.stderr)

    total_in_tok = sum(len(c["plain"]) for c in candidates) / 3.5
    cost_full = (total_in_tok / 1_000_000) * 3.0 + (len(candidates) * 150 / 1_000_000) * 15.0
    cost_batch = cost_full * 0.5

    state = {
        "mode": "en-extended",
        "model": args.model,
        "total_candidates": len(candidates),
        "estimated_cost_usd": round(cost_batch, 2),
        "chunk_size": CHUNK_SIZE,
        "chunks": chunks_meta,
    }
    save_state(args.state, state)

    print(f"\n✓ {len(chunks_meta)} chunk(s) prepared", file=sys.stderr)
    print(f"  total candidates: {len(candidates):,}", file=sys.stderr)
    print(f"  state file: {args.state}", file=sys.stderr)
    print(f"  estimated batch cost: ~${cost_batch:.2f}", file=sys.stderr)
    print(f"\nNext: uv run python -m scripts.translate_en_extended submit", file=sys.stderr)
    return 0


def cmd_submit(args) -> int:
    state = load_state(args.state)
    if not state.get("chunks"):
        print(f"ERROR: no chunks in {args.state}. Run `prepare` first.", file=sys.stderr)
        return 1
    pending = [c for c in state["chunks"] if c["status"] == "prepared"]
    if not pending:
        print(f"All {len(state['chunks'])} chunks already submitted.", file=sys.stderr)
        return 0

    print(f"Submitting {len(pending)} pending chunks…", file=sys.stderr)
    client = require_client()

    submitted = 0
    for chunk in state["chunks"]:
        if chunk["status"] != "prepared":
            continue
        chunk_path = ROOT / chunk["path"]
        if not chunk_path.exists():
            chunk["status"] = "failed"
            chunk["error"] = "request file missing"
            save_state(args.state, state)
            continue
        with chunk_path.open(encoding="utf-8") as f:
            requests = [json.loads(line) for line in f if line.strip()]

        try:
            print(f"  chunk {chunk['n']}: submitting {len(requests):,} requests…",
                  file=sys.stderr)
            batch = client.messages.batches.create(requests=requests)
            chunk["batch_id"] = batch.id
            chunk["status"] = "submitted"
            chunk["submitted_at"] = int(time.time())
            save_state(args.state, state)
            submitted += 1
            print(f"    → batch_id={batch.id}", file=sys.stderr)
        except Exception as e:
            if is_limit_error(e):
                print(f"\n⚠️  Limit hit on chunk {chunk['n']}: {type(e).__name__}: {e}",
                      file=sys.stderr)
                print(f"   {submitted} submitted. Re-run after limit refresh.",
                      file=sys.stderr)
                save_state(args.state, state)
                return 2
            else:
                chunk["status"] = "failed"
                chunk["error"] = str(e)
                save_state(args.state, state)
                return 1

    print(f"\n✓ {submitted} submitted this run.", file=sys.stderr)
    return 0


def cmd_poll(args) -> int:
    state = load_state(args.state)
    submitted_chunks = [c for c in state["chunks"] if c["status"] == "submitted"]
    if not submitted_chunks:
        print("No chunks in 'submitted' state.", file=sys.stderr)
        return 0
    client = require_client()
    deadline = time.time() + args.max_wait_seconds if args.wait else 0

    while True:
        any_pending = False
        for chunk in state["chunks"]:
            if chunk["status"] != "submitted":
                continue
            try:
                batch = client.messages.batches.retrieve(chunk["batch_id"])
            except Exception as e:
                if is_limit_error(e):
                    save_state(args.state, state)
                    return 2
                continue
            print(f"  chunk {chunk['n']} ({chunk['batch_id']}): {batch.processing_status}",
                  file=sys.stderr)
            if batch.processing_status == "ended":
                chunk["status"] = "ended"
                chunk["ended_at"] = int(time.time())
                save_state(args.state, state)
            elif batch.processing_status in ("in_progress", "canceling"):
                any_pending = True

        if not any_pending or not args.wait:
            break
        if time.time() >= deadline:
            return 1
        time.sleep(args.poll_interval)
    return 0


def cmd_retrieve(args) -> int:
    state = load_state(args.state)
    ended = [c for c in state["chunks"] if c["status"] == "ended"]
    if not ended:
        print("No 'ended' chunks. Run poll first.", file=sys.stderr)
        return 0
    client = require_client()
    args.final.parent.mkdir(parents=True, exist_ok=True)
    seen = set()
    if args.final.exists():
        with args.final.open(encoding="utf-8") as f:
            for line in f:
                try: seen.add(json.loads(line)["entry_id"])
                except Exception: pass
    new_count = 0
    failures_path = args.final.with_suffix(".failures.jsonl")
    failures_count = 0
    for chunk in state["chunks"]:
        if chunk["status"] != "ended":
            continue
        try:
            results = client.messages.batches.results(chunk["batch_id"])
        except Exception as e:
            if is_limit_error(e):
                save_state(args.state, state)
                return 2
            continue
        with args.final.open("a", encoding="utf-8") as out_f, failures_path.open("a", encoding="utf-8") as err_f:
            for result in results:
                cid = result.custom_id
                if cid in seen:
                    continue
                if result.result.type == "succeeded":
                    msg = result.result.message
                    ko = "".join(b.text for b in msg.content if b.type == "text").strip()
                    out_f.write(json.dumps({"entry_id": cid, "ko": ko}, ensure_ascii=False) + "\n")
                    seen.add(cid)
                    new_count += 1
                else:
                    err_f.write(json.dumps({"custom_id": cid, "type": result.result.type}, ensure_ascii=False) + "\n")
                    failures_count += 1
        chunk["status"] = "retrieved"
        save_state(args.state, state)
    print(f"\n✓ Retrieved {new_count:,} translations into {args.final}", file=sys.stderr)
    if failures_count:
        print(f"  {failures_count} failures → {failures_path}", file=sys.stderr)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="EN-source extended (top-50K) batch translator")
    parser.add_argument("--sources", type=Path, default=ROOT / "data" / "sources")
    parser.add_argument("--jsonl", type=Path, default=ROOT / "data" / "jsonl")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--state", type=Path, default=DEFAULT_OUT_DIR / "state.json")
    parser.add_argument("--final", type=Path, default=DEFAULT_FINAL)
    parser.add_argument("--top10k", type=Path, default=DEFAULT_TOP10K)
    parser.add_argument("--top50k", type=Path, default=DEFAULT_TOP50K)
    parser.add_argument("--phase2", type=Path, default=DEFAULT_PHASE2_TRANSLATIONS)
    parser.add_argument("--model", default=DEFAULT_MODEL)

    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("prepare"); p.set_defaults(func=cmd_prepare)
    p = sub.add_parser("submit"); p.set_defaults(func=cmd_submit)
    p = sub.add_parser("poll"); p.add_argument("--wait", action="store_true")
    p.add_argument("--poll-interval", type=int, default=60)
    p.add_argument("--max-wait-seconds", type=int, default=DEFAULT_MAX_WAIT)
    p.set_defaults(func=cmd_poll)
    p = sub.add_parser("retrieve"); p.set_defaults(func=cmd_retrieve)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
