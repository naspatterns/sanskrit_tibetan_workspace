#!/usr/bin/env python3
"""OCR + extract Amarakośa Nāmaliṅgānuśāsana (TSS 1914-17, 4 vols).

Source: 1121-page scanned PDF (Trivandrum Sanskrit Series 38/43/51/52),
Sanskrit thesaurus by Amarasiṃha with Kṣīrasvāmin + Sarvānanda commentaries.
Pure Devanagari script.

Strategy: OCR all pages → archival raw text per page (one JSONL row per page).
Verse-level structured extraction (synonym groups) deferred — requires
Sanskrit NLP (verse boundary detection, lemma identification, topic grouping)
which is beyond OCR scope.

Output is `role: "thesaurus"` per ARCHITECTURE.md §11.8.2 — Amarakośa is a
synonym dictionary, not cross-language equivalents per se.
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

PDF_PATHS = [
    Path(
        "/Users/jibak/Library/CloudStorage/GoogleDrive-naspatterns@gmail.com/"
        "내 드라이브/haMsa CODE/Sanskrit_Tibetan_Reading_Tools/Amarakoza/"
        f"Ama914{n}__Amarasimha_Namalinganusasana_2COMMs-Ksir-Sarv_{n}_191"
        f"{4 if n in (1,2) else 7}_TSS_{['38','43','51','52'][n-1]}.pdf"
    )
    for n in (1, 2, 3, 4)
]
SLUG_BASE = "equiv-amarakoza"
SLUG_PER_VOL = lambda v: f"{SLUG_BASE}-v{v}"  # noqa: E731

OUT_META = ROOT / "data" / "sources" / SLUG_BASE / "meta.json"
OUT_JSONL = ROOT / "data" / "jsonl" / f"{SLUG_BASE}.jsonl"

# Devanagari verse delimiter (full-stop / two stops)
VERSE_END_RE = re.compile(r"॥|।।")
# Skip lines that are just numbers (page footers like "१७" = 17 in Devanagari)
DEV_NUM = re.compile(r"^[०-९]{1,4}$")


def parse_pages(pages: list[PageOCR], vol: int) -> list[dict]:
    """One row per OCR'd page (archival raw text). Future NLP can re-parse."""
    rows = []
    for po in pages:
        text = po.text.strip()
        if not text or len(text) < 20:
            continue
        # Drop lines that are likely page numbers
        cleaned = []
        for line in text.splitlines():
            s = line.strip()
            if not s or DEV_NUM.match(s):
                continue
            cleaned.append(s)
        if not cleaned:
            continue
        rows.append({
            "vol": vol,
            "page": po.page,
            "conf": po.conf,
            "text": "\n".join(cleaned),
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--first", type=int, default=1)
    ap.add_argument("--last", type=int, default=None)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--psm", type=int, default=4)
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--columns", type=int, default=1)  # single column
    ap.add_argument("--langs", type=str, default="san+eng")
    ap.add_argument("--vol", type=int, choices=[1, 2, 3, 4, 0], default=0,
                    help="0 = all 4 vols; otherwise single vol")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--from-cache", action="store_true")
    args = ap.parse_args()

    vols = [args.vol] if args.vol else [1, 2, 3, 4]
    all_rows: list[dict] = []
    for vol in vols:
        slug = SLUG_PER_VOL(vol)
        if args.from_cache:
            page_ocrs = load_cached_pages(slug)
            print(f"vol{vol}: loaded {len(page_ocrs)} cached pages", flush=True)
        else:
            assert_tools_available()
            pdf_path = PDF_PATHS[vol - 1]
            if not pdf_path.exists():
                print(f"PDF not found: {pdf_path}", file=sys.stderr)
                continue
            n_pages = page_count(pdf_path)
            last = args.last or n_pages
            pages = list(range(args.first, last + 1))
            print(
                f"vol{vol} ({pdf_path.name[:40]}): {n_pages}p; OCR {len(pages)} "
                f"({args.first}..{last}), langs={args.langs}, psm={args.psm}",
                flush=True,
            )
            page_ocrs = ocr_pdf_parallel(
                slug=slug,
                pdf_path=pdf_path,
                pages=pages,
                langs=args.langs,
                psm=args.psm,
                dpi=args.dpi,
                workers=args.workers,
                columns=args.columns,
            )
        confs = [p.conf for p in page_ocrs if p.n_words > 0]
        if confs:
            print(f"  vol{vol} mean conf: {sum(confs)/len(confs):.1f}", flush=True)
        all_rows.extend(parse_pages(page_ocrs, vol))

    print(f"Parsed {len(all_rows):,} rows (1 per page)", flush=True)
    if args.no_write:
        for r in all_rows[:3]:
            print(f"  vol{r['vol']} p{r['page']} conf{r['conf']:.0f}: {r['text'][:100]!r}")
        return 0

    OUT_META.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)

    meta = {
        "slug": SLUG_BASE,
        "name": "Amarakośa Nāmaliṅgānuśāsana w/ Kṣīrasvāmin + Sarvānanda commentaries (TSS 1914-17, 4 vols)",
        "lang": "skt",
        "tier": 3,
        "priority": 49,
        "role": "thesaurus",
        "direction": "skt-thesaurus",
        "license": "public-domain",
        "source_paths": [str(p.relative_to(p.parents[2])) for p in PDF_PATHS],
        "extraction": {
            "method": "tesseract-ocr (raw text dump)",
            "langs": args.langs,
            "psm": args.psm,
            "dpi": args.dpi,
            "note": "Per-page raw OCR. Verse-level synonym groups NOT extracted (requires Sanskrit NLP).",
        },
        "row_count": 0,
    }

    written = 0
    with OUT_JSONL.open("w", encoding="utf-8") as f:
        for i, r in enumerate(all_rows, 1):
            text = r["text"]
            row = {
                "id": f"{SLUG_BASE}-v{r['vol']}-{r['page']:04d}",
                "dict": SLUG_BASE,
                "headword": f"vol{r['vol']} p{r['page']}",
                "headword_iast": f"amarakoza-v{r['vol']}-p{r['page']}",
                "headword_norm": f"amarakoza-v{r['vol']}-p{r['page']}",
                "lang": "skt",
                "tier": 3,
                "priority": 49,
                "role": "thesaurus",
                "body": {
                    "plain": text[:1500],
                    "raw": text[:5000],
                },
                "license": "public-domain",
                "source_meta": {
                    "vol": r["vol"],
                    "page": r["page"],
                    "ocr_conf": round(r["conf"], 1),
                    "structure": "page-raw (verse-level NLP deferred)",
                },
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            written += 1

    meta["row_count"] = written
    OUT_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {written:,} JSONL rows → {OUT_JSONL}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
