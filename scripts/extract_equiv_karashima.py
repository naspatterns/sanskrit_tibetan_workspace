#!/usr/bin/env python3
"""Extract Karashima's Glossary of Kumārajīva's Lotus Sutra translation.

Format per entry (variable lines):

    寶舍                                         ← Chinese headword (1-6 CJK chars)
    (bǎo shè)                                    ← pinyin in parens
    "a jewelled dwelling"                        ← English meaning in quotes
    not found at 《漢語大詞典》 ...               ← citations (skip)
    3b12.或見菩薩 ……… 千萬億種 栴檀寶舍       ← Lotus Sūtra citations
    K.13.15.vihāra- ... ratnāmaya~;              ← Kern-Nanjio Sanskrit equiv
    Dharmarakṣa: Z.65a19....                     ← variant translations

We extract:
  - headword (CJK)
  - pinyin
  - English meaning (between curly/straight quotes)
  - Sanskrit equivalent (regex on K.<n>.<n>.<word>)

Output:
  data/sources/equiv-karashima-lotus/meta.json
  data/jsonl/equiv-karashima-lotus.jsonl
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.lib.reverse_tokens import extract_en_tokens

SRC_PDF = Path(
    "/Users/jibak/Library/CloudStorage/GoogleDrive-naspatterns@gmail.com/"
    "내 드라이브/haMsa CODE/Sanskrit_Tibetan_Reading_Tools/Karashima 라집역 연화경 glossary.pdf"
)
SLUG = "equiv-karashima-lotus"
OUT_META = ROOT / "data" / "sources" / SLUG / "meta.json"
OUT_JSONL = ROOT / "data" / "jsonl" / f"{SLUG}.jsonl"

# CJK Unified Ideographs only (no spaces, no parens)
CJK_RE = re.compile(r"[㐀-鿿豈-﫿]+")
PINYIN_RE = re.compile(r"^\(([^)]+)\)\s*$")
ENGLISH_QUOTE_RE = re.compile(r"^[\"“”](.+)[\"“”]\s*$")
# K.<page>.<line>.<sanskrit_word>~ or -; also O., Pk., D1., etc.
SKT_REF_RE = re.compile(
    r"(?:K|O|Pk|D\d?|R\d?|Cdv?)\.\d+(?:\.\d+)?\.([ -ɏḀ-ỿ a-zA-Z\(\)\-~,]+?)(?:[;,]|$)"
)
PAGE_NUM_RE = re.compile(r"^\d{1,4}$")
ENTRY_HEADER_RE = re.compile(r"^[㐀-鿿豈-﫿]{1,6}$")  # 1-6 CJK chars only


def is_pure_cjk_short(line: str) -> bool:
    """Pure CJK header line, 1-6 chars (typical headword)."""
    s = line.strip()
    if not s:
        return False
    return bool(ENTRY_HEADER_RE.match(s))


def extract_pinyin(line: str) -> str | None:
    s = line.strip()
    m = PINYIN_RE.match(s)
    if not m:
        return None
    val = m.group(1).strip()
    # Skip ones that are clearly citations like "(法華經)"
    if CJK_RE.search(val):
        return None
    return val


def extract_quoted_english(line: str) -> str | None:
    s = line.strip()
    m = ENGLISH_QUOTE_RE.match(s)
    if m:
        return m.group(1).strip()
    return None


def extract_sanskrit(line: str) -> list[str]:
    """Find Sanskrit equivalents in a citation line."""
    s = line.strip()
    out = []
    for m in SKT_REF_RE.finditer(s):
        cand = m.group(1).strip().rstrip("~-., ")
        # Filter: must contain IAST diacritic OR be lowercase Latin word (~5+ chars)
        if not cand:
            continue
        if any(c in cand for c in "āīūṛṝḷḹṃṁḥṅñṭḍṇśṣ"):
            out.append(cand)
        elif cand.islower() and len(cand) >= 4 and " " not in cand:
            out.append(cand)
    return out


def parse_pdf() -> list[dict]:
    entries: list[dict] = []
    current: dict | None = None
    skip_until_after = 30  # Skip first ~30 pages of intro/abbreviations

    with pdfplumber.open(str(SRC_PDF)) as pdf:
        n_pages = len(pdf.pages)
        for pi, page in enumerate(pdf.pages):
            if pi + 1 < skip_until_after:
                continue
            text = page.extract_text() or ""
            for raw in text.split("\n"):
                line = raw.strip()
                if not line:
                    continue
                if PAGE_NUM_RE.match(line):
                    continue

                # Detect new entry header (pure CJK, 1-6 chars)
                if is_pure_cjk_short(line):
                    # Flush previous
                    if current is not None:
                        entries.append(current)
                    current = {
                        "headword": line,
                        "pinyin": "",
                        "english": "",
                        "sanskrit": [],
                        "raw_lines": [],
                        "page": pi + 1,
                    }
                    continue

                if current is None:
                    continue

                # pinyin?
                py = extract_pinyin(line)
                if py and not current["pinyin"]:
                    current["pinyin"] = py
                    continue

                # english quoted?
                eng = extract_quoted_english(line)
                if eng and not current["english"]:
                    current["english"] = eng
                    continue

                # sanskrit?
                skts = extract_sanskrit(line)
                if skts:
                    for s in skts:
                        if s not in current["sanskrit"]:
                            current["sanskrit"].append(s)

                current["raw_lines"].append(line)

            if (pi + 1) % 100 == 0:
                print(f"  page {pi+1}/{n_pages}, entries so far: {len(entries):,}", flush=True)

    if current is not None:
        entries.append(current)
    return entries


def main() -> int:
    print(f"Opening {SRC_PDF.name} ...", flush=True)
    OUT_META.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)

    entries = parse_pdf()
    print(f"Parsed {len(entries):,} headword entries", flush=True)

    # Filter: must have at least pinyin or sanskrit (else likely noise)
    valid = [e for e in entries if e["pinyin"] or e["sanskrit"] or e["english"]]
    print(f"With pinyin/skt/eng: {len(valid):,}", flush=True)

    meta = {
        "slug": SLUG,
        "name": "A Glossary of Kumārajīva's Lotus Sutra Translation (Karashima 妙法蓮華經詞典)",
        "lang": "zh",
        "tier": 2,
        "priority": 32,
        "role": "equivalents",
        "direction": "zh-to-skt",
        "license": "CC-BY-SA-4.0",
        "source_path": str(SRC_PDF.relative_to(SRC_PDF.parents[2])),
        "row_count": len(valid),
    }
    OUT_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    written = 0
    with OUT_JSONL.open("w", encoding="utf-8") as f:
        for i, e in enumerate(valid, 1):
            zh = e["headword"]
            pinyin = e["pinyin"]
            eng = e["english"]
            skt_list = e["sanskrit"]
            skt_joined = "; ".join(skt_list)

            parts = [zh]
            if pinyin:
                parts.append(f"({pinyin})")
            if eng:
                parts.append(f'"{eng}"')
            if skt_joined:
                parts.append(f"[skt] {skt_joined}")
            plain = " · ".join(parts)

            primary_skt = skt_list[0] if skt_list else ""

            row = {
                "id": f"{SLUG}-{i:06d}",
                "dict": SLUG,
                "headword": zh,
                "headword_iast": primary_skt if primary_skt else zh,
                "headword_norm": zh.lower(),
                "lang": "zh",
                "tier": 2,
                "priority": 32,
                "role": "equivalents",
                "body": {
                    "plain": plain,
                    "skt_iast": skt_joined,
                    "tib_wylie": "",
                    "zh": zh,
                    "ko": "",
                    "en": eng,
                    "category": "lotus-sutra-glossary",
                    "note": "Kumārajīva translation glossary (Karashima 2001)",
                    "raw": " | ".join(e["raw_lines"][:6])[:500],
                    "pinyin": pinyin,
                    "skt_all": skt_list,
                },
                "reverse": {
                    "en": extract_en_tokens(eng) if eng else [],
                    "ko": [],
                },
                "source_meta": {"page": e["page"]},
                "license": meta["license"],
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            written += 1

    print(f"Wrote {written:,} JSONL rows → {OUT_JSONL}", flush=True)
    print(f"Meta: {OUT_META}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
