#!/usr/bin/env python3
"""Extract Yogācārabhūmi index PDF (티베탄딕셔너리-유가사지론색인.pdf).

Format per line: <Tibetan-Wylie> <Chinese> [<Sanskrit-IAST>]
Sanskrit may wrap to next line. We detect a wraparound when the line
contains no CJK and starts with lowercase IAST.

Output:
  data/sources/equiv-yogacara-index/meta.json
  data/jsonl/equiv-yogacara-index.jsonl
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.lib.reverse_tokens import extract_en_tokens, extract_ko_tokens
from scripts.lib.transliterate import normalize as tx_normalize

SRC_PDF = Path(
    "/Users/jibak/Library/CloudStorage/GoogleDrive-naspatterns@gmail.com/"
    "내 드라이브/haMsa CODE/Sanskrit_Tibetan_Reading_Tools/"
    "티베탄딕셔너리-유가사지론색인.pdf"
)
SLUG = "equiv-yogacara-index"
OUT_META = ROOT / "data" / "sources" / SLUG / "meta.json"
OUT_JSONL = ROOT / "data" / "jsonl" / f"{SLUG}.jsonl"

CJK_RE = re.compile(r"[㐀-鿿豈-﫿]")  # CJK Unified + Compat
IAST_DIACRITIC = "āīūṛṝḷḹṃṁḥṅñṭḍṇśṣĀĪŪṚṜḶḸṂṀḤṄÑṬḌṆŚṢ"


def has_cjk(s: str) -> bool:
    return bool(CJK_RE.search(s))


def parse_line(line: str) -> tuple[str, str, str] | None:
    """Parse one line into (tib_wylie, chinese, sanskrit).

    The Tibetan Wylie portion ends at the first CJK char.
    The Chinese portion is the contiguous CJK run (possibly with embedded
    spaces) up to the trailing Sanskrit IAST run.
    """
    line = line.rstrip()
    if not line:
        return None

    cjk_match = CJK_RE.search(line)
    if not cjk_match:
        return None

    tib = line[: cjk_match.start()].strip()
    rest = line[cjk_match.start() :]

    # Find end of CJK run (last CJK char)
    last_cjk = None
    for m in CJK_RE.finditer(line):
        last_cjk = m
    cjk_end = last_cjk.end() if last_cjk else cjk_match.end()

    chinese_chunk = line[cjk_match.start() : cjk_end].strip()
    skt_chunk = line[cjk_end:].strip()

    return tib, chinese_chunk, skt_chunk


def is_continuation(line: str) -> bool:
    """A continuation line has no CJK and starts with lowercase IAST/Latin."""
    if has_cjk(line):
        return False
    s = line.strip()
    if not s:
        return False
    first = s[0]
    return first.islower() or first in IAST_DIACRITIC


def normalize_wylie(s: str) -> str:
    return tx_normalize(s)


def main() -> int:
    print(f"Opening {SRC_PDF.name} ...", flush=True)
    OUT_META.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)

    entries: list[dict] = []
    pending: dict | None = None

    with pdfplumber.open(str(SRC_PDF)) as pdf:
        n_pages = len(pdf.pages)
        for pi, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            for raw_line in text.split("\n"):
                line = raw_line.strip()
                if not line:
                    continue

                if is_continuation(line) and pending is not None:
                    # Append to previous Sanskrit
                    if pending["skt"]:
                        pending["skt"] += " " + line
                    else:
                        pending["skt"] = line
                    continue

                # Flush pending
                if pending is not None:
                    entries.append(pending)
                    pending = None

                parsed = parse_line(line)
                if parsed is None:
                    # Lines without CJK and not a continuation: noise/skip
                    continue
                tib, zh, skt = parsed
                if not tib or not zh:
                    continue
                pending = {"tib": tib, "zh": zh, "skt": skt, "page": pi + 1}

            if (pi + 1) % 100 == 0:
                print(f"  page {pi+1}/{n_pages}, entries so far: {len(entries):,}", flush=True)

    if pending is not None:
        entries.append(pending)

    print(f"Parsed {len(entries):,} entries from {n_pages} pages", flush=True)

    # Write meta.json
    meta = {
        "slug": SLUG,
        "name": "Yogācārabhūmi Tibetan-Chinese-Sanskrit Index (티베탄딕셔너리-유가사지론색인)",
        "lang": "bo",
        "tier": 2,
        "priority": 28,
        "role": "equivalents",
        "direction": "tib-to-zh-skt",
        "license": "unknown",
        "source_path": str(SRC_PDF.relative_to(SRC_PDF.parents[2])),
        "row_count": len(entries),
    }
    OUT_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # Write jsonl
    written = 0
    with OUT_JSONL.open("w", encoding="utf-8") as f:
        for i, e in enumerate(entries, 1):
            tib = e["tib"]
            zh = e["zh"]
            skt = e["skt"]
            # Build plain string for body.plain (schema-required)
            parts = [tib]
            if zh:
                parts.append(f"[zh] {zh}")
            if skt:
                parts.append(f"[skt] {skt}")
            plain = " · ".join(parts)

            row = {
                "id": f"{SLUG}-{i:06d}",
                "dict": SLUG,
                "headword": tib,
                "headword_iast": skt if skt else tib,
                "headword_norm": normalize_wylie(tib),
                "lang": "bo",
                "tier": 2,
                "priority": 28,
                "role": "equivalents",
                "body": {
                    "plain": plain,
                    "skt_iast": skt,
                    "tib_wylie": tib,
                    "zh": zh,
                    "ko": "",
                    "en": "",
                    "category": "",
                    "note": "",
                    "raw": e.get("page_raw", ""),
                },
                "reverse": {
                    "en": extract_en_tokens(skt) if skt else [],
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
