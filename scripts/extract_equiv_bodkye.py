#!/usr/bin/env python3
"""Extract user's haMsa Bodkye Tibetan dictionary (DOCX).

Format per dictionary line:
    * <Tibetan-unicode>\t[<sanskrit>], <english>; <korean>
    - <Tibetan-unicode>\t[bracket-tag] <description>
    ex. <example sentence in Wylie>

Headword starts with `*` or `-` followed by Tibetan unicode then a TAB,
then mixed English / Sanskrit (in [brackets]) / Korean.
'ex.' lines are example sentences.

Output:
  data/sources/equiv-bodkye-haMsa/meta.json
  data/jsonl/equiv-bodkye-haMsa.jsonl
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.lib.reverse_tokens import extract_en_tokens, extract_ko_tokens

SRC_DOCX = Path(
    "/Users/jibak/Library/CloudStorage/GoogleDrive-naspatterns@gmail.com/"
    "내 드라이브/haMsa CODE/Sanskrit_Tibetan_Reading_Tools/Bodkye/haMsa의 Tibetan 사전.docx"
)
SLUG = "equiv-bodkye-hamsa"
OUT_META = ROOT / "data" / "sources" / SLUG / "meta.json"
OUT_JSONL = ROOT / "data" / "jsonl" / f"{SLUG}.jsonl"

TIB_UNI_RE = re.compile(r"[ༀ-࿿]+")
SKT_BRACKET_RE = re.compile(r"\[([^\]]+)\]")
KOREAN_RE = re.compile(r"[가-힯]+")
ENTRY_PREFIX_RE = re.compile(r"^([\*\-])\s*(.+)")


def parse_paragraph(text: str) -> dict | None:
    """Parse a dictionary entry paragraph.

    Returns dict with: tibetan, sanskrit, english, korean, kind ('main'/'sub'/'ex')
    or None if not parseable.
    """
    text = text.strip()
    if not text:
        return None

    # Example sentence?
    if text.startswith("ex.") or text.startswith("ex "):
        return {"kind": "ex", "raw": text}

    m = ENTRY_PREFIX_RE.match(text)
    if not m:
        return None
    prefix, body = m.group(1), m.group(2)

    # Body format: <Tibetan>\t<gloss>
    parts = body.split("\t", 1)
    if len(parts) < 2:
        # Try splitting on multi-space
        parts = re.split(r"\s{2,}", body, maxsplit=1)
    if len(parts) < 2:
        return None

    tib_part, gloss = parts[0].strip(), parts[1].strip()

    # Sanskrit in brackets
    skt = ""
    sk_m = SKT_BRACKET_RE.search(gloss)
    if sk_m:
        skt = sk_m.group(1).strip()

    # Korean (Hangul ranges)
    ko_chunks = KOREAN_RE.findall(gloss)
    korean = " ".join(ko_chunks).strip()

    # English: gloss minus brackets and Korean
    eng = SKT_BRACKET_RE.sub("", gloss)
    eng = re.sub(r"[가-힯]+", "", eng)
    eng = re.sub(r"[,;]+\s*$", "", eng).strip(" ,;.")

    return {
        "kind": "main" if prefix == "*" else "sub",
        "tibetan": tib_part,
        "sanskrit": skt,
        "english": eng,
        "korean": korean,
        "raw": text,
    }


def main() -> int:
    print(f"Opening {SRC_DOCX.name}", flush=True)
    OUT_META.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)

    doc = Document(str(SRC_DOCX))
    entries: list[dict] = []
    last_main: dict | None = None
    examples_for_last: list[str] = []

    for p in doc.paragraphs:
        rec = parse_paragraph(p.text)
        if rec is None:
            continue
        if rec["kind"] == "ex":
            if last_main is not None:
                last_main.setdefault("examples", []).append(rec["raw"])
            continue
        # main or sub
        entries.append(rec)
        if rec["kind"] == "main":
            last_main = rec

    print(f"Parsed {len(entries):,} dictionary entries", flush=True)

    # Filter: keep only entries with Tibetan content
    valid = [e for e in entries if e.get("tibetan") and TIB_UNI_RE.search(e["tibetan"])]
    print(f"Valid (with Tibetan): {len(valid):,}", flush=True)

    meta = {
        "slug": SLUG,
        "name": "haMsa의 Tibetan 사전 (사용자 정리, Bodkye)",
        "lang": "bo",
        "tier": 1,
        "priority": 35,
        "role": "equivalents",
        "direction": "tib-to-skt-eng-ko",
        "license": "personal-CC-BY-NC",
        "source_path": str(SRC_DOCX.relative_to(SRC_DOCX.parents[2])),
        "row_count": len(valid),
        "extraction_note": "Personal study notes; small but high-quality 4-language entries with Tibetan examples.",
    }
    OUT_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    written = 0
    with OUT_JSONL.open("w", encoding="utf-8") as f:
        for i, e in enumerate(valid, 1):
            tib = e["tibetan"]
            skt = e["sanskrit"]
            eng = e["english"]
            ko = e["korean"]
            examples = e.get("examples", [])

            parts = [tib]
            if skt:
                parts.append(f"[skt] {skt}")
            if eng:
                parts.append(f"[eng] {eng}")
            if ko:
                parts.append(f"[ko] {ko}")
            plain = " · ".join(parts)

            row = {
                "id": f"{SLUG}-{i:04d}",
                "dict": SLUG,
                "headword": tib,
                "headword_iast": skt if skt else tib,
                "headword_norm": tib.lower(),
                "lang": "bo",
                "tier": 1,
                "priority": 35,
                "role": "equivalents",
                "body": {
                    "plain": plain,
                    "skt_iast": skt,
                    "tib_wylie": "",  # original is Tibetan unicode; main session converts
                    "tib_unicode": tib,
                    "zh": "",
                    "ko": ko,
                    "en": eng,
                    "category": e["kind"],
                    "note": "; ".join(examples)[:500] if examples else "",
                    "raw": e["raw"][:300],
                },
                "reverse": {
                    "en": extract_en_tokens(eng) if eng else [],
                    "ko": extract_ko_tokens(ko) if ko else [],
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
