#!/usr/bin/env python3
"""Migrate Bonwa (ja) + Turfan (de) note prefix → dedicated body.equivalents fields.

Before: body.equivalents.note = "ja: 後手に縛られた."
After:  body.equivalents.ja   = "後手に縛られた."
        body.equivalents.note = "Bonwa Daijiten OCR" (or original meta)

Same for Turfan: "de: ..." prefix → body.equivalents.de field.
Requires schema.json with body.equivalents.{ja, de} fields.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def migrate_jsonl(slug: str, prefix: str, dest_field: str, default_note: str) -> tuple[int, int]:
    """Return (total, migrated)."""
    path = ROOT / "data" / "jsonl" / f"{slug}.jsonl"
    if not path.exists():
        print(f"SKIP: {path} not found", file=sys.stderr)
        return 0, 0

    n_total = 0
    n_migrated = 0
    out: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        n_total += 1
        row = json.loads(line)
        eq = row.get("body", {}).get("equivalents")
        if not eq:
            out.append(json.dumps(row, ensure_ascii=False))
            continue
        note = eq.get("note", "")
        if note.startswith(prefix):
            value = note[len(prefix):].strip()
            eq[dest_field] = value
            eq["note"] = default_note
            n_migrated += 1
        out.append(json.dumps(row, ensure_ascii=False))

    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return n_total, n_migrated


def main() -> int:
    print("Migrating Bonwa Daijiten (ja prefix → body.equivalents.ja) ...")
    n_total, n_mig = migrate_jsonl(
        slug="equiv-bonwa-daijiten",
        prefix="ja: ",
        dest_field="ja",
        default_note="Bonwa Daijiten 1979 OCR",
    )
    print(f"  → {n_mig:,}/{n_total:,} migrated")

    print("Migrating Turfan SWB (de prefix → body.equivalents.de) ...")
    n_total, n_mig = migrate_jsonl(
        slug="equiv-turfan-skt-de",
        prefix="de: ",
        dest_field="de",
        default_note="Turfan SWB OCR (eng+san+deu, ä→ā normalized in headword)",
    )
    print(f"  → {n_mig:,}/{n_total:,} migrated")

    return 0


if __name__ == "__main__":
    sys.exit(main())
