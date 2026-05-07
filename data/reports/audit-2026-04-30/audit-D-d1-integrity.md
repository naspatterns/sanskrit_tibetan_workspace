# audit-D-d1-integrity — Phase 5 D1 + Edge API verification

- API origin: `https://stw-api.naspatterns.workers.dev`
- Method: HTTP GET via urllib

- **Health**: ✅ (`/api/health` returned in 458ms)

## Search probes

| # | Name | Query | Expected ≥ | Got | Latency | Verdict |
|---|---|---|---:|---:|---:|---|
| 1 | dharma (canonical, in tier0) | `dharma` | 5 | 10 | 2209ms | ✅ |
| 2 | agni (canonical) | `agni` | 5 | 10 | 614ms | ✅ |
| 3 | vajracchedika (Sentinel ❌ → ✅) | `vajracchedika` | 1 | 2 | 757ms | ✅ |
| 4 | surangama (Sentinel ❌ → ✅) | `surangama` | 1 | 2 | 760ms | ✅ |
| 5 | prajna | `prajna` | 5 | 10 | 614ms | ✅ |
| 6 | buddha | `buddha` | 5 | 10 | 581ms | ✅ |
| 7 | bodhisattva | `bodhisattva` | 5 | 10 | 604ms | ✅ |
| 8 | rabidlydoesntexistaaa | `rabidlydoesntexistaaa` | 0 | 0 | 749ms | ✅ |

## Latency stats

- p50: 681ms
- max: 2209ms
- mean: 861ms
- N: 8

