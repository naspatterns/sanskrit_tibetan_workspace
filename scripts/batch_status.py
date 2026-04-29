"""Quick status of all in-flight batches (Phase 3.7 P0-2 + P1-2).

Reads `data/translations/{eu,en-extended}/state.json` and the final JSONL
files; prints a one-screen summary so you can tell whether
  - submit still has chunks to send
  - polling is needed (chunks in 'submitted' state)
  - retrieve is needed (chunks in 'ended' state)
  - everything is done (chunks all 'retrieved' AND final JSONL line counts
    match expected totals)

Usage:
    uv run python -m scripts.batch_status
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BATCHES = [
    ("EU re-translate",
     ROOT / "data" / "translations" / "eu" / "state.json",
     ROOT / "data" / "translations-eu.jsonl"),
    ("EN-extended (top-10K..50K)",
     ROOT / "data" / "translations" / "en-extended" / "state.json",
     ROOT / "data" / "translations-en-extended.jsonl"),
]


def line_count(path: Path) -> int:
    if not path.exists():
        return 0
    n = 0
    with path.open("rb") as f:
        for _ in f:
            n += 1
    return n


def status_emoji(s: str) -> str:
    return {
        "prepared": "📦",
        "submitted": "⏳",
        "ended": "🔄",
        "retrieved": "✅",
        "failed": "❌",
    }.get(s, "?")


def main() -> int:
    any_pending = False
    for label, state_path, final_path in BATCHES:
        print(f"\n━━━ {label} ━━━")
        if not state_path.exists():
            print(f"  state.json not found at {state_path}")
            print(f"  → run `uv run python -m scripts.translate_*  prepare` first")
            continue

        state = json.loads(state_path.read_text(encoding="utf-8"))
        chunks = state.get("chunks", [])
        total_candidates = state.get("total_candidates", "?")
        cost = state.get("estimated_cost_usd", "?")

        # Per-chunk
        for c in chunks:
            mark = status_emoji(c["status"])
            batch_id = c.get("batch_id", "—")[:24]
            counts = c.get("request_counts", {})
            counts_str = ""
            if counts:
                counts_str = (f"  succeeded={counts.get('succeeded',0):>6,}"
                              f" errored={counts.get('errored',0):>4,}")
            print(f"  {mark} chunk {c['n']:>2} · {c['status']:>10} · "
                  f"count={c['count']:>6,} · batch={batch_id}{counts_str}")

        # Aggregate
        from collections import Counter
        bucket = Counter(c["status"] for c in chunks)
        bucket_str = " · ".join(f"{s}={n}" for s, n in bucket.most_common())
        retrieved_lines = line_count(final_path)
        print(f"  Summary: {bucket_str}  ·  estimated cost ~${cost}")
        print(f"  Final JSONL: {final_path.name} → {retrieved_lines:,} lines "
              f"(of {total_candidates:,} expected)")

        # Suggest next action
        if any(c["status"] == "prepared" for c in chunks):
            print(f"  ▶ next: uv run python -m scripts.translate_{'eu' if 'eu' in str(state_path) else 'en_extended'} submit")
            any_pending = True
        elif any(c["status"] == "submitted" for c in chunks):
            print(f"  ▶ next: uv run python -m scripts.translate_{'eu' if 'eu' in str(state_path) else 'en_extended'} poll --wait")
            any_pending = True
        elif any(c["status"] == "ended" for c in chunks):
            print(f"  ▶ next: uv run python -m scripts.translate_{'eu' if 'eu' in str(state_path) else 'en_extended'} retrieve")
            any_pending = True
        elif all(c["status"] == "retrieved" for c in chunks):
            if retrieved_lines >= total_candidates * 0.95:  # 95% recovered = done
                print(f"  ✅ DONE")
            else:
                print(f"  ⚠️  All chunks retrieved but final JSONL has fewer lines than expected — check failures.jsonl")

    print()
    if not any_pending:
        print("All batches complete (or none started). Phase 3.7 ready to wrap up:")
        print("  - tier0 재빌드 (3 ko sources 통합)")
        print("  - audit 재측정 + Sentinel 50 queries before/after")
        print("  - Phase 4 deploy entry checklist")
    return 0


if __name__ == "__main__":
    sys.exit(main())
