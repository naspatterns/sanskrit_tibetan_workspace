# Track D partial — TypeScript + production build (D1 + D3)

Date: 2026-04-30

## D1 — TypeScript strict check (`npm run check`)

```
COMPLETED 255 FILES 0 ERRORS 0 WARNINGS 0 FILES_WITH_PROBLEMS
```

✅ **Verdict**: 255 files, **0 errors / 0 warnings**. Strict mode passes cleanly.

(Implication: type system is sound. No `any` escapes that the compiler would have flagged.)

---

## D3 — Production build (adapter-static)

```
✓ built in 298ms (client)
✓ built in 1.44s (server)
✔ done — Wrote site to "build"
```

✅ **Verdict**: SvelteKit 2.57 + adapter-static 3.0 production build succeeds.

### Bundle size analysis (gzipped)

| Chunk | Raw | Gzipped | Notes |
|---|---:|---:|---|
| `nodes/0.CXehjpko.js` (root layout) | 27.27 kB | **10.20 kB** | Splash + theme + bundle loader |
| `nodes/2.C49awZ4Z.js` (search page) | 21.23 kB | **7.66 kB** | `+page.svelte` 684 LoC compiled |
| `nodes/3.DNwT1fJx.js` (declension page) | 4.30 kB | 2.10 kB | Lightweight |
| `chunks/xU7KhxP_.js` (vendor) | 45.66 kB | **17.65 kB** | fzstd + msgpack runtime |
| `chunks/BNbemLvI.js` (svelte runtime) | 26.01 kB | 10.15 kB | Svelte 5 client |
| `chunks/DL3wOVsZ.js` (helpers) | 2.88 kB | 1.64 kB | `transliterate.ts` etc. |
| Other chunks | ~3 kB | ~1.5 kB | Routing |
| CSS (3 files combined) | 12.91 kB | 3.62 kB | Theme + per-page |
| **Total client critical-path (gzipped)** | — | **~50 kB** | Excellent |

### Server-side (SSR fallback for adapter-static)

| Chunk | Gzipped |
|---|---:|
| `index-server.js` | 32.91 kB |
| `index.js` | 30.74 kB |
| Total server | ~80 kB |

### Cloudflare Pages compatibility

- Total static asset count: ~25 (under 25,000 limit ✅)
- Largest single asset: 45.66 kB raw chunk (under 25 MB limit ✅)
- Index files (76 MB compressed under `static/indices/`) — separate from build output, served directly by CDN

### Phase 4 deploy readiness

✅ adapter-static produces `build/` directory ready for Cloudflare Pages drop-in deploy. Service Worker (`static/sw.js`) gets copied as-is. Index files in `public/indices/` get copied to `build/indices/`.

---

## What's not measured here (other Track D items)

- **D2** Svelte 5 runes consistency — agent running (Explore type)
- **D4** Heap profiling — requires running browser (Track C / Day 3)
- **D5** Search latency in browser — bench/index.html (Track C / Day 3)
- **D6** Service Worker behavior — devtools application tab (Track C / Day 3)
- **D7** Build script perf — backgrounded (`time` measurements)
- **D8** Test coverage — pending (vitest + pytest gap analysis)
- **D9** Declension HMR race — production build done, will verify in Track C

---

## Coverage matrix (Track D)

| # | Item | Status | Verdict |
|---|---|---|---|
| D1 | TypeScript strict | ✅ done | 0/0 |
| D2 | Svelte 5 runes | ⏳ running | — |
| D3 | Production build | ✅ done | ~50 kB gzipped |
| D4 | Heap profile | ⏭️ Day 3 | — |
| D5 | Latency in browser | ⏭️ Day 3 | — |
| D6 | Service Worker | ⏭️ Day 3 | — |
| D7 | Build script perf | ⏳ running | — |
| D8 | Test coverage | ⏳ pending | — |
| D9 | Declension HMR race | ⏭️ Day 3 (prod preview) | — |
