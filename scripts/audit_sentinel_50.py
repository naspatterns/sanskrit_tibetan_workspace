"""Audit-C: Sentinel 50 query evaluation against current indices.

Automates the manual UI-walkthrough described in
`data/reports/audit-2026-04-30/sentinel-50-queries-draft.md` by directly
querying the 7 client indices (tier0, tier0-bo, headwords, reverse_en,
reverse_ko, reverse_meta, equivalents). For each of the 50 queries we
record: channel used, top-5 results, verdict (✅/⚠️/❌) vs expected,
notes.

Output:
  data/reports/audit-2026-04-30/audit-C-sentinel-results.csv
  data/reports/audit-2026-04-30/audit-C-sentinel-summary.md

Usage:
  uv run python -m scripts.audit_sentinel_50

Re-running this script is the canonical way to measure regression /
improvement across Phase 3.7 follow-ups (KO salience tuning, more
en-extended, Phase 4 deploy etc.).
"""
from __future__ import annotations

import csv
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import msgpack
import zstandard as zstd

ROOT = Path(__file__).resolve().parent.parent
INDICES = ROOT / "public" / "indices"
OUT_CSV = ROOT / "data" / "reports" / "audit-2026-04-30" / "audit-C-sentinel-results.csv"
OUT_MD = ROOT / "data" / "reports" / "audit-2026-04-30" / "audit-C-sentinel-summary.md"


# ─────────────────────────────────────────────────────────────────────
#  50 sentinel queries (cross-checked with sentinel-50-queries-draft.md)
# ─────────────────────────────────────────────────────────────────────
@dataclass
class Query:
    n: int
    text: str
    category: str
    channel: str  # "skt" / "bo" / "en" / "ko" / "zh" / "prefix" / "edge"
    expected: list[str] = field(default_factory=list)  # any-of match
    notes: str = ""


QUERIES: list[Query] = [
    # 1. SA headword (10)
    Query(1, "dharma", "skt-core", "skt", ["dharma"]),
    Query(2, "ātman", "skt-core", "skt", ["ātman"]),
    Query(3, "karman", "skt-core", "skt", ["karman"]),
    Query(4, "agni", "skt-core", "skt", ["agni"]),
    Query(5, "prajñā", "skt-core", "skt", ["prajñā"]),
    Query(6, "śūnyatā", "skt-core", "skt", ["śūnyatā"]),
    Query(7, "bodhicitta", "skt-core", "skt", ["bodhicitta"]),
    Query(8, "tathāgata", "skt-core", "skt", ["tathāgata"]),
    Query(9, "mokṣa", "skt-core", "skt", ["mokṣa"]),
    Query(10, "saṃskāra", "skt-core", "skt", ["saṃskāra"]),
    # 2. Prefix (5)
    Query(11, "dha", "prefix", "prefix", ["dharma", "dhātu", "dhana"]),
    Query(12, "bud", "prefix", "prefix", ["buddha", "buddhi"]),
    Query(13, "pra", "prefix", "prefix", ["prajñā", "pratyaya"]),
    Query(14, "ana", "prefix", "prefix", ["anātman", "anitya", "ānanda"]),
    Query(15, "mahā", "prefix", "prefix", ["mahābhārata", "mahāyāna", "mahātman"]),
    # 3. Wylie (5)
    Query(16, "chos", "bo-wylie", "bo", ["chos"]),
    Query(17, "byang chub sems dpa'", "bo-wylie", "bo", ["byang chub sems dpa'", "bodhisattva"]),
    Query(18, "klong chen", "bo-wylie", "bo", ["klong chen"]),
    Query(19, "rdo rje", "bo-wylie", "bo", ["rdo rje", "vajra"]),
    Query(20, "'jam dpal", "bo-wylie", "bo", ["'jam dpal", "mañjuśrī"]),
    # 4. EN reverse (10)
    Query(21, "fire", "en-reverse", "en", ["agni"]),
    Query(22, "wisdom", "en-reverse", "en", ["prajñā", "jñāna", "buddhi"]),
    Query(23, "compassion", "en-reverse", "en", ["karuṇā", "anukampā", "dayā"]),
    Query(24, "emptiness", "en-reverse", "en", ["śūnyatā", "śūnya"]),
    Query(25, "liberation", "en-reverse", "en", ["mokṣa", "mukti"]),
    Query(26, "meditation", "en-reverse", "en", ["dhyāna", "samādhi"]),
    Query(27, "enlightenment", "en-reverse", "en", ["bodhi", "sambodhi"]),
    Query(28, "suffering", "en-reverse", "en", ["duḥkha"]),
    Query(29, "consciousness", "en-reverse", "en", ["vijñāna", "citta"]),
    Query(30, "righteousness", "en-reverse", "en", ["dharma"]),
    # 5. KO reverse (5)
    Query(31, "법", "ko-reverse", "ko", ["dharma"]),
    Query(32, "자비", "ko-reverse", "ko", ["karuṇā", "maitrī"]),
    Query(33, "지혜", "ko-reverse", "ko", ["prajñā", "jñāna"]),
    Query(34, "도", "ko-reverse", "ko", ["mārga", "panthan"]),
    Query(35, "불", "ko-reverse", "ko", ["agni", "buddha"]),
    # 6. ZH reverse (5) — equivalents zh channel
    Query(36, "法", "zh-reverse", "zh", ["dharma"]),
    Query(37, "空", "zh-reverse", "zh", ["śūnyatā", "śūnya"]),
    Query(38, "菩薩", "zh-reverse", "zh", ["bodhisattva"]),
    Query(39, "涅槃", "zh-reverse", "zh", ["nirvāṇa"]),
    Query(40, "如來", "zh-reverse", "zh", ["tathāgata"]),
    # 7. Edge cases (5) — Phase 3.7 (Option E) added space-split multi-word
    Query(41, "mahābhārata", "edge", "skt", ["mahābhārata"]),
    Query(42, "jagannātha", "edge", "skt", ["jagannātha"]),
    Query(43, "tat tvam asi", "edge", "skt", ["tat", "tvam", "asi"]),
    Query(44, "oṃ", "edge", "skt", ["oṃ", "om"]),
    Query(45, "aham brahmāsmi", "edge", "skt", ["aham", "brahman", "asmi"]),
    # 8. Typo (3)
    Query(46, "dharmaaa", "typo", "edge", []),  # graceful empty
    Query(47, "aaa", "typo", "edge", []),
    Query(48, "   ", "typo", "edge", []),
    # 9. Dead-zone (2)
    Query(49, "decl-a01", "dead-zone", "edge", []),  # exclude_from_search
    Query(50, "aṃśanīya@aṃś", "dead-zone", "edge", []),
]


# ─────────────────────────────────────────────────────────────────────
#  Index loaders
# ─────────────────────────────────────────────────────────────────────
def load_msgpack_zst(path: Path):
    raw = path.read_bytes()
    return msgpack.unpackb(zstd.ZstdDecompressor().decompress(raw),
                           raw=False, strict_map_key=False)


def load_headwords(path: Path) -> list[tuple[str, str, int, str]]:
    """Load 4-column TSV (norm, iast, rank, upasarga).

    Tolerates the 2-column and 3-column legacy formats by defaulting missing
    fields to long-tail rank / empty upasarga.
    """
    raw = path.read_bytes()
    text = zstd.ZstdDecompressor().decompress(raw).decode("utf-8")
    out = []
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) >= 4:
            try:
                rank = int(parts[2])
            except ValueError:
                rank = 999_999
            out.append((parts[0], parts[1], rank, parts[3]))
        elif len(parts) == 3:
            try:
                rank = int(parts[2])
            except ValueError:
                rank = 999_999
            out.append((parts[0], parts[1], rank, ""))
        elif len(parts) == 2:
            out.append((parts[0], parts[1], 999_999, ""))
    return out


# ─────────────────────────────────────────────────────────────────────
#  Normalization (matches client engine.ts norm())
# ─────────────────────────────────────────────────────────────────────
def normalize_skt(q: str) -> str:
    """Match client `normalize(s)` in src/lib/search/transliterate.ts:219:
       NFD → strip combining marks → lowercase → trim.
       This drops diacritics: prajñā → prajna, ātman → atman.
    """
    nfd = unicodedata.normalize("NFD", q.strip().lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


# ─────────────────────────────────────────────────────────────────────
#  Channel evaluators
# ─────────────────────────────────────────────────────────────────────
def eval_skt(q: str, tier0: dict, tier0_bo: dict, tier0_ext: dict) -> list[str]:
    norm = normalize_skt(q)
    hits = []
    for src in (tier0, tier0_ext, tier0_bo):
        if norm in src:
            iast = src[norm].get("iast", norm)
            if iast not in hits:
                hits.append(iast)
    if hits:
        return hits[:5]
    # Phase 3.7 (Option E): multi-word fallback. Split on whitespace and
    # try each token; surface as many distinct iast hits as the limit allows.
    if " " in norm:
        for token in norm.split():
            if not token:
                continue
            for src in (tier0, tier0_ext, tier0_bo):
                if token in src:
                    iast = src[token].get("iast", token)
                    if iast not in hits:
                        hits.append(iast)
                    break  # first source that has this token
            if len(hits) >= 5:
                break
    return hits[:5]


def eval_bo(q: str, tier0_bo: dict, tier0: dict, tier0_ext: dict) -> list[str]:
    """Wylie input — primarily tier0-bo, then Sanskrit fallback."""
    norm = normalize_skt(q)  # Wylie is ASCII; lowercase OK
    hits = []
    for src in (tier0_bo, tier0, tier0_ext):
        if norm in src:
            iast = src[norm].get("iast", norm)
            if iast not in hits:
                hits.append(iast)
    return hits[:5]


def eval_prefix(q: str, headwords: list[tuple[str, str, int, str]]) -> list[str]:
    """Match the client `prefixSearch` — Phase 3.7 follow-up with upasarga
    awareness. Sort key: (upasarga-match-bonus, rank ASC, len ASC, alpha).
    """
    norm = normalize_skt(q)
    cands: list[tuple[str, str, int, str]] = []
    started = False
    for tup in headwords:
        n = tup[0]
        if n.startswith(norm):
            cands.append(tup)
            started = True
        elif started:
            break
    if not cands:
        return []
    upa_query = norm if any(c[3] == norm for c in cands) else ""
    def sort_key(c):
        upa_hit = 0 if (upa_query and c[3] == upa_query) else 1
        return (upa_hit, c[2], len(c[0]), c[0])
    cands.sort(key=sort_key)
    return [c[1] for c in cands[:5]]


def eval_reverse(q: str, reverse_idx: dict, reverse_meta: dict) -> list[str]:
    """English / Korean reverse — top-5 entry_ids resolved to iast."""
    token = q.strip().lower() if q.isascii() else q.strip()
    if token not in reverse_idx:
        return []
    ids = reverse_idx[token][:5]
    out = []
    meta_ids = reverse_meta.get("ids", {}) if isinstance(reverse_meta, dict) else {}
    for eid in ids:
        slot = meta_ids.get(eid)
        if slot:
            out.append(slot[0])  # iast
        else:
            out.append(eid)  # fallback
    return out


def eval_zh(q: str, equivalents: dict) -> list[str]:
    """ZH lookup against equivalents — search_key = zh char."""
    if q in equivalents:
        rows = equivalents[q]
        out = []
        seen = set()
        for r in rows[:10]:
            iast = r.get("skt_iast", "")
            if iast and iast not in seen:
                out.append(iast)
                seen.add(iast)
                if len(out) >= 5:
                    break
        return out
    return []


def eval_edge(q: str, tier0: dict, tier0_bo: dict, tier0_ext: dict,
              headwords: list, eq: dict) -> list[str]:
    """Try multiple channels for edge cases; return first non-empty."""
    if not q.strip():
        return []
    res = eval_skt(q, tier0, tier0_bo, tier0_ext)
    if res:
        return res
    res = eval_bo(q, tier0_bo, tier0, tier0_ext)
    if res:
        return res
    res = eval_prefix(q, headwords)
    if res:
        return res
    return []


# ─────────────────────────────────────────────────────────────────────
#  Verdict
# ─────────────────────────────────────────────────────────────────────
def verdict(query: Query, results: list[str]) -> str:
    """Match expected against top-5 results. Returns ✅/⚠️/❌."""
    if not query.expected:
        # Edge cases: accept empty or any reasonable graceful behaviour
        if query.category in ("typo", "dead-zone"):
            return "✅" if not results else "⚠️"
        return "⚠️" if results else "❌"
    expected_set = {normalize_skt(e) for e in query.expected}
    results_norm = [normalize_skt(r) for r in results]
    # exact match in top-5 → ✅
    if any(r in expected_set for r in results_norm):
        return "✅"
    # partial match (substring on either side) → ⚠️
    for r in results_norm:
        for e in expected_set:
            if r in e or e in r:
                return "⚠️"
    return "❌"


# ─────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────
def main() -> int:
    print("Loading indices…", file=sys.stderr)
    tier0 = load_msgpack_zst(INDICES / "tier0.msgpack.zst")
    tier0_bo = load_msgpack_zst(INDICES / "tier0-bo.msgpack.zst")
    tier0_ext_path = INDICES / "tier0-extended.msgpack.zst"
    tier0_ext = load_msgpack_zst(tier0_ext_path) if tier0_ext_path.exists() else {}
    headwords = load_headwords(INDICES / "headwords.txt.zst")
    reverse_en = load_msgpack_zst(INDICES / "reverse_en.msgpack.zst")
    reverse_ko = load_msgpack_zst(INDICES / "reverse_ko.msgpack.zst")
    reverse_meta = load_msgpack_zst(INDICES / "reverse_meta.msgpack.zst")
    equivalents = load_msgpack_zst(INDICES / "equivalents.msgpack.zst")
    print(f"  tier0 keys: {len(tier0):,} · tier0-bo: {len(tier0_bo):,} · "
          f"tier0-ext: {len(tier0_ext):,}", file=sys.stderr)
    print(f"  headwords: {len(headwords):,} · reverse_en: {len(reverse_en):,} · "
          f"reverse_ko: {len(reverse_ko):,}", file=sys.stderr)

    rows = []
    summary = {"✅": 0, "⚠️": 0, "❌": 0}
    by_cat = {}

    for q in QUERIES:
        ch = q.channel
        if ch == "skt":
            hits = eval_skt(q.text, tier0, tier0_bo, tier0_ext)
        elif ch == "bo":
            hits = eval_bo(q.text, tier0_bo, tier0, tier0_ext)
        elif ch == "prefix":
            hits = eval_prefix(q.text, headwords)
        elif ch == "en":
            hits = eval_reverse(q.text, reverse_en, reverse_meta)
        elif ch == "ko":
            hits = eval_reverse(q.text, reverse_ko, reverse_meta)
        elif ch == "zh":
            hits = eval_zh(q.text, equivalents)
        else:  # edge
            hits = eval_edge(q.text, tier0, tier0_bo, tier0_ext,
                             headwords, equivalents)
        v = verdict(q, hits)
        summary[v] += 1
        by_cat.setdefault(q.category, {"✅": 0, "⚠️": 0, "❌": 0})[v] += 1

        rows.append({
            "n": q.n,
            "query": q.text,
            "category": q.category,
            "channel": q.channel,
            "expected": " | ".join(q.expected),
            "top_5": " | ".join(hits) if hits else "(none)",
            "verdict": v,
        })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f, fieldnames=["n", "query", "category", "channel", "expected", "top_5", "verdict"]
        )
        w.writeheader()
        w.writerows(rows)
    print(f"\n✓ Wrote {OUT_CSV.relative_to(ROOT)}")

    # Summary md
    total = sum(summary.values())
    lines = [
        "# audit-C-sentinel — 50 query 자동 평가",
        "",
        f"- **종합**: ✅ {summary['✅']}/{total} · ⚠️ {summary['⚠️']}/{total} · ❌ {summary['❌']}/{total}",
        f"- 평가 시점: 인덱스 — tier0 {len(tier0):,} keys · reverse_en {len(reverse_en):,} · reverse_ko {len(reverse_ko):,}",
        "",
        "## 카테고리별",
        "",
        "| Category | ✅ | ⚠️ | ❌ | Total |",
        "|---|---:|---:|---:|---:|",
    ]
    for cat, sc in sorted(by_cat.items()):
        t = sum(sc.values())
        lines.append(f"| {cat} | {sc['✅']} | {sc['⚠️']} | {sc['❌']} | {t} |")
    lines.append("")
    lines.append("## Query별 결과")
    lines.append("")
    lines.append("| # | Query | Cat | Ch | Expected | Top-5 | Verdict |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in rows:
        top = r["top_5"][:60].replace("|", "\\|")
        exp = r["expected"][:30].replace("|", "\\|") or "(none)"
        q = r["query"].replace("|", "\\|")
        lines.append(
            f"| {r['n']} | `{q}` | {r['category']} | {r['channel']} | "
            f"{exp} | {top} | {r['verdict']} |"
        )

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✓ Wrote {OUT_MD.relative_to(ROOT)}")
    print(f"\n총합: ✅ {summary['✅']} · ⚠️ {summary['⚠️']} · ❌ {summary['❌']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
