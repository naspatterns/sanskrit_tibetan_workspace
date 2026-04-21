# Sanskrit-Tibetan Workspace — Architecture (v2)

## 1. 핵심 진단

v1의 근본 문제:

| 증상 | 표면 원인 | 근본 원인 |
|------|-----------|-----------|
| 첫 검색 5-10초 | HTTP Range 왕복 다수 | **정적 호스팅에서 2.3GB SQLite를 브라우저가 직접 쿼리하는 구조 자체가 잘못** |
| 본문 로딩 5-10초 | dict.sqlite 크기 2.3GB | 비슷한 ID끼리 물리적으로 모여있지 않아 cache miss 다발 |
| 인덱스 빌드 22단계 | 사전 포맷 이질성 | 원본 → SQLite 직접 INSERT, 중간 표현(IR) 없음 |
| 메모리 200MB+ | 모든 인덱스 동시 로드 | 쿼리 빈도 무관하게 균등 분배 |

**핵심 통찰**: 학술 사용 패턴의 Pareto 분포가 극단적 — 상위 1% 단어가 쿼리 90%.
v1은 모든 단어를 균등 처리. v2는 hot path를 최적화하고 cold path는 우아하게 degrade.

---

## 2. 7대 설계 원칙

### 2.1 Edge Compute First, Static Fallback
정적 호스팅만 고집하지 않음. Cloudflare Workers + D1 (edge SQLite)가
무료 티어(5M reads/일)로 학술 트래픽 전부 커버. 글로벌 <100ms.

### 2.2 Frequency-Tiered Storage
- **Tier 0** (<50ms): 상위 1만 단어 사전 렌더링 완료 JSON → 브라우저 메모리
- **Tier 1** (<200ms): 상위 10만 단어 → 첫 글자별 shard JSON, lazy fetch
- **Tier 2** (<500ms): 나머지 → Cloudflare D1 edge 쿼리
- **Tier 3** (<2s): full-text body search → D1 FTS5

### 2.3 Offline-First
Service Worker + OPFS (Origin Private File System).
학자들은 도서관·비행기·산속에서 작업. 한 번 로드 후 인터넷 없이 동작.

### 2.4 Data as Artifact, Not Database
원본 사전은 **JSONL** (JSON Lines)로 저장. SQLite는 **검색 엔진**일 뿐 데이터 원본 아님.
- Git diff 가능 (사전 변경 추적 명료)
- 외부 도구(`jq`, `grep`, pandas)로 분석 가능
- 학술용 인용 가능한 corpus로 공개
- 사전 추가/수정 시 다른 사전 재빌드 불필요

### 2.5 Streaming UI
모든 렌더링이 "데이터 오면 교체"가 아닌 "데이터 흘러 들어오면서 점진적 렌더".
Tier 0 결과 즉시 → Tier 1 도착 시 merge → Tier 2 완성.

### 2.6 URL-as-State
`/?q=dharma&dict=mw,bhsd&tier=12&from=mvy-123` 같은 URL만으로 완전한 상태 복원.
북마크, 공유, 인용, 외부 링크 가능.

### 2.7 Plugin Architecture
각 사전 = 독립 디렉터리:
```
data/sources/monier-williams/
├── source.xdxf       (원본)
├── parse.py          (사전별 변환 로직)
├── meta.json         (이름, 라이선스, tier, 언어)
└── entries.jsonl     (생성 산출물, gitignored)
```
새 사전 추가 = 디렉터리 추가, 다른 사전 영향 없음.

---

## 3. 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│  사용자 브라우저                                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Svelte 5 SPA (런타임 ~30KB)                           │  │
│  │  - Virtual scrolling (TanStack Virtual)               │  │
│  │  - URL-sync state (nanostores)                        │  │
│  │  - Streaming renderer                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Service Worker                                        │  │
│  │  - Cache-first 전략                                   │  │
│  │  - OPFS (tier 0/1 인덱스 영구 저장)                    │  │
│  │  - 업데이트 manifest 폴링                              │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ In-memory (Tier 0)                                    │  │
│  │  - top-10K entries (~30MB compressed) — fully rendered│  │
│  │  - autocomplete FST (Finite State Transducer, ~3MB)   │  │
│  └──────────────────────────────────────────────────────┘  │
└──────┬──────────────────────────────────────────────────────┘
       │ (cache miss)
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Cloudflare Pages (정적 에셋)                                  │
│  ├── /shards/{a-z}.json.zst    (Tier 1, 26 shards)         │
│  ├── /indices/tier0.msgpack.zst                            │
│  ├── /indices/autocomplete.fst                             │
│  └── /meta/manifest.json       (버전, ETags)                │
└──────┬──────────────────────────────────────────────────────┘
       │ (Tier 2 필요시)
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Cloudflare Workers (엣지 컴퓨트)                              │
│  - 글로벌 <50ms 응답                                           │
│  - GET /api/search?q=...&fields=...                         │
│  - GET /api/entry/:id                                       │
│  - Rate limit + analytics                                   │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Cloudflare D1 (Edge SQLite)                                 │
│  - 자동 글로벌 복제                                             │
│  - FTS5 (한자/IAST/Wylie 통합 인덱스)                          │
│  - Read-only 워크로드                                          │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. 데이터 레이어

### 4.1 JSONL 스키마

```json
{
  "id": "mw-00001",
  "dict": "monier-williams",
  "headword": "dharma",
  "headword_norm": "dharma",
  "headword_iast": "dharma",
  "lang": "skt",
  "tier": 1,
  "body": {
    "raw": "<original markup>",
    "plain": "established order, decree, statute...",
    "snippet_50": "established order, decree, statute, ordina...",
    "snippet_200": "...(more)..."
  },
  "license": "public-domain",
  "source_meta": {"page": "510", "edition": "1899"}
}
```

각 사전의 entries.jsonl이 이 스키마 따름. JSON Schema로 검증.

### 4.2 빌드 파이프라인 (재설계)

```
원본 (XDXF/CSV/HTML/Apple) → parse.py → entries.jsonl   [사전별]
                                            ↓
                                   normalize_pipeline.py  [공통]
                                            ↓
                              canonical-{dict}.jsonl
                                            ↓
                ┌──────────────┬──────────────┬──────────────┐
                ▼              ▼              ▼              ▼
          tier0.msgpack   shards/*.json   d1/import.sql  fst.bin
          (top-10K)       (Tier 1)        (Edge DB)      (autocomplete)
```

각 단계는 멱등적 + 부분 실행 가능 (사전 하나만 재빌드).

### 4.3 빈도 결정
"top-10K"의 빈도는 어떻게 정하나?
- v1 사용 로그 활용 (있다면)
- 없으면 휴리스틱: 사전당 등재 횟수 + 본문에서의 cross-reference 횟수
- 산스크리트 코퍼스의 word frequency (DCS)
- 시간 지나면 실제 쿼리 로그로 재조정 (Cloudflare Analytics)

---

## 5. 검색 엔진

### 5.1 Tier 0 (메모리, <50ms)
```
top-10k.msgpack.zst (~30MB)
 ├── entry_ids sorted by headword_norm
 ├── fully-rendered body snippets (500 chars)
 └── per-headword dict mapping
```
첫 페이지 로드 시 다운로드 + Service Worker 영구 캐시.

### 5.2 FST for autocomplete
- v1: headwords.json 17MB 정렬 배열
- v2: Rust `fst` crate를 WASM 컴파일 → 약 3MB
- 메모리 효율 + prefix 검색 O(log)

### 5.3 Tier 1 (OPFS/CDN, <200ms)
```
shards/{a-z}.jsonl.zst  (26 shards, 각 3-20MB)
- 첫 글자(headword_norm[0])로 샤딩
- 처음 사용 시 OPFS 저장 → 재사용
- HTTP/2 multiplexing으로 여러 shard 동시 로드 가능
```

### 5.4 Tier 2 (Edge API, <500ms)
```
GET /api/search?q=rarelyusedword&lang=skt&limit=100
→ Cloudflare Worker
→ D1 SELECT ... WHERE headword_norm = ?
→ JSON 응답 <200ms 글로벌
```

### 5.5 Tier 3 (Full-text, <2s)
본문 검색은 cold path. D1의 FTS5로 처리. UI에서 별도 진입점 ("내용에서 찾기").

---

## 6. 프론트엔드

### 6.1 프레임워크: Svelte 5
- React 대비 번들 1/5 크기
- Runes reactivity 명료
- SSR 옵션 (SvelteKit)
- 학술 SPA에 충분

### 6.2 상태 관리: nanostores + URL
- 전역 상태는 URL이 source of truth
- 로컬 컴포넌트 상태만 nanostores
- 페이지 새로고침 시 완전 복원

### 6.3 렌더링 전략
- **Progressive streaming**: Tier 0 즉시 → Tier 1 merge → Tier 2 완성
- **Virtual scrolling**: 1000+ 결과에서도 부드러움
- **View Transitions API**: 검색 전환 자연스러움

### 6.4 접근성
- 키보드 네비게이션 full (`j/k`, `/` 검색, `?` 도움말)
- 스크린 리더 지원
- 한자 IME 호환 (`compositionstart/end` 이벤트)
- prefers-reduced-motion 존중
- 대비비 WCAG AAA

---

## 7. 인프라 (월 비용 ~$0)

| 레이어 | 서비스 | 무료 한도 | 현재 규모 충분? |
|--------|--------|-----------|----------------|
| 정적 에셋 | Cloudflare Pages | 무제한 대역폭 | ✅ |
| API | Cloudflare Workers | 100K req/일 | ✅ (학술용) |
| DB | Cloudflare D1 | 5M reads/일 | ✅ |
| 사전 원본 | HuggingFace Datasets | 학술 무료 | ✅ |
| 도메인 | (선택) | $10/년 | 옵션 |

CI/CD: GitHub Actions (무료 2000분/월) — 데이터 빌드 + 배포.

---

## 8. 모니터링

- **Cloudflare Analytics** (PII-free, GDPR 친화적)
- **Sentry** free tier — JS 에러
- **Web Vitals** 자동 수집 → Lighthouse CI 회귀 감지
- **쿼리 카운트** → hot path 확인 → Tier 0 동적 재조정

---

## 9. 데이터 품질

v1에서 발견된 문제 (재발 방지):
- ❌ zh_norm에 티벳어 혼재 (YBh 소스)
- ❌ HK/IAST 정규화 불일치
- ❌ 사전마다 다른 normalize 규칙

v2 해결:
- ✅ JSONL 받는 즉시 JSON Schema 검증
- ✅ 소스별 변환 규칙은 `meta.json`에 명시
- ✅ `verify.py`를 CI 필수 게이트로 승격
- ✅ 정규화 함수는 단일 모듈 (Python + JS 동기화 보장)

---

## 10. 보안·프라이버시

- CSP 엄격 (`script-src 'self'`, `'unsafe-inline'` 없음)
- SRI 모든 외부 스크립트 (있다면)
- 분석 도구: PII 수집 없음, IP 익명화
- 라이선스 명시 (각 사전의 원 라이선스 승계)
- 사용자 검색어 로깅 안 함 (또는 옵트인)

---

## 11. Content Quality (v1 피드백 반영)

v1 사용자 피드백 4건을 데이터 레이어와 UI에서 모두 해결. 상세는 `docs/v1-feedback.md`.

### 11.1 Smart Snippets (FB-1)
- 50자 고정 잘림 → **문장 경계 감지 기반 분절**
- `body.snippet_short` (~120자): 첫 완전 정의 (Zone A 기본)
- `body.snippet_medium` (~400자): 첫 2-3 senses (Zone A 더 보기)
- `body.senses[]`: 구조화된 의미 단위 (Apte/MW 등 번호 매김 사전)
- 빌드 시 `sense_separator` 정규식(meta.json)으로 파싱

### 11.2 Translation Coverage (FB-2)
- v1에서 미완성된 DE/FR/LA/RU 사전 번역 체계적 보완
- Claude Sonnet 4.5 batch API (비용 절감)
- `scripts/audit_translations.py`: coverage 리포트
- `verify.py`: 번역률 <95%면 CI 경고
- UI: `body.ko` 없으면 "원문만" 배지 + 원문 표시

### 11.3 Dictionary Priority (FB-3)
- **Apte #1, MW #2**가 기본 (사용자 요청)
- `meta.json.priority` (1-100) 명시적 순서
- 정렬: priority → tier → entry_count → alphabetical
- 사용자 오버라이드: URL `?pin=...`, localStorage 개인화

### 11.4 IAST Display Normalization (FB-4)
- 모든 산스크리트 엔트리에 `headword_iast` **필수 필드**
- UI는 항상 `headword_iast` 표시 (HK `ajJa` / Devanagari `धर्म` 절대 노출 금지)
- 원본 `headword`는 archival + "원본 보기" 토글 전용
- 티벳어는 Wylie 유지 (IAST는 산스크리트 전용)
- 빌드 시 `transliterate.detect_and_convert_to_iast()` 자동 적용
- `verify.py`: IAST 유효성 검증 (허용 유니코드 범위)

### 11.5 Declension 탭 분리 (FB-5)
- Heritage declension 사전 ~20개를 **검색 결과에서 완전 제외**
- `meta.json.exclude_from_search: true` 플래그로 파이프라인 분기
- 전용 `/declension` 라우트에서 곡용표 조회·생성
- 검색 탭 결과 하단에 "곡용 보기 →" 링크로 크로스-네비게이션
- 상세: `docs/declension-tab.md`

### 11.6 Dark Mode (FB-6)
- 시스템 `prefers-color-scheme` 기본 respect
- 사용자 토글 (라이트/다크/자동 3-state)
- OKLCH 색 공간 사용 — 두 모드에서 명도 일관성 보장
- localStorage로 선택 유지
- 구현: `src/lib/stores/theme.ts` + `src/styles/theme.css` (CSS variables)
- `view-transition` API로 부드러운 전환
- 폰트·색 대비 WCAG AAA 준수 (특히 산스크리트/티벳 diacritics 가독성)

---

## 12. 탭 아키텍처

v2는 3개 주요 탭, 각각 독립적 데이터/라우트/상태:

| 탭 | 라우트 | 데이터 소스 | Phase |
|----|--------|-------------|-------|
| 검색 | `/` | 135개 사전 − declension 제외 | Phase 1-3 |
| 곡용 | `/declension` | Heritage declension 사전 전용 | Phase 3.5 |
| 독해 | `/reader` | 업로드 텍스트 + 검색 API | Phase 6+ |

탭 간 공유:
- 헤더의 검색 입력창은 컨텍스트 감지: 검색 탭에서는 사전 조회, 곡용 탭에서는 곡용표
- URL로 직접 진입 가능 (`/declension?q=deva`)
- 다크모드 토글은 모든 탭에서 공유 (localStorage)

분리 이유:
v1은 모든 사전을 한 검색 공간에 섞어 결과 오염. v2는 **용도별로 데이터 분리**.

---

## 13. v1과 차이 한 줄

> v1: "브라우저에서 2GB SQLite를 HTTP Range로 쿼리"
> v2: "데이터는 JSONL, 검색은 edge, 캐시는 tier별, UI는 streaming"

v1에서 기술적 성능을 고쳐도 콘텐츠 품질 문제가 남음 — v2는 §11에서 이 부분도 체계적으로 해결.
