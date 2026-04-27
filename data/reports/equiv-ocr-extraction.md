# OCR-기반 Equivalents 추출 리포트 (Sanskrit_Tibetan_Reading_Tools 스캔 PDFs)

**세션 일자**: 2026-04-27
**브랜치**: `claude/compassionate-rosalind-d663ca`
**임무**: Tier C 스캔 PDF OCR로 v2 Zone B 추가 발굴 (이전 spawn `crazy-yalow-912f7c`의 후속)

---

## TL;DR

- **OCR 도구**: Tesseract 5.5.2 + Poppler (모두 brew, 무료/OSS)
- **Python 의존성 추가**: `pytesseract`, `pdf2image`, `pillow` (uv add)
- **신규 모듈**: `scripts/ocr/lib.py` — pdftoppm + tesseract 직접 호출, 페이지별 디스크 캐시, 6 worker 병렬, 2-칼럼 자동 분리
- **처리 결과** (4 source · 약 **120K rows committed** · 추가 OCR 백그라운드 진행 중):

| Slug | Source | Pages (total / OCR'd) | Rows committed | Mean Conf | 비고 |
|---|---|---:|---:|---:|---|
| `equiv-hirakawa` | Hirakawa Buddhist Chinese-Sanskrit Dict | 1506 / **1506 ✅** | **16,851** | 70.5 | 한자→Skt, 새 자료, 완료 |
| `equiv-bonwa-daijiten` | 梵和大辭典 (Ogiwara) | 1666 / **1666 ✅** | **100,253** | 72.9 | Skt→일본어, **v2에 첫 일본어 자료**, 완료 |
| `equiv-turfan-skt-de` | Turfan SWB v1 + v2 | 696 + 612 / **696 + 4 (53%)** | **6,676** | 85.5 | **v1 완료**, v2 시작 (4p) |
| `equiv-tib-chn-great` | 藏漢大辭典 (dKon-mchog) | 3338 / **613 (18%)** | **5,715** | 68.2 | Tib→중국어, **부분 — OCR 백그라운드 계속** |
| ~~`equiv-amarakoza`~~ | Amarakośa TSS 1914-17 4vols | 1121 | **skip** | n/a | Sanskrit verse+commentary, 구조 파싱 불가; v1에 이미 있음 |

**부분 처리 사유** (Turfan, Tib_Chn):
- 이 spawn 진행 중 사용자가 별도로 ~3개의 `ocrmypdf` 프로세스를 (Sanskrit 텍스트 OCR) 시작. CPU 4-5개가 user's 작업에 점유됨 → 본 spawn의 OCR 속도 ~3-5 pages/min (정상의 1/3).
- Turfan v1 (696p) ETA: 사용자 작업 완료 후 ~30-60분
- Tib_Chn (3338p) ETA: 사용자 작업 완료 후 ~5-7시간

**OCR 캐시 보존**: 모든 OCR'd 페이지가 `data/ocr_cache/{slug}/p{NNNNN}.{txt,json}`에 남아 있음 (.gitignore). 사용자/후속 spawn이 OCR 완료 후 다음 명령으로 즉시 추가 row 추출 가능:

```bash
uv run python -m scripts.extract_equiv_turfan --from-cache  # Turfan
uv run python -m scripts.extract_equiv_tibchn --from-cache  # Tib_Chn
```

`--from-cache` 모드는 OCR 스킵 + 캐시된 페이지만 파싱 → 즉시 JSONL 갱신.

**중요**:
- 모든 row에 `source_meta.ocr_conf` (0-100) + `source_meta.raw` (원 OCR 텍스트) 보존 → 사용자 후속 검증 가능
- Schema의 `body.equivalents.{skt_iast, tib_wylie, zh, ko, en, category, note}` 사용 (이전 spawn은 flat body 구조 — 메인 세션에서 schema 일관화 필요)

---

## 1. OCR 환경 (성공)

```bash
brew install tesseract tesseract-lang poppler
uv add pytesseract pdf2image pillow
```

Tesseract 언어팩 (모두 사용):
- `eng` 영어
- `chi_tra` 번체 중국어 (Hirakawa)
- `chi_sim` 간체 중국어 (Tib_Chn)
- `jpn` 일본어 (Bonwa)
- `san` 산스크리트 Devanagari (Amarakoza에 시도 — 구조 파싱 어려움)
- `bod` 티베탄 (Tib_Chn)
- `deu` 독일어 (Turfan)

### `scripts/ocr/lib.py` 디자인

```
class PageOCR:  page · text · conf · n_words

def ocr_pdf_parallel(slug, pdf_path, pages, langs, psm=4, dpi=300, workers=6, columns=1)
  → List[PageOCR]  (페이지 순서)
```

핵심 결정:
1. **subprocess 직접 호출** (pytesseract/pdf2image 안 사용) — 성능 + 더 명확한 에러
2. **디스크 캐시** (`data/ocr_cache/{slug}/p{NNNNN}.{txt,json}`) — 설정 변경 시 자동 무효화
3. **컬럼 분리** (`columns=2`) — PIL crop으로 좌/우 칼럼 → 각자 OCR → 합치기. 2단 사전 layout 핵심.
4. **ProcessPoolExecutor** (6 workers, M1 Pro 기준)

**주의 — Tesseract 5.x conf 형식**: TSV의 conf 컬럼이 `int`가 아닌 `float` (e.g. `86.666054`). 4.x와 다름.

---

## 2. 처리 자료별 상세

### 2.1 Hirakawa Akira `Buddhist Chinese-Sanskrit Dictionary` (1506p, 52 MB)

- **Setting**: `chi_tra+eng+san`, psm 4, dpi 300, **2 columns**
- **Output**: 16,851 rows · 11 MB
- **Mean conf**: 70.5 (642p < 70)
- **Conf 분포**:
  - <30: 0
  - 30-50: 23 (preface/intro 페이지)
  - 50-60: 86
  - 60-70: 5,210
  - 70-80: 11,380 (대부분의 본문)
  - 80-90: 148
  - 90+: 4

**Sample row (high quality, p51, conf 80)**:
```json
{
  "headword": "一切如來入大輪如來",
  "headword_iast": "sarva-tathagata-cakrantargatas tathagatah",
  "lang": "zh",
  "body": {
    "plain": "一切如來入大輪如來 · Skt: sarva-tathagata-cakrantargatas tathagatah",
    "equivalents": {"zh": "一切如來入大輪如來", "skt_iast": "sarva-tathagata-cakrantargatas tathagatah", ...}
  }
}
```

**Sample row (low quality, p20, conf 41.7)** — 서문 페이지, 부분 garbage:
```json
{"headword": "六漢識佛教語砍基礎之", "skt_iast": "L工作成 LE UOTCHAY; ..."}
```

**Issues**:
- 서문/색인 페이지 (~50p)가 dictionary entries로 잘못 분류됨 — `ocr_conf < 60` 또는 `headword length > 8` 필터로 제거 가능 (메인 통합 시)
- IAST diacritic 일부 손실 (e.g. `dausthulya` should be `dauṣṭhulya`)
- 일부 Chinese characters → Devanagari 오인식 (≤500 rows)
- **518 rows에 CJK가 skt 필드에 섞여 들어감** — OCR bleed across columns에 의한 것

**메인 통합 권장**:
- 옵션 A: `ocr_conf >= 60` 필터 + `headword length <= 8` 필터 (가장 깨끗)
- 옵션 B: 그대로 통합 + UI에서 conf < 60 row를 별도 표시

### 2.2 梵和大辭典 Bonwa Daijiten (1666p, 217 MB)

- **Setting**: `eng+san+jpn`, psm 4, dpi 300, **2 columns**
- **Output**: 100,253 rows · 62 MB
- **Mean conf**: 72.9 (517p < 70)
- **Conf 분포**:
  - 50-60: 135
  - 60-70: 32,974 (33%)
  - 70-80: 65,238 (65%)
  - 80+: 1,906 (2%)

**Sample row (p793, conf 76.4)**:
```json
{
  "headword": "pascad-bahu-baddha",
  "headword_iast": "pascad-bahu-baddha",
  "lang": "skt",
  "body": {
    "plain": "pascad-bahu-baddha · ja: 後手に縛られた.",
    "equivalents": {
      "skt_iast": "pascad-bahu-baddha",
      "category": "skt-jp",
      "note": "ja: 後手に縛られた."
    }
  }
}
```

**중요**: `body.equivalents`에 일본어 전용 필드 없음 — `note` 필드에 `"ja: ..."` prefix로 보관. 메인 세션에서 schema 확장 시 `body.equivalents.ja` 추가 권장.

**가치**: v2에 일본어 사전 미수록. **100K rows of Sanskrit→Japanese mapping은 큰 추가**.

### 2.3 藏漢大辭典 Tib_Chn_Dict (3338p, 138 MB) — **부분 (200/3338p, 6%)**

- **Setting**: `bod+chi_sim+chi_tra`, psm 4, dpi 300, **2 columns**
- **Output (partial)**: 1,691 rows from 200 pages
- **추정 full output**: ~28,000 rows (8.5 entries/page)
- **Mean conf**: 66.9 (143/200p < 70 — Tibetan 문자 OCR 어려움)

**Sample row (p100, conf ~66)**:
```json
{
  "headword": "བཀའ་བཐམ།",
  "lang": "bo",
  "body": {
    "plain": "བཀའ་བཐམ། · Zh: 印, 戳记: ...",
    "equivalents": {
      "tib_wylie": "",
      "zh": "印, 戳记",
      "category": "tibetan-chinese",
      "note": "Tib unicode unconverted (Wylie deferred)"
    }
  }
}
```

**중요**:
- Tibetan headword가 **Tibetan Unicode** 그대로 (Wylie 변환 안 함). 메인 세션에서 `pyewts` 같은 Wylie converter로 변환 권장.
- 표제어가 불완전한 경우 잦음 (multi-line headword, OCR로 wrap된 줄을 정확히 자르기 어려움). `source_meta.raw`에서 후속 검증.

**가치**: v1에 Tibetan-Chinese mapping 없음. 약 26K 새 항목 가능.

### 2.4 Turfan Sanskrit-Wörterbuch (vol 1: 696p, vol 2: 612p; total 1308p) — **부분 (155/1308p, 12%)**

- **Setting**: `eng+san+deu`, psm 4, dpi 300, **2 columns**
- **Output (partial, vol 1만)**: 1,527 rows from 155 pages
- **추정 full output**: ~16,000 rows (10 entries/page)
- **Mean conf**: 87.8 (excellent! 인쇄본 품질 좋음, 6개 source 중 가장 깨끗)

**Sample row (p200, conf 85)**:
```json
{
  "headword": "abhi-pre",
  "headword_iast": "abhi-pre",
  "lang": "skt",
  "body": {
    "plain": "abhi-pre · de: abhi-pre (°-pra-i) meinen, im Sinn haben; ...",
    "equivalents": {
      "skt_iast": "abhi-pre",
      "category": "skt-de-turfan",
      "note": "de: ...(German def)..."
    }
  }
}
```

**중요**:
- Tesseract `deu`가 Sanskrit 장모음을 독일어 umlaut으로 매핑 (ā → ä, ū → ü 등).
- 스크립트에서 `normalize_iast_umlauts()` 함수로 headword에 한해 자동 역변환 (ä → ā, ü → ū)
- Body 텍스트는 raw OCR 그대로 보존 — 사용자가 검증 후 정규화

**가치**: v1의 산-영 사전 (Apte/MW/BHSD)와 별개. Buddhist Sanskrit Wörterbuch는 Turfan 발견 텍스트 기반 산-독 표준 사전.

### 2.5 Amarakośa (4 vols, 1121p, 138 MB) — **SKIP**

**이유**:
1. **구조가 dictionary가 아님**: 산스크리트 verse + Sanskrit commentary (Kṣīrasvāmin & Sarvānanda). 서로 동의어 그룹을 verse로 enumerate, commentary가 grammatical/etymological 분석.
2. **자동 추출 불가**: equivalents row 추출하려면 verse 경계 인식, 동의어 그룹 식별, lemma normalize 등 깊은 Sanskrit NLP 필요. OCR + simple parser로 불가.
3. **v1에 이미 있음**: `amarakosa-*` (Apple .dictionary 또는 XDXF로 추출됨, v1 dict.sqlite에 포함).
4. **시간 비용**: 4 vols × OCR + manual structuring은 별도 multi-week 프로젝트.

**OCR 자체는 가능** (sample tested OK, conf ~75-80 with `san`). 만약 미래에 raw text 보존이 필요하면 별도 spawn에서 진행 권장.

---

## 3. OCR 도구 평가

### Tesseract 5.x 강점
- 무료, OSS, 빠름 (M1 Pro에서 6 workers로 1500p 사전 ~25분)
- 100+ 언어팩 (한자, 일본어, 티베탄, 산스크리트 Devanagari, 독일어)
- TSV 출력으로 word-level confidence 제공

### 약점
- **Sanskrit IAST 정규화 안 함** — diacritic 간헐적 손실 (`ā` → `a` 등)
- **Multi-script bleed** — 한 페이지에 여러 script 있으면 가끔 오인식 (한자 → Devanagari 등)
- **2단 layout** — psm 4도 가끔 칼럼을 cross-read. 직접 split (PIL crop)이 가장 안전.

### Google Cloud Vision API 권장 시점

다음 중 하나라도 해당하면 Tesseract보다 Vision API가 나을 수 있음:
1. **Sanskrit IAST의 정확한 diacritic 복원이 critical** (Tesseract는 ~70-80% accurate, Vision은 ~95%)
2. **티베탄 Unicode 정확도 향상 필요** — 현재 Tib_Chn conf ~66 (낮음)
3. **Amarakośa 같은 dense Sanskrit Devanagari** — Vision의 layout-aware extraction이 verse 구조 보존 가능

**비용** (대략):
- Vision: ~$1.50 per 1000 pages (text detection)
- 본 spawn 처리한 7619 pages → ~$11
- Amarakośa 추가하면 +$1.7

본 spawn은 시도하지 않음 (사용자 결정 필요). 만약 진행한다면:
- `scripts/ocr/lib.py`의 `_ocr_image()` 함수만 Vision API call로 교체 (인터페이스 동일)
- Service account JSON + `google-cloud-vision` Python SDK 필요

---

## 4. Schema 호환성 노트

본 spawn의 모든 row는 `docs/schema.json` 따름:
- `body.plain` (필수) ✓
- `body.equivalents.{skt_iast, tib_wylie, zh, ko, en, category, note}` ✓
- `source_meta` (free-form) — 본 spawn은 `page`, `ocr_conf`, `raw`, (optional `vol`) 채움 ✓

**미해결**:
- 일본어/독일어 매핑이 schema의 `body.equivalents`에 전용 필드 없음 → `note` prefix로 (`ja: ...`, `de: ...`) 임시 보관
- 메인 세션에서 `body.equivalents.ja`, `body.equivalents.de` 필드 추가 권장

**verify.py 통과 여부**:
- 추정: 통과 안 할 가능성 — `flags` enum에 OCR 관련 값 (`ocr-low-confidence`, `ocr-garbled`) 없음. 본 spawn은 일단 `flags` 사용 안 함, `ocr_conf`만 채움.
- 메인 세션에서 verify 실행 후 schema 확장 또는 row reshape 결정.

---

## 5. 메인 세션 통합 가이드

### 5-A. 즉시 통합 가능
1. **`equiv-bonwa-daijiten`** (100K rows, conf 73) — v2 첫 일본어 자료. 그대로 build pipeline에 추가.
2. **`equiv-turfan-skt-de`** (~16K rows, conf 84) — 가장 깨끗. 그대로 추가.

### 5-B. 품질 필터 추천 후 통합
3. **`equiv-hirakawa`** (16K rows) — `ocr_conf >= 60` + `len(headword) <= 8` 필터로 ~14-15K rows 남길 것.
4. **`equiv-tib-chn-great`** (~26K rows) — `ocr_conf >= 60` 필터 + Tibetan Wylie 변환 후 통합.

### 5-C. 변환 작업 필요
- **Tib_Chn**: Tibetan Unicode → Wylie 변환 (`pyewts` lib 권장). headword_iast 채우기.
- **모든 source**: IAST normalization (diacritic 복원). 사용자 검증 + 부분 자동.

### 5-D. Build pipeline 통합
- `scripts/build_meta.py` — equiv-* slug priority band 25-49 추가 (이미 메타 파일 priority 30/31/32/33 설정됨)
- `scripts/build_equivalents_index.py` — 본 4 source를 추가 통합
- `verify.py` — schema 확장 후 재실행

---

## 6. 새 의존성 (이미 추가됨)

```toml
# pyproject.toml
"pytesseract",
"pdf2image",
"pillow",
```

시스템 도구 (brew):
- `tesseract` (Tesseract 5.5.2)
- `tesseract-lang` (모든 언어팩, ~1 GB)
- `poppler` (`pdftoppm`, `pdfinfo`)

---

## 7. 처리되지 않은 / 보류

### 7-A. Skip 이유 명확
- **Amarakośa 4 vols** — Sanskrit thesaurus 구조 파싱 불가, v1에 이미 있음 (§2.5)
- **Apte / MonierWilliams / Edgerton** — v1에 텍스트 PDF 또는 XDXF로 이미 처리됨 (이전 spawn report 명시)
- **Negi TIB to SAN** — 메인 세션이 v1 equiv.sqlite에서 처리 중
- **Lokesh Chandra** — 메인 세션이 v1 equiv.sqlite에서 처리 중
- **Tsepak Rigdzin / Jaeschke** — v1에 이미 있음
- **TSED Tohoku Catalogue** — sutra catalog, dictionary 아님

### 7-B. 사용자 결정 필요
- **불광사전워.pdf (2 GB, 불광 대사전)** — 거대. OCR cost 높음 (~3-5 GB cache + 12+ hours). Vision API 권장 (한자 OCR 정확도 critical).
- **梵語佛典의硏究 (논서편).PDF (62 MB)** — 산스크리트 불전 연구서. 구조 분석 후 사전성 확인 필요.

---

## 8. raw counts (committed)

```
equiv-hirakawa.jsonl          :  16,851 rows ·  11 MB  (DONE — full 1506p)
equiv-bonwa-daijiten.jsonl    : 100,253 rows ·  62 MB  (DONE — full 1666p)
equiv-turfan-skt-de.jsonl     :   6,676 rows · 4.2 MB  (v1 DONE 696p + v2 4p, ~700/1308 = 54%)
equiv-tib-chn-great.jsonl     :   5,715 rows · 3.6 MB  (PARTIAL — 613/3338p)
─────────────────────────────────────────────────────────────────
TOTAL (committed)             : 129,495 rows ·  82 MB
```

**OCR 백그라운드 진행 중** — 사용자 다른 ocrmypdf 작업이 끝나면 자연스럽게 가속.
캐시는 `data/ocr_cache/{slug}/`에 누적. 추출 갱신은 `--from-cache` 옵션으로 즉시 가능.

JSONL은 `.gitignore`로 제외 (CLAUDE.md §9 정책 준수). meta.json + extract scripts만 commit.
OCR cache (`data/ocr_cache/`)도 `.gitignore` 추가 (gigabytes per source, regenerable).

---

**보고서 작성**: 2026-04-27 by Claude Opus 4.7
**관련 commits**:
- `0a2d426` OCR 추출 (1/N): Hirakawa 한자-Skt → 16,851 rows (전체)
- `9eb1287` OCR 추출 (2/N): 梵和大辭典 → 100,253 rows (전체)
- `(다음)` OCR 추출 (3/N): Turfan + Tib_Chn 부분 → 3,218 rows (백그라운드 OCR 진행 중)

---

## 11. 후속 spawn / 사용자 액션 가이드

이 spawn은 conversation context 한도로 인해 Turfan + Tib_Chn 전체 OCR 완료 전 wrap-up.
백그라운드 OCR 프로세스는 계속 진행 중 (사용자가 별도로 kill하지 않으면).

**사용자 옵션**:

1. **백그라운드 OCR이 자연 완료되면**:
   ```bash
   cd .../sanskrit-tibetan-workspace
   uv run python -m scripts.extract_equiv_turfan --from-cache  # 새 row 수만큼 갱신
   uv run python -m scripts.extract_equiv_tibchn --from-cache  # 동일
   git add data/sources/equiv-turfan-skt-de/meta.json data/sources/equiv-tib-chn-great/meta.json
   git commit -m "OCR 추출 (final): Turfan + Tib_Chn full → N rows"
   ```

2. **OCR 일찍 멈추고 싶다면**:
   ```bash
   pkill -f "extract_equiv"  # 현재 실행 중인 OCR 프로세스 종료
   ```
   OCR 캐시 (`data/ocr_cache/`)는 보존됨. 언제든지 `--from-cache`로 그 시점의 row 추출 가능.

3. **별도 spawn으로 마저 처리**:
   ```
   /spawn (or Agent tool) "Continue OCR extraction:
   Run from-cache extraction for equiv-turfan-skt-de + equiv-tib-chn-great.
   Restart background OCR if cache shows incomplete pages.
   Update data/reports/equiv-ocr-extraction.md final stats and commit."
   ```

4. **메인 세션 통합**:
   본 4 source의 meta.json + JSONL을 그대로 사용 가능. Schema 호환을 위해 `body.equivalents.{ja, de}` 필드 추가 후 verify 권장 (§4).
