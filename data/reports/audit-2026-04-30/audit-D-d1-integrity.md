# audit-D-d1-integrity — Phase 5 D1 + Edge API verification

- API origin: `https://stw-api.naspatterns.workers.dev`
- Method: HTTP GET via urllib

- **Health**: ✅ (`/api/health` returned in 433ms)

## Search probes

| # | Name | Query | Expected ≥ | Got | Latency | Verdict |
|---|---|---|---:|---:|---:|---|
| 1 | dharma (canonical, in tier0) | `dharma` | 5 | 10 | 589ms | ✅ |
| 2 | agni (canonical) | `agni` | 5 | 10 | 578ms | ✅ |
| 3 | vajracchedika (Sentinel ❌ → ✅) | `vajracchedika` | 1 | 2 | 710ms | ✅ |
| 4 | surangama (Sentinel ❌ → ✅) | `surangama` | 1 | 2 | 796ms | ✅ |
| 5 | prajna | `prajna` | 5 | 10 | 613ms | ✅ |
| 6 | buddha | `buddha` | 5 | 10 | 559ms | ✅ |
| 7 | bodhisattva | `bodhisattva` | 5 | 10 | 564ms | ✅ |
| 8 | rabidlydoesntexistaaa | `rabidlydoesntexistaaa` | 0 | 0 | 823ms | ✅ |

## Latency stats

- p50: 601ms
- max: 823ms
- mean: 654ms
- N: 8

