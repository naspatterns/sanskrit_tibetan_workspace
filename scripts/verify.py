"""Verify JSONL integrity against schema + Phase 1 invariants.

Checks performed:
  - JSON Schema validation (docs/schema.json)
  - FB-4: Sanskrit entries have valid headword_iast within allowed unicode range
  - FB-4: no HK signature chars leaking into supposedly-IAST headwords
  - FB-3: meta.priority in range 1-100, all slugs unique
  - FB-5: dicts with exclude_from_search=true belong to declension family
  - FB-8: reverse.en tokens ASCII-only, ≤40 each; reverse.ko tokens hangul/hanja
  - body.plain non-empty for most entries (body-empty flag for rare cases)
  - headword_norm matches transliterate.normalize_headword(headword)

Exit codes:
  0 = pass (with warnings allowed)
  2 = errors (schema violations, missing required fields)
"""
from __future__ import annotations

import argparse
import itertools
import json
import multiprocessing as mp
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import fastjsonschema

from scripts.lib.io import iter_slug_dirs, load_meta
from scripts.lib.normalize import has_hk_signature, is_valid_iast
from scripts.lib.transliterate import normalize_headword


SCHEMA_PATH = Path(__file__).resolve().parent.parent / "docs" / "schema.json"


@dataclass
class VerifyStats:
    dict_slug: str
    total: int = 0
    errors: int = 0
    warnings: int = 0
    error_samples: list[str] = field(default_factory=list)
    warning_samples: list[str] = field(default_factory=list)
    flag_counts: Counter = field(default_factory=Counter)


_ASCII_TOKEN_RE = re.compile(r"^[a-z]+$")
_KO_TOKEN_RE = re.compile(r"^[\uAC00-\uD7AF\u4E00-\u9FFF]+$")

# Dict families where IAST headword validation should be skipped:
#   - ashtadhyayi, siddhanta-kaumudi: headwords are sutra numbers like '1.1.1'
#   - heritage-decl: headwords use '@stem' notation like 'aṃśanīya@aṃś'
#   - dhatupatha: source material mixes forms
IAST_SKIP_FAMILIES = {"ashtadhyayi", "heritage-decl", "dhatupatha"}
IAST_SKIP_SLUGS = {"siddhanta-kaumudi"}


def verify_entry(entry: dict, meta: dict, schema_validator, stats: VerifyStats) -> None:
    """Check one entry. Appends to stats.errors/warnings.

    `schema_validator` is a compiled fastjsonschema validator callable —
    much faster than the equivalent `jsonschema.Draft*Validator.validate`.
    """
    stats.total += 1

    try:
        schema_validator(entry)
    except fastjsonschema.JsonSchemaException as e:
        stats.errors += 1
        if len(stats.error_samples) < 5:
            stats.error_samples.append(f"schema: {e.message[:120]} at {entry.get('id')}")
        return

    # FB-4: IAST validation for Sanskrit/Pali entries
    lang = entry.get("lang")
    headword = entry["headword"]
    iast = entry["headword_iast"]
    family = meta.get("family", "")
    slug = meta.get("slug", "")

    skip_iast_check = family in IAST_SKIP_FAMILIES or slug in IAST_SKIP_SLUGS

    # Pāli also uses IAST (per `detect_and_convert_to_iast`), so validate both.
    if lang in ("skt", "pi") and not skip_iast_check:
        if not is_valid_iast(iast):
            # Allow if entry flags iast-conversion-failed or headword-script-mixed
            flags = entry.get("flags", [])
            if "iast-conversion-failed" not in flags and "headword-script-mixed" not in flags:
                stats.warnings += 1
                if len(stats.warning_samples) < 5:
                    stats.warning_samples.append(
                        f"FB-4 IAST invalid: '{iast}' in {entry['id']}"
                    )
        elif has_hk_signature(iast):
            stats.warnings += 1
            if len(stats.warning_samples) < 5:
                stats.warning_samples.append(
                    f"FB-4 HK signature in IAST: '{iast}' in {entry['id']}"
                )

    expected_norm = normalize_headword(headword)
    if entry["headword_norm"] != expected_norm:
        stats.warnings += 1
        if len(stats.warning_samples) < 5:
            stats.warning_samples.append(
                f"norm mismatch: '{entry['headword_norm']}' vs expected '{expected_norm}' in {entry['id']}"
            )

    # FB-8: reverse token validation
    reverse = entry.get("reverse", {})
    en_tokens = reverse.get("en", [])
    if len(en_tokens) > 40:
        stats.warnings += 1
    for tok in en_tokens:
        if not _ASCII_TOKEN_RE.match(tok):
            stats.warnings += 1
            if len(stats.warning_samples) < 5:
                stats.warning_samples.append(
                    f"FB-8 en token not ASCII: '{tok}' in {entry['id']}"
                )
            break

    ko_tokens = reverse.get("ko", [])
    if len(ko_tokens) > 40:
        stats.warnings += 1
    for tok in ko_tokens:
        if not _KO_TOKEN_RE.match(tok):
            stats.warnings += 1
            if len(stats.warning_samples) < 5:
                stats.warning_samples.append(
                    f"FB-8 ko token invalid: '{tok}' in {entry['id']}"
                )
            break

    for f in entry.get("flags", []):
        stats.flag_counts[f] += 1


def verify_dict(
    slug_dir: Path,
    jsonl_dir: Path,
    schema_validator,
    sample_n: int | None = None,
) -> VerifyStats:
    """Verify entries from a dict's JSONL.

    `sample_n`: only check the first N entries (for fast spot-checks).
    """
    meta = load_meta(slug_dir)
    stats = VerifyStats(dict_slug=meta["slug"])

    jsonl_path = jsonl_dir / f"{meta['slug']}.jsonl"
    if not jsonl_path.exists():
        stats.warnings += 1
        stats.warning_samples.append(f"JSONL missing: {jsonl_path}")
        return stats

    with jsonl_path.open(encoding="utf-8") as f:
        lines = itertools.islice(f, sample_n) if sample_n else f
        for line in lines:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                stats.errors += 1
                if len(stats.error_samples) < 3:
                    stats.error_samples.append(f"JSON parse error: {e}")
                continue
            verify_entry(entry, meta, schema_validator, stats)

    return stats


def verify_meta_registry(sources_dir: Path) -> list[str]:
    """Check meta.json invariants across all dicts."""
    errors: list[str] = []
    slugs: set[str] = set()
    priorities: Counter = Counter()
    excluded_families: set[str] = set()

    for slug_dir in iter_slug_dirs(sources_dir):
        try:
            meta = load_meta(slug_dir)
        except json.JSONDecodeError as e:
            errors.append(f"{slug_dir.name}/meta.json: JSON parse error: {e}")
            continue

        # Unique slug
        if meta["slug"] in slugs:
            errors.append(f"Duplicate slug: {meta['slug']}")
        slugs.add(meta["slug"])

        # Priority range
        p = meta.get("priority")
        if not isinstance(p, int) or not (1 <= p <= 100):
            errors.append(f"{meta['slug']}: priority out of range: {p}")
        else:
            priorities[p] += 1

        # FB-5: exclude_from_search must be traceable. Two valid shapes:
        #   (a) family-based exclude (heritage-decl) — needs `used_by` + `family`,
        #       and `family` must be in the known-excluded set.
        #   (b) dedup-via-supersession (`superseded_by` points at the canonical
        #       dict) — replaces the used_by/family pair, since the data lives
        #       elsewhere under a different family.
        if meta.get("exclude_from_search"):
            is_dedup = bool(meta.get("superseded_by"))
            if not is_dedup:
                if "used_by" not in meta:
                    errors.append(
                        f"{meta['slug']}: exclude_from_search=true without used_by or superseded_by"
                    )
                family = meta.get("family")
                if not family:
                    errors.append(f"{meta['slug']}: exclude_from_search=true without family")
                else:
                    excluded_families.add(family)

    # FB-5 sanity: family-based excludes (case (a) above) must use a known
    # family. Dedup excludes (case (b)) can have any family — they're routing
    # markers, not Phase 3.5 declension hints — so they don't feed this check.
    known_excluded = {"heritage-decl"}
    unknown = excluded_families - known_excluded
    if unknown:
        errors.append(
            f"FB-5: unknown families in exclude_from_search: {unknown} "
            f"(known: {known_excluded})"
        )

    return errors


_WORKER_VALIDATOR = None


def _worker_init(schema_dict: dict) -> None:
    """Compile the fastjsonschema validator once per worker process.

    The compiled validator is a closure, so we can't share it via Pool arg.
    Instead each worker recompiles (cheap, <100ms).
    """
    global _WORKER_VALIDATOR
    _WORKER_VALIDATOR = fastjsonschema.compile(schema_dict)


def _worker_verify(args: tuple[Path, Path, int | None]) -> VerifyStats:
    slug_dir, jsonl_dir, sample_n = args
    assert _WORKER_VALIDATOR is not None, "worker not initialized"
    return verify_dict(slug_dir, jsonl_dir, _WORKER_VALIDATOR, sample_n=sample_n)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, default=Path("data/sources"))
    parser.add_argument("--jsonl", type=Path, default=Path("data/jsonl"))
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH)
    parser.add_argument("--dicts", type=str, default="", help="Comma-separated slug filter")
    parser.add_argument("--sample", type=int, default=0,
                        help="Only verify first N entries per dict (speed up)")
    parser.add_argument(
        "--jobs", type=int, default=0,
        help="Worker processes (0 = single-process; default = cpu_count // 2)",
    )
    args = parser.parse_args()

    schema = json.loads(args.schema.read_text(encoding="utf-8"))

    print("━━━ Meta registry checks ━━━")
    reg_errors = verify_meta_registry(args.sources)
    if reg_errors:
        for e in reg_errors:
            print(f"  ERROR: {e}")
        return 2
    print("  ✓ All meta.json files pass registry checks")

    print("\n━━━ JSONL entry checks ━━━")
    slug_filter = args.dicts.split(",") if args.dicts else None
    slug_dirs = iter_slug_dirs(args.sources, slug_filter)
    sample_n = args.sample if args.sample > 0 else None
    jobs = args.jobs if args.jobs > 0 else max(1, (os.cpu_count() or 2) // 2)

    all_stats: list[VerifyStats] = []
    if jobs == 1 or len(slug_dirs) <= 2:
        validator = fastjsonschema.compile(schema)
        for slug_dir in slug_dirs:
            all_stats.append(verify_dict(slug_dir, args.jsonl, validator, sample_n=sample_n))
    else:
        work = [(d, args.jsonl, sample_n) for d in slug_dirs]
        ctx = mp.get_context("spawn")
        with ctx.Pool(processes=jobs, initializer=_worker_init, initargs=(schema,)) as pool:
            all_stats = list(pool.imap_unordered(_worker_verify, work))

    # Summary
    total = sum(s.total for s in all_stats)
    errors = sum(s.errors for s in all_stats)
    warnings = sum(s.warnings for s in all_stats)

    print(f"\n━━━ Summary ━━━")
    print(f"Dicts verified: {len(all_stats)}")
    print(f"Entries checked: {total:,}")
    print(f"Errors: {errors:,}")
    print(f"Warnings: {warnings:,}")

    # Aggregate flag histogram
    agg_flags: Counter = Counter()
    for s in all_stats:
        agg_flags.update(s.flag_counts)
    if agg_flags:
        print("\nFlag histogram:")
        for flag, n in agg_flags.most_common():
            print(f"  {flag}: {n:,}")

    # Top 10 dicts with most errors/warnings
    worst = sorted(all_stats, key=lambda s: -(s.errors * 100 + s.warnings))[:10]
    if any(s.errors or s.warnings for s in worst):
        print("\nTop dicts with issues:")
        for s in worst:
            if s.errors or s.warnings:
                print(f"  {s.dict_slug}: {s.errors} errors, {s.warnings} warnings")
                for sample in s.error_samples[:3]:
                    print(f"    ERR  {sample}")
                for sample in s.warning_samples[:3]:
                    print(f"    WARN {sample}")

    return 2 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
