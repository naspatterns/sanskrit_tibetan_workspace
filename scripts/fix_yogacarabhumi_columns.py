"""Phase 4-B (2026-05-12) — column-type re-balancing for the
equiv-yogacarabhumi-idx JSONL.

The v1 bilex.sqlite extraction produced rows where 67% have CJK or
Tibetan script in `body.equivalents.skt_iast`. Inspection of the bad
rows reveals two distinct corruption patterns:

  (1) Columns rotated: skt_iast and zh swapped, e.g.
        skt_iast = "ト羯婆家", zh = "pukkasa-kula"
      → recoverable by detecting Latin in zh and CJK in skt.

  (2) Same headword in multiple script columns, e.g.
        skt_iast = "ཀ་བ།", tib_wylie = "ka ba", zh = "ཀ་བ།"
      → strip the Tibetan-script duplicates from skt_iast / zh; the
        legitimate Wylie tib_wylie is already in the right place.

This script rewrites the JSONL in place after backing up the original
to `<path>.bak`. Idempotent — applying twice produces the same output.

The corresponding build pipeline change is in `build_equivalents_index.py`
which still tolerates these patterns generically (defence in depth).

Usage:
    uv run python -m scripts.fix_yogacarabhumi_columns
    uv run python -m scripts.fix_yogacarabhumi_columns --dry-run
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
# Latin run of 3+ letters with optional IAST diacritics. Negation guard
# against pure CJK with embedded ASCII punct (rare but possible).
LATIN_IAST = re.compile(r'[a-zA-ZāīūṛṝḷḹṃḥśṣṭḍṇñṅĀĪŪṚṜḶḸṂḤŚṢṬḌṆÑṄ]{3}')


def looks_like_iast(s: str) -> bool:
    """True when `s` is plausibly IAST/Latin Sanskrit (not CJK, not Tibetan)."""
    if not s:
        return False
    if CJK.search(s) or TIBETAN.search(s):
        return False
    return bool(LATIN_IAST.search(s))


def rebalance_equivalents(eq: dict, stats: Counter) -> tuple[dict, bool]:
    """Return a corrected `eq` dict and whether it changed.

    Order of operations matters — we discard junk in skt_iast / zh first
    so that the swap heuristic doesn't move garbage around.
    """
    skt = (eq.get('skt_iast') or '').strip()
    tib = (eq.get('tib_wylie') or '').strip()
    zh = (eq.get('zh') or '').strip()
    changed = False

    # 1) Tibetan script in skt_iast / zh → drop. We already have tib_wylie
    #    set in nearly every such row (corruption pattern #2).
    if skt and TIBETAN.search(skt):
        skt = ''
        stats['drop_tib_from_skt'] += 1
        changed = True
    if zh and TIBETAN.search(zh):
        zh = ''
        stats['drop_tib_from_zh'] += 1
        changed = True

    # 2) skt has CJK and zh has Latin IAST → swap (corruption pattern #1).
    if CJK.search(skt) and looks_like_iast(zh):
        skt, zh = zh, skt
        stats['swap_skt_zh'] += 1
        changed = True
    elif CJK.search(skt) and not zh:
        # Only one CJK token, no Latin counterpart. Move the CJK to zh.
        zh = skt
        skt = ''
        stats['move_cjk_skt_to_zh'] += 1
        changed = True
    elif CJK.search(skt) and zh and not looks_like_iast(zh):
        # Both fields garbled. Keep the CJK in zh, drop skt_iast (it's
        # not Sanskrit anyway).
        zh = zh + (' / ' + skt if zh != skt else '')
        skt = ''
        stats['merge_dual_cjk'] += 1
        changed = True

    out = dict(eq)
    if skt:
        out['skt_iast'] = skt
    else:
        out.pop('skt_iast', None)
    if tib:
        out['tib_wylie'] = tib
    else:
        out.pop('tib_wylie', None)
    if zh:
        out['zh'] = zh
    else:
        out.pop('zh', None)
    # Preserve any other keys (category, note, etc.)
    return out, changed


def process_file(path: Path, dry_run: bool = False) -> tuple[Counter, int, int]:
    stats: Counter = Counter()
    rows = 0
    changed_rows = 0
    out_lines: list[str] = []
    with path.open(encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                out_lines.append(line)
                continue
            entry = json.loads(line)
            rows += 1
            body = entry.get('body') or {}
            eq = body.get('equivalents')
            if isinstance(eq, dict):
                new_eq, changed = rebalance_equivalents(eq, stats)
                if changed:
                    changed_rows += 1
                    body['equivalents'] = new_eq
                    # Also rewrite body.plain (a synthesised summary) so
                    # the surface text matches the corrected equivalents.
                    parts = []
                    if new_eq.get('skt_iast'):
                        parts.append(f"Skt: {new_eq['skt_iast']}")
                    if new_eq.get('tib_wylie'):
                        parts.append(f"Tib: {new_eq['tib_wylie']}")
                    if new_eq.get('zh'):
                        parts.append(f"Zh: {new_eq['zh']}")
                    body['plain'] = ' · '.join(parts)
                    entry['body'] = body
            out_lines.append(json.dumps(entry, ensure_ascii=False) + '\n')

    if not dry_run:
        backup = path.with_suffix(path.suffix + '.bak')
        if not backup.exists():
            shutil.copy2(path, backup)
            print(f'  backup → {backup.name}', file=sys.stderr)
        path.write_text(''.join(out_lines), encoding='utf-8')
    return stats, rows, changed_rows


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--jsonl', type=Path,
                   default=Path('data/jsonl/equiv-yogacarabhumi-idx.jsonl'))
    p.add_argument('--dry-run', action='store_true',
                   help='Report stats only, do not modify the file.')
    args = p.parse_args()

    if not args.jsonl.exists():
        print(f'ERROR: {args.jsonl} not found', file=sys.stderr)
        return 1

    print(f'Processing {args.jsonl}…', file=sys.stderr)
    stats, total, changed = process_file(args.jsonl, dry_run=args.dry_run)

    print(f'\nTotal rows: {total:,}', file=sys.stderr)
    print(f'Rows changed: {changed:,} ({100*changed/max(1,total):.1f}%)', file=sys.stderr)
    print('\nOperations:', file=sys.stderr)
    for op, n in sorted(stats.items(), key=lambda x: -x[1]):
        print(f'  {op:<24} {n:>8,}', file=sys.stderr)

    if args.dry_run:
        print('\n(dry run — no files modified)', file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
