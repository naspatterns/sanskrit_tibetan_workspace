# audit-D-decl-race — Declension HMR race verification (D9)

Date: 2026-04-30
Context: Phase 3.5 known issue — `?q=` URL parameter not auto-filled in declension input under dev mode HMR. Production verification deferred until Phase 3.6 / 4.

## Verification method

Production preview (`npm run preview`, port 4173) reachable. SSR HTML responses captured for:
- `/declension?q=dharma`
- `/?q=fire`

Both return **HTTP 200 + splash HTML** as expected. The actual query input population happens client-side after Svelte hydration, which is the same code path in dev and prod — but **without Vite HMR's module re-execution loop in prod**.

## Code path analysis

`declension/+page.svelte:13-21` (production-built code is identical):

```ts
onMount(() => {
  query = page.url.searchParams.get('q') ?? '';
  const onPop = () => {
    const nextQ = new URL(window.location.href).searchParams.get('q') ?? '';
    if (nextQ !== query) query = nextQ;
  };
  window.addEventListener('popstate', onPop);
  return () => window.removeEventListener('popstate', onPop);
});
```

In dev:
1. SvelteKit hydrates → `page` store reactive
2. HMR may re-execute `+page.svelte` module  
3. onMount fires → reads `page.url.searchParams.get('q')`
4. Race window: if HMR re-execution clears local `query` after onMount has set it, input shows empty

In prod:
1. SvelteKit hydrates once → `page` store reactive
2. No HMR
3. onMount fires → reads searchParams → sets query
4. No subsequent overwrite path

**Conclusion**: Production preview cannot exhibit the dev HMR race because the trigger (HMR module re-execution) doesn't exist.

## Manual verification needed (sub-issue)

The full visual verification — load `http://localhost:4173/declension?q=dharma` in a real browser, observe input pre-filled — requires a UI session. Since this is end-to-end, recommended for Day 3 sentinel demo (sentinel #16-20 cover Wylie input on declension page).

If the input *fails* to pre-fill in production preview, root cause is different (would be a real bug). Current evidence (HTTP 200 + clean module path) suggests no production race.

## Verdict

✅ **HMR race is dev-mode only** — production preview's clean module lifecycle removes the trigger.

⏭️ **Day 3 sentinel demo** will be the final visual confirmation.

## Recommendation

- Phase 3.6: include `/declension?q=*` in sentinel queries (sentinel #16-20 cover this).
- If race still observed in prod (unexpected), elevate to P0; current evidence is strong negative.
