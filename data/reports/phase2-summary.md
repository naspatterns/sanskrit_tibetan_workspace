# Phase 2 Summary — 2026-04-22 + 04-23

ROADMAP Phase 2 (Tier 0 + FST + 번역 보완) 완료. 후속 Korean 번역 배치는 POC 100/9995 상태.

## 완료된 작업

### 2.1 빈도 결정 (`scripts/frequency.py`)
- Priority-가중 (priority 1 → weight 1.0, 99 → 0.01) × 엔트리 카운트
- 출력: `data/reports/top10k.txt` (상위 10K headword_norm, 알파벳 순)
- 956K 유니크 headwords 채점, 17s
- Top 20: `su, nir, sa, a, mahaa, dur, para, prati, go, deva, ...`

### 2.4 역인덱스 빌드 (`scripts/build_reverse_index.py`)
- Inline `reverse.en[]` / `reverse.ko[]` 집계 (Phase 1에서 이미 추출된 토큰)
- Bounded heap: 토큰당 상위 100 entry-ids (priority ASC)
- `min_freq=3` 필터 (long-tail noise 제거)
- 산출:
  - `public/indices/reverse_en.msgpack.zst` — **14.8 MB**, 318,221 토큰
  - `public/indices/reverse_ko.msgpack.zst` — **92 KB**, 532 토큰
- 검증: `fire` → 100 Apte entries priority-sorted; `법` → 100 PWK entries

### 2.3b FST 자동완성 준비 (`scripts/build_fst.py`)
- 정렬된 유니크 `(headword_norm, headword_iast)` 쌍
- 산출: `public/indices/headwords.txt.zst` — **6.6 MB** (raw 32 MB, 20% ratio)
- 956K headwords
- Phase 3 클라이언트가 `mnemonist/fst` 또는 fzf-wasm으로 쓰는 입력

### 2.3a Tier 0 인덱스 빌드 (`scripts/build_tier0.py`)
- Top-10K × 모든 search-enabled dict → long-key 스키마
- 엔트리 구조 (Phase 3 UI 커플링 최소화 위해 장식 키 대신 가독성 선택):
  ```
  {
    iast: "dharma",
    entries: [
      {
        dict: "apte-sanskrit-english",
        short: "Apte",
        priority: 1,
        tier: 1,
        id: "apte-sanskrit-english-000042",
        snippet_short: "...",
        snippet_medium: "...",
        ko: "...",
        target_lang: "en",
      },
      ...
    ]
  }
  ```
- 산출: `public/indices/tier0.msgpack.zst` — **27.4 MB** compressed (raw 179 MB)
- 10K headwords × avg 35.6 entries/hw = 355,648 entries

### 2.5 벤치마크 (`scripts/bench.py`)
- Cold load (decompress + msgpack): **606-641 ms** (target <2s 4G ✅)
- Hit lookup: **0.2 µs median, 0.3 µs p95** (target <50 ms ✅)
- 전체 인덱스 크기: **48.9 MB** (타겟 ~50 MB 이내 ✅)

### 2.2 번역 batch 파이프라인 (`scripts/translate_batch.py`)
- Anthropic Batch API 4-step wrapper (`prepare/submit/poll/retrieve`)
- 안전장치 (리뷰 반영):
  - Submit 이중 제출 방지 (`batch_state.json` 체크 + `--force`)
  - Retrieve atomic tmp+rename + append-resume (데이터 손실 방지)
  - Failure 로그 `failures.jsonl` 별도 기록
  - Poll `--max-wait-seconds` 타임아웃
  - API 에러 catch + batch_id stderr dump
- Model: `claude-sonnet-4-6` (`--model` 플래그로 오버라이드)
- 9,995 requests prepared (`data/translations/requests.jsonl`), 예상 비용 ~$6.31

## 후속 번역 배치 POC (subagents)

API 대신 Claude Code 서브에이전트로 병렬 번역 실시험:
- 3 agent × 50 chunk 목표 → 2 완료 (100 번역), 1 지연·포기
- 품질 확인: IAST `dharma`·`ātman` 유지, 약어 `m./f./n./cf.`, 인용 `Mn./RV./Bg.`, 번호 매김 구조 전부 보존
- 샘플:
  - `agre` → "앞에, (시간·공간상) 이전에... 처음에, 최초로"
  - `aka` → "구불구불하게 움직이는"
  - `akṣauhiṇī` → "21,870대의 전차, 같은 수의 코끼리, 65,610명의 기병, 109,350명의 보병으로 구성된 대군"
- 병합 → `data/translations.jsonl` (100 entries, 커밋됨)
- Tier 0 재빌드 반영

## 리뷰 라운드 (B + A × 3 agents)

**Light B (design/safety)** 3 critical fix:
- `translate_batch.submit` double-billing 방지
- `translate_batch.retrieve` 손실 방지 (atomic + resume)
- `translate_batch.poll` infinite loop 방지

**Simplify A (reuse/quality/efficiency)** 주요 적용:
- `lib/io.py` 헬퍼 4개 추가 (`write_msgpack_zst`, `load_zst_msgpack`, `iter_slugs_by_priority`, `load_top10k`)
- `_require_client()` 헬퍼 (API key guard 3중 중복 제거)
- `build_tier0` long-key 스키마 (Phase 3 가독성)
- `build_tier0` whitespace-only `ko` strip
- `build_tier0` slug 정렬 invariant assert
- Narrating 주석 및 미사용 import 정리
- Hot-path 최적화 (snippet short-body 단락, audit substring filter)

**Deferred (Phase 3 이후 재검토)**:
- Multiprocessing × 4 builders (extract/verify 패턴; 5× 속도 향상 가능)
- jsonschema → fastjsonschema (verify는 이미 적용 완료 Phase 1)
- DE/FR/LA 전체 재번역 (~$225 via batch) — 사용자 결정 보류

## 산출물 파일 목록

### Committed
```
scripts/lib/io.py (확장 — 4 helpers 추가)
scripts/frequency.py
scripts/build_reverse_index.py
scripts/build_fst.py
scripts/build_tier0.py
scripts/translate_batch.py
scripts/bench.py
data/reports/top10k.txt
data/reports/phase2-benchmark.md
data/translations.jsonl (POC 100 entries)
pyproject.toml (+ fastjsonschema, anthropic)
uv.lock
```

### Gitignored (재생성 가능)
```
data/translations/chunks/chunk_000~199.jsonl (200개)
data/translations/results/result_000~001.jsonl (POC)
data/translations/requests.jsonl
public/indices/tier0.msgpack.zst
public/indices/reverse_en.msgpack.zst
public/indices/reverse_ko.msgpack.zst
public/indices/headwords.txt.zst
```

## 지표 요약

| 항목 | 값 |
|---|---|
| 인덱스 빌드 총 시간 | ~2분 (frequency 17s + reverse 73s + fst 27s + tier0 88s) |
| Tier 0 cold load | 606-641 ms |
| Hit lookup | 0.2 µs median |
| 전체 인덱스 용량 | 48.9 MB compressed |
| Top-10K coverage | 10K headwords × 35.6 avg entries |
| Unique en reverse tokens | 318,221 |
| Unique ko reverse tokens | 532 (v1 body_ko 제한; Phase 2b 확장 예정) |
| POC Ko translations | 100 / 9,995 (1%, 나머지 pending) |

## Phase 3 준비 상태

Phase 3에서 소비할 인덱스는 전부 준비됨:
- `public/indices/tier0.msgpack.zst` — top-10K 엔트리 사전 렌더링
- `public/indices/reverse_en.msgpack.zst` — 영어 역검색
- `public/indices/reverse_ko.msgpack.zst` — 한국어 역검색
- `public/indices/headwords.txt.zst` — 자동완성 기본 재료

장기 과제 (Phase 2b 완료 후):
- 10K 번역 완성되면 `data/translations.jsonl` 갱신 → `build_tier0` 재실행 → 27.4 MB 유지 예상

## 다음 단계

- **Phase 3 시작**: `ROADMAP.md §Phase 3` 참조 (SvelteKit + nanostores + OKLCH 다크모드)
- **Phase 2b 마무리**: 9,895 Korean 번역 (spawn_task 또는 batch API)
- **Phase 3.5 Declension 탭**: Phase 3 완료 후
