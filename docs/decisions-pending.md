# Decisions Pending — Nighaṇṭu v2

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
- **A**: `nighantu.haMsa.io` (서브도메인)
- **B**: `nighantu.org` 또는 비슷한 신규 도메인
- **C**: GitHub Pages 기본 도메인 + Cloudflare Pages 기본
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

상세: `docs/v1-feedback.md`
