#!/usr/bin/env python3
"""Extract 常用漢藏梵英佛學術語 (Common Chinese-Tibetan-Sanskrit-English
Buddhist Terminology), Lin Chung-an 2008.

Each row roughly: <num?> <chinese> <tibetan-unicode> <sanskrit-iast> <english>
English may wrap to multiple lines (no CJK, no Sanskrit diacritic).
Tibetan portion contains (cid:NNN) glyph references (font missing) — keep
raw; Wylie conversion handled downstream.

Output:
  data/sources/equiv-lin-4lang/meta.json
  data/jsonl/equiv-lin-4lang.jsonl
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
    "내 드라이브/haMsa CODE/Sanskrit_Tibetan_Reading_Tools/[#haMsa TIBETAN]/"
    "상용한장범영불학술어_2008.pdf"
)
SLUG = "equiv-lin-4lang"
OUT_META = ROOT / "data" / "sources" / SLUG / "meta.json"
OUT_JSONL = ROOT / "data" / "jsonl" / f"{SLUG}.jsonl"

CJK_RE = re.compile(r"[㐀-鿿豈-﫿]+")
TIB_UNI_RE = re.compile(r"[ༀ-࿿]+")  # Tibetan Unicode block
CID_RE = re.compile(r"\(cid:\d+\)")
IAST_DIACRITIC = "āīūṛṝḷḹṃṁḥṅñṭḍṇśṣĀĪŪṚṜḶḸṂṀḤṄÑṬḌṆŚṢ"
PAGE_NUM_RE = re.compile(r"^\d{1,4}$")


def has_cjk(s: str) -> bool:
    return bool(CJK_RE.search(s))


def has_tib(s: str) -> bool:
    """Has Tibetan Unicode or (cid:NNN) glyphs (font fallback)."""
    return bool(TIB_UNI_RE.search(s) or CID_RE.search(s))


def is_pure_english_continuation(line: str) -> bool:
    """Line that's purely lowercase Latin words (continuation of English)."""
    s = line.strip()
    if not s:
        return False
    if has_cjk(s) or has_tib(s):
        return False
    # No Sanskrit diacritics
    if any(c in s for c in IAST_DIACRITIC):
        return False
    # Mostly lowercase letters/spaces
    if not re.match(r"^[a-zA-Z][a-zA-Z\s\-,;:.()/\d]*$", s):
        return False
    return True


def find_sanskrit_chunk(s: str, after_idx: int) -> tuple[str, int] | None:
    """Find a contiguous Sanskrit IAST run starting at/after index.

    Returns (skt_word, end_idx) or None.
    """
    # Skip whitespace
    while after_idx < len(s) and s[after_idx].isspace():
        after_idx += 1
    if after_idx >= len(s):
        return None
    # Sanskrit IAST: lowercase Latin + diacritics + hyphen, no whitespace
    end = after_idx
    while end < len(s):
        c = s[end]
        if c.isalpha() or c in IAST_DIACRITIC or c in "-":
            end += 1
        else:
            break
    if end == after_idx:
        return None
    chunk = s[after_idx:end]
    # Must contain a diacritic OR be at least 4 chars (sanskrit-like)
    if not (any(c in chunk for c in IAST_DIACRITIC) or (len(chunk) >= 5 and chunk.islower())):
        return None
    return chunk, end


def parse_line(line: str) -> dict | None:
    """Try to parse a 4-lang line into {chinese, tibetan, sanskrit, english}."""
    s = line.strip()
    if not s:
        return None
    # Strip leading numerals like "1 ", "12 ", "a "
    s2 = re.sub(r"^[\dabcdef]+\s+", "", s)
    cjk_match = CJK_RE.search(s2)
    if not cjk_match:
        return None
    chinese = cjk_match.group(0)
    cjk_end = cjk_match.end()
    rest = s2[cjk_end:].strip()

    # Tibetan portion: from start until first Sanskrit-IAST run
    # Find Sanskrit-IAST chunk in rest
    found = None
    for i in range(len(rest)):
        if rest[i].isspace():
            continue
        # Check if this position starts a Sanskrit IAST word
        sk = find_sanskrit_chunk(rest, i)
        if sk:
            # But only if there's Tibetan content before it
            tib_part = rest[:i].strip()
            if tib_part and (has_tib(tib_part) or i > 2):
                found = (sk[0], i, sk[1])
                break
    if not found:
        # No Sanskrit found; whole rest is Tibetan + English
        return {
            "chinese": chinese,
            "tibetan": rest if has_tib(rest) else "",
            "sanskrit": "",
            "english": "" if has_tib(rest) else rest,
        }
    skt_word, skt_start, skt_end = found
    tibetan = rest[:skt_start].strip()
    english = rest[skt_end:].strip()
    return {
        "chinese": chinese,
        "tibetan": tibetan,
        "sanskrit": skt_word,
        "english": english,
    }


def parse_pdf() -> list[dict]:
    entries: list[dict] = []
    pending: dict | None = None
    skip_until = 4  # Skip TOC

    with pdfplumber.open(str(SRC_PDF)) as pdf:
        n = len(pdf.pages)
        for pi, page in enumerate(pdf.pages):
            if pi + 1 < skip_until:
                continue
            text = page.extract_text() or ""
            for raw in text.split("\n"):
                line = raw.strip()
                if not line:
                    continue
                if PAGE_NUM_RE.match(line):
                    continue

                # Continuation (no CJK, no Tibetan, no diacritic)?
                if pending is not None and is_pure_english_continuation(line):
                    if pending["english"]:
                        pending["english"] += " " + line
                    else:
                        pending["english"] = line
                    continue

                # Sometimes a continuation can be a Tibetan-only fragment
                # ("མ་"), or pure Sanskrit continuation. Append into raw.
                parsed = parse_line(line)
                if parsed is None:
                    if pending is not None:
                        pending.setdefault("raw_extra", []).append(line)
                    continue

                if pending is not None:
                    entries.append(pending)
                pending = parsed
                pending["page"] = pi + 1

            if (pi + 1) % 20 == 0:
                print(f"  page {pi+1}/{n}, entries: {len(entries):,}", flush=True)

    if pending is not None:
        entries.append(pending)
    return entries


def main() -> int:
    print(f"Opening {SRC_PDF.name} ...", flush=True)
    OUT_META.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)

    entries = parse_pdf()
    print(f"Parsed {len(entries):,} entries", flush=True)
    valid = [e for e in entries if e["chinese"] and (e["sanskrit"] or e["english"])]
    print(f"Valid (zh + skt|en): {len(valid):,}", flush=True)

    meta = {
        "slug": SLUG,
        "name": "Common Chinese-Tibetan-Sanskrit-English Buddhist Terminology (常用漢藏梵英佛學術語, 林崇安 2008)",
        "lang": "zh",
        "tier": 1,
        "priority": 30,
        "role": "equivalents",
        "direction": "zh-to-tib-skt-eng",
        "license": "unknown",
        "source_path": str(SRC_PDF.relative_to(SRC_PDF.parents[2])),
        "row_count": len(valid),
        "extraction_note": "Tibetan column contains (cid:NNN) glyph fallbacks where the PDF font lacked Tibetan Unicode mappings. Wylie conversion deferred to downstream pipeline.",
    }
    OUT_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    written = 0
    with OUT_JSONL.open("w", encoding="utf-8") as f:
        for i, e in enumerate(valid, 1):
            zh = e["chinese"]
            tib = e["tibetan"]
            skt = e["sanskrit"]
            eng = e["english"]
            tib_clean = CID_RE.sub("∅", tib).strip()  # mark broken glyphs

            parts = [zh]
            if tib_clean:
                parts.append(f"[tib] {tib_clean}")
            if skt:
                parts.append(f"[skt] {skt}")
            if eng:
                parts.append(f"[eng] {eng}")
            plain = " · ".join(parts)

            row = {
                "id": f"{SLUG}-{i:06d}",
                "dict": SLUG,
                "headword": zh,
                "headword_iast": skt if skt else zh,
                "headword_norm": zh.lower(),
                "lang": "zh",
                "tier": 1,
                "priority": 30,
                "role": "equivalents",
                "body": {
                    "plain": plain,
                    "skt_iast": skt,
                    "tib_wylie": "",  # cannot recover from cid encoding
                    "tib_raw": tib,  # preserve raw (with cid)
                    "zh": zh,
                    "ko": "",
                    "en": eng,
                    "category": "buddhist-terminology",
                    "note": "Lin Chung-an, 2008",
                    "raw": " | ".join([tib, skt, eng])[:300],
                },
                "reverse": {
                    "en": extract_en_tokens(eng) if eng else [],
                    "ko": [],
                },
                "source_meta": {"page": e.get("page", 0)},
                "license": meta["license"],
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            written += 1

    print(f"Wrote {written:,} JSONL rows → {OUT_JSONL}", flush=True)
    print(f"Meta: {OUT_META}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
