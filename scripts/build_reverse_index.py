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

Phase 3.7 P1-2 follow-up: optional Korean synonym injection. Reads
`data/sources/_kosynonym/synonyms.json` (committed) which maps headword_iast
→ [Korean tokens]. For each canonical entry whose iast matches and whose
priority is best-in-dict (Apte 1 / MW 2), the Korean tokens are injected
into ko_buckets with SUPER_SALIENCE so they rank above all natural body.ko
hits. Fixes Sentinel KO 0/5 baseline where 자비/지혜/도/불 don't surface
karuṇā/prajñā/agni/mārga because their Apte body.ko uses 동정/지식/화/길.
"""
from __future__ import annotations

import argparse
import heapq
import json
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

# Phase 3.7 P1-2 follow-up: Korean synonym injection. Tokens added via
# synonyms.json get a salience > SALIENCE_TOP so they always rank above
# natural body.ko-derived tokens for the same Sanskrit canonical entry.
SUPER_SALIENCE = SALIENCE_TOP + 5  # = 10. Plenty of headroom for natural [0..4].

# Path of optional Korean synonym table (Phase 3.7 P1-2 follow-up).
KO_SYNONYM_PATH_DEFAULT = Path("data/sources/_kosynonym/synonyms.json")


def load_ko_synonyms(path: Path) -> dict[str, list[str]]:
    """Load `iast → [Korean tokens]` mapping for canonical synonym injection.

    Returns empty dict if path doesn't exist (preserves backward compat with
    callers that don't ship the curated table). The schema is documented in
    `data/sources/_kosynonym/synonyms.json:_meta`.
    """
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"WARN: failed to parse {path}: {exc}", file=sys.stderr)
        return {}
    syns = data.get("synonyms", {})
    # Validate shape — keys are str, values are list[str]
    out: dict[str, list[str]] = {}
    for iast, ko_list in syns.items():
        if isinstance(iast, str) and isinstance(ko_list, list):
            cleaned = [s for s in ko_list if isinstance(s, str) and s.strip()]
            if cleaned:
                out[iast] = cleaned
    return out


def collect_tokens(
    sources: Path,
    jsonl_dir: Path,
    ko_synonyms: dict[str, list[str]] | None = None,
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

            # Phase 3.7 P1-2 follow-up: Korean synonym injection.
            # If ko_synonyms maps this entry's iast to canonical Korean tokens,
            # push them with SUPER_SALIENCE so they outrank natural body.ko
            # hits. The heap's priority/hw_len tiebreakers still apply, so
            # Apte priority=1 short-headword wins over MW priority=2 long
            # for the same synonym. Only the canonical entries get this
            # boost — entries with the same iast but different priority
            # naturally fall behind in priority sort.
            if ko_synonyms:
                iast = entry.get("headword_iast") or ""
                synonym_list = ko_synonyms.get(iast)
                if synonym_list:
                    item = (SUPER_SALIENCE, -priority, -hw_len, entry_id)
                    for tok in synonym_list:
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
    parser.add_argument("--ko-synonyms", type=Path,
                        default=KO_SYNONYM_PATH_DEFAULT,
                        help="Optional Korean synonym table for canonical injection "
                             "(Phase 3.7 P1-2 follow-up). Pass /dev/null to disable.")
    args = parser.parse_args()

    ko_synonyms = load_ko_synonyms(args.ko_synonyms)
    if ko_synonyms:
        n_tokens = sum(len(v) for v in ko_synonyms.values())
        print(f"Loaded {len(ko_synonyms):,} iast → KO synonym mappings "
              f"({n_tokens:,} tokens) from {args.ko_synonyms}", file=sys.stderr)
    else:
        print(f"(No KO synonym table at {args.ko_synonyms}; natural body.ko only)",
              file=sys.stderr)

    print("Collecting reverse tokens across 130 dicts…", file=sys.stderr)
    en_buckets, ko_buckets = collect_tokens(args.sources, args.jsonl, ko_synonyms)

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
