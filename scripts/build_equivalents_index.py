"""Build Zone B (equivalents) index from role=equivalents/thesaurus dicts.

Aggregates active equiv-* sources (those with `meta.exclude_from_search`
falsy) into a single multi-channel lookup index used by the search UI's
Zone B (대응어 / Equivalents).

Output: public/indices/equivalents.msgpack.zst
Schema: { <search_key>: [ <equiv_row>, ... ] }
  - <search_key>: NFD-stripped lowercase. Three channels per row:
      • normalize_headword(skt_iast)  ← matches HK input via client-side translit
      • normalize(tib_wylie)
      • zh stripped (CJK kept as-is)
  - <equiv_row>: { sources: [slug, ...], skt_iast?, tib_wylie?, zh?,
                   ko?, en?, ja?, de?, category?, note? }
    Empty fields omitted. `sources` is priority-ASC sorted (Mvy < Negi < ...).

Dedup (D10b/(b) policy): cross-source. Unique identity is
`(skt_iast_lower, tib_wylie_lower, zh_lower)`. On collision the row with the
larger field-fill score wins; the loser's slug is merged into `sources`.
Field-level merging is intentionally avoided so each output row stays
attributable to a single primary source.

frequency.py interaction (D10c/(c)): equiv rows do not feed top-10K
weighting — that script filters role∈{equivalents, thesaurus} out.
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

from tqdm import tqdm

from scripts.lib.io import (
    iter_jsonl,
    iter_slugs_by_priority,
    write_msgpack_zst,
)
from scripts.lib.transliterate import normalize, normalize_headword


# Fields propagated from `body.equivalents` into the output row.
# Order is preserved into msgpack for stable bytes across rebuilds.
EQUIV_FIELDS: tuple[str, ...] = (
    "skt_iast", "tib_wylie", "zh", "ko", "en", "ja", "de", "category", "note",
)
EQUIV_ROLES: frozenset[str] = frozenset({"equivalents", "thesaurus"})

# A row must carry at least one of these to be searchable.
SEARCHABLE_CHANNELS: tuple[str, ...] = ("skt_iast", "tib_wylie", "zh")


def _info_score(row: dict) -> int:
    """Total non-empty content length across language fields.

    Used to pick the richer row on dedup collision. `sources` is excluded —
    it's metadata, not content.
    """
    return sum(len(row.get(f, "") or "") for f in EQUIV_FIELDS)


def _dedup_key(row: dict) -> tuple[str, str, str]:
    """Identity tuple for cross-source collision detection.

    Same (skt, tib, zh) triple from different dicts collapses to one output
    row, regardless of which dict reported it first.
    """
    return (
        (row.get("skt_iast") or "").strip().lower(),
        (row.get("tib_wylie") or "").strip().lower(),
        (row.get("zh") or "").strip(),
    )


def _row_from_entry(entry: dict, slug: str) -> dict | None:
    """Project a JSONL entry's body.equivalents into a flat row.

    Returns None when the entry has no skt/tib/zh signal at all (would not
    be searchable in any channel, so storing it is dead weight).
    """
    eq = (entry.get("body") or {}).get("equivalents") or {}
    row: dict = {"sources": [slug]}
    for f in EQUIV_FIELDS:
        v = eq.get(f, "")
        if v:
            row[f] = v
    if not any(row.get(c) for c in SEARCHABLE_CHANNELS):
        return None
    return row


def _search_keys(row: dict) -> list[str]:
    """Lookup keys this row should appear under (1–3 channels).

    Sanskrit uses `normalize_headword` so HK queries (e.g. 'dharma') reach
    the same key as IAST. Tibetan and Chinese use the lighter `normalize`
    (NFD + strip combining + lowercase) since they don't need transliteration.
    """
    keys: list[str] = []
    if "skt_iast" in row:
        k = normalize_headword(row["skt_iast"])
        if k:
            keys.append(k)
    if "tib_wylie" in row:
        k = normalize(row["tib_wylie"])
        if k:
            keys.append(k)
    if "zh" in row:
        k = row["zh"].strip()
        if k:
            keys.append(k)
    return keys


def collect_rows(
    sources_dir: Path,
    jsonl_dir: Path,
) -> tuple[dict[tuple[str, str, str], dict], dict[str, int]]:
    """Stream every active equiv-* JSONL once, dedup as we go.

    Returns (deduped_rows, stats). `deduped_rows` is keyed by `_dedup_key`;
    iteration order matches priority-ASC slug order (cosmetic only — the
    output index is rebuilt independently in `index_by_key`).
    """
    deduped: dict[tuple[str, str, str], dict] = {}
    stats: dict[str, int] = defaultdict(int)

    pairs = iter_slugs_by_priority(sources_dir)
    equiv_pairs = [
        (d, m) for d, m in pairs
        if m.get("role") in EQUIV_ROLES
    ]
    print(f"Found {len(equiv_pairs)} equiv-role dicts (any exclude state)", file=sys.stderr)

    for slug_dir, meta in equiv_pairs:
        slug = meta["slug"]
        if meta.get("exclude_from_search"):
            stats["dicts_skipped_excluded"] += 1
            superseded = meta.get("superseded_by", "—")
            print(f"  skip {slug:30s}  → superseded by {superseded}", file=sys.stderr)
            continue
        jsonl_path = jsonl_dir / f"{slug}.jsonl"
        if not jsonl_path.exists():
            stats["dicts_missing_jsonl"] += 1
            print(f"  ! missing  {slug:30s}  ({jsonl_path.name})", file=sys.stderr)
            continue

        stats["dicts_read"] += 1
        priority = meta.get("priority", "?")
        print(f"  read {slug:30s}  prio={priority}", file=sys.stderr)

        for entry in tqdm(iter_jsonl(jsonl_path), desc=slug, unit="row", leave=False):
            stats["entries_read"] += 1
            row = _row_from_entry(entry, slug)
            if row is None:
                stats["entries_no_signal"] += 1
                continue

            dk = _dedup_key(row)
            existing = deduped.get(dk)
            if existing is None:
                deduped[dk] = row
                stats["unique_rows"] += 1
                continue

            stats["entries_deduped"] += 1
            new_better = _info_score(row) > _info_score(existing)
            if new_better:
                # Promote richer row, preserve sources history (highest-prio
                # source still listed first since iteration is priority-ASC
                # and `existing.sources` already carries the earlier slugs).
                merged = list(existing["sources"])
                for s in row["sources"]:
                    if s not in merged:
                        merged.append(s)
                row["sources"] = merged
                deduped[dk] = row
            else:
                if slug not in existing["sources"]:
                    existing["sources"].append(slug)

    return deduped, dict(stats)


def index_by_key(
    deduped: dict[tuple[str, str, str], dict],
) -> dict[str, list[dict]]:
    """Bucket deduped rows by 1–3 search keys per row."""
    index: dict[str, list[dict]] = defaultdict(list)
    for row in deduped.values():
        for key in _search_keys(row):
            index[key].append(row)
    return dict(index)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", maxsplit=1)[0])
    parser.add_argument("--sources", type=Path, default=Path("data/sources"))
    parser.add_argument("--jsonl", type=Path, default=Path("data/jsonl"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("public/indices/equivalents.msgpack.zst"),
    )
    args = parser.parse_args()

    print("Collecting rows from active equiv-* dicts…\n", file=sys.stderr)
    deduped, stats = collect_rows(args.sources, args.jsonl)

    print("\nCollection summary:", file=sys.stderr)
    print(f"  dicts read           : {stats.get('dicts_read', 0)}", file=sys.stderr)
    print(f"  dicts skipped (excl) : {stats.get('dicts_skipped_excluded', 0)}", file=sys.stderr)
    print(f"  dicts missing jsonl  : {stats.get('dicts_missing_jsonl', 0)}", file=sys.stderr)
    print(f"  rows read            : {stats.get('entries_read', 0):,}", file=sys.stderr)
    print(f"  rows no signal       : {stats.get('entries_no_signal', 0):,}", file=sys.stderr)
    print(f"  unique rows kept     : {stats.get('unique_rows', 0):,}", file=sys.stderr)
    print(f"  rows deduped         : {stats.get('entries_deduped', 0):,}", file=sys.stderr)

    print("\nIndexing rows by search keys…", file=sys.stderr)
    index = index_by_key(deduped)

    raw_size, comp_size = write_msgpack_zst(index, args.out)

    total_lookups = sum(len(v) for v in index.values())
    print(f"\n✓ Wrote {args.out}", file=sys.stderr)
    print(f"  keys (lookup buckets): {len(index):,}", file=sys.stderr)
    print(f"  total row-references : {total_lookups:,}", file=sys.stderr)
    print(f"  raw msgpack          : {raw_size / 1024 / 1024:.1f} MB", file=sys.stderr)
    print(f"  zstd compressed      : {comp_size / 1024 / 1024:.1f} MB", file=sys.stderr)
    print(
        f"  compression ratio    : {raw_size / max(comp_size, 1):.1f}x",
        file=sys.stderr,
    )

    # Probe a few well-known headwords for sanity (silent if none present).
    for probe in ("dharma", "byang chub", "般若", "nirvāṇa"):
        norm = normalize_headword(probe)
        if norm in index:
            n = len(index[norm])
            srcs = sorted({s for r in index[norm] for s in r.get("sources", [])})
            print(f"  probe '{probe}' → {n} rows · sources={srcs}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
