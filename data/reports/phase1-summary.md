# Phase 1 Summary — 2026-04-22

Phase 1 "데이터 추출 + 검증" 완료.

## 완료된 작업

### 1.0 환경 + 인프라
- `uv 0.11.7` + Python 3.12.13 + 20 패키지
- `pyproject.toml` + `uv.lock` (재현 가능)
- 디렉터리 구조: `scripts/lib/` · `data/sources/` · `data/jsonl/` · `data/reports/` · `tests/`

### 1.0b 공통 모듈 (`scripts/lib/`)
- `transliterate.py` — v1에서 복사 (동기화 유지)
- `normalize.py` — IAST 유효성 + HK signature 감지
- `html_utils.py` — XDXF/Apple HTML → plain text
- `snippet.py` — FB-1 smart snippet (short ≤180, medium ≤500)
- `reverse_tokens.py` — FB-8 en/ko 토큰 추출 (stopwords + 한자 병기)
- `types.py` — Entry/Meta TypedDict

**79 단위 테스트 통과**.

### 1.4 meta.json × 130
- `scripts/build_meta.py`가 매핑 테이블 → 130 `data/sources/{slug}/meta.json` 생성
- Priority 1-92 배분 (FB-3): Apte #1, MW #2, Macdonell #3, BHSD #4, ...
- 19개 `exclude_from_search: true` (FB-5 Heritage Declension)
- 3개 `direction: en-to-skt` (FB-8 역방향)

### 1.4b 중복 감지 + 병합
`scripts/detect_duplicates.py`로 24 pair 비교:
- **STRICT 병합 3쌍** (Jaccard ≥0.9, body ≥0.8): bod-rgya 중복 / Hopkins-Skt 1992+2015 / Grassmann XDXF+GRETIL
- **MW option A 드롭 2개**: mwse.sandic, mw-sdt.apple (high redundancy)
- 135 원본 → **130 canonical**

### 1.1 + 1.3 extract_from_v1.py
- v1 sqlite → 130 JSONL (`data/jsonl/`)
- IAST 강제 (FB-4): Sanskrit 엔트리 전부 `headword_iast` 생성
- Headword 클린: `\n`, `{` 이후 제거 (v1 data quality 이슈 수정)
- 병합 사전 de-dup by `headword_norm`

### 1.2 Smart snippets (FB-1)
- 문장 경계 감지: sense_separator → `;` → 번호 → 문장 끝
- `snippet_short` ≤180, `snippet_medium` ≤500
- 58,003 엔트리에서 `body.senses[]` 구조화 (Apte/MW/Macdonell)

### 1.6 Reverse tokens (FB-8)
- 각 엔트리에 `reverse.en[]` (max 40), `reverse.ko[]` (max 40) inline 저장
- 영어: stopwords (학술 약어 포함) 제거, 위치 가중치
- 한국어: 한자 병기 `법(法)` → `[법, 法]` 둘 다 유지
- **검증**: MW에서 "fire" 검색 → 1,276개 산스크리트 엔트리 매칭

### 1.5 audit_translations.py
- 130 dict별 `body.ko` 커버리지 카운트
- 결과: DE/FR/LA 100%, EN/BO/SA 0% (v1 이미 유럽어 완료)
- Phase 2 todo: En→Ko 확장 검토 (1.87M 영어 정의 엔트리)

### 1.7 verify.py
- JSON Schema (docs/schema.json) 전체 검증
- FB-4 IAST 유효성 (dict family별 예외 처리)
- FB-3 priority 범위 + 중복
- FB-5 exclude_from_search family 일관성
- FB-8 reverse 토큰 형식

## 결과 지표

| 지표 | 값 |
|---|---|
| Dictionaries | 130 |
| Total entries | 3,364,487 |
| Original v1 entries | 3,811,344 |
| Dropped (MW option A) | 363,082 |
| Deduped (3 merges) | 83,775 |
| Total JSONL size | 5.4 GB (gitignored) |
| Schema errors | **0** |
| Warnings (data-quality) | 21,134 (0.63%) |
| IAST conversion failures | 0 |
| Empty bodies | 29 |
| Structured senses parsed | 58,003 |
| Korean translations | 381,071 (11.3%) |
| Reverse EN tokens | all entries with body |
| Reverse KO tokens | 310,327 entries |

## 성능 (병렬화 + fastjsonschema 적용 후)

| 단계 | 시간 |
|---|---|
| build_meta (check-only) | 0.2s |
| **extract** (5 workers) | **1분 23초** |
| audit_translations | 14s |
| **verify** (5 workers + fastjsonschema) | **16s** |
| **전체** | **~2분** |

Sequential 버전 대비 파이프라인 **6.5× 빠름** (13분 → 2분).
- extract: 6:10 → 1:23 (4.5×, `multiprocessing.Pool`, SQLite ro-concurrent)
- verify: 6:12 → 0:16 (23×, `fastjsonschema` JIT + `multiprocessing`)
- audit: 30s → 14s (2.1×, `"ko":` substring 사전 필터)

Unit tests: **0.1초** (79 tests)

## Phase 1 남은 경고 21K개 — Phase 2+ 처리

비IAST 헤드워드 경고 분포:
- `macdonell-sandic` (11,712): circumflex 악센트 (â, ê, î) — SANDIC 고유 인코딩
- `bloomfield-vedic-concordance`: 전체 운문 텍스트가 headword (특수 사전)
- `pwk`/`pwg`: prefix `*-` marker
- `abhyankar-grammar`: 파니니 수트라 괄호 표기
- `apte-sanskrit-english` (105): `agha = aṃgh` 같은 참조 equal sign

모두 데이터 품질 개선 후보이지 빌드 실패 요인 아님.

## 다음 (Phase 2)

ROADMAP Phase 2:
1. **빈도 결정**: top-10K headwords (Tier 0 메모리)
2. **번역 batch** (FB-2 재해석): En→Ko 확장 검토
3. **Tier 0 index**: `public/indices/tier0.msgpack.zst`
4. **FST 자동완성**: `public/indices/autocomplete.fst`
5. **역인덱스 빌드** (FB-8): `reverse_en.msgpack.zst`, `reverse_ko.msgpack.zst`

## 참조

- 스키마: `docs/schema.json`
- 매핑: `data/reports/slug-mapping-proposal.md`
- 중복: `data/reports/duplicates.md`
- 번역 coverage: `data/reports/translation_coverage.md`
- 라이선스 + 배포 정책: `LICENSES.md`
