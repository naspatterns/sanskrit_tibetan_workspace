"""Generate sorted unique headwords for client-side autocomplete (FST/trie).

Phase 2 MVP ships a plain sorted list; the browser-side decides whether to
build a real FST (mnemonist/fst) or a linear binary-search array from it.
Phase 6+ can swap in a Rust-compiled WASM FST if perf measurements demand it.

Output:
  - public/indices/headwords.txt.zst
    (one `headword_norm\theadword_iast` per line, sorted by norm)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import zstandard as zstd
from tqdm import tqdm

from scripts.lib.io import iter_jsonl, iter_slugs_by_priority


def collect_headwords(sources: Path, jsonl_dir: Path) -> dict[str, str]:
    """Return `{headword_norm: headword_iast}`.

    Priority-ASC iteration means Apte/MW's IAST spelling wins on collisions.
    """
    pairs: dict[str, str] = {}

    for _slug_dir, meta in tqdm(
        iter_slugs_by_priority(sources), desc="dicts", unit="dict"
    ):
        if meta.get("exclude_from_search"):
            continue
        jsonl_path = jsonl_dir / f"{meta['slug']}.jsonl"
        if not jsonl_path.exists():
            continue
        for entry in iter_jsonl(jsonl_path):
            norm = entry.get("headword_norm")
            iast = entry.get("headword_iast")
            if not norm or not iast:
                continue
            if norm not in pairs:
                pairs[norm] = iast

    return pairs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, default=Path("data/sources"))
    parser.add_argument("--jsonl", type=Path, default=Path("data/jsonl"))
    parser.add_argument(
        "--out", type=Path,
        default=Path("public/indices/headwords.txt.zst"),
    )
    parser.add_argument("--level", type=int, default=19, help="zstd level (default 19)")
    args = parser.parse_args()

    pairs = collect_headwords(args.sources, args.jsonl)
    print(f"\nCollected {len(pairs):,} unique headwords", file=sys.stderr)

    # Sort by norm for binary-search-friendly client consumption.
    lines = (f"{norm}\t{iast}\n" for norm, iast in sorted(pairs.items()))
    text = "".join(lines).encode("utf-8")
    raw_size = len(text)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    compressor = zstd.ZstdCompressor(level=args.level)
    compressed = compressor.compress(text)
    args.out.write_bytes(compressed)

    print(f"✓ Wrote {args.out}")
    print(f"  raw:        {raw_size/1024/1024:.1f} MB")
    print(f"  compressed: {len(compressed)/1024/1024:.1f} MB ({len(compressed)/raw_size:.1%})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
