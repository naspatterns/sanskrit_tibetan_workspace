#!/usr/bin/env python3
"""Tib_Chn JSONL post-process: Tibetan Unicode headword → standard EWTS Wylie.

Reads existing equiv-tib-chn-great.jsonl, populates body.equivalents.tib_wylie
(currently "") with Wylie transliteration. Also updates headword_iast (was set
to Tibetan unicode) to Wylie for proper search index integration.

Standard EWTS via pyewts — root-letter aware, full stack handling.
The Tibetan unicode original is always preserved in `headword`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.lib.transliterate import normalize, tibetan_to_wylie as to_wylie  # noqa: E402

JSONL_PATH = ROOT / "data" / "jsonl" / "equiv-tib-chn-great.jsonl"
META_PATH = ROOT / "data" / "sources" / "equiv-tib-chn-great" / "meta.json"


def main() -> int:
    if not JSONL_PATH.exists():
        print(f"ERROR: {JSONL_PATH} not found — run extract_equiv_tibchn first", file=sys.stderr)
        return 1

    n_total = 0
    n_with_wylie = 0
    out_lines: list[str] = []

    for line in JSONL_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        n_total += 1
        row = json.loads(line)

        head = row.get("headword", "")
        wylie = to_wylie(head) if head else ""

        if wylie:
            n_with_wylie += 1
            row["headword_iast"] = wylie
            row["headword_norm"] = normalize(wylie)
            row.setdefault("body", {}).setdefault("equivalents", {})
            row["body"]["equivalents"]["tib_wylie"] = wylie
            note = row["body"]["equivalents"].get("note", "")
            if "Tib unicode unconverted" in note or "root-letter not detected" in note:
                row["body"]["equivalents"]["note"] = "Wylie = EWTS (pyewts)"
        else:
            # Lone shad / garbage OCR: schema requires headword_iast >= 1 char,
            # so we can't blank. Fall back to headword passthrough (matches the
            # pre-fix behavior for these rows).
            if not row.get("headword_iast"):
                row["headword_iast"] = head
                row["headword_norm"] = normalize(head)

        out_lines.append(json.dumps(row, ensure_ascii=False))

    JSONL_PATH.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"Updated {JSONL_PATH.name}: {n_with_wylie:,}/{n_total:,} rows have Wylie", flush=True)

    # Update meta
    meta = json.loads(META_PATH.read_text())
    meta["postprocess"] = {
        "wylie_converter": "pyewts",
        "wylie_kind": "standard-ewts (root-letter aware, stack-aware)",
        "rows_with_wylie": n_with_wylie,
    }
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated meta: {META_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
