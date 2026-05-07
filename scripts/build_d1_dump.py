"""Generate SQL INSERT statements for D1 bulk import (Phase 5).

Reads `data/jsonl/<slug>.jsonl` for every dict whose entries should be in
D1 (top-1.5M by frequency rank). Emits batched INSERT statements to
`workers/sql/data-NNN.sql` chunks so wrangler can stream them sequentially
without hitting per-request size limits.

Strategy:
  1. Load full frequency.json (rank for every headword_norm in the corpus)
  2. Build a per-rank cutoff: rank ≤ 1,500,000 → include in D1
  3. Walk all JSONL entries; for each, if its headword_norm rank ≤ cutoff,
     emit a row with light fields (id, norm, iast, dict, priority,
     snippet_short, body_ko, target_lang).
  4. Batch ~500 rows per multi-INSERT statement
  5. Split into ~50 MB chunks

Usage:
    uv run python -m scripts.build_d1_dump
    # → workers/sql/data-001.sql .. data-NNN.sql
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterator

from tqdm import tqdm

from scripts.lib.io import iter_jsonl, iter_slugs_by_priority

# Phase 5: top-1.5M ensures D1 free tier (1 GB) fits with headroom.
# Long-tail beyond top-1.5M is reachable via reverse search + Phase 5e R2.
DEFAULT_RANK_CUTOFF = 1_500_000

# Per-multi-INSERT batch size. D1 imposes a per-statement byte limit
# (~100KB observed via SQLITE_TOOBIG). With body_ko up to 1000 chars per row,
# we use 50 rows/statement = ~30KB per INSERT statement, well under limit.
ROWS_PER_INSERT = 50

# Per-file row count target. Each row ~580 bytes → 50K rows ~30 MB.
# Smaller chunks make resumable imports easier.
ROWS_PER_CHUNK = 50_000


def sql_quote(s: str | None) -> str:
    """Quote a string for SQL VALUES. SQLite uses '' to escape single quotes."""
    if s is None or s == "":
        return "NULL"
    return "'" + s.replace("'", "''") + "'"


def emit_row(entry: dict, meta: dict) -> str | None:
    """Return a single VALUES tuple `(...)` or None if the row should be skipped."""
    eid = entry.get("id")
    norm = entry.get("headword_norm")
    iast = entry.get("headword_iast") or norm
    if not eid or not norm:
        return None

    body = entry.get("body", {}) or {}
    snippet = (body.get("snippet_short") or "")[:180]  # FB-1 cap
    body_ko = (body.get("ko") or "")[:1000]  # Reasonable cap for D1 free tier
    priority = int(entry.get("priority", meta.get("priority", 99)))
    target_lang = (
        entry.get("target_lang")
        or meta.get("target_lang")
        or meta.get("lang", "en")
    )

    return (
        "("
        f"{sql_quote(eid)},"
        f"{sql_quote(norm)},"
        f"{sql_quote(iast)},"
        f"{sql_quote(meta['slug'])},"
        f"{priority},"
        f"{sql_quote(snippet)},"
        f"{sql_quote(body_ko)},"
        f"{sql_quote(target_lang)}"
        ")"
    )


def iter_eligible_rows(
    sources: Path,
    jsonl_dir: Path,
    rank_cutoff: int,
    frequency: dict[str, int] | None,
) -> Iterator[str]:
    """Yield SQL VALUES tuples for every entry that passes the rank cutoff."""
    for slug_dir, meta in iter_slugs_by_priority(sources):
        if meta.get("exclude_from_search"):
            continue
        jsonl_path = jsonl_dir / f"{meta['slug']}.jsonl"
        if not jsonl_path.exists():
            continue
        for entry in iter_jsonl(jsonl_path):
            norm = entry.get("headword_norm")
            if not norm:
                continue
            if frequency is not None:
                rank = frequency.get(norm, 10**9)
                if rank > rank_cutoff:
                    continue
            row = emit_row(entry, meta)
            if row:
                yield row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, default=Path("data/sources"))
    parser.add_argument("--jsonl", type=Path, default=Path("data/jsonl"))
    parser.add_argument("--frequency-json", type=Path,
                        default=Path("data/reports/frequency.json"),
                        help="Per-headword rank table from frequency.py "
                             "(generated with --out-full).")
    parser.add_argument("--rank-cutoff", type=int, default=DEFAULT_RANK_CUTOFF)
    parser.add_argument("--out-dir", type=Path,
                        default=Path("workers/sql"))
    args = parser.parse_args()

    # Load frequency table (norm → score, score-DESC sorted in JSON).
    frequency: dict[str, int] | None = None
    if args.frequency_json.exists():
        print(f"Loading {args.frequency_json}…", file=sys.stderr)
        scores = json.loads(args.frequency_json.read_text(encoding="utf-8"))
        # Build rank table: highest-score = rank 1
        ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
        frequency = {hw: r for r, (hw, _) in enumerate(ranked, start=1)}
        print(f"  Loaded ranks for {len(frequency):,} headwords",
              file=sys.stderr)
        print(f"  Cutoff: rank ≤ {args.rank_cutoff:,}", file=sys.stderr)
    else:
        print(f"WARN: {args.frequency_json} missing — emitting ALL rows",
              file=sys.stderr)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    # Wipe stale chunks
    for f in args.out_dir.glob("data-*.sql"):
        f.unlink()

    chunk_idx = 1
    chunk_rows: list[str] = []
    total_rows = 0
    chunk_path: Path | None = None

    def flush_chunk():
        nonlocal chunk_idx, chunk_rows, chunk_path
        if not chunk_rows:
            return
        chunk_path = args.out_dir / f"data-{chunk_idx:03d}.sql"
        with chunk_path.open("w", encoding="utf-8") as f:
            f.write("-- D1 bulk import chunk (Phase 5).\n")
            f.write("-- INSERT batches with ROWS_PER_INSERT VALUES per statement.\n\n")
            for i in range(0, len(chunk_rows), ROWS_PER_INSERT):
                batch = chunk_rows[i : i + ROWS_PER_INSERT]
                f.write(
                    "INSERT OR REPLACE INTO entries "
                    "(id, headword_norm, headword_iast, dict_slug, priority, "
                    "snippet_short, body_ko, target_lang) VALUES\n"
                )
                f.write(",\n".join(batch))
                f.write(";\n\n")
        size_mb = chunk_path.stat().st_size / 1024 / 1024
        print(f"  ✓ Wrote {chunk_path.name} ({len(chunk_rows):,} rows, "
              f"{size_mb:.1f} MB)", file=sys.stderr)
        chunk_idx += 1
        chunk_rows = []

    print("Streaming JSONL → SQL chunks…", file=sys.stderr)
    for row in tqdm(iter_eligible_rows(args.sources, args.jsonl,
                                          args.rank_cutoff, frequency),
                     desc="rows", unit="row", smoothing=0.05):
        chunk_rows.append(row)
        total_rows += 1
        if len(chunk_rows) >= ROWS_PER_CHUNK:
            flush_chunk()

    flush_chunk()
    print(f"\n✓ Total: {total_rows:,} rows across {chunk_idx-1} chunk files",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
