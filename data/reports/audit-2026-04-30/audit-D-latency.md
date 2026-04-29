# audit-D-latency — D5 v2 full 7-index latency profile

Date: 2026-04-30
Method: Python `time.perf_counter_ns` × 1000 queries × 5 rounds per index

## Cold load (Python msgpack/zstd, single thread)

| Index | Size (MB) | Cold load (ms) | Keys |
|---|---:|---:|---:|
| `tier0.msgpack.zst` | 28.53 | 680.0 | 10,000 |
| `tier0-bo.msgpack.zst` | 7.07 | 188.5 | 10,000 |
| `equivalents.msgpack.zst` | 13.24 | 778.3 | 480,732 |
| `reverse_en.msgpack.zst` | 14.82 | 490.4 | 317,878 |
| `reverse_ko.msgpack.zst` | 0.14 | 5.7 | 3,102 |
| `declension.msgpack.zst` | 2.07 | 67.5 | 7,438 |
| `headwords.txt.zst` | 7.76 | 141.2 | 1,127,166 |
| **TOTAL** | **73.63** | **2,351.6** | — |

**Browser baseline (fzstd + @msgpack/msgpack JS)**: typically 1.5-2× faster than Python — Phase 3.2 measurements showed ~3.5s cold first-visit, ~50 ms warm cache hit. Service Worker pre-cache makes second visit ~50ms (ADR-011 D target).

## Lookup latency

All Map.get operations are **sub-microsecond** — orders of magnitude below the ADR-011 D target of <1 ms.

| Index | hit median | hit p95 | miss median | miss p95 |
|---|---:|---:|---:|---:|
| `tier0` | 0.05 µs | 0.14 µs | 0.04 µs | 0.07 µs |
| `tier0-bo` | 0.12 µs | 0.20 µs | 0.10 µs | 0.18 µs |
| `equivalents` | 0.06 µs | 0.35 µs | 0.04 µs | 0.22 µs |
| `reverse_en` | 0.07 µs | 0.34 µs | 0.05 µs | 0.22 µs |
| `reverse_ko` | 0.04 µs | 0.16 µs | 0.03 µs | 0.04 µs |
| `declension` | 0.04 µs | 0.21 µs | 0.04 µs | 0.05 µs |

## Prefix binary search (headwords.txt.zst)

| Prefix | Avg latency / query | Matches |
|---|---:|---:|
| `dha` | 2.65 µs | 20 |
| `pra` | 2.69 µs | 20 |
| `bud` | 3.37 µs | 20 |
| `a` | 2.53 µs | 20 |
| `ana` | 2.63 µs | 20 |
| `kara` | 2.55 µs | 20 |
| `tat` | 3.57 µs | 20 |
| `mahā` | 0.20 µs | 0 ← prefix doesn't normalize-match (Sentinel #15 verifies frontend normalizes via `normalizeHeadword('mahā')` → 'mahaa') |
| `śūn` | 0.19 µs | 0 ← same; frontend normalizes to 'suun' |

## Verdict

✅ **Lookup latency is non-issue** — sub-µs everywhere. The end-to-end perceived latency in the browser is dominated by:
1. Network fetch (bytes from CDN)
2. Decompression (fzstd)
3. msgpack decode

Once loaded into Maps, Map.get is essentially free.

✅ **Cold load 2.35s (Python)** matches expectation. Browser side typically 1.5-2× faster + Service Worker eliminates cold load on second visit.

## Implications for Phase 3.6

- No latency optimization needed in lookup path.
- Decompression strategy (main thread vs Worker) discussed in CLAUDE.md §7 — main thread chosen by ADR-011, jank only if needed.
- Phase 5 D1 Edge API will add ~50ms KV lookup for long-tail entries — that's still well under user-perceptible threshold.

## Note on Phase 3.5 entry-id matching

The mahā/śūn 0-match results above demonstrate: **the IAST frontend input normalizes** (`normalizeHeadword`) to ASCII for index lookup. Phase 3.5b A4 audit measured against raw IAST keys and saw the same effect. This is why `audit_reverse_precision.py` v2 needed the full JSONL id resolution path.
