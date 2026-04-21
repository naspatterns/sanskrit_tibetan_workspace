"""Extract v1 dict.sqlite entries to per-dict JSONL files.

For each slug in data/sources/<slug>/meta.json, reads entries from v1's
`dict.sqlite` (matching by meta.v1_name or meta.merged_from) and emits
data/jsonl/<slug>.jsonl with one Entry per line per the schema.json.

Phase 1 responsibilities covered:
  - FB-1: smart snippet extraction (body.snippet_short / snippet_medium)
  - FB-3: priority + tier from meta.json
  - FB-4: mandatory headword_iast for Sanskrit entries
  - FB-5: exclude_from_search flag preserved in meta only (all dicts extracted)
  - FB-8: reverse.en[] / reverse.ko[] tokens
  - body.senses[] when meta.sense_separator is defined

Usage:
    uv run python -m scripts.extract_from_v1                     # all 130 dicts
    uv run python -m scripts.extract_from_v1 --dicts apte,mw     # selected slugs
    uv run python -m scripts.extract_from_v1 --limit 100         # dry-run
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from tqdm import tqdm

from scripts.lib.html_utils import strip_markup
from scripts.lib.io import V1_DB, iter_slug_dirs, load_meta, open_v1_readonly
from scripts.lib.normalize import has_hk_signature
from scripts.lib.reverse_tokens import extract_en_tokens, extract_ko_tokens
from scripts.lib.snippet import extract_senses, extract_snippets
from scripts.lib.transliterate import detect_and_convert_to_iast, normalize_headword


@dataclass
class DictStats:
    slug: str
    expected: int
    extracted: int = 0
    iast_failed: int = 0
    empty_body: int = 0
    senses_parsed: int = 0
    reverse_ko_count: int = 0
    flags_histogram: Counter = field(default_factory=Counter)


def v1_dict_ids(conn: sqlite3.Connection, names: list[str]) -> list[tuple[int, str]]:
    """Return [(dict_id, v1_name), ...] for the given v1 names. Missing names skipped with warning."""
    result: list[tuple[int, str]] = []
    for name in names:
        row = conn.execute("SELECT id FROM dictionaries WHERE name = ?", (name,)).fetchone()
        if row is None:
            print(f"    WARN: v1 dict not found: {name}", file=sys.stderr)
            continue
        result.append((row[0], name))
    return result


def iter_v1_entries(
    conn: sqlite3.Connection, dict_ids: list[tuple[int, str]], limit: int | None = None
) -> Iterator[tuple[int, str, str, str]]:
    """Yield (v1_entry_id, v1_dict_name, headword, body, body_ko)."""
    for dict_id, dict_name in dict_ids:
        q = "SELECT id, headword, body, body_ko FROM entries WHERE dict_id = ? ORDER BY id"
        if limit:
            q += f" LIMIT {limit}"
        cur = conn.execute(q, (dict_id,))
        for row in cur:
            yield (row[0], dict_name, row[1] or "", row[2] or "", row[3] or "")


def _clean_headword(raw: str) -> str:
    """Strip v1 data-quality artifacts from headword:
      - Cut at first newline / tab / carriage return (body bled into headword)
      - Cut at first '{' (dhatupatha-krsnacarya embeds JSON)
      - Cut at first '<' (stray markup leakage)
      - Trim whitespace
    """
    if not raw:
        return ""
    hw = raw
    for delim in ("\n", "\t", "\r", "{", "<"):
        idx = hw.find(delim)
        if idx > 0:
            hw = hw[:idx]
    return hw.strip()


def make_entry(
    meta: dict,
    seq: int,
    v1_entry_id: int,
    v1_dict_name: str,
    raw_headword: str,
    raw_body: str,
    raw_body_ko: str,
    stats: DictStats,
    cleaned: str | None = None,
) -> dict | None:
    """Build one Entry dict from a v1 row. Returns None for entries to skip.

    `cleaned`: pre-cleaned headword from the caller, to avoid re-running
    `_clean_headword` on merged-dict dedup paths.
    """
    headword = cleaned if cleaned is not None else _clean_headword(raw_headword)
    if not headword:
        return None

    entry: dict = {
        "id": f"{meta['slug']}-{seq:06d}",
        "dict": meta["slug"],
        "headword": headword,
        "lang": meta["lang"],
        "body": {},
    }

    # FB-4: headword_iast + headword_norm
    lang = meta["lang"]
    flags: list[str] = []

    if lang in ("skt", "pi"):
        headword_iast = detect_and_convert_to_iast(headword)
        if not headword_iast:
            headword_iast = headword  # fallback to raw
            flags.append("iast-conversion-failed")
            stats.iast_failed += 1
        elif has_hk_signature(headword_iast):
            # Suspect: conversion didn't complete
            flags.append("headword-script-mixed")
    elif lang == "bo":
        # Tibetan keeps Wylie as-is (IAST is Skt-specific)
        headword_iast = headword
    elif lang == "en":
        # English reverse dicts: headword IS the English word
        headword_iast = headword
    else:
        headword_iast = headword

    entry["headword_iast"] = headword_iast
    # For English headwords (reverse dicts), skip HK detection which can misfire on
    # capitalized English words. Simple lowercase+strip is the correct norm here.
    if lang == "en":
        entry["headword_norm"] = headword.lower().strip()
    else:
        entry["headword_norm"] = normalize_headword(headword)

    body: dict = {}
    if raw_body:
        body["raw"] = raw_body
        plain = strip_markup(raw_body, source_format=meta["source_format"], flags=flags)
        body["plain"] = plain
        if not plain:
            flags.append("body-empty")
            stats.empty_body += 1
        else:
            # Smart snippets (FB-1)
            sep = meta.get("sense_separator")
            snippet_short, snippet_medium = extract_snippets(plain, sense_separator=sep)
            if snippet_short:
                body["snippet_short"] = snippet_short
            if snippet_medium:
                body["snippet_medium"] = snippet_medium

            # Structured senses: attempt whenever meta defines sense_separator.
            # extract_senses returns [] for text without recognizable structure,
            # so we don't over-emit on poorly-structured sources.
            if sep:
                senses = extract_senses(plain, sense_separator=sep)
                if senses:
                    body["senses"] = senses
                    stats.senses_parsed += 1
    else:
        flags.append("body-empty")
        stats.empty_body += 1
        body["plain"] = ""

    if raw_body_ko:
        body["ko"] = raw_body_ko

    entry["body"] = body

    # FB-8: reverse tokens
    reverse: dict = {}
    plain_body = body.get("plain", "")
    if plain_body:
        tokens_en = extract_en_tokens(plain_body)
        if tokens_en:
            reverse["en"] = tokens_en
    if raw_body_ko:
        tokens_ko = extract_ko_tokens(raw_body_ko)
        if tokens_ko:
            reverse["ko"] = tokens_ko
            stats.reverse_ko_count += 1
    if reverse:
        entry["reverse"] = reverse

    entry["priority"] = meta["priority"]
    entry["tier"] = meta["tier"]
    if meta.get("license"):
        entry["license"] = meta["license"]
    entry["source_meta"] = {
        "v1_dict_name": v1_dict_name,
        "v1_entry_id": v1_entry_id,
    }
    if flags:
        entry["flags"] = flags
        stats.flags_histogram.update(flags)

    return entry


def extract_dict(
    conn: sqlite3.Connection,
    slug_dir: Path,
    out_dir: Path,
    limit: int | None = None,
) -> DictStats:
    meta = load_meta(slug_dir)
    stats = DictStats(slug=meta["slug"], expected=meta.get("expected_entries", 0))

    # Determine which v1 names to read (includes merged_from).
    # For merged dicts, put the canonical v1_name FIRST so de-dup prefers its
    # body when the same headword appears in multiple sources.
    merged = meta.get("merged_from")
    if merged:
        primary = meta["v1_name"]
        v1_names = [primary] + [n for n in merged if n != primary]
        is_merged = True
    else:
        v1_names = [meta["v1_name"]]
        is_merged = False

    dict_ids = v1_dict_ids(conn, v1_names)
    if not dict_ids:
        print(f"  SKIP {meta['slug']}: no matching v1 dicts", file=sys.stderr)
        return stats

    out_file = out_dir / f"{meta['slug']}.jsonl"
    tmp_file = out_file.with_suffix(".jsonl.tmp")
    seen_norms: set[str] = set()  # populated only when is_merged
    dup_skipped = 0
    seq = 0
    with tmp_file.open("w", encoding="utf-8") as fp:
        for v1_entry_id, v1_dict_name, headword, body, body_ko in iter_v1_entries(
            conn, dict_ids, limit
        ):
            # For merged dicts, de-dup by normalized headword. First occurrence
            # wins (primary source ordered first). Clean raw headword first so
            # dirty data (newlines, JSON blobs) doesn't defeat the dedup.
            cleaned_hw: str | None = None
            if is_merged:
                cleaned_hw = _clean_headword(headword)
                if not cleaned_hw:
                    continue
                norm = normalize_headword(cleaned_hw)
                if not norm:
                    continue
                if norm in seen_norms:
                    dup_skipped += 1
                    continue
                seen_norms.add(norm)

            seq += 1
            entry = make_entry(
                meta, seq, v1_entry_id, v1_dict_name, headword, body, body_ko,
                stats, cleaned=cleaned_hw,
            )
            if entry is None:
                continue
            fp.write(json.dumps(entry, ensure_ascii=False))
            fp.write("\n")
            stats.extracted += 1

    if is_merged and dup_skipped:
        stats.flags_histogram["merged-dup-skipped"] = dup_skipped

    # Atomic rename so an interrupted extract leaves the previous good file intact
    tmp_file.replace(out_file)

    return stats


_WORKER_CONN: sqlite3.Connection | None = None


def _worker_init() -> None:
    """Open a per-worker readonly SQLite connection and stash on module globals.

    SQLite's `?mode=ro&immutable` URI lets many processes read concurrently.
    """
    global _WORKER_CONN
    _WORKER_CONN = open_v1_readonly()


def _worker_extract(args: tuple[Path, Path, int | None]) -> DictStats:
    slug_dir, out_dir, limit = args
    assert _WORKER_CONN is not None, "worker not initialized"
    return extract_dict(_WORKER_CONN, slug_dir, out_dir, limit=limit)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, default=Path("data/sources"))
    parser.add_argument("--out", type=Path, default=Path("data/jsonl"))
    parser.add_argument("--dicts", type=str, default="", help="Comma-separated slug filter")
    parser.add_argument("--limit", type=int, default=None, help="Per-dict entry limit")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument(
        "--jobs", type=int, default=0,
        help="Worker processes (0 = single-process; default = cpu_count // 2)",
    )
    args = parser.parse_args()

    if not V1_DB.exists():
        print(f"ERROR: v1 DB not found at {V1_DB}", file=sys.stderr)
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    slug_filter = args.dicts.split(",") if args.dicts else None
    slug_dirs = iter_slug_dirs(args.sources, slug_filter)

    if args.skip_existing:
        slug_dirs = [d for d in slug_dirs if not (args.out / f"{d.name}.jsonl").exists()]

    if not slug_dirs:
        print("No matching dicts.", file=sys.stderr)
        return 1

    jobs = args.jobs if args.jobs > 0 else max(1, (os.cpu_count() or 2) // 2)
    print(f"Extracting {len(slug_dirs)} dicts from v1 → {args.out}/ (jobs={jobs})")
    if args.limit:
        print(f"  (dry-run: limit {args.limit} per dict)")
    print()

    all_stats: list[DictStats] = []
    if jobs == 1:
        conn = open_v1_readonly()
        try:
            for slug_dir in tqdm(slug_dirs, desc="dicts", unit="dict"):
                all_stats.append(extract_dict(conn, slug_dir, args.out, limit=args.limit))
        finally:
            conn.close()
    else:
        work = [(d, args.out, args.limit) for d in slug_dirs]
        # spawn context: safe for lxml + sqlite (fork inherits parent's fd state,
        # which is fragile for sqlite connections).
        ctx = mp.get_context("spawn")
        with ctx.Pool(processes=jobs, initializer=_worker_init) as pool:
            for stats in tqdm(
                pool.imap_unordered(_worker_extract, work),
                total=len(work), desc="dicts", unit="dict",
            ):
                all_stats.append(stats)

    total_extracted = sum(s.extracted for s in all_stats)
    total_iast_failed = sum(s.iast_failed for s in all_stats)
    total_empty = sum(s.empty_body for s in all_stats)
    total_senses = sum(s.senses_parsed for s in all_stats)
    total_ko = sum(s.reverse_ko_count for s in all_stats)
    agg_flags: Counter = Counter()
    for s in all_stats:
        agg_flags.update(s.flags_histogram)

    print("\n━━━ Extract Summary ━━━")
    print(f"Dicts processed: {len(all_stats)}")
    print(f"Total entries extracted: {total_extracted:,}")
    print(f"  IAST conversion issues: {total_iast_failed:,}")
    print(f"  Empty body: {total_empty:,}")
    print(f"  Senses parsed: {total_senses:,}")
    print(f"  Entries with Korean reverse tokens: {total_ko:,}")

    if agg_flags:
        print("\nFlag histogram:")
        for flag, n in agg_flags.most_common():
            print(f"  {flag}: {n:,}")

    print("\nDicts with count deviation >5%:")
    for s in all_stats:
        if s.expected > 0:
            deviation = abs(s.extracted - s.expected) / s.expected
            if deviation > 0.05:
                print(f"  {s.slug}: expected {s.expected:,} got {s.extracted:,} ({deviation:.1%})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
