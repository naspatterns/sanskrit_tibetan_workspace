#!/usr/bin/env python3
"""OCR + extract Bonwa Daijiten 梵和大辭典 (Ogiwara Unrai 荻原雲来 1979).

Source: 1666-page scanned PDF, Sanskrit-Japanese dictionary. Each entry:

    anya-bija-ja 他の種子より生じたる.
    anya-bhrta (n.) =anya-pusta.
    anya-mānasa (m.) [同上].

Pattern: lowercase Latin (+ diacritics + hyphens) headword + space +
Japanese definition with kanji/hiragana/katakana, often with bracketed PoS
markers like (m.), (n.), (f.). Two columns per page.

Note: lang=skt for output (Sanskrit headwords). Japanese def goes into
body.equivalents.note with "ja:" prefix (no dedicated ja field in schema).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.lib.transliterate import normalize  # noqa: E402
from scripts.ocr.lib import (  # noqa: E402
    PageOCR,
    assert_tools_available,
    ocr_pdf_parallel,
    page_count,
)

SRC_PDF = Path(
    "/Users/jibak/Library/CloudStorage/GoogleDrive-naspatterns@gmail.com/"
    "내 드라이브/haMsa CODE/Sanskrit_Tibetan_Reading_Tools/[DICS] SANSKRIT/梵和大辭典.pdf"
)
SLUG = "equiv-bonwa-daijiten"
OUT_META = ROOT / "data" / "sources" / SLUG / "meta.json"
OUT_JSONL = ROOT / "data" / "jsonl" / f"{SLUG}.jsonl"

# Headword: sequence of letters (incl IAST diacritics), hyphens, dots; minimum 2 chars
# Must start with a lowercase letter (or rarely uppercase for proper nouns)
HEAD_RE = re.compile(
    r"^([a-zA-ZāīūṛṝḷḹṃḥṅñṭḍṇśṣĀĪŪṚṜḶḸṂḤṄÑṬḌṆŚṢṆ]"
    r"[a-zA-ZāīūṛṝḷḹṃḥṅñṭḍṇśṣĀĪŪṚṜḶḸṂḤṄÑṬḌṆŚṢṆ\-\.]{1,60})"
    r"[\s　]+(.+)$"
)
# Page header: 'anya-bija-ja' or numeric only
PAGE_HEADER_RE = re.compile(r"^[a-zāīūṛṝḷḹṃḥṅñṭḍṇśṣ\-\.]+$")
# Pure-number footer
PAGE_NUM_RE = re.compile(r"^\d{1,4}$")
# Japanese chars (hiragana/katakana/kanji)
JP_RE = re.compile(r"[぀-ゟ゠-ヿ一-鿿]")


def is_jp_continuation(line: str) -> bool:
    """A continuation line is mostly Japanese, possibly with leading whitespace."""
    s = line.strip()
    if not s:
        return False
    # Pure-Japanese, OR Japanese-dominant
    jp_count = sum(1 for c in s if JP_RE.match(c))
    if jp_count == 0:
        return False
    return jp_count > 2  # at least 3 Japanese chars


def parse_page(page_ocr: PageOCR) -> list[dict]:
    entries: list[dict] = []
    current: dict | None = None
    seen_first = False  # skip headers until we see a real entry

    for line in page_ocr.text.splitlines():
        s = line.rstrip()
        stripped = s.strip()
        if not stripped:
            continue
        # Skip column markers
        if stripped.startswith("--- COL"):
            continue
        # Skip likely page headers (top of page) until first entry
        if not seen_first and PAGE_HEADER_RE.match(stripped):
            continue
        if PAGE_NUM_RE.match(stripped):
            continue

        m = HEAD_RE.match(s)
        if m:
            # Validate: rest must contain at least Japanese OR a bracket marker
            head = m.group(1).strip()
            rest = m.group(2).strip()
            # Filter very-likely garbage: headword too short (<3 chars usually noise except 'go', etc)
            # We allow 2+ chars
            # Reject if headword has no vowel and no hyphen (likely OCR)
            if (
                len(head) < 2
                or (not re.search(r"[aeiouāīūṛḷ]", head, re.I) and "-" not in head)
            ):
                continue
            if current is not None:
                entries.append(current)
            current = {
                "headword": head,
                "definition": [rest],
                "page": page_ocr.page,
                "conf": page_ocr.conf,
                "raw": s,
            }
            seen_first = True
            continue

        # Continuation
        if current is None:
            continue
        if is_jp_continuation(s):
            current["definition"].append(stripped)
            current["raw"] = (current["raw"] + " | " + stripped)[:500]
            continue

        # Else (latin-only continuation) — skip noise

    if current is not None:
        entries.append(current)
    return entries


def parse_pages(pages: list[PageOCR]) -> list[dict]:
    out = []
    for po in pages:
        out.extend(parse_page(po))
    return out


def clean_iast(s: str) -> str:
    s = s.strip().rstrip(",.;:")
    return re.sub(r"[\s　]+", " ", s)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--first", type=int, default=1)
    ap.add_argument("--last", type=int, default=None)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--psm", type=int, default=4)
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--columns", type=int, default=2)
    ap.add_argument("--langs", type=str, default="eng+san+jpn")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    assert_tools_available()
    if not SRC_PDF.exists():
        print(f"PDF not found: {SRC_PDF}", file=sys.stderr)
        return 1

    n_pages = page_count(SRC_PDF)
    last = args.last or n_pages
    pages = list(range(args.first, last + 1))
    print(
        f"Bonwa Daijiten: {n_pages} pages; OCRing {len(pages)} ({args.first}..{last}), "
        f"langs={args.langs}, cols={args.columns}",
        flush=True,
    )

    page_ocrs = ocr_pdf_parallel(
        slug=SLUG,
        pdf_path=SRC_PDF,
        pages=pages,
        langs=args.langs,
        psm=args.psm,
        dpi=args.dpi,
        workers=args.workers,
        columns=args.columns,
    )
    confs = [p.conf for p in page_ocrs if p.n_words > 0]
    if confs:
        print(
            f"OCR done. Pages: {len(page_ocrs)}, mean conf: {sum(confs)/len(confs):.1f}, "
            f"low (<70): {sum(1 for c in confs if c < 70)}",
            flush=True,
        )

    entries = parse_pages(page_ocrs)
    print(f"Parsed {len(entries):,} entries", flush=True)

    if args.no_write:
        for e in entries[:5]:
            print(f"  {e['headword']} → {' '.join(e['definition'])[:80]} (p{e['page']}, conf {e['conf']:.0f})")
        return 0

    OUT_META.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)

    meta = {
        "slug": SLUG,
        "name": "Bonwa Daijiten 梵和大辭典 (Ogiwara Unrai 荻原雲來 1979 reprint)",
        "lang": "skt",
        "tier": 2,
        "priority": 31,
        "role": "equivalents",
        "direction": "skt-to-ja",
        "license": "research-use",
        "source_path": "haMsa CODE/Sanskrit_Tibetan_Reading_Tools/[DICS] SANSKRIT/梵和大辭典.pdf",
        "extraction": {
            "method": "tesseract-ocr",
            "langs": args.langs,
            "psm": args.psm,
            "dpi": args.dpi,
            "columns": args.columns,
            "pages": [args.first, last],
        },
        "row_count": 0,
    }

    written = 0
    with OUT_JSONL.open("w", encoding="utf-8") as f:
        for i, e in enumerate(entries, 1):
            head = clean_iast(e["headword"])
            if not head or len(head) < 2:
                continue
            jp_def = " ".join(e["definition"]).strip()
            plain = f"{head}"
            if jp_def:
                plain += f" · ja: {jp_def[:200]}"
            if e["conf"] < 70:
                plain += f" · [OCR conf {e['conf']:.0f}]"

            row = {
                "id": f"{SLUG}-{i:06d}",
                "dict": SLUG,
                "headword": head,
                "headword_iast": head,
                "headword_norm": normalize(head),
                "lang": "skt",
                "tier": 2,
                "priority": 31,
                "role": "equivalents",
                "body": {
                    "plain": plain,
                    "equivalents": {
                        "skt_iast": head,
                        "tib_wylie": "",
                        "zh": "",
                        "ko": "",
                        "en": "",
                        "ja": jp_def[:280] if jp_def else "",
                        "category": "skt-jp",
                        "note": "Bonwa Daijiten 1979 OCR",
                    },
                },
                "license": "research-use",
                "source_meta": {
                    "page": e["page"],
                    "ocr_conf": round(e["conf"], 1),
                    "raw": e["raw"][:400],
                },
            }
            written += 1
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    meta["row_count"] = written
    OUT_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {written:,} JSONL rows → {OUT_JSONL}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
