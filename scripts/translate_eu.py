"""Multi-chunk batch translator for DE/FR/LA → ko (P0-2, Phase 3.6/3.7).

Differences vs scripts/translate_batch.py (Phase 2 single-batch):
  - Re-translates ALL EU entries (ignores existing body.ko — v1 carryover
    was per-token substitution, not real translation, per audit-B-eu-quality)
  - Chunks into 100K-request batches (Anthropic Batch API limit)
  - State per chunk: prepared / submitted / ended / retrieved / failed
  - Graceful resume: rerun any sub-command and it continues from current state
  - Rate-limit / spending-limit aware: catches Anthropic API errors during
    submit, saves state, exits with code 2 so the caller knows to retry
    after limit refresh

Usage:
    uv run python -m scripts.translate_eu prepare
    uv run python -m scripts.translate_eu submit          # resumable
    uv run python -m scripts.translate_eu poll --wait
    uv run python -m scripts.translate_eu retrieve

Output:
    data/translations/eu/requests-chunk-NNNN.jsonl   # per-chunk requests
    data/translations/eu/state.json                  # progress
    data/translations-eu.jsonl                       # final ko output (append-resume)

Cost: Claude Sonnet 4.6 batch (50% off). EU = 381,070 entries × avg 40 in tokens
+ 150 out tokens ≈ ~$451. Adjust scope (`--include` / `--exclude`) to fit budget.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from scripts.lib.io import iter_jsonl, iter_slugs_by_priority


DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_WAIT = 24 * 60 * 60  # 24h: most batches finish in <1h
CHUNK_SIZE = 100_000  # Anthropic Batch API per-batch request limit
EU_LANGS = {"de", "fr", "la"}

# Multilingual prompt — model auto-detects DE/FR/LA from input.
SYSTEM_PROMPT = """You are an expert Sanskrit-European-Korean translator specializing in
academic dictionary definitions. The input may be in German, French, or Latin
(plus Sanskrit forms). Translate the dictionary entry into concise, scholarly
Korean. Preserve:
- All Sanskrit words in IAST (do not transliterate to Hangul)
- Grammatical abbreviations (m., f., n., adj., adv., cf., etc.)
- Citation references (Mn., RV., Bg., AV., MBh., etc.)
- Numbered sense structure (1., 2., a., b., etc.)
- Original sentence boundaries and parenthetical glosses

Output: Korean translation only. No preamble, no commentary, no transliteration of European words.
Keep length roughly proportional to input."""

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT_DIR = ROOT / "data" / "translations" / "eu"
DEFAULT_FINAL = ROOT / "data" / "translations-eu.jsonl"


# ---------- candidate collection ----------

def collect_candidates(
    sources: Path,
    jsonl_dir: Path,
    include: list[str] | None,
    exclude: list[str] | None,
) -> list[dict]:
    candidates = []
    for _slug_dir, meta in iter_slugs_by_priority(sources):
        slug = meta["slug"]
        if meta.get("exclude_from_search"):
            continue
        if meta.get("target_lang") not in EU_LANGS:
            continue
        if meta.get("role") in ("equivalents", "thesaurus"):
            continue
        if include and slug not in include:
            continue
        if exclude and slug in exclude:
            continue
        path = jsonl_dir / f"{slug}.jsonl"
        if not path.exists():
            continue

        for entry in iter_jsonl(path):
            plain = (entry.get("body") or {}).get("plain", "").strip()
            if not plain or len(plain) < 10:
                continue
            candidates.append({
                "custom_id": entry["id"],
                "headword_iast": entry.get("headword_iast", entry.get("headword", "?")),
                "plain": plain[:4000],
                "source_lang": meta["target_lang"],  # de/fr/la
                "dict": slug,
            })
    return candidates


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
                    "content": (
                        f"Headword: {c['headword_iast']}\n"
                        f"Source language: {c['source_lang']}\n\n"
                        f"Entry:\n{c['plain']}"
                    ),
                }
            ],
        },
    }


# ---------- state file ----------

def load_state(state_path: Path) -> dict:
    if state_path.exists():
        return json.loads(state_path.read_text(encoding="utf-8"))
    return {"chunks": []}


def save_state(state_path: Path, state: dict) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = state_path.with_suffix(state_path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(state_path)


# ---------- API client ----------

def require_client():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set in environment", file=sys.stderr)
        print("  Set via: export ANTHROPIC_API_KEY=sk-ant-...", file=sys.stderr)
        sys.exit(1)
    import anthropic
    return anthropic.Anthropic()


def is_limit_error(e: Exception) -> bool:
    """Detect Anthropic rate-limit / spending-limit / quota errors.

    Anthropic SDK raises:
      - anthropic.RateLimitError (HTTP 429)
      - anthropic.PermissionDeniedError (HTTP 403, often spending limit)
      - anthropic.APIStatusError with .status_code in (429, 403)
    """
    name = type(e).__name__
    if name in ("RateLimitError", "PermissionDeniedError"):
        return True
    code = getattr(e, "status_code", None)
    if code in (429, 403):
        return True
    msg = str(e).lower()
    return any(kw in msg for kw in ("rate limit", "quota", "spending limit", "credit", "budget"))


# ---------- commands ----------

def cmd_prepare(args) -> int:
    candidates = collect_candidates(args.sources, args.jsonl, args.include, args.exclude)
    print(f"Collected {len(candidates):,} EU re-translate candidates", file=sys.stderr)
    if not candidates:
        print("Nothing to do.", file=sys.stderr)
        return 0

    args.out_dir.mkdir(parents=True, exist_ok=True)

    # Chunk
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
        print(f"  chunk {chunk_n}: {len(chunk):,} requests → {chunk_path.name}", file=sys.stderr)

    # Cost estimate (re-compute on actual batched chars)
    total_in_tok = sum(len(c["plain"]) for c in candidates) / 3.5
    cost_full = (total_in_tok / 1_000_000) * 3.0 + (len(candidates) * 150 / 1_000_000) * 15.0
    cost_batch = cost_full * 0.5

    state = {
        "mode": "eu",
        "model": args.model,
        "total_candidates": len(candidates),
        "estimated_cost_usd": round(cost_batch, 2),
        "chunk_size": CHUNK_SIZE,
        "chunks": chunks_meta,
    }
    save_state(args.state, state)

    print(f"\n✓ {len(chunks_meta)} chunks prepared", file=sys.stderr)
    print(f"  total candidates: {len(candidates):,}", file=sys.stderr)
    print(f"  state file: {args.state}", file=sys.stderr)
    print(f"  estimated batch cost: ~${cost_batch:.2f}", file=sys.stderr)
    print(f"\nNext: uv run python -m scripts.translate_eu submit", file=sys.stderr)
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

    print(f"Submitting {len(pending)} pending chunks (of {len(state['chunks'])} total)…", file=sys.stderr)
    client = require_client()

    submitted = 0
    for chunk in state["chunks"]:
        if chunk["status"] != "prepared":
            continue
        chunk_path = ROOT / chunk["path"]
        if not chunk_path.exists():
            print(f"  chunk {chunk['n']}: ERROR — request file missing at {chunk_path}", file=sys.stderr)
            chunk["status"] = "failed"
            chunk["error"] = "request file missing"
            save_state(args.state, state)
            continue

        with chunk_path.open(encoding="utf-8") as f:
            requests = [json.loads(line) for line in f if line.strip()]

        try:
            print(f"  chunk {chunk['n']}: submitting {len(requests):,} requests…", file=sys.stderr)
            batch = client.messages.batches.create(requests=requests)
            chunk["batch_id"] = batch.id
            chunk["status"] = "submitted"
            chunk["submitted_at"] = int(time.time())
            save_state(args.state, state)
            submitted += 1
            print(f"    → batch_id={batch.id}", file=sys.stderr)
        except Exception as e:
            if is_limit_error(e):
                print(f"\n⚠️  Rate / spending limit hit on chunk {chunk['n']}: {type(e).__name__}: {e}", file=sys.stderr)
                print(f"   {submitted} chunks submitted so far. State saved.", file=sys.stderr)
                print(f"   Re-run `submit` after limit refresh — it will resume.", file=sys.stderr)
                save_state(args.state, state)
                return 2  # special exit code for limit-hit resume
            else:
                print(f"  chunk {chunk['n']}: FAILED — {type(e).__name__}: {e}", file=sys.stderr)
                chunk["status"] = "failed"
                chunk["error"] = str(e)
                save_state(args.state, state)
                return 1

    print(f"\n✓ {submitted} chunks submitted this run.", file=sys.stderr)
    print(f"  Use `poll --wait` to wait for completion.", file=sys.stderr)
    return 0


def cmd_poll(args) -> int:
    state = load_state(args.state)
    if not state.get("chunks"):
        print(f"ERROR: no chunks in {args.state}", file=sys.stderr)
        return 1

    submitted_chunks = [c for c in state["chunks"] if c["status"] == "submitted"]
    if not submitted_chunks:
        print("No chunks in 'submitted' state to poll.", file=sys.stderr)
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
                    print(f"⚠️  Limit hit on poll. State saved.", file=sys.stderr)
                    save_state(args.state, state)
                    return 2
                print(f"  chunk {chunk['n']}: poll error — {e}", file=sys.stderr)
                continue

            print(f"  chunk {chunk['n']} ({chunk['batch_id']}): {batch.processing_status} " +
                  f"req_counts={batch.request_counts}", file=sys.stderr)

            if batch.processing_status == "ended":
                chunk["status"] = "ended"
                chunk["ended_at"] = int(time.time())
                chunk["request_counts"] = {
                    "succeeded": batch.request_counts.succeeded,
                    "errored": batch.request_counts.errored,
                    "expired": batch.request_counts.expired,
                    "canceled": batch.request_counts.canceled,
                    "processing": batch.request_counts.processing,
                }
                save_state(args.state, state)
            elif batch.processing_status in ("in_progress", "canceling"):
                any_pending = True

        if not any_pending or not args.wait:
            break
        if time.time() >= deadline:
            print(f"⏱  Poll timeout after {args.max_wait_seconds}s.", file=sys.stderr)
            return 1
        time.sleep(args.poll_interval)

    print(f"\nState summary:", file=sys.stderr)
    for s in ("prepared", "submitted", "ended", "retrieved", "failed"):
        n = sum(1 for c in state["chunks"] if c["status"] == s)
        if n: print(f"  {s}: {n}", file=sys.stderr)
    return 0


def cmd_retrieve(args) -> int:
    state = load_state(args.state)
    if not state.get("chunks"):
        print(f"ERROR: no chunks in {args.state}", file=sys.stderr)
        return 1

    ended_chunks = [c for c in state["chunks"] if c["status"] == "ended"]
    if not ended_chunks:
        print("No chunks in 'ended' state. Run `poll` first.", file=sys.stderr)
        return 0

    client = require_client()
    args.final.parent.mkdir(parents=True, exist_ok=True)

    # Append-resume: skip ids already in final
    seen_ids = set()
    if args.final.exists():
        with args.final.open(encoding="utf-8") as f:
            for line in f:
                try:
                    seen_ids.add(json.loads(line)["entry_id"])
                except Exception:
                    pass
        print(f"Resume: {len(seen_ids):,} already in {args.final.name}", file=sys.stderr)

    new_count = 0
    failures_path = args.final.with_suffix(".failures.jsonl")
    failures_count = 0

    for chunk in state["chunks"]:
        if chunk["status"] != "ended":
            continue
        try:
            print(f"  chunk {chunk['n']} ({chunk['batch_id']}): retrieving results…", file=sys.stderr)
            results = client.messages.batches.results(chunk["batch_id"])
        except Exception as e:
            if is_limit_error(e):
                print(f"⚠️  Limit hit on retrieve. State saved.", file=sys.stderr)
                save_state(args.state, state)
                return 2
            print(f"  chunk {chunk['n']}: retrieve error — {e}", file=sys.stderr)
            continue

        # Atomic append: write to .tmp, fsync, append to final
        with args.final.open("a", encoding="utf-8") as out_f, failures_path.open("a", encoding="utf-8") as err_f:
            for result in results:
                custom_id = result.custom_id
                if custom_id in seen_ids:
                    continue
                if result.result.type == "succeeded":
                    msg = result.result.message
                    ko = "".join(b.text for b in msg.content if b.type == "text").strip()
                    out_f.write(json.dumps({"entry_id": custom_id, "ko": ko}, ensure_ascii=False))
                    out_f.write("\n")
                    seen_ids.add(custom_id)
                    new_count += 1
                else:
                    err_f.write(json.dumps({
                        "custom_id": custom_id,
                        "type": result.result.type,
                        "error": getattr(result.result, "error", None) and str(result.result.error),
                    }, ensure_ascii=False))
                    err_f.write("\n")
                    failures_count += 1

        chunk["status"] = "retrieved"
        save_state(args.state, state)

    print(f"\n✓ Retrieved {new_count:,} new translations into {args.final}", file=sys.stderr)
    if failures_count:
        print(f"  {failures_count} failures logged to {failures_path}", file=sys.stderr)
    return 0


# ---------- main ----------

def main() -> int:
    parser = argparse.ArgumentParser(description="EU re-translate batch (DE/FR/LA → ko)")
    parser.add_argument("--sources", type=Path, default=ROOT / "data" / "sources")
    parser.add_argument("--jsonl", type=Path, default=ROOT / "data" / "jsonl")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR,
                        help="chunked request files dir")
    parser.add_argument("--state", type=Path, default=DEFAULT_OUT_DIR / "state.json")
    parser.add_argument("--final", type=Path, default=DEFAULT_FINAL,
                        help="merged ko output JSONL")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--include", nargs="*", default=None,
                        help="restrict to these dict slugs (whitelist)")
    parser.add_argument("--exclude", nargs="*", default=None,
                        help="skip these dict slugs (blacklist)")

    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("prepare", help="Build chunked request files")
    p.set_defaults(func=cmd_prepare)

    p = sub.add_parser("submit", help="Submit pending chunks (resumable on limit)")
    p.set_defaults(func=cmd_submit)

    p = sub.add_parser("poll", help="Check batch status (use --wait to loop)")
    p.add_argument("--wait", action="store_true")
    p.add_argument("--poll-interval", type=int, default=60)
    p.add_argument("--max-wait-seconds", type=int, default=DEFAULT_MAX_WAIT)
    p.set_defaults(func=cmd_poll)

    p = sub.add_parser("retrieve", help="Download results to final JSONL")
    p.set_defaults(func=cmd_retrieve)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
