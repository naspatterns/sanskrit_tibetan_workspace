# Equivalents 추출 리포트 (Sanskrit_Tibetan_Reading_Tools 발굴)

**세션 일자**: 2026-04-27
**브랜치**: `claude/crazy-yalow-912f7c`
**임무**: v1 bilex/equiv.sqlite 외에 `Sanskrit_Tibetan_Reading_Tools/` 폴더의 추가 자료를 발굴해 cross-language equivalents row 확보

---

## TL;DR

- **추출 완료**: 5 source · **77,815 rows** · 약 48 MB JSONL
- **확실 새 자료** (v1에 없음): **Karashima Lotus 2,320** + **Bodkye haMsa 32** = 2,352 rows
- **메인 세션 dedup 필요** (v1 dict.sqlite와 부분 중복): Yogacara index 54,452 / Hopkins TSED 18,600 / Lin 4-lang 2,411 = 75,463 rows
- **OCR 별도 작업 권장 (Tier C)**: 11+ 개 스캔 PDF, 추정 80–200K rows 추가 가능
- **Skip 권장**: THL .def (v1에 모든 18 columns 이미 분리), TIB-SAN-ENG UMA (Tibetan stacked layout 자동 파싱 불가, Hopkins 변형이라 가치 낮음)

---

## 1. 추출 결과 (5 source · 77,815 rows)

| Slug | Source | Rows | v1 중복 여부 | 비고 |
|---|---|---:|---|---|
| `equiv-yogacara-index` | 티베탄딕셔너리-유가사지론색인.pdf (1373p) | **54,452** | ⚠️ `tib-yogacarabhumi` (16,028 expected) — v1보다 3.4× 많음 (sense 단위 vs lemma 단위 가능성) | tib-zh-skt 3언어, 가장 큰 자료 |
| `equiv-hopkins-tsed` | hopkins.ddbc.pdf (2306p, DDBC) | **18,600** | ⚠️ `tib-hopkins-*` (skt/eng/def/div/ex/syn/tenses 7개 split, 메인은 column별 별도 dict) | 우리는 1 entry = 통합 ({Hopkins}, {C}, {MSA}, {L}, {LCh}, {PH} 등 합성) |
| `equiv-karashima-lotus` | Karashima 라집역 연화경 glossary.pdf (620p) | **2,320** | ✅ **새 자료** (v1에 없음) | zh-skt, Kumārajīva 연화경 술어 |
| `equiv-lin-4lang` | 상용한장범영불학술어_2008.pdf (75p, Lin Chung-an) | **2,411** | ⚠️ `tib-common-terms-lin` (2,325) 거의 동일. v1이 더 깨끗 (Tibetan Wylie); 우리는 PDF의 (cid:N) 깨짐 raw | zh-tib-skt-eng 4언어, Tibetan은 (cid:NNN) 폰트 fallback 보존 |
| `equiv-bodkye-hamsa` | Bodkye/haMsa의 Tibetan 사전.docx | **32** | ✅ **새 자료** (사용자 personal study notes) | tib-skt-eng-ko 4언어, 짧지만 고품질 |

**합계**: 77,815 rows, **새 가치 (v1 dedup 후 추정)**: ~44,000 rows
- Karashima 2,320 (확실 새) + Bodkye 32 (확실 새) + Yogacara delta ~38K (54K − 16K) + Hopkins delta ~3.8K (18.6K − 14.7K) + 4-lang delta ~86 (2,411 − 2,325)

---

## 2. 메인 세션 통합 시 처리 가이드

### 2-A. 즉시 통합 가능 (확실 새 자료)
1. **`equiv-karashima-lotus`** — v1에 동일 source 없음. 그대로 build pipeline에 추가.
2. **`equiv-bodkye-hamsa`** — 사용자 personal. 그대로 통합.

### 2-B. 메인 세션이 v1 추출과 비교 후 결정
3. **`equiv-yogacara-index` (54K)** vs **v1 `tib-yogacarabhumi` (16K, XDXF)** —
   - 우리: PDF 색인의 모든 라인 (1 sense = 1 row, e.g. 同 entry가 5개 다른 Sanskrit equivalent마다 별도 row)
   - v1: XDXF lemma 단위 통합
   - **권장**: 우리 추출을 sense-detail level로 두고, v1을 lemma level로 두 dict 모두 유지. UI에서 lemma → senses expand 가능.
4. **`equiv-hopkins-tsed` (18.6K)** vs **v1 `tib-hopkins-*` (split into 7+ dicts by column)** —
   - 우리: 1 row = 1 headword + all `[translation-san]`, `[translation-eng]`, `[tenses]`, `[division-*]`, `[comments]` 통합
   - v1: column 단위로 8개 별도 dict
   - **권장**: 우리 통합 형식을 default view로, v1 column dicts를 detail view 보조로 배치. Or 메인 세션이 dedup하고 v1만 유지.
5. **`equiv-lin-4lang` (2.4K)** vs **v1 `tib-common-terms-lin` (2.3K)** —
   - 거의 동일. v1이 깨끗 (Tibetan Wylie). 우리는 (cid:NNN) 깨짐 raw + PDF citation 정보 유지.
   - **권장**: v1 사용. 우리 거 skip 또는 supplement (Lin 2008 PDF는 zh column이 좀 더 많을 수 있음 — 확인 후 보충).

### 2-C. body schema 호환
모든 row가 `body.plain` 필수 필드를 채움 (schema.json 통과 가능). 추가로:
- `body.skt_iast`, `body.tib_wylie`, `body.tib_unicode`, `body.zh`, `body.ko`, `body.en`, `body.category`, `body.note`, `body.raw` 등 `equivalents` 전용 필드를 body 안에 포함.
- 이 필드들은 현재 `schema.json`의 `body.additionalProperties: false`를 위반함. **메인 세션에서 schema 확장**(equiv role용) 또는 **source_meta로 reshape** 필요.
- `verify.py`는 이대로 통과 안 함. 메인 세션이 schema 확장 후 다시 verify.

---

## 3. 추출 방법 요약

각 source당 `scripts/extract_equiv_<slug>.py` 추가:

```
scripts/extract_equiv_yogacara.py    # Tib + Chinese + Skt 3-언어 line-by-line
scripts/extract_equiv_hopkins.py     # Wylie headword + [tag] body, state machine
scripts/extract_equiv_karashima.py   # CJK headword + (pinyin) + "english" + K.<n>.<skt>
scripts/extract_equiv_4lang.py       # CJK + Tibetan(cid) + Sanskrit IAST + English
scripts/extract_equiv_bodkye.py      # DOCX paragraphs * <Tib>\t[skt], eng; ko
```

각 script 모두 `pdfplumber`/`python-docx` 사용. `scripts/lib/transliterate.py`의 `normalize`, `scripts/lib/reverse_tokens.py`의 `extract_en_tokens`/`extract_ko_tokens` 활용.

새 의존성: `pdfplumber`, `pypdf`, `openpyxl`, `python-docx`, `xlrd<2` (already added).

---

## 4. Skipped / 가치 없음 자료

### 4-A. v1과 중복 명백
- **`Mahavyutpatti/번역명의대집.xls`** (9,857 rows) — Sheet1 column 0이 numeric IDs + few headers뿐. v1 bilex Mvy (9,568)와 동일 source. **메인 세션 처리 중**.
- **`mahavyutpatti.ddbc.pdf`** (1448p, 9,553 entries) — DDBC Mvy. v1 bilex Mvy와 동일. **메인 세션 처리 중**.
- **`Bodkye/티벳어 동사 활용표.xls` + `[#haMsa TIBETAN]/haMsa Tibetan Verbs.xlsx`** (1,228 rows) — 동사 변화표 (현재/과거/미래/명령). 대응어가 아닌 conjugation. v2의 verb table은 Phase 6+ 별도 처리.

### 4-B. v1에 이미 모든 columns split됨 (THL .def)
- **`[#haMsa TIBETAN]/thl-dicts/thl.def` (22MB binary)** — UVA Tibetan Translator 데이터. Format: 2-byte BE length-prefixed fields, 20 columns per record (English / Other_English / Tenses / Sanskrit / Other_Tibetan / Def_Tibetan / Def_English / Div_Tibetan / Div_English / Syn_Tibetan / Syn_English / Comments / Ex_Tibetan / Ex_English / Yogacara_Bh_Gl / Dan_Martin / Jim_Valby / Ives_Waldo / Richard_Barron / Rangjung_Yeshe).
- **v1에 모든 18 columns가 이미 분리되어 있음**: `tib-jim-valby`, `tib-ives-waldo`, `tib-richard-barron`, `tib-rangjung-yeshe`, `tib-dan-martin`, `tib-yogacarabhumi` (= Yogacara_Bh_Gl col), `tib-hopkins-*` (Hopkins 7+ cols).
- **권장**: skip. THL의 모든 source가 이미 v1에 정제되어 있음.
- thl.wrd (6MB) = Tibetan headword → offset index. 사용 안함.

### 4-C. 자동 파싱 어려움
- **`[#haMsa TIBETAN]/TIB-SAN-ENG DICTIONARY.pdf` (UMA Hopkins/Hackett, 880p)** — Tibetan Unicode가 Wylie 위에 stacked overlay되어 PDF text extraction이 두 줄을 interleave시킴 (예: `'གླང་པpaོ་ཆr mེ་ལed་ས...'`). Layout-aware parser 또는 OCR 필요. Hopkins 변형이라 우리 `equiv-hopkins-tsed`로 거의 cover됨.
- **`[#haMsa TIBETAN]/Martin, Dan Tibskrit 2011.pdf` (2163p)** — Bibliography 형식 (책/저자 listing). 사전 entries가 아니라 references. Skip.

---

## 5. Tier C — 스캔 PDF (OCR 별도 작업 필요)

**OCR 직접 시도 안 함**. 사용자 결정/별도 세션 권장.

| 파일 | 페이지 | 크기 | 추정 가치 |
|---|---:|---:|---|
| `Hirakawa Akira-Buddhist-Chinese-Sanskrit-Dictionary.pdf` | ~2000? | 52 MB | 한자-Skt 불교사전. **매우 가치 높음**. Hirakawa Akira는 standard reference. |
| `Amarakoza/Ama914{1,2,3,4}__Amarasimha_*.pdf` | 4 vols | 138 MB total | Trivandrum Sanskrit Series 1914-17 Amarakośa with Kṣīrasvāmin/Sarvānanda commentaries. Sanskrit thesaurus. |
| `[DICS] SANSKRIT/Apte_PracticalSktEngDic.pdf` | — | 144 MB | v1에 `apte-sanskrit-english`로 이미 있음. Scan은 archival. |
| `[DICS] SANSKRIT/MonierWilliams_SktEngDic.pdf` | — | 232 MB | v1에 `monier-williams`로 이미 있음. |
| `[DICS] SANSKRIT/Edgerton.pdf` | — | 97 MB | BHSD. v1에 `bhsd`로 이미 있음. |
| `[DICS] SANSKRIT/sanskrit-wortebuch 1 (Turfan).pdf` + `2 k-dh` | — | 97 MB total | 산스크리트 → 독일어 Turfan 출토. v1의 `bopp` 등과 별개. **새 자료**. |
| `[DICS] SANSKRIT/梵和大辭典.pdf` | — | 217 MB | 산스크리트-일본어 대사전 (荻原雲来 *Bonwa Daijiten*). **OCR 가치 매우 높음** (산-일 미수록). |
| `불광사전워.pdf` | — | **2,084 MB** | 불광 대사전 (전자판). **거대**. OCR 시 전체 인덱싱 가능하면 가치 매우 큼. |
| `梵語佛典의硏究 (논서편).PDF` | — | 62 MB | 산스크리트 불전 연구서. 텍스트 PDF지만 구조 분석 필요. |
| `Tib_Sde dge_Tohoku_Catalogue.pdf` | — | **821 MB** | 데르게 Tohoku 목록. 사전이 아니라 catalog. |
| `[#haMsa TIBETAN]/Negi TIB to SAN/TSD_Negi_vol{01..16}.pdf` | 16 vols | 467 MB total | **메인 세션이 v1 equiv.sqlite Negi 처리 중 — 중복 금지** |
| `[#haMsa TIBETAN]/[DICS] TIBETAN/Tsepak Rigdzin .../File {1..30}.pdf` | 30 files | ~26 MB total | 모두 image-based. v1에 `tib-tsepak-rigdzin` (2,695 entries) 이미 있음. Skip. |
| `[#haMsa TIBETAN]/[DICS] TIBETAN/Tibetan Dictionaries/*.pdf` | — | ~750 MB total | BodgyaTsegdzodchenmo, Dag yig gsar bsgrigs, Dung dkar Tshig mdzod, Goldstein 사전들. v1과 일부 겹침 가능. 검토 필요. |
| `[#haMsa TIBETAN]/[DICS] TIBETAN/Jaeschke - A Tibetan-English Dictionary.pdf` | — | 96 MB | v1에 `tib-jaeschke-scan` 있음. 스캔본 동일. |
| `[#haMsa TIBETAN]/[DICS] TIBETAN/TibetanSanskritDic-LokeshChandra.pdf` | — | 176 MB | Lokesh Chandra Tibetan-Sanskrit. **메인 세션이 v1 equiv.sqlite LCh 처리 중 — 중복 금지**. |
| `[#haMsa TIBETAN]/[DICS] TIBETAN/Tib_Chn_Dict.pdf` | — | 138 MB | Tibetan-Chinese. v1에는 없음. **OCR 가치 있음**. |
| `토대종료.pdf` | — | 12 MB | **PDF corrupted** (`Unexpected EOF`). 파일 자체 복구 필요. |

**OCR 시 우선순위 (가치 순)**:
1. **Hirakawa Akira** (한자-Skt 불교사전, 52 MB)
2. **梵和大辭典** (산스-일본어 대사전, 217 MB) — 일본어 동의어 추가 가치
3. **Tib_Chn_Dict** (Tib-Chinese, 138 MB)
4. **Hopkins.ddbc** 제외한 sanskrit-wortebuch (Skt-독일어 Turfan)
5. **불광사전워** (불광 대사전, 2 GB) — 거대, OCR cost 고려

OCR engine 추천: Tesseract 5 (Sanskrit/Tibetan/Chinese language packs) 또는 Google Cloud Vision (정확도 높음).

---

## 6. Tier D — Apple .dictionary 파일들 (조사만)

**총 50+ .dictionary 폴더**가 `Sanskrit_Tibetan_Reading_Tools/` 최상위 + 하위 (`Dictionaries/`, `MAC DICT FILES/`, `OSX Sanskrit Dictionaries/`)에 산재.

대부분 **v1 dict.sqlite의 130 dicts에 이미 포함됨** (XDXF source 형식). 우리 v2 `data/sources/` 의 130개도 이를 그대로 사용.

확인된 candidates (이미 v1에 있음):
- `BHSD.dictionary` → `bhsd`
- `apte*.dictionary` → `apte-*`
- `mw-sa_apple_dict.dictionary` → `monier-williams`
- `amara*.dictionary` → `amarakosa-*`
- `kalpadruma-sa.dictionary` → `kalpadruma`
- `Tibetan Great Dictionary.dictionary` → `tib-tshig-mdzod-chen-mo` (있음!)
- `padamanjari/padamanjarI*.dictionary` → 메인 세션에 padamanjari로 추가 가능
- `Declension-*.dictionary` (~20개) → v1에 `decl-*` 있음

**아마 새 자료일 가능성**:
- `aShTAdhyAyI-anuvRtt_apple_dict_*.dictionary` / `aShTAdhyAyI-english_*.dictionary` → v2에 `ashtadhyayi-anuvrtti`, `ashtadhyayi-english` 있음 (이미)
- `pali-en-pa_apple_dict.dictionary` → v2에 `pali-english`
- `dhAtu-pATha-kRShNAchArya_apple_dict_*.dictionary` → v2에 `dhatupatha-krsnacarya`
- `umabiblio-JAN-2018.pdf` (1.5 MB) — UMA Bibliography. **사전이 아닌 reference**. Skip.

**Apple .dictionary 추출 방법** (메인 세션 또는 후속):
1. `Contents/Resources/Body.data` = gzip-compressed XHTML (decompile_all.sh 참고: `Dictionaries/decompile_all.sh`)
2. `Contents/Resources/KeyText.data` = binary plist (헤드워드 인덱스)
3. 도구: macOS의 `mdimport` + `osxdictsdk` 또는 Python `applescript` bridge.

이 작업 cost vs benefit 낮음 — v1에 거의 다 있음. **메인 세션이 결정**.

---

## 7. 다음 메인 세션에서 합칠 것 (체크리스트)

### 7-A. 즉시 통합
- [ ] `data/jsonl/equiv-karashima-lotus.jsonl` (2,320 rows) → build pipeline
- [ ] `data/jsonl/equiv-bodkye-hamsa.jsonl` (32 rows) → build pipeline
- [ ] `data/sources/equiv-karashima-lotus/meta.json`, `data/sources/equiv-bodkye-hamsa/meta.json` 등록

### 7-B. dedup 결정
- [ ] `equiv-yogacara-index` (54,452) vs `tib-yogacarabhumi` (16,028) → 어느 쪽을 사용할지 결정
  - 옵션 A: 우리 sense-detail 사용 (54K), v1 lemma 통합은 쓰지 않음
  - 옵션 B: v1 lemma 통합만 사용, 우리 거 skip
  - 옵션 C: 둘 다 별개 dict로 유지 (UI에서 lemma → senses expand)
- [ ] `equiv-hopkins-tsed` (18,600) vs v1 `tib-hopkins-*` (8개 split dicts) → 통합 vs split 형식 선택
- [ ] `equiv-lin-4lang` (2,411) vs `tib-common-terms-lin` (2,325) → v1이 더 깨끗하므로 v1 권장 (우리는 skip)

### 7-C. Schema
- [ ] `docs/schema.json`의 `body.additionalProperties: false`를 `equivalents` role 전용으로 확장. 또는 cross-lang fields를 `source_meta`로 reshape.
- [ ] `scripts/verify.py` 통과 확인.

### 7-D. Build pipeline
- [ ] `scripts/build_meta.py` — equiv-* slug들을 priority 25-49 band에 추가.
- [ ] `scripts/frequency.py` — equiv role rows의 priority weighting 검토.
- [ ] `scripts/build_reverse_index.py` — `reverse.en[]`/`reverse.ko[]` 토큰 통합.

---

## 8. 새 의존성 (이미 추가됨)

```toml
# pyproject.toml에 추가됨
"pdfplumber",
"pypdf",
"openpyxl",
"python-docx",
"xlrd<2",  # legacy .xls support
```

---

## 9. 보류 / 사용자 결정 필요

- **THL .def binary parsing** — 18 columns 모두 v1에 split되어 있어 추출 불필요. 만약 메인 세션이 다른 결론이면, format 분석은 본 보고서 §4-B 참고.
- **TIB-SAN-ENG (UMA Hopkins/Hackett) PDF** — 880p, layout 자동 파싱 불가. OCR 또는 layout-aware (column bbox 기반) re-extract 필요.
- **Apple .dictionary 50+** — 거의 모두 v1과 중복. 새 자료 골라낼 가치 낮음. 메인 세션 결정.
- **Tier C 스캔 PDFs** — OCR cost vs benefit 분석 후 사용자 결정. 추천 우선순위: Hirakawa Akira > 梵和大辭典 > Tib_Chn_Dict.

---

## 10. 추출 통계 (raw counts)

```
equiv-bodkye-hamsa.jsonl     :     32 rows ·  24 KB
equiv-hopkins-tsed.jsonl     : 18,600 rows ·  15 MB
equiv-karashima-lotus.jsonl  :  2,320 rows · 2.3 MB
equiv-lin-4lang.jsonl        :  2,411 rows · 1.7 MB
equiv-yogacara-index.jsonl   : 54,452 rows ·  29 MB
─────────────────────────────────────────────────
TOTAL                        : 77,815 rows ·  48 MB
```

JSONL 파일은 `.gitignore`로 제외 (CLAUDE.md §9 정책 준수). meta.json + extract scripts만 커밋.

---

**보고서 작성**: 2026-04-27 by Claude Opus 4.7
**관련 commit**:
- `3e04747` equiv 추출 (1/N): 유가사지론색인 PDF → 54,452 entries
- `7b64a5c` equiv 추출 (2/N): 4 source 추가 → 누적 77,815 rows
