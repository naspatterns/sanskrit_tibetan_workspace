# Declension 탭 설계

## 배경

v1에서 Heritage Declension 사전 (decl-a01~a10, decl-a1-ss~a5-ss, decl-b1~b3 등 ~20개)은
일반 검색 결과를 오염시켰음. 예: "dharma" 검색 → 곡용 표 여러 개 + 실제 정의문이 섞임.

**사용자 피드백 (FB-5)**: "Declension 사전은 검색 탭에서 제외하고 별도 탭으로 분리해달라."

## 목표

- 산스크리트 명사/형용사의 곡용표(파라다임) 조회·생성을 **독립된 도구**로 분리
- 검색 결과에서 declension 사전 완전 제외
- 학자가 원하는 정보: 성(gender) × 수(number) × 격(case) 24 slot의 완전한 표

---

## UI 초안

```
┌─ 검색 | Declension | 독해 ──────────────────────────────┐
│                                                           │
│  [단어 입력: ____________] [성별: 자동 ▼] [조회]         │
│                                                           │
│  ├─ 자동 감지된 단어: deva (m., a-stem, class I)          │
│  ├─ 패러다임: a-stem masculine                            │
│  └─ 같은 패턴: rāma, nara, vṛkṣa                          │
│                                                           │
│  ┌─ 곡용표 ──────────────────────────────────────────┐   │
│  │          단수 (sg.)  양수 (du.)  복수 (pl.)        │   │
│  │  주격   deva-ḥ     devau        devā-ḥ           │   │
│  │  대격   deva-m     devau        devā-n           │   │
│  │  구격   deve-na    devā-bhyām   devai-ḥ          │   │
│  │  여격   devā-ya    devā-bhyām   deve-bhyaḥ       │   │
│  │  탈격   devā-t     devā-bhyām   deve-bhyaḥ       │   │
│  │  속격   deva-sya   dev-ayoḥ     devā-nām         │   │
│  │  처격   deve       dev-ayoḥ     deve-ṣu          │   │
│  │  호격   deva       devau        devā-ḥ           │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
│  [Sandhi 적용] [비교하기: + 다른 단어 추가] [인쇄]       │
│  [이 단어 사전 검색 →] [같은 패러다임 모두 보기]         │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 상호작용
- **단어 입력**: Sanskrit IAST/HK/Devanagari 자동 감지 (검색 탭과 동일)
- **성별 자동 감지**: 사전에서 `lang.gender` 힌트 + 어미 패턴으로 추정. 수동 오버라이드 가능
- **패러다임 클래스 표시**: "a-stem m.", "i-stem n." 등. 클래스 클릭 → 예시 단어 리스트
- **각 cell 클릭**: 해당 형태로 검색 탭 이동 (declined form → 원형 검색)
- **비교 모드**: 2개 단어 나란히 (학습용)
- **Sandhi 토글**: 표준형 vs 연성 적용형

---

## 데이터 소스

### v1의 Heritage Declension 사전 구조
Apple `.dictionary` 포맷에서 추출된 파라다임 데이터:
```
decl-a01 ~ decl-a10: 기본 파라다임 (a-stem, i-stem, u-stem, ...)
decl-a1-ss ~ decl-a5-ss: semi-stem (자주 쓰는 짧은 클래스)
decl-b1 ~ decl-b3: consonant-stem 변형
decl-b-ss: consonant semi-stem
```

각 사전은 수백~수천 개 예시 단어를 포함하며, 각 단어당 24 cell 완전 표.

### v2 재구조화

`data/declension/` 디렉터리에 다음 산출:

**1. `paradigms.json`** — 파라다임 클래스 자체
```json
{
  "classes": [
    {
      "id": "a-stem-m",
      "name": "a-stem masculine",
      "example_word": "deva",
      "pattern": {
        "nom.sg": "{stem}-ḥ",
        "nom.du": "{stem}au",
        "nom.pl": "{stem}ā-ḥ",
        ...
      },
      "example_declension": { /* 완전 표 */ }
    },
    ...
  ]
}
```

**2. `words.json`** — 단어 → 클래스 매핑
```json
{
  "deva": { "class": "a-stem-m", "gender": "m" },
  "nara": { "class": "a-stem-m", "gender": "m" },
  "gaṅgā": { "class": "a-stem-f", "gender": "f" },
  ...
}
```

**3. `generated.json`** — 자주 쓰는 단어의 완전 표 pre-render (~2-3K 단어)

### 생성 vs 조회

- **Tier 1 조회** (fast path): `words.json`에 있는 단어는 `generated.json`에서 직접 읽기 (<10ms)
- **Tier 2 생성** (fallback): 미등록 단어는 어미 패턴으로 클래스 추정 → paradigm 적용 → 생성
- **Tier 3 rule-based** (v3+): 완전한 sandhi + 복합어 처리는 후속 과제

---

## 빌드 파이프라인

`scripts/build_declension.py`:

1. **입력**: v1 dict.sqlite에서 `dict_id IN (decl-*)` 엔트리
2. **파싱**: Apple .dictionary HTML 구조 → 표 추출
   - 각 엔트리의 body는 HTML 표 형태 (decl-a01 등)
   - BeautifulSoup으로 파싱, 표준 24-cell 구조로 변환
3. **패러다임 분류**:
   - 엔트리 제목 (decl-a01, decl-b2 등) → 공식 클래스 이름 매핑
   - 같은 클래스의 예시 단어들 그룹화
4. **검증**:
   - 24 cell 완전성 체크
   - IAST 유효성
   - 패턴 추출 (공통 어미 패턴 자동 유도)
5. **출력**:
   - `public/declension/paradigms.json`
   - `public/declension/words.json`
   - `public/declension/generated.json.zst`

---

## 검색 탭과의 분리

### 데이터 레이어
`meta.json`에 `exclude_from_search: true` 플래그:
```json
{
  "slug": "decl-a01",
  "name": "Heritage Declension a-stem I",
  "exclude_from_search": true,
  "used_by": "declension-tab"
}
```

빌드 스크립트:
- `build_tier0.py`, `build_fst.py`: `exclude_from_search: true` 사전 **스킵**
- `build_declension.py`: 해당 사전**만** 처리

### UI
- 검색 탭 결과에 declension 사전 엔트리 절대 노출 안 함
- 검색 탭에서 단어 검색 결과 하단에 "곡용 보기 →" 링크 (Declension 탭으로 이동)

---

## Phase별 구현

### Phase 1: 데이터 추출 (Phase 1과 동시)
- `extract_from_v1.py`가 declension 사전도 추출
- 결과는 `data/jsonl/decl-*.jsonl`로 저장
- `meta.json.exclude_from_search = true` 자동 설정

### Phase 3.5: Declension 빌드 + 기본 UI (Phase 3 직후)
- `build_declension.py` 구현
- paradigms.json + words.json 생성 (~1주)
- `/declension` 라우트 추가 (Svelte)
- 기본 조회 기능 (단어 입력 → 표 출력)

### Phase 6+ (v3): 고급 기능
- Rule-based 생성기 (미등록 단어 처리)
- Sandhi 적용 모드
- 복합어(compound) 분해
- 동사 활용(conjugation)까지 확장?

---

## 기술 선택

- **표 렌더링**: 단순 `<table>` + CSS Grid. React-Table 같은 라이브러리 과잉
- **파싱**: Python BeautifulSoup (Phase 1) + 순수 JS (런타임 필요 시)
- **생성기**: 초기엔 lookup-only, v3에서 규칙 엔진 검토
- **IAST 변환**: `transliterate.py` 재사용

---

## 우선순위 및 범위

**Phase 3.5 MVP (꼭 있어야)**:
- [ ] Heritage 사전 ~3000개 단어 lookup
- [ ] 24-cell 표 표시
- [ ] IAST 입력 + Devanagari/HK 자동 변환
- [ ] 다크모드 호환

**Phase 6+ (있으면 좋음)**:
- [ ] 미등록 단어 규칙 생성
- [ ] Sandhi 토글
- [ ] 비교 모드 (2+ 단어)
- [ ] 동사 활용
- [ ] 복합어 분해

**범위 외**:
- 역조회 (declined form → lemma) — 별도 기능 (파싱 라이브러리 필요)
- Vedic sandhi — 복잡도 과도
- 산스크리트 작문 도우미 — 프로젝트 scope 벗어남

---

## 참고 자료

- Heritage Sanskrit dictionary (원본 출처)
- Whitney, *Sanskrit Grammar* §§187-294 (명사 곡용)
- Apte, *Practical Sanskrit-English Dictionary* appendix (파라다임 테이블)
- sanskrit-parser (https://github.com/kmadathil/sanskrit_parser) — 향후 참조
