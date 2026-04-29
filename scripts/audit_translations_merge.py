"""Audit-A7: translations.jsonl ↔ tier0.msgpack.zst merge integrity.

Confirms that build_tier0.py correctly joined Korean translations into the
tier0 index:

  1. Load 9,995 translations.jsonl (entry_id → ko).
  2. Decompress + decode tier0.msgpack.zst (and tier0-bo).
  3. For each tier0 entry, check whether `entry["ko"]` is non-empty.
  4. Cross-check translations.jsonl entry_ids against tier0 ids:
     - entries in translations.jsonl that *aren't* in tier0 → translation orphan
     - tier0 entries that *should* have translation but don't → merge gap
  5. Sample mismatches.

Output: data/reports/audit-2026-04-30/audit-A-translations.md
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import msgpack
import zstandard as zstd

ROOT = Path(__file__).resolve().parent.parent
TRANSLATIONS = ROOT / "data" / "translations.jsonl"
TIER0 = ROOT / "public" / "indices" / "tier0.msgpack.zst"
TIER0_BO = ROOT / "public" / "indices" / "tier0-bo.msgpack.zst"
OUT = ROOT / "data" / "reports" / "audit-2026-04-30" / "audit-A-translations.md"


def load_translations() -> dict[str, str]:
    out = {}
    with TRANSLATIONS.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            out[obj["entry_id"]] = obj.get("ko") or ""
    return out


def load_tier0(path: Path) -> dict:
    raw = path.read_bytes()
    decompressed = zstd.ZstdDecompressor().decompress(raw)
    return msgpack.unpackb(decompressed, raw=False, strict_map_key=False)


def main() -> int:
    translations = load_translations()
    print(f"Loaded {len(translations):,} translations from translations.jsonl")

    tier0 = load_tier0(TIER0)
    tier0_bo = load_tier0(TIER0_BO)
    print(f"tier0 keys: {len(tier0):,} · tier0-bo keys: {len(tier0_bo):,}")

    # Walk all entries
    n_entries = 0
    n_with_ko = 0
    n_ko_from_translations = 0
    n_ko_from_v1 = 0  # body.ko already in v1 (DE/FR/LA dicts)
    by_dict_ko = Counter()
    by_dict_no_ko = Counter()
    tier0_ids: set[str] = set()
    sample_no_ko = []

    def walk(idx, label):
        nonlocal n_entries, n_with_ko, n_ko_from_translations, n_ko_from_v1
        for hw, slot in idx.items():
            for e in slot.get("entries", []):
                n_entries += 1
                eid = e.get("id")
                if eid:
                    tier0_ids.add(eid)
                ko = e.get("ko") or ""
                dict_slug = e.get("dict", "?")
                if ko:
                    n_with_ko += 1
                    by_dict_ko[dict_slug] += 1
                    if eid and eid in translations:
                        # Could be translations.jsonl OR pre-existing v1 ko;
                        # we can't distinguish without re-reading JSONL —
                        # but if id matches translations.jsonl, count once.
                        n_ko_from_translations += 1
                    else:
                        n_ko_from_v1 += 1
                else:
                    by_dict_no_ko[dict_slug] += 1
                    if eid and eid in translations and len(sample_no_ko) < 12:
                        sample_no_ko.append(
                            f"{label}: {hw} → {eid} (translations has ko but tier0 entry doesn't!)"
                        )

    walk(tier0, "tier0")
    walk(tier0_bo, "tier0-bo")
    print(f"Total tier0/tier0-bo entries: {n_entries:,}")
    print(f"  with ko: {n_with_ko:,} ({n_with_ko/n_entries*100:.1f}%)")
    print(f"  via translations.jsonl id match: {n_ko_from_translations:,}")
    print(f"  pre-existing (v1 body.ko): {n_ko_from_v1:,}")

    # Translation orphans (entries in translations.jsonl but not in tier0)
    orphans = [tid for tid in translations if tid not in tier0_ids]
    print(f"Translation orphans (not in tier0/tier0-bo): {len(orphans):,}")

    lines = []
    lines.append("# audit-A-translations — translations.jsonl ↔ tier0 merge")
    lines.append("")
    lines.append(f"- translations.jsonl entries: **{len(translations):,}**")
    lines.append(f"- tier0 + tier0-bo total entries: **{n_entries:,}**")
    lines.append(f"- entries with `ko` filled: **{n_with_ko:,}** ({n_with_ko/n_entries*100:.1f}%)")
    lines.append(f"  - id-matched to translations.jsonl: **{n_ko_from_translations:,}**")
    lines.append(f"  - other (v1 body.ko: DE/FR/LA): **{n_ko_from_v1:,}**")
    lines.append(f"- translation orphans (in jsonl, not in tier0): **{len(orphans):,}**")
    lines.append("")
    lines.append("## Top 20 dicts with `ko`-filled tier0 entries")
    lines.append("")
    lines.append("| Dict | with ko | without ko | coverage |")
    lines.append("|---|---:|---:|---:|")
    all_dicts = set(by_dict_ko.keys()) | set(by_dict_no_ko.keys())
    rows = []
    for d in all_dicts:
        a, b = by_dict_ko[d], by_dict_no_ko[d]
        cov = a / (a + b) if (a + b) else 0
        rows.append((d, a, b, cov))
    rows.sort(key=lambda r: -r[1])
    for d, a, b, cov in rows[:20]:
        lines.append(f"| `{d}` | {a:,} | {b:,} | {cov*100:.1f}% |")
    lines.append("")

    if orphans:
        lines.append("## Translation orphan samples")
        lines.append("")
        for o in orphans[:20]:
            lines.append(f"- {o}")
        if len(orphans) > 20:
            lines.append(f"- … and {len(orphans) - 20} more")
        lines.append("")

    if sample_no_ko:
        lines.append("## Tier0 entries that should have ko but don't (merge gap)")
        lines.append("")
        for s in sample_no_ko:
            lines.append(f"- {s}")
        lines.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
