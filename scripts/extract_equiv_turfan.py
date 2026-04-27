#!/usr/bin/env python3
"""OCR + extract Sanskrit-Wörterbuch der Buddhistischen Texte aus den Turfan-Funden.

Source: 2 PDFs (vol 1 696p · vol 2 612p), Sanskrit-German dictionary of
Turfan Buddhist Sanskrit (Bechert et al.). 2 columns, dense entries:

    abhi-präya
    F SHT 811 (Abhidharma) c A4 ///tam tasya
    ~am Almji.... .e///.

    abhi-pre (°-pra-i) meinen, im Sinn haben;
    abs.: in Hinsicht auf; ...

Pattern: bold lowercase Sanskrit IAST headword on own line, followed by
German definition with extensive citations.

Note: tesseract `eng+san+deu` — German config preserves umlauts but
maps long-vowel diacritics → umlauts (ā → ä). Raw OCR preserved in
source_meta.raw for user post-processing.
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
    load_cached_pages,
    ocr_pdf_parallel,
    page_count,
)

PDF_PATHS = {
    "v1": Path(
        "/Users/jibak/Library/CloudStorage/GoogleDrive-naspatterns@gmail.com/"
        "내 드라이브/haMsa CODE/Sanskrit_Tibetan_Reading_Tools/[DICS] SANSKRIT/"
        "sanskrit-wortebuch 1 (Turfan).pdf"
    ),
    "v2": Path(
        "/Users/jibak/Library/CloudStorage/GoogleDrive-naspatterns@gmail.com/"
        "내 드라이브/haMsa CODE/Sanskrit_Tibetan_Reading_Tools/[DICS] SANSKRIT/"
        "sanskrit-wortebuch 2 k-dh (Turfan).pdf"
    ),
}
SLUG = "equiv-turfan-skt-de"
OUT_META = ROOT / "data" / "sources" / SLUG / "meta.json"
OUT_JSONL = ROOT / "data" / "jsonl" / f"{SLUG}.jsonl"

# Headword: lowercase + IAST + hyphen + dot + degree (°)
HEAD_CHARS = (
    r"a-zA-ZāīūṛṝḷḹṃḥṅñṭḍṇśṣĀĪŪṚṜḶḸṂḤṄÑṬḌṆŚṢ"
    r"äöüßÄÖÜ"  # German umlauts (OCR maps long vowels here)
)
HEAD_RE = re.compile(
    rf"^([a-z{HEAD_CHARS}\-\.°]{{3,80}})\s*$"
)
# Headword line ends without trailing prose (often just headword on own line)
# But also: some entries have headword + (annotation) then prose; let's also catch:
HEAD_INLINE_RE = re.compile(
    rf"^([a-z{HEAD_CHARS}\-\.°]{{3,80}})\s+(\([^)]+\))?\s*([nfmvVN]\.?|pp\.|pron\.|adj\.|adv\.|m\.|f\.|n\.|num\.).*$"
)
DE_CITATION_RE = re.compile(r"^[FCM]\s+SHT\s+\d|^[mn]\.nom\.sg\.|^abs\.|^vgl\.")


def is_german_continuation(line: str) -> bool:
    """Continuation lines: start with whitespace OR contain German prose markers."""
    s = line.strip()
    if not s:
        return False
    # Lines that don't look like a new headword
    # Headwords are short single-word-ish; continuations often have spaces + prose
    # Heuristic: if line contains a sequence of 5+ regular German/Latin words, it's continuation
    if len(s) > 50:
        return True
    # Or starts with citation pattern
    if DE_CITATION_RE.match(s):
        return True
    # Or has multiple words
    if s.count(" ") >= 3:
        return True
    return False


def parse_page(page_ocr: PageOCR) -> list[dict]:
    entries: list[dict] = []
    current: dict | None = None

    for line in page_ocr.text.splitlines():
        s = line.rstrip()
        stripped = s.strip()
        if not stripped:
            continue
        if stripped.startswith("--- COL"):
            continue
        # Skip page numbers / running headers
        if re.match(r"^\d{1,4}$", stripped):
            continue
        # Skip running header lines that look like "abhi-priya  122  abhi-..."
        if re.match(rf"^[a-z{HEAD_CHARS}\-\.°]{{3,30}}\s+\d{{1,4}}(\s+[a-z{HEAD_CHARS}\-\.°]+)?$", stripped):
            continue

        # Try standalone headword
        m = HEAD_RE.match(stripped)
        if m and not is_german_continuation(stripped):
            head = m.group(1).strip(" -.")
            if len(head) >= 3:
                if current is not None:
                    entries.append(current)
                current = {
                    "headword": head,
                    "definition": [],
                    "page": page_ocr.page,
                    "conf": page_ocr.conf,
                    "raw": stripped,
                }
                continue

        # Inline headword (e.g. "abc-def n. ...")
        m2 = HEAD_INLINE_RE.match(stripped)
        if m2:
            head = m2.group(1).strip(" -.")
            if len(head) >= 3:
                if current is not None:
                    entries.append(current)
                current = {
                    "headword": head,
                    "definition": [stripped],
                    "page": page_ocr.page,
                    "conf": page_ocr.conf,
                    "raw": stripped,
                }
                continue

        # Continuation — append to current
        if current is not None:
            current["definition"].append(stripped)
            current["raw"] = (current["raw"] + " | " + stripped)[:500]

    if current is not None:
        entries.append(current)
    return entries


def parse_pages(pages: list[PageOCR]) -> list[dict]:
    out = []
    for po in pages:
        out.extend(parse_page(po))
    return out


def normalize_iast_umlauts(s: str) -> str:
    """OCR maps Sanskrit long vowels to German umlauts (ā→ä, etc.) via
    the deu language pack. Map back conservatively in the headword (not body)."""
    return (
        s.replace("ä", "ā")
        .replace("ö", "ō")  # not standard IAST but possible OCR artifact
        .replace("ü", "ū")
        .replace("Ä", "Ā")
        .replace("Ö", "Ō")
        .replace("Ü", "Ū")
        .replace("ß", "ss")
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--first", type=int, default=1)
    ap.add_argument("--last", type=int, default=None)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--psm", type=int, default=4)
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--columns", type=int, default=2)
    ap.add_argument("--langs", type=str, default="eng+san+deu")
    ap.add_argument("--vol", choices=["v1", "v2", "both"], default="both")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--from-cache", action="store_true", help="parse only, skip OCR")
    args = ap.parse_args()

    vols = [args.vol] if args.vol != "both" else ["v1", "v2"]

    all_entries: list[dict] = []
    for vol in vols:
        slug_per_vol = f"{SLUG}-{vol}"
        if args.from_cache:
            page_ocrs = load_cached_pages(slug_per_vol)
            print(f"Turfan {vol}: loaded {len(page_ocrs)} cached pages", flush=True)
        else:
            assert_tools_available()
            pdf_path = PDF_PATHS[vol]
            if not pdf_path.exists():
                print(f"PDF not found: {pdf_path}", file=sys.stderr)
                return 1
            n_pages = page_count(pdf_path)
            last = args.last or n_pages
            pages = list(range(args.first, last + 1))
            print(
                f"Turfan {vol}: {n_pages} pages; OCRing {len(pages)} ({args.first}..{last}), "
                f"langs={args.langs}, cols={args.columns}",
                flush=True,
            )
            page_ocrs = ocr_pdf_parallel(
                slug=slug_per_vol,
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
            print(
                f"  {vol} OCR done. mean conf: {sum(confs)/len(confs):.1f}, "
                f"low (<70): {sum(1 for c in confs if c < 70)}",
                flush=True,
            )
        ent = parse_pages(page_ocrs)
        for e in ent:
            e["vol"] = vol
        all_entries.extend(ent)

    print(f"Parsed {len(all_entries):,} total entries", flush=True)

    if args.no_write:
        for e in all_entries[:5]:
            d = " ".join(e["definition"])[:60]
            print(f"  [{e['vol']}] {e['headword']} → {d} (p{e['page']}, conf {e['conf']:.0f})")
        return 0

    OUT_META.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)

    meta = {
        "slug": SLUG,
        "name": "Sanskrit-Wörterbuch der buddhistischen Texte aus den Turfan-Funden (Bechert et al. 1973-)",
        "lang": "skt",
        "tier": 2,
        "priority": 33,
        "role": "equivalents",
        "direction": "skt-to-de",
        "license": "research-use",
        "source_paths": [
            "haMsa CODE/Sanskrit_Tibetan_Reading_Tools/[DICS] SANSKRIT/sanskrit-wortebuch 1 (Turfan).pdf",
            "haMsa CODE/Sanskrit_Tibetan_Reading_Tools/[DICS] SANSKRIT/sanskrit-wortebuch 2 k-dh (Turfan).pdf",
        ],
        "extraction": {
            "method": "tesseract-ocr",
            "langs": args.langs,
            "psm": args.psm,
            "dpi": args.dpi,
            "columns": args.columns,
        },
        "row_count": 0,
    }

    written = 0
    with OUT_JSONL.open("w", encoding="utf-8") as f:
        for i, e in enumerate(all_entries, 1):
            head = normalize_iast_umlauts(e["headword"]).strip(" -.")
            if not head or len(head) < 3:
                continue
            de_def = " ".join(e["definition"]).strip()
            plain = head
            if de_def:
                plain += f" · de: {de_def[:200]}"
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
                "priority": 33,
                "role": "equivalents",
                "body": {
                    "plain": plain,
                    "equivalents": {
                        "skt_iast": head,
                        "tib_wylie": "",
                        "zh": "",
                        "ko": "",
                        "en": "",
                        "category": "skt-de-turfan",
                        "note": (
                            f"de: {de_def[:280]}"
                            if de_def
                            else "Turfan SWB OCR (de def empty)"
                        ),
                    },
                },
                "license": "research-use",
                "source_meta": {
                    "page": e["page"],
                    "vol": e["vol"],
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
