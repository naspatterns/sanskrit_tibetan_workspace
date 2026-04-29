# audit-E-deploy — Production readiness (Track E)

Date: 2026-04-30

## E1 — adapter-static export completeness

✅ `npm run build` succeeds (verified D3).
- Output directory: `build/`
- Fallback: `index.html` (SPA mode)
- Prerender: not required (single-page client)

Production preview (`npm run preview` → http://localhost:4173/) verified:
- `/` returns 200 + splash HTML
- `/declension` returns 200
- `/sw.js` returns 200 (Service Worker source)

## E2 — CSP + security headers

⚠️ Not yet configured. `build/_headers` not present.

### Recommended `_headers` (Cloudflare Pages format)

```
/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: interest-cohort=()
  Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; font-src 'self'; worker-src 'self'

/indices/*
  Cache-Control: public, max-age=31536000, immutable
  Content-Type: application/octet-stream

/sw.js
  Cache-Control: no-cache
  Service-Worker-Allowed: /
```

`'unsafe-inline'` for script: Svelte 5 hydration bootstrap injects an inline script. Could be eliminated via SvelteKit nonce config but adds complexity; acceptable for Phase 4.

## E3 — Cloudflare Pages limits

| Limit | Value | Our usage | Headroom |
|---|---|---|---|
| Total file count | 25,000 | ~30 (build/) + 7 (indices/) = ~40 | 99.8% |
| Single file size | 25 MB | tier0.msgpack.zst 28.78 MB ⚠️ | **OVER** |
| Total deploy size | 25 GB | ~76 MB | 99.7% |
| Build minutes/month (free) | 500 | <10 typical | ample |
| Bandwidth | unlimited free | — | — |

### ⚠️ tier0.msgpack.zst exceeds 25 MB limit

`tier0.msgpack.zst` is **28.78 MB** — Cloudflare Pages rejects files >25 MB.

**Options**:

1. **Cloudflare R2** (object storage) — fetch from `r2.example.com/indices/tier0.msgpack.zst` instead of `/indices/`. ~$0.015/GB-month. Adds CORS config.

2. **Split tier0** by frequency band — `tier0-top5k.msgpack.zst` (~14 MB) + `tier0-tier-5to10k.msgpack.zst` (~14 MB), client merges. ADR-009 originally rejected sharding; this is targeted sharding for limit, not for memory.

3. **Re-tune zstd compression** — currently default level. zstd `--ultra -22` could reduce to ~24 MB at higher CPU cost (one-time).

4. **Cloudflare Workers** + KV — Phase 5 plan anyway. Move tier0 to KV, fetch on demand.

**Recommendation**: Option 3 (zstd recompress) for Phase 4 minimal-change. Option 4 (Phase 5 Edge API) for long-term.

Estimated effort:
- Option 3: 30 min + redeploy (zstd flags in `build_tier0.py`)
- Option 4: Phase 5 scope (already planned)

## E4 — License coverage

| Source | Count |
|---|---:|
| Total dicts in `data/sources/` | 148 |
| Documented in `LICENSES.md` | 101 |
| **Missing license entries** | **47** |

⚠️ **47 dicts not documented in LICENSES.md**. Phase 4 deploy gate.

### Likely uncovered groups (need cross-check)

- `equiv-*` extension dicts added during Phase 2.5 (yogācārabhūmi-idx, bonwa-daijiten, hirakawa, karashima-lotus, etc.)
- Heritage Hopkins sub-decompositions (`tib-hopkins-divisions`, `tib-hopkins-others-english`, etc.)
- Phase 1 spawn additions (Tib_Chn Wylie, amarakośa NLP synonyms)

### Recommendation

Phase 4 deploy gate: regenerate LICENSES.md to include all 148 dicts. ~1-2h to research + verify license claim per dict. Most equiv-* sources are CC0 academic (Bingenheimer, 84000) but need explicit listing.

## E5 — User feedback loop

✅ `LICENSES.md` already includes contact email: `naspatterns@gmail.com`.
⏭️ Phase 4: add a feedback form (GitHub issue link or Cloudflare Form). Currently no in-app feedback path.

## Summary

| # | Item | Status | P-level |
|---|---|---|---|
| E1 | adapter-static export | ✅ | — |
| E2 | CSP + headers | ⚠️ `_headers` not yet present | P1 (Phase 4 entry) |
| E3 | Cloudflare 25 MB limit | ❌ tier0 28.78 MB | **P0 for Phase 4** |
| E4 | License coverage | ⚠️ 47 dicts missing | P1 (Phase 4 gate) |
| E5 | Feedback loop | ⏭️ deferred | P2 |

## Phase 4 entry checklist (recommended)

Before invoking `wrangler pages deploy build` or git-push deploy:

1. ☐ Recompress tier0 (zstd `-22 --ultra`) to fit under 25 MB OR move to R2/Workers
2. ☐ Write `static/_headers` with CSP + Cache-Control + Service-Worker-Allowed
3. ☐ Backfill LICENSES.md to all 148 dicts
4. ☐ Set up `wrangler.toml` or Cloudflare Pages git-push integration
5. ☐ Custom domain or `*.pages.dev` URL
6. ☐ Smoke test deploy → 50 sentinel queries pass on production URL
