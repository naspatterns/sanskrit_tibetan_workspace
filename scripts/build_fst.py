"""Generate sorted unique headwords for client-side autocomplete (FST/trie).

Phase 2 MVP ships a plain sorted list; the browser-side decides whether to
build a real FST (mnemonist/fst) or a linear binary-search array from it.
Phase 6+ can swap in a Rust-compiled WASM FST if perf measurements demand it.

Phase 3.7 follow-up: emit 3-column TSV `norm\\tiast\\trank` so the client
prefix engine can re-rank matches by importance (top-10K first). Also filter
out HTML extraction noise (combining marks `͜`, MW circumflex compound
markers `â`, etc.) that pollute prefix results without adding semantic value.

Output:
  - public/indices/headwords.txt.zst
    (one `headword_norm\\theadword_iast\\trank` per line, sorted by norm.
     rank = top10k position 1..10000, or 999999 for long-tail.)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import zstandard as zstd
from tqdm import tqdm

from scripts.lib.io import iter_jsonl, iter_slugs_by_priority


# Phase 3.7 follow-up: noise filter for HTML extraction artifacts.
# These characters appear in MW's compound display forms that shouldn't
# surface as standalone autocomplete candidates.
NOISE_CHARS = frozenset([
    "͜",  # COMBINING DOUBLE BREVE BELOW (e.g. dhâ ͜ ana)
    "̂",  # COMBINING CIRCUMFLEX ACCENT
    "â",       # a-circumflex (MW HTML compound joiner)
    "ê", "î", "ô", "û",
])


def is_noise(iast: str) -> bool:
    """True if iast contains HTML extraction noise that pollutes autocomplete."""
    return any(c in NOISE_CHARS for c in iast)


def load_rank_table(top10k_path: Path) -> dict[str, int]:
    """Load `headword_norm → 1-based rank` from data/reports/top10k.txt.

    Returns empty dict if the file is missing — caller falls back to no-rank
    output (effectively rank=999999 for everyone). Allows new repos to build
    indices before ever running `frequency.py`.
    """
    if not top10k_path.exists():
        return {}
    out: dict[str, int] = {}
    for i, line in enumerate(top10k_path.read_text(encoding="utf-8").splitlines(),
                              start=1):
        s = line.strip()
        if s:
            out[s] = i
    return out


def collect_headwords(sources: Path, jsonl_dir: Path) -> dict[str, str]:
    """Return `{headword_norm: headword_iast}`.

    Priority-ASC iteration means Apte/MW's IAST spelling wins on collisions.
    Skips entries whose iast contains noise characters (Phase 3.7 follow-up)
    so HTML compound display forms don't pollute autocomplete.
    """
    pairs: dict[str, str] = {}
    skipped = 0

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
            if is_noise(iast):
                skipped += 1
                continue
            if norm not in pairs:
                pairs[norm] = iast

    if skipped:
        print(f"  (filtered {skipped:,} noise-iast headwords)", file=sys.stderr)
    return pairs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, default=Path("data/sources"))
    parser.add_argument("--jsonl", type=Path, default=Path("data/jsonl"))
    parser.add_argument(
        "--out", type=Path,
        default=Path("public/indices/headwords.txt.zst"),
    )
    parser.add_argument(
        "--top10k", type=Path, default=Path("data/reports/top10k.txt"),
        help="Source of rank info (1..10000). Long-tail terms get rank=999999.",
    )
    parser.add_argument("--level", type=int, default=19, help="zstd level (default 19)")
    args = parser.parse_args()

    rank_table = load_rank_table(args.top10k)
    if rank_table:
        print(f"Loaded {len(rank_table):,} ranks from {args.top10k}",
              file=sys.stderr)
    else:
        print(f"(No rank table at {args.top10k}; emitting rank=999999 for all)",
              file=sys.stderr)

    pairs = collect_headwords(args.sources, args.jsonl)
    print(f"\nCollected {len(pairs):,} unique headwords", file=sys.stderr)

    # Sort by norm for binary-search-friendly client consumption.
    # Phase 3.7: append rank column. Top-10K terms get 1..10000; long-tail 999999.
    LONG_TAIL_RANK = 999_999
    lines = (
        f"{norm}\t{iast}\t{rank_table.get(norm, LONG_TAIL_RANK)}\n"
        for norm, iast in sorted(pairs.items())
    )
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
