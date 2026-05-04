"""Phase 3.7 P1-2 alt: translate via Claude Code sub-agents (no Anthropic API).

Phase 2b proved this pattern works (subagents 병렬 배치, 9,995 entries done).
For Phase 3.7 P1-2 we re-use it: 39,874 EN-extended candidates split into
~798 sub-batches × 50 entries each. The orchestrator (the parent agent)
spawns sub-agents in waves of 5-10, each sub-agent translates its 50
entries and emits one JSON line per entry.

State machine per sub-batch:
    📦 pending  →  ⏳ dispatched  →  ✅ done   |  ❌ failed

Resume: rerunning any sub-command picks up `pending` sub-batches; `done`
ones are skipped; `dispatched` ones are re-driven (in case the orchestrator
crashed mid-wave).

Sub-commands:
    prepare      Read en-extended chunk 1 → sub-batches × 50 + state.json
    next BATCH   Print the prompt body for sub-batch BATCH (orchestrator
                 hands this to a spawned sub-agent and feeds back result)
    record N FILE  Parse sub-agent's JSON output `FILE`, append to final
                 JSONL, mark sub-batch N done in state
    status       Print one-screen summary (pending / dispatched / done / failed)
    pending      Print next K pending sub-batch numbers (for the orchestrator's
                 next wave; default K=10)

Usage flow (orchestrator side):
    uv run python -m scripts.translate_via_subagent prepare
    # → state initialized with ~798 sub-batches in 'pending'

    # Repeat until all done:
    uv run python -m scripts.translate_via_subagent pending --k 10
    # → orchestrator spawns 10 sub-agents in parallel, each given the
    #   prompt produced by `next N`. After collecting each result:
    uv run python -m scripts.translate_via_subagent record N out.json

Final output: data/translations-en-extended.jsonl (append-resume safe).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_CHUNK = ROOT / "data" / "translations" / "en-extended" / "requests-chunk-0001.jsonl"
DEFAULT_STATE = ROOT / "data" / "translations" / "en-extended-subagent" / "state.json"
DEFAULT_BATCHES = ROOT / "data" / "translations" / "en-extended-subagent" / "batches"
DEFAULT_FINAL = ROOT / "data" / "translations-en-extended.jsonl"

SUB_BATCH_SIZE = 50

# Sub-agent prompt template — mirrors translate_eu/translate_batch.py SYSTEM.
PROMPT_HEADER = """You are an expert Sanskrit-English-Korean translator specializing in
academic dictionary definitions. Translate each of the following English
dictionary entries into concise, scholarly Korean. Preserve in your output:
- All Sanskrit words in IAST (do not transliterate to Hangul)
- Grammatical abbreviations (m., f., n., cf., etc.)
- Citation references (Mn., RV., Bg., AV., MBh., etc.)
- Numbered sense structure (1., 2., a., b., etc.)
- Original sentence boundaries

OUTPUT FORMAT — strict.
Emit exactly one JSON line per entry, no preamble, no commentary, no markdown:
{"entry_id": "<custom_id>", "ko": "<Korean translation only>"}

Entries below (50 total). Translate each independently.
"""


def load_chunk_entries(chunk_path: Path) -> list[dict]:
    """Read en-extended/requests-chunk-0001.jsonl back into entry dicts.

    The file is in Anthropic Batch API format: each line is a request with
    custom_id + params.messages[0].content. We extract:
      { custom_id, headword, plain }
    so the sub-agent prompt is concise.
    """
    out = []
    with chunk_path.open(encoding="utf-8") as f:
        for line in f:
            req = json.loads(line)
            content = req["params"]["messages"][0]["content"]
            # content format: "Headword: X\n\nEntry:\nY"
            headword = ""
            plain = content
            if content.startswith("Headword:"):
                head_line, _, body = content.partition("\n\n")
                headword = head_line.removeprefix("Headword:").strip()
                if body.startswith("Entry:\n"):
                    plain = body.removeprefix("Entry:\n").strip()
                else:
                    plain = body.strip()
            out.append({
                "custom_id": req["custom_id"],
                "headword": headword,
                "plain": plain,
            })
    return out


def cmd_prepare(args) -> int:
    if not args.chunk.exists():
        print(f"ERROR: {args.chunk} missing. Run translate_en_extended prepare first.",
              file=sys.stderr)
        return 1
    if args.state.exists() and not args.force:
        print(f"State already exists at {args.state}. Use --force to rebuild.",
              file=sys.stderr)
        return 1

    entries = load_chunk_entries(args.chunk)
    print(f"Loaded {len(entries):,} entries from {args.chunk.name}", file=sys.stderr)

    args.batches.mkdir(parents=True, exist_ok=True)

    sub_batches: list[dict] = []
    for n, start in enumerate(range(0, len(entries), SUB_BATCH_SIZE), start=1):
        sub = entries[start : start + SUB_BATCH_SIZE]
        batch_path = args.batches / f"sb-{n:04d}.json"
        batch_path.write_text(json.dumps(sub, ensure_ascii=False), encoding="utf-8")
        sub_batches.append({"n": n, "size": len(sub), "status": "pending"})

    state = {
        "mode": "en-extended-subagent",
        "total_entries": len(entries),
        "sub_batch_size": SUB_BATCH_SIZE,
        "sub_batches": sub_batches,
    }
    args.state.parent.mkdir(parents=True, exist_ok=True)
    args.state.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✓ Prepared {len(sub_batches):,} sub-batches × {SUB_BATCH_SIZE} entries",
          file=sys.stderr)
    print(f"  state file: {args.state}", file=sys.stderr)
    print(f"  batch files: {args.batches}/sb-NNNN.json", file=sys.stderr)
    return 0


def cmd_next(args) -> int:
    """Print the sub-agent prompt for sub-batch N to stdout."""
    state = json.loads(args.state.read_text(encoding="utf-8"))
    n = args.batch_n
    target = next((sb for sb in state["sub_batches"] if sb["n"] == n), None)
    if target is None:
        print(f"ERROR: sub-batch {n} not in state", file=sys.stderr)
        return 1
    batch_path = args.batches / f"sb-{n:04d}.json"
    if not batch_path.exists():
        print(f"ERROR: {batch_path} missing", file=sys.stderr)
        return 1

    entries = json.loads(batch_path.read_text(encoding="utf-8"))
    print(PROMPT_HEADER)
    for i, e in enumerate(entries, start=1):
        print(f"--- Entry {i} ---")
        print(f"custom_id: {e['custom_id']}")
        print(f"headword: {e['headword']}")
        print(f"body:")
        print(e["plain"])
        print()
    return 0


def cmd_record(args) -> int:
    """Parse sub-agent JSON output (NDJSON: one line per entry) → final JSONL."""
    state = json.loads(args.state.read_text(encoding="utf-8"))
    n = args.batch_n
    target = next((sb for sb in state["sub_batches"] if sb["n"] == n), None)
    if target is None:
        print(f"ERROR: sub-batch {n} not in state", file=sys.stderr)
        return 1
    if target["status"] == "done":
        print(f"sub-batch {n}: already done, skipping", file=sys.stderr)
        return 0

    text = args.result.read_text(encoding="utf-8") if args.result.exists() else ""
    if not text.strip():
        print(f"ERROR: empty result file {args.result}", file=sys.stderr)
        return 1

    # Tolerate code fences and stray text by extracting JSON object lines.
    parsed = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("```", "//", "#")):
            continue
        # Trim trailing commas
        if line.endswith(","):
            line = line[:-1]
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "entry_id" in obj and "ko" in obj:
            parsed.append(obj)

    if not parsed:
        print(f"ERROR: no valid JSON lines parsed from {args.result}", file=sys.stderr)
        target["status"] = "failed"
        target["error"] = "no parseable JSON"
        args.state.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        return 1

    # Append to final (resume-safe: skip already-seen ids)
    seen: set[str] = set()
    if args.final.exists():
        with args.final.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        seen.add(json.loads(line)["entry_id"])
                    except Exception:
                        pass

    args.final.parent.mkdir(parents=True, exist_ok=True)
    new_count = 0
    with args.final.open("a", encoding="utf-8") as f:
        for obj in parsed:
            if obj["entry_id"] in seen:
                continue
            f.write(json.dumps({"entry_id": obj["entry_id"], "ko": obj["ko"]}, ensure_ascii=False))
            f.write("\n")
            seen.add(obj["entry_id"])
            new_count += 1

    target["status"] = "done"
    target["recorded"] = new_count
    args.state.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ sub-batch {n}: parsed {len(parsed)} / recorded {new_count} new "
          f"(of {target['size']} expected)", file=sys.stderr)
    return 0


def cmd_status(args) -> int:
    if not args.state.exists():
        print("State not found. Run `prepare` first.", file=sys.stderr)
        return 1
    state = json.loads(args.state.read_text(encoding="utf-8"))
    cnt = Counter(sb["status"] for sb in state["sub_batches"])
    total = len(state["sub_batches"])
    final_lines = 0
    if args.final.exists():
        with args.final.open(encoding="utf-8") as f:
            for _ in f:
                final_lines += 1
    print(f"Sub-batches × {state['sub_batch_size']} (total entries: {state['total_entries']:,})")
    for st in ("pending", "dispatched", "done", "failed"):
        n = cnt.get(st, 0)
        if n:
            print(f"  {st:>10}: {n:>5,} ({n/total*100:.1f}%)")
    print(f"Final JSONL: {args.final.name} → {final_lines:,} lines / {state['total_entries']:,} expected")
    if cnt.get("done", 0) == total:
        print("\n✅ ALL DONE — Phase 3.7 P1-2 sub-agent path complete")
    return 0


def cmd_pending(args) -> int:
    """Print the next K pending sub-batch numbers (one per line)."""
    state = json.loads(args.state.read_text(encoding="utf-8"))
    pending = [sb["n"] for sb in state["sub_batches"] if sb["status"] == "pending"]
    out = pending[: args.k]
    for n in out:
        print(n)
    if not out:
        print("# (no pending sub-batches)", file=sys.stderr)
    return 0


def cmd_mark(args) -> int:
    """Mark sub-batch as `dispatched` (orchestrator just spawned a sub-agent)."""
    state = json.loads(args.state.read_text(encoding="utf-8"))
    target = next((sb for sb in state["sub_batches"] if sb["n"] == args.batch_n), None)
    if target is None:
        print(f"ERROR: sub-batch {args.batch_n} not in state", file=sys.stderr)
        return 1
    if target["status"] in ("done", "failed"):
        print(f"sub-batch {args.batch_n}: already {target['status']}, not re-marking",
              file=sys.stderr)
        return 0
    target["status"] = "dispatched"
    args.state.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--chunk", type=Path, default=DEFAULT_CHUNK)
    p.add_argument("--state", type=Path, default=DEFAULT_STATE)
    p.add_argument("--batches", type=Path, default=DEFAULT_BATCHES)
    p.add_argument("--final", type=Path, default=DEFAULT_FINAL)
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("prepare")
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(func=cmd_prepare)

    sp = sub.add_parser("next")
    sp.add_argument("batch_n", type=int)
    sp.set_defaults(func=cmd_next)

    sp = sub.add_parser("record")
    sp.add_argument("batch_n", type=int)
    sp.add_argument("result", type=Path, help="Sub-agent result file (NDJSON)")
    sp.set_defaults(func=cmd_record)

    sp = sub.add_parser("mark")
    sp.add_argument("batch_n", type=int)
    sp.set_defaults(func=cmd_mark)

    sp = sub.add_parser("status")
    sp.set_defaults(func=cmd_status)

    sp = sub.add_parser("pending")
    sp.add_argument("--k", type=int, default=10)
    sp.set_defaults(func=cmd_pending)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
