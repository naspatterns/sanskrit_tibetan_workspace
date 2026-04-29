"""Audit-A3 + A4 + A5: built indices integrity.

Decodes 7 indices and runs three integrity checks in one pass:

  A3 equivalents.msgpack.zst — cross-source dedup effect
       - sources distribution (per row + per key)
       - rows with ≥2 sources (dedup hits) ratio
       - sources Counter

  A4 reverse_en + reverse_ko — sentinel query precision
       - 10 English seed queries (fire, duty, soul, knowledge, ...)
         expected to surface specific Sanskrit/Tibetan entries in top-N
       - 10 Korean seed queries (법, 불, 지혜, 자비, ...)
       - top-5 hit precision per query

  A5 tier0 vs tier0-bo — split overlap
       - intersection of headword_norm keys
       - which words appear in both (sample)
       - Wylie pattern leakage in tier0, IAST leakage in tier0-bo

Output: data/reports/audit-2026-04-30/audit-A-indices.md
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import msgpack
import zstandard as zstd

ROOT = Path(__file__).resolve().parent.parent
IDX = ROOT / "public" / "indices"
OUT = ROOT / "data" / "reports" / "audit-2026-04-30" / "audit-A-indices.md"


def decode(path: Path):
    raw = path.read_bytes()
    return msgpack.unpackb(zstd.ZstdDecompressor().decompress(raw), raw=False, strict_map_key=False)


# Sentinel queries (user-reviewable in Track C; here we use a small auto-set)
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
}

KO_SEEDS = {
    "법": ["dharma"],
    "불": ["agni", "buddha"],
    "물": ["jala", "ap"],
    "지혜": ["prajñā", "jñāna"],
    "자비": ["karuṇā", "maitrī"],
    "마음": ["manas", "citta"],
    "공": ["śūnyatā", "kha"],
    "도": ["mārga", "panthan", "dao"],  # 道
    "신": ["deva", "īśvara"],  # 神
    "왕": ["rāja", "nṛpa"],
}


def main() -> int:
    print("Decoding indices…")
    tier0 = decode(IDX / "tier0.msgpack.zst")
    tier0_bo = decode(IDX / "tier0-bo.msgpack.zst")
    equiv = decode(IDX / "equivalents.msgpack.zst")
    rev_en = decode(IDX / "reverse_en.msgpack.zst")
    rev_ko = decode(IDX / "reverse_ko.msgpack.zst")

    lines = []
    lines.append("# audit-A-indices — A3 + A4 + A5 combined")
    lines.append("")

    # ---------------- A3 equivalents ----------------
    lines.append("## A3 — equivalents cross-source dedup")
    lines.append("")
    n_keys = len(equiv)
    sources_cnt = Counter()
    rows_total = 0
    rows_multi_source = 0
    keys_with_multi = 0
    multi_source_combos = Counter()
    for key, rows in equiv.items():
        any_multi = False
        for r in rows:
            srcs = r.get("sources") or []
            for s in srcs:
                sources_cnt[s] += 1
            rows_total += 1
            if len(srcs) >= 2:
                rows_multi_source += 1
                any_multi = True
                multi_source_combos[" + ".join(sorted(srcs))] += 1
        if any_multi:
            keys_with_multi += 1
    lines.append(f"- Keys: **{n_keys:,}**")
    lines.append(f"- Rows total: **{rows_total:,}**")
    lines.append(f"- Rows with ≥2 sources (dedup merge): **{rows_multi_source:,}** ({rows_multi_source/max(rows_total,1)*100:.2f}%)")
    lines.append(f"- Keys touched by ≥1 multi-source row: **{keys_with_multi:,}**")
    lines.append("")
    lines.append("### Sources histogram (per-row presence count)")
    lines.append("")
    lines.append("| Source | Rows |")
    lines.append("|---|---:|")
    for s, n in sources_cnt.most_common():
        lines.append(f"| `{s}` | {n:,} |")
    lines.append("")
    if multi_source_combos:
        lines.append("### Top 15 cross-source merges")
        lines.append("")
        lines.append("| Combo | Count |")
        lines.append("|---|---:|")
        for combo, n in multi_source_combos.most_common(15):
            lines.append(f"| {combo} | {n:,} |")
        lines.append("")

    # ---------------- A4 reverse precision ----------------
    lines.append("## A4 — reverse_en / reverse_ko sentinel precision")
    lines.append("")
    lines.append(f"- reverse_en tokens: **{len(rev_en):,}**")
    lines.append(f"- reverse_ko tokens: **{len(rev_ko):,}**")
    lines.append("")

    def hit_for(rev, key, expected, idx_bundle):
        """Is any expected iast in top-5 entries of rev[key]?"""
        ids = rev.get(key) or []
        if not ids:
            return False, "no rev hit"
        top5 = ids[:5]
        # Resolve entry_id → headword via tier0 / tier0-bo entries
        # Build a one-shot id → iast map only for these top5
        id_to_iast = {}
        for hw, slot in idx_bundle:
            for e in slot.get("entries", []):
                if e.get("id") in top5:
                    id_to_iast[e["id"]] = slot.get("iast") or e.get("iast") or hw
                    if len(id_to_iast) == len(top5):
                        break
        retrieved_iasts = [id_to_iast.get(i, "?") for i in top5]
        for exp in expected:
            for r in retrieved_iasts:
                if exp.lower() in r.lower():
                    return True, retrieved_iasts
        return False, retrieved_iasts

    # Lazy materialize: use full tier0 / tier0-bo for resolution
    bundle = list(tier0.items()) + list(tier0_bo.items())

    lines.append("### English seeds (10)")
    lines.append("")
    lines.append("| Query | Expected | Hit? | Retrieved top-5 iast |")
    lines.append("|---|---|---|---|")
    en_hits = 0
    for q, expected in EN_SEEDS.items():
        hit, retrieved = hit_for(rev_en, q, expected, bundle)
        if hit:
            en_hits += 1
        retrieved_str = retrieved if isinstance(retrieved, str) else ", ".join(retrieved)
        lines.append(f"| `{q}` | {', '.join(expected)} | {'✅' if hit else '❌'} | {retrieved_str} |")
    lines.append("")
    lines.append(f"**English precision (top-5): {en_hits}/{len(EN_SEEDS)}**")
    lines.append("")

    lines.append("### Korean seeds (10)")
    lines.append("")
    lines.append("| Query | Expected | Hit? | Retrieved top-5 iast |")
    lines.append("|---|---|---|---|")
    ko_hits = 0
    for q, expected in KO_SEEDS.items():
        hit, retrieved = hit_for(rev_ko, q, expected, bundle)
        if hit:
            ko_hits += 1
        retrieved_str = retrieved if isinstance(retrieved, str) else ", ".join(retrieved)
        lines.append(f"| `{q}` | {', '.join(expected)} | {'✅' if hit else '❌'} | {retrieved_str} |")
    lines.append("")
    lines.append(f"**Korean precision (top-5): {ko_hits}/{len(KO_SEEDS)}**")
    lines.append("")

    # ---------------- A5 tier0 vs tier0-bo overlap ----------------
    lines.append("## A5 — tier0 ↔ tier0-bo split")
    lines.append("")
    keys_skt = set(tier0.keys())
    keys_bo = set(tier0_bo.keys())
    overlap = keys_skt & keys_bo
    lines.append(f"- tier0 keys: **{len(keys_skt):,}**")
    lines.append(f"- tier0-bo keys: **{len(keys_bo):,}**")
    lines.append(f"- intersection: **{len(overlap):,}** ({len(overlap)/min(len(keys_skt), len(keys_bo))*100:.2f}% of smaller)")
    lines.append("")

    # Suspect: Wylie-like keys in tier0 (containing apostrophe or 'ng', 'gs', etc.)
    wylie_in_skt = [k for k in keys_skt if (" " in k or "'" in k)][:30]
    iast_in_bo = []
    for k in keys_bo:
        if any(ch in k for ch in "āīūṛṝḷḹṅñṭḍṇśṣḥṁ"):
            iast_in_bo.append(k)
            if len(iast_in_bo) >= 30:
                break
    lines.append(f"- tier0 keys that look Wylie (space or apostrophe): **{len([k for k in keys_skt if (' ' in k or chr(39) in k)]):,}**")
    lines.append(f"- tier0-bo keys with Sanskrit diacritics: **{len([k for k in keys_bo if any(ch in k for ch in 'āīūṛṝḷḹṅñṭḍṇśṣḥṁ')]):,}**")
    lines.append("")
    lines.append("### Sample overlap (both indices have this norm)")
    lines.append("")
    sample_overlap = sorted(overlap)[:20]
    for k in sample_overlap:
        skt_iast = tier0[k].get("iast", "?")
        bo_iast = tier0_bo[k].get("iast", "?")
        lines.append(f"- `{k}` — skt iast `{skt_iast}` | bo iast `{bo_iast}`")
    lines.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"A3 sources: {len(sources_cnt)} unique, {rows_multi_source:,}/{rows_total:,} multi-source rows")
    print(f"A4 EN top-5 hits: {en_hits}/{len(EN_SEEDS)}, KO top-5 hits: {ko_hits}/{len(KO_SEEDS)}")
    print(f"A5 tier0 ∩ tier0-bo: {len(overlap):,} keys overlap")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
