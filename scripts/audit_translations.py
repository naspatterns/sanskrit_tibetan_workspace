"""Audit Korean translation coverage across all JSONL dicts (FB-2).

For each dict in data/sources, reports:
  - Total entries
  - Entries with `body.ko` present and non-empty
  - Coverage percentage
  - Target language (from meta.json) — highlights DE/FR/LA/RU dicts

Output:
  - data/reports/translation_coverage.md — human-readable summary
  - data/reports/translate_todo.json — machine-readable list for Phase 2 batch re-translate
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from scripts.lib.io import iter_slug_dirs, load_meta


@dataclass
class DictCoverage:
    slug: str
    short_name: str
    lang: str
    target_lang: str
    direction: str
    priority: int
    total: int
    translated: int

    @property
    def coverage(self) -> float:
        return self.translated / self.total if self.total else 0.0

    @property
    def priority_for_batch(self) -> int:
        """Phase 2 re-translation priority: DE/FR/LA/RU first (FB-2 focus)."""
        return {"de": 1, "fr": 2, "la": 3, "ru": 4, "en": 9, "sa": 10, "bo": 11}.get(
            self.target_lang, 5
        )


def audit_dict(slug_dir: Path, jsonl_dir: Path) -> DictCoverage | None:
    meta = load_meta(slug_dir)
    jsonl_path = jsonl_dir / f"{meta['slug']}.jsonl"
    if not jsonl_path.exists():
        return None

    total = 0
    translated = 0
    # Substring pre-filter: entries without "ko": in the raw line can't be
    # translated, so skip json.loads on them. Saves most of the runtime for
    # dicts with low Korean coverage (~60-80% of entries are filter-skippable).
    with jsonl_path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            total += 1
            if '"ko"' not in line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            ko = entry.get("body", {}).get("ko", "")
            if ko and len(ko.strip()) > 0:
                translated += 1

    return DictCoverage(
        slug=meta["slug"],
        short_name=meta["short_name"],
        lang=meta["lang"],
        target_lang=meta["target_lang"],
        direction=meta["direction"],
        priority=meta["priority"],
        total=total,
        translated=translated,
    )


def write_report(coverages: list[DictCoverage], out: Path) -> None:
    # Group by target_lang
    by_lang: dict[str, list[DictCoverage]] = {}
    for c in coverages:
        by_lang.setdefault(c.target_lang, []).append(c)

    total_entries = sum(c.total for c in coverages)
    total_translated = sum(c.translated for c in coverages)
    overall = total_translated / total_entries if total_entries else 0.0

    lines = [
        "# Korean Translation Coverage Audit (FB-2)",
        "",
        f"Scan of {len(coverages)} dictionaries · {total_entries:,} entries.",
        f"Overall coverage: **{overall:.1%}** ({total_translated:,} translated).",
        "",
        "## Coverage by Target Language",
        "",
        "| Target | Dicts | Entries | Translated | Coverage |",
        "|--------|------:|--------:|-----------:|---------:|",
    ]
    for lang in sorted(by_lang, key=lambda l: -sum(c.total for c in by_lang[l])):
        items = by_lang[lang]
        entries = sum(c.total for c in items)
        translated = sum(c.translated for c in items)
        cov = translated / entries if entries else 0.0
        lines.append(
            f"| {lang} | {len(items)} | {entries:,} | {translated:,} | {cov:.1%} |"
        )
    lines.append("")

    # Phase 2 batch re-translation targets: non-Korean target langs with low coverage
    lines.append("## Phase 2 Re-translation Candidates (FB-2)")
    lines.append("")
    lines.append("Dicts where `target_lang` is DE/FR/LA/RU (non-English European) "
                 "and Korean coverage is below 95%.")
    lines.append("")
    lines.append("| Priority | Slug | Target | Total | Translated | Coverage |")
    lines.append("|---------:|------|--------|------:|-----------:|---------:|")
    euro = [c for c in coverages if c.target_lang in ("de", "fr", "la", "ru")]
    euro.sort(key=lambda c: (c.priority_for_batch, -c.total))
    for c in euro:
        if c.coverage < 0.95:
            lines.append(
                f"| {c.priority} | `{c.slug}` | {c.target_lang} | {c.total:,} "
                f"| {c.translated:,} | {c.coverage:.1%} |"
            )
    lines.append("")

    # Per-dict full listing
    lines.append("## All Dicts (sorted by priority)")
    lines.append("")
    lines.append("| Priority | Slug | Direction | Total | Translated | Coverage |")
    lines.append("|---------:|------|-----------|------:|-----------:|---------:|")
    for c in sorted(coverages, key=lambda c: c.priority):
        lines.append(
            f"| {c.priority} | `{c.slug}` | {c.direction} | {c.total:,} "
            f"| {c.translated:,} | {c.coverage:.1%} |"
        )

    out.write_text("\n".join(lines), encoding="utf-8")


def write_todo(coverages: list[DictCoverage], out: Path) -> None:
    """Machine-readable list of (slug, target_lang, entries_to_translate) for Phase 2."""
    todo = []
    for c in coverages:
        if c.target_lang in ("de", "fr", "la", "ru") and c.coverage < 0.95:
            todo.append({
                "slug": c.slug,
                "target_lang": c.target_lang,
                "total": c.total,
                "translated": c.translated,
                "pending": c.total - c.translated,
                "priority": c.priority,
            })
    todo.sort(key=lambda x: (-x["pending"], x["priority"]))
    out.write_text(json.dumps(todo, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, default=Path("data/sources"))
    parser.add_argument("--jsonl", type=Path, default=Path("data/jsonl"))
    parser.add_argument("--out-report", type=Path,
                        default=Path("data/reports/translation_coverage.md"))
    parser.add_argument("--out-todo", type=Path,
                        default=Path("data/reports/translate_todo.json"))
    args = parser.parse_args()

    args.out_report.parent.mkdir(parents=True, exist_ok=True)

    slug_dirs = iter_slug_dirs(args.sources)

    coverages: list[DictCoverage] = []
    for slug_dir in slug_dirs:
        cov = audit_dict(slug_dir, args.jsonl)
        if cov:
            coverages.append(cov)

    if not coverages:
        print("No JSONL files found to audit.")
        return 1

    write_report(coverages, args.out_report)
    write_todo(coverages, args.out_todo)

    overall_total = sum(c.total for c in coverages)
    overall_translated = sum(c.translated for c in coverages)
    overall = overall_translated / overall_total if overall_total else 0.0
    print(f"✓ Audited {len(coverages)} dicts · {overall_total:,} entries")
    print(f"  Overall Korean coverage: {overall:.2%} ({overall_translated:,} / {overall_total:,})")
    print(f"  Report: {args.out_report}")
    print(f"  Todo (machine-readable): {args.out_todo}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
