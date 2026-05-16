# audit-sprint1-lighthouse — Lighthouse re-measurement after Sprint 1

**Date**: 2026-05-16
**Production URL**: https://sanskrit-tibetan-workspace.pages.dev/
**Production commits**: Pages `0b041ec`, Worker `73d8ea59`
**Sprint 1 commits**: `495937d` (A1) · `198caaf` (A2) · `0c68ed8` (A3) · `9f6ff58` (A5) · `3cb73e5` (A6) · `c749a54` (A4) · `9c54a71` (C5)

## Score change

| Strategy | Phase 3.6 baseline | Sprint 1 (this measurement) | Δ |
|----------|-------------------:|----------------------------:|---:|
| **Desktop** | 45 | **85** | **+40** |
| **Mobile**  | 45 | **96** | **+51** |

## Detailed metrics

### Desktop (full mode — all indices loaded)
```
First Contentful Paint     1.13 s
Largest Contentful Paint   1.38 s
Speed Index                1.73 s
Total Blocking Time         200 ms   (baseline ~3000 ms)
Cumulative Layout Shift       0
Time to Interactive        1.43 s
Max Potential FID           170 ms
```

### Mobile (lazy mode — Edge API only, 4G + slow CPU simulated)
```
First Contentful Paint     1.86 s
Largest Contentful Paint   2.62 s
Speed Index                1.86 s
Total Blocking Time           0 ms   (baseline ~3000 ms)
Cumulative Layout Shift       0
Time to Interactive        2.62 s
Max Potential FID            50 ms
```

Lighthouse top-opportunities list is empty in both runs — no single
audit estimates ≥100 ms savings, which means the major bottlenecks
have all been removed.

## Why mobile scores higher than desktop

Counter-intuitive but intentional. Mobile enters **lazy mode** at
runtime (per `src/lib/indices/detect.ts isProbablySlow()`): the
viewport-≤768px heuristic skips the eager 38 MB core-tier fetch and
routes searches through the Edge API. Net effect on the Lighthouse
audit:

- mobile: no index downloads in the audit window → TBT 0 ms → score
  approaches 100
- desktop: full-mode loads the core tier in the audit window → TBT
  205 ms of decode/object-conversion work → score capped at 85

This is the design trade-off, not a regression. Desktop users get
local-first search after the initial 1.5 s settle; mobile users get
zero-blocking page render plus ~500 ms Edge API per query (which the
audit doesn't time-stamp into the score). Both populations get the
result they actually need.

## Decomposition by Sprint 1 task

| Task | Likely contribution |
|------|---------------------|
| A1 (Worker offload) | Primary TBT reduction (~2.5 s → 0–205 ms). Most of the score lift. |
| A2 (Preload hints in app.html) | Pulled FCP / LCP / TTI in by parallelising index download with JS bundle parse. |
| A3 (reverse_meta lazy) | -9 MB removed from the audit-window network total → smaller LCP. |
| A5 (Self-host font) | Removed render-blocking external stylesheet → cleaner FCP. |
| A4 / A6 (lazy-mode UX) | Mobile path now functionally complete; Edge autocomplete + focus prefetch don't show up as a Lighthouse score but unblock the user. |
| C5 (HTTP/3 + Early Hints) | Already on by Cloudflare default (`alt-svc: h3` present). |

## Measurement environment

- Lighthouse **13.3.0**
- Google Chrome **148.0.7778.168** (headless via `--headless=new`)
- macOS host (developer workstation), running `npx --yes lighthouse@latest`
- Production target — first request to a cold edge (Service Worker not
  installed yet); cold cache.
- Raw JSON archived at `data/reports/sprint1-lighthouse.json`
  (preset summary) and `/tmp/stw-lh/{desktop,mobile}.json` (full
  output, ~200 KB each).

## How to reproduce

```bash
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
mkdir -p /tmp/stw-lh

CHROME_PATH="$CHROME" npx --yes lighthouse@latest \
  "https://sanskrit-tibetan-workspace.pages.dev/" \
  --preset=desktop --only-categories=performance \
  --output=json --output-path=/tmp/stw-lh/desktop.json \
  --chrome-flags="--headless=new --no-sandbox" --quiet

CHROME_PATH="$CHROME" npx --yes lighthouse@latest \
  "https://sanskrit-tibetan-workspace.pages.dev/" \
  --only-categories=performance \
  --output=json --output-path=/tmp/stw-lh/mobile.json \
  --chrome-flags="--headless=new --no-sandbox" --quiet
```

Then either pipe the JSON into the metric extractor in this audit's
git history, or open the files in https://googlechrome.github.io/lighthouse/viewer/
for the standard HTML view.

## Recommendations

Sprint 1 closes the "perceived performance" gap. Remaining future-work
candidates for further improvement (none urgent):

1. **Sprint 2 B1** (Top-1K instant tier) — pushes desktop TTI < 1.0 s
   and lets even cold first-paint serve hot queries without waiting on
   any tier load.
2. **Sprint 2 B2** (zstd-wasm replacing fzstd) — combined with A1's
   worker offload, would let desktop TBT drop the remaining ~200 ms.
3. **Sprint 2 B4** (D1 covering index) — would shave the ~600 ms cold
   Edge-API latency that mobile users feel on first query (doesn't show
   in Lighthouse score but is the user-perceived bottleneck).
4. **D1 ranking column** — Edge autocomplete currently orders by
   `priority`, ties resolved alphabetically. Local autocomplete uses
   `rank` from headwords.txt. A `rank` column in D1 would lift `dharma`
   above `dha`, `dhah`, etc. in the lazy-mode dropdown.

These are nice-to-haves; Lighthouse already says 85 desktop / 96 mobile.
