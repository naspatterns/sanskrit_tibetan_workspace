"""Build `reverse_meta.msgpack.zst` — entry_id → [iast, dict, snippet_short].

P0-1 (Phase 3.6): the reverse search UI in `+page.svelte:359-371` currently
renders raw entry_ids when the user types an English/Korean gloss. This is
useless to readers — they cannot tell *which Sanskrit/Tibetan word* matches
their query. To fix, we build a small lookup index of metadata for every
entry_id that appears in `reverse_en` or `reverse_ko`, and update the UI
to render headword_iast + dict_slug + snippet_short per hit.

Schema:
    {
      "<entry_id>": ["<iast>", "<dict_slug>", "<snippet_short>"],
      ...
    }

Compressed target ~10 MB. Subset of all 3.81M entry ids — only those
referenced by reverse_en or reverse_ko (priority-bounded heap top-100).

Usage:
    uv run python -m scripts.build_reverse_meta
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import msgpack
import zstandard as zstd

from scripts.lib.io import iter_jsonl, iter_slug_dirs, load_meta, write_msgpack_zst


UI_TOP_N = 30  # +page.svelte:359 renders top-30 reverse hits


def collect_referenced_ids(
    reverse_en_path: Path,
    reverse_ko_path: Path,
) -> set[str]:
    """Decode reverse_en + reverse_ko and collect entry_ids referenced.

    reverse_en/ko stores up to 100 entry_ids per token (priority-bounded
    heap), but the UI only renders top-30 (`+page.svelte:359`). We collect
    metadata only for those top-30 entries; deeper reverse hits beyond
    UI_TOP_N would require Phase 5 D1 Edge API lazy fetch anyway.
    """
    ids: set[str] = set()
    dctx = zstd.ZstdDecompressor()
    for path, label in [(reverse_en_path, "reverse_en"), (reverse_ko_path, "reverse_ko")]:
        if not path.exists():
            print(f"WARN: {path} missing, skipping {label}", file=sys.stderr)
            continue
        raw = dctx.decompress(path.read_bytes())
        idx = msgpack.unpackb(raw, raw=False, strict_map_key=False)
        before = len(ids)
        for token, entry_ids in idx.items():
            for eid in entry_ids[:UI_TOP_N]:
                ids.add(eid)
        print(f"  {label}: +{len(ids)-before:,} unique ids "
              f"(top-{UI_TOP_N} of {len(idx):,} tokens)",
              file=sys.stderr)
    return ids


def build_meta_for_ids(
    referenced: set[str],
    sources: Path,
    jsonl_dir: Path,
) -> dict:
    """Walk all JSONL once, picking out entries whose id is referenced.

    Output schema (compact, designed to fit Cloudflare 25 MiB single-file cap):
      {
        "dicts": [<slug>, <slug>, ...],   # dict idx → slug, ~148 strings
        "ids": {
          "<entry_id>": [<iast>, <dict_idx>],  # 2-element array
          ...
        }
      }

    snippet_short omitted — UI shows iast + dict + then user clicks through
    to see the full entry (Phase 5 D1 Edge API for full body). Trade-off
    for fitting under 25 MiB without R2.
    """
    # First pass: enumerate dict slugs in priority-ASC order so the index
    # matches build_tier0 order (deterministic).
    slug_to_idx: dict[str, int] = {}
    dict_list: list[str] = []
    for slug_dir in iter_slug_dirs(sources):
        slug = load_meta(slug_dir)["slug"]
        slug_to_idx[slug] = len(dict_list)
        dict_list.append(slug)

    ids_meta: dict[str, list] = {}
    found = 0
    for slug_dir in iter_slug_dirs(sources):
        slug_meta = load_meta(slug_dir)
        slug = slug_meta["slug"]
        path = jsonl_dir / f"{slug}.jsonl"
        if not path.exists():
            continue
        for entry in iter_jsonl(path):
            eid = entry.get("id")
            if not eid or eid not in referenced:
                continue
            iast = entry.get("headword_iast") or entry.get("headword") or "?"
            ids_meta[eid] = [iast, slug_to_idx[slug]]
            found += 1
    print(f"\nResolved {found:,} / {len(referenced):,} referenced ids",
          file=sys.stderr)
    return {"dicts": dict_list, "ids": ids_meta}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, default=Path("data/sources"))
    parser.add_argument("--jsonl", type=Path, default=Path("data/jsonl"))
    parser.add_argument("--reverse-en", type=Path,
                        default=Path("public/indices/reverse_en.msgpack.zst"))
    parser.add_argument("--reverse-ko", type=Path,
                        default=Path("public/indices/reverse_ko.msgpack.zst"))
    parser.add_argument("--out", type=Path,
                        default=Path("public/indices/reverse_meta.msgpack.zst"))
    args = parser.parse_args()

    print("Collecting referenced entry_ids from reverse indices…", file=sys.stderr)
    referenced = collect_referenced_ids(args.reverse_en, args.reverse_ko)
    print(f"\nTotal unique referenced ids: {len(referenced):,}", file=sys.stderr)

    print("\nResolving id → [iast, dict, snippet_short] from JSONL…", file=sys.stderr)
    meta = build_meta_for_ids(referenced, args.sources, args.jsonl)

    print("\nWriting compressed index…", file=sys.stderr)
    raw, compressed = write_msgpack_zst(meta, args.out, level=22, long_range=True)
    print(f"\n✓ Wrote {args.out}", file=sys.stderr)
    print(f"  raw msgpack:  {raw/1024/1024:.1f} MB", file=sys.stderr)
    print(f"  compressed:   {compressed/1024/1024:.1f} MB ({compressed/raw:.1%})",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
