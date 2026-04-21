# Dictionary Source Plugin Spec

각 사전 = 독립 디렉터리 `data/sources/<slug>/`. 다음 파일을 가져야 함:

```
data/sources/<slug>/
├── meta.json           ← 사전 메타데이터
├── parse.py            ← 원본 → JSONL 변환 (사전별)
├── source.<ext>        ← 원본 파일 (gitignored)
└── entries.jsonl       ← parse.py 산출물 (gitignored)
```

## meta.json

```json
{
  "slug": "apte-sanskrit-english",
  "name": "Apte Practical Sanskrit-English Dictionary",
  "short_name": "Apte",
  "lang": "skt",
  "target_lang": "en",
  "priority": 1,
  "tier": 1,
  "family": "apte",
  "license": "public-domain",
  "source_format": "xdxf",
  "source_url": "https://www.sanskrit-lexicon.uni-koeln.de/scans/AP90Scan/",
  "edition": "1890",
  "import_script": "parse.py",
  "expected_entries": 60000,
  "input_script": "iast",
  "sense_separator": ";|-[0-9]+|\\s[0-9]+\\.\\s"
}
```

### 필드 설명
- **slug**: URL-safe 식별자. 디렉터리명과 일치.
- **name / short_name**: 표시명 (긴 / 짧은).
- **lang**: 표제어 언어 (`skt`, `bo`, `zh`, `pi` 등).
- **target_lang**: 정의문 언어 (`en`, `de`, `fr`, `la`, `ru`, `ko`, `mixed` 등).
- **priority**: **1-100 정수. 낮을수록 검색 결과 상단**. Apte=1, MW=2, Macdonell=3, BHSD=4.
  UI 정렬의 1순위 키. tier와 독립 (tier는 펼침 여부, priority는 순서).
- **tier**: 1(auto-expand) / 2(expand on match) / 3(collapsed). UI 펼침 상태.
- **family**: 같은 사전의 다른 판본 그룹 (예: `mw`, `apte`, `heritage-decl`).
- **license**: SPDX. 공개 가능 여부 결정.
- **source_format**: `xdxf`, `csv`, `apple_dict`, `gretil_html`, `sandic_xml` 등.
- **input_script**: `iast`, `hk`, `devanagari`, `wylie`, `mixed`.
  parse.py가 IAST 변환 시 참조. `mixed` 인 경우 per-entry 감지.
- **expected_entries**: 검증용. parse.py 출력이 ±5% 벗어나면 실패.
- **sense_separator** (선택): 정규식. body를 senses 배열로 파싱할 때 사용.
  MW/Apte 는 `;` + 번호 패턴. 없으면 sense 분리 생략.

### priority 가이드라인

```
 1- 9:  Sanskrit-English/German 주요 학술 사전 (Apte, MW, Macdonell, BHSD, ...)
10-19:  Sanskrit-Sanskrit 사전 (Kalpadruma, Vacaspatyam, ...)
20-29:  Tibetan 주요 (RangjungYeshe, Hopkins, 84000, tshig-mdzod-chen-mo)
30-49:  Tibetan 전문 + Pali + 기타 언어
50-69:  Sanskrit tier 2 (전문 분야별)
70-89:  Declension tables, morphology, 파생 자료
90-99:  Archival, 중복, low-quality
```

같은 priority 허용. 동점 시 tier → entry_count → alphabetical 순.

## parse.py 인터페이스

```python
# data/sources/<slug>/parse.py
from pathlib import Path
from typing import Iterator
from nighantu.types import Entry  # 공통 타입

def parse(source_path: Path, meta: dict) -> Iterator[Entry]:
    """원본 파일 → 표준 Entry 객체 generator.
    
    각 Entry는 schema.json에 부합해야 함.
    headword_norm은 nighantu.normalize.normalize_headword()로 자동 생성됨.
    """
    ...
```

공통 정규화 (`headword_norm`, `headword_iast`, `snippet_*`)는 파이프라인이 자동 처리.
parse.py는 raw 데이터 추출만 책임.

## 파이프라인 실행

```bash
# 단일 사전 빌드
python3 -m nighantu.build monier-williams

# 전체 빌드
python3 -m nighantu.build --all

# 특정 사전만 재빌드 (다른 사전 영향 없음)
python3 -m nighantu.build mvy --force
```

각 빌드는:
1. `meta.json` 검증
2. `parse.py` 실행 → entries.jsonl
3. 공통 정규화 적용
4. JSON Schema 검증
5. 통계 출력 (entry count, file size)

## 새 사전 추가 워크플로우

```bash
# 1. 디렉터리 생성
mkdir data/sources/my-new-dict
cd data/sources/my-new-dict

# 2. meta.json 작성
$EDITOR meta.json

# 3. parse.py 작성 (기존 parse_xdxf.py 등 참조)
$EDITOR parse.py

# 4. 원본 파일 배치
cp ~/Downloads/my-dict.xdxf source.xdxf

# 5. 빌드 + 검증
python3 -m nighantu.build my-new-dict
python3 -m nighantu.verify my-new-dict

# 6. 인덱스 재생성
python3 scripts/build_tier0.py     # 새 사전이 top-10K에 진입할 수 있음
python3 scripts/build_fst.py       # 새 headword 추가
```

다른 사전 재빌드 불필요. 다른 사람의 `data/sources/`에는 영향 없음.
