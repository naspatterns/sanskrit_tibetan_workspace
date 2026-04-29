# Track D — Code Quality + Build Performance Summary

Date: 2026-04-30
Scope: 2,892 LoC TS+Svelte · 9,155 LoC Python · 75 vitest · 79 pytest

## Verdict per item

| # | Item | Verdict | P-level | Linked report |
|---|---|---|---|---|
| D1 | TypeScript strict (`npm run check`) | ✅ **0 errors / 0 warnings / 255 files** | — | `audit-D-build.md` |
| D2 | Svelte 5 runes consistency | ⚠️ 1 P1 (closure fragility) + 2 P2 (style) | P1 + P2 | `audit-D-svelte5.md` |
| D3 | Production build (adapter-static) | ✅ build success, ~50 kB gzipped client critical-path | — | `audit-D-build.md` |
| D4 | Heap profiling | ⏭️ Day 3 (Track C / browser) | — | — |
| D5 | Search latency in browser | ⏭️ Day 3 (bench/index.html) | — | — |
| D6 | Service Worker | ⏭️ Day 3 (devtools) | — | — |
| D7 | Build script perf | ✅ 4:18 total cold rebuild; tier0 + reverse_index = 78% of time | P3 (defer multiprocessing) | `audit-D-buildperf.md` |
| D8 | Test coverage | ⚠️ 75 vitest + 79 pytest pass; **gaps**: parse.ts, loader.ts (P1) | P1 | `audit-D-tests.md` |
| D9 | Declension HMR race | ⚠️ Not reproduced in code review; verify in production preview (Day 3) | — | folded into D2 |

## Headline numbers

```
TypeScript files .................. 255   ✅
TypeScript errors ................. 0
TypeScript warnings ............... 0

Production client gzipped (critical) ~50 kB
Production server gzipped .......... ~80 kB
Build time (Vite) ................. 1.74 s

Cold rebuild all 7 indices ........ 4:18 (4 min 18 s)
  - build_tier0.py ................ 90.5 s  (single-process)
  - build_reverse_index.py ........ 76.8 s  (single-process)
  - others ........................ 71 s combined

vitest .................. 3 files / 75 tests / 192 ms / ✅
pytest .................. 6 files / 79 tests / 250 ms / ✅
```

## Top findings

### ✅ Stable

- **Type safety perfect** — 0 implicit-any, 0 `as any`, all Map.get guarded with `??`.
- **Production build succeeds** — adapter-static produces clean `build/` directory ready for Cloudflare Pages.
- **Tests all pass** — 154 tests in <1s combined.

### ⚠️ Phase 3.6 should-fix (P1)

**P1 (D2-1) · `$effect` debounce closure fragility** (`+page.svelte:40-56`, `declension/+page.svelte:23-39`)
- Pattern: `const target = query` captured outside setTimeout, compared inside callback.
- Cleanup `() => clearTimeout(id)` mitigates correctly.
- Recommended refactor: move `const target = query` *inside* setTimeout, or use `$effect.pre()`.

**P1 (D8-1) · Test gap for `declension/parse.ts`** (Phase 3.5 new code, 70 LoC, 0 tests)
- Heritage Declension HTML table parser; bugs would silently break /declension UI.
- ~30 min to add 5 unit tests covering grid round-trip + missing cell + sandhi forms.

**P1 (D8-2) · Test gap for `indices/loader.ts`** (136 LoC, 0 tests)
- Critical fetch + zstd decompress + msgpack decode for 7 indices.
- ~1h to add 2-3 tests with mocked fetch + golden bytes.

### P2 (Phase 3.7+)

- **D2-2** SSR guard pattern repeated in 3 files — consolidate into `lib/utils/ssr.ts`
- **D2-3** Add JSDoc clarifying `Map.get()` null contract in engine.ts
- **D8-3** stores/theme.ts happy-path test
- **D7** Multiprocessing for build_tier0 + build_reverse_index (52% speedup)

### Day 3 deferred (browser-side)

- D4 Heap profile (Chrome devtools)
- D5 Latency p95 in browser (bench/index.html, 1000 query × 5 round)
- D6 Service Worker behavior (install/activate/cache/offline)
- D9 Declension HMR race (verify gone in production preview)

## Track D handoff

✅ Track D static analysis complete. Code quality is solid: 0 P0, 3 P1 (all fixable in <2h each), 4 P2 (deferred).

**Combined P1 backlog from Track D**:
1. $effect closure refactor (D2-1) — ~30 min
2. parse.ts test (D8-1) — ~30 min
3. loader.ts test (D8-2) — ~1h

These pair well with Phase 3.6 P0/P1 fixes from Tracks A/B.

Next: Day 3 — Track C (sentinel queries on production preview) + D4·D5·D6 (browser perf).
