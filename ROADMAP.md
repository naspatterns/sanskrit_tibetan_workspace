# Sanskrit-Tibetan Workspace — Roadmap (v2)

목표: 7주 안에 v1 사용자가 자연스럽게 v2로 넘어올 수 있는 상태 도달.
원칙: **각 Phase는 독립적으로 가치 있고, v1은 무중단 유지**.

---

## Phase 0: 준비 ✅
- [x] 프로젝트 디렉터리 + 뼈대
- [x] README, ARCHITECTURE, ROADMAP 작성
- [x] 명명 결정: Sanskrit-Tibetan Workspace
- [x] 기술 스택 결정 (Svelte 5 + Vite + Cloudflare)
- [x] v1 피드백 7건 반영 (FB-1~7)
- [x] Declension 탭 설계 초안

산출물: 이 저장소.

---

## Phase 1: 데이터 추출 + 검증 ✅ (2026-04-22 완료)

**목표**: v1의 dict.sqlite → JSONL 변환 + 데이터 품질 검증.
v1 데이터를 그대로 활용 (사전별 재파싱 안 함). 빠른 시작.

**산출물**: 130 JSONL (3,364,487 entries, 5.4GB) · 130 meta.json · 0 schema errors.
세부 리포트: `data/reports/` (duplicates, slug-mapping, translation-coverage, phase1-summary)

### 1.1 v1 → JSONL 추출
- `scripts/extract_from_v1.py` 작성
- 입력: `../sanskrit_tibetan_reading_workspace/build/dict.sqlite`
- 출력: `data/jsonl/{dict_name}.jsonl` (135개)
- 스키마: ARCHITECTURE.md §4.1

### 1.2 **Smart Snippets 생성 (FB-1)**
- `scripts/lib/snippet.py` — 문장/정의 경계 감지
- 각 사전 `meta.json.sense_separator` 정규식 존중
- `body.snippet_short` (~120자) + `body.snippet_medium` (~400자)
- 구조화 가능한 사전(Apte/MW/Macdonell)은 `body.senses[]`도 생성

### 1.3 **IAST 표제어 강제 (FB-4)**
- `transliterate.detect_and_convert_to_iast()` 모든 엔트리에 적용
- `headword_iast` 필드 필수 생성
- Sanskrit 엔트리 중 IAST 생성 실패 시 빌드 에러
- Tibetan은 Wylie 유지, Chinese는 원본 유지

### 1.4 **사전 meta.json 작성 (FB-3)**
- v1 `dictnames.js` 135개 → 개별 `data/sources/<slug>/meta.json`
- `priority` 수동 할당:
  - 1=Apte, 2=MW, 3=Macdonell, 4=BHSD, ...
  - v1-feedback.md §FB-3 초기값 테이블 참조
- 타입 체크 + 중복/누락 검증

### 1.5 **번역 Coverage Audit (FB-2)**
- `scripts/audit_translations.py`
- 사전별 `body.ko` 유/무 카운트
- 리포트: `data/reports/translation_coverage.md`
- Phase 2에서 재번역 대상 식별

### 1.6 **역검색 데이터 준비 (FB-8)**
- `scripts/lib/reverse_tokens.py`
  - 영어 토크나이저: lowercase + 알파벳만 + stopword 제거 (학술 gloss 약어
    `m. f. n. cf. esp. pl. sg.` 포함), 위치 가중치, 중복 제거, top 20
  - 한국어 토크나이저: 공백 + 구두점 split, 한자 병기 `법(法)` → `[법, 法]` 둘 다 유지
- `extract_from_v1.py`가 각 엔트리에 `reverse.en[]`, `reverse.ko[]` 자동 채움
- 이미 역방향인 사전 3개 (Apte Eng→Skt, Borooah, MW Eng→Skt):
  `meta.json.direction: "en-to-skt"` 명시, 평소 검색 경로로 편입
- Phase 2에서 `build_reverse_index.py`가 이걸 모아 역인덱스 생성

### 1.7 JSON Schema 검증
- `scripts/verify.py`:
  - schema.json 준수
  - `headword_iast` 유효성 (허용 unicode 범위)
  - priority 중복/gap 체크
  - body 비어있는 엔트리 flag
  - `reverse.en[]`: ASCII 알파벳, 최대 40개
  - `reverse.ko[]`: 한글·한자, 최대 40개
  - `meta.json.exclude_from_search=true` 사전 = declension family 검증
- CI에서 자동 실행 (PR 게이트)

### 1.8 산출물
- 135개 사전 JSONL (~600MB raw incl. reverse tokens, ~120MB zstd)
- 135개 `meta.json` (priority + direction)
- 번역 coverage 리포트
- 검증 스크립트 + 스키마
- `LICENSES.md` (v1에서 복사, v2 배포 정책 추가)

**완료 기준**: 모든 사전이 JSONL + meta.json 완비, `verify.py` 통과, 번역 coverage
리포트 생성, 각 엔트리에 `reverse` 필드 채워짐 (body가 비어있지 않은 경우).

---

## Phase 2: Tier 0 인덱스 + FST + 번역 보완 ✅ (2026-04-22 / 23 완료)

**목표**: 상위 10K 단어를 메모리에서 즉시 검색 + 번역 미완성 엔트리 재번역.

**산출물**: 4 compressed indices (48.9 MB total) · Tier 0 cold load 606-641ms · hit lookup 0.2µs.
Top-10K Ko 번역 POC 100/9,995 (나머지는 subagent spawn_task 또는 batch API).
세부 리포트: `data/reports/phase2-summary.md`, `phase2-benchmark.md`.

### 2.1 빈도 결정
- v1 `body` 안의 cross-reference 카운트
- DCS Sanskrit corpus frequency 활용
- 결과: `data/top10k.txt` (정렬된 headword_norm 리스트)

### 2.2 **번역 배치 재번역 (FB-2)**
- `scripts/translate_batch.py`
- Phase 1.5의 coverage 리포트 기반
- Claude Sonnet 4.5 batch API (50% 비용 절감)
- 원본 언어별 프롬프트 템플릿:
  - DE → KO (Böhtlingk-Roth, Bopp, Cappeller 독, Böhtlingk kürzer, Schmidt)
  - FR → KO (Burnouf, Stchoupak, Renou)
  - LA → KO (Vedic concordance)
  - RU → KO (있으면)
- v1 번역 재사용 (비용 절감)
- 번역 품질 플래그 (길이/반복 휴리스틱)

### 2.3 Tier 0 인덱스 빌드
- `scripts/build_tier0.py`
- 입력: 모든 사전 JSONL + top10k.txt + priority (meta.json)
- 출력: `public/indices/tier0.msgpack.zst` (~30MB)
- **priority 순으로 정렬 저장** — UI에서 re-sort 불필요
- 내용: 각 단어별 사전 등재 (priority ASC) + `snippet_short` + `snippet_medium`

### 2.3 FST 자동완성
- `scripts/build_fst.py`
- Rust `fst` crate를 WASM 컴파일하거나
- 순수 JS FST 라이브러리 사용 (성능 트레이드오프 측정)
- 입력: 1M 고유 headword
- 출력: `public/indices/autocomplete.fst` (~3MB)

### 2.4 **역검색 인덱스 빌드 (FB-8)**
- `scripts/build_reverse_index.py`
- 입력: Phase 1에서 생성된 모든 JSONL의 `reverse.en[]`, `reverse.ko[]`
- 출력:
  - `public/indices/reverse_en.msgpack.zst` (~15MB, 토큰 → [(entry_id, weight)])
  - `public/indices/reverse_ko.msgpack.zst` (~5MB)
- 토큰당 상위 N개 엔트리만 유지 (priority 순)
- 포함될 사전: 명시적 Eng→Skt 역방향 3개는 평소 인덱스로, 나머지는 역인덱스로

### 2.5 벤치마크
- 메모리 로드 시간 측정
- 1000 무작위 쿼리 평균 응답 시간
- 모바일 디바이스 테스트
- 역검색 응답 시간 (Eng/Ko 입력 → 결과)

**완료 기준**:
- Tier 0 로드 <2s on 4G
- 검색 응답 <50ms (캐시 hit)
- 역검색 <100ms (Tier 0 인덱스 hit)

---

## Phase 2.5: Zone B 대응어 데이터 + 빌드 (✅ 완료, 2026-04-29)

**목표**: cross-language equivalents (산-티-한-일-독-한-영) 통합 + Zone B 단일 인덱스 빌드.

### 2.5a 데이터 통합 ✅ (2026-04-26~28 완료)

**17 source dicts · 약 445K rows** (`role=equivalents` 16 + `role=thesaurus` 1):

| 단계 | source | rows | commit |
|---|---|---:|---|
| v1 baseline (메인) | bilex/equiv 7 sources (Mvy·Negi·LCh·84000·Hopkins·NTI·YBh) | 207K | `87b774e` / `790215a` |
| spawn 1 텍스트 발굴 | 5 sources → dedup 후 활성 3 (Karashima·Bodkye·Hopkins-tsed) | 78K → 활성 ~21K | `2e54c8a` / `eaf9727` |
| spawn 2 OCR | 5 sources (Hirakawa·Bonwa·Turfan·Tib-Chn·Amarakośa) | 161K | `cc5afa5` |

**부수 산출물**:
- `docs/schema.json` 확장: 최상위 `role` + `body.equivalents.{skt_iast, tib_wylie, zh, ko, en, ja, de, category, note}`
- `scripts/ocr/lib.py` — Tesseract 5 + pdftoppm + 6 worker 병렬 + 2-column split + 디스크 캐시
- `scripts/lib/tibetan_wylie.py` — Tib unicode → Wylie (char-by-char + syllable-end 'a')
- `scripts/postprocess_{ja_de_fields, tib_chn_wylie}.py`
- 16 사전 `exclude_from_search: true` (dedup, ADR-005 패턴)
- 새 의존성: `pdfplumber`, `pypdf`, `openpyxl`, `python-docx`, `xlrd<2`, `pytesseract`, `pdf2image`, `pillow`

세부 보고:
- `data/reports/equiv-extraction.md` (spawn 1 텍스트)
- `data/reports/equiv-ocr-extraction.md` (spawn 2 OCR)
- `data/reports/equiv-pending-tasks.md` (메인 세션 작업 체크리스트) ⭐

### 2.5b Zone B 빌드 파이프라인 ✅ (commit `519c2ca`, 2026-04-28)

| # | 작업 | 결과 |
|---|---|---|
| 1 ⭐ | `scripts/build_equivalents_index.py` 신규 | 14 active equiv 사전 → `equivalents.msgpack.zst` **13 MB compressed** (예상 30-40 MB의 ⅓) · 110 MB decompressed · 498K keys · 344K unique rows. dedup D10b/(b): cross-source `(skt_iast, tib_wylie, zh)`, 정보량 많은 row keep + sources merge. 키 채널 3 (IAST norm / Wylie norm / 한자) |
| 2 | `scripts/build_meta.py` 동기화 | 변경 없음 — equiv 메타는 build_meta DICTS 외부 영역, 충돌 없음 |
| 3 | `scripts/frequency.py` 검토 | **D10c (c) 채택** — `role in {equivalents, thesaurus}` skip. equiv는 top-10K 빈도 무관 |
| 4 | `scripts/verify.py` 재실행 | **0 errors / 148 dicts / 3.81M entries** (FB-5 dedup-superseded 인정 + spawn1 schema 후처리 후) |
| 5 | `bench/index.html` 갱신 + 측정 | 5 indices cold ~3.5 s · heap +793 MB · equivalents 단독 +109.79 MB → **60 MB target × 1.8 초과**. ADR-009 재검토 → ADR-011 (D) 채택 |

### 2.5c 후속 spawn 머지 ✅ (3 commits, 2026-04-29)

| spawn | commit | 결과 |
|---|---|---|
| Tib_Chn Wylie pyewts | `b686c8d` | 표준 EWTS 변환 (root-letter 식별) — `bstna` → `bstan`. norm mismatch warning 감소, "byang chub" 검색 매칭 회복 |
| Amarakośa verse-level NLP | `dd7013a` | heuristic phase A: 1,119 raw rows → 1,082 verse-level synonym groups (평균 9.9 syn/group) · `body.equivalents.synonyms[]` schema field 추가 · 신규 slug `equiv-amarakoza-synonyms` |
| Hirakawa OCR 노이즈 필터 | `e470356` | conf<60 + len(headword)>8 drop · 16,851 → 16,484 rows (367 drop, 2.18%) |

빌드 영향: dicts 14 → 15, unique rows +410, compressed 13.0 → 13.2 MB.

---

## Phase 3: Svelte UI (Pre-deploy 충실 구현, 2026-04-29~)

**목표**: 배포 전 검색 + 곡용 기능을 충실히 구현. v1 대비 모든 차원 개선.

**구조**: 사용자 review (2026-04-29) 후 sub-phase로 세분화 + Reader/Vocab은 마지막으로 deferred.

### 3.1 Search UI minimal viable ✅ (commit `cf18e57`까지)

scaffold + 5 indices loader + Service Worker + 5 채널 검색 (tier0 / equivalents 3채널 / reverse_en+ko / headwords prefix) + Zone B/C/D + 다크모드 + Sprint 1 quick wins (clickable terms / lang-balanced top-3 / EntryFull modal / Tibetan miss notice / role-filtered tier0).

검증 (Chromium):
- IAST 'dharma' / CJK '般若' / Korean '법' / Devanagari 'धर्म' / HK 'Dharma' / Wylie 'chos' 모든 채널 동작
- query latency 0.00-0.20 µs (ADR-011 D 목표 ×5000배)
- 68 vitest + 79 pytest pass

### 3.2 Search UX polish ✅ (`40802ca` + race fix `07bbbd5`)

- URL ↔ query sync (popstate listener — reactive `$effect`는 race로 typing reset 유발, fix `07bbbd5`)
- Autocomplete dropdown (입력 중, ↑↓/Enter, mouse hover)
- 키보드 단축키 (`/` focus, `Esc` clear/close, `Shift+D` 다크모드)
- LANG pills (전체/산스/티벳/Pāli) + Priority slider (1-100) + visible/total count
- store→URL debounce 120ms
- `?from=entry-id` deep link → EntryFull modal 직접 진입
- vitest 7 추가 (lang.test.ts) → 총 75 pass

### 3.3 Tibetan tier0 확장 ✅ (`d5e91f2`, option A)

별도 `public/indices/tier0-bo.msgpack.zst` (7.1 MB compressed · 162,888 entries · 16.3 avg/hw).
- `scripts/frequency.py --lang-filter bo` 옵션 추가 → `data/reports/top10k_bo.txt`
- 클라이언트 6번째 index + `engine.ts`에서 tier0 + tier0-bo union (entries concat → langBalancedTop이 lang별 top-3 분배)
- **Verify**: `klong chen` 정의 0 → 9 (RY [20] "great expanse...")

### 3.4 Equivalents UX 마감 ✅ (`829286b`)

- `src/lib/search/source-colors.ts`: 18 equiv 사전 → label + OKLCH hue 매핑 (Mvy purple / Negi blue / LCh green / 84K amber / ...)
- `src/lib/components/EquivDetail.svelte`: 클릭 시 modal (10 fields + sources list)
- 50씩 페이지네이션 ("더 보기" / "접기" toggle)

### 3.5 Declension tab ✅ (`9c2b6f7`)

- `/declension` 라우트
- `scripts/build_declension.py`: top-10K Heritage Declension → `public/indices/declension.msgpack.zst` (2.1 MB compressed · 7,438 unique headwords · 39,408 rows)
- `src/lib/declension/parse.ts`: `body.plain` → 8 case × 3 number grid (HEADER_RE + CASE_SPLIT_RE)
- 검색 탭 ↔ 곡용 탭 cross-link tabs
- 7번째 index를 eager bundle에 통합 (lazy fetch는 dev HMR race로 hint stuck → eager가 안정적)

**알려진 issue**: dev mode HMR + URL hydration race로 `?q=` 파라미터가 일부 hot-reload 사이클에서 input에 자동 채워지지 않음. 사용자 직접 typing 시 정상. **Production build (Phase 4) 검증 deferred**.

### 3.5b 통합 검토 (Audit) ✅ Day 1+2+3 (2026-04-30, commits `10b9d93`+`257404f`+`fdf1fee`+Day 3)

Phase 4 배포 직전 데이터 정합성·완전성·UX·코드 품질·배포 readiness 통합 audit.
산출물: `data/reports/audit-2026-04-30/` (22+ md 보고서) · `scripts/audit_*.py` (5 신규).

**Track A (Data Integrity)** — ✅ data layer clean
- Schema errors 0 / id duplicates 0 / missing iast·norm 0 / 3.81M entries
- 189K warnings 모두 카테고리 분류 (대부분 학술 표기·의도된 데이터)
- Cross-source dedup 작동, exclude_from_search filter 0 leaks
- 산출 보고서: A-summary, A-warnings, A-meta-consistency, A-translations, A-indices, A-reverse-precision, A-zh-contamination

**Track B (Data Completeness)** — ⚠️ 번역 품질이 핵심 결함
- Tibetan top-10K coverage 94% sentinel hit
- Long-tail 98.4% (Phase 5 D1 Edge API 가치 확인)
- **DE/FR/LA `body.ko` 1.87/4.0** (498 sample) — v1은 per-token substitution, 실제 한국어 5-7% only
- 산출 보고서: B-summary, B-coverage, B-eu-quality

**Track D (Code Quality + Build)** — ✅ 코드 견고
- TypeScript strict 0/0 / 255 files
- Production build 성공 ~50 kB gzipped client critical-path
- Svelte 5 runes 0 P0 / 1 P1 (closure pattern) / 2 P2
- vitest 75 + pytest 79 pass / <1s
- 산출 보고서: D-summary, D-build, D-svelte5, D-tests, D-buildperf

**Track C+D Day 3 결과** — ✅ 자동 측정 완료, 사용자 시연만 다음 세션
- D5 Latency: Map.get 모두 < 1µs ✅, cold load 2.35s (Python)
- D6 Service Worker: v3 cache, 7 indices precache, scope-limited ✅
- D9 Declension HMR race: production code path 분석 — race 부재 ✅
- Lighthouse (production preview): Performance 45 (측정 artifact, splash + SW cold), **Accessibility 95 ✅ (목표 달성)**, Best Practices 100, SEO 82
- Sentinel 50 queries draft + 사용자 #15 정정 (mahā)
- 사용자 시연 가이드 작성 (`audit-C-demo-guide.md`)

**Track E Production Readiness** — ⚠️ 2 deploy gates
- E1 adapter-static export ✅
- E2 `_headers` 미작성 — P1 (Phase 4 entry)
- **E3 `tier0.msgpack.zst` 28.78 MB > Cloudflare 25 MB 한계 — P0 새로 (Phase 4 deploy blocker)**
- **E4 LICENSES.md 47 dicts 미명시 (148-101) — P1 새로**
- E5 피드백 루프 — P2 deferred

**P0/P1 backlog 도출 → Phase 3.6 + Phase 4 확장**

### 3.6 Polish + a11y + Audit P0/P1 fixes ⏭️ (즉시 다음, ~3-5일 확장)

**Audit P0** (must fix before deploy):
- **P0-1** Reverse search UI raw entry_id → `reverse_meta.msgpack.zst` 신규 인덱스 + 렌더링 갱신
- **P0-2** DE/FR/LA `body.ko` re-translation — $225 batch (priority pwg→pwk→cappeller-german→schmidt-nachtrage→stchoupak→burnouf→grassmann-vedic→bopp-latin)
- **P0-3** [NEW Day 3] tier0.msgpack.zst 28.78 MB > Cloudflare 25 MB. zstd `-22 --ultra` 재압축 또는 R2/Workers 이관

**Audit P1**:
- **P1-1** `build_reverse_index.py` headword salience boost (target ≥12/15 EN strict)
- **P1-2** Korean coverage push for English-source dicts ($30 batch, top 50K)
- **P1-3** `extract_equiv_yogacarabhumi.py` zh column-mapping fix → equivalents 재빌드
- **P1-D2-1** `$effect` debounce closure refactor (+page.svelte, declension/+page.svelte)
- **P1-D8-1** `parse.ts` unit tests (~30 min)
- **P1-D8-2** `loader.ts` unit tests (~1h)
- **P1-E2** [NEW Day 3] `static/_headers` 작성 (CSP + Cache-Control + Service-Worker-Allowed)
- **P1-E4** [NEW Day 3] LICENSES.md 47 dicts 보충

**Original 3.6 polish**:
- 모바일 반응형 (≤768px) — devtools 시뮬 (audit-C-demo-guide.md)
- Lighthouse Performance fix — 현재 45 (측정 artifact, splash + SW cold load main thread block). zstd Web Worker 이전 시 80+ 예상
- Accessibility ≥ 95 ✅ (Day 3 production preview 측정 완료)
- 키보드 navigation 완성 (tab order, focus rings)
- Loading state 고도화 (per-channel progress)

**Phase 3.6 완료 기준**:
- v1 대비 모든 검색 채널 + 곡용 탭 + 역검색이 의미 있게 동작 (P0-1, P0-2, P1-1, P1-2 fix 후)
- query latency <1ms 유지 (ADR-011 D)
- Lighthouse Performance ≥ 80 (zstd Worker 후 80+, deployed CDN으로 90+)
- Accessibility ≥ 95 ✅
- 모바일 반응형 정상
- vitest ≥ 80 cases (parse.ts + loader.ts 테스트 추가)
- Sentinel 50 queries baseline + after-fix 비교 (사용자 시연)

---

## Phase 3.5: Declension 탭 (1주)

**목표**: Heritage declension 사전을 전용 탭으로 분리. 검색 오염 제거 + 문법 참조 도구.

### 3.5.1 데이터 빌드
- `scripts/build_declension.py`
- 입력: `data/jsonl/decl-*.jsonl` (Phase 1에서 추출됨)
- BeautifulSoup으로 Apple .dictionary HTML 표 파싱
- 출력:
  - `public/declension/paradigms.json` (~40 클래스)
  - `public/declension/words.json` (~3000 단어 → 클래스 매핑)
  - `public/declension/generated.json.zst` (pre-rendered 표)
- 24-cell 완전성 검증

### 3.5.2 `/declension` 라우트 (Svelte)
- `src/routes/declension/+page.svelte`
- 단어 입력창 (검색 탭과 별도 state)
- URL 동기화 (`/declension?q=deva&gender=m`)

### 3.5.3 컴포넌트
- `<DeclensionForm>`: 단어 + 성별 선택
- `<DeclensionTable>`: 24-cell 테이블 렌더
- `<ParadigmInfo>`: 클래스 + 예시 단어 표시
- `<SandhiToggle>`: 표준/연성 전환

### 3.5.4 검색 탭 연결
- 검색 결과에 "곡용 보기 →" 링크 추가
- Declension 셀 클릭 → 검색 탭 이동 (해당 form)

### 3.5.5 빌드 파이프라인 분리 확인
- `build_tier0.py` / `build_fst.py` / D1 import가 `exclude_from_search` 존중
- `verify.py`에 "declension 사전이 검색 인덱스에 없음" 단정 추가

**완료 기준**:
- ~3000 단어 즉시 곡용표 조회
- 검색 결과에 declension 사전 엔트리 절대 없음
- Phase 3 다크모드와 호환

상세: `docs/declension-tab.md`

---

## Phase 4: 배포 + 운영 (1주)

**목표**: 프로덕션 배포, 사용자 점진 이전.

### 4.1 배포
- Cloudflare Pages 연결
- 도메인 (선택): `workspace.haMsa.io` 또는 `skt-tib.pages.dev`
- v1과 병렬 운영 (별도 도메인 또는 `/v2`)

### 4.2 CI/CD
- GitHub Actions:
  - PR: 빌드 + 테스트 + Lighthouse + verify
  - main push: 자동 deploy to Pages
  - 데이터 변경 시 인덱스 재빌드 + cache bust

### 4.3 모니터링
- Cloudflare Analytics 연결
- Sentry 셋업
- Web Vitals 대시보드

### 4.4 문서
- `docs/USER_GUIDE.md`: 사용자 가이드
- `docs/CONTRIBUTING.md`: 개발자 가이드
- `docs/DATA.md`: 데이터 출처 + 라이선스

### 4.5 사용자 이전
- v1 홈페이지에 v2 배너 추가
- 기존 검색 URL → v2 redirect (선택)
- 한 달 후 v1 deprecation 공지

**완료 기준**: v2 일일 사용자가 v1 추월.

---

## Phase 5: Edge API (Tier 2) (1주)

**목표**: 희귀 단어 검색을 위한 Cloudflare Workers + D1.

### 5.1 D1 셋업
- Wrangler CLI 설치
- D1 데이터베이스 생성
- 스키마 (entries, dictionaries, fts)
- JSONL → SQL import 스크립트

### 5.2 Worker API
- `GET /api/search?q=...&limit=...`
- `GET /api/entry/:id`
- Rate limiting (분당 100 req)
- CORS 설정

### 5.3 클라이언트 통합
- Tier 0/1 miss 시 Tier 2 호출
- 응답 타임아웃 처리
- 에러 UX (오프라인 시 안내)

**완료 기준**: 모든 사전 단어 검색 가능 (Tier 0/1/2 합쳐서).

---

## Phase 6: 고급 기능 (이후)

v2가 안정화된 후 검토:
- Full-text body search (Tier 3)
- 학습 카드 (vocab) — v1 기능 포팅
- 독해 모드 — v1 기능 포팅
- 사용자 계정 (선택, 클라우드 동기화)
- 사전 추가 contribution 워크플로우 (PR 기반)
- API 공개 (다른 도구 연동)

---

## 마일스톤 요약

| Week | Phase | 산출물 |
|------|-------|--------|
| 0    | 0     | 뼈대 + 설계 + 피드백 반영 ✅ |
| 1    | 1     | 135개 사전 JSONL + meta.json + verify |
| 2-3  | 2     | Tier 0 + FST + 번역 batch |
| 4-5  | 3     | Svelte UI (검색 + **다크모드**) |
| 6    | 3.5   | **Declension 탭** |
| 7    | 4     | 배포 + 모니터링 |
| 8    | 5     | Edge API (희귀 단어) |
| 9+   | 6     | Reader + Vocab 포팅 |

**7주 후**: v2가 v1보다 빠르고 안정적 + Declension 탭 + 다크모드. 사용자 자연 이전.

---

## 위험 요소 + 완화

| 위험 | 영향 | 완화 |
|------|------|------|
| Cloudflare 무료 한도 초과 | API 다운 | Tier 0/1로 대부분 처리, Tier 2는 backup |
| Svelte 5 학습 곡선 | 일정 지연 | Phase 3에 2주 할당, 필요 시 Vue/Solid 검토 |
| FST WASM 빌드 복잡 | 일정 지연 | 순수 JS fallback 준비 |
| OPFS 브라우저 호환성 | 일부 사용자 캐시 안 됨 | localStorage fallback (한도 작음) |
| 데이터 품질 회귀 | 검색 결과 누락 | verify.py CI 게이트 필수 |
| v1 사용자 저항 | 이전 거부 | v1 무중단 유지, 점진 이전 |

---

## 의사결정 일지

이 섹션에 주요 기술 선택의 이유를 기록 (ADR-lite).

### ADR-001: Svelte 5 (vs React/Vue/Solid)
- **결정**: Svelte 5
- **이유**: 번들 크기 (학술 도구는 가벼워야 함), runes의 명료한 reactivity
- **대안 검토**: React (생태계 크지만 무거움), Solid (가볍지만 생태계 작음), Vanilla (상태 관리 부담)
- **재검토 시점**: Phase 3 시작 전

### ADR-002: Cloudflare (vs Vercel/AWS)
- **결정**: Cloudflare Pages + Workers + D1
- **이유**: 통합된 무료 티어, 글로벌 엣지, 학술용에 충분
- **대안 검토**: Vercel (좋지만 D1 같은 엣지 SQL 없음), AWS (관리 부담)
- **재검토 시점**: Phase 4 배포 전

### ADR-003: JSONL (vs Parquet/Arrow)
- **결정**: JSONL + Zstandard 압축
- **이유**: Git diff 가능, 외부 도구 친화, 학술 corpus 표준
- **대안 검토**: Parquet (압축 좋지만 binary, diff 안 됨), Arrow (메모리 좋지만 학습 부담)
- **재검토 시점**: Phase 1 완료 후 크기 측정

### ADR-004: 정규화 함수 단일 소스
- **결정**: Python `transliterate.py` + JS `translit.js` 1:1 동기화 + verify CI
- **이유**: v1에서 두 함수 불일치로 데이터 오염 발생함
- **대안 검토**: Pyodide로 Python을 브라우저에서 직접 실행 (무거움), Rust 단일 구현 후 양쪽에서 사용 (복잡)
- **재검토 시점**: Phase 2 완료 후 실측

### ADR-005: Declension을 검색에서 분리 (FB-5)
- **결정**: Heritage declension 사전 ~20개를 `exclude_from_search: true` 플래그로
  검색 인덱스에서 제외, `/declension` 전용 탭에서 처리
- **이유**: 검색 결과 오염 + 곡용표는 본질적으로 다른 UI 포맷 (표 vs 정의문) 요구
- **대안 검토**:
  - 유지 (현상태) — 오염 지속
  - 사전 필터 UI 추가 — 사용자 부담
  - 완전 삭제 — 데이터 손실
- **재검토 시점**: Phase 3.5 완료 후 사용성 피드백

### ADR-006: 다크모드 (FB-6)
- **결정**: `light` / `dark` / `auto` 3-state, OKLCH 색 공간, View Transitions API
- **이유**: 학자 장시간 사용 환경 배려 + 지각적 명도 일관성 (OKLCH)
- **대안 검토**:
  - 2-state (light/dark만) — 시스템 선호 무시
  - HSL — 명도 비일관 (녹색 vs 파란색 같은 L 값이 달라 보임)
- **재검토 시점**: Phase 3 완료 후

### ADR-007: 프로젝트 이름 (FB-7)
- **결정**: **Sanskrit-Tibetan Workspace**
- **이유**: 명확, 검색 가능, v1과 연결성, 비전문가 친화
- **대안 검토**:
  - `Nighaṇṭu` (निघण्टु) — 학술적이지만 대중 친숙도 낮음
  - `Kosha` (कोश) — 대중 친숙도 중간
  - `Vidya`, `Shabda` 등 — 너무 광범위한 의미
- **재검토 시점**: 공개 배포 직전 여론 검토

### ADR-008: 역검색 (FB-8) — inline `reverse` 필드 + 별도 역인덱스
- **결정**: Phase 1에서 각 JSONL 엔트리에 `reverse.en[]` + `reverse.ko[]`를 inline으로
  채우고, Phase 2에서 `build_reverse_index.py`가 모아 별도 msgpack 역인덱스 생성.
  명시적 Eng→Skt 사전 3개는 `direction: "en-to-skt"`로 표기해 정상 검색 경로로 편입.
  티벳어 역검색은 body 토큰 추출에 전적으로 의존.
- **이유**:
  - v1에 Eng→Bo 사전이 없어 티벳어 역검색은 body 추출이 유일한 경로
  - inline 저장: JSONL single source of truth 유지, 재빌드 시 데이터 일관성 보장
  - 영어·한국어 토크나이저 Phase 1 완비 → Phase 2 인덱스는 순수 조합 작업
- **대안 검토**:
  - *전문 검색 (FTS5)만으로*: 노이즈 크고, Tier 0 캐시 불가 → 사용자 체감 느림
  - *별도 역 JSONL 파일*: inline vs separate 논쟁 — inline이 재생성 편리
  - *규칙 기반 추출 없이 raw body 저장*: 쿼리 시 토크나이징 부담, 브라우저에서 느림
- **재검토 시점**: Phase 3 UI 완성 후 사용자 피드백 수집 (특히 한국어 조사 처리)

### ADR-009: 사전 Pareto + `role` 필드 + Tier 0 사전 shard

> **SUPERSEDED 2026-04-29 by ADR-011 (D)** — Phase 2.5b 종결 후 측정 (Chromium
> bench/index.html): equivalents 단독 heap +109.79 MB, 5 indices 합 +793 MB.
> 사전 shard 분할 시 lazy fetch latency가 발생하여 사용자가 정한 "검색 query
> latency 최우선" 원칙과 충돌. 데스크톱 우선 + Service Worker precache 채택.
> 아래 본문은 historical record로 유지. `role` 필드 도입(1번 항목)과 equivalents
> 별도 인덱스(3번 항목)는 ADR-011에서도 그대로 유지됨. 2번 (Tier 0 shard)과
> 4번 (lang별 top-3 prefetch)만 폐기.

- **결정**:
  1. `meta.json.role` + entry 최상위 `role` 필드 도입 — `definition` / `equivalents` / `thesaurus` / `declension`
  2. Tier 0를 사전별 shard로 분할: `tier0-core` (언어별 top-3 정의 사전) + `tier0-rest/{slug}` (priority≥4 lazy)
  3. `role=equivalents` + `role=thesaurus` 사전은 별도 인덱스 `equivalents.msgpack.zst` (Zone B 전용)
  4. 산스크리트 top-3 = Apte/MW/BHSD, 티벳 top-3 = RY/Hopkins/84000 (입력 문자 감지로 prefetch 결정)
- **이유**:
  - 2026-04-26 cold load 측정 (`bench/index.html`): tier0 단독 JS heap **428 MB** 폭증 → 모바일 OOM 위험
  - 학자 사용 패턴 — 한 검색에서 진짜 정독하는 사전은 언어별 top-3 (Pareto 분포)
  - 추정 효과: 압축 28.6 MB → ~5 MB, JS heap 428 MB → ~60 MB
  - v1의 "사전 균등 처리" 결함 (FB-3에서 priority 정렬만 했지만 데이터 레이어는 그대로) 데이터 레이어에서 해결
- **대안 검토**:
  - hot/warm 분할 (top-1K vs 1K-10K) — *headword* Pareto만 다룸. 사전 Pareto에 둔감. 효과 적음.
  - 클라이언트 sql.js (IndexedDB/OPFS) — ceiling 가장 높지만 모바일 hydration 미지수 + 1-2주 작업
  - 변경 없음 (v1처럼) — 모바일에서 즉사 (heap 428 MB)
- **재검토 시점**: spawn_task의 `Sanskrit_Tibetan_Reading_Tools` 발굴 결과 통합 후 + Phase 3 LCP 재측정. Zone B 비대 시 `equivalents.msgpack.zst`도 source별 shard 검토.
- **진행 (2026-04-28)**:
  - spawn 1 (`crazy-yalow-912f7c`) — 텍스트/xlsx/docx 발굴 5 sources · 77,815 rows · commit `2e54c8a`.
  - spawn 2 (`compassionate-rosalind-d663ca`) — 스캔 PDF OCR 5 sources · 160,874 rows · commits `e25c39a`/`16fec77` (+ 28 incremental). Hirakawa/Bonwa/Turfan/Tib_Chn/Amarakośa 모두 완료. schema 확장 (body.equivalents.{ja, de}) + Tib_Chn Wylie 자동변환 포함.
  - **메인 세션 잔여**: `scripts/build_equivalents_index.py` 신규 + `equivalents.msgpack.zst` 빌드 → `data/reports/equiv-pending-tasks.md` 참조.
  - 누적 약 445K rows · 17 source dicts (role=equivalents 16 + role=thesaurus 1).

### ADR-010: Zone 재설계 — Zone A 제거 + 순서 (Header → B → C → D)
- **결정**:
  1. v1의 Zone A 통째 제거 — 1줄 header strip("검색어 · 정의 카운트 · 대응어 카운트 · 매칭 모드")로 대체
  2. Zone 순서: header strip → Zone B (equivalents) → Zone C (정의 top-3, prefetched) → Zone D (추가 사전 lazy)
  3. v1의 A → B → D → C 패턴 폐기. 검색 결과 정의가 부분→전체가 아닌 즉시→토글 패턴.
- **이유**:
  - v1 Zone A는 두 역할 — (1) bilex 즉시 도착 + body lazy load의 *buffer*, (2) 사전 *navigation aid* (`wireZoneALinks`).
    ADR-009의 top-3 prefetch로 (1) buffer 역할 사라짐. (2) navigation은 한 화면에 3 사전 다 보여서 가치 약함.
  - v1이 D를 C 위에 둔 이유는 lazy body load. v2는 즉시 prefetch라 정합성 잃음.
  - 학술 사용 패턴 — 검색의 본질이 "대응어 + 정의" 첫 시각, equivalents는 dense reference (한 줄당 4언어).
- **대안 검토**:
  - Zone A 유지 — buffer 역할 없는데 화면 점유. redundant.
  - Zone C 위 B — 검색의 primary가 정의이므로 합리적. 다만 v1 사용자(=현 사용자)가 B 위 패턴을 선호한 패턴 + 학자 dense reference 가치 무시.
  - 단일 zone (모두 Zone C 안에 평탄화) — 시각적 분리 잃음, equivalents가 정의 사이 끼어 v1과 같은 결과 오염 (FB-5 패턴 재발).
- **재검토 시점**: Phase 3 UX 테스트 (특히 모바일 좁은 화면). Zone B 비대 시 (예: 단어당 1000+ 매핑) collapse 정책 + source 그룹 토글.

### ADR-011: All-eager 인덱스 + Service Worker precache (supersedes ADR-009 사전 shard)
- **결정**:
  1. 모든 5 indices (tier0 + equivalents + reverse_en + reverse_ko + headwords)를 page load 시 eager fetch + decompress(fzstd) + decode(msgpack) → JS heap에 resident.
  2. Service Worker가 5 indices를 precache (`stw-indices-v1` cache) → 두 번째 방문은 즉시 cold start.
  3. tier0/equivalents 모두 단일 파일 유지 — 사전 shard 분할 안 함. 클라이언트가 priority별 정렬/필터.
  4. ADR-009의 (1) `role` 필드 + (3) equivalents 별도 인덱스는 그대로 유효. (2) Tier 0 shard와 (4) lang별 top-3 prefetch만 폐기.
  5. 모바일은 graceful degradation — 데스크톱이 주요 form factor. 모바일 사용 비율 측정 후 Phase 4+에 UA-detect lazy 옵션 검토.
- **이유**:
  - 사용자 우선순위(2026-04-29 명시): 검색 query latency가 최우선. 데스크톱 주요.
  - 측정 (2026-04-28, Chromium `bench/index.html`): tier0 +427 MB · equivalents +109 MB · 5 indices 합 +793 MB heap. 모바일 60 MB target 초과지만 데스크톱은 충분.
  - 사전 shard 시 일부 query에 lazy fetch + decode latency 50-1000 ms 추가. in-memory hash lookup만이 <1 ms 보장.
  - SW precache로 cold start 비용을 1회로 amortize (subsequent visit 즉시 ~50ms).
- **대안 검토**:
  - **(B+A) priority-tier eager + sharded source lazy** — 모바일 친화이지만 일부 query에 lazy fetch latency. 사용자 기준(검색 latency 최우선)과 충돌.
  - **(C) language-channel shard** (skt/tib/zh) — channel별 fetch latency, cross-language search 시 multiple fetch.
  - **All-eager + WASM FST** — 진짜 ms 단위 가능, 그러나 구현 복잡도 큼. Phase 3에서는 vanilla msgpack 우선.
- **수치**:
  - cold load (5 indices, sequential): ~3.5 s (LAN), 4G 환경은 별도 측정 필요
  - SW cached subsequent visit: ~50 ms (browser cache hit)
  - query latency: <1 ms (Map.get, 모든 채널)
  - heap: ~793 MB total (데스크톱 OK, 모바일 한계)
- **재검토 시점**: Phase 3 사용자 피드백. 모바일 사용 비율이 예상보다 높으면 graceful degradation 강화 (UA-detect lazy shard fallback).
- **5 default 결정 (2026-04-29)**:
  1. CSS 전략: Vanilla CSS modules (Tailwind 안 함, 학술 도구 단순성)
  2. 번역 머지: `build_tier0.py --translations data/translations.jsonl` 재실행 → JSONL `body.ko` join
  3. SW precache 범위: 5 indices 모두 (~64 MB compressed)
  4. 인덱스 포맷: msgpack + zstd 그대로
  5. decode 위치: 메인스레드 (jank 측정 후 worker 옵션)
