"""Phase 3.5 — Build declension lookup index from decl-* JSONL.

Heritage Declension dicts (`family: "heritage-decl"`, `exclude_from_search:
true`) carry parsed declension paradigms in `body.plain` as flat text:
    "<deva>Declension table of [Mas.] <iast> MasculineSingularDualPlural
     Nominativeaḥ au āḥ Vocative... ..."

Output `public/indices/declension.msgpack.zst` is loaded *lazily* by the
/declension route only — not part of the eager bundle (ADR-011 D Search
tab pre-cache budget). Schema:

    { "<headword_norm>": [
        { iast: string, body: string, dict: string }, ...
    ] }

Multiple decl-* dicts can list the same headword (different paradigm
classes); we keep them all and let the UI present them as alternatives.
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

from tqdm import tqdm

from scripts.lib.io import iter_jsonl, iter_slugs_by_priority, write_msgpack_zst


def build(
    sources: Path,
    jsonl_dir: Path,
    top_filter: set[str] | None = None,
) -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = defaultdict(list)
    seen_per_hw: dict[str, set[str]] = defaultdict(set)

    for slug_dir, meta in tqdm(iter_slugs_by_priority(sources), desc="dicts", unit="dict"):
        if meta.get("family") != "heritage-decl":
            continue
        slug = meta["slug"]
        path = jsonl_dir / f"{slug}.jsonl"
        if not path.exists():
            continue
        for entry in iter_jsonl(path):
            hw_norm = entry.get("headword_norm")
            if not hw_norm:
                continue
            if top_filter is not None and hw_norm not in top_filter:
                continue
            iast = entry.get("headword_iast", hw_norm)
            body = (entry.get("body") or {}).get("plain", "")
            if not body:
                continue
            key = f"{slug}:{iast}"
            if key in seen_per_hw[hw_norm]:
                continue
            seen_per_hw[hw_norm].add(key)
            index[hw_norm].append({"iast": iast, "body": body, "dict": slug})
    return dict(index)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", maxsplit=1)[0])
    parser.add_argument("--sources", type=Path, default=Path("data/sources"))
    parser.add_argument("--jsonl", type=Path, default=Path("data/jsonl"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("public/indices/declension.msgpack.zst"),
    )
    parser.add_argument(
        "--top-source",
        type=Path,
        default=Path("data/reports/top10k.txt"),
        help="Restrict index to headwords in this top-N file (one per line). "
        "Drops the lazy-fetch payload from ~40 MB to ~3-5 MB so the "
        "main-thread decompress completes in under a second.",
    )
    args = parser.parse_args()

    top_filter: set[str] | None = None
    if args.top_source and args.top_source.exists():
        top_filter = set(
            line.strip() for line in args.top_source.read_text().splitlines() if line.strip()
        )
        print(f"Restricting to {len(top_filter):,} top headwords from {args.top_source}",
              file=sys.stderr)

    print("Aggregating heritage-decl dicts…", file=sys.stderr)
    index = build(args.sources, args.jsonl, top_filter=top_filter)
    total_rows = sum(len(v) for v in index.values())
    print(
        f"  unique headwords : {len(index):>7,}\n"
        f"  total rows       : {total_rows:>7,}",
        file=sys.stderr,
    )

    raw, compressed = write_msgpack_zst(index, args.out)
    print(f"\n✓ Wrote {args.out}", file=sys.stderr)
    print(f"  raw msgpack     : {raw / 1024 / 1024:.1f} MB", file=sys.stderr)
    print(f"  compressed      : {compressed / 1024 / 1024:.1f} MB", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
