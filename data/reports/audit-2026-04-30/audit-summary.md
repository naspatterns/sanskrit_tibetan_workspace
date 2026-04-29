# 통합 검토 종합 보고서 — Sanskrit-Tibetan Workspace v2

Date: 2026-04-30
Phase: 3.5b 통합 검토 (Audit) — Phase 4 배포 직전
Scope: 5 트랙 (A 정합성·B 완전성·C UX·D 코드품질·E 배포 readiness)
Status: **Day 1+2 완료** (Track A·B·D static), **Day 3 deferred** (Track C·D4-6 browser, Track E)

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

### Track C — UX 시연 ⏭️ Day 3

- Sentinel 50 queries 초안 작성 ✅ (`sentinel-50-queries-draft.md`)
  - 9 카테고리: 산스크리트 핵심 10 / prefix 5 / Wylie 5 / 영어 역검색 10 / 한국어 5 / 한자 5 / 혼용 5 / typo 3 / dead zone 2
  - 사용자 검토 대기 중
- 시연 시점: production preview build (`npm run preview`) 가동 후
- Track C는 P0/P1 fix 전후 비교가 가장 가치 있음 → Phase 3.6 진입 후 일정 협의

### Track D — Code Quality + Build ✅

| # | Item | Verdict | P-level |
|---|---|---|---|
| D1 | TypeScript strict | ✅ 0 errors / 0 warnings / 255 files | — |
| D2 | Svelte 5 runes (Explore agent) | ✅ 0 P0, 1 P1 closure, 2 P2 style | **P1-D2-1** |
| D3 | Production build | ✅ adapter-static 성공 ~50 kB gzipped | — |
| D7 | Build script perf | ✅ 4:18 cold rebuild | P3 (multiprocessing) |
| D8 | Test coverage | ⚠️ parse.ts·loader.ts 갭 | **P1-D8-1·D8-2** |
| D4 Heap | ⏭️ Day 3 | — | — |
| D5 Latency | ⏭️ Day 3 | — | — |
| D6 SW | ⏭️ Day 3 | — | — |
| D9 HMR race | ⏭️ Day 3 (production preview) | — | — |

상세: `audit-D-summary.md` + `audit-D-build.md` + `audit-D-svelte5.md` + `audit-D-tests.md` + `audit-D-buildperf.md`

### Track E — Production Readiness ⏭️ Day 3

- E1 adapter-static export 완전성 (D3에서 일부 검증됨)
- E2 CSP / security headers
- E3 Cloudflare Pages 한계
- E4 LICENSES.md 17 equiv source coverage
- E5 사용자 피드백 루프

---

## 4. Phase 3.6 확장 backlog (audit 결과 통합)

```
P0 (must fix before Phase 4 deploy)
├─ P0-1 reverse search UI render headword + snippet
│       (reverse_meta.msgpack.zst 신규 + +page.svelte 갱신)
└─ P0-2 DE/FR/LA $225 batch re-translation
        (priority pwg→pwk→cappeller→schmidt→stchoupak→burnouf→grassmann→bopp-latin)

P1 (Phase 3.6 sprint)
├─ P1-1 build_reverse_index.py headword salience boost
├─ P1-2 English-source dicts 한국어 $30 batch (top 50K)
├─ P1-3 extract_equiv_yogacarabhumi.py zh column-mapping fix
├─ P1-D2-1 $effect debounce closure refactor (+page, declension)
├─ P1-D8-1 parse.ts unit tests (~30 min)
└─ P1-D8-2 loader.ts unit tests (~1h)

Original 3.6 polish (1-1.5일)
├─ 모바일 반응형 (≤768px)
├─ Lighthouse Performance ≥ 90 / Accessibility ≥ 95
├─ 키보드 navigation 완성
└─ Loading state per-channel progress

P2/P3 deferred
├─ P2 9 dicts FB-5 family rule align
├─ P2 1,119 equiv-amarakoza 'amarakoza-v1-pX' 슬러그 re-extract
├─ P2 stores/theme.ts unit test, audit_meta_consistency relax
├─ P3 147 dicts entry_count auto-fill
├─ P3 frequency.py stable sort
└─ P3 build_tier0/build_reverse_index multiprocessing (52% speedup)
```

원래 Phase 3.6 = 1일 polish.
**확장 Phase 3.6 = ~3-5일** (audit P0 2건 + P1 6건 + polish 1.5일).

---

## 5. Day 3 계획 (다음 세션)

### 5.1 입장 조건
사용자가 Sentinel 50 queries 검토 완료 + Phase 3.6 진입 결정 OK.

### 5.2 작업 순서
1. **Track C 시연** — production preview build 가동 → 50 queries 직접 입력 → CSV 기록 (audit-C-sentinel-results.csv)
2. **D4 Heap profile** — Chrome devtools memory snapshot, 7 indices load 후 heap, 검색 100회 후 leak 여부
3. **D5 Latency** — bench/index.html 확장 (declension, equivalents 채널 추가), 1000 query × 5 round
4. **D6 Service Worker** — devtools application tab으로 install/activate/cache-first 실제 동작, offline 검증
5. **D9 HMR race** — production preview에서 declension `?q=` 자동 채움 검증 (dev에서만 race이면 OK)
6. **Track E** — Cloudflare Pages 한계, CSP draft, LICENSES re-check
7. **audit-summary.md 최종 갱신** + Phase 3.6 진입 게이트

### 5.3 시간 추정
Day 3 = ~4-6시간 (Track C 1.5h + D4-6 2h + Track E 1h + 통합 1h)

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
