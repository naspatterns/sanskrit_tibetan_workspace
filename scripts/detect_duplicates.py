"""Detect duplicate dictionaries in v1 dict.sqlite.

For each candidate pair (same family or similar name), compute:
  - Jaccard overlap on headword_norm sets
  - Body text similarity on N sampled intersecting headwords (markup-stripped)

Classification thresholds (per user decision):
  - STRICT_DUPLICATE: Jaccard >= 0.9 AND body_sim >= 0.8
  - PARTIAL_DUPLICATE: Jaccard 0.5-0.9
  - DIFFERENT: < 0.5

Output: data/reports/duplicates.md with findings + canonical recommendations.
"""
from __future__ import annotations

import random
import sqlite3
import sys
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from scripts.lib.html_utils import strip_markup
from scripts.lib.io import V1_DB, open_v1_readonly

# Candidate pairs. Each pair is compared both directions implicitly (jaccard symmetric).
SUSPECT_PAIRS: list[tuple[str, str]] = [
    # MW family (4 variants)
    ("mwse.dict", "mwse.sandic"),
    ("mwse.dict", "mw-sdt.apple"),
    ("mwse.dict", "mwse72.dict"),
    ("mwse.sandic", "mw-sdt.apple"),
    ("mwse.sandic", "mwse72.dict"),
    ("mw-sdt.apple", "mwse72.dict"),
    # Apte family (3 + reverse)
    ("aptees.dict", "aptese.sandic"),
    ("aptees.dict", "apte-bi.apple"),
    ("apte-bi.apple", "aptese.sandic"),
    # Macdonell
    ("macdse.dict", "macdse.sandic"),
    # Vacaspatyam
    ("vacaspatyam.apple", "vcpss.dict"),
    # Kalpadruma
    ("kalpadruma.apple", "skdss.dict"),
    # Bod-rgya — same entry count strongly suggests duplicate
    ("bod-rgya.apple", "apple_bod_rgya_tshig_mdzod"),
    # Grassmann
    ("grasg_a.dict", "grasg_p.gretil"),
    # Mahavyutpatti triplet
    ("mahavyutpatti", "tib_21-Mahavyutpatti-Skt"),
    ("mahavyutpatti", "tib_63-Mahavyutpatti-Scan-1989"),
    ("tib_21-Mahavyutpatti-Skt", "tib_63-Mahavyutpatti-Scan-1989"),
    # Dhatupatha triplet
    ("dhatupatha.sandic", "dhatupatha-kr.apple"),
    ("dhatupatha.sandic", "dhatupatha-sa.apple"),
    ("dhatupatha-kr.apple", "dhatupatha-sa.apple"),
    # Ashtadhyayi
    ("ashtadhyayi-en.apple", "ashtadhyayi-anv.apple"),
    # Vedic concordance
    ("bloomfield.apple", "vedconc.gretil"),
    # Hopkins Skt 1992 vs 2015 (likely different editions but close)
    ("tib_15-Hopkins-Skt1992", "tib_15-Hopkins-Skt2015"),
    ("tib_17-Hopkins-TibetanSynonyms1992", "tib_17-Hopkins-TibetanSynonyms2015"),
]

BODY_SAMPLE_SIZE = 20  # Entries to sample for body comparison
BODY_CHAR_LIMIT = 2000  # Limit chars per body for SequenceMatcher speed


@dataclass
class PairResult:
    dict_a: str
    dict_b: str
    count_a: int
    count_b: int
    intersection: int
    jaccard: float
    body_sim: float
    verdict: str

    def canonical_recommendation(self) -> str:
        """Suggest canonical choice when duplicate detected."""
        if self.verdict == "DIFFERENT":
            return "keep both — distinct data"
        # Prefer: (1) XDXF/gretil over Apple (standardized format)
        #         (2) larger entry count (more complete)
        #         (3) alphabetical as tiebreaker
        a_fmt = _format_rank(self.dict_a)
        b_fmt = _format_rank(self.dict_b)
        if a_fmt != b_fmt:
            winner = self.dict_a if a_fmt < b_fmt else self.dict_b
        elif self.count_a != self.count_b:
            winner = self.dict_a if self.count_a > self.count_b else self.dict_b
        else:
            winner = min(self.dict_a, self.dict_b)
        return f"canonical: `{winner}` (merge the other)"


_FORMAT_PRIORITY = {"dict": 1, "gretil": 2, "sandic": 3, "apple": 4}


def _format_rank(name: str) -> int:
    """Lower rank = preferred canonical. XDXF (`.dict`) > GRETIL > SANDIC > Apple."""
    for suffix, rank in _FORMAT_PRIORITY.items():
        if name.endswith("." + suffix) or name.endswith(suffix):
            return rank
    # Unknown (e.g. mahavyutpatti, tib_*) — treat as standard
    return 1


def _source_format(name: str) -> str:
    if name == "mahavyutpatti":
        return "xdxf"
    if name.startswith("tib_"):
        return "xdxf"
    if name == "apple_bod_rgya_tshig_mdzod":
        return "apple_dict"
    if "." in name:
        ext = name.rsplit(".", 1)[1]
        return {"dict": "xdxf", "sandic": "sandic", "gretil": "gretil", "apple": "apple_dict"}.get(ext, ext)
    return "unknown"


def classify(jaccard: float, body_sim: float) -> str:
    if jaccard >= 0.9 and body_sim >= 0.8:
        return "STRICT_DUPLICATE"
    if jaccard >= 0.5:
        return "PARTIAL_DUPLICATE"
    return "DIFFERENT"


def get_dict_id(conn: sqlite3.Connection, name: str) -> int | None:
    row = conn.execute("SELECT id FROM dictionaries WHERE name = ?", (name,)).fetchone()
    return row[0] if row else None


def get_headwords(conn: sqlite3.Connection, dict_id: int) -> set[str]:
    cur = conn.execute(
        "SELECT DISTINCT headword_norm FROM entries WHERE dict_id = ? AND headword_norm IS NOT NULL",
        (dict_id,),
    )
    return {row[0] for row in cur if row[0]}


def sample_bodies(
    conn: sqlite3.Connection,
    dict_id: int,
    headwords: list[str],
) -> dict[str, str]:
    """Fetch bodies for the given headwords in this dict. Returns {headword: body}.

    No LIMIT — polyseme-heavy dicts (Apte, MW) have many entries per headword_norm,
    and a tight limit biased the sampled subset. The IN clause already bounds
    the result to the sampled headwords.
    """
    if not headwords:
        return {}
    placeholders = ",".join("?" * len(headwords))
    cur = conn.execute(
        f"SELECT headword_norm, body FROM entries WHERE dict_id = ? "
        f"AND headword_norm IN ({placeholders})",
        (dict_id, *headwords),
    )
    result: dict[str, str] = {}
    for hw, body in cur:
        if hw not in result and body:
            result[hw] = body
    return result


def body_similarity(a: str, b: str, src_a: str, src_b: str) -> float:
    """Strip markup from both, compute SequenceMatcher ratio on plain text."""
    if not a or not b:
        return 0.0
    plain_a = strip_markup(a[:BODY_CHAR_LIMIT * 2], source_format=src_a)
    plain_b = strip_markup(b[:BODY_CHAR_LIMIT * 2], source_format=src_b)
    if not plain_a or not plain_b:
        return 0.0
    return SequenceMatcher(
        None, plain_a[:BODY_CHAR_LIMIT], plain_b[:BODY_CHAR_LIMIT]
    ).ratio()


def compare_pair(
    conn: sqlite3.Connection,
    dict_a: str,
    dict_b: str,
    rng: random.Random,
) -> PairResult | None:
    id_a = get_dict_id(conn, dict_a)
    id_b = get_dict_id(conn, dict_b)
    if id_a is None:
        print(f"  WARN: {dict_a} not in DB", file=sys.stderr)
        return None
    if id_b is None:
        print(f"  WARN: {dict_b} not in DB", file=sys.stderr)
        return None

    hw_a = get_headwords(conn, id_a)
    hw_b = get_headwords(conn, id_b)
    if not hw_a:
        print(f"    WARN: {dict_a} has no headwords (pair skipped)", file=sys.stderr)
        return None
    if not hw_b:
        print(f"    WARN: {dict_b} has no headwords (pair skipped)", file=sys.stderr)
        return None

    intersection = hw_a & hw_b
    union = hw_a | hw_b
    jaccard = len(intersection) / len(union) if union else 0.0

    body_sim = 0.0
    if intersection:
        sample_size = min(BODY_SAMPLE_SIZE, len(intersection))
        sample_hws = rng.sample(list(intersection), sample_size)
        bodies_a = sample_bodies(conn, id_a, sample_hws)
        bodies_b = sample_bodies(conn, id_b, sample_hws)
        src_a = _source_format(dict_a)
        src_b = _source_format(dict_b)
        sims = [
            body_similarity(bodies_a[hw], bodies_b[hw], src_a, src_b)
            for hw in sample_hws
            if hw in bodies_a and hw in bodies_b
        ]
        body_sim = sum(sims) / len(sims) if sims else 0.0

    return PairResult(
        dict_a=dict_a,
        dict_b=dict_b,
        count_a=len(hw_a),
        count_b=len(hw_b),
        intersection=len(intersection),
        jaccard=jaccard,
        body_sim=body_sim,
        verdict=classify(jaccard, body_sim),
    )


def main() -> int:
    if not V1_DB.exists():
        print(f"ERROR: v1 DB not found at {V1_DB}", file=sys.stderr)
        return 1

    rng = random.Random(42)
    conn = open_v1_readonly()
    try:
        results: list[PairResult] = []
        for i, (a, b) in enumerate(SUSPECT_PAIRS, 1):
            print(f"[{i}/{len(SUSPECT_PAIRS)}] Comparing {a}  ←→  {b}")
            r = compare_pair(conn, a, b, rng)
            if r:
                results.append(r)
                print(f"    Jaccard={r.jaccard:.3f}  body_sim={r.body_sim:.3f}  → {r.verdict}")
    finally:
        conn.close()

    # Sort: STRICT first, then PARTIAL, then DIFFERENT
    verdict_order = {"STRICT_DUPLICATE": 0, "PARTIAL_DUPLICATE": 1, "DIFFERENT": 2}
    results.sort(key=lambda r: (verdict_order[r.verdict], -r.jaccard))

    out = Path("data/reports/duplicates.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    write_report(results, out)
    print(f"\n✓ Report written to {out}")
    return 0


def write_report(results: list[PairResult], out: Path) -> None:
    strict = [r for r in results if r.verdict == "STRICT_DUPLICATE"]
    partial = [r for r in results if r.verdict == "PARTIAL_DUPLICATE"]
    different = [r for r in results if r.verdict == "DIFFERENT"]

    lines = [
        "# Duplicate Detection Report",
        "",
        f"Compared {len(results)} candidate pairs from v1 `dict.sqlite`.",
        "",
        "## Methodology",
        "",
        "- **Jaccard overlap**: size of headword_norm intersection ÷ union.",
        "- **Body similarity**: sampled 20 intersecting headwords, stripped markup, "
        "computed `difflib.SequenceMatcher` ratio on first 2000 chars, averaged.",
        "- **Thresholds**: STRICT (Jaccard ≥0.9 AND body_sim ≥0.8), "
        "PARTIAL (Jaccard ≥0.5), DIFFERENT otherwise.",
        "",
        f"## Summary",
        "",
        f"- STRICT duplicates: {len(strict)} pair(s) — merge candidates",
        f"- PARTIAL overlaps: {len(partial)} pair(s) — review each",
        f"- Different data: {len(different)} pair(s) — keep both",
        "",
    ]

    def table(rs: list[PairResult], title: str) -> list[str]:
        if not rs:
            return [f"## {title}\n\n(none)\n"]
        out = [
            f"## {title}",
            "",
            "| Dict A | Dict B | Count A | Count B | ∩ | Jaccard | Body Sim | Recommendation |",
            "|---|---|---:|---:|---:|---:|---:|---|",
        ]
        for r in rs:
            out.append(
                f"| `{r.dict_a}` | `{r.dict_b}` | {r.count_a:,} | {r.count_b:,} "
                f"| {r.intersection:,} | {r.jaccard:.3f} | {r.body_sim:.3f} "
                f"| {r.canonical_recommendation()} |"
            )
        out.append("")
        return out

    lines.extend(table(strict, "STRICT Duplicates (Merge)"))
    lines.extend(table(partial, "PARTIAL Overlaps (Review)"))
    lines.extend(table(different, "Different Data (Keep Both)"))

    lines.append("\n## Notes\n")
    lines.append("- `canonical` is chosen by: format rank (XDXF > GRETIL > SANDIC > Apple) "
                 "→ entry count DESC → alphabetical.")
    lines.append("- If user prefers a different canonical, override in slug-mapping.")
    lines.append("- PARTIAL overlaps may represent different editions; consider keeping "
                 "with distinct `edition` in meta.json.")

    out.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
