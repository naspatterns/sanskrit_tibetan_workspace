# audit-D-buildperf — build script timing (D7)

Date: 2026-04-30

## Total cold rebuild time

| Script | Wall clock | User CPU | CPU% | Bottleneck |
|---|---:|---:|---:|---|
| `frequency.py` | 20.2s | 17.3s | 90% | single-threaded scan of 3.81M JSONL lines |
| `build_fst.py` | 37.1s | 34.3s | 95% | single-threaded sort+zstd |
| `build_reverse_index.py` | **76.8s** | 73.5s | 97% | single-threaded heap-bounded merge |
| `build_tier0.py` | **90.5s** | 86.8s | 97% | single-threaded JSONL re-scan + msgpack |
| `build_declension.py` | 16.5s | 15.5s | 98% | single-threaded |
| `verify.py` | 17.3s | 70.5s | **419%** | ✅ already 4-worker multiprocessing |
| **Total cold rebuild (sequential)** | **4:18 min** | — | — | — |

(equiv index build not measured — done separately via `build_equivalents_index.py`.)

## Hotspots

1. **`build_tier0.py` 90s** — biggest. Re-scans every JSONL to filter top-10K headwords + builds long-key schema.
2. **`build_reverse_index.py` 77s** — second biggest. Iterates all 3.81M entries, accumulates per-token heaps.

Both are CPU-bound at 97%, single-process. Already noted in CLAUDE.md §6 as deferred multiprocessing target.

## Speedup estimate

If both were parallelized via `multiprocessing.Pool(4)`:
- `build_tier0`: 90s → ~25-30s (3× speedup, IO + msgpack overhead caps higher)
- `build_reverse_index`: 77s → ~22-25s

Total cold rebuild: ~4:18 → **~2:00 min** (52% faster).

## Recommendation

- **P3** — defer. Cold rebuild is ~4 min, run nightly or per-content-update. Not in user-facing path.
- **P2** if data updates become more frequent (e.g. post-Phase 4 with continuous integration on PR).

## Phase 3.6 readiness

- ✅ Build pipeline functional. Total time acceptable.
- ⏭️ Multiprocessing optimization deferred until rebuild frequency justifies.
