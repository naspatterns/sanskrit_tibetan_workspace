#!/usr/bin/env python3
"""OCR + extract Hirakawa Akira's Buddhist Chinese-Sanskrit Dictionary.

Source: 1506-page scanned PDF (Hirakawa 1997). Each entry:

    不退 avinivartanIya, avaivartika, aparihani, a-
    hani, akhinna, akheda, acyuta, acyuta-gamin, ...

Pattern: leading CJK headword followed by 1+ Sanskrit IAST equivalents
(comma-separated, may wrap to indented continuation lines).

Two columns per page; tesseract psm=4 reads them top-to-bottom in left
column, then top-to-bottom in right column.

Pipeline:
  1. ocr_pdf_parallel → cached per-page OCR text (data/ocr_cache/equiv-hirakawa)
  2. parse_pages → list of {zh, skt[], page, conf}
  3. write JSONL + meta.json

OCR confidence per row = page-level conf (we don't have per-entry granularity).
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
    "내 드라이브/haMsa CODE/Sanskrit_Tibetan_Reading_Tools/"
    "Hirakawa Akira-Buddhist-Chinese-Sanskrit-Dictionary.pdf"
)
SLUG = "equiv-hirakawa"
OUT_META = ROOT / "data" / "sources" / SLUG / "meta.json"
OUT_JSONL = ROOT / "data" / "jsonl" / f"{SLUG}.jsonl"

# CJK Unified Ideographs (BMP + Compat) — Hirakawa uses traditional Chinese
CJK_RANGE = r"一-鿿㐀-䶿豈-﫿"
HEAD_RE = re.compile(rf"^([{CJK_RANGE}]{{1,12}})[\s　]+(.+)$")
# Page header: "1 一(3)不" or "2 ⼀(2)中" — section/stroke marker
PAGE_HEADER_RE = re.compile(rf"^\d+\s+[{CJK_RANGE}⺀-⿟]+[（(]\d+[）)][{CJK_RANGE}]+$")
# Page footer: "— 52 —" or "9" alone
PAGE_FOOTER_RE = re.compile(r"^[—\-]\s*\d+\s*[—\-]$|^\d{1,4}$")
# Sanskrit-like fragment: latin letters, IAST diacritics, hyphens, periods
SKT_FRAG_RE = re.compile(r"[a-zA-ZāīūṛṝḷḹṃḥṅñṭḍṇśṣĀĪŪṚṜḶḸṂḤṄÑṬḌṆŚṢ\-\.\*~]")
# Strip leading non-alpha noise from Sanskrit text (quotes, leading bullets)
LEAD_NOISE_RE = re.compile(r'^[\s"“”‘’"\'\.\*　]+')


def is_sanskrit_continuation(line: str) -> bool:
    """Continuation lines: pure latin/IAST words, comma/hyphen separated.

    Heuristic: contains a Sanskrit-looking fragment, AND has no CJK or other
    non-Latin scripts (Devanagari, Hangul, Kana — these are OCR misreads of
    CJK and indicate a fresh entry, not a continuation).
    """
    s = line.strip()
    if not s:
        return False
    cjk = sum(1 for c in s if "一" <= c <= "鿿" or "㐀" <= c <= "䶿")
    devan = sum(1 for c in s if "ऀ" <= c <= "ॿ")
    hangul = sum(1 for c in s if "가" <= c <= "힯")
    kana = sum(1 for c in s if "぀" <= c <= "ヿ")
    if cjk + devan + hangul + kana > 0:
        return False
    latin = sum(1 for c in s if c.isascii() and c.isalpha())
    iast = sum(1 for c in s if c in "āīūṛṝḷḹṃḥṅñṭḍṇśṣĀĪŪṚṜḶḸṂḤṄÑṬḌṆŚṢ")
    return (latin + iast) > 3


def split_sanskrit_terms(blob: str) -> list[str]:
    """Split a Sanskrit blob like 'akheda, niyati-pata; abc-def' into individual terms.

    Drops empty / pure-punctuation pieces.
    """
    blob = blob.strip()
    # Replace common OCR noise
    blob = blob.replace("，", ",").replace("；", ";").replace("。", ".")
    # Strip leading/trailing punctuation per term
    pieces = re.split(r"[;,]+", blob)
    out = []
    for p in pieces:
        p = LEAD_NOISE_RE.sub("", p).strip()
        # Trailing punct
        p = re.sub(r'[\s\.\*"　]+$', "", p)
        if not p:
            continue
        # Must have at least one alphabetic char
        if not re.search(r"[a-zA-Zāīūṛṝḷḹṃḥṅñṭḍṇśṣ]", p):
            continue
        # Filter pure-noise short tokens
        if len(p) < 2:
            continue
        out.append(p)
    return out


def parse_page(page_ocr: PageOCR) -> list[dict]:
    """Parse one OCR'd page → list of entry dicts.

    Each entry: {zh: str, skt: [str,...], page: int, conf: float, raw: str}
    """
    entries: list[dict] = []
    current: dict | None = None
    raw_buffer: list[str] = []

    for line in page_ocr.text.splitlines():
        s = line.rstrip()
        if not s.strip():
            continue
        # Skip page headers/footers
        if PAGE_HEADER_RE.match(s) or PAGE_FOOTER_RE.match(s.strip()):
            continue

        m = HEAD_RE.match(s)
        if m:
            # Flush prev
            if current is not None and current["skt"]:
                entries.append(current)
            zh, rest = m.group(1), m.group(2)
            # Sanity: rest must look like Sanskrit (latin chars dominant)
            if not SKT_FRAG_RE.search(rest):
                # Skip — likely noise, e.g. CJK-only line that matched HEAD_RE pattern
                current = None
                continue
            skt_terms = split_sanskrit_terms(rest)
            current = {
                "zh": zh,
                "skt": skt_terms,
                "page": page_ocr.page,
                "conf": page_ocr.conf,
                "raw": s,
            }
            raw_buffer = [s]
        else:
            # Possibly a continuation line for current entry
            if current is None:
                continue
            if is_sanskrit_continuation(s):
                more = split_sanskrit_terms(s)
                if more:
                    # Merge with last term if it ended in hyphenation marker
                    # (real hyphen "-" or OCR-confused "=").
                    last = current["skt"][-1] if current["skt"] else ""
                    if last and last.endswith(("-", "=")):
                        current["skt"][-1] = last.rstrip("-=") + more[0]
                        more = more[1:]
                    current["skt"].extend(more)
                    raw_buffer.append(s)
                    current["raw"] = " | ".join(raw_buffer[:5])

    if current is not None and current["skt"]:
        entries.append(current)

    return entries


def parse_pages(pages: list[PageOCR]) -> list[dict]:
    all_entries = []
    for po in pages:
        all_entries.extend(parse_page(po))
    return all_entries


def ocr_normalize_iast(s: str) -> str:
    """Light cleanup for OCR'd IAST: normalize quotes, strip trailing punct.

    NB: We do NOT auto-correct missing diacritics — that requires a lemma
    list lookup. Raw OCR is preserved in source_meta.raw.
    """
    s = s.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"[\s　]+", " ", s).strip()
    return s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--first", type=int, default=1, help="first page (1-indexed)")
    ap.add_argument("--last", type=int, default=None, help="last page (None = all)")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--psm", type=int, default=4)
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--columns", type=int, default=2, help="image cols (Hirakawa = 2)")
    ap.add_argument("--langs", type=str, default="chi_tra+eng+san")
    ap.add_argument(
        "--no-write",
        action="store_true",
        help="OCR + parse only, skip JSONL write (for sample / quality eval)",
    )
    args = ap.parse_args()

    assert_tools_available()
    if not SRC_PDF.exists():
        print(f"ERROR: PDF not found: {SRC_PDF}", file=sys.stderr)
        return 1

    n_pages = page_count(SRC_PDF)
    last = args.last or n_pages
    pages_to_do = list(range(args.first, last + 1))
    print(
        f"Hirakawa: {n_pages} total pages; OCRing {len(pages_to_do)} "
        f"({args.first}..{last}) with {args.workers} workers, langs={args.langs}",
        flush=True,
    )

    page_ocrs = ocr_pdf_parallel(
        slug=SLUG,
        pdf_path=SRC_PDF,
        pages=pages_to_do,
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
    print(f"  with ≥1 Skt term: {sum(1 for e in entries if e['skt']):,}", flush=True)

    if args.no_write:
        # Print sample
        print("\n--- sample 5 entries ---")
        for e in entries[:5]:
            print(f"  {e['zh']} → {e['skt'][:3]}... (page {e['page']}, conf {e['conf']:.0f})")
        return 0

    OUT_META.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)

    meta = {
        "slug": SLUG,
        "name": "Buddhist Chinese-Sanskrit Dictionary (Hirakawa Akira 平川彰 1997)",
        "lang": "zh",
        "tier": 2,
        "priority": 30,
        "role": "equivalents",
        "direction": "zh-to-skt",
        "license": "research-use",
        "source_path": "haMsa CODE/Sanskrit_Tibetan_Reading_Tools/Hirakawa Akira-Buddhist-Chinese-Sanskrit-Dictionary.pdf",
        "extraction": {
            "method": "tesseract-ocr",
            "langs": args.langs,
            "psm": args.psm,
            "dpi": args.dpi,
            "pages": [args.first, last],
        },
        "row_count": len(entries),
    }
    OUT_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote meta → {OUT_META}", flush=True)

    written = 0
    with OUT_JSONL.open("w", encoding="utf-8") as f:
        for i, e in enumerate(entries, 1):
            zh = e["zh"]
            skt_list = [ocr_normalize_iast(s) for s in e["skt"]]
            skt_list = [s for s in skt_list if s]
            if not skt_list:
                continue
            primary_skt = skt_list[0]
            skt_joined = "; ".join(skt_list)

            plain_parts = [zh, f"Skt: {skt_joined}"]
            if e["conf"] < 70:
                plain_parts.append(f"[OCR conf {e['conf']:.0f}]")
            plain = " · ".join(plain_parts)

            row = {
                "id": f"{SLUG}-{i:06d}",
                "dict": SLUG,
                "headword": zh,
                "headword_iast": primary_skt,
                "headword_norm": normalize(primary_skt),
                "lang": "zh",
                "tier": 2,
                "priority": 30,
                "role": "equivalents",
                "body": {
                    "plain": plain,
                    "equivalents": {
                        "skt_iast": skt_joined,
                        "tib_wylie": "",
                        "zh": zh,
                        "ko": "",
                        "en": "",
                        "category": "buddhist",
                        "note": "Hirakawa 1997 OCR (raw)",
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

    print(f"Wrote {written:,} JSONL rows → {OUT_JSONL}", flush=True)
    # Update row_count in meta
    meta["row_count"] = written
    OUT_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
