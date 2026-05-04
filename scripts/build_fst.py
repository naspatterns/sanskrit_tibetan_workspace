"""Generate sorted unique headwords for client-side autocomplete (FST/trie).

Phase 2 MVP ships a plain sorted list; the browser-side decides whether to
build a real FST (mnemonist/fst) or a linear binary-search array from it.
Phase 6+ can swap in a Rust-compiled WASM FST if perf measurements demand it.

Phase 3.7 follow-up: emit 4-column TSV `norm\\tiast\\trank\\tupasarga` so the
client prefix engine can:
  - re-rank matches by importance (top-10K first)
  - tag each headword with at most ONE Sanskrit upasarga (the single shortest
    canonical prefix at the start of the word). Tibetan headwords get tagged
    if they start with a recognized translation phrase like 'rab tu', 'rnam
    par', 'kun', etc. Empty 4th column = no upasarga.

Also filters out HTML extraction noise (combining marks `͜`, MW circumflex
compound markers `â`, etc.) that pollute prefix results without adding
semantic value.

The upasarga tagging is single (not chained). For `prajñā` → `pra`. For
`pratisthā` → `prati` (its own canonical upasarga, NOT `pra+ti`). For
`prasamskāra` → `pra` only (no chained `pra+sam` even though both start the
word). User instruction: 짧은 prefix 기준 (single canonical, not chained).

Output:
  - public/indices/headwords.txt.zst
    (one `headword_norm\\theadword_iast\\trank\\tupasarga` per line, sorted
     by norm. rank = top10k position 1..10000, or 999999 for long-tail.
     upasarga = canonical norm string, or empty.)
"""
from __future__ import annotations

import argparse
import json
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


# Phase 3.7 follow-up (upasarga tagging).
UPASARGA_PATH_DEFAULT = Path("data/sources/_upasarga/upasarga.json")


def load_upasargas(path: Path) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Return (sanskrit, tibetan) tag tables.

    Each entry is `(iast_prefix, return_norm)` so we match by IAST (preserves
    diacritics — avoids `sūrya` falsely tagged with upasarga `su`) but emit
    the normalized form so the client can compare against `entry.upasarga ==
    queryNorm`.

    Both lists sorted by IAST-length DESC so `prati` matches before `pra` for
    `pratiṣṭhā`, correctly identifying `prati` as the single upasarga. User
    instruction: "짧은 prefix 기준" = single canonical (not chained).
    """
    if not path.exists():
        return [], []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"WARN: failed to parse {path}: {exc}", file=sys.stderr)
        return [], []
    skt = [(v.get("iast", k), k) for k, v in data.get("sanskrit", {}).items()]
    bo = [(v.get("iast", k), k) for k, v in data.get("tibetan", {}).items()]
    skt.sort(key=lambda t: (-len(t[0]), t[0]))
    bo.sort(key=lambda t: (-len(t[0]), t[0]))
    return skt, bo


def tag_upasarga(
    iast: str,
    norm: str,
    skt_upasargas: list[tuple[str, str]],
    bo_upasargas: list[tuple[str, str]],
) -> str:
    """Return the SINGLE canonical upasarga (norm form) matching `iast` start.

    Match is on lowercased IAST so `prati` matches `pratītyasamutpāda` (not
    `pratyaya` which would be a sandhi case beyond this heuristic). Diacritics
    matter: `su` matches `sukha` but NOT `sūrya` (because lowercased iast for
    sūrya begins with `sū` ≠ `su`).

    For Tibetan, normalized form (with spaces) matches against word-boundary.
    Single match — never chained. Empty string if no canonical upasarga
    starts the headword cleanly with at least 2 chars of remainder.
    """
    if not iast:
        return ""
    iast_low = iast.lower()
    # Sanskrit: continuous string (no internal space outside Tib).
    if " " not in norm:
        for u_iast, u_norm in skt_upasargas:
            if iast_low.startswith(u_iast) and len(iast_low) > len(u_iast) + 1:
                return u_norm
        return ""
    # Tibetan: word-boundary aware on normalized form.
    for _u_iast, u_norm in bo_upasargas:
        if norm == u_norm:
            continue
        if norm.startswith(u_norm + " "):
            return u_norm
    return ""


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
    parser.add_argument(
        "--upasargas", type=Path, default=UPASARGA_PATH_DEFAULT,
        help="Optional upasarga reference for single-prefix tagging "
             "(Phase 3.7 follow-up). Pass /dev/null to disable.",
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

    skt_upasargas, bo_upasargas = load_upasargas(args.upasargas)
    if skt_upasargas or bo_upasargas:
        print(f"Loaded upasargas from {args.upasargas}: "
              f"{len(skt_upasargas)} Sanskrit · {len(bo_upasargas)} Tibetan",
              file=sys.stderr)
    else:
        print(f"(No upasarga table at {args.upasargas}; emitting empty tags)",
              file=sys.stderr)

    pairs = collect_headwords(args.sources, args.jsonl)
    print(f"\nCollected {len(pairs):,} unique headwords", file=sys.stderr)

    # Sort by norm for binary-search-friendly client consumption.
    # Phase 3.7: append rank + upasarga columns.
    #   col 3 = rank (top-10K position, or 999999 long-tail)
    #   col 4 = upasarga norm if matched, else "" (empty string)
    LONG_TAIL_RANK = 999_999
    lines_list: list[str] = []
    n_tagged_skt = 0
    n_tagged_bo = 0
    for norm, iast in sorted(pairs.items()):
        rank = rank_table.get(norm, LONG_TAIL_RANK)
        upa = tag_upasarga(iast, norm, skt_upasargas, bo_upasargas) if skt_upasargas else ""
        if upa:
            if " " in norm:
                n_tagged_bo += 1
            else:
                n_tagged_skt += 1
        lines_list.append(f"{norm}\t{iast}\t{rank}\t{upa}\n")
    if skt_upasargas:
        print(f"  Tagged {n_tagged_skt:,} Sanskrit + {n_tagged_bo:,} Tibetan "
              f"headwords with upasarga", file=sys.stderr)
    text = "".join(lines_list).encode("utf-8")
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
