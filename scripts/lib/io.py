"""Shared I/O helpers for Phase 1+2 scripts.

Consolidates v1 DB access, meta.json loading, slug enumeration, JSONL
streaming, top-10K loading, and msgpack+zstd I/O.
"""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Iterator
from pathlib import Path

import msgpack
import zstandard as zstd


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


def iter_slugs_by_priority(
    sources: Path, slug_filter: Iterable[str] | None = None
) -> list[tuple[Path, dict]]:
    """Return `[(slug_dir, meta), ...]` priority-ASC-sorted.

    Folds the common pattern of: list slug dirs → load each meta → sort by
    priority. Avoids re-reading meta.json during sort-key lookups.
    """
    pairs = [(d, load_meta(d)) for d in iter_slug_dirs(sources, slug_filter)]
    pairs.sort(key=lambda pair: (pair[1]["priority"], pair[1]["slug"]))
    return pairs


def load_top10k(path: Path) -> list[str]:
    """Load the top-N headword_norm list (one per line, blanks skipped)."""
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_msgpack_zst(
    data: object,
    path: Path,
    level: int = 19,
    long_range: bool = False,
) -> tuple[int, int]:
    """Serialize `data` as msgpack, zstd-compress, write atomically to `path`.

    Returns `(raw_size, compressed_size)` so callers can report compression
    ratio without re-packing.

    `long_range=True` enables long-range matching with window_log=27 (128 MB
    window) — squeezes out an extra ~3-5% on highly redundant data like
    tier0.msgpack.zst (P0-3 fix, Phase 3.6, to fit Cloudflare Pages 25 MiB
    single-file limit). fzstd 0.1.x supports any standard window size.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    packed = msgpack.packb(data, use_bin_type=True)
    if long_range:
        params = zstd.ZstdCompressionParameters.from_level(
            level, window_log=27, enable_ldm=True
        )
        compressed = zstd.ZstdCompressor(compression_params=params).compress(packed)
    else:
        compressed = zstd.ZstdCompressor(level=level).compress(packed)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(compressed)
    tmp.replace(path)
    return len(packed), len(compressed)


def load_zst_msgpack(path: Path) -> object:
    """Decompress + msgpack-decode the file at `path` (symmetric to write_msgpack_zst)."""
    compressed = path.read_bytes()
    raw = zstd.ZstdDecompressor().decompress(compressed)
    return msgpack.unpackb(raw, raw=False)
