#!/usr/bin/env python3
"""OCR + extract Great Tibetan-Chinese Dictionary 藏漢大辭典 (dKon-mchog 2004).

Source: scanned PDF, 2 columns. Each entry:

    བཀའ་བཐམ། (1)ཕྱག་དམས་མཚམ། དམ་ཕྱག
    印, 戳记: བཀའ་རྒྱ་བཀའ་བྲམ་འབྱར་མ།
    ...

Pattern: bold Tibetan headword (terminated by ། shad) followed by
Tibetan synonyms/numbered glosses, then Chinese definition with kanji.
Multi-word headwords are common; entries can span multiple paragraphs.

Strategy: paragraph-based parsing. For each paragraph:
  - Take leading Tibetan text up to first Chinese character as headword
  - Take Chinese text as definition
  - Skip paragraphs without both
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ocr.lib import (  # noqa: E402
    PageOCR,
    assert_tools_available,
    load_cached_pages,
    ocr_pdf_parallel,
    page_count,
)

SRC_PDF = Path(
    "/Users/jibak/Library/CloudStorage/GoogleDrive-naspatterns@gmail.com/"
    "내 드라이브/haMsa CODE/Sanskrit_Tibetan_Reading_Tools/[#haMsa TIBETAN]/"
    "[DICS] TIBETAN/Tib_Chn_Dict.pdf"
)
SLUG = "equiv-tib-chn-great"
OUT_META = ROOT / "data" / "sources" / SLUG / "meta.json"
OUT_JSONL = ROOT / "data" / "jsonl" / f"{SLUG}.jsonl"

TIB_RE = re.compile(r"[ༀ-࿿]")  # U+0F00..U+0FFF + extensions
CJK_RE = re.compile(r"[一-鿿㐀-䶿豈-﫿]")
PAGE_NUM_RE = re.compile(r"^\s*\d{1,4}\s*$")


def split_tib_chn(text: str) -> tuple[str, str]:
    """Split a paragraph into (Tibetan-prefix, Chinese-rest).

    Walks chars; once we encounter a CJK char, everything from there is
    Chinese (incl punctuation between CJK words).
    """
    cjk_start = None
    for i, c in enumerate(text):
        if CJK_RE.match(c):
            cjk_start = i
            break
    if cjk_start is None:
        return text.strip(), ""
    return text[:cjk_start].strip(), text[cjk_start:].strip()


def parse_page(page_ocr: PageOCR) -> list[dict]:
    """Paragraph-based: split text on blank lines, then split each para
    into Tibetan headword + Chinese definition.

    Discard paragraphs without both Tibetan and Chinese content.
    """
    entries: list[dict] = []
    raw = page_ocr.text
    # Normalize column markers to paragraph break
    raw = raw.replace("--- COL", "\n\n--- COL")
    paragraphs = re.split(r"\n\s*\n", raw)
    for para in paragraphs:
        para = para.strip()
        if not para or para.startswith("---"):
            continue
        # Skip page numbers / very short noise
        if len(para) < 5:
            continue
        # Collapse line breaks within a para
        flat = re.sub(r"\s+", " ", para)
        tib, chn = split_tib_chn(flat)
        # Quality gate
        if not tib or not chn:
            continue
        if len(TIB_RE.findall(tib)) < 3:  # too little Tibetan content
            continue
        if len(CJK_RE.findall(chn)) < 2:  # too little Chinese
            continue
        # Headword = the part of tib before first shad+space or first ; or first whitespace longer than 2
        # Simpler: take first segment up to first `།` (Tibetan shad)
        first_shad = tib.find("།")
        if first_shad >= 0 and first_shad < 60:
            head = tib[: first_shad + 1].strip()
            tib_rest = tib[first_shad + 1 :].strip()
        else:
            head = tib[:40].strip()
            tib_rest = tib[40:].strip()

        entries.append({
            "head": head,
            "tib_rest": tib_rest,
            "chn": chn,
            "page": page_ocr.page,
            "conf": page_ocr.conf,
            "raw": flat[:400],
        })
    return entries


def parse_pages(pages: list[PageOCR]) -> list[dict]:
    out = []
    for po in pages:
        out.extend(parse_page(po))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--first", type=int, default=1)
    ap.add_argument("--last", type=int, default=None)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--psm", type=int, default=4)
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--columns", type=int, default=2)
    ap.add_argument("--langs", type=str, default="bod+chi_sim+chi_tra")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument(
        "--from-cache",
        action="store_true",
        help="Parse only — read all cached pages, skip OCR (fast, partial)",
    )
    args = ap.parse_args()

    if args.from_cache:
        page_ocrs = load_cached_pages(SLUG)
        print(f"Loaded {len(page_ocrs)} cached pages (no OCR)", flush=True)
    else:
        assert_tools_available()
        if not SRC_PDF.exists():
            print(f"PDF not found: {SRC_PDF}", file=sys.stderr)
            return 1

        n_pages = page_count(SRC_PDF)
        last = args.last or n_pages
        pages = list(range(args.first, last + 1))
        print(
            f"Tib-Chn Dict: {n_pages} pages; OCRing {len(pages)} ({args.first}..{last}), "
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
            print(f"  {e['head'][:30]} → {e['chn'][:50]} (p{e['page']}, conf {e['conf']:.0f})")
        return 0

    OUT_META.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)

    meta = {
        "slug": SLUG,
        "name": "Great Tibetan-Chinese Dictionary 藏漢大辭典 (dKon-mchog tshul-khrims 2004)",
        "lang": "bo",
        "tier": 2,
        "priority": 32,
        "role": "equivalents",
        "direction": "tib-to-zh",
        "license": "research-use",
        "source_path": "haMsa CODE/Sanskrit_Tibetan_Reading_Tools/[#haMsa TIBETAN]/[DICS] TIBETAN/Tib_Chn_Dict.pdf",
        "extraction": {
            "method": "tesseract-ocr",
            "langs": args.langs,
            "psm": args.psm,
            "dpi": args.dpi,
            "columns": args.columns,
            "pages_processed": [p.page for p in page_ocrs[:1]] + [p.page for p in page_ocrs[-1:]] if page_ocrs else [],
            "n_pages_processed": len(page_ocrs),
            "from_cache": args.from_cache,
        },
        "row_count": 0,
    }

    written = 0
    with OUT_JSONL.open("w", encoding="utf-8") as f:
        for i, e in enumerate(entries, 1):
            head = e["head"]
            chn = e["chn"]
            tib_rest = e["tib_rest"]
            plain_parts = [head, f"Zh: {chn[:200]}"]
            if tib_rest:
                plain_parts.insert(1, f"Tib syn: {tib_rest[:120]}")
            if e["conf"] < 70:
                plain_parts.append(f"[OCR conf {e['conf']:.0f}]")
            plain = " · ".join(plain_parts)

            row = {
                "id": f"{SLUG}-{i:06d}",
                "dict": SLUG,
                "headword": head,
                "headword_iast": head,  # Tibetan unicode; meta says lang=bo, IAST = Wylie typically
                "headword_norm": head.lower(),
                "lang": "bo",
                "tier": 2,
                "priority": 32,
                "role": "equivalents",
                "body": {
                    "plain": plain,
                    "equivalents": {
                        "skt_iast": "",
                        "tib_wylie": "",  # Wylie conversion deferred (raw Tibetan unicode in headword)
                        "zh": chn[:300],
                        "ko": "",
                        "en": "",
                        "category": "tibetan-chinese",
                        "note": (
                            f"tib syn: {tib_rest[:200]}"
                            if tib_rest
                            else "Tib unicode unconverted (Wylie deferred)"
                        ),
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
