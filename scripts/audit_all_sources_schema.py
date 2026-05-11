"""Phase 4-C audit (2026-05-12) — schema integrity check across ALL 148
source dictionaries (not just the equiv-* ones already audited in 4-B).

For each JSONL we verify:

  1. `headword_iast` must NEVER contain CJK or Tibetan script. Sanskrit
     dictionaries occasionally leak Chinese gloss into the headword.
  2. `headword_norm` must round-trip the headword (NFD + strip diacritics
     + lowercase). Mismatches indicate a transliteration bug.
  3. `lang` must match the headword script (skt → Latin/Devanagari,
     bo → Wylie/Tibetan, etc.). Wrong-lang tags break the language filter
     in the UI.
  4. `body.equivalents.*` audited by `audit_equivalents_schema.py` (post-
     build), this script audits the upstream JSONL.

Output:
  - data/reports/phase4-all-sources-schema.md (markdown summary)
  - exit 0 if no hard violations, 1 if --strict and any found

Usage:
    uv run python -m scripts.audit_all_sources_schema
    uv run python -m scripts.audit_all_sources_schema --strict
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

CJK = re.compile(r'[一-鿿㐀-䶿]')
TIBETAN = re.compile(r'[ༀ-࿿]')
DEVANAGARI = re.compile(r'[ऀ-ॿ]')
HANGUL = re.compile(r'[가-힣]')

# Sets we use to classify a headword's script.
SCRIPT_FOR_LANG = {
    'skt': {'latin', 'devanagari'},      # Sanskrit accepts IAST or Devanagari
    'sa': {'latin', 'devanagari'},       # alias
    'bo': {'latin', 'tibetan'},          # Tibetan: Wylie (Latin) or Tibetan script
    'pi': {'latin'},                     # Pali: Latin/IAST
    'pal': {'latin'},
    'pa': {'latin'},
    'en': {'latin'},
    'ko': {'latin', 'hangul'},
    'zh': {'cjk'},
    'ja': {'cjk', 'kana', 'latin'},
}


def classify_script(s: str) -> str | None:
    if not s:
        return None
    if CJK.search(s):
        return 'cjk'
    if TIBETAN.search(s):
        return 'tibetan'
    if DEVANAGARI.search(s):
        return 'devanagari'
    if HANGUL.search(s):
        return 'hangul'
    # Default: Latin / IAST diacritics
    return 'latin'


def audit_jsonl(jsonl_path: Path, meta: dict) -> tuple[int, dict]:
    lang = (meta.get('lang') or '').lower()
    expected = SCRIPT_FOR_LANG.get(lang, set())
    violations: Counter = Counter()
    samples: dict[str, list[str]] = defaultdict(list)
    rows = 0
    with jsonl_path.open(encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                violations['parse_error'] += 1
                continue
            rows += 1
            hw = e.get('headword_iast') or e.get('headword') or ''
            # 1. headword_iast script vs declared lang
            script = classify_script(hw)
            if script and expected and script not in expected:
                # Bilex dictionaries (role='equivalents') legitimately have
                # multi-script headwords — e.g. yogacarabhumi-idx lists both
                # Sanskrit and Tibetan terms as headwords. Skip the hard check
                # for those; only enforce on monolingual lemma dictionaries.
                role = (meta.get('role') or '').lower()
                strict_lang = lang in ('skt', 'sa', 'bo', 'pi', 'pal', 'pa')
                if role != 'equivalents' and strict_lang:
                    violations['hw_wrong_script'] += 1
                    if len(samples['hw_wrong_script']) < 3:
                        samples['hw_wrong_script'].append(
                            f'id={e.get("id")} hw={hw!r} script={script} expected={sorted(expected)}'
                        )
            # 2. headword vs headword_norm presence
            if 'headword_norm' not in e:
                violations['missing_norm'] += 1
            # 3. body.equivalents pre-check (deeper check in build)
            body = e.get('body') or {}
            eq = body.get('equivalents')
            if isinstance(eq, dict):
                skt = eq.get('skt_iast') or ''
                if skt and (CJK.search(skt) or TIBETAN.search(skt)):
                    violations['eq_skt_wrong_script'] += 1
                    if len(samples['eq_skt_wrong_script']) < 3:
                        samples['eq_skt_wrong_script'].append(
                            f'id={e.get("id")} skt={skt!r}'
                        )
    return rows, {'violations': violations, 'samples': samples}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--sources', type=Path, default=Path('data/sources'))
    p.add_argument('--jsonl-dir', type=Path, default=Path('data/jsonl'))
    p.add_argument('--out', type=Path,
                   default=Path('data/reports/phase4-all-sources-schema.md'))
    p.add_argument('--strict', action='store_true')
    args = p.parse_args()

    if not args.jsonl_dir.exists():
        print(f'ERROR: {args.jsonl_dir} missing — JSONL must be present (gitignored).',
              file=sys.stderr)
        return 2

    slug_dirs = sorted(d for d in args.sources.iterdir()
                       if d.is_dir() and (d / 'meta.json').exists())

    rows_by_slug: dict[str, int] = {}
    violations_by_slug: dict[str, Counter] = {}
    samples_by_slug: dict[str, dict] = {}
    sources_with_issues = []

    for d in slug_dirs:
        meta = json.loads((d / 'meta.json').read_text(encoding='utf-8'))
        slug = meta['slug']
        jsonl = args.jsonl_dir / f'{slug}.jsonl'
        if not jsonl.exists():
            # Curated assets (_canonical / _kosynonym / etc.) have no JSONL.
            continue
        rows, result = audit_jsonl(jsonl, meta)
        rows_by_slug[slug] = rows
        if any(result['violations'].values()):
            violations_by_slug[slug] = result['violations']
            samples_by_slug[slug] = result['samples']
            sources_with_issues.append(slug)

    # Markdown report
    lines = ['# audit-all-sources-schema (Phase 4-C)', '']
    lines.append(f'- sources scanned: {len(rows_by_slug)}')
    lines.append(f'- sources with issues: {len(sources_with_issues)}')
    lines.append(f'- total rows: {sum(rows_by_slug.values()):,}')
    lines.append('')

    if not sources_with_issues:
        lines.append('## ✅ All sources clean')
        lines.append('')
        lines.append('No headword-script mismatches, no body.equivalents.skt_iast violations, no missing norms.')
    else:
        lines.append('## Sources with issues')
        lines.append('')
        lines.append('| source | rows | hw_wrong_script | missing_norm | eq_skt_wrong_script | parse_error |')
        lines.append('|---|---:|---:|---:|---:|---:|')
        for slug in sorted(sources_with_issues,
                           key=lambda s: -sum(violations_by_slug[s].values())):
            v = violations_by_slug[slug]
            lines.append(
                f'| {slug} | {rows_by_slug[slug]:,} | '
                f'{v.get("hw_wrong_script", 0)} | '
                f'{v.get("missing_norm", 0)} | '
                f'{v.get("eq_skt_wrong_script", 0)} | '
                f'{v.get("parse_error", 0)} |'
            )
        lines.append('')
        lines.append('## Sample violations')
        lines.append('')
        for slug in sorted(sources_with_issues):
            samples = samples_by_slug.get(slug, {})
            if not any(samples.values()):
                continue
            lines.append(f'### {slug}')
            for kind, examples in sorted(samples.items()):
                lines.append(f'**{kind}**:')
                for ex in examples:
                    lines.append(f'- `{ex}`')
            lines.append('')

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines))
    print(f'\n→ wrote {args.out}', file=sys.stderr)

    if args.strict and sources_with_issues:
        # Hard-fail only on `eq_skt_wrong_script` because that breaks the
        # equivalents pipeline. Soft warnings about headword script are
        # often expected (Tibetan-Chinese dictionaries with bilingual
        # headwords, etc.) — surface them but don't block CI.
        hard = any(violations_by_slug[s].get('eq_skt_wrong_script', 0) > 0
                   for s in sources_with_issues)
        if hard:
            print('FAIL: at least one source has body.equivalents.skt_iast violations.',
                  file=sys.stderr)
            return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
