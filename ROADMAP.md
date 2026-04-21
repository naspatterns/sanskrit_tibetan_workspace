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

## Phase 1: 데이터 추출 + 검증 (1주)

**목표**: v1의 dict.sqlite → JSONL 변환 + 데이터 품질 검증.
v1 데이터를 그대로 활용 (사전별 재파싱 안 함). 빠른 시작.

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

### 1.6 JSON Schema 검증
- `scripts/verify.py`:
  - schema.json 준수
  - `headword_iast` 유효성 (허용 unicode 범위)
  - priority 중복/gap 체크
  - body 비어있는 엔트리 flag
- CI에서 자동 실행 (PR 게이트)

### 1.7 산출물
- 135개 사전 JSONL (~500MB raw, ~100MB zstd)
- 135개 `meta.json` (priority 부여)
- 번역 coverage 리포트
- 검증 스크립트 + 스키마

**완료 기준**: 모든 사전이 JSONL + meta.json 완비, `verify.py` 통과, 번역 coverage 리포트 생성.

---

## Phase 2: Tier 0 인덱스 + FST + 번역 보완 (1-2주)

**목표**: 상위 10K 단어를 메모리에서 즉시 검색 + 번역 미완성 엔트리 재번역.

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

### 2.4 벤치마크
- 메모리 로드 시간 측정
- 1000 무작위 쿼리 평균 응답 시간
- 모바일 디바이스 테스트

**완료 기준**:
- Tier 0 로드 <2s on 4G
- 검색 응답 <50ms (캐시 hit)

---

## Phase 3: Svelte UI 최소 버전 (2주)

**목표**: v1의 검색 모드 기능을 Svelte로 구현. 본격 사용 가능.

### 3.1 프로젝트 셋업
- Vite + Svelte 5
- TypeScript
- Vitest 단위 테스트
- Playwright E2E

### 3.2 핵심 컴포넌트
- `<SearchBar>`: 자동완성 (FST), HK/IAST/Devanagari 입력 호환
- `<ResultList>`: 4-zone 레이아웃 (A/B/D/C), **priority 순 정렬**
- `<DictBlock>`: 사전별 엔트리
  - 표제어는 **항상 `headword_iast`** 표시 (FB-4)
  - 원본과 IAST가 다를 때만 "원본: ..." 작게 표시
  - `body.ko` 없으면 "원문만" 배지 (FB-2)
- `<ZoneA>`: `snippet_short` 기본 → "더 보기" 클릭 시 `snippet_medium` (FB-1)
- `<EntryFull>`: 본문 전체 보기 + "원본 보기" 토글

### 3.3 상태 관리
- nanostores: `searchTerm`, `results`, `loadingState`
- URL ↔ store 양방향 동기화
- 페이지 새로고침 시 완전 복원

### 3.4 Service Worker
- Cache-first for indices
- Stale-while-revalidate for API
- OPFS 캐시 (1GB까지)

### 3.5 **다크모드 (FB-6)**
- `src/styles/theme.css`: OKLCH 기반 CSS 변수
  - 라이트: `--bg: oklch(0.99 0 0)`, `--fg: oklch(0.18 0 0)` 등
  - 다크: `--bg: oklch(0.18 0 0)`, `--fg: oklch(0.92 0 0)` 등
  - 대비비 WCAG AAA (본문) / AA (보조)
- `src/lib/stores/theme.ts`: Svelte store + localStorage 동기화
  - `$state<'light' | 'dark' | 'auto'>`
  - `prefers-color-scheme` media query 감지
- `<ThemeToggle>`: 헤더 우상단 3-state 토글 (☀️/🌙/🔄)
- 키보드 단축키 `Shift+D`
- View Transitions API로 부드러운 전환
- 산스크리트/티벳 diacritic 가독성 테스트 (모바일 + 다크)

### 3.6 디자인 마무리
- 모바일 우선 반응형
- 폰트 로딩: Noto Sans Devanagari/Tibetan system fallback, IAST는 Latin 기본 폰트
- 한자 system fonts

### 3.7 탭 네비게이션
- 헤더에 3-탭 (검색 · 곡용 · 독해)
- 독해 탭은 Phase 3에선 "Coming soon" placeholder
- 검색/곡용 탭 간 쉬운 이동 (단어 공유)

**완료 기준**:
- v1과 동일한 검색 결과 (검색 탭)
- 첫 로드 후 모든 검색 <100ms (Tier 0 hit)
- 다크모드 토글 작동, localStorage 유지
- Lighthouse Performance ≥ 90

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
