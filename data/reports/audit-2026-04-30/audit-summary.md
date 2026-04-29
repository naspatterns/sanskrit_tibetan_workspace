# 통합 검토 종합 보고서 — Sanskrit-Tibetan Workspace v2

Date: 2026-04-30
Phase: 3.5b 통합 검토 (Audit) — Phase 4 배포 직전
Scope: 5 트랙 (A 정합성·B 완전성·C UX·D 코드품질·E 배포 readiness)
Status: **Day 1+2+3 완료** (Track A·B 자동·D 자동+browser·E 자동·C user demo guide). **사용자 시연 (Sentinel 50 queries baseline)은 다음 세션에서 진행**.

---

## 1. 한 줄 결론

✅ **데이터 layer 자체는 깨끗** (3.81M entries · errors 0 · id duplicates 0 · missing iast·norm 0).

⚠️ **5개 P0/P1 발견** — 모두 *빌드/UI/번역* 결함이지 데이터 corruption 아님. Phase 3.6 sprint에서 fix 가능 (~3-5일).

⏭️ **Day 3 (Track C UX 시연 + browser perf)는 다음 세션 진행** — Sentinel queries 사용자 검토 후.

---

## 2. 베이스라인

```
Dicts ........................................ 148
Entries ...................................... 3,810,986
Compressed indices (7) ....................... 76 MB
Schema errors ................................ 0  ✅
Schema warnings (categorized) ................ 189,468 (대부분 학술 표기)
Unique entry ids ............................. 3,810,986 (no dups)
Missing headword_iast / norm ................. 0
TypeScript files ............................. 255
TypeScript errors ............................ 0
Production build (gzipped) ................... ~50 kB client critical-path
Tests ........................................ 75 vitest + 79 pytest = 154 pass
Cold rebuild .................................. 4:18 min
```

---

## 3. 트랙별 결과

### Track A — Data Integrity ✅

| # | Item | Verdict | P-level |
|---|---|---|---|
| A1 | Schema validation | ✅ 0 errors / 3.81M | — |
| A2 | meta ↔ JSONL consistency | ⚠️ 147× entry_count 미선언 (cosmetic), 9 FB-5 strict mismatch | P3 + P2 |
| A3 | equivalents dedup | ✅ 14 sources, 1.03% multi-source | — |
| A4 | reverse precision | ❌ EN 2/15 strict, KO 6/15 strict | **P1** (P1-1, P1-2) |
| A5 | tier0 ↔ tier0-bo split | ✅ 910 keys overlap (intended cross-ref) | P2 |
| A6 | warning categorization | ✅ 189K classified — no data damage | P2 |
| A7 | translation merge | ✅ 84K entries with ko (1 orphan) | — |
| A8 | id duplicates | ✅ 0 / 3.81M | — |
| (UI) | reverse hit rendering | ❌ raw entry_id only | **P0-1** |
| (data) | equiv.zh field | ❌ 119K Wylie/IAST in zh slot | **P1-3** |

상세: `audit-A-summary.md` + `audit-A-warnings.md` + `audit-A-meta-consistency.md` + `audit-A-translations.md` + `audit-A-indices.md` + `audit-A-reverse-precision.md` + `audit-A-zh-contamination.md`

### Track B — Data Completeness ⚠️

| # | Item | Verdict | P-level |
|---|---|---|---|
| B1 | translation coverage re-baseline | ⚠️ ko 16.3%, EN-source 0% | P1 |
| B2 | DE/FR/LA quality 498 sample | ❌ **score 1.87/4.0** — v1 ko는 per-token substitution | **P0-2** |
| B3 | Tibetan tier0-bo coverage | ✅ 47/50 sentinel hits (94%) | — |
| B4 | Equivalents source unbalance | ✅ in audit-A-indices.md A3 | — |
| B5 | OCR Tier C cost | 불광사전 $4.50 (P2 defer), 梵語佛典 $0.30 (P3) | P2/P3 |
| B6 | long-tail distribution | 98.4% 단어 long-tail (Phase 5 정당성) | Phase 5 driver |
| B7 | dead zone leakage | ✅ 35 excluded dicts → 0 leaks | — |

상세: `audit-B-summary.md` + `audit-B-coverage.md` + `audit-B-eu-quality.md`

### Track C — UX 자동 측정 ✅ + 사용자 시연 가이드 ✅

| Item | Verdict | P-level |
|---|---|---|
| Sentinel 50 queries (작성, 사용자 검토 후 #15 mahā 정정) | ✅ ready | — |
| Lighthouse Performance | ❌ 45/100 (측정 artifact, splash + SW cold load) | P2 |
| Lighthouse Accessibility | ✅ 95/100 (목표 달성) | — |
| Lighthouse Best Practices | ✅ 100/100 | — |
| Lighthouse SEO | ⚠️ 82/100 (meta description 부족) | P2 (Phase 4) |
| Production preview reachability | ✅ /, /declension, /sw.js 200 | — |
| 사용자 시연 가이드 | ✅ 작성 (`audit-C-demo-guide.md`) | — |

상세: `audit-C-a11y.md` + `audit-C-demo-guide.md`

**사용자 시연 (Sentinel 50 queries baseline)은 다음 세션에서 진행** — Phase 3.6 P0/P1 fix 전 baseline + fix 후 비교를 위해 의도적 보류.

### Track D — Code Quality + Build ✅

| # | Item | Verdict | P-level |
|---|---|---|---|
| D1 | TypeScript strict | ✅ 0 errors / 0 warnings / 255 files | — |
| D2 | Svelte 5 runes (Explore agent) | ✅ 0 P0, 1 P1 closure, 2 P2 style | **P1-D2-1** |
| D3 | Production build | ✅ adapter-static 성공 ~50 kB gzipped | — |
| D7 | Build script perf | ✅ 4:18 cold rebuild | P3 (multiprocessing) |
| D8 | Test coverage | ⚠️ parse.ts·loader.ts 갭 | **P1-D8-1·D8-2** |
| D4 Heap | ⏭️ user demo (devtools 수동) | — | guide 제공 |
| D5 Latency | ✅ Map.get 모두 < 1µs, cold load 2.35s (Python) | — | `audit-D-latency.md` |
| D6 SW | ✅ v3 cache, 7 indices precache, scope-limited fetch | P3 (app shell precache) | `audit-D-sw.md` |
| D9 HMR race | ✅ prod 코드 path 분석 — race 없음 (HMR 부재) | — | `audit-D-decl-race.md` |

상세: `audit-D-summary.md` + `audit-D-build.md` + `audit-D-svelte5.md` + `audit-D-tests.md` + `audit-D-buildperf.md` + `audit-D-latency.md` + `audit-D-sw.md` + `audit-D-decl-race.md`

### Track E — Production Readiness ✅

| # | Item | Status | P-level |
|---|---|---|---|
| E1 | adapter-static export | ✅ | — |
| E2 | CSP + headers | ⚠️ `_headers` 미작성 | P1 (Phase 4 entry) |
| E3 | Cloudflare 25 MB 한계 | ❌ **tier0.msgpack.zst 28.78 MB > 25 MB** | **P0 새로 (Phase 4 deploy blocker)** |
| E4 | LICENSES.md 커버리지 | ⚠️ **47 dicts 미명시** (148 - 101) | **P1 새로** |
| E5 | 피드백 루프 | ⏭️ deferred | P2 |

**Phase 4 entry checklist**:
1. tier0 zstd 재압축 (`-22 --ultra`) → ~24 MB OR R2/Workers 이관
2. `static/_headers` 작성 (CSP + Cache-Control + Service-Worker-Allowed)
3. LICENSES.md 47 dicts 보충
4. wrangler.toml 또는 Pages Git integration
5. 도메인 또는 *.pages.dev URL
6. 배포 후 50 sentinel queries 재실행

상세: `audit-E-deploy.md`

---

## 4. Phase 3.6 + Phase 4 확장 backlog (audit 결과 통합 + Day 3)

```
P0 (must fix before Phase 4 deploy)
├─ P0-1 reverse search UI render headword + snippet
│       (reverse_meta.msgpack.zst 신규 + +page.svelte 갱신)
├─ P0-2 DE/FR/LA $225 batch re-translation
│       (priority pwg→pwk→cappeller→schmidt→stchoupak→burnouf→grassmann→bopp-latin)
└─ P0-3 [NEW Day 3] tier0.msgpack.zst (28.78 MB) > Cloudflare 25 MB 한계
        Option A: zstd -22 --ultra 재압축 (30 min)
        Option B: R2/Workers 이관 (Phase 5)
        ※ Phase 4 deploy blocker

P1 (Phase 3.6 sprint)
├─ P1-1 build_reverse_index.py headword salience boost
├─ P1-2 English-source dicts 한국어 $30 batch (top 50K)
├─ P1-3 extract_equiv_yogacarabhumi.py zh column-mapping fix
├─ P1-D2-1 $effect debounce closure refactor (+page, declension)
├─ P1-D8-1 parse.ts unit tests (~30 min)
├─ P1-D8-2 loader.ts unit tests (~1h)
├─ P1-E2 [NEW Day 3] static/_headers 작성 (CSP + Cache-Control)
└─ P1-E4 [NEW Day 3] LICENSES.md 47 dicts 보충

Original 3.6 polish (1-1.5일)
├─ 모바일 반응형 (≤768px) — devtools 시뮬 with audit-C-demo-guide.md
├─ Lighthouse Performance fix (현재 45 — zstd Web Worker 이전 시 80+ 예상)
├─ Lighthouse Accessibility ≥ 95 (현재 95 ✅)
├─ 키보드 navigation 완성
└─ Loading state per-channel progress

P2/P3 deferred
├─ P2 9 dicts FB-5 family rule align
├─ P2 1,119 equiv-amarakoza 'amarakoza-v1-pX' 슬러그 re-extract
├─ P2 stores/theme.ts unit test, audit_meta_consistency relax
├─ P2 [NEW Day 3] zstd 디컴프 Web Worker 이전 (Performance 45→80+)
├─ P2 [NEW Day 3] meta description / sitemap.xml / robots.txt (SEO 82→95)
├─ P3 147 dicts entry_count auto-fill
├─ P3 frequency.py stable sort
└─ P3 build_tier0/build_reverse_index multiprocessing (52% speedup)
```

원래 Phase 3.6 = 1일 polish.
**확장 Phase 3.6 = ~3-5일** (audit P0 2건 + P1 6건 + polish 1.5일).

---

## 5. Day 3 결과 + 다음 세션 작업

### 5.1 Day 3 완료된 항목 ✅

- D5 Latency 정밀 측정 (7 index profile)
- D6 Service Worker 코드 분석 + production 검증
- D9 Declension HMR race production 분석 (race 없음 확인)
- Track E1-E5 (Cloudflare 한계 + LICENSES + CSP draft)
- Lighthouse 자동 측정 (Performance 45 측정 artifact, A11y 95 ✅)
- Sentinel #15 사용자 정정 (māhā → mahā)
- Track C 사용자 시연 가이드 (`audit-C-demo-guide.md`)

### 5.2 다음 세션 작업

**A. 사용자 시연** (Track C 직접 입력, ~2h)
- 50 queries baseline 측정 → `audit-C-sentinel-results.csv`
- D4 Heap profile (devtools 수동, audit-C-demo-guide.md §D4)
- 모바일 시뮬 (devtools)

**B. Phase 3.6 sprint** (~3-5일, audit-C 시연과 병행 가능)

순서:
1. P0-3 tier0 zstd 재압축 (30 min) — 즉시 unblock Phase 4
2. P0-1 reverse_meta.msgpack.zst 신규 + UI 갱신 (~4-6h)
3. P0-2 $225 batch submit (병렬 — 폴링 2-3일)
4. P1-1 build_reverse_index salience boost (~2h) + 재측정
5. P1-3 yogācārabhūmi zh fix (~2-4h)
6. P1-D2-1 + P1-D8-1 + P1-D8-2 (코드/테스트, ~3h)
7. P1-E2 _headers 작성 (~30 min)
8. P1-E4 LICENSES.md 47 dicts 보충 (~1-2h)
9. P0-2 batch retrieve + tier0 재빌드 (~1h)
10. Lighthouse 재측정 + 모바일 polish

**C. Phase 4 deploy entry** (Phase 3.6 완료 후)
- adapter-static build → wrangler pages deploy
- 도메인 결정
- 배포된 URL에서 50 queries 재실행 → before/after 비교

---

## 6. 산출물 인벤토리

### 신규 audit 보고서 (16개)

```
data/reports/audit-2026-04-30/
├── audit-summary.md                    # ← 이 파일
├── audit-A-summary.md
├── audit-A-warnings.md
├── audit-A-meta-consistency.md
├── audit-A-translations.md
├── audit-A-indices.md
├── audit-A-reverse-precision.md
├── audit-A-zh-contamination.md
├── audit-B-summary.md
├── audit-B-coverage.md
├── audit-B-eu-quality.md
├── audit-D-summary.md
├── audit-D-build.md
├── audit-D-svelte5.md
├── audit-D-tests.md
├── audit-D-buildperf.md
└── sentinel-50-queries-draft.md       # 사용자 검토 대상
```

### 신규 audit script (5개)

```
scripts/audit_warnings.py               # Track A6 — warning category breakdown
scripts/audit_meta_consistency.py       # Track A2 — meta ↔ JSONL
scripts/audit_translations_merge.py     # Track A7 — translations.jsonl ↔ tier0
scripts/audit_indices.py                # Track A3+A4(v1)+A5 — index integrity
scripts/audit_reverse_precision.py      # Track A4 v2 — full JSONL id resolution
```

### 로그 (raw output)

```
data/reports/audit-2026-04-30/
├── verify-run.log
├── A8-id-scan.log
├── A6-warnings.log
├── A2-meta.log
├── A7-translations.log
├── A345-indices.log
├── A4-reverse-v2.log
├── A3b-zh-contamination.log
├── B6-longtail.log
├── B7-deadzone.log
├── B3-tibetan.log
├── B5-ocr.log
├── D1-check.log
├── D3-build.log
├── D7-buildperf.log
└── D8-tests.log
```

### 관련 문서 갱신

- `ROADMAP.md` — Phase 3.5b 신설, Phase 3.6 확장
- `docs/decisions-pending.md` — D-Audit-2026-04-30 + D-Audit-Day3-Pending 추가
- `CLAUDE.md` — §1 phase 표 + §6/§7 갱신

### Commit 추적

- `10b9d93` audit(track-A) — Day 1
- `257404f` audit(track-B+D) — Day 2
- (다음) audit(docs) — md 갱신 + main 머지

---

## 7. 주요 통찰

1. **데이터 무결성 자체는 매우 안정적** — 3.81M entries에서 schema error 0건, id duplicate 0건, missing required field 0건. v1 → v2 추출 파이프라인이 견고했다는 증거.

2. **품질 vs 양** — `body.ko` "100% coverage" 통계가 거짓이었음 (per-token substitution). 다른 양적 지표도 의심해서 *실제 사용자가 받는 정보*를 매번 검증해야 함.

3. **UI가 데이터의 보틀넥** — 역검색은 데이터가 잘 저장되어 있어도 UI에서 raw entry_id로만 노출하면 사용자에게 무가치. Phase 3.5b처럼 *audit 단계에서 UI까지 추적*해야 진짜 결함 발견 가능.

4. **Tier0 + tier0-bo 분리는 옳은 결정** — Tibetan 94% sentinel hit, 1.6% 단어 cover but 15.7% entries → top-N 인덱스의 가치 검증.

5. **Long-tail 98.4%** — Phase 5 D1 Edge API가 단순 nice-to-have가 아닌 필수. Tier0만으로는 검색 결과 부족.

6. **코드 품질 견고** — TypeScript 0 error, Svelte 5 runes 0 P0, production build 50 kB gzipped, 154 tests pass. 코드 layer는 deploy-ready.

7. **Audit 효과** — 36시간 audit으로 P0 2건 + P1 6건 발견 + 향후 작업 우선순위 명확. Phase 3.6 시간 1일 → 3-5일 확장 정당화.
