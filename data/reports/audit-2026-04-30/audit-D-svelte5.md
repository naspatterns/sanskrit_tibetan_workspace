# audit-D-svelte5 — Svelte 5 runes consistency + memory safety

Date: 2026-04-30
Codebase: sanskrit-tibetan-workspace (Phase 3.6 readiness)
Reviewer: Explore agent (read-only review, ~2,900 LoC across 15 files)

## Verdict

**0 P0, 1 P1, 2 P2 issues found** — codebase is Svelte 5 compliant and deploy-ready.

## Top 3 findings

1. **P1 · Stale closure in $effect debounce** (`+page.svelte:40-56`, `declension/+page.svelte:23-39`)
   - `const target = query` captured at effect entry; `setTimeout` callback later compares `cur === target` against URL.
   - Mitigation present: cleanup `() => clearTimeout(id)` cancels stale timers.
   - Pattern is fragile but not a bug. Refactor recommendation in §Recommendations.

2. **P2 · SSR guard pattern repetition** (theme.ts, +page.svelte, declension/+page.svelte)
   - `if (typeof window === 'undefined') return` repeated in 3 files.
   - Works correctly; readability cost only. Consolidate into `lib/utils/ssr.ts`.

3. **P2 · engine.ts Map.get null handling not documented** (`engine.ts:71-100`)
   - 7 Map.get sites all use `?? null` fallback correctly.
   - Add JSDoc clarifying that `null` from `.get()` is a logic error post-load (Maps are pre-populated).

## Per-file detail

### `src/routes/+layout.svelte` (79 LoC)
- ✅ 3 $state declarations (progress, loaded, error) appropriately local.
- ✅ Single `onMount`. SW registration with try-catch swallow. No listener leaks.
- ✅ SSR guard correct.

### `src/routes/+page.svelte` (684 LoC) — main search page
- 8 $state declarations all appropriate (none wrap massive data structures).
- $derived used correctly for `result` (re-computed on query change).
- **L40-56 ($effect debounce)** — P1 stale closure (see Top 3). Cleanup is correct, but pattern fragile.
- **L60-83 (onMount popstate)** — Correctly cleaned up. Hydration safe. fromId deep-link is O(n) but only on first mount.
- `<svelte:window onkeydown={…}/>` — Svelte-managed lifecycle, no manual cleanup needed. ✅

### `src/routes/declension/+page.svelte` (224 LoC)
- Same shape as +page.svelte. Same P1 closure pattern.
- **L24** SSR guard inside $effect — works, but `onMount` would be more idiomatic for browser-only logic.

### `src/lib/components/ThemeToggle.svelte` (52 LoC)
- $state(theme) + $effect to persist localStorage. ✅ No leaks.

### `src/lib/components/Autocomplete.svelte` (138 LoC)
- $state(selected) + $effect to reset selection when items change. ✅ Stateless export functions.

### `src/lib/components/SplashScreen.svelte` (112 LoC)
- Pure presentational, $props only. ✅

### `src/lib/components/EntryFull.svelte` (145 LoC)
- $props only. `<svelte:window onkeydown>` for Esc-close. ✅

### `src/lib/components/EquivDetail.svelte` (172 LoC)
- $props only. ✅

### `src/lib/components/FilterBar.svelte` (106 LoC)
- $bindable for langFilter/priorityMax — correct Svelte 5 two-way idiom. ✅

### `src/lib/stores/theme.ts` (28 LoC)
- Non-reactive helper functions. SSR-safe.
- ⚠️ Repeated `typeof localStorage !== 'undefined'` guards (lines 11, 17, 21). P2 readability.

### `src/lib/stores/search.ts` (12 LoC)
- Stateless wrapper around engine.search(). ✅

### `src/lib/indices/store.ts` (27 LoC)
- **Critical design choice**: non-reactive holder by design (ADR-011). 30 MB tier0 bundle never enters Svelte's reactive machinery. ✅
- Fail-fast `getIndexBundle()` throws if not loaded.

### `src/lib/indices/loader.ts` (136 LoC)
- Promise.all parallel fetch+decompress. Synchronous emit() callback. Pure helpers.
- ✅ No leaks (promises ephemeral).

### `src/lib/indices/types.ts` (85 LoC)
- Pure type definitions. ✅

### `src/lib/search/engine.ts` (154 LoC)
- Pure search function, no state.
- 7 Map.get sites all `?? null` guarded. P2 — add JSDoc to clarify Maps are pre-populated.

### `src/lib/search/lang.ts` (47 LoC)
- Pure helpers. langBalancedTop/Rest O(n log n) on small filtered slices. ✅

## Cross-file matrix

| Category | Status | Notes |
|---|---|---|
| Type safety | ✅ Clean | 0 `as any` / `: any`. All Map.get guarded. |
| Reactive primitives | ✅ Correct | $state mutable, $derived computed, $effect side-effects. No over-wrapping. |
| Memory leaks | ⚠️ P1 minor | All listeners cleaned up. P1 closure is timing-fragile only. |
| SSR hydration | ✅ Safe | All window/document/localStorage access guarded. |
| URL↔query sync | ✅ Fixed (`07bbbd5`) | popstate listener replaces reactive $effect. |
| Declension HMR race | ⚠️ Not reproduced | No structural HMR race in code. Eager bundle (2.1 MB) avoids lazy-promise hang. Likely dev-mode only. |

## Recommendations

### P1 — refactor $effect debounce closure

Both `+page.svelte:40-56` and `declension/+page.svelte:23-39`:

```ts
// Before (fragile)
const target = query;
const id = window.setTimeout(() => {
  if (cur === target) return;  // captured at outer scope
  ...
}, 120);

// After (idiomatic Svelte 5)
const id = window.setTimeout(() => {
  const target = query;  // fresh read on fire
  ...
}, 120);
```

Or replace with `$effect.pre()` dependency tracking.

### P2 — consolidate SSR guards

New `src/lib/utils/ssr.ts`:
```ts
export const isBrowser = () => typeof window !== 'undefined';
```
Then `if (!isBrowser()) return;` everywhere.

### P2 — document engine.ts Map.get contract

Add JSDoc:
```ts
/**
 * @remarks
 * `bundle.*` Maps are pre-populated by `loader.ts` during splash.
 * `.get()` returning null indicates the requested key is genuinely
 * absent from the indexed corpus — not a load-time race.
 */
```

## Phase 3.6 readiness

- ✅ Runes usage: compliant
- ✅ Memory: clean
- ✅ Types: clean
- ⚠️ Code quality: 1 P1 + 2 P2 (all minor)
- ✅ Deploy risk: **low** — no blockers

**Recommendation**: Deploy as-is. Schedule P1 closure refactor + P2 cleanups for Phase 3.7 sprint or fold into Phase 3.6 if cheap.
