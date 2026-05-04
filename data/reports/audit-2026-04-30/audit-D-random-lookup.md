# audit-D-random-lookup — 통계적 인덱스 샘플링 검증

각 인덱스에서 무작위 100개 key를 추출해 lookup 정상 여부 측정.
100% hit가 정상. <100%는 버그 (Map.get이 빈/잘못된 결과 반환).

- Random seed: 42 (deterministic across runs)

| Index | Hits | Total | Hit Rate | Index Size |
|---|---:|---:|---:|---:|
| `tier0` | 100 | 100 | 100% | 10,000 |
| `tier0-extended` | 100 | 100 | 100% | 10,000 |
| `tier0-bo` | 100 | 100 | 100% | 10,000 |
| `reverse_en` | 100 | 100 | 100% | 317,884 |
| `reverse_ko` | 100 | 100 | 100% | 20,962 |
| `equivalents` | 100 | 100 | 100% | 424,820 |
| `headwords` | 100 | 100 | 100% | 1,071,112 |

**결과**: 모든 인덱스 100% lookup 정상 ✅

