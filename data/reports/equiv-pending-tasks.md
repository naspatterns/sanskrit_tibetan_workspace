# Equivalents (Zone B) — 메인 세션 잔여 작업

**현재 상태 (2026-04-28 기준)**:
- v1 baseline: 207K rows · 7 sources (commit `87b774e`) — `equiv-{mahavyutpatti,negi,lokesh-chandra,84000,hopkins,nti-reader,yogacarabhumi}`
- spawn 1 발굴 (`crazy-yalow-912f7c`): 77,815 rows · 5 sources (commit `2e54c8a`) — `equiv-{karashima-lotus,bodkye-hamsa,yogacara-index,hopkins-tsed,lin-4lang}`
- spawn 2 OCR (`compassionate-rosalind-d663ca`, **본 작업**): 160,874 rows · 5 sources (commits `e25c39a`, `16fec77`) — `equiv-{hirakawa,bonwa-daijiten,turfan-skt-de,tib-chn-great,amarakoza}`

**총합**: 약 **445K rows · 17 source dicts** (role=equivalents 16개 + role=thesaurus 1개).

verify.py: **0 errors / 160,874 entries** for equiv 5개 (146 dicts 전체 통과).

---

## 1. 메인 세션이 즉시 해야 할 일

### 1.1 `scripts/build_equivalents_index.py` 신규 작성 ⭐

**목표**: `role=equivalents` + `role=thesaurus` 모든 사전을 통합 → `public/indices/equivalents.msgpack.zst` (Zone B 전용 인덱스).

**입력** (17개 dict, glob 가능):
```bash
data/jsonl/equiv-*.jsonl  # 17 files
data/sources/equiv-*/meta.json  # 17 meta files
```

**출력 schema** (ARCHITECTURE.md §11.8.5 참조):
```
{
  "<headword_norm>": [
    {
      "source": "<slug>",          # e.g. "equiv-hirakawa"
      "skt_iast": "...",
      "tib_wylie": "...",
      "zh": "...",
      "ko": "...",
      "en": "...",
      "ja": "...",                  # NEW (Bonwa Daijiten 100K rows)
      "de": "...",                  # NEW (Turfan SWB 11K rows)
      "category": "...",
      "note": "..."
    },
    ...
  ]
}
```

**참고 코드** (v1):
- `../sanskrit_tibetan_reading_workspace/docs/app.js:254-336` (`mergeBilexResults` 패턴)
- `../sanskrit_tibetan_reading_workspace/docs/app.js:815-` (`renderEquivEntry`)

**빌드 실행 후 확인**:
```bash
uv run python -m scripts.build_equivalents_index
ls -lh public/indices/equivalents.msgpack.zst
# 추정 크기: ~30-40 MB (445K rows × ~80 byte avg)
```

### 1.2 `scripts/build_meta.py` 갱신

5 새 슬러그 등록 추가:
- `equiv-hirakawa` (priority 30, lang=zh)
- `equiv-bonwa-daijiten` (priority 31, lang=skt)
- `equiv-tib-chn-great` (priority 32, lang=bo)
- `equiv-turfan-skt-de` (priority 33, lang=skt)
- `equiv-amarakoza` (priority 49, lang=skt, role=thesaurus, tier=3)

이미 `data/sources/equiv-*/meta.json` 직접 작성됨 — `build_meta.py`가 이들을 *덮어쓰지 않게* 하든지 (skip if exists), 동일한 priority로 재생성하게 하든지 결정 필요.

### 1.3 `scripts/frequency.py` priority weighting 검토

`role=equivalents`/`role=thesaurus` rows를 top-10K headword 빈도 가중치에 어떻게 포함할지 결정 (ARCHITECTURE.md §11.8.4).

---

## 2. 데이터 품질 후속 (선택 / 우선순위 낮음)

### 2.1 Tib_Chn Wylie 정확도 향상 (현 근사 → 표준 EWTS)

**현 상태**: `scripts/lib/tibetan_wylie.py` 자체 변환기, 30,851 rows 변환됨. char-by-char 매핑 + syllable-end 'a' 보충. **root-letter 식별 안 함**.

**예시 차이**:
- 표준: `bstan` (b-prefix + s-super + t-root + a-vowel + n-suffix)
- 현재: `bstna` (낱자 끝에 'a' 부착)

**개선 방법** (선택 시):
```bash
uv add pyewts --extra-build-dependencies setuptools  # OR
uv add botok  # Tibetan tokenizer with built-in Wylie
```

빌드 이슈가 있다면 (이번 spawn 사례), 다음 시도:
- `uv add pyewts --frozen` + 수동 setup 패치
- 또는 `pyewts`-fork (PyPI에 newer fork 있을 수 있음)

`scripts/postprocess_tib_chn_wylie.py`의 `to_wylie` 호출만 교체.

### 2.2 Hirakawa 노이즈 페이지 필터 (선택)

**현 상태**: 16,851 rows 중 ~109 rows가 conf < 60 (대부분 preface 페이지의 OCR 잡음).

**필터 옵션**:
```python
# data/jsonl/equiv-hirakawa.jsonl 후처리
import json
ok = [r for r in rows if r['source_meta']['ocr_conf'] >= 60 and len(r['headword']) <= 8]
# → 약 14,500 rows로 축소 (15% 절감)
```

OR: build_equivalents_index.py에서 query-time 필터로 처리.

### 2.3 Amarakośa verse-level NLP (별도 작업)

**현 상태**: `equiv-amarakoza` 1,119 rows (페이지당 1 row, raw text dump).

**필요한 작업**:
1. Sanskrit verse boundary detection (` ॥` 마커)
2. Lemma identification (compound 분해)
3. Topic group inference (kāṇḍa.varga)
4. → `role=thesaurus` 동의어 group rows 재생성

**도구 후보**:
- Sanskrit parser: `vidyut-prakriya`, `parashara`, `dharmamitra`
- Or: Custom Devanagari NLP

이 작업은 산스 학술 NLP 별도 spawn 권장.

---

## 3. 미처리 자료 (사용자 결정 필요)

### 3.1 불광사전워.pdf (2 GB)

- 한자 불교 대사전, OCR 가치 큼
- Tesseract 시도 시 ~12+ hours, conf 우려
- **권장**: Google Cloud Vision API (~$3, 한자 OCR 정확도 critical)
- 별도 spawn 권장

### 3.2 梵語佛典의硏究 (논서편).PDF (62 MB)

- 산스 불전 연구서 (사전이 아닌 단행본)
- 사전성 검토 필요 — 대응어 추출 가치 미정

---

## 4. 통합 검증 (메인 세션 작업 완료 후)

```bash
# 1. 빌드
uv run python -m scripts.build_meta
uv run python -m scripts.build_equivalents_index   # 신규
uv run python -m scripts.frequency                  # priority 재계산

# 2. verify
uv run python -m scripts.verify
# 기대: 0 errors, ~50K warnings (FB-4 IAST hint, OCR data 특성)

# 3. bench (Zone B 단독 측정)
# bench/index.html에 equivalents-load 시나리오 추가
```

---

## 5. ADR-009 재검토 트리거

ROADMAP.md ADR-009 §재검토 시점에 명시: "spawn_task의 `Sanskrit_Tibetan_Reading_Tools` 발굴 결과 통합 후 + Phase 3 LCP 재측정. Zone B 비대 시 `equivalents.msgpack.zst`도 source별 shard 검토."

**현재 통합 후 추정**:
- Zone B 단일 인덱스 ~30-40 MB compressed → decompressed ~250 MB
- JS heap 영향: ~50-100 MB 추정
- 모바일 임계 (60 MB target) 초과 시 source별 shard 분할 검토

---

**작성**: 2026-04-28 by spawn `compassionate-rosalind-d663ca`
**관련 commits**: `e25c39a`, `16fec77` (이전 incremental 28개 commits 포함)
**상세 OCR 리포트**: [data/reports/equiv-ocr-extraction.md](equiv-ocr-extraction.md)
