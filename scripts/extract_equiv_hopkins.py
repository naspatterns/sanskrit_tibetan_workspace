#!/usr/bin/env python3
"""Extract Jeffrey Hopkins' Tibetan-Sanskrit-English Dictionary (DDBC ed).

Format per entry (variable lines):

    bkres pa
    [tenses] bkru/; 'khrud/; bkrus/; khrus/
    [translation-san] {C} bubhukṣita
    [translation-san] {C} jighatsita
    [translation-san] bubhūkṣā
    [translation-eng] {Hopkins} hunger; hungry
    [translation-eng] {C} famished; starving; hungry
    [comments] ...

A line that is NOT a [tag] line, NOT plain English continuation of a
[tag] body, AND is lowercase Wylie-shaped → start of a new headword.

Output:
  data/sources/equiv-hopkins-tsed/meta.json
  data/jsonl/equiv-hopkins-tsed.jsonl
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
from scripts.lib.transliterate import normalize as tx_normalize

SRC_PDF = Path(
    "/Users/jibak/Library/CloudStorage/GoogleDrive-naspatterns@gmail.com/"
    "내 드라이브/haMsa CODE/Sanskrit_Tibetan_Reading_Tools/[#haMsa TIBETAN]/hopkins.ddbc.pdf"
)
SLUG = "equiv-hopkins-tsed"
OUT_META = ROOT / "data" / "sources" / SLUG / "meta.json"
OUT_JSONL = ROOT / "data" / "jsonl" / f"{SLUG}.jsonl"

TAG_RE = re.compile(r"^\[([a-z\-]+)\]\s*(.*)$")
SOURCE_BRACE_RE = re.compile(r"^\{([^}]+)\}\s*(.*)$")
PAGENUM_RE = re.compile(r"^\d{1,4}$")  # standalone page numbers
WYLIE_HEAD_RE = re.compile(r"^[a-zśṣṅñṇṃḥṛṝḷḹ' ./;]+$", re.IGNORECASE)


def is_wylie_headword(line: str) -> bool:
    """Heuristic: a Wylie-only short line that looks like a Tibetan headword.

    Headwords:
      - lowercase Latin + apostrophe + hyphen + dot + slash + spaces
      - usually short (< 80 chars)
      - no IAST diacritics typical of Sanskrit (those are in [translation-san])
      - no parentheses, no English-only words like "example", "see"
    """
    s = line.strip()
    if not s:
        return False
    if s.startswith("[") or s.startswith("{") or s.startswith("("):
        return False
    if len(s) > 100:
        return False
    if s in ("example",):
        return False
    # Disallow English sentence-like content
    if any(c in s for c in ",:?!"):
        return False
    if s[0].isupper():
        return False
    # Must be all wylie-allowed chars + spaces; allow leading/trailing slashes
    allowed = set("abcdefghijklmnopqrstuvwxyz' ./;-")
    if not all(c in allowed for c in s):
        return False
    return True


def parse_pdf() -> list[dict]:
    entries: list[dict] = []
    current: dict | None = None
    pending_tag: str | None = None
    intro_done = False  # skip intro pages

    with pdfplumber.open(str(SRC_PDF)) as pdf:
        n_pages = len(pdf.pages)
        for pi, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            for raw_line in text.split("\n"):
                line = raw_line.strip()
                if not line:
                    continue
                if PAGENUM_RE.match(line):
                    continue

                # Parse tag if present
                m = TAG_RE.match(line)
                if m:
                    tag, rest = m.group(1), m.group(2).strip()
                    # Save tag value to current entry
                    if current is None:
                        # tag without headword: ignore (intro)
                        continue
                    intro_done = True
                    current.setdefault(tag, []).append(rest)
                    pending_tag = tag
                    continue

                # Continuation of previous tag body? (e.g. wrapped lines)
                if current is not None and pending_tag is not None:
                    # If this line clearly looks like a Wylie headword,
                    # it's a new entry; otherwise treat as continuation.
                    if is_wylie_headword(line):
                        # Flush
                        entries.append(current)
                        current = {"headword": line}
                        pending_tag = None
                        continue
                    # Append to last value of pending tag
                    cur_list = current[pending_tag]
                    cur_list[-1] = (cur_list[-1] + " " + line).strip()
                    continue

                # No pending tag: must be a new headword if Wylie-shaped
                if is_wylie_headword(line):
                    if current is not None:
                        entries.append(current)
                    current = {"headword": line}
                    pending_tag = None
                else:
                    # Skip intro/preamble noise
                    pass

            if (pi + 1) % 200 == 0:
                print(f"  page {pi+1}/{n_pages}, entries so far: {len(entries):,}", flush=True)

    if current is not None:
        entries.append(current)

    return entries


def main() -> int:
    print(f"Opening {SRC_PDF.name} ...", flush=True)
    OUT_META.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)

    entries = parse_pdf()
    print(f"Parsed {len(entries):,} headwords", flush=True)

    # Filter: must have at least one [translation-*] tag (else it's noise)
    # Optional: keep entries even without translations as "no-equiv stub"
    valid = [e for e in entries if any(k.startswith("translation-") for k in e)]
    print(f"With at least one translation: {len(valid):,}", flush=True)

    meta = {
        "slug": SLUG,
        "name": "Jeffrey Hopkins' Tibetan-Sanskrit-English Dictionary (DDBC)",
        "lang": "bo",
        "tier": 1,
        "priority": 26,
        "role": "equivalents",
        "direction": "tib-to-skt-eng",
        "license": "CC-BY-SA-4.0",
        "source_path": str(SRC_PDF.relative_to(SRC_PDF.parents[2])),
        "row_count": len(valid),
        "extraction_note": "Multi-source consolidated: {Hopkins}, {C}=Conze, {MSA}=Mahāyānasūtrālaṃkāra, {L}=Lalitavistara, {LCh}=Lokesh Chandra, {PH}=Padmakara Hackett, etc.",
    }
    OUT_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # Write jsonl
    written = 0
    with OUT_JSONL.open("w", encoding="utf-8") as f:
        for i, e in enumerate(valid, 1):
            tib = e["headword"]
            skt_list = e.get("translation-san", [])
            eng_list = e.get("translation-eng", [])
            tenses = e.get("tenses", [])
            div_bod = e.get("division-bod", [])
            div_eng = e.get("division-eng", [])
            comments = e.get("comments", [])

            # Strip {Source} prefix from each value
            def clean(vals: list[str]) -> list[str]:
                out = []
                for v in vals:
                    m = SOURCE_BRACE_RE.match(v)
                    if m:
                        out.append(m.group(2).strip())
                    else:
                        out.append(v.strip())
                return [x for x in out if x]

            skt_clean = clean(skt_list)
            eng_clean = clean(eng_list)

            skt_joined = "; ".join(skt_clean)
            eng_joined = "; ".join(eng_clean)

            # Build plain
            parts = [tib]
            if tenses:
                parts.append(f"[tenses] {'; '.join(tenses)}")
            if skt_joined:
                parts.append(f"[skt] {skt_joined}")
            if eng_joined:
                parts.append(f"[eng] {eng_joined}")
            if div_bod:
                parts.append(f"[div-bod] {'; '.join(div_bod)}")
            if div_eng:
                parts.append(f"[div-eng] {'; '.join(div_eng)}")
            if comments:
                parts.append(f"[comm] {'; '.join(comments)[:300]}")
            plain = " · ".join(parts)

            # First Sanskrit equivalent → headword_iast
            primary_skt = skt_clean[0] if skt_clean else ""

            row = {
                "id": f"{SLUG}-{i:06d}",
                "dict": SLUG,
                "headword": tib,
                "headword_iast": primary_skt if primary_skt else tib,
                "headword_norm": tx_normalize(tib),
                "lang": "bo",
                "tier": 1,
                "priority": 26,
                "role": "equivalents",
                "body": {
                    "plain": plain,
                    "skt_iast": skt_joined,
                    "tib_wylie": tib,
                    "zh": "",
                    "ko": "",
                    "en": eng_joined,
                    "category": "",
                    "note": "; ".join(comments)[:500] if comments else "",
                    "raw": "",
                    "tenses": "; ".join(tenses) if tenses else "",
                    "div_bod": "; ".join(div_bod) if div_bod else "",
                    "div_eng": "; ".join(div_eng) if div_eng else "",
                    "skt_all": skt_clean,
                    "eng_all": eng_clean,
                },
                "reverse": {
                    "en": extract_en_tokens(eng_joined),
                    "ko": [],
                },
                "license": meta["license"],
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            written += 1

    print(f"Wrote {written:,} JSONL rows → {OUT_JSONL}", flush=True)
    print(f"Meta: {OUT_META}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
