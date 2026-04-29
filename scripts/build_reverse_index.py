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

# Phase 3.6 P1-1 — headword salience boost. reverse_tokens.py emits the
# reverse.en[] / reverse.ko[] list ordered by position weight (tokens in the
# first 30 chars of body.plain rank highest). We use that index as a salience
# signal: entries where the searched token appears as one of the *first 5*
# reverse tokens get prioritised over entries where it's a buried gloss.
#
# Combined with a short-headword secondary signal, this fixes the audit-A
# finding that `fire` returned `homiḥ, homaḥ, hotṛ, huta, hu` (alphabetic late
# entries) instead of `agni`. After boost: `agni`'s body starts "m. fire; the
# god of fire" → token `fire` is reverse.en[0], salience=5; `huta`'s body
# starts "burnt offering" → `fire` appears later, salience<5. agni rises.
SALIENCE_TOP = 5  # tokens at indices [0..SALIENCE_TOP-1] get descending boost


def collect_tokens(
    sources: Path,
    jsonl_dir: Path,
) -> tuple[dict[str, list], dict[str, list]]:
    """Single pass over all JSONL files.

    Each heap item is now `(salience, -priority, -hw_len, entry_id)` so the
    sort cascade is:
      1. salience DESC — token in body.plain first-30-chars wins (P1-1)
      2. -priority ASC actually meaning priority ASC — Apte (1) before MW (2)
      3. -hw_len DESC actually meaning hw_len ASC — short canonical headwords
         (`agni`) before long compounds
      4. entry_id — deterministic tiebreak
    See finalize() for the actual ordering reverse.
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

        meta_priority = meta["priority"]
        for entry in iter_jsonl(jsonl_path):
            # Phase 1 design: entries inherit `priority` inline from meta.
            # Phase 2.5 equiv-* extract scripts skipped this backfill, so
            # fall back to meta priority when the inline field is absent
            # (B1 fix, 2026-04-29). The B2 backfill script populates the
            # inline field in-place; both code paths converge to the same
            # priority value.
            priority = entry.get("priority", meta_priority)
            entry_id = entry["id"]
            hw = entry.get("headword_iast") or entry.get("headword") or ""
            hw_len = len(hw)
            reverse = entry.get("reverse") or {}

            # P1-1: enumerate reverse.en/ko to recover position. The list is
            # already sorted by position weight (reverse_tokens.py:103), so
            # index 0 = highest salience.
            for i, tok in enumerate(reverse.get("en", ())):
                salience = max(0, SALIENCE_TOP - i)
                item = (salience, -priority, -hw_len, entry_id)
                _bounded_push(en_buckets[tok], item)
            for i, tok in enumerate(reverse.get("ko", ())):
                salience = max(0, SALIENCE_TOP - i)
                item = (salience, -priority, -hw_len, entry_id)
                _bounded_push(ko_buckets[tok], item)

    return en_buckets, ko_buckets


def _bounded_push(heap: list, item: tuple) -> None:
    """Keep the N items with HIGHEST salience-priority composite key.

    Items are tuples whose lexicographic ordering reflects:
      (salience DESC, priority ASC, hw_len ASC, entry_id ASC)
    encoded as (salience, -priority, -hw_len, entry_id) so that `item > heap[0]`
    means "better candidate, evict the worst-held".

    P1-1 (Phase 3.6): The 4-tuple replaces the prior 2-tuple
    `(-priority, entry_id)`. `agni`/`fire` example: agni has salience=5
    (fire is reverse.en[0]); huta has salience<5 (fire is later) — heap keeps
    agni even though both have priority=1.
    """
    if len(heap) < MAX_PER_TOKEN:
        heapq.heappush(heap, item)
    elif item > heap[0]:
        heapq.heapreplace(heap, item)


def finalize(buckets: dict[str, list], min_freq: int) -> dict[str, list[str]]:
    """Convert heaps to salience+priority-sorted entry-id lists.

    Drops tokens below min_freq. The heap items are
    `(salience, -priority, -hw_len, entry_id)`, so `sorted(heap, reverse=True)`
    yields highest salience first → priority 1 first → shortest headword first.
    """
    out: dict[str, list[str]] = {}
    for tok, heap in buckets.items():
        if len(heap) < min_freq:
            continue
        ordered = sorted(heap, reverse=True)
        out[tok] = [entry_id for _, _, _, entry_id in ordered]
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
