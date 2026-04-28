"""Build the Tier 0 in-memory index for top-10K headwords.

For each headword in `top10k.txt`, gather every entry across search-enabled
dicts, priority-sort them, and ship pre-rendered short/medium snippets so
the client can render zero-to-first-result in <50ms with no parsing.

Output: `public/indices/tier0.msgpack.zst` — target size ~30MB compressed.

Optionally merges `data/translations.jsonl` (written by `translate_batch`)
so Phase 2 En→Ko additions flow into the hot cache.

Entry schema (long key names — zstd collapses duplicate keys anyway, so
wire savings from single-letter keys are <1% and Phase 3 legibility wins):
    {
      "iast": "dharma",                # display headword
      "entries": [
        {
          "dict": "apte-sanskrit-english",
          "short": "Apte",
          "priority": 1,
          "tier": 1,
          "id": "apte-sanskrit-english-000042",
          "snippet_short": "…",
          "snippet_medium": "…",
          "ko": "…",                   # empty string if no translation
          "target_lang": "en",         # so UI can flag "Korean", "German" etc.
        },
        …
      ]
    }
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import msgpack
import zstandard as zstd
from tqdm import tqdm

from scripts.lib.io import (
    iter_jsonl,
    iter_slugs_by_priority,
    load_top10k,
    write_msgpack_zst,
)


def load_translations(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return {
        row["entry_id"]: row["ko"].strip()
        for row in iter_jsonl(path)
        if row.get("entry_id") and row.get("ko", "").strip()
    }


def build_index(
    top10k: list[str],
    sources: Path,
    jsonl_dir: Path,
    translations: dict[str, str],
) -> dict:
    top_set = set(top10k)
    buckets: dict[str, list[dict]] = defaultdict(list)
    iast_by_hw: dict[str, str] = {}

    # iter_slugs_by_priority gives us priority-ASC order, which the IAST-
    # picker below relies on (first-seen wins → Apte/MW spelling sticks).
    prev_priority = -1
    for slug_dir, meta in tqdm(
        iter_slugs_by_priority(sources), desc="dicts", unit="dict"
    ):
        assert meta["priority"] >= prev_priority, "iter_slugs_by_priority must be ASC"
        prev_priority = meta["priority"]

        if meta.get("exclude_from_search"):
            continue
        jsonl_path = jsonl_dir / f"{meta['slug']}.jsonl"
        if not jsonl_path.exists():
            continue

        for entry in iter_jsonl(jsonl_path):
            hw = entry.get("headword_norm")
            if hw not in top_set:
                continue

            iast_by_hw.setdefault(hw, entry.get("headword_iast", hw))

            body = entry.get("body", {})
            existing_ko = (body.get("ko") or "").strip()
            ko = existing_ko or translations.get(entry["id"], "")
            buckets[hw].append({
                "dict": meta["slug"],
                # equiv-* meta omits short_name/target_lang; fall back to
                # slug / lang so they still sort + render in the UI without
                # special-casing (B1 fix, 2026-04-29).
                "short": meta.get("short_name", meta["slug"]),
                "priority": meta["priority"],
                "tier": meta["tier"],
                "id": entry["id"],
                "snippet_short": body.get("snippet_short", ""),
                "snippet_medium": body.get("snippet_medium", ""),
                "ko": ko,
                "target_lang": meta.get("target_lang", meta.get("lang", "en")),
            })

    index: dict[str, dict] = {}
    for hw in top10k:
        if hw not in buckets:
            continue
        entries = sorted(buckets[hw], key=lambda e: (e["priority"], e["dict"]))
        index[hw] = {
            "iast": iast_by_hw.get(hw, hw),
            "entries": entries,
        }

    return index


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, default=Path("data/sources"))
    parser.add_argument("--jsonl", type=Path, default=Path("data/jsonl"))
    parser.add_argument("--top10k", type=Path, default=Path("data/reports/top10k.txt"))
    parser.add_argument("--translations", type=Path,
                        default=Path("data/translations.jsonl"))
    parser.add_argument("--out", type=Path,
                        default=Path("public/indices/tier0.msgpack.zst"))
    args = parser.parse_args()

    top10k = load_top10k(args.top10k)
    print(f"Loaded {len(top10k):,} top headwords", file=sys.stderr)

    translations = load_translations(args.translations)
    if translations:
        print(f"Loaded {len(translations):,} translations from {args.translations}",
              file=sys.stderr)
    else:
        print(f"(No translations at {args.translations}; using v1 body.ko only)",
              file=sys.stderr)

    index = build_index(top10k, args.sources, args.jsonl, translations)
    total_entries = sum(len(v["entries"]) for v in index.values())
    print(f"\nBuilt Tier 0 for {len(index):,} headwords "
          f"({total_entries:,} entries, avg {total_entries/max(1,len(index)):.1f}/hw)",
          file=sys.stderr)

    raw, compressed = write_msgpack_zst(index, args.out)
    print(f"\n✓ Wrote {args.out}")
    print(f"  raw msgpack:  {raw/1024/1024:.1f} MB")
    print(f"  compressed:   {compressed/1024/1024:.1f} MB ({compressed/raw:.1%})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
