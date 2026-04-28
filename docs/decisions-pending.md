# Decisions Pending — Sanskrit-Tibetan Workspace v2

다음 세션 시작 전에 사용자가 확정해야 할 결정들. ARCHITECTURE.md / ROADMAP.md
의 ADR 섹션 보강용.

---

## 즉시 결정 필요 (Phase 1 시작 전)

### D1. 모노레포 vs 단일 패키지
- **A**: 단일 패키지 (현재 구조). 단순.
- **B**: pnpm workspace 모노레포 (`apps/web`, `packages/data`, `packages/search`).
  공유 타입 명료, 향후 npm 배포 가능.
- **추천**: A로 시작, 필요 시 B 전환. 학술 도구는 모노레포 부담 큼.

### D2. SvelteKit vs Vite + Svelte (SPA only)
- **A**: SvelteKit. 라우팅 + SSR + adapter-cloudflare 통합.
- **B**: Vite + Svelte SPA. 정적 사이트, 단순.
- **추천**: A. SvelteKit의 prerender + cloudflare-pages adapter가 깔끔.

### D3. 한국어 번역 어떻게? **[FB-2로 확정]**
- v1의 DE/FR/LA 번역이 **불완전**하다는 사용자 피드백 있음 (FB-2)
- **결정: A + B 혼합** — v1 번역 재사용 + 빈 것만 신규 번역
  - 이미 있는 `body.ko`는 재사용 (비용 0)
  - 빈 것은 Claude Sonnet 4.5 batch API로 재번역 (50% 할인)
  - 러시아어 자료 있으면 신규 추가
- 자세한 절차: `docs/v1-feedback.md` §FB-2
- coverage 목표: 95%+

---

## Phase 2 결정

### D4. FST 구현
- **A**: `fst` Rust crate → WASM. 작고 빠름. 빌드 설정 복잡.
- **B**: 순수 JS FST 라이브러리 (`mnemonist/fst`). 큰 번들, 단순.
- **C**: v1처럼 정렬 배열 + binary search. 이미 검증됨, 17MB.
- **추천**: B로 시작 → 측정 후 A 검토.

### D5. msgpack vs JSON for Tier 0
- **A**: msgpack + zstd. 30% 작음, 파싱 빠름. 디버깅 어려움.
- **B**: JSON + zstd. v1과 동일. 디버깅 쉬움.
- **추천**: B로 시작. Phase 2 측정 후 msgpack 전환 검토.

---

## Phase 3 결정

### D6. CSS 전략
- **A**: Vanilla CSS + CSS modules (Svelte 기본).
- **B**: Tailwind v4. 빠른 프로토타이핑.
- **C**: UnoCSS. 가벼움.
- **추천**: A. 학술 사이트는 디자인 시스템 단순. Tailwind는 과잉.

### D7. 폰트 전략
- 산스크리트 IAST: Latin diacritics 필요한 모든 폰트
- 데바나가리: Noto Sans Devanagari (system fallback 가능)
- 티벳: Noto Sans Tibetan or Jomolhari
- 한자: System fonts (Noto Sans CJK fallback)
- **결정**: self-host vs Google Fonts vs system?
- **추천**: System first, self-host fallback. 라이선스 + GDPR 안전.

---

## Phase 4 결정

### D8. 도메인
- **A**: `workspace.haMsa.io` 또는 `skt-tib.haMsa.io` (서브도메인)
- **B**: `sanskrit-tibetan.org` 또는 비슷한 신규 도메인
- **C**: Cloudflare Pages 기본 (`*.pages.dev`)
- **추천**: C로 시작 (무료), 안정화 후 B.

### D9. v1 deprecation 일정
- **A**: 1개월 후 v1 종료
- **B**: v1 영구 유지 (read-only)
- **C**: v1을 v2로 redirect
- **추천**: B. 학술 자료는 stable URL 가치 큼. 단, 새 검색은 v2 권장.

---

## Phase 5 결정

### D10. Edge SQL: D1 vs Turso vs PlanetScale
- **A**: Cloudflare D1. Workers와 통합 매끄러움. 글로벌 복제 자동.
- **B**: Turso. SQLite 기반, edge replicas. 개발 경험 좋음.
- **C**: PlanetScale (MySQL). FTS는 좀 어려움.
- **추천**: A. CF 무료 티어로 충분.

---

## 데이터 결정

### D10b. Zone B (equivalents) 통합 — **메인 세션 작업**

본 spawn (`compassionate-rosalind-d663ca`)이 OCR 5 sources · 160,874 rows 완료
(Hirakawa·Bonwa·Turfan·Tib_Chn·Amarakośa). schema 확장 (`body.equivalents.{ja, de}`)
+ Tib_Chn Wylie 자동변환 포함.

**메인 세션 즉시 작업** (체크리스트 → [`data/reports/equiv-pending-tasks.md`](../data/reports/equiv-pending-tasks.md)):
1. `scripts/build_equivalents_index.py` 신규 — 17 dict (v1 baseline 7 + spawn1 5 + spawn2 5) → `equivalents.msgpack.zst`
2. `scripts/build_meta.py` — 5 새 슬러그 등록 또는 직접 작성 meta 보존
3. `scripts/frequency.py` — equiv role rows priority weighting 검토
4. verify.py 재실행 (현재 0 errors / 160,874 entries)

**선택적 후속** (우선순위 낮음):
- Tib_Chn Wylie 정확도 향상 (현 root-letter 미식별 → pyewts/botok)
- Hirakawa OCR 노이즈 페이지 필터 (~109 rows)
- Amarakośa verse-level NLP (산스 thesaurus 동의어 group 구조 추출)
- 불광사전워.pdf 2GB OCR — Vision API 별도 spawn 권장

### D11. 빈도 데이터 출처
top-10K 단어 결정 기준:
- v1 사용 로그 (있다면)
- DCS Sanskrit corpus
- Cross-reference count
- Buddhist canon frequency (84000)
- **결정**: 어떤 weight로 합칠지?
- **추천**: Phase 2에서 실험. 초기엔 단순 cross-ref count.

### D12. 사전 우선순위 재조정 **[FB-3로 확정]**
v1은 tier 1 (15개) 내부 순서가 무작위 → 사용자 불만.
- **결정**: `priority` 1-100 명시적 도입 (각 사전 meta.json)
- **초기 순서 (사용자 확정)**:
  1. Apte — 가장 정확, 학술 표준
  2. Monier-Williams
  3. Macdonell
  4. BHSD
  5. Cappeller
  6. PW kürzer / groß
  7-10. Sanskrit-Sanskrit 사전
  20-29. Tibetan 주요
- 자세한 테이블: `docs/v1-feedback.md` §FB-3
- 사용자 개인화: localStorage + URL param

### D13. 표제어 표시 형식 **[FB-4로 확정]**
- **결정**: 모든 산스크리트 표제어 UI는 IAST (`headword_iast`)
- 원본 (HK `ajJa`, Devanagari `धर्म`) 은 노출 안 함
- "원본 보기" 토글로만 확인 가능
- 티벳어 = Wylie 유지 (IAST는 산스크리트 전용)
- 한자 = 원본 유지
- 빌드 시 강제 생성, verify에서 검증

### D14. 스니펫 추출 전략 **[FB-1로 확정]**
- **결정**: 문자 수 고정 자르기 폐기. 문장 경계 기반.
- `snippet_short` (~120자): 첫 완전 정의
- `snippet_medium` (~400자): 첫 2-3 senses
- `body.senses[]`: 구조화 사전에서 파싱 (Apte/MW 번호)
- 사전별 `sense_separator` 정규식을 `meta.json`에 명시

### D15. Declension 탭 범위 **[FB-5 관련, Phase 3.5 결정]**
- **MVP 결정**: Lookup-only (Heritage 데이터에 있는 ~3000 단어만)
- **Phase 6+ 확장 검토**:
  - 규칙 기반 생성기 (미등록 단어)
  - 복합어(compound) 분해
  - 동사 활용(conjugation)
  - Sandhi 적용 토글
- **비범위**: 역조회(declined → lemma), Vedic sandhi
- 상세: `docs/declension-tab.md`

### D16. 다크모드 색 공간 **[FB-6으로 확정]**
- **결정**: OKLCH 사용 (전통 HSL 대신)
- **이유**: 지각적 명도 일관성 → 라이트/다크 자연스러운 대칭
- 브라우저 호환성: Safari 15.4+, Chrome 111+, Firefox 113+ (2023년 기준 충분)
- Fallback: `@supports (color: oklch(0.5 0 0))` 안에서만 적용, 미지원 시 sRGB fallback
- 재검토: Phase 3 디자인 리뷰 시

### D17. 탭 라우팅 전략 **[FB-5으로 확정]**
- **결정**: 3개 메인 탭 (검색 / 곡용 / 독해)
- 각 탭은 독립 URL 라우트 (`/`, `/declension`, `/reader`)
- 헤더의 검색 입력창은 탭별 컨텍스트 감지
- 독해 탭은 Phase 6+에서 활성화 (초기엔 "Coming soon")
- 탭 간 단어 공유: 검색 결과에 "곡용 보기 →" 크로스-링크

### D18. 역검색 (Eng/Ko → 원어) **[FB-8으로 확정]**
- **결정**:
  - Phase 1에서 각 JSONL 엔트리에 `reverse.en[]` + `reverse.ko[]` 필드 inline 채움
  - 명시적 Eng→Skt 사전 3개 (Apte, Borooah, MW): `meta.json.direction: "en-to-skt"`
    표기 → 평소 검색 경로
  - 티벳어는 Eng→Bo 사전 부재로 body 토큰 추출이 유일한 역검색 경로
  - Phase 2에서 `build_reverse_index.py`가 `reverse.en/ko`를 모아 msgpack 역인덱스
  - 한국어 토크나이저: 공백·구두점 split, 한자 병기 `법(法)` → `[법, 法]` 둘 다 유지
  - stopword 리스트는 Claude가 제안 (사용자 승인 없이)
- **이유**: 사용자가 영어 `duty`나 한국어 `의무`를 입력할 때 산스크리트 `dharma`,
  티벳어 `chos` 찾기. v1에서 전혀 불가능했던 기능.
- **대안 검토**:
  - Phase 2 이후로 미루기 → 사용자 명시적 요청으로 Phase 1 포함
  - FTS5만으로 → 노이즈 크고 Tier 0 캐시 불가
- **범위 외**:
  - 한국어 morphological analysis (조사 제거) — Phase 2 `mecab-ko` 검토
  - 영어 stemming/lemmatization — Phase 2 검토
  - Vedic/한문 원어 역검색 — Phase 6+ 영역
- **재검토 시점**: Phase 3 UI 완성 후

---

## 결정 미정 시 영향

각 결정은 미정으로 두고 시작 가능. 미정 시 기본값:
- 단순 단일 패키지 (D1=A)
- SvelteKit (D2=A)
- 한국어 v1 재사용 (D3=A)
- JS FST (D4=B)
- JSON + zstd (D5=B)
- Vanilla CSS (D6=A)
- System fonts (D7)
- GitHub Pages (D8=C)
- v1 영구 유지 (D9=B)
- D1 (D10=A)
- 단순 cross-ref count (D11)
- v1 tier 유지 (D12)

이 기본값으로 진행해도 충분히 동작. 실제 데이터 보고 변경.

---

## ✅ 확정된 결정 (사용자 피드백 기반)

- D3 한국어 번역 = v1 재사용 + 신규 batch 보완 (FB-2)
- D12 사전 우선순위 = Apte #1, MW #2 + priority 1-100 (FB-3)
- D13 표제어 표시 = 항상 IAST, 원본은 토글 (FB-4)
- D14 스니펫 = 문장 경계 기반 short/medium/senses (FB-1)
- D15 Declension 탭 = lookup-only MVP, 생성기는 v3+ (FB-5)
- D16 다크모드 = OKLCH 3-state 토글 (FB-6)
- D17 탭 라우팅 = 3-탭 독립 URL (FB-5)
- D18 역검색 = Phase 1 inline reverse 필드 + Phase 2 인덱스 (FB-8)
- 프로젝트 이름 = Sanskrit-Tibetan Workspace (FB-7)
- 패키지 매니저 = `uv` + `pyproject.toml`
- Git 배포 정책 = meta.json/reports 커밋, JSONL은 gitignore (LICENSES 참조)
- HTML 파싱 = `lxml` (XDXF) + `beautifulsoup4` (Apple dict) 조합

상세: `docs/v1-feedback.md`, `LICENSES.md`
