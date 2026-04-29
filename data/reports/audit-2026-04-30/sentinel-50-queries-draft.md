# Sentinel 50 — Track C 검색 시나리오 후보

**용도**: Track C에서 production preview build (`vite preview`) 가동 후 50개 query를 직접 입력해 결과 정확도·우선순위·zone 표시·UX 흐름을 평가합니다.

**평가 항목** (각 query별로 기록):
- 결과가 의미적으로 맞는가? (top-3 안에 정답 있나)
- Zone A (정의) / Zone B (대응어) / 역검색 / 자동완성이 적절히 구분 표시되는가?
- 우선순위 정렬 정상? (Apte 1 → MW 2 → Macdonell 3 등)
- Snippet 잘림 적절한가? (FB-1 short ≤180, medium ≤500)
- 검색 latency 체감?
- 모바일 ≤768px에서 가독성?

---

## 카테고리 분포 (50 queries)

| 카테고리 | 개수 | 목적 |
|---|---:|---|
| 1. 산스크리트 핵심 단어 (IAST 입력) | 10 | tier0 정의 + equivalents 회수 정확도 |
| 2. 산스크리트 prefix / 자동완성 | 5 | headwords.txt 기반 prefix 검색 |
| 3. 티벳어 Wylie 입력 | 5 | tier0-bo 정의 + equivalents (Wylie 채널) |
| 4. 영어 역검색 | 10 | reverse_en — P1-1 fix 후 기대값 |
| 5. 한국어 역검색 | 5 | reverse_ko — coverage 한계 노출 |
| 6. 한자 역검색 | 5 | equivalents zh 채널 |
| 7. 혼용·sandhi·고유명 | 5 | edge case 처리 |
| 8. typo / 잘못된 입력 | 3 | UX feedback (안내 메시지) |
| 9. exclude_from_search 누출 | 2 | 곡용표 사전이 결과에 안 나오는지 |

---

## 카테고리 1 — 산스크리트 핵심 (10)

| # | Query | 기대 top-3 | 채널 | 비고 |
|---|---|---|---|---|
| 1 | `dharma` | Apte/MW/Macdonell `dharma` 정의 | tier0 | 가장 흔한 단어, priority 정렬 검증 |
| 2 | `ātman` | Apte/MW `ātman` (영혼/자아) | tier0 | diacritic 입력 |
| 3 | `karman` | Apte/MW `karman` | tier0 | n-stem |
| 4 | `agni` | Apte/MW `agni` (불) | tier0 | 베다 핵심어 |
| 5 | `prajñā` | Apte/MW `prajñā` (지혜) | tier0 | ñ diacritic |
| 6 | `śūnyatā` | MW `śūnyatā` | tier0 | 불교 용어 |
| 7 | `bodhicitta` | MW `bodhicitta` | tier0 | 복합어 |
| 8 | `tathāgata` | MW `tathāgata` | tier0 | 불교 칭호 |
| 9 | `mokṣa` | Apte/MW `mokṣa` | tier0 | ṣ diacritic |
| 10 | `saṃskāra` | Apte/MW `saṃskāra` | tier0 | ṃ + ā |

## 카테고리 2 — Prefix 자동완성 (5)

| # | Query | 기대 자동완성 (≥3건) | 비고 |
|---|---|---|---|
| 11 | `dha` | dharma, dhātu, dhana, dhī, dhairya … | 흔한 prefix |
| 12 | `bud` | buddha, buddhi, buddhānusmṛti … | 불교 |
| 13 | `pra` | prajñā, pratyaya, pratīyasamutpāda … | 가장 큰 prefix bucket |
| 14 | `ana` | anātman, anitya, ānanda … | a-prefix 부정 |
| 15 | `māhā` (오타로 두번째 글자 ā) | (자동완성 비호환 테스트) | norm 처리 검증 |

## 카테고리 3 — 티벳어 Wylie (5)

| # | Query | 기대 top-3 | 채널 | 비고 |
|---|---|---|---|---|
| 16 | `chos` | RY/Hopkins/84000 chos (=dharma) | tier0-bo | 가장 흔한 |
| 17 | `byang chub sems dpa'` | bodhisattva 대응어 | tier0-bo | space + apostrophe |
| 18 | `klong chen` | klong chen rab 'byams | tier0-bo | Phase 3.3 검증 케이스 |
| 19 | `rdo rje` | vajra 대응어 | tier0-bo / equivalents | bo→skt 매핑 |
| 20 | `'jam dpal` | mañjuśrī 대응어 | tier0-bo | apostrophe 시작 |

## 카테고리 4 — 영어 역검색 (10)

> **주의**: P0-1 fix (entry_id → headword 렌더링) + P1-1 fix (priority sort) 적용 후 측정해야 함. fix 전 측정값은 baseline.

| # | Query | 기대 (top-5에 나와야) | 비고 |
|---|---|---|---|
| 21 | `fire` | agni | 가장 기본 |
| 22 | `wisdom` | prajñā, jñāna | (현재 ✅ wisdom→bodhiḥ) |
| 23 | `compassion` | karuṇā | 불교 핵심 |
| 24 | `emptiness` | śūnyatā | 불교 |
| 25 | `liberation` | mokṣa, mukti | |
| 26 | `meditation` | dhyāna, samādhi | |
| 27 | `enlightenment` | bodhi, sambodhi | |
| 28 | `suffering` | duḥkha | |
| 29 | `consciousness` | vijñāna, citta | |
| 30 | `righteousness` | dharma | dharma의 윤리적 의미 |

## 카테고리 5 — 한국어 역검색 (5)

> **주의**: P1-2 (한국어 coverage 부족) 인지된 상태에서 어떤 query가 hit / miss인지 baseline.

| # | Query | 기대 (top-5에) | 현재 측정 |
|---|---|---|---|
| 31 | `법` | dharma | ✅ A4에서 hit |
| 32 | `자비` | karuṇā | ❌ A4 0 hits — coverage 부족 |
| 33 | `지혜` | prajñā, jñāna | ❌ A4 73 hits but mis-ranked |
| 34 | `도` | mārga | ❌ A4 0 hits |
| 35 | `불` | agni 또는 buddha | ❌ A4 mis-rank |

## 카테고리 6 — 한자 역검색 (5)

| # | Query | 기대 (equivalents zh 채널) | 비고 |
|---|---|---|---|
| 36 | `法` | dharma | (한자 → 산스크리트) |
| 37 | `空` | śūnyatā | |
| 38 | `菩薩` | bodhisattva | 복합 한자 |
| 39 | `涅槃` | nirvāṇa | |
| 40 | `如來` | tathāgata | |

## 카테고리 7 — 혼용·sandhi·고유명 (5)

| # | Query | 기대 | 검증 포인트 |
|---|---|---|---|
| 41 | `mahābhārata` | epic 인용 매핑 | 고유명 |
| 42 | `jagannātha` | Apte/MW jagannātha | sandhi 융합 |
| 43 | `tat tvam asi` | (전형 mahāvākya) | space + 짧은 단어 |
| 44 | `oṃ` | oṃ + om 변이형 | 짧은 단어 |
| 45 | `aham brahmāsmi` | 우파니샤드 인용 | 다단어 |

## 카테고리 8 — Typo / Edge (3)

| # | Query | 기대 동작 |
|---|---|---|
| 46 | `dharmaaa` | 자동완성 또는 "결과 없음" 안내 |
| 47 | `aaa` | 빈 결과 graceful 처리 |
| 48 | `   ` (공백만) | 초기 상태 (검색 안 됨) |

## 카테고리 9 — Dead zone 검증 (2)

| # | Query | 기대 |
|---|---|---|
| 49 | `decl-a01` | 결과 0건 — 곡용 사전 검색에서 빠져야 |
| 50 | `aṃśanīya@aṃś` | 결과 0건 (Heritage decl 형식) — 검색 X, 곡용탭에서만 보여야 |

---

## 측정 방법 (Track C 시점)

1. `npm run preview` 가동 → http://localhost:4173
2. 50개 query를 차례로 입력
3. 각 query별로 `data/reports/audit-2026-04-30/audit-C-sentinel-results.csv`에 기록:
   - query / category / top-3 retrieved / verdict (✅/⚠️/❌) / notes / latency
4. 종합 점수: 50개 × 1점 = 50점 만점
5. P0/P1 fix 후 재측정 → before/after 비교

---

## 사용자 검토 요청

다음 사항 검토 부탁:

1. **카테고리 분포 적절한가?** (1-9번 분류)
2. **추가/변경할 query 있나?** (특히 산스크리트 학자 관점에서 빠진 핵심어)
3. **카테고리 4·5의 baseline 측정만 할 것인지, 아니면 P1 fix 후에만 측정할 것인지?** (제 권장: baseline 먼저, fix 후 비교)
4. **카테고리 9 (dead zone)에 추가할 표제어?**

검토 완료되면 Track C에서 실측 시작합니다.
