"""Apply Phase 2b + Phase 3.7 Korean translations to JSONL `body.ko` in-place.

Reads one or more translation JSONL files (each with `{entry_id, ko}` rows)
and merges them into `data/jsonl/<slug>.jsonl`:

  - For each row whose id matches a translation:
      * If `body.ko` is empty/missing → fill with translation
      * If `body.ko` already has content → leave existing v1 ko alone (DE/FR/LA
        carry-over wins; we do NOT re-translate over those — that's P0-2 EU)
  - When ko is filled, recompute `reverse.ko[]` via lib/reverse_tokens

JSONL files are gitignored and regenerable from v1 sqlite + this script, so
in-place mutation is safe (idempotent).

Usage:
    uv run python -m scripts.apply_translations_to_jsonl \\
        --translations data/translations.jsonl data/translations-en-extended.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from scripts.lib.io import iter_slug_dirs, load_meta
from scripts.lib.reverse_tokens import extract_ko_tokens


def load_translations(paths: list[Path]) -> dict[str, str]:
    """Merge translations from multiple JSONL files.

    Later paths override earlier ones for the same entry_id. We expect no
    overlap (translations.jsonl = top-10K, translations-en-extended.jsonl =
    top-10K..50K), but the override semantics make re-runs deterministic.
    """
    out: dict[str, str] = {}
    for p in paths:
        if not p.exists():
            print(f"WARN: {p} does not exist, skipping", file=sys.stderr)
            continue
        n = 0
        with p.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                eid = row.get("entry_id")
                ko = (row.get("ko") or "").strip()
                if eid and ko:
                    out[eid] = ko
                    n += 1
        print(f"  Loaded {n:,} translations from {p.name}", file=sys.stderr)
    return out


def apply_to_jsonl(
    jsonl_path: Path,
    translations: dict[str, str],
) -> tuple[int, int, int]:
    """Apply translations to one JSONL file in place.

    Returns (total_rows, ko_added, ko_already_present_skipped).
    """
    total = 0
    added = 0
    skipped_existing = 0

    # Read all rows first (avoid in-place truncation issues), then write.
    rows: list[dict] = []
    with jsonl_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                # Preserve the line as-is; can't update it
                rows.append({"_raw": line})
                continue
            rows.append(row)

    # Pass 2: mutate
    for row in rows:
        if "_raw" in row:
            continue
        total += 1
        eid = row.get("id")
        if not eid or eid not in translations:
            continue

        body = row.setdefault("body", {})
        existing = (body.get("ko") or "").strip()
        if existing:
            skipped_existing += 1
            continue

        ko = translations[eid]
        body["ko"] = ko

        # Recompute reverse.ko[] from new body.ko
        reverse = row.setdefault("reverse", {})
        reverse["ko"] = extract_ko_tokens(ko)

        added += 1

    if added == 0 and skipped_existing == 0:
        return total, 0, 0

    # Write back atomically (write to .tmp, rename)
    tmp = jsonl_path.with_suffix(jsonl_path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for row in rows:
            if "_raw" in row:
                f.write(row["_raw"] + "\n")
            else:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    tmp.replace(jsonl_path)
    return total, added, skipped_existing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--translations",
        type=Path,
        nargs="+",
        default=[
            Path("data/translations.jsonl"),
            Path("data/translations-en-extended.jsonl"),
        ],
        help="One or more translation JSONL files (entry_id + ko per row)",
    )
    parser.add_argument("--sources", type=Path, default=Path("data/sources"))
    parser.add_argument("--jsonl", type=Path, default=Path("data/jsonl"))
    args = parser.parse_args()

    print(f"Loading translations from {len(args.translations)} files…",
          file=sys.stderr)
    translations = load_translations(args.translations)
    print(f"\nTotal unique translations to apply: {len(translations):,}",
          file=sys.stderr)
    if not translations:
        print("No translations loaded; nothing to do.", file=sys.stderr)
        return 0

    # Walk every dict; only those whose ids overlap will see changes.
    per_dict: list[tuple[str, int, int, int]] = []
    grand_total = 0
    grand_added = 0
    grand_skipped = 0

    print("\nApplying to JSONL files…", file=sys.stderr)
    for slug_dir in iter_slug_dirs(args.sources):
        meta = load_meta(slug_dir)
        slug = meta["slug"]
        jsonl_path = args.jsonl / f"{slug}.jsonl"
        if not jsonl_path.exists():
            continue
        total, added, skipped = apply_to_jsonl(jsonl_path, translations)
        if added > 0 or skipped > 0:
            per_dict.append((slug, total, added, skipped))
        grand_total += total
        grand_added += added
        grand_skipped += skipped

    # Sort by additions DESC so the report is useful
    per_dict.sort(key=lambda r: -r[2])

    print(f"\nApplied {grand_added:,} new ko translations across "
          f"{len(per_dict)} dicts ({grand_skipped:,} skipped — "
          f"existing v1 ko present).", file=sys.stderr)
    print(f"Walked {grand_total:,} rows total.", file=sys.stderr)
    print()
    print("Top 20 dicts by ko additions:", file=sys.stderr)
    for slug, total, added, skipped in per_dict[:20]:
        cov = (added + skipped) / total * 100 if total else 0
        print(f"  {slug:50s}  +{added:>5,}  (skipped {skipped:>4,})  "
              f"of {total:>6,}  match={cov:.1f}%", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
