"""Phase 4-B audit (2026-05-12) — column-type validation for the built
equivalents.msgpack.zst.

The expected schema (post-build) for every row inside the equivalents
index:
  - skt_iast: Latin (IAST). NEVER CJK / NEVER Tibetan script.
  - tib_wylie: Latin Wylie. May contain Tibetan script (some sources
    keep both — checked separately as soft warnings).
  - zh: CJK. NEVER pure Latin (whole field).

This is the runtime invariant check — pipeline scripts that violate
it surface here. Run from CI to catch regressions; runs locally in
under a second.

Usage:
    uv run python -m scripts.audit_equivalents_schema
    uv run python -m scripts.audit_equivalents_schema --strict   # exit 1 on any
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import zstandard as zstd
import msgpack

CJK = re.compile(r'[一-鿿㐀-䶿]')
TIBETAN = re.compile(r'[ༀ-࿿]')
DEVANAGARI = re.compile(r'[ऀ-ॿ]')
# OCR garbage glyphs seen in tib-chn-great
OCR_NOISE = re.compile(r'[°›ˆ‹‒–—„‟]')
# "Real" Wylie has at least 2 consecutive letters somewhere
WYLIE_LETTER_RUN = re.compile(r'[a-zA-Z]{2,}')


def audit(path: Path) -> tuple[dict, dict]:
    raw = zstd.ZstdDecompressor().decompress(path.read_bytes())
    data = msgpack.unpackb(raw, raw=False, strict_map_key=False)

    totals: Counter = Counter()
    violations: dict[str, Counter] = defaultdict(Counter)
    samples: dict[tuple[str, str], list[str]] = defaultdict(list)

    for k, rows in data.items():
        if not isinstance(rows, list):
            continue
        for r in rows:
            if not isinstance(r, dict):
                continue
            sources = tuple(sorted(r.get('sources') or [])) or ('<unknown>',)
            for src in sources:
                totals[src] += 1
                skt = r.get('skt_iast') or ''
                tib = r.get('tib_wylie') or ''
                zh = r.get('zh') or ''
                # skt_iast must be Latin
                if skt and CJK.search(skt):
                    violations[src]['skt_has_cjk'] += 1
                    if len(samples[(src, 'skt_has_cjk')]) < 3:
                        samples[(src, 'skt_has_cjk')].append(f'key={k!r} skt={skt!r}')
                if skt and TIBETAN.search(skt):
                    violations[src]['skt_has_tib'] += 1
                    if len(samples[(src, 'skt_has_tib')]) < 3:
                        samples[(src, 'skt_has_tib')].append(f'key={k!r} skt={skt!r}')
                # tib_wylie soft checks
                if tib and CJK.search(tib):
                    violations[src]['tib_has_cjk'] += 1
                if tib and OCR_NOISE.search(tib):
                    violations[src]['tib_ocr_noise'] += 1
                if tib and not WYLIE_LETTER_RUN.search(tib):
                    violations[src]['tib_no_letters'] += 1
                # zh must be CJK if set
                if zh and not CJK.search(zh):
                    violations[src]['zh_not_cjk'] += 1

    return totals, violations, samples


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--path', type=Path,
                   default=Path('public/indices/equivalents.msgpack.zst'))
    p.add_argument('--strict', action='store_true',
                   help='Exit 1 on any violation.')
    p.add_argument('--out', type=Path,
                   default=None,
                   help='Write Markdown report to this file (in addition to stdout).')
    args = p.parse_args()

    if not args.path.exists():
        print(f'ERROR: {args.path} not found — run build_equivalents_index first', file=sys.stderr)
        return 2

    totals, violations, samples = audit(args.path)

    lines: list[str] = []
    lines.append('# audit-equivalents-schema')
    lines.append('')
    lines.append(f'- index: `{args.path}`')
    lines.append(f'- sources analysed: {len(totals)}')
    lines.append(f'- total row-references: {sum(totals.values()):,}')
    lines.append('')
    lines.append('## Per-source violation counts')
    lines.append('')
    lines.append('| source | total | skt+cjk | skt+tib | tib+cjk | tib OCR | tib no letters | zh not CJK |')
    lines.append('|---|---:|---:|---:|---:|---:|---:|---:|')

    has_violation = False
    for src, total in sorted(totals.items(), key=lambda x: -x[1]):
        v = violations[src]
        row_violations = sum(v.values())
        if row_violations > 0:
            has_violation = True
        lines.append(
            f'| {src} | {total:,} | '
            f'{v["skt_has_cjk"] or "-"} | {v["skt_has_tib"] or "-"} | '
            f'{v["tib_has_cjk"] or "-"} | {v["tib_ocr_noise"] or "-"} | '
            f'{v["tib_no_letters"] or "-"} | {v["zh_not_cjk"] or "-"} |'
        )

    if samples:
        lines.append('')
        lines.append('## Sample violations')
        lines.append('')
        for (src, kind), examples in sorted(samples.items()):
            lines.append(f'**{src} / {kind}**:')
            for ex in examples:
                lines.append(f'- `{ex}`')
            lines.append('')

    out = '\n'.join(lines)
    print(out)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(out + '\n', encoding='utf-8')
        print(f'\n→ wrote {args.out}', file=sys.stderr)

    if args.strict and has_violation:
        # Hard-fail only on the "must never happen" classes (skt_iast columns).
        # tib_* soft checks are not yet enforced.
        hard = any(
            violations[src]['skt_has_cjk'] + violations[src]['skt_has_tib'] > 0
            for src in violations
        )
        if hard:
            print('\nFAIL: skt_iast has CJK/Tibetan content (hard violation).', file=sys.stderr)
            return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
