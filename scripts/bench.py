"""Benchmark Phase 2 indices.

Measures:
  - Tier 0 decompress + msgpack load time
  - 1000 random Tier 0 lookups (hit ratio, median/p95 latency)
  - 1000 random reverse_en lookups
  - Reverse index sizes
  - Total on-disk footprint

Output: data/reports/phase2-benchmark.md
"""
from __future__ import annotations

import argparse
import random
import statistics
import sys
import time
from pathlib import Path

from scripts.lib.io import load_zst_msgpack


def timed_load(path: Path) -> tuple[object, float]:
    """Return (data, total_load_ms) — decompress + msgpack unpack together."""
    t0 = time.perf_counter()
    data = load_zst_msgpack(path)
    return data, (time.perf_counter() - t0) * 1000


def bench_lookups(data: dict, keys: list[str], n: int = 1000) -> dict:
    """Random lookup benchmark. Returns stats dict."""
    rng = random.Random(42)
    sample_hits = [rng.choice(keys) for _ in range(n)]
    sample_misses = [f"__missing_key_{i}__" for i in range(n)]

    hit_times: list[float] = []
    for k in sample_hits:
        t0 = time.perf_counter_ns()
        _ = data.get(k)
        hit_times.append((time.perf_counter_ns() - t0) / 1000)  # microseconds

    miss_times: list[float] = []
    for k in sample_misses:
        t0 = time.perf_counter_ns()
        _ = data.get(k)
        miss_times.append((time.perf_counter_ns() - t0) / 1000)

    return {
        "hit_median_us": statistics.median(hit_times),
        "hit_p95_us": statistics.quantiles(hit_times, n=20)[18],
        "miss_median_us": statistics.median(miss_times),
    }


def format_size(bytes_: int) -> str:
    if bytes_ < 1024:
        return f"{bytes_} B"
    if bytes_ < 1024 * 1024:
        return f"{bytes_/1024:.1f} KB"
    return f"{bytes_/1024/1024:.2f} MB"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tier0", type=Path, default=Path("public/indices/tier0.msgpack.zst"))
    parser.add_argument("--reverse-en", type=Path,
                        default=Path("public/indices/reverse_en.msgpack.zst"))
    parser.add_argument("--reverse-ko", type=Path,
                        default=Path("public/indices/reverse_ko.msgpack.zst"))
    parser.add_argument("--headwords", type=Path,
                        default=Path("public/indices/headwords.txt.zst"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/reports/phase2-benchmark.md"))
    args = parser.parse_args()

    report: list[str] = ["# Phase 2 Index Benchmark", ""]

    # Sizes
    report.append("## Artifact sizes")
    report.append("")
    report.append("| File | Size |")
    report.append("|---|---:|")
    for path in [args.tier0, args.reverse_en, args.reverse_ko, args.headwords]:
        if path.exists():
            report.append(f"| `{path}` | {format_size(path.stat().st_size)} |")
    report.append("")

    # Tier 0
    print("Loading Tier 0…", file=sys.stderr)
    tier0, tier0_ms = timed_load(args.tier0)
    total_entries = sum(len(v["entries"]) for v in tier0.values())
    report.append("## Tier 0 (top-10K in-memory)")
    report.append("")
    report.append(f"- Headwords: **{len(tier0):,}**")
    report.append(f"- Total entries: **{total_entries:,}** "
                  f"(avg {total_entries/max(1,len(tier0)):.1f}/hw)")
    report.append(f"- **Cold load (decompress + msgpack): {tier0_ms:.1f} ms**")
    report.append("")

    keys = list(tier0.keys())
    stats = bench_lookups(tier0, keys)
    report.append(f"- Hit lookup median: **{stats['hit_median_us']:.1f} µs**  "
                  f"(p95 {stats['hit_p95_us']:.1f} µs)")
    report.append(f"- Miss lookup median: **{stats['miss_median_us']:.1f} µs**")
    report.append("")

    print("Loading reverse_en…", file=sys.stderr)
    rev_en, rev_en_ms = timed_load(args.reverse_en)
    report.append("## Reverse index (English → Sanskrit/Tibetan)")
    report.append("")
    report.append(f"- Tokens: **{len(rev_en):,}**")
    report.append(f"- Cold load: **{rev_en_ms:.1f} ms**")

    rev_en_keys = list(rev_en.keys())
    stats_en = bench_lookups(rev_en, rev_en_keys)
    report.append(f"- Hit lookup median: **{stats_en['hit_median_us']:.1f} µs**  "
                  f"(p95 {stats_en['hit_p95_us']:.1f} µs)")

    if "fire" in rev_en:
        report.append(f"- Example: `fire` → {len(rev_en['fire'])} entries, "
                      f"first: `{rev_en['fire'][0]}`")
    if "duty" in rev_en:
        report.append(f"- Example: `duty` → {len(rev_en['duty'])} entries")
    report.append("")

    print("Loading reverse_ko…", file=sys.stderr)
    rev_ko, rev_ko_ms = timed_load(args.reverse_ko)
    report.append("## Reverse index (Korean → original)")
    report.append("")
    report.append(f"- Tokens: **{len(rev_ko):,}** (limited — expands after Phase 2 En→Ko batch)")
    report.append(f"- Cold load: **{rev_ko_ms:.1f} ms**")
    if "법" in rev_ko:
        report.append(f"- Example: `법` → {len(rev_ko['법'])} entries")
    report.append("")

    # Grand total
    total_size = sum(
        p.stat().st_size for p in [args.tier0, args.reverse_en, args.reverse_ko, args.headwords]
        if p.exists()
    )
    report.append("## Grand total")
    report.append("")
    report.append(f"- **All Phase 2 indices: {format_size(total_size)}**")
    report.append("")
    report.append("### Comparison with ROADMAP targets")
    report.append("")
    report.append("| Metric | Target | Actual |")
    report.append("|---|---|---|")
    report.append(f"| Tier 0 size | ~30 MB | {format_size(args.tier0.stat().st_size)} |")
    report.append(f"| Tier 0 cold load | <2s on 4G | {tier0_ms:.0f} ms local |")
    report.append(f"| Search response (cache hit) | <50 ms | {stats['hit_median_us']:.1f} µs |")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(report), encoding="utf-8")
    print(f"\n✓ Report written to {args.out}")

    print("\n━━━ Summary ━━━")
    print(f"Tier 0: {format_size(args.tier0.stat().st_size)}, cold load {tier0_ms:.0f}ms")
    print(f"  Hit lookup: {stats['hit_median_us']:.1f}µs median, {stats['hit_p95_us']:.1f}µs p95")
    print(f"Reverse EN: {format_size(args.reverse_en.stat().st_size)}, {len(rev_en):,} tokens")
    print(f"Reverse KO: {format_size(args.reverse_ko.stat().st_size)}, {len(rev_ko):,} tokens")
    print(f"Total: {format_size(total_size)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
