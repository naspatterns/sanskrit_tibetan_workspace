# PROJECT_STATUS.md — Sanskrit-Tibetan Workspace v2 (state at 2026-05-04)

**Repository commit**: `64eb0ee` (main)
**Phases complete**: 0, 1, 2, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 3.5b, 3.6, **3.7 (with 5+1 follow-ups)**
**Phases pending**: 4 (deploy), 5 (Edge API), 6 (Reader), 7 (Vocab)

---

## Executive snapshot

A multi-dictionary Sanskrit/Tibetan/Pali search + declension + reader
web app rewritten from v1. **3.81M entries** across **148 dictionaries**
ship as **9 compressed indices (~89 MB)** loaded eagerly into the browser.
Search latency is **<1 ms** (Map.get + binary search) with first-paint
~3 s cold / ~50 ms cached (Service Worker).

| Quality dimension | Metric | Target | Status |
|---|---:|---:|---|
| Schema integrity (JSONL) | 0 errors / 3.81M entries | 0 | ✅ |
| Index round-trip | 7/7 indices @ 100% random lookup | 100% | ✅ |
| Reverse precision EN | 15/15 strict, 15/15 loose | ≥12 | ✅ |
| Reverse precision KO | 15/15 strict, 15/15 loose | ≥8  | ✅ |
| Sentinel 50 (curated) | 50/50 ✅ (100%) | ≥40 | ✅ |
| Sentinel 215 (extended) | 202/215 ✅ (94.0%) | ≥80% | ✅ |
| Korean coverage | 12.79% (of all 3.36M searchable) | ≥10% | ✅ |
| Test suite | 79 pytest + 104 vitest = 183 | all green | ✅ |
| TypeScript strict | 0 errors / 257 files | 0 | ✅ |
| Lighthouse a11y | 95 / 100 | ≥90 | ✅ |
| Cloudflare 25 MiB cap | All 9 indices fit | each ≤25 | ✅ |

---

## Repo at a glance (`tree -L 1`)

```
ARCHITECTURE.md, README.md, ROADMAP.md, LICENSES.md     ← design docs
CLAUDE.md                                                ← per-session orientation (gitignored)
PROJECT_STATUS.md                                        ← this file
REPRODUCIBLE.md                                          ← step-by-step rebuild

pyproject.toml, uv.lock                                  ← Python 3.12, uv-managed
package.json, vite.config.ts, svelte.config.js, tsconfig.json

docs/                                                    ← reference (committed)
  schema.json                JSONL schema
  dict-source.md             meta.json spec + priority bands
  v1-feedback.md             FB-1..8 user concerns
  decisions-pending.md       ADRs
  declension-tab.md          Phase 3.5 design

scripts/                     44 Python scripts (8 lib + 36 entrypoints)
  lib/                       shared helpers (io/snippet/reverse_tokens/transliterate/normalize/html_utils/types/zstd_io)

tests/                       79 pytest tests (Phase 1 helpers)
data/
  sources/                   148 meta.json   (committed)
  reports/                   audit + benchmarks (committed)
  translations.jsonl         9,995 Phase 2b ko (committed)
  translations-en-extended.jsonl  39,873 Phase 3.7 ko (committed)
  jsonl/                     3.81M entries   (gitignored, regenerable, ~5.6 GB)
  translations/              chunks + batch state  (gitignored)

public/indices/              9 compressed .zst files (gitignored, ~89 MB)
src/                         Svelte 5 + SvelteKit (15.7K LOC total)
  lib/indices/               types, loader, reverse_meta parsing
  lib/search/                engine, transliterate, lang detection
  lib/declension/            parse, render
  routes/+page.svelte        main search UI (760 LOC)
  routes/declension/         곡용 tab
  routes/+layout.svelte      shell
static/                      sw.js (v5 cache), _headers, robots.txt
```

---

## Indices inventory (production deploy artifact)

| File | Size | Decoder | Schema | Phase |
|---|---:|---|---|---|
| `tier0.msgpack.zst` | 23 MB | msgpack | `{norm: {iast, entries: [Tier0Entry]}}` | 2 + 3.7B |
| `tier0-bo.msgpack.zst` | 7.7 MB | msgpack | same | 3.3 |
| `tier0-extended.msgpack.zst` | 9.1 MB | msgpack | same (top-10K..20K) | 3.7A |
| `equivalents.msgpack.zst` | 12 MB | msgpack | `{key: [EquivRow]}` | 2.5 |
| `reverse_en.msgpack.zst` | 17 MB | msgpack | `{token: [entry_id]}` | 2 + 3.7 |
| `reverse_ko.msgpack.zst` | 918 KB | msgpack | same | 2 + 3.7 |
| `reverse_meta.msgpack.zst` | 8.9 MB | msgpack | `{dicts:[slug], ids:{eid:[iast,dict_idx]}}` | 3.6 |
| `declension.msgpack.zst` | 2.0 MB | msgpack | `{norm: [DeclensionRow]}` | 3.5 |
| `headwords.txt.zst` | 7.7 MB | text | `norm\tiast\trank\tupasarga` per line | 2 + 3.7 |
| **Total** | **88.3 MB** | — | — | — |

All under Cloudflare Pages **25 MiB single-file cap**.

---

## Phase progress (chronological)

### Phase 0 — Scaffolding ✅
Repo structure, design docs, schema, license inventory.

### Phase 1 — JSONL extraction ✅
- `extract_from_v1.py` extracts 3.36M entries from v1 SQLite
- 130 source dicts → `data/jsonl/<slug>.jsonl`
- 79 unit tests verify schema + invariants
- `verify.py` parallel validation with `fastjsonschema`

### Phase 2 — Tier 0 + FST + reverse index ✅
- `frequency.py` priority-weighted top-10K headword scoring
- `build_tier0.py` materializes top-10K with snippets
- `build_fst.py` headwords sorted text for binary search
- `build_reverse_index.py` reverse.en/ko aggregation

### Phase 2b — Top-10K En→Ko translation ✅
- 9,995 / 9,995 entries translated via Claude Code sub-agents (4 days)
- `data/translations.jsonl` committed (4 MB)

### Phase 2.5 — Zone B 대응어 통합 ✅
- 17 source dicts × 445K rows (after dedup)
- `build_equivalents_index.py` → 13 MB compressed
- Multi-channel keys (skt_iast / tib_wylie / zh)

### Phase 3.1-3.6 — Frontend + UX + Audit ✅
- 3.1: Svelte UI scaffold (5-channel search, zones, dark mode)
- 3.2: Search UX polish (autocomplete, keyboard, URL sync, debounce)
- 3.3: Tibetan tier0 (`tier0-bo.msgpack.zst`)
- 3.4: Equivalents UX (chip colors, EquivDetail modal, pagination)
- 3.5: Declension tab (top-10K Heritage paradigms)
- 3.5b: Comprehensive audit (5 tracks · 22+ reports)
- 3.6: P0/P1 fixes (reverse_meta, Cloudflare 25MB cap, mobile, a11y)

### Phase 3.7 — Data quality + Sentinel polish ✅ (this session's focus)

| Sub-step | Outcome | Commit |
|---|---|---|
| **P1-1** reverse salience boost | EN strict 2/15 → 9/15 | `c0972e1` |
| **P1-3** yogācārabhūmi zh contamination | 119,464 → 0 | `c0972e1` |
| **P1-2** en-extended translation | 39,873 / 39,874 ko via sub-agent | `a403d2f` |
| Sentinel 50 baseline | 24/50 ✅ | `85ddafb` |
| KO synonym injection | KO reverse 4/15 → 15/15 (100%) | `e4c8f0f` |
| EN synonym injection | EN reverse 9/15 → 15/15 (100%) | `4cac0cb` |
| **5 follow-ups** B+D+A+E+C | Sentinel 50: 19→50 (100%), 215: 95.5% | `559393a` |
| **Upasarga tagging (Depth 2)** | 23 SA + 30 BO canonical prefix recognition | `64eb0ee` |

#### Phase 3.7 quality lifts (cumulative)

| Metric | Phase 3.6 baseline | Phase 3.7 final | Δ |
|---|---:|---:|---:|
| Korean coverage | 11.31% | **12.79%** | +1.48pp |
| EN reverse strict (audit-A) | 2/15 | **15/15** | +650% |
| KO reverse strict (audit-A) | 6/15 | **15/15** | +150% |
| Sentinel 50 | 19 ✅ | **50 ✅** | +163% |
| Sentinel 215 | n/a | **202 ✅ (94%)** | new |
| reverse_ko index | 0.17 MB | 0.9 MB | 5.5x tokens |
| tier0 size | 28.78 MB | 23 MB | -20% (snippet caps) |
| tier0 coverage | 10K | 10K + ext 10K = **20K** | 2x |
| Headwords schema | 2-col | **4-col** (rank, upasarga) | +2 cols |

---

## Curated data assets (committed, source-of-truth)

```
data/sources/_canonical/important.txt    332 philosophical 핵심어
data/sources/_kosynonym/synonyms.json     52 iast → 89 KO/Hanja synonyms
data/sources/_ensynonym/synonyms.json    113 iast → 193 EN synonyms
data/sources/_upasarga/upasarga.json      23 SA + 30 BO canonical prefixes
data/translations.jsonl                  9,995 Phase 2b top-10K Korean
data/translations-en-extended.jsonl     39,873 Phase 3.7 top-10K..50K Korean
data/sources/<slug>/meta.json            148 dictionary metadata files
```

These power build-time enrichment of the indices.

---

## Test coverage

- **Python (pytest)**: 79 tests in `tests/`
  - normalize / transliterate / snippet / reverse_tokens / html_utils
- **TypeScript (vitest)**: 104 tests in `src/lib/**`
  - `engine.test.ts` (search routing, prefix re-rank)
  - `transliterate.test.ts` (HK/IAST/Devanagari)
  - `loader.test.ts` (parseHeadwords 2/3/4-col, objectToMap, recomputeOverall)
  - `parse.test.ts` (declension grid)
  - `lang.test.ts` (script detection)

Total: **183 tests, all green**.

---

## Known limitations & deferred work

### Phase 5+ (Edge API + R2)
- Long-tail entries (rank > 20,000) require Phase 5 D1 lookup
- Multi-word sandhi unfolding (`brahmāsmi` → `brahma + asmi`)
- Devanagari / Hanzi auto-conversion in main search bar (currently passthrough)
- Real morphological analyzer (e.g. `vidyut-prakriya`) — current upasarga
  matching is heuristic (IAST prefix + 2-char remainder)

### Phase 4 (deploy) — known prerequisites
- Cloudflare Pages account
- Custom domain DNS pointed
- CI workflow (`.github/workflows/build.yml` not yet created)
- See `data/reports/audit-2026-04-30/audit-E-deploy.md §6` checklist

### Performance optimizations (deferred)
- `frequency.py`, `build_tier0.py`, `build_reverse_index.py` are
  single-process. Multiprocessing.Pool would yield 3-5× speedup.
  Not blocking — total build time ~5 min.
- Decompression on main thread; Web Worker offload for Lighthouse
  Performance ≥80 (currently 45 with cold-load splash).

---

## How to verify (CI-friendly)

```bash
# Quick smoke test (all should pass with no manual fixes)
uv run pytest -q                              # 79 pass
npm test                                      # 104 pass
npx svelte-check --threshold error            # 0/0
uv run python -m scripts.verify               # 0 errors
uv run python -m scripts.audit_sentinel_50    # 50/50 ✅
uv run python -m scripts.audit_random_lookup  # 7/7 indices @ 100%
npm run build                                 # exits 0
```

For full rebuild from v1 SQLite (~10 minutes): see `REPRODUCIBLE.md`.

---

## Recent commits (last 10)

```
64eb0ee  feat: upasarga tagging (Depth 2) — Sanskrit 23 + Tibetan 30 canonical prefixes
559393a  feat: Phase 3.7 5 follow-ups — Sentinel 50/50 (100%), 200/200 (95.5%)
4cac0cb  feat: EN synonym injection — EN reverse precision 9/15 → 15/15 (100%)
e4c8f0f  feat: KO synonym injection — KO reverse precision 4/15 → 15/15 (100%)
85ddafb  feat: audit_sentinel_50.py — 50 query 자동 평가 (Phase 3.7 baseline)
a403d2f  feat(P1-2): en-extended sub-agent 39,873 + JSONL apply + 인덱스 재빌드
c4e5921  feat: scripts/batch_status.py — one-screen progress for in-flight batches
5b8b104  docs: Phase 3.7 진입 + P1-1/P1-3 결과 + batch ready 안내
a8c7a28  feat(P1-2): translate_en_extended.py — top-50K batch + top50k.txt
c0972e1  fix(P1-1, P1-3): reverse salience boost + equivalents.zh sanitize
```

---

## Next session priorities (suggested)

1. **Phase 4 deploy** — Cloudflare Pages + adapter-static + CI
2. **P0-2 EU $451 batch** (or sub-agent path) — DE/FR/LA quality lift
3. **Multiprocessing builders** — Phase 5 prerequisite optimization
4. **Devanagari/Hanzi auto-conversion** — Sentinel 215's 2 remaining ❌

— end —
