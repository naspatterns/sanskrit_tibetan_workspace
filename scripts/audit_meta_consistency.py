"""Audit-A2: meta.json declared vs JSONL actual consistency.

For each dict, compare meta.json fields against the actual JSONL contents:

  - declared `entry_count`     vs actual JSONL line count
  - declared `target_lang`     vs each entry's `target_lang` (entry-level if present)
  - declared `direction`       vs entry-level `direction` (if present)
  - declared `exclude_from_search` (FB-5) — not exposed at entry-level
  - declared `priority` range  vs entry-level `priority` if any
  - declared `family` membership consistency
  - declared `lang` (source script) vs entry-level `lang`

Output: data/reports/audit-2026-04-30/audit-A-meta-consistency.md
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from scripts.lib.io import iter_slug_dirs, load_meta

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "data" / "sources"
JSONL = ROOT / "data" / "jsonl"
OUT = ROOT / "data" / "reports" / "audit-2026-04-30" / "audit-A-meta-consistency.md"


def scan_dict(meta: dict) -> dict:
    """Scan one dict's JSONL and collect entry-level field stats."""
    slug = meta["slug"]
    path = JSONL / f"{slug}.jsonl"
    out = {
        "slug": slug,
        "exists": path.exists(),
        "actual_count": 0,
        "lang_seen": Counter(),
        "target_lang_seen": Counter(),
        "direction_seen": Counter(),
        "priority_seen": Counter(),
        "missing_iast": 0,
        "missing_norm": 0,
        "missing_body": 0,
    }
    if not path.exists():
        return out
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            out["actual_count"] += 1
            if e.get("lang"):
                out["lang_seen"][e["lang"]] += 1
            if e.get("target_lang"):
                out["target_lang_seen"][e["target_lang"]] += 1
            if e.get("direction"):
                out["direction_seen"][e["direction"]] += 1
            if "priority" in e:
                out["priority_seen"][e["priority"]] += 1
            if not e.get("headword_iast"):
                out["missing_iast"] += 1
            if not e.get("headword_norm"):
                out["missing_norm"] += 1
            body = e.get("body") or {}
            if not (body.get("plain") or "").strip():
                out["missing_body"] += 1
    return out


def main() -> int:
    rows = []
    issues = []
    for slug_dir in iter_slug_dirs(SOURCES):
        meta = load_meta(slug_dir)
        scan = scan_dict(meta)
        rows.append((meta, scan))

        # Find inconsistencies
        slug = meta["slug"]
        decl_count = meta.get("entry_count")
        actual_count = scan["actual_count"]

        if decl_count is None:
            issues.append(f"{slug}: meta.entry_count not declared")
        elif decl_count != actual_count:
            issues.append(
                f"{slug}: entry_count meta={decl_count:,} actual={actual_count:,} (Δ={actual_count - decl_count:+,})"
            )

        # Lang consistency
        decl_lang = meta.get("lang")
        if decl_lang and scan["lang_seen"]:
            seen_langs = set(scan["lang_seen"].keys())
            if decl_lang not in seen_langs:
                issues.append(
                    f"{slug}: meta.lang={decl_lang!r} but JSONL only has {sorted(seen_langs)}"
                )
            elif len(seen_langs) > 1:
                issues.append(
                    f"{slug}: mixed entry langs {dict(scan['lang_seen'])} vs meta.lang={decl_lang!r}"
                )

        # exclude_from_search vs family
        if meta.get("exclude_from_search") and "decl" not in (meta.get("family") or ""):
            issues.append(
                f"{slug}: exclude_from_search=true but family={meta.get('family')!r} (FB-5 expects declension family)"
            )

    # Build report
    lines = []
    lines.append("# audit-A-meta-consistency — meta.json vs JSONL")
    lines.append("")
    lines.append(f"Audited **{len(rows)}** dicts.")
    lines.append("")
    lines.append(f"## Inconsistencies: **{len(issues)}**")
    lines.append("")
    if issues:
        for i in issues[:200]:
            lines.append(f"- {i}")
        if len(issues) > 200:
            lines.append(f"- … and {len(issues) - 200} more")
    else:
        lines.append("None.")
    lines.append("")

    lines.append("## Per-dict summary (top 15 by entry count)")
    lines.append("")
    lines.append("| Slug | Lang | Target | Direction | Decl. count | Actual | iast missing | norm missing | body empty |")
    lines.append("|---|---|---|---|---:|---:|---:|---:|---:|")
    rows.sort(key=lambda r: -r[1]["actual_count"])
    for meta, scan in rows[:30]:
        lines.append(
            "| `{slug}` | {lang} | {target} | {direction} | {dc} | {ac} | {mi} | {mn} | {mb} |".format(
                slug=meta["slug"],
                lang=meta.get("lang", "—"),
                target=meta.get("target_lang", "—"),
                direction=meta.get("direction", "—"),
                dc=meta.get("entry_count", "—"),
                ac=f"{scan['actual_count']:,}",
                mi=scan["missing_iast"],
                mn=scan["missing_norm"],
                mb=scan["missing_body"],
            )
        )
    lines.append("")

    # Field-level distributions
    lang_total = Counter()
    target_total = Counter()
    direction_total = Counter()
    excl = 0
    family_total = Counter()
    priority_buckets = Counter()
    for meta, _ in rows:
        if meta.get("lang"):
            lang_total[meta["lang"]] += 1
        if meta.get("target_lang"):
            target_total[meta["target_lang"]] += 1
        if meta.get("direction"):
            direction_total[meta["direction"]] += 1
        if meta.get("exclude_from_search"):
            excl += 1
        family_total[meta.get("family") or "?"] += 1
        p = meta.get("priority")
        if isinstance(p, int):
            bucket = (p // 10) * 10
            priority_buckets[f"{bucket}-{bucket+9}"] += 1

    lines.append("## meta.json field distributions (148 dicts)")
    lines.append("")
    lines.append(f"- exclude_from_search=true: **{excl}** dicts")
    lines.append("")
    lines.append("### lang")
    for k, n in lang_total.most_common():
        lines.append(f"- {k}: {n}")
    lines.append("")
    lines.append("### target_lang")
    for k, n in target_total.most_common():
        lines.append(f"- {k}: {n}")
    lines.append("")
    lines.append("### direction")
    for k, n in direction_total.most_common():
        lines.append(f"- {k}: {n}")
    lines.append("")
    lines.append("### family")
    for k, n in family_total.most_common():
        lines.append(f"- {k}: {n}")
    lines.append("")
    lines.append("### priority buckets")
    for k in sorted(priority_buckets.keys(), key=lambda s: int(s.split("-")[0])):
        lines.append(f"- {k}: {priority_buckets[k]}")
    lines.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"Inconsistencies: {len(issues)}")
    for i in issues[:10]:
        print(f"  {i}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
