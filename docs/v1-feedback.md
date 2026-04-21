# v1 사용자 피드백 → v2 반영 사항

v1 (`sanskrit_tibetan_reading_workspace`) 실사용자로부터 받은 불만과
v2에서의 구체적 해결 전략. Phase 1-3 구현 시 체크리스트로 활용.

---

## FB-1. Zone A 스니펫이 너무 짧음

**증상**: 50자 스니펫이 정의문 중간에서 끊겨 핵심 내용 누락.
예) MW "dharma" → `m. (rarely n.) that which is established or...` (다음 단어가 "firm"인데 잘림)

**v2 해결**:

1. **Smart snippet** — 문장/정의 경계 감지
   - 라인 break, 세미콜론, 번호 매김(1., 2., a., b.) 기준으로 senses 구분
   - 빌드 시 (`scripts/build_tier0.py`)에서 첫 완전한 의미 단위 추출

2. **Multi-level snippets** (schema.json 개정):
   - `body.snippet_short` (~120자): 첫 완전한 정의문 (Zone A 기본)
   - `body.snippet_medium` (~400자): 첫 2-3 senses (Zone A "더 보기")
   - `body.plain`: 전체 정의 (Zone C)

3. **사전별 맞춤 추출**:
   - MW/Apte/Macdonell: `;` + 첫 대문자/번호 기준 sense 구분
   - BHSD: BHSD-특유의 번호 형식 파싱
   - 독일어 사전: 번역 필드 우선 노출

4. **Zone A UI**:
   - 기본: `snippet_short` 표시
   - "더 보기" 클릭 → `snippet_medium`
   - "전문" 클릭 → Zone C로 스크롤

---

## FB-2. 독일어/불어/러시아어 번역 미완성

**증상**: v1 번역 파이프라인이 Böhtlingk-Roth, Bopp 등 독일어 사전, Burnouf 등 불어 사전에서 일부만 완료. 러시아어 자료는 거의 미번역.

**v2 해결**:

1. **번역 coverage audit** — `scripts/audit_translations.py`
   - 각 사전별 `body.ko` 유/무 카운트
   - 사전별 coverage % 리포트
   - Phase 1 결과물로 포함

2. **체계적 재번역**:
   - Claude Sonnet 4.5 batch API 사용 (비용 50% 절감)
   - 원본 언어 감지 → 해당 언어 → 한국어
   - 독일어: Böhtlingk-Roth, Bopp, Böhtlingk kürzer, Schmidt, Grassmann, Cappeller (독), Schnzsw
   - 불어: Burnouf, Stchoupak, Renou
   - 라틴: 베다 concordance
   - 러시아어: 있으면 (v1에 명시 안 됨, Phase 1에서 확인)
   - 산스크리트 예문: 주변 문맥 포함 번역

3. **UI 표시**:
   - `body.ko` 있음 → 한국어 기본, "원문 보기" 토글
   - `body.ko` 없음 → "원문만 제공" 배지 + 원문 그대로
   - 번역 품질이 낮을 경우 (짧은 번역, 반복 등) 플래그

4. **CI gate**:
   - `verify.py`에 번역 coverage 체크 추가
   - 전체 번역률 < 95% 면 CI 경고 (block은 아님)

5. **번역 재사용**:
   - v1의 `body_ko` 값이 있는 것은 그대로 재사용 (비용 절감)
   - 빈 것만 신규 번역

---

## FB-3. 사전 우선순위: Apte가 최우선

**증상**: v1에서 tier 1 내부 순서가 무작위/알파벳. Apte가 가장 정확하고 학술적인데 MW 뒤에 표시되거나 묻힘. 사용자는 Apte를 가장 먼저 보고 싶음.

**v2 해결**:

1. **`priority` 필드 도입** — `meta.json`에 1-100 정수
   - 낮을수록 위에 표시
   - tier와 독립적 (tier는 펼침 여부, priority는 순서)

2. **초기값 (사용자 요청 반영)**:
   ```
   priority  dict                  비고
   ─────────────────────────────────────────────
   1         apte-sanskrit-english  Apte (산영)
   2         monier-williams        MW (산영)
   3         macdonell              Macdonell (산영)
   4         bhsd                   BHSD (불교 산영)
   5         cappeller              Cappeller (산영)
   6         pwk                    PW kürzer (산독)
   7         pwg                    PW groß (산독)
   8         kalpadruma             Kalpadruma (산산)
   9         vacaspatyam            Vacaspatyam (산산)
   10        apte-bilingual         Apte 이중언어
   ─────────────────────────────────────────────
   20-29     Tibetan tier 1 (RY, Hopkins, 84000, tshig-mdzod)
   30-49     Tibetan tier 2
   50-69     기타 산스크리트 tier 2
   70-89     declension tables, 파생 사전
   90-99     archival only
   ```
   - Apte 동점 처리: Apte-ES (영), Apte-Skt 순

3. **정렬 규칙**:
   - 1순위: `priority` ASC
   - 2순위: `tier` ASC (1 > 2 > 3)
   - 3순위: entry count DESC (같은 priority면 더 많은 결과)
   - 4순위: alphabetical

4. **사용자 개인화**:
   - URL: `?pin=apte,mw` → 해당 사전을 맨 위로
   - localStorage: 즐겨찾기 별도 관리 (v1 기능 유지)
   - 기본 priority도 사용자가 오버라이드 가능 (설정 페이지)

5. **표시**:
   - priority 1-3은 자동 펼침 + 강조 색상
   - priority 4-10 펼침 + 일반 색상
   - priority 10+는 접힘 기본

---

## FB-4. 표제어 표시는 항상 IAST

**증상**: v1 UI에 `ajJa` (HK), `zAnti` (HK), `धर्म` (Devanagari) 같은 원본 표기가 그대로 노출됨. 사용자는 IAST 표준화된 표시(`ajña`, `śānti`, `dharma`)를 원함.

**v2 해결**:

1. **schema.json 개정** — `headword_iast` **필수 필드**로 승격
   - 모든 Sanskrit 엔트리는 IAST 형식 표제어 보유
   - 빌드 시 `transliterate.detect_and_convert_to_iast()` 자동 적용

2. **3-layer 표제어**:
   - `headword`: 원본 (archival, "원본 보기" 토글)
   - `headword_iast`: IAST 표준 (**UI 표시 기본**)
   - `headword_norm`: 검색 키 (IAST → NFD + strip + lowercase)

3. **UI 규칙**:
   - Zone A/B/C/D 모든 표제어 = `headword_iast`
   - 검색 결과 카운트는 `headword_norm` 기준 (같은 단어 병합)
   - 사전 엔트리 메타 영역에 작게 "원본: ..." 표시 (원본과 IAST가 다를 때만)

4. **언어별 정책**:
   - **산스크리트** (`lang=skt`): 항상 IAST 표시
   - **티벳어** (`lang=bo`): **Wylie 유지** (IAST는 산스크리트 전용, Wylie가 표준)
   - **팔리** (`lang=pi`): IAST-Pali 형식
   - **한자** (`lang=zh`): 한자 그대로 (번체/간체 결정 필요 → decisions-pending)

5. **편집 일관성**:
   - 빌드 단계에서 `headword_iast` 생성 실패 시 빌드 에러
   - `verify.py`에 IAST 유효성 검증 추가 (허용된 유니코드 범위)
   - 의심 케이스 (IAST인데 `z` 포함, HK인데 diacritic 포함) 플래그

6. **마이그레이션 전략**:
   - v1의 모든 `headword` → `transliterate.detect_and_convert_to_iast()` 적용
   - 결과 `headword_iast` JSONL에 추가
   - 원본이 이미 IAST인 경우 pass-through

---

## FB-5. Heritage Declension 사전을 별도 탭으로

**증상**: "dharma" 검색 → 실제 정의문 사이사이 곡용표 사전 엔트리가 섞여 나와
결과 오염. Heritage declension 사전 약 20개 (decl-a01~a10, decl-b1~b3, etc.)는
본질적으로 문법 참조 자료이지 정의 사전이 아님.

**v2 해결**:

1. **데이터 레이어**:
   - `meta.json.exclude_from_search: true` 플래그 (신규)
   - `build_tier0.py`, `build_fst.py`, D1 import에서 해당 사전 스킵
   - `build_declension.py` 전용 파이프라인에서만 사용

2. **UI**:
   - 검색 탭 옆에 **`/declension` 탭 신설**
   - 검색 결과 하단에 "곡용 보기 →" 크로스-네비 링크
   - `/declension?q=deva` URL 직진입 가능

3. **Declension 탭 기능** (Phase 3.5):
   - 단어 입력 → 24-cell 곡용표 (3 numbers × 8 cases)
   - 자동 성별 감지 + 수동 오버라이드
   - 패러다임 클래스 표시 (a-stem m., i-stem n. 등)
   - Cell 클릭 → 해당 형태로 검색 탭 이동
   - Sandhi 토글 (표준형 vs 연성형)

4. **데이터 재구조화**:
   - Heritage 사전의 HTML 표 → `paradigms.json` + `words.json`으로 추출
   - 약 3천 단어 완전 표 pre-render
   - 미등록 단어는 규칙 기반 생성 (v3+)

상세: `docs/declension-tab.md`

---

## FB-6. 다크모드 지원

**증상**: v1에는 다크모드 없음. 산스크리트 학자들은 장시간 텍스트 작업하는데
흰 배경은 눈 피로 유발. 특히 야간 도서관·집 작업 환경.

**v2 해결**:

1. **3-state 토글**: `light` / `dark` / `auto` (시스템 선택 추종)
   - 기본: `auto` (`prefers-color-scheme`)
   - localStorage로 사용자 선택 유지

2. **OKLCH 색 공간**:
   - 전통 HSL/sRGB 대신 OKLCH 사용 — 명도(L) 값이 지각적으로 일관됨
   - 라이트/다크 테마가 자연스럽게 대칭
   - 예: 배경은 `oklch(0.99 0 0)` → `oklch(0.18 0 0)`

3. **구현**:
   - `src/styles/theme.css`: CSS custom properties (`--bg`, `--fg`, `--accent`, ...)
   - `src/lib/stores/theme.ts`: Svelte store + localStorage 동기화
   - `<html data-theme="dark">` 속성 기반 CSS 스위칭
   - View Transitions API로 부드러운 전환

4. **접근성**:
   - 대비비 WCAG AAA (7:1) 기본, AA (4.5:1) 최소
   - 산스크리트/티벳 diacritics (ṛ, ṝ, ṁ, ś, ṣ) 가독성 특별 검토
   - 의미 색상 (tier, priority 색)도 두 모드에서 구분 가능해야 함

5. **UI 배치**:
   - 헤더 우상단 아이콘 토글 (☀️ / 🌙 / 🔄 auto)
   - 키보드 단축키: `Shift+D`

---

## FB-7. 프로젝트 이름 "Sanskrit-Tibetan Workspace"

**증상**: v2 초기 제안 이름 "Nighaṇṭu"(निघण्टु)는 산스크리트어 고전 용어지만
대중에게 지나치게 낯설고 발음도 어려움. 사용자/개발자 모두 부담.

**v2 해결**:

- **공식 이름**: **Sanskrit-Tibetan Workspace**
  - 명확하고 검색 가능, v1과 자연스럽게 연결
- **폴더/패키지**: `sanskrit-tibetan-workspace`
- **짧은 코드네임** (내부용, 필요시): `stw` 또는 `workspace`
- v1 (`sanskrit_tibetan_reading_workspace`)과 구분: "reading" 단어 제거

---

## FB-8. 역검색 — 영어/한국어로 산스크리트·티벳어 원어 찾기

**증상**: v1은 표제어 방향으로만 검색 가능. 사용자가 "duty"를 영어로 치면
`dharma`, `kartavya`, `vrata` 같은 산스크리트 원어를 찾을 수 없음 (Apte Eng→Skt
등 몇몇 역방향 사전을 직접 지목해야 함). 티벳어는 Eng→Bo 사전이 아예 없어
`byang chub sems dpa'` 같은 원어를 영어 gloss로부터 찾는 경로가 없음. 한국어도
마찬가지 — `body.ko`가 있어도 그걸로 역검색이 안 됨.

**v2 해결**:

1. **이원화된 전략**
   - **이미 역방향인 사전** (Apte Eng→Skt, Borooah, MW Eng→Skt): `meta.json`에
     `direction: "en-to-skt"`로 표기. 정상 검색 경로로 편입. 표제어가 영어이므로
     사용자가 영어를 치면 exact match로 즉시 반환.
   - **본문 기반 역인덱스**: Skt→Eng, Bo→Eng 사전의 `body.plain`과 `body.ko`에서
     gloss 토큰 추출 → 별도 역인덱스 생성.

2. **Phase 1: 각 엔트리에 `reverse` 필드 채움** (schema.json)
   ```json
   {
     "id": "mw-12345",
     "headword_iast": "agni",
     "body": { "plain": "m. fire; the god of fire; sacrificial fire; ..." },
     "reverse": {
       "en": ["fire", "god", "sacrificial"],
       "ko": ["불", "화신"]
     }
   }
   ```
   토큰화는 `scripts/lib/reverse_tokens.py`가 담당:
   - **영어**: lowercase, 알파벳만, stopword 제거 (`m. f. n. cf. esp. pl. sg. the a an of to from with by in on at`). 정의 앞쪽 30자 내 토큰 우선. 중복 제거, top 20.
   - **한국어**: 공백 + 구두점 기준 split. 한자 병기 `법(法)`는 **두 토큰 모두 유지** (`법` + `法`). 사용자가 한자 학자일 수 있음. 조사는 Phase 1에서 무시 (Phase 2 `mecab-ko` 검토).

3. **Phase 2: 역인덱스 빌드** — `scripts/build_reverse_index.py`
   - 전체 JSONL 스캔 → `reverse.en` / `reverse.ko` 토큰 역맵 구성
   - 출력: `public/indices/reverse_en.msgpack.zst`, `reverse_ko.msgpack.zst`
   - 구조: `{token: [(entry_id, weight), ...]}` 토큰당 상위 N개 엔트리만
   - 크기 예상: 영어 ~15MB, 한국어 ~5MB (압축 후)

4. **Phase 3: UI 감지**
   - 검색 바가 입력 문자 감지:
     - Latin alphabet-only → `en-to-skt` 사전 우선 + 역인덱스 조회
     - 한글 → `ko` 역인덱스 조회
     - IAST/Devanagari/Wylie → 기존 표제어 검색
   - 역검색 결과 섹션은 별도 "영어/한국어 gloss로 찾음" 라벨 표시 (원본과 구분)

5. **커버리지 예상 (Phase 1 직후)**
   - 영어 역검색: 모든 Skt→En, Bo→En 사전 (~100 사전) → **매우 넓음**
   - 한국어 역검색: `body.ko` 있는 엔트리만 → Phase 2 재번역 전까지 30-50%,
     이후 90%+

6. **검증**
   - `verify.py`: `reverse.en` 토큰 40개 이하, ASCII 알파벳만
   - `reverse.ko` 토큰 40개 이하, 한글 또는 한자
   - 빈 `reverse` 블록은 허용 (body가 숫자·코드뿐일 수 있음)

---

## 반영 우선순위 (Phase 대응)

| FB | Phase 1 | Phase 2 | Phase 3 | Phase 3.5 |
|----|---------|---------|---------|-----------|
| FB-1 Smart snippet | schema 확정 | 빌드 구현 | Zone A UI | — |
| FB-2 번역 coverage | audit 스크립트 | 재번역 batch | UI 배지 | — |
| FB-3 priority 순서 | meta.json 스키마 | 정렬 규칙 | UI 반영 | — |
| FB-4 IAST 표시 | schema 필수 승격 | 빌드 강제 | UI 치환 | — |
| FB-5 Declension 탭 | exclude 플래그 | declension 빌드 | — | 탭 구현 |
| FB-6 다크모드 | — | — | theme.css + store | — |
| FB-7 이름 변경 | ✅ 완료 | — | — | — |
| FB-8 역검색 | `reverse` 필드 + direction | 역인덱스 빌드 | 언어 감지 UI | — |

Phase 1이 끝난 시점에 FB-1~5, FB-8의 데이터 레이어가 완성되어 있어야 함.

---

## 피드백 수집 계속

v2 출시 후에도 이 문서에 추가. 각 피드백은 번호 + 증상 + 해결 전략 형식.
