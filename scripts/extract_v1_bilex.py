"""Extract v1 bilex/equiv → v2 equivalents JSONL.

Source: v1 `bilex.sqlite` (READ-ONLY).
  - `equiv` table holds 207,095 cross-language rows across 7 sources
    (mahavyutpatti, negi, lokesh-chandra, 84000, hopkins, nti-reader,
    yogacarabhumi-idx). bilex table is a 9,568-row subset of mahavyutpatti
    with no extra value (bilex.gloss_en is empty everywhere).

Output:
  - data/sources/equiv-{slug}/meta.json (7 files)
  - data/jsonl/equiv-{slug}.jsonl       (7 files)

Schema: docs/schema.json with role="equivalents" + body.equivalents sub-object.
Each row's body.plain is auto-generated as natural-language summary
("Skt: ... · Tib: ... · Zh: ... · cat: ...") so existing schema's plain-required
constraint is satisfied without losing structured cross-lang data.
"""
from __future__ import annotations

import json
import sqlite3
import sys
import unicodedata
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from scripts.lib.reverse_tokens import extract_ko_tokens  # noqa: E402

V1_DB = Path(
    "/Users/jibak/Library/CloudStorage/GoogleDrive-naspatterns@gmail.com/"
    "내 드라이브/haMsa CODE/sanskrit_tibetan_reading_workspace/bilex.sqlite"
)
SOURCES_DIR = PROJECT / "data" / "sources"
JSONL_DIR = PROJECT / "data" / "jsonl"

# Source mapping: equiv_sources.id → metadata.
# Priority band 25-31 sits between Tibetan tier-1 dicts (20-24) and tier-2
# (30+) — equivalents are *cross-cutting* lookups, not primary definitions.
SOURCE_META: dict[int, dict] = {
    1: {
        "slug": "equiv-mahavyutpatti",
        "name": "Mahāvyutpatti (翻譯名義大集)",
        "lang": "skt",
        "priority": 25,
        "direction": "skt-to-tib",
        "license": "public-domain",
    },
    2: {
        "slug": "equiv-negi",
        "name": "Negi Tibetan-Sanskrit Dictionary (16-vol)",
        "lang": "bo",
        "priority": 26,
        "direction": "tib-to-skt",
        "license": "research-use",
    },
    3: {
        "slug": "equiv-lokesh-chandra",
        "name": "Lokesh Chandra Tibetan-Sanskrit Dictionary",
        "lang": "bo",
        "priority": 27,
        "direction": "tib-to-skt",
        "license": "research-use",
    },
    4: {
        "slug": "equiv-84000",
        "name": "84000 Tibetan-Sanskrit Glossary",
        "lang": "bo",
        "priority": 28,
        "direction": "tib-to-skt",
        "license": "CC-BY-4.0",
    },
    5: {
        "slug": "equiv-hopkins",
        "name": "Hopkins Tibetan-Sanskrit Dictionary (2015)",
        "lang": "bo",
        "priority": 29,
        "direction": "tib-to-skt",
        "license": "research-use",
    },
    6: {
        "slug": "equiv-nti-reader",
        "name": "NTI Reader Buddhist Dictionary (Sanskrit-Chinese, Fo Guang Shan)",
        "lang": "skt",
        "priority": 30,
        "direction": "skt-to-zh",
        "license": "CC-BY-SA-4.0",
    },
    7: {
        "slug": "equiv-yogacarabhumi-idx",
        "name": "Yokoyama-Hirosawa Yogācārabhūmi Index (Skt-Tib-Zh, 1996)",
        "lang": "skt",
        "priority": 31,
        "direction": "skt-to-tib-zh",
        "license": "research-use",
    },
}


def normalize_norm(s: str) -> str:
    """NFD strip combining marks, lowercase, strip whitespace."""
    if not s:
        return ""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


def make_entry(row: sqlite3.Row, src: dict, seq: int) -> dict | None:
    """Convert one equiv row → v2 entry dict (returns None if row is empty)."""
    skt_iast = (row["skt_iast"] or "").strip()
    skt_norm_v1 = (row["skt_norm"] or "").strip()
    tib_wylie = (row["tib_wylie"] or "").strip()
    tib_norm_v1 = (row["tib_norm"] or "").strip()
    zh = (row["zh"] or "").strip()
    category = (row["category"] or "").strip()
    note = (row["note"] or "").strip()

    # Pick primary headword + norm based on source's primary lang
    if src["lang"] == "skt":
        primary = skt_iast or zh or tib_wylie
        primary_iast = skt_iast or primary
        primary_norm = skt_norm_v1 or normalize_norm(primary)
    elif src["lang"] == "bo":
        primary = tib_wylie or skt_iast or zh
        primary_iast = tib_wylie or primary  # Wylie acts as IAST for bo
        primary_norm = tib_norm_v1 or normalize_norm(primary)
    elif src["lang"] == "zh":
        primary = zh or skt_iast or tib_wylie
        primary_iast = skt_iast or zh
        primary_norm = normalize_norm(skt_norm_v1 or zh)
    else:
        primary = skt_iast or tib_wylie or zh
        primary_iast = primary
        primary_norm = normalize_norm(primary)

    if not primary:
        return None

    # Natural-language plain (Zone B fallback / search snippet)
    plain_parts = []
    if skt_iast:
        plain_parts.append(f"Skt: {skt_iast}")
    if tib_wylie:
        plain_parts.append(f"Tib: {tib_wylie}")
    if zh:
        plain_parts.append(f"Zh: {zh}")
    if category and category != ".":
        plain_parts.append(f"({category})")
    plain = " · ".join(plain_parts) if plain_parts else primary

    # Reverse tokens — equivalents have no English body, but we tokenize zh
    # so Korean-only users can still hit hanja. en stays empty.
    rev_ko = extract_ko_tokens(zh) if zh else []

    body = {
        "plain": plain,
        "equivalents": {
            "skt_iast": skt_iast,
            "tib_wylie": tib_wylie,
            "zh": zh,
            "category": category,
            "note": note,
        },
    }

    entry = {
        "id": f"{src['slug']}-{seq:06d}",
        "dict": src["slug"],
        "headword": primary,
        "headword_iast": primary_iast,
        "headword_norm": primary_norm,
        "lang": src["lang"],
        "tier": 1,
        "role": "equivalents",
        "body": body,
        "license": src["license"],
        "source_meta": {"v1_id": row["id"], "v1_db": "bilex.sqlite/equiv"},
    }
    if rev_ko:
        entry["reverse"] = {"en": [], "ko": rev_ko[:20]}
    return entry


def write_meta(src: dict, count: int) -> None:
    out_dir = SOURCES_DIR / src["slug"]
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "slug": src["slug"],
        "name": src["name"],
        "lang": src["lang"],
        "tier": 1,
        "priority": src["priority"],
        "role": "equivalents",
        "direction": src["direction"],
        "license": src["license"],
        "source": "v1 bilex.sqlite/equiv table",
        "entry_count": count,
    }
    (out_dir / "meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main() -> int:
    if not V1_DB.exists():
        print(f"ERROR: v1 DB not found at {V1_DB}", file=sys.stderr)
        return 1
    JSONL_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(f"file:{V1_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    print(f"Extracting from {V1_DB.name} → {JSONL_DIR}")
    grand_total = 0
    for source_id, src in SOURCE_META.items():
        rows = conn.execute(
            "SELECT * FROM equiv WHERE source_id = ? ORDER BY id",
            (source_id,),
        ).fetchall()

        out_jsonl = JSONL_DIR / f"{src['slug']}.jsonl"
        written = 0
        skipped = 0
        with out_jsonl.open("w", encoding="utf-8") as f:
            for row in rows:
                entry = make_entry(row, src, written + skipped + 1)
                if entry is None:
                    skipped += 1
                    continue
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                written += 1

        write_meta(src, written)
        grand_total += written
        print(f"  {src['slug']:<30} {written:>7,} rows ({skipped} skipped empty)")

    conn.close()
    print(f"\nTotal: {grand_total:,} equivalents rows across {len(SOURCE_META)} sources")
    return 0


if __name__ == "__main__":
    sys.exit(main())
