# PROJECT_STATUS.md — Sanskrit-Tibetan Workspace v2 (state at 2026-05-16)

**Repository commit**: `0b041ec` (main)
**Phases complete**: 0, 1, 2, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 3.5b, 3.6, **3.7 (with 5+1 follow-ups)**, **5 (Edge API + D1)**, **4 (Cloudflare Pages first deploy)**, **Sprint 1 (perf overhaul — Lighthouse 45→85 desktop / 96 mobile)**
**Phases pending**: 6 (Reader), 7 (Vocab)
**Production**: https://sanskrit-tibetan-workspace.pages.dev

---

## Executive snapshot

A multi-dictionary Sanskrit/Tibetan/Pali search + declension + reader web
app rewritten from v1. **3.81M entries** across **148 dictionaries** ship
as **9 compressed indices (~89 MB)** loaded eagerly into the browser, with
**Edge API + D1 fallback (Phase 5)** for the long-tail 2.98M entries
beyond top-20K. Search latency is **<1 ms** local (Map.get) and **~600ms
cold / ~50 ms cached** for D1 fallback (Korea→ICN edge).

| Quality dimension | Metric | Target | Status |
|---|---:|---:|---|
| Schema integrity (JSONL) | 0 errors / 3.81M entries | 0 | ✅ |
| Index round-trip | 7/7 indices @ 100% random lookup | 100% | ✅ |
| Reverse precision EN | 15/15 strict, 15/15 loose | ≥12 | ✅ |
| Reverse precision KO | 15/15 strict, 15/15 loose | ≥8  | ✅ |
| Sentinel 50 (curated) | 50/50 ✅ (100%) | ≥40 | ✅ |
| Sentinel 215 (extended) | 202/215 ✅ (94.0%) | ≥80% | ✅ |
| **D1 + Edge API (Phase 5)** | **8/8 ✅ probes** | 100% | ✅ |
| **Long-tail coverage** | **2.98M / 3.81M searchable** | full corpus | ✅ |
| Korean coverage | 12.79% (of all 3.36M searchable) | ≥10% | ✅ |
| Test suite | 79 pytest + 104 vitest = 183 | all green | ✅ |
| TypeScript strict | 0 errors / 258 files | 0 | ✅ |
| Lighthouse a11y | 95 / 100 | ≥90 | ✅ |
| **Lighthouse perf (desktop)** | **85 / 100** (was 45) | ≥80 | ✅ |
| **Lighthouse perf (mobile)** | **96 / 100** (was 45) | ≥80 | ✅ |
| **TBT (desktop)** | **205 ms** (was ~3000 ms) | <300 ms | ✅ |
| **TBT (mobile)** | **0 ms** (lazy mode) | <300 ms | ✅ |
| Cloudflare 25 MiB cap | All 9 indices fit | each ≤25 | ✅ |
| **D1 free tier headroom** | **780MB / 5GB · <100 req/일** | <80% | ✅ |

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

### Phase 3.7 — Data quality + Sentinel polish ✅

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

### Phase 5 — Edge API + D1 ✅ (사용자 결정으로 Phase 4 swap)

| Sub-step | Outcome | Detail |
|---|---|---|
| **5.1** D1 setup | `wrangler d1 create stw-entries` | region APAC/ICN (한국 가까움), id `b53085a2-…` |
| **5.1** Schema design | `workers/sql/schema.sql` | light cols (id, norm, iast, dict, priority, snippet, ko, target_lang) |
| **5.1** SQL dump | `scripts/build_d1_dump.py` | 60 chunks · 50K rows/file · 50 rows/INSERT (SQLITE_TOOBIG safety) |
| **5.1** Bulk import | `workers/import_all.sh` | 2,978,861 rows imported · 780 MB · resumable |
| **5.2** Worker API | `workers/src/index.ts` | `/api/search/:norm` exact + prefix · `/api/entry/:id` · `/api/health` |
| **5.2** CORS + Cache | response headers | `Access-Control-Allow-Origin: *` · `max-age=86400` |
| **5.2** Deploy | `wrangler deploy` | `https://stw-api.naspatterns.workers.dev` |
| **5.3** Client fallback | `src/lib/search/apiSearch.ts` | AbortSignal · 250ms debounce |
| **5.3** UI | `+page.svelte` zone-edge section | loading state · graceful 404 |
| **5.4** Audit | `scripts/audit_d1_integrity.py` | 8/8 ✅ · vajracchedikā/śūraṅgama Sentinel ❌→✅ |

All in commit `c615b0a`. Free tier 사용량: D1 780MB / 5GB · Workers <100 req/일.

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
- ~~Decompression on main thread; Web Worker offload for Lighthouse
  Performance ≥80 (currently 45 with cold-load splash).~~ **Resolved
  in Sprint 1 A1 (commit `495937d`)** — score now 85 desktop / 96
  mobile (see `data/reports/audit-2026-04-30/audit-sprint1-lighthouse.md`).
- Edge API autocomplete results sort by `priority` only; ties fall
  back to alphabetical. Adding a `rank` column to D1 (mirror of
  headwords.txt rank field) would lift `dharma` above `dha`, `dhah` …
  in the lazy-mode autocomplete dropdown. Not blocking — lazy mode
  users still get *working* autocomplete after Sprint 1 A4.

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
0b041ec  fix(Sprint 1): preload hints in app.html, not svelte:head (SPA fallback)
9c54a71  docs(Sprint 1 C5): document HTTP/3 + Early Hints activation on Cloudflare
c749a54  perf(Sprint 1 A4): Edge API autocomplete — /api/autocomplete/:prefix
3cb73e5  perf(Sprint 1 A6): focus prefetch — lazy mode warms core tier on first input
9f6ff58  perf(Sprint 1 A5): self-host Noto Sans Devanagari (Google Fonts removed)
0c68ed8  perf(Sprint 1 A3): reverse_meta lazy load (auxiliary → on-demand)
198caaf  perf(Sprint 1 A2): static preload of core tier indices in HTML head
495937d  perf(Sprint 1 A1): offload fzstd decompress + msgpack decode to module Worker
ba8e5f6  ci(Phase 4): GitHub Actions — pytest + vitest + svelte-check + dry-build
8664e9a  fix(Phase 4): CSP allow Worker API origin for cross-origin Edge fetch
```

---

## Phase 4 — Cloudflare Pages first deploy ✅ (2026-05-08)

### What's live now
- **URL**: https://sanskrit-tibetan-workspace.pages.dev
- **Edge**: ICN/APAC (server: cloudflare, cf-ray ICN)
- **Build artifact**: 89 MB (9 indices + app shell + sw.js + _headers)
- **Routing decision**: 옵션 A (Pages 정적 + Worker 별 도메인) — 코드 변경 0줄
- **CSP fix** (`8664e9a`): connect-src allows stw-api.naspatterns.workers.dev
  — without this Phase 5 long-tail fallback silent-fails in production
- **CI** (`ba8e5f6`): pytest + vitest + svelte-check + dry-build (broken
  static/indices symlink replaced with empty dir for CI build)

### Verified
- ✅ `curl -sI /` HTTP 200 + CSP includes Worker origin
- ✅ `curl -sI /indices/headwords.txt.zst` cache-control max-age=31536000 immutable
- ✅ `audit_d1_integrity` 8/8 ✅ (vajracchedika·surangama via Edge API)
- ✅ Local CI sim (clone /tmp + remove symlink + npm run build) → 216 KB shell

### Deploy command (every release)
```bash
npm run build
npx wrangler pages deploy ./build \
  --project-name=sanskrit-tibetan-workspace \
  --branch=main \
  --commit-message="<ASCII description>" \
  --commit-hash=$(git rev-parse --short HEAD)
```

⚠ `--commit-message` 명시 필수 — wrangler가 한글/em-dash 포함 commit
message에서 UTF-8 인코딩 오류 (`code: 8000111`)로 deploy fail.

---

## Next session priorities (Sprint 2 / Phase 6 / Phase 7)

### Sprint 2 (perf — optional, gates on real-user metrics)
- **B1** Top-1K instant tier — push desktop TTI < 1.0 s
- **B2** zstd-wasm replacing fzstd — combined with A1 worker offload,
  push desktop TBT below 100 ms
- **B3** SW manifest.json — partial index updates instead of full
  88 MB re-cache on every cache bump
- **B4** D1 covering index `(headword_norm, priority)` — shave 100-
  200 ms off Edge API cold path

### Phase 4 잔여 (verify on real users, ~30 min)
1. **브라우저 SW 검증** — DevTools Application → Cache Storage →
   `stw-indices-v8` populated, network idle 후 indices Cache Hit
2. ~~**Lighthouse**~~ ✅ Done — see Sprint 1 commit `0b041ec` /
   `audit-sprint1-lighthouse.md`. Desktop 85, Mobile 96.
3. **Sentinel 50/215** production URL에서 재실행 (manual 또는 audit script)
4. **Custom domain** (선택, ~$10-15/년)

### Phase 6 Reader tab (~3-5일)
- `/reader` route
- 텍스트 import (paste/file)
- 어휘 lookup overlay (click → tier0 entry modal)

### Phase 7 Vocab tab (~3-5일)
- 어휘 학습 (FSRS spaced repetition)
- localStorage progress
- export/import deck

### 참고 자료
- `REPRODUCIBLE.md §10` — Phase 4 deploy 단계 + 검증 명령
- `CLAUDE.md §7` — 다음 세션 진입 가이드
- `ROADMAP.md §Phase 4` — 체크리스트 + 잔여

— end —
