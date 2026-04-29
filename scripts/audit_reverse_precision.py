"""Audit-A4 v2: reverse_en / reverse_ko precision against JSONL ground truth.

The first pass (audit_indices.py) only resolved entry_id → iast via tier0 +
tier0-bo, which only contains the top-10K. So entries returned by reverse_en
that fell outside top-10K showed as "?". This v2 builds a complete
`entry_id → (headword_iast, dict_slug, body.plain[:100])` map by streaming all
JSONL files (~3.8M entries, ~600 MB peak RSS).

Output: data/reports/audit-2026-04-30/audit-A-reverse-precision.md
"""
from __future__ import annotations

import gc
import json
from pathlib import Path

import msgpack
import zstandard as zstd

from scripts.lib.io import iter_slug_dirs, load_meta

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "data" / "sources"
JSONL = ROOT / "data" / "jsonl"
IDX = ROOT / "public" / "indices"
OUT = ROOT / "data" / "reports" / "audit-2026-04-30" / "audit-A-reverse-precision.md"


def decode(path: Path):
    raw = path.read_bytes()
    return msgpack.unpackb(zstd.ZstdDecompressor().decompress(raw), raw=False, strict_map_key=False)


def build_id_map() -> dict[str, tuple[str, str]]:
    """id → (headword_iast, dict_slug). ~190 MB RAM at peak for 3.81M entries."""
    id_map: dict[str, tuple[str, str]] = {}
    n = 0
    for slug_dir in iter_slug_dirs(SOURCES):
        meta = load_meta(slug_dir)
        slug = meta["slug"]
        path = JSONL / f"{slug}.jsonl"
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                eid = e.get("id")
                iast = e.get("headword_iast") or e.get("headword") or "?"
                if eid:
                    id_map[eid] = (iast, slug)
                n += 1
    print(f"Loaded {len(id_map):,} unique ids ({n:,} entries scanned)")
    return id_map


EN_SEEDS = {
    "fire": ["agni"],
    "water": ["jala", "ap", "ambu", "vāri", "udaka"],
    "earth": ["pṛthivī", "bhūmi"],
    "duty": ["dharma", "kartavya", "vrata"],
    "soul": ["ātman", "jīva"],
    "knowledge": ["jñāna", "vidyā"],
    "compassion": ["karuṇā", "anukampā", "dayā"],
    "wisdom": ["prajñā", "jñāna", "buddhi"],
    "mind": ["manas", "citta", "cetas"],
    "buddha": ["buddha", "tathāgata", "sambuddha"],
    "love": ["preman", "rāga", "kāma", "sneha"],
    "death": ["mṛtyu", "marana", "yama"],
    "king": ["rāja", "nṛpa", "narendra"],
    "moon": ["candra", "soma", "indu"],
    "sun": ["sūrya", "āditya", "savitṛ", "ravi"],
}

KO_SEEDS = {
    "법": ["dharma"],
    "불": ["agni", "buddha"],
    "물": ["jala", "ap"],
    "지혜": ["prajñā", "jñāna"],
    "자비": ["karuṇā", "maitrī"],
    "마음": ["manas", "citta"],
    "공": ["śūnyatā", "kha"],
    "도": ["mārga", "panthan"],
    "신": ["deva", "īśvara"],
    "왕": ["rāja", "nṛpa"],
    "인연": ["nidāna", "pratyaya"],
    "지옥": ["naraka", "niraya"],
    "天": ["deva", "svarga"],
    "地": ["pṛthivī", "bhūmi"],
    "心": ["citta", "manas", "hṛd"],
}


def main() -> int:
    print("Decoding reverse indices…")
    rev_en = decode(IDX / "reverse_en.msgpack.zst")
    rev_ko = decode(IDX / "reverse_ko.msgpack.zst")
    print(f"reverse_en: {len(rev_en):,} tokens · reverse_ko: {len(rev_ko):,} tokens")

    print("Building id → (iast, slug) map from JSONL…")
    id_map = build_id_map()
    gc.collect()

    def measure(rev, seeds, top_n=5, top_n_loose=20):
        out_rows = []
        hits_strict = 0
        hits_loose = 0
        for q, expected in seeds.items():
            ids = rev.get(q) or []
            top = ids[:top_n]
            top_loose = ids[:top_n_loose]
            iasts = [id_map.get(i, ("?", "?"))[0] for i in top]
            iasts_loose = [id_map.get(i, ("?", "?"))[0] for i in top_loose]
            slugs = [id_map.get(i, ("?", "?"))[1] for i in top]

            def expected_in(retrieved):
                for exp in expected:
                    for r in retrieved:
                        if exp.lower() == r.lower() or exp.lower() in r.lower():
                            return True
                return False

            strict = expected_in(iasts)
            loose = expected_in(iasts_loose)
            if strict:
                hits_strict += 1
            if loose:
                hits_loose += 1
            out_rows.append((q, expected, len(ids), iasts, slugs, strict, loose))
        return out_rows, hits_strict, hits_loose

    en_rows, en_strict, en_loose = measure(rev_en, EN_SEEDS)
    ko_rows, ko_strict, ko_loose = measure(rev_ko, KO_SEEDS)

    lines = []
    lines.append("# audit-A-reverse-precision (v2 with full JSONL id resolution)")
    lines.append("")
    lines.append(f"- reverse_en tokens: **{len(rev_en):,}**")
    lines.append(f"- reverse_ko tokens: **{len(rev_ko):,}**")
    lines.append(f"- JSONL id map size: **{len(id_map):,}**")
    lines.append("")
    lines.append("## English seed precision (top-5 strict / top-20 loose)")
    lines.append("")
    lines.append(f"**Strict (top-5): {en_strict}/{len(EN_SEEDS)}** · **Loose (top-20): {en_loose}/{len(EN_SEEDS)}**")
    lines.append("")
    lines.append("| Query | Expected | rev hits | Top-5 iast | Top-5 dicts | Strict | Loose |")
    lines.append("|---|---|---:|---|---|---|---|")
    for q, exp, total, iasts, slugs, s, l in en_rows:
        iast_disp = ", ".join(iasts) or "—"
        slug_disp = ", ".join(slugs[:3]) + (f", +{len(slugs)-3}" if len(slugs) > 3 else "")
        lines.append(f"| `{q}` | {', '.join(exp)} | {total:,} | {iast_disp} | {slug_disp} | {'✅' if s else '❌'} | {'✅' if l else '❌'} |")
    lines.append("")

    lines.append("## Korean seed precision (top-5 strict / top-20 loose)")
    lines.append("")
    lines.append(f"**Strict (top-5): {ko_strict}/{len(KO_SEEDS)}** · **Loose (top-20): {ko_loose}/{len(KO_SEEDS)}**")
    lines.append("")
    lines.append("| Query | Expected | rev hits | Top-5 iast | Top-5 dicts | Strict | Loose |")
    lines.append("|---|---|---:|---|---|---|---|")
    for q, exp, total, iasts, slugs, s, l in ko_rows:
        iast_disp = ", ".join(iasts) or "—"
        slug_disp = ", ".join(slugs[:3]) + (f", +{len(slugs)-3}" if len(slugs) > 3 else "")
        lines.append(f"| `{q}` | {', '.join(exp)} | {total:,} | {iast_disp} | {slug_disp} | {'✅' if s else '❌'} | {'✅' if l else '❌'} |")
    lines.append("")

    lines.append("## Notes")
    lines.append("")
    lines.append("- **Strict** = expected iast appears in top-5 of priority-sorted reverse_en/ko lookup (what UI shows by default).")
    lines.append("- **Loose** = expected iast appears in top-20 (within reach if user expands).")
    lines.append("- A high *loose* but low *strict* score means the *data* is correct but the *priority sort* is misranking.")
    lines.append("- A low *loose* score means the reverse extraction itself missed the gloss — extraction tuning needed in `scripts/lib/reverse_tokens.py`.")
    lines.append("")
    lines.append("## UX caveat (orthogonal to data correctness)")
    lines.append("")
    lines.append("`src/routes/+page.svelte:359-371` currently renders reverse hits as raw entry_ids with a dict-slug button. Even when the underlying data is correct, the user cannot tell *which Sanskrit/Tibetan word* matched their English/Korean gloss without clicking through. This is a P0 UX issue tracked in Track C.")
    lines.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"EN strict={en_strict}/{len(EN_SEEDS)} loose={en_loose}/{len(EN_SEEDS)}")
    print(f"KO strict={ko_strict}/{len(KO_SEEDS)} loose={ko_loose}/{len(KO_SEEDS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
