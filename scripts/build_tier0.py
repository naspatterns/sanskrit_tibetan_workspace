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
        # Tier 0 = definition zone (Zone C/D). Skip equivalents/thesaurus —
        # those route to Zone B via equivalents.msgpack.zst. Without this
        # filter, Negi/Mvy/Hopkins-tsed/etc. show up in Zone C with empty
        # snippets (their bodies are cross-language mappings, not prose).
        if meta.get("role") in ("equivalents", "thesaurus"):
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
                # P0-3 (Phase 3.6) + Phase 4 fix (2026-05-08): cap snippet_medium
                # at 200 chars in tier0 (JSONL keeps full ≤500, full body
                # available via Phase 5 D1 Edge API `/api/entry/:id`).
                #
                # Phase 4 size budget: must fit at zstd level 19 within
                # Cloudflare 25 MiB single-file cap because fzstd 0.1.1 silently
                # misdecodes level-22 streams (see compression call below).
                # snippet_medium total raw was 46 MB at cap=350; cap=200 trims
                # to ~26 MB → fits at level 19 with margin.
                "snippet_medium": body.get("snippet_medium", "")[:200],
                # ko outlier cap — a handful of long-form dictionary entries
                # (e.g. Apte's 'a' definition) leaked 10-45K chars from v1
                # body.ko. Cap at 2000 chars to preserve typical translations
                # while bounding the worst case.
                "ko": ko[:2000],
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

    # Phase 4 fix (2026-05-08): use zstd level 19, NOT 22 — fzstd 0.1.1
    # silently misdecodes level-22 streams. The decompressed length matches
    # but the contents are corrupted (verified by SHA256 mismatch vs Python
    # `zstandard`), causing the JS msgpack decoder to explode with
    # "The type of key must be string or number but object" because the byte
    # misalignment shifts value-objects into key-positions. Python's
    # `zstandard` library decodes level-22 correctly, which masked the bug
    # at build time — it only surfaced in the live browser.
    #
    # To fit the Cloudflare Pages 25 MiB per-file limit at level 19, this
    # script also caps snippet_medium at 200 chars (was 350). Full body is
    # served by the Phase 5 Edge API at `/api/entry/:id`.
    raw, compressed = write_msgpack_zst(index, args.out, level=19, long_range=False)
    print(f"\n✓ Wrote {args.out}")
    print(f"  raw msgpack:  {raw/1024/1024:.1f} MB")
    print(f"  compressed:   {compressed/1024/1024:.1f} MB ({compressed/raw:.1%})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
