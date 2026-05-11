"""Phase 4-C residual cleanup (2026-05-12) — drop or strip the last 524
entries across hirakawa / nti-reader / bodkye-hamsa where the skt_iast
column contains CJK or Tibetan script.

These are not column-rotation bugs (Phase 4-B handled those for yogacara).
They are individual rows where the upstream dictionary's Sanskrit entry
itself contained Chinese gloss, cross-references, or Tibetan
illustrations. Two policies are applied per row:

  - If skt_iast has CJK + IAST mixed (e.g. "aprameya-近ana"), the field
    is replaced with the non-CJK portion when extractable, else dropped.
  - If skt_iast is pure CJK / Tibetan / a cross-ref like "see 跋難陀"
    or "15. See 兩 221", the field is dropped entirely.

The body.equivalents.zh and tib_wylie sides are preserved so the
entry remains searchable through those channels — we lose the
Sanskrit headword but not the corresponding-term row.

Idempotent. Originals backed up to <path>.bak.

Usage:
    uv run python -m scripts.fix_equivalents_residual
    uv run python -m scripts.fix_equivalents_residual --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

CJK = re.compile(r'[一-鿿㐀-䶿]')
TIBETAN = re.compile(r'[ༀ-࿿]')
HANGUL = re.compile(r'[가-힣]')
SEE_CROSS_REF = re.compile(r'^\s*(?:\d+\.?\s*)?see\s+\S', re.IGNORECASE)
LATIN_IAST = re.compile(r'[a-zA-ZāīūṛṝḷḹṃḥśṣṭḍṇñṅĀĪŪṚṜḶḸṂḤŚṢṬḌṆÑṄ]{3}')

TARGETS = [
    'equiv-hirakawa',
    'equiv-nti-reader',
    'equiv-bodkye-hamsa',
    'equiv-yogacara-index',
]


def strip_cjk_tib(s: str) -> str:
    """Strip CJK chars + Tibetan-script chars, normalise whitespace and
    leftover separators. Returns empty string if nothing useful remains."""
    out = CJK.sub('', s)
    out = TIBETAN.sub('', out)
    # Collapse trailing/leading separator junk
    out = re.sub(r'[\s;,/\-]{2,}', ' ', out).strip(' ;,/-')
    out = re.sub(r'\s+', ' ', out)
    return out


def clean_skt(skt: str, stats: Counter) -> str:
    """Return a cleaned skt_iast value; '' means drop."""
    if not skt:
        return ''
    s = skt.strip()
    # `see 跋難陀` / `15. See 兩 221`-style cross-ref → drop
    if SEE_CROSS_REF.match(s):
        stats['drop_cross_ref'] += 1
        return ''
    # Pure CJK / Tibetan → drop
    only_non_latin = re.fullmatch(r'[一-鿿㐀-䶿ༀ-࿿\s\.\,\;\:\-\(\)]+', s)
    if only_non_latin:
        stats['drop_pure_non_latin'] += 1
        return ''
    if CJK.search(s) or TIBETAN.search(s):
        # Mixed → strip the foreign chars, keep the IAST run if substantial
        stripped = strip_cjk_tib(s)
        if LATIN_IAST.search(stripped):
            stats['strip_kept_iast'] += 1
            return stripped
        stats['drop_mixed_no_iast'] += 1
        return ''
    return s


def clean_headword(hw: str, stats: Counter) -> str | None:
    """Drop Hangul-only or pure-non-latin headwords. Returns None if no
    cleaning was needed, or the cleaned value otherwise."""
    if not hw:
        return None
    if HANGUL.search(hw):
        cleaned = HANGUL.sub('', hw).strip()
        if cleaned:
            stats['hw_strip_hangul'] += 1
            return cleaned
    return None


def process(slug: str, jsonl_dir: Path, dry_run: bool) -> tuple[Counter, int, int]:
    path = jsonl_dir / f'{slug}.jsonl'
    if not path.exists():
        return Counter(), 0, 0
    stats: Counter = Counter()
    out_lines = []
    rows = 0
    changed = 0
    with path.open(encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                out_lines.append(line)
                continue
            entry = json.loads(line)
            rows += 1
            row_changed = False
            body = entry.get('body') or {}
            eq = body.get('equivalents') if isinstance(body.get('equivalents'), dict) else None
            if eq:
                old_skt = eq.get('skt_iast') or ''
                new_skt = clean_skt(old_skt, stats)
                if new_skt != old_skt:
                    if new_skt:
                        eq['skt_iast'] = new_skt
                    else:
                        eq.pop('skt_iast', None)
                    row_changed = True
            # Hangul-tainted headwords in equiv-yogacara-index
            for key in ('headword', 'headword_iast'):
                hw = entry.get(key) or ''
                new_hw = clean_headword(hw, stats)
                if new_hw is not None and new_hw != hw:
                    entry[key] = new_hw
                    row_changed = True
            if row_changed:
                changed += 1
                # Re-synthesise body.plain when equivalents changed
                if eq:
                    parts = []
                    if eq.get('skt_iast'):
                        parts.append(f"Skt: {eq['skt_iast']}")
                    if eq.get('tib_wylie'):
                        parts.append(f"Tib: {eq['tib_wylie']}")
                    if eq.get('zh'):
                        parts.append(f"Zh: {eq['zh']}")
                    if parts:
                        body['plain'] = ' · '.join(parts)
                    entry['body'] = body
            out_lines.append(json.dumps(entry, ensure_ascii=False) + '\n')
    if not dry_run and changed:
        backup = path.with_suffix(path.suffix + '.bak')
        if not backup.exists():
            shutil.copy2(path, backup)
        path.write_text(''.join(out_lines), encoding='utf-8')
    return stats, rows, changed


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--jsonl-dir', type=Path, default=Path('data/jsonl'))
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()

    print(f'Cleaning residual schema issues across {len(TARGETS)} sources…',
          file=sys.stderr)
    total_changed = 0
    grand: Counter = Counter()
    for slug in TARGETS:
        stats, rows, changed = process(slug, args.jsonl_dir, args.dry_run)
        if rows:
            print(f'\n[{slug}] rows={rows:,}, changed={changed}', file=sys.stderr)
            for k, v in sorted(stats.items(), key=lambda x: -x[1]):
                print(f'    {k:<24} {v:>6}', file=sys.stderr)
            grand.update(stats)
            total_changed += changed
    print(f'\nTotal rows changed across all sources: {total_changed}', file=sys.stderr)
    print('Grand totals:', file=sys.stderr)
    for k, v in sorted(grand.items(), key=lambda x: -x[1]):
        print(f'  {k:<24} {v:>6}', file=sys.stderr)
    if args.dry_run:
        print('\n(dry run — no files modified)', file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
