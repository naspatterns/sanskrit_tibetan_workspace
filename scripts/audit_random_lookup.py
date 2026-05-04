"""Random sampling audit — statistical coverage measurement (Option C, Phase 3.7).

Complements the curated Sentinel 50/200 by sampling random keys from each
index and verifying lookups succeed. Catches systemic regressions that
curated tests might miss because their query set is too narrow.

Methodology:
  - tier0:  100 random keys → expect Map.get to return non-empty Tier0Entry
  - tier0-extended: 100 random keys → same
  - tier0-bo: 100 random keys → same
  - reverse_en: 100 random tokens → expect non-empty entry_id list
  - reverse_ko: 100 random tokens → expect non-empty entry_id list
  - headwords: 100 random rows → verify 3-column structure & rank ∈ {1..N, 999_999}
  - equivalents: 100 random keys → verify EquivRow shape

Reports lookup hit rate per index. Anything below 100% indicates a bug
(Map.get returning undefined for a key the index claims exists).

Output:
  data/reports/audit-2026-04-30/audit-D-random-lookup.md
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

import msgpack
import zstandard as zstd

ROOT = Path(__file__).resolve().parent.parent
INDICES = ROOT / "public" / "indices"
OUT = ROOT / "data" / "reports" / "audit-2026-04-30" / "audit-D-random-lookup.md"

SAMPLE_SIZE = 100


def load_msgpack_zst(path: Path):
    raw = path.read_bytes()
    return msgpack.unpackb(zstd.ZstdDecompressor().decompress(raw),
                           raw=False, strict_map_key=False)


def load_headwords(path: Path) -> list[tuple[str, str, int]]:
    raw = path.read_bytes()
    text = zstd.ZstdDecompressor().decompress(raw).decode("utf-8")
    out = []
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            try:
                rank = int(parts[2])
            except ValueError:
                rank = -1
            out.append((parts[0], parts[1], rank))
    return out


def audit_dict_index(name: str, idx: dict, validator) -> tuple[int, int, list[str]]:
    """Random-sample SAMPLE_SIZE keys, verify each lookup → validator True.

    Returns (hits, total, sample_failures).
    """
    if not idx:
        return 0, 0, [f"{name}: empty index"]
    keys = list(idx.keys())
    sample = random.sample(keys, min(SAMPLE_SIZE, len(keys)))
    hits = 0
    failures = []
    for key in sample:
        v = idx.get(key)
        if validator(v):
            hits += 1
        elif len(failures) < 3:
            failures.append(f"  {key!r} → {repr(v)[:80]}")
    return hits, len(sample), failures


def audit_headwords(rows: list[tuple[str, str, int]]) -> tuple[int, int, list[str]]:
    """Sample rows; verify rank is in {1..K} or 999_999 (Phase 3.7 sentinel)."""
    if not rows:
        return 0, 0, ["empty headwords list"]
    sample = random.sample(rows, min(SAMPLE_SIZE, len(rows)))
    hits = 0
    failures = []
    for norm, iast, rank in sample:
        # rank invariants: 1..20000 (canonical+ext) or 999_999 (long-tail)
        valid = norm and iast and (1 <= rank <= 20_000 or rank == 999_999)
        if valid:
            hits += 1
        elif len(failures) < 3:
            failures.append(f"  norm={norm!r} iast={iast!r} rank={rank}")
    return hits, len(sample), failures


def main() -> int:
    random.seed(42)  # deterministic reports for diff-friendly tracking

    print("Loading indices…", file=sys.stderr)
    tier0 = load_msgpack_zst(INDICES / "tier0.msgpack.zst")
    ext_path = INDICES / "tier0-extended.msgpack.zst"
    tier0_ext = load_msgpack_zst(ext_path) if ext_path.exists() else {}
    tier0_bo = load_msgpack_zst(INDICES / "tier0-bo.msgpack.zst")
    rev_en = load_msgpack_zst(INDICES / "reverse_en.msgpack.zst")
    rev_ko = load_msgpack_zst(INDICES / "reverse_ko.msgpack.zst")
    equivalents = load_msgpack_zst(INDICES / "equivalents.msgpack.zst")
    headwords = load_headwords(INDICES / "headwords.txt.zst")

    # Validators
    def is_tier0_entry(v) -> bool:
        return isinstance(v, dict) and "iast" in v and "entries" in v \
               and isinstance(v["entries"], list) and len(v["entries"]) > 0

    def is_reverse_entry(v) -> bool:
        return isinstance(v, list) and len(v) > 0 and \
               all(isinstance(x, str) for x in v[:3])

    def is_equiv_entry(v) -> bool:
        return isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict)

    cases = [
        ("tier0", tier0, is_tier0_entry),
        ("tier0-extended", tier0_ext, is_tier0_entry),
        ("tier0-bo", tier0_bo, is_tier0_entry),
        ("reverse_en", rev_en, is_reverse_entry),
        ("reverse_ko", rev_ko, is_reverse_entry),
        ("equivalents", equivalents, is_equiv_entry),
    ]

    lines = [
        "# audit-D-random-lookup — 통계적 인덱스 샘플링 검증",
        "",
        f"각 인덱스에서 무작위 {SAMPLE_SIZE}개 key를 추출해 lookup 정상 여부 측정.",
        "100% hit가 정상. <100%는 버그 (Map.get이 빈/잘못된 결과 반환).",
        "",
        f"- Random seed: 42 (deterministic across runs)",
        "",
        "| Index | Hits | Total | Hit Rate | Index Size |",
        "|---|---:|---:|---:|---:|",
    ]
    all_pass = True
    for name, idx, validator in cases:
        hits, total, failures = audit_dict_index(name, idx, validator)
        rate = hits / total * 100 if total else 0
        size = len(idx) if hasattr(idx, "__len__") else "?"
        lines.append(f"| `{name}` | {hits} | {total} | {rate:.0f}% | "
                     f"{size:,} |" if isinstance(size, int) else
                     f"| `{name}` | {hits} | {total} | {rate:.0f}% | {size} |")
        if hits < total:
            all_pass = False
            print(f"  {name}: {hits}/{total} (FAIL)", file=sys.stderr)
            for fail in failures:
                print(f"    {fail}", file=sys.stderr)
        else:
            print(f"  {name}: {hits}/{total} ✓", file=sys.stderr)

    # Headwords audit
    hits, total, failures = audit_headwords(headwords)
    rate = hits / total * 100 if total else 0
    lines.append(f"| `headwords` | {hits} | {total} | {rate:.0f}% | "
                 f"{len(headwords):,} |")
    print(f"  headwords: {hits}/{total} {'✓' if hits == total else '(FAIL)'}",
          file=sys.stderr)
    for fail in failures:
        print(f"    {fail}", file=sys.stderr)
    if hits < total:
        all_pass = False

    lines.append("")
    if all_pass:
        lines.append("**결과**: 모든 인덱스 100% lookup 정상 ✅")
    else:
        lines.append("**결과**: 일부 인덱스에 lookup 실패 — 자세히는 stderr 확인 ❌")
    lines.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n✓ Wrote {OUT.relative_to(ROOT)}", file=sys.stderr)
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
