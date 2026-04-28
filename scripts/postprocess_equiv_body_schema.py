"""Fix spawn1 equiv-* JSONL where equivalent fields were placed directly under
`body` instead of `body.equivalents` (schema violation, blocks verify.py).

Affected dicts: bodkye-hamsa, hopkins-tsed, karashima-lotus, lin-4lang,
yogacara-index. Re-extracting from source would take hours; in-place
post-processing is reversible (run from JSONL backup) and idempotent.

Transformations:
  1. Schema-defined equiv fields living at body root
       body.{skt_iast, skt_slp1, tib_wylie, zh, ja, de, category, note}
     → body.equivalents.{...}

  2. Source-specific extras (not in body.equivalents schema) — wherever they
     ended up (body root or body.equivalents from a previous run)
       {skt_all, eng_all, tenses, div_bod, div_eng, tib_raw, tib_unicode, pinyin}
     → entry.source_meta.{...}

`body.ko` and `body.en` carry semantic ambiguity (full translation vs.
term-level equivalent). spawn1 likely meant term-level since they sit
alongside skt_iast/tib_wylie. We copy them into body.equivalents while
also keeping them at body root (schema allows both — `body.ko` empty is
"translation pending"). Phase 3 UI can disambiguate later.

Idempotent: re-running on already-fixed JSONL is a no-op.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# Schema-defined fields that belong inside body.equivalents.
EQUIV_SCHEMA_FIELDS: tuple[str, ...] = (
    "skt_iast", "skt_slp1", "tib_wylie", "zh", "ja", "de", "category", "note",
)

# Source-specific extras outside the schema → routed to entry.source_meta.
EQUIV_EXTRA_FIELDS: tuple[str, ...] = (
    "skt_all", "eng_all", "tenses", "div_bod", "div_eng",
    "tib_raw", "tib_unicode", "pinyin",
)

# Dual-meaning fields: copy into body.equivalents but also keep at body root.
EQUIV_DUAL_FIELDS: tuple[str, ...] = ("ko", "en")

# spawn1 dicts known to need the fix.
TARGET_SLUGS: tuple[str, ...] = (
    "equiv-bodkye-hamsa",
    "equiv-hopkins-tsed",
    "equiv-karashima-lotus",
    "equiv-lin-4lang",
    "equiv-yogacara-index",
)


def fix_entry(entry: dict) -> bool:
    """Mutate entry in place; return True iff something actually moved."""
    changed = False
    body = entry.get("body") or {}
    source_meta = entry.get("source_meta") or {}
    eq = dict(body.get("equivalents") or {})

    # (1) body root → body.equivalents for schema-defined equiv fields.
    for f in EQUIV_SCHEMA_FIELDS:
        if f in body:
            v = body.pop(f)
            changed = True
            if v and f not in eq:
                eq[f] = v
    for f in EQUIV_DUAL_FIELDS:
        v = body.get(f)
        if v and f not in eq:
            eq[f] = v
            changed = True

    # (2) Source-specific extras (anywhere) → entry.source_meta.
    for f in EQUIV_EXTRA_FIELDS:
        if f in body:
            v = body.pop(f)
            changed = True
            if v and f not in source_meta:
                source_meta[f] = v
        if f in eq:
            v = eq.pop(f)
            changed = True
            if v and f not in source_meta:
                source_meta[f] = v

    if eq:
        body["equivalents"] = eq
    entry["body"] = body
    if source_meta:
        entry["source_meta"] = source_meta
    return changed


def fix_file(path: Path) -> tuple[int, int]:
    """Rewrite `path` in place. Returns (entries_total, entries_modified)."""
    total = 0
    modified = 0
    tmp = path.with_suffix(path.suffix + ".tmp")
    with path.open(encoding="utf-8") as fin, tmp.open("w", encoding="utf-8") as fout:
        for line in fin:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            entry = json.loads(line)
            total += 1
            if fix_entry(entry):
                modified += 1
            fout.write(json.dumps(entry, ensure_ascii=False) + "\n")
    tmp.replace(path)
    return total, modified


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", maxsplit=1)[0])
    parser.add_argument("--jsonl", type=Path, default=Path("data/jsonl"))
    parser.add_argument("--slugs", nargs="*", default=list(TARGET_SLUGS))
    args = parser.parse_args()

    grand_total = 0
    grand_modified = 0
    for slug in args.slugs:
        path = args.jsonl / f"{slug}.jsonl"
        if not path.exists():
            print(f"  ! missing: {path}", file=sys.stderr)
            continue
        total, modified = fix_file(path)
        grand_total += total
        grand_modified += modified
        print(f"  {slug:30s}  {total:>8,} entries  · {modified:>8,} fixed", file=sys.stderr)

    print(f"\n✓ {grand_modified:,} of {grand_total:,} entries rewritten across {len(args.slugs)} dicts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
