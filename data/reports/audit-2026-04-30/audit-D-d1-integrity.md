# audit-D-d1-integrity — Phase 5 D1 + Edge API verification

- API origin: `https://stw-api.naspatterns.workers.dev`
- Method: HTTP GET via urllib

- **Health**: ✅ (`/api/health` returned in 458ms)

## Search probes

| # | Name | Query | Expected ≥ | Got | Latency | Verdict |
|---|---|---|---:|---:|---:|---|
| 1 | dharma (canonical, in tier0) | `dharma` | 5 | 10 | 602ms | ✅ |
| 2 | agni (canonical) | `agni` | 5 | 10 | 584ms | ✅ |
| 3 | vajracchedika (Sentinel ❌ → ✅) | `vajracchedika` | 1 | 2 | 732ms | ✅ |
| 4 | surangama (Sentinel ❌ → ✅) | `surangama` | 1 | 2 | 772ms | ✅ |
| 5 | prajna | `prajna` | 5 | 10 | 586ms | ✅ |
| 6 | buddha | `buddha` | 5 | 10 | 610ms | ✅ |
| 7 | bodhisattva | `bodhisattva` | 5 | 10 | 599ms | ✅ |
| 8 | rabidlydoesntexistaaa | `rabidlydoesntexistaaa` | 0 | 0 | 729ms | ✅ |

## Latency stats

- p50: 606ms
- max: 772ms
- mean: 652ms
- N: 8

