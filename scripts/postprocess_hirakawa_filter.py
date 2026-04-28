#!/usr/bin/env python3
"""Filter Hirakawa OCR noise rows from equiv-hirakawa.jsonl.

Drops rows where:
  - source_meta.ocr_conf < MIN_OCR_CONF (default 60), OR
  - len(headword) > MAX_HEADWORD_LEN (default 8)

These thresholds target preface / index page OCR noise: entries with low
page-level confidence or overly long CJK headwords are typically misreads
that pollute the equivalents index without adding usable mappings.

Idempotent: when no surviving row violates the thresholds, the script
exits without rewriting (so re-running on already-filtered data is a
no-op apart from refreshing the report).

Outputs:
  - rewrites  data/jsonl/equiv-hirakawa.jsonl                 (in-place, atomic)
  - updates   data/sources/equiv-hirakawa/meta.json           (row_count + filter audit)
  - writes    data/reports/hirakawa-filter.md                 (drop statistics)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLUG = "equiv-hirakawa"
JSONL = ROOT / "data" / "jsonl" / f"{SLUG}.jsonl"
META = ROOT / "data" / "sources" / SLUG / "meta.json"
REPORT = ROOT / "data" / "reports" / "hirakawa-filter.md"

DEFAULT_MIN_OCR_CONF = 60.0
DEFAULT_MAX_HEADWORD_LEN = 8


def conf_bucket(c: float) -> str:
    """Bucket OCR conf into 10-point bins."""
    if c < 50:
        return "<50"
    lo = int(c // 10) * 10
    return f"{lo}-{lo + 9}"


def hw_len_bucket(n: int) -> str:
    if n <= 8:
        return str(n)
    if n <= 12:
        return "9-12"
    return "13+"


def drop_reason(row: dict, min_conf: float, max_len: int) -> str | None:
    """Return None if kept, else a short reason tag."""
    conf = row.get("source_meta", {}).get("ocr_conf", 100.0)
    hw_len = len(row.get("headword", ""))
    low = conf < min_conf
    long_hw = hw_len > max_len
    if low and long_hw:
        return "low_conf+long_hw"
    if low:
        return "low_conf"
    if long_hw:
        return "long_hw"
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-ocr-conf", type=float, default=DEFAULT_MIN_OCR_CONF)
    ap.add_argument("--max-headword-len", type=int, default=DEFAULT_MAX_HEADWORD_LEN)
    ap.add_argument("--dry-run", action="store_true",
                    help="Compute stats + write report, but skip JSONL/meta rewrite.")
    args = ap.parse_args()

    if not JSONL.exists():
        print(f"ERROR: {JSONL} not found", file=sys.stderr)
        return 1
    if not META.exists():
        print(f"ERROR: {META} not found", file=sys.stderr)
        return 1

    kept_lines: list[str] = []
    dropped_samples: list[dict] = []
    drop_reasons: Counter = Counter()
    conf_hist_in: Counter = Counter()
    conf_hist_kept: Counter = Counter()
    hw_len_hist_in: Counter = Counter()
    hw_len_hist_kept: Counter = Counter()
    drops_by_page: Counter = Counter()
    n_total = 0
    n_kept = 0
    n_dropped = 0

    with JSONL.open(encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line.strip():
                continue
            n_total += 1
            row = json.loads(line)

            conf = float(row.get("source_meta", {}).get("ocr_conf", 100.0))
            hw_len = len(row.get("headword", ""))
            conf_hist_in[conf_bucket(conf)] += 1
            hw_len_hist_in[hw_len_bucket(hw_len)] += 1

            reason = drop_reason(row, args.min_ocr_conf, args.max_headword_len)
            if reason is None:
                kept_lines.append(line)
                conf_hist_kept[conf_bucket(conf)] += 1
                hw_len_hist_kept[hw_len_bucket(hw_len)] += 1
                n_kept += 1
            else:
                drop_reasons[reason] += 1
                drops_by_page[row.get("source_meta", {}).get("page", "?")] += 1
                if len(dropped_samples) < 10:
                    dropped_samples.append({
                        "id": row.get("id"),
                        "headword": row.get("headword", "")[:30],
                        "headword_len": hw_len,
                        "ocr_conf": conf,
                        "page": row.get("source_meta", {}).get("page"),
                        "reason": reason,
                    })
                n_dropped += 1

    pct = (n_dropped / n_total * 100) if n_total else 0.0
    print(f"input rows : {n_total:,}")
    print(f"kept       : {n_kept:,}")
    print(f"dropped    : {n_dropped:,} ({pct:.2f}%)")
    for r, n in drop_reasons.most_common():
        print(f"  {r}: {n}")

    meta = json.loads(META.read_text(encoding="utf-8"))
    prev_count = meta.get("row_count")

    if n_dropped == 0:
        print("No rows match drop criteria — JSONL already filtered (no-op).")
    elif args.dry_run:
        print("--dry-run: skipping JSONL/meta rewrite.")
    else:
        tmp = JSONL.with_suffix(".jsonl.tmp")
        with tmp.open("w", encoding="utf-8") as f:
            f.write("\n".join(kept_lines))
            if kept_lines:
                f.write("\n")
        os.replace(tmp, JSONL)
        print(f"rewrote    : {JSONL} ({n_kept:,} rows)")

    # Only refresh meta on the run that actually drops rows. No-op re-runs
    # preserve the original filter audit (timestamp, input/dropped counts).
    if n_dropped > 0 and not args.dry_run:
        meta["row_count"] = n_kept
        meta["filter"] = {
            "applied_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "min_ocr_conf": args.min_ocr_conf,
            "max_headword_len": args.max_headword_len,
            "input_rows": n_total,
            "kept_rows": n_kept,
            "dropped_rows": n_dropped,
        }
        META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"updated    : {META} (row_count {prev_count} → {n_kept})")

    # Regenerate the report only when this run actually filtered something.
    # On a no-op re-run the existing report (from the run that did the drops)
    # remains the authoritative record.
    if n_dropped > 0:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        write_report(
            REPORT,
            n_total=n_total,
            n_kept=n_kept,
            n_dropped=n_dropped,
            drop_reasons=drop_reasons,
            conf_hist_in=conf_hist_in,
            conf_hist_kept=conf_hist_kept,
            hw_len_hist_in=hw_len_hist_in,
            hw_len_hist_kept=hw_len_hist_kept,
            drops_by_page=drops_by_page,
            dropped_samples=dropped_samples,
            min_conf=args.min_ocr_conf,
            max_len=args.max_headword_len,
            dry_run=args.dry_run,
        )
        print(f"report     : {REPORT}")
    elif REPORT.exists():
        print(f"report     : {REPORT} (preserved — no new drops)")
    else:
        print(f"report     : not written (no drops, no prior report)")

    return 0


def _hist_table(title: str, h_in: Counter, h_kept: Counter, key_order: list[str]) -> list[str]:
    lines = [f"### {title}", "", "| bucket | input | kept | dropped |", "|---|---:|---:|---:|"]
    for k in key_order:
        i = h_in.get(k, 0)
        kp = h_kept.get(k, 0)
        if i == 0:
            continue
        lines.append(f"| `{k}` | {i:,} | {kp:,} | {i - kp:,} |")
    lines.append("")
    return lines


def write_report(
    path: Path,
    *,
    n_total: int,
    n_kept: int,
    n_dropped: int,
    drop_reasons: Counter,
    conf_hist_in: Counter,
    conf_hist_kept: Counter,
    hw_len_hist_in: Counter,
    hw_len_hist_kept: Counter,
    drops_by_page: Counter,
    dropped_samples: list[dict],
    min_conf: float,
    max_len: int,
    dry_run: bool,
) -> None:
    pct = (n_dropped / n_total * 100) if n_total else 0.0
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines: list[str] = []
    lines.append("# Hirakawa OCR Noise Filter — Report")
    lines.append("")
    lines.append(f"**Generated**: {now}{'  *(dry-run)*' if dry_run else ''}")
    lines.append("")
    lines.append("## Filter")
    lines.append("")
    lines.append(f"- `source_meta.ocr_conf >= {min_conf}`")
    lines.append(f"- `len(headword) <= {max_len}`")
    lines.append("")
    lines.append("Rows failing **either** condition are dropped.")
    lines.append("")
    lines.append("## Result")
    lines.append("")
    lines.append("| metric | rows |")
    lines.append("|---|---:|")
    lines.append(f"| input | {n_total:,} |")
    lines.append(f"| kept | {n_kept:,} |")
    lines.append(f"| dropped | {n_dropped:,} ({pct:.2f}%) |")
    lines.append("")

    lines.append("### Drop reasons")
    lines.append("")
    lines.append("| reason | count |")
    lines.append("|---|---:|")
    for r in ("low_conf", "long_hw", "low_conf+long_hw"):
        lines.append(f"| `{r}` | {drop_reasons.get(r, 0):,} |")
    lines.append("")

    conf_keys = ["<50", "50-59", "60-69", "70-79", "80-89", "90-99"]
    lines.extend(_hist_table("OCR confidence (page-level)", conf_hist_in, conf_hist_kept, conf_keys))
    hw_keys = [str(i) for i in range(1, 9)] + ["9-12", "13+"]
    lines.extend(_hist_table("Headword length (CJK chars)", hw_len_hist_in, hw_len_hist_kept, hw_keys))

    if drops_by_page:
        lines.append("### Top 10 pages by drop count")
        lines.append("")
        lines.append("| page | drops |")
        lines.append("|---:|---:|")
        for page, n in drops_by_page.most_common(10):
            lines.append(f"| {page} | {n} |")
        lines.append("")

    if dropped_samples:
        lines.append("### Sample dropped rows")
        lines.append("")
        lines.append("| id | headword | len | conf | page | reason |")
        lines.append("|---|---|---:|---:|---:|---|")
        for s in dropped_samples:
            hw = s["headword"].replace("|", "\\|")
            lines.append(
                f"| `{s['id']}` | `{hw}` | {s['headword_len']} | "
                f"{s['ocr_conf']:.1f} | {s['page']} | {s['reason']} |"
            )
        lines.append("")

    lines.append("## Notes")
    lines.append("")
    lines.append(
        "- Filter is applied in-place by `scripts/postprocess_hirakawa_filter.py`. "
        "Re-running the script on already-filtered data is a no-op."
    )
    lines.append(
        "- Surviving rows include the page-level OCR confidence in "
        "`source_meta.ocr_conf`, so downstream consumers can apply stricter "
        "filters at query time without re-running this pass."
    )
    lines.append(
        f"- Audit trail: `data/sources/{SLUG}/meta.json` records the filter "
        "thresholds and counts under the `filter` key."
    )
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
