# Nighaṇṭu — Roadmap

목표: 6주 안에 v1 사용자가 자연스럽게 v2로 넘어올 수 있는 상태 도달.
원칙: **각 Phase는 독립적으로 가치 있고, v1은 무중단 유지**.

---

## Phase 0: 준비 (이번 세션 ✅)
- [x] 프로젝트 디렉터리 + 뼈대
- [x] README, ARCHITECTURE, ROADMAP 작성
- [x] 명명 결정 (nighantu = 산스크리트 "용어집")
- [x] 기술 스택 결정 (Svelte 5 + Vite + Cloudflare)

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
- snippet 50/200 미리 계산 (런타임 SUBSTR 제거)

### 1.2 정규화 통합
- v1의 `transliterate.py` 재사용 (이미 IAST/HK/Devanagari 처리)
- 정규화 결과를 JSONL에 미리 저장 → 런타임 부담 0

### 1.3 JSON Schema 검증
- `scripts/verify.py`: 모든 JSONL이 schema.json 만족 확인
- CI에서 자동 실행 (PR 게이트)

### 1.4 산출물
- 135개 사전 JSONL (~500MB raw, ~100MB zstd)
- 검증 스크립트 + 스키마

**완료 기준**: 모든 사전이 JSONL이고 verify.py 통과.

---

## Phase 2: Tier 0 인덱스 + FST (1주)

**목표**: 상위 10K 단어를 메모리에서 즉시 검색.

### 2.1 빈도 결정
- v1 `body` 안의 cross-reference 카운트
- DCS Sanskrit corpus frequency 활용
- 결과: `data/top10k.txt` (정렬된 headword_norm 리스트)

### 2.2 Tier 0 인덱스 빌드
- `scripts/build_tier0.py`
- 입력: 모든 사전 JSONL + top10k.txt
- 출력: `public/indices/tier0.msgpack.zst` (~30MB)
- 형식: msgpack (JSON보다 작고 빠름)
- 내용: 각 단어별 모든 사전 등재 + 50자/200자 snippet

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
- `<SearchBar>`: 자동완성 (FST), 다국어 IME 호환
- `<ResultList>`: 4-zone 레이아웃 (A/B/D/C)
- `<DictBlock>`: 사전별 엔트리 표시
- `<EntryFull>`: 본문 전체 보기

### 3.3 상태 관리
- nanostores: `searchTerm`, `results`, `loadingState`
- URL ↔ store 양방향 동기화
- 페이지 새로고침 시 완전 복원

### 3.4 Service Worker
- Cache-first for indices
- Stale-while-revalidate for API
- OPFS 캐시 (1GB까지)

### 3.5 디자인
- Light/dark mode
- 모바일 우선 반응형
- 한자 폰트, IAST 폰트, 티벳 폰트 적절히 로딩

**완료 기준**:
- v1과 동일한 검색 결과
- 첫 로드 후 모든 검색 <100ms (Tier 0 hit)
- Lighthouse Performance ≥ 90

---

## Phase 4: 배포 + 운영 (1주)

**목표**: 프로덕션 배포, 사용자 점진 이전.

### 4.1 배포
- Cloudflare Pages 연결
- 도메인 (선택): `nighantu.haMsa.io` 또는 비슷한
- v1과 병렬 운영 (`/v2` 또는 별도 도메인)

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
| 0    | 0     | 뼈대 + 설계 (이번 세션) |
| 1    | 1     | 135개 사전 JSONL + verify |
| 2    | 2     | Tier 0 + FST |
| 3-4  | 3     | Svelte UI 최소 |
| 5    | 4     | 배포 + 모니터링 |
| 6    | 5     | Edge API (희귀 단어) |
| 7+   | 6     | 고급 기능 |

**6주 후**: v2가 v1보다 빠르고 안정적. 사용자 자연 이전.

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
