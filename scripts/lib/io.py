"""Shared I/O helpers for Phase 1 scripts.

Consolidates v1 DB access, meta.json loading, slug enumeration, and JSONL
streaming that were repeated across build_meta / extract_from_v1 / verify /
audit_translations / detect_duplicates.
"""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Iterator
from pathlib import Path


V1_DB = Path(
    "/Users/jibak/Library/CloudStorage/GoogleDrive-naspatterns@gmail.com/"
    "내 드라이브/haMsa CODE/sanskrit_tibetan_reading_workspace/build/dict.sqlite"
)


def open_v1_readonly() -> sqlite3.Connection:
    """Open v1 `dict.sqlite` in read-only URI mode. Caller must close."""
    return sqlite3.connect(f"file:{V1_DB}?mode=ro", uri=True)


def load_meta(slug_dir: Path) -> dict:
    """Load `meta.json` under a slug directory. Raises on malformed JSON —
    verify.py wraps its own call to report per-dict instead of crashing."""
    return json.loads((slug_dir / "meta.json").read_text(encoding="utf-8"))


def iter_slug_dirs(
    sources: Path, slug_filter: Iterable[str] | None = None
) -> list[Path]:
    """Return sorted slug directories under `sources/` that hold a meta.json.

    `slug_filter` restricts to specific slugs (by directory basename).
    """
    filter_set = set(slug_filter) if slug_filter else None
    dirs = sorted(
        d for d in sources.iterdir()
        if d.is_dir() and (d / "meta.json").exists()
    )
    if filter_set is not None:
        dirs = [d for d in dirs if d.name in filter_set]
    return dirs


def iter_jsonl(path: Path, limit: int | None = None) -> Iterator[dict]:
    """Stream parsed entries from a JSONL file.

    Blank lines and `JSONDecodeError` rows are silently skipped (callers that
    need to count parse failures should inline the open loop instead).
    `limit` stops after that many yielded entries.
    """
    yielded = 0
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            yield entry
            yielded += 1
            if limit is not None and yielded >= limit:
                return
