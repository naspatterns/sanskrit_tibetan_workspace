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
  "slug": "monier-williams",
  "name": "Monier-Williams Sanskrit-English Dictionary",
  "short_name": "MW",
  "lang": "skt",
  "target_lang": "en",
  "tier": 1,
  "family": "mw",
  "license": "public-domain",
  "source_format": "xdxf",
  "source_url": "https://www.sanskrit-lexicon.uni-koeln.de/",
  "edition": "1899",
  "import_script": "parse.py",
  "expected_entries": 161000,
  "input_script": "iast"
}
```

### 필드 설명
- **slug**: URL-safe 식별자. 디렉터리명과 일치.
- **name / short_name**: 표시명 (긴 / 짧은).
- **lang**: 표제어 언어 (`skt`, `bo`, `zh` 등).
- **target_lang**: 정의문 언어 (`en`, `de`, `ko`, `mixed` 등).
- **tier**: 1(주요) / 2(전문) / 3(보조). UI 기본 펼침 결정.
- **family**: 같은 사전의 다른 판본 그룹 (예: `mw`, `apte`, `heritage-decl`).
- **license**: SPDX. 공개 가능 여부 결정.
- **source_format**: `xdxf`, `csv`, `apple_dict`, `gretil_html`, `sandic_xml` 등.
- **input_script**: `iast`, `hk`, `devanagari`, `wylie`, `mixed` — parse.py가 알아야 하는 정보.
- **expected_entries**: 검증용. parse.py 출력이 ±5% 벗어나면 실패.

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
