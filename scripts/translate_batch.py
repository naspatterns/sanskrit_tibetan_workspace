"""En→Ko batch translation via Anthropic Message Batches API (FB-2 Phase 2).

For each headword in `top10k.txt`, selects the canonical English entry
(highest-priority EN-target dict where body.ko is empty) and submits it to
Claude Sonnet 4.x batch translation. Results are written to
`data/translations.jsonl` and can later be merged by `build_tier0.py`.

Cost estimate (top 10K entries, ~80 input + 150 output tokens each, batch
pricing ~50% off): **~$6**.

Requires: ANTHROPIC_API_KEY env var.

Workflow:
  uv run python -m scripts.translate_batch prepare          # build request file
  uv run python -m scripts.translate_batch submit           # submit, save batch ID
  uv run python -m scripts.translate_batch poll --wait      # block until done
  uv run python -m scripts.translate_batch retrieve         # fetch results
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
DEFAULT_MAX_WAIT = 24 * 60 * 60  # 24h: most batches finish in <1h

SYSTEM_PROMPT = """You are an expert Sanskrit-English-Korean translator specializing in
academic dictionary definitions. Translate the following English dictionary
entry into concise, scholarly Korean. Preserve:
- All Sanskrit words in IAST (do not transliterate to Hangul)
- Grammatical abbreviations (m., f., n., cf., etc.)
- Citation references and abbreviations
- Numbered sense structure (1., 2., etc.)

Output: Korean translation only. No preamble, no commentary. Keep length
roughly proportional to input."""


def _require_client():
    """Import + construct the Anthropic client, failing loud if key is missing."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    import anthropic
    return anthropic.Anthropic()


def collect_candidates(sources: Path, jsonl_dir: Path, top10k: list[str]) -> list[dict]:
    """For each headword in top10k, find the canonical EN-target entry that
    lacks body.ko.

    Iterates dicts priority-ASC so the FIRST matching English entry per
    headword is the canonical choice — we short-circuit instead of
    collecting all candidates then filtering.
    """
    top10k_set = set(top10k)
    selected_by_hw: dict[str, dict] = {}

    for _slug_dir, meta in iter_slugs_by_priority(sources):
        if meta.get("exclude_from_search") or meta["target_lang"] != "en":
            continue
        jsonl_path = jsonl_dir / f"{meta['slug']}.jsonl"
        if not jsonl_path.exists():
            continue

        for entry in iter_jsonl(jsonl_path):
            hw = entry.get("headword_norm")
            if hw not in top10k_set or hw in selected_by_hw:
                continue
            plain = entry.get("body", {}).get("plain", "").strip()
            if not plain or len(plain) < 10:
                continue
            ko = entry.get("body", {}).get("ko", "").strip()
            if ko:
                # v1 already translated this entry; mark the hw done so we
                # don't pick a worse-priority candidate from another dict.
                selected_by_hw[hw] = {"__done__": True}
                continue
            selected_by_hw[hw] = {
                "custom_id": entry["id"],
                "entry_id": entry["id"],
                "headword_iast": entry["headword_iast"],
                "plain": plain[:4000],
            }

    return [c for c in selected_by_hw.values() if "__done__" not in c]


def build_batch_requests(candidates: list[dict], model: str) -> list[dict]:
    return [
        {
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
        for c in candidates
    ]


def cmd_prepare(args: argparse.Namespace) -> int:
    top10k = load_top10k(args.top10k)
    print(f"Loaded {len(top10k):,} top headwords from {args.top10k}", file=sys.stderr)

    candidates = collect_candidates(args.sources, args.jsonl, top10k)
    print(f"Selected {len(candidates):,} canonical entries needing translation",
          file=sys.stderr)

    requests = build_batch_requests(candidates, model=args.model)
    args.requests.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.requests.with_suffix(args.requests.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for r in requests:
            f.write(json.dumps(r, ensure_ascii=False))
            f.write("\n")
    tmp.replace(args.requests)

    avg_input_tokens = sum(len(c["plain"]) for c in candidates) / max(1, len(candidates)) / 3.5
    total_input = avg_input_tokens * len(candidates)
    est_full = (total_input / 1_000_000) * 1.50 + (len(candidates) * 150 / 1_000_000) * 7.50

    print(f"\n✓ Wrote {len(requests):,} batch requests → {args.requests}")
    print(f"  Model: {args.model}")
    print(f"  Avg input tokens: {avg_input_tokens:.0f}")
    print(f"  Cost estimate (batch pricing, 50% off): ~${est_full/2:.2f}")
    return 0


def _load_state(state_path: Path) -> dict | None:
    if not state_path.exists():
        return None
    return json.loads(state_path.read_text(encoding="utf-8"))


def _save_state(state_path: Path, state: dict) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = state_path.with_suffix(state_path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp.replace(state_path)


def cmd_submit(args: argparse.Namespace) -> int:
    # Double-submit guard: refuse if a state file exists unless --force.
    existing = _load_state(args.state)
    if existing and not args.force:
        print(f"ERROR: batch state already exists at {args.state}", file=sys.stderr)
        print(f"  batch_id: {existing.get('batch_id')}", file=sys.stderr)
        print(f"  Use `poll`/`retrieve` for that batch, or pass --force to overwrite",
              file=sys.stderr)
        print(f"  (overwriting abandons the existing batch but you will still be BILLED)",
              file=sys.stderr)
        return 1

    client = _require_client()
    requests = []
    with args.requests.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                requests.append(json.loads(line))

    print(f"Submitting {len(requests):,} requests to Anthropic Batch API…")
    try:
        batch = client.messages.batches.create(requests=requests)
    except Exception as e:
        # If the create() call itself failed we have no batch to bill, so just
        # surface the error. If it partially succeeded but we never got a
        # batch_id back, the user's logs should show it in stderr.
        print(f"ERROR: batch create failed: {e}", file=sys.stderr)
        return 2

    print(f"✓ Batch created: {batch.id}")
    print(f"  Status: {batch.processing_status}")

    # Save state BEFORE anything else that could fail — losing batch_id while
    # the batch is running and billing is the worst outcome.
    try:
        _save_state(args.state, {"batch_id": batch.id, "model": args.model})
        print(f"  State saved to {args.state}")
    except Exception as e:
        print(f"CRITICAL: state save failed! batch_id={batch.id}", file=sys.stderr)
        print(f"  Write this ID down manually; billing has started: {e}", file=sys.stderr)
        return 3
    return 0


def cmd_poll(args: argparse.Namespace) -> int:
    client = _require_client()
    state = _load_state(args.state)
    if not state:
        print(f"ERROR: no batch state at {args.state}", file=sys.stderr)
        return 1
    batch_id = state["batch_id"]

    deadline = time.monotonic() + args.max_wait_seconds
    while True:
        try:
            batch = client.messages.batches.retrieve(batch_id)
        except Exception as e:
            print(f"WARN: retrieve failed ({e}); retrying in {args.poll_interval}s",
                  file=sys.stderr)
            time.sleep(args.poll_interval)
            continue
        print(f"[{time.strftime('%H:%M:%S')}] {batch.processing_status}  "
              f"succeeded={batch.request_counts.succeeded} "
              f"errored={batch.request_counts.errored} "
              f"processing={batch.request_counts.processing}")
        if batch.processing_status == "ended":
            return 0
        if not args.wait:
            return 0
        if time.monotonic() >= deadline:
            print(f"ERROR: polling timed out after {args.max_wait_seconds}s",
                  file=sys.stderr)
            return 4
        time.sleep(args.poll_interval)


def _load_existing_translations(out: Path) -> set[str]:
    """Return entry_ids already present in `out` for resume support."""
    if not out.exists():
        return set()
    return {entry["entry_id"] for entry in iter_jsonl(out) if "entry_id" in entry}


def cmd_retrieve(args: argparse.Namespace) -> int:
    client = _require_client()
    state = _load_state(args.state)
    if not state:
        print(f"ERROR: no batch state at {args.state}", file=sys.stderr)
        return 1
    batch_id = state["batch_id"]

    # Resume support: skip entries we already saved on a previous run.
    existing_ids = _load_existing_translations(args.out)
    if existing_ids and not args.overwrite:
        print(f"Resuming: {len(existing_ids):,} translations already in {args.out}",
              file=sys.stderr)

    # Try for anthropic.types.TextBlock import so we can isinstance-check
    # cleanly instead of string-matching attributes.
    try:
        from anthropic.types import TextBlock
    except ImportError:
        TextBlock = None  # type: ignore[assignment]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.failures.parent.mkdir(parents=True, exist_ok=True)

    out_mode = "w" if args.overwrite else "a"
    added = 0
    failed = 0
    with args.out.open(out_mode, encoding="utf-8") as out_f, \
         args.failures.open("w", encoding="utf-8") as fail_f:
        for result in client.messages.batches.results(batch_id):
            entry_id = result.custom_id
            rtype = result.result.type
            if rtype != "succeeded":
                fail_f.write(json.dumps({
                    "entry_id": entry_id,
                    "type": rtype,
                    "detail": str(getattr(result.result, "error", ""))[:500],
                }, ensure_ascii=False))
                fail_f.write("\n")
                failed += 1
                continue
            if entry_id in existing_ids:
                continue
            content = result.result.message.content
            if TextBlock is not None:
                parts = [b.text for b in content if isinstance(b, TextBlock)]
            else:
                parts = [b.text for b in content if getattr(b, "type", None) == "text"]
            translation = "".join(parts).strip()
            if not translation:
                fail_f.write(json.dumps({
                    "entry_id": entry_id, "type": "empty-response",
                }, ensure_ascii=False))
                fail_f.write("\n")
                failed += 1
                continue
            out_f.write(json.dumps(
                {"entry_id": entry_id, "ko": translation},
                ensure_ascii=False,
            ))
            out_f.write("\n")
            added += 1

    print(f"✓ Added {added:,} translations → {args.out}")
    if failed:
        print(f"⚠  {failed:,} failures → {args.failures}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top10k", type=Path, default=Path("data/reports/top10k.txt"))
    parser.add_argument("--sources", type=Path, default=Path("data/sources"))
    parser.add_argument("--jsonl", type=Path, default=Path("data/jsonl"))
    parser.add_argument("--requests", type=Path,
                        default=Path("data/translations/requests.jsonl"))
    parser.add_argument("--state", type=Path,
                        default=Path("data/translations/batch_state.json"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/translations.jsonl"))
    parser.add_argument("--failures", type=Path,
                        default=Path("data/translations/failures.jsonl"))
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"Claude model id (default: {DEFAULT_MODEL})")

    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("prepare", help="Build batch request file from top10k")
    p.set_defaults(func=cmd_prepare)

    p = sub.add_parser("submit", help="Submit batch to Anthropic API")
    p.add_argument("--force", action="store_true",
                   help="Overwrite existing batch_state.json (abandons prior batch)")
    p.set_defaults(func=cmd_submit)

    p = sub.add_parser("poll", help="Check batch status (use --wait to loop)")
    p.add_argument("--wait", action="store_true")
    p.add_argument("--poll-interval", type=int, default=60, help="seconds between polls")
    p.add_argument("--max-wait-seconds", type=int, default=DEFAULT_MAX_WAIT)
    p.set_defaults(func=cmd_poll)

    p = sub.add_parser("retrieve", help="Download results; appends by default to support resume")
    p.add_argument("--overwrite", action="store_true",
                   help="Start fresh instead of appending (dangerous if prior run succeeded)")
    p.set_defaults(func=cmd_retrieve)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
