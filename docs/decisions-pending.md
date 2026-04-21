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

### D3. 한국어 번역 어떻게?
- v1은 DE/FR/LA 사전 9종 → Anthropic API로 번역해서 `body_ko` 저장
- v2도 같은 방식?
- **A**: v1 결과 그대로 재사용 (JSONL에 `body.ko` 포함)
- **B**: 처음부터 다시 번역 (Claude Sonnet 4.5? 더 정확)
- **C**: 번역 생략, 원문만 표시
- **추천**: A. 추가 비용 없음. v3에서 재번역 검토.

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

### D12. 사전 우선순위 재조정
v1의 tier 1 (15개) 그대로? 재검토?
- MW, BHSD, Macdonell — 합의된 핵심
- Tibetan Hopkins, RangjungYeshe — 합의됨
- 84000 — Buddhist 특화
- **추천**: v1 유지. 사용 데이터 보고 조정.

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
