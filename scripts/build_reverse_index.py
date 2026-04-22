"""Aggregate per-entry `reverse.en[]` / `reverse.ko[]` tokens into a pair of
searchable indices.

For each token, keep the top-N entry IDs ranked by `priority` ASC (Apte=1
beats MW=2 beats …). Excludes `exclude_from_search` dicts (FB-5). Drops
tokens that appear in fewer than `--min-freq` entries after aggregation.

Output:
  - public/indices/reverse_en.msgpack.zst
  - public/indices/reverse_ko.msgpack.zst

Each file decodes to: `{token: [entry_id, ...]}` — entry_id list is
priority-sorted so the client just iterates in order.
"""
from __future__ import annotations

import argparse
import heapq
import sys
from collections import defaultdict
from pathlib import Path

from tqdm import tqdm

from scripts.lib.io import iter_jsonl, iter_slug_dirs, load_meta, write_msgpack_zst


# Bounded heap cap per token. 100 gives plenty of results for UI paging.
MAX_PER_TOKEN = 100

# Tokens with global frequency below this are dropped (long-tail noise).
DEFAULT_MIN_FREQ = 3


def collect_tokens(
    sources: Path,
    jsonl_dir: Path,
) -> tuple[dict[str, list], dict[str, list]]:
    """Single pass over all JSONL files.

    Returns (en_buckets, ko_buckets) where each bucket is a min-heap keyed on
    (priority, entry_id). Using a max-heap on -priority would keep the
    *worst*; we want to keep the best, so we use a min-heap and `heappushpop`
    to evict when full.
    """
    en_buckets: dict[str, list] = defaultdict(list)
    ko_buckets: dict[str, list] = defaultdict(list)

    for slug_dir in tqdm(iter_slug_dirs(sources), desc="dicts", unit="dict"):
        meta = load_meta(slug_dir)
        if meta.get("exclude_from_search"):
            continue
        jsonl_path = jsonl_dir / f"{meta['slug']}.jsonl"
        if not jsonl_path.exists():
            continue

        for entry in iter_jsonl(jsonl_path):
            # Every Phase 1 entry inherits `priority` from meta; a missing
            # field signals an upstream bug, so refuse to silently bucket it
            # at a made-up rank.
            priority = entry["priority"]
            entry_id = entry["id"]
            reverse = entry.get("reverse") or {}
            item = (-priority, entry_id)
            for tok in reverse.get("en", ()):
                _bounded_push(en_buckets[tok], item)
            for tok in reverse.get("ko", ()):
                _bounded_push(ko_buckets[tok], item)

    return en_buckets, ko_buckets


def _bounded_push(heap: list, item: tuple) -> None:
    """Keep the N items with LOWEST `priority` number (= BEST dict).

    Items are `(-priority, entry_id)`, so min-heap's `heap[0]` is the worst
    priority held. When a better candidate arrives (`-priority` less negative
    than heap[0]), evict the worst. Trace: heap=[(-89,x)], push (-1,y) →
    (-1,y) > (-89,x) → heapreplace → heap=[(-1,y)], priority 1 kept.
    """
    if len(heap) < MAX_PER_TOKEN:
        heapq.heappush(heap, item)
    elif item > heap[0]:
        heapq.heapreplace(heap, item)


def finalize(buckets: dict[str, list], min_freq: int) -> dict[str, list[str]]:
    """Convert heaps to priority-sorted entry-id lists, dropping rare tokens."""
    out: dict[str, list[str]] = {}
    for tok, heap in buckets.items():
        if len(heap) < min_freq:
            continue
        # heap contains (-priority, entry_id). Sort so BEST priority comes first.
        ordered = sorted(heap, reverse=True)  # reverse: largest -priority (=lowest prio) first
        out[tok] = [entry_id for _, entry_id in ordered]
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, default=Path("data/sources"))
    parser.add_argument("--jsonl", type=Path, default=Path("data/jsonl"))
    parser.add_argument("--out-dir", type=Path, default=Path("public/indices"))
    parser.add_argument("--min-freq", type=int, default=DEFAULT_MIN_FREQ,
                        help="Drop tokens appearing in fewer than N entries (default: 3)")
    args = parser.parse_args()

    print("Collecting reverse tokens across 130 dicts…", file=sys.stderr)
    en_buckets, ko_buckets = collect_tokens(args.sources, args.jsonl)

    print(f"  raw tokens: en={len(en_buckets):,}  ko={len(ko_buckets):,}", file=sys.stderr)

    en_index = finalize(en_buckets, args.min_freq)
    ko_index = finalize(ko_buckets, args.min_freq)

    print(f"  after min-freq≥{args.min_freq}: en={len(en_index):,}  ko={len(ko_index):,}",
          file=sys.stderr)

    _, en_size = write_msgpack_zst(en_index, args.out_dir / "reverse_en.msgpack.zst")
    _, ko_size = write_msgpack_zst(ko_index, args.out_dir / "reverse_ko.msgpack.zst")

    print(f"\n✓ Wrote reverse_en.msgpack.zst  {en_size/1024/1024:.1f} MB "
          f"({len(en_index):,} tokens)")
    print(f"✓ Wrote reverse_ko.msgpack.zst  {ko_size/1024/1024:.1f} MB "
          f"({len(ko_index):,} tokens)")

    if "fire" in en_index:
        print(f"\nExample: 'fire' → {len(en_index['fire'])} entries, first 5: "
              f"{en_index['fire'][:5]}")
    if "법" in ko_index:
        print(f"Example: '법' → {len(ko_index['법'])} entries, first 5: "
              f"{ko_index['법'][:5]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
