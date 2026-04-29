# audit-D-tests — vitest + pytest coverage gap

Date: 2026-04-30

## Test pass summary

| Suite | Files | Tests | Duration | Status |
|---|---:|---:|---:|---|
| vitest (TS) | 3 | 75 | 192ms | ✅ all pass |
| pytest (Python) | 6 | 79 | 250ms | ✅ all pass |
| **Total** | 9 | 154 | <1s | ✅ |

## Vitest coverage by source

### Tested ✅

| Source | LoC | Test file | LoC | Tests |
|---|---:|---|---:|---:|
| `search/engine.ts` | 154 | `engine.test.ts` | 138 | ~25 |
| `search/lang.ts` | 47 | `lang.test.ts` | 71 | ~15 |
| `search/transliterate.ts` | 231 | `transliterate.test.ts` | 148 | ~35 |

### Not tested ❌

| Source | LoC | Risk | Recommendation |
|---|---:|---|---|
| `declension/parse.ts` | 70 | **High** — Phase 3.5 new code, parses Heritage Declension HTML tables. Bugs would break /declension UI silently. | **P1** — add `parse.test.ts` (8 case × 3 number grid round-trip, missing-cell handling, sandhi forms). |
| `indices/loader.ts` | 136 | **High** — fetch + zstd decompress + msgpack decode for 7 indices. Race or off-by-one would corrupt entire UI. | **P1** — add `loader.test.ts` with mocked fetch + golden bundle. |
| `search/source-colors.ts` | 39 | Low — pure label/hue mapping for 18 dicts. | P3 — minor unit test for completeness. |
| `stores/search.ts` | 11 | Trivial wrapper. | P3 — skip. |
| `stores/theme.ts` | 27 | Low — localStorage roundtrip + system pref detect. | P2 — happy-path test would prevent regression on theme cycle. |
| `indices/store.ts` | 26 | Trivial holder. | P3 — skip. |
| `indices/types.ts` | 84 | Type-only, no runtime. | — |
| `index.ts` | 1 | Re-export. | — |
| **Components** (8 .svelte files, ~900 LoC) | 900 | — | Component testing via @testing-library/svelte deferred to Phase 4+. |

### Components NOT covered (deferred)

- SplashScreen, ThemeToggle, EntryFull, EquivDetail, Autocomplete, FilterBar
- Most are presentational (props in, rendered out) — unit-testable but high-value tests would be Playwright e2e, not vitest.
- Phase 4 should add 3-5 e2e flows: cold load, search→equiv→modal→close, autocomplete keyboard navigation.

## Pytest coverage

```
6 files · 79 tests · all pass in 0.25s
- test_html_utils.py
- test_normalize.py
- test_reverse_tokens.py
- test_snippet.py
- test_transliterate.py
- (one more)
```

Pytest covers `scripts/lib/` helpers thoroughly. **Build scripts** (`scripts/build_*.py`, `scripts/extract_*.py`, `scripts/audit_*.py`) are not unit-tested — relies on integration via `verify.py` and the new audit scripts.

## Coverage maturity (Track D8)

| Layer | Test coverage | Verdict |
|---|---|---|
| `scripts/lib/*` | ✅ 79 tests | mature |
| `src/lib/search/*` | ✅ 75 tests | mature |
| `src/lib/declension/*` | ❌ 0 tests | **P1 gap** |
| `src/lib/indices/*` | ❌ 0 tests (loader is critical) | **P1 gap** |
| `src/lib/components/*` | ❌ 0 tests | acceptable for Phase 3.6, P2 for Phase 4 |
| `src/routes/*` | ❌ 0 tests | acceptable, P2 for Phase 4 e2e |
| `scripts/build_*` | ❌ no unit tests, but verify.py + audit covers integration | acceptable |

## Recommendations

### Phase 3.6 (priority)
1. **Add `src/lib/declension/parse.test.ts`** (~30 min) — 4-5 unit tests covering known Heritage Declension formats from `data/jsonl/decl-a01.jsonl` etc.
2. **Add `src/lib/indices/loader.test.ts`** (~1h) — 2-3 tests with mocked fetch + golden msgpack bytes (use small fixture).

### Phase 4+ (deploy)
- 3-5 Playwright e2e flows
- Lighthouse CI in build pipeline
- Component snapshot tests for key UI (SplashScreen, EntryFull modal)

### Defer
- store/theme.ts unit test (low risk, happy path well-known)
- store/search.ts (wrapper)
- source-colors.ts (mapping table)
