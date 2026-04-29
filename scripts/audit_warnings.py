"""Audit-A6: warning category cumulative count + per-dict breakdown.

verify.py samples up to 5 warning examples per dict; this script returns the
*exact* count per category × dict so we can classify them as P0 (real defect)
vs P3 (academic notation, expected). Output is a markdown report under
`data/reports/audit-2026-04-30/`.

Categories tracked (mirroring verify.py emission points):
  - FB-4 IAST invalid (skt/pi entry, headword_iast fails is_valid_iast,
    not flagged iast-conversion-failed/headword-script-mixed)
  - FB-4 HK signature (IAST passes is_valid_iast but contains z/J/A pattern)
  - norm mismatch (headword_norm != normalize_headword(headword))
  - FB-8 en token not ASCII (any reverse.en token fails [a-z]+)
  - FB-8 en >40 (length cap violation)
  - FB-8 ko token invalid (any reverse.ko token fails Hangul/Hanja)
  - FB-8 ko >40

Run: uv run python -m scripts.audit_warnings
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from scripts.lib.io import iter_slug_dirs, load_meta
from scripts.lib.normalize import has_hk_signature, is_valid_iast
from scripts.lib.transliterate import normalize_headword

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "data" / "sources"
JSONL = ROOT / "data" / "jsonl"
OUT = ROOT / "data" / "reports" / "audit-2026-04-30" / "audit-A-warnings.md"

IAST_SKIP_FAMILIES = {"ashtadhyayi", "heritage-decl", "dhatupatha"}
IAST_SKIP_SLUGS = {"siddhanta-kaumudi"}

_ASCII = re.compile(r"^[a-z]+$")
_KO = re.compile(r"^[가-힯一-鿿]+$")


def categorize_entry(entry: dict, meta: dict) -> list[tuple[str, str]]:
    """Return list of (category, sample_str) for this entry."""
    out: list[tuple[str, str]] = []
    lang = entry.get("lang")
    headword = entry.get("headword", "")
    iast = entry.get("headword_iast", "")
    family = meta.get("family", "")
    slug = meta.get("slug", "")
    eid = entry.get("id", "?")
    skip_iast = family in IAST_SKIP_FAMILIES or slug in IAST_SKIP_SLUGS

    if lang in ("skt", "pi") and not skip_iast:
        if not is_valid_iast(iast):
            flags = entry.get("flags", [])
            if "iast-conversion-failed" not in flags and "headword-script-mixed" not in flags:
                out.append(("FB-4 IAST invalid", f"{iast!r} in {eid}"))
        elif has_hk_signature(iast):
            out.append(("FB-4 HK signature", f"{iast!r} in {eid}"))

    if entry.get("headword_norm") != normalize_headword(headword):
        out.append(("norm mismatch", f"{entry.get('headword_norm')!r} vs {normalize_headword(headword)!r} in {eid}"))

    rev = entry.get("reverse") or {}
    en = rev.get("en") or []
    if len(en) > 40:
        out.append(("FB-8 en >40", f"len={len(en)} in {eid}"))
    for t in en:
        if not _ASCII.match(t):
            out.append(("FB-8 en token not ASCII", f"{t!r} in {eid}"))
            break
    ko = rev.get("ko") or []
    if len(ko) > 40:
        out.append(("FB-8 ko >40", f"len={len(ko)} in {eid}"))
    for t in ko:
        if not _KO.match(t):
            out.append(("FB-8 ko token invalid", f"{t!r} in {eid}"))
            break

    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample-n", type=int, default=None)
    args = ap.parse_args()

    cat_total: Counter = Counter()
    cat_by_dict: dict[str, Counter] = defaultdict(Counter)
    samples: dict[str, list[str]] = defaultdict(list)
    body_empty_total = 0
    body_empty_by_dict: Counter = Counter()
    flag_total: Counter = Counter()

    n_entries = 0
    for slug_dir in iter_slug_dirs(SOURCES):
        meta = load_meta(slug_dir)
        slug = meta["slug"]
        path = JSONL / f"{slug}.jsonl"
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as f:
            for i, line in enumerate(f):
                if args.sample_n and i >= args.sample_n:
                    break
                if not line.strip():
                    continue
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                n_entries += 1
                # body empty?
                body = e.get("body") or {}
                plain = body.get("plain") or ""
                if not plain.strip():
                    body_empty_total += 1
                    body_empty_by_dict[slug] += 1
                # flags
                for fl in e.get("flags", []) or []:
                    flag_total[fl] += 1
                # warnings
                for cat, sample in categorize_entry(e, meta):
                    cat_total[cat] += 1
                    cat_by_dict[slug][cat] += 1
                    if len(samples[cat]) < 8:
                        samples[cat].append(f"{slug}: {sample}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append("# audit-A-warnings — verify.py warning category breakdown")
    lines.append("")
    lines.append(f"Scanned: **{n_entries:,} entries** across **148 dicts**.")
    lines.append("")
    lines.append("## Warning category totals")
    lines.append("")
    lines.append("| Category | Count |")
    lines.append("|---|---:|")
    for cat, n in cat_total.most_common():
        lines.append(f"| {cat} | {n:,} |")
    lines.append(f"| body-empty | {body_empty_total:,} |")
    lines.append("")

    lines.append("## Top 15 dicts by warning volume")
    lines.append("")
    dict_totals = sorted(
        ((slug, sum(c.values())) for slug, c in cat_by_dict.items()),
        key=lambda x: -x[1],
    )[:15]
    lines.append("| Dict | Total | Breakdown |")
    lines.append("|---|---:|---|")
    for slug, total in dict_totals:
        breakdown = ", ".join(f"{cat}={n:,}" for cat, n in cat_by_dict[slug].most_common())
        lines.append(f"| `{slug}` | {total:,} | {breakdown} |")
    lines.append("")

    lines.append("## body-empty distribution")
    lines.append("")
    lines.append("| Dict | body-empty count |")
    lines.append("|---|---:|")
    for slug, n in body_empty_by_dict.most_common(15):
        lines.append(f"| `{slug}` | {n:,} |")
    lines.append("")

    lines.append("## Flag histogram (entry-level flags[])")
    lines.append("")
    lines.append("| Flag | Count |")
    lines.append("|---|---:|")
    for fl, n in flag_total.most_common(20):
        lines.append(f"| `{fl}` | {n:,} |")
    lines.append("")

    lines.append("## Sample warnings per category (up to 8 each)")
    lines.append("")
    for cat in cat_total.keys():
        lines.append(f"### {cat}")
        lines.append("")
        for s in samples[cat]:
            lines.append(f"- {s}")
        lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"Scanned {n_entries:,} entries.")
    print("Top warnings:")
    for cat, n in cat_total.most_common(10):
        print(f"  {cat:30s} {n:>10,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
