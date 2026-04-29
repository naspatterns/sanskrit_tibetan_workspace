"""Compute headword frequency ranking across all Phase 1 JSONL.

Ranking: each occurrence of a headword in a dict contributes a priority-weighted
score. A hit in Apte (priority 1) outweighs a hit in a priority-89 dict. This
proxies "how prominent is this word in the v2 corpus", which is a reasonable
stand-in for actual query popularity until real logs exist.

Excludes `exclude_from_search` (Heritage Declension) dicts from the count
since their headwords aren't searchable. Per D10c (option c, 2026-04-28),
also excludes role=equivalents/thesaurus dicts — Zone B is a separate
channel and must not bias top-10K headword selection for Zone C/D.

Output:
  - data/reports/top10k.txt — one headword_norm per line, rank order.
  - data/reports/frequency.json — full rank table (headword_norm → score).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from tqdm import tqdm

from scripts.lib.io import iter_jsonl, iter_slugs_by_priority


def priority_weight(priority: int) -> float:
    """Higher priority (lower number) → higher weight. 1→1.0, 50→0.5, 99→0.01."""
    return max(0.01, (100 - priority) / 100)


def compute_scores(
    sources: Path,
    jsonl_dir: Path,
    lang_filter: str | None = None,
) -> dict[str, float]:
    scores: dict[str, float] = defaultdict(float)

    for _slug_dir, meta in tqdm(
        iter_slugs_by_priority(sources), desc="dicts", unit="dict"
    ):
        if meta.get("exclude_from_search"):
            continue
        if meta.get("role") in ("equivalents", "thesaurus"):
            continue
        # Phase 3.3 (D-Tib10K) — restrict scoring to a single source language
        # so we can build per-language Tier 0 (e.g. tier0-bo).
        if lang_filter and meta.get("lang") != lang_filter:
            continue
        jsonl_path = jsonl_dir / f"{meta['slug']}.jsonl"
        if not jsonl_path.exists():
            continue
        weight = priority_weight(meta["priority"])
        for entry in iter_jsonl(jsonl_path):
            hw = entry.get("headword_norm")
            if hw:
                scores[hw] += weight

    return dict(scores)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, default=Path("data/sources"))
    parser.add_argument("--jsonl", type=Path, default=Path("data/jsonl"))
    parser.add_argument(
        "--out-top", type=Path,
        default=Path("data/reports/top10k.txt"),
    )
    parser.add_argument(
        "--out-full", type=Path, default=None,
        help="Optional: write full ranking (all scored headwords) as JSON",
    )
    parser.add_argument("--top-n", type=int, default=10_000)
    parser.add_argument(
        "--lang-filter",
        choices=["skt", "bo", "pi", "zh"],
        default=None,
        help="Restrict scoring to dicts with meta.lang == this value "
        "(used for Phase 3.3 per-language Tier 0 — e.g. --lang-filter bo "
        "→ data/reports/top10k_bo.txt).",
    )
    args = parser.parse_args()

    args.out_top.parent.mkdir(parents=True, exist_ok=True)

    scores = compute_scores(args.sources, args.jsonl, lang_filter=args.lang_filter)
    print(f"Scored {len(scores):,} unique headwords", file=sys.stderr)

    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))

    top = ranked[: args.top_n]
    args.out_top.write_text(
        "\n".join(hw for hw, _ in top) + "\n",
        encoding="utf-8",
    )
    print(f"✓ Wrote top-{args.top_n:,} → {args.out_top}")

    if args.out_full is not None:
        args.out_full.write_text(
            json.dumps({hw: round(score, 3) for hw, score in ranked},
                       ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"✓ Wrote full ranking → {args.out_full}")

    print(f"\nTop 20 headwords:")
    for hw, score in ranked[:20]:
        print(f"  {hw:30s}  {score:8.2f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
