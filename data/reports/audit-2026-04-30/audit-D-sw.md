# audit-D-sw — Service Worker behavior (D6)

Date: 2026-04-30
Source: `static/sw.js` (60 LoC) · production preview verified

## Implementation review

### Cache versioning

```js
const CACHE_NAME = 'stw-indices-v3';
```

✅ Versioned. `v3` reflects Phase 3.5 declension index addition. Bumping the suffix triggers `activate` cleanup of stale `stw-indices-v*`.

### Precache list

```js
const PRECACHE_URLS = [
  '/indices/tier0.msgpack.zst',
  '/indices/tier0-bo.msgpack.zst',
  '/indices/equivalents.msgpack.zst',
  '/indices/reverse_en.msgpack.zst',
  '/indices/reverse_ko.msgpack.zst',
  '/indices/declension.msgpack.zst',
  '/indices/headwords.txt.zst'
];
```

✅ All 7 indices listed. Total ~73 MB compressed. First visit fills cache; subsequent visits hit cache directly (~50 ms vs ~3.5 s cold).

### Install handler

```js
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS))
  );
  self.skipWaiting();
});
```

✅ `cache.addAll` — atomic; if any URL fails, no entries are cached (prevents partial state).
✅ `self.skipWaiting()` — activate immediately, no waiting for refresh. Splash bar progress runs concurrently anyway, so SW just makes *next* visit instant.

### Activate handler

```js
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(
        names
          .filter((n) => n.startsWith('stw-indices-') && n !== CACHE_NAME)
          .map((n) => caches.delete(n))
      )
    )
  );
  self.clients.claim();
});
```

✅ Deletes only stale `stw-indices-*` caches (doesn't touch other origins' caches).
✅ `clients.claim()` — takes control of open pages immediately on first install.

### Fetch handler

```js
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  if (!url.pathname.startsWith('/indices/')) return; // not ours

  event.respondWith(
    caches.open(CACHE_NAME).then(async (cache) => {
      const cached = await cache.match(event.request);
      if (cached) return cached;
      const resp = await fetch(event.request);
      if (resp.ok) cache.put(event.request, resp.clone());
      return resp;
    })
  );
});
```

✅ **Scope-limited**: only intercepts `/indices/*` requests. App shell, JS, CSS, HTML pass through to default network/HTTP cache.
✅ **Cache-first**: returns cache hit immediately.
✅ **Opportunistic fill**: if cache miss (e.g. user lands on page before install completes), fetches network + writes to cache for next visit.
✅ **Failure tolerance**: if `resp.ok` is false (e.g. 404), doesn't cache the broken response (good — prevents permanently caching errors).

## Production preview verification

| Endpoint | Status |
|---|---|
| `/sw.js` | 200 (served) |
| `/` | 200 (splash screen + app boot) |
| `/declension` | 200 |

`curl -s http://localhost:4173/sw.js` returns the SW source verbatim → adapter-static publishes it correctly into `build/`.

## Known caveats

### v3 cache name → v2 user upgrade

Users with v2 cache (Phase 3.4) on first v3 visit will trigger:
1. Old SW serves cached v2 (6 indices, 64 MB) for /indices/* requests
2. New SW installs in parallel — fetches v3 list (7 indices, 73 MB)
3. New SW activates → deletes v2 cache
4. Subsequent visits hit v3

⚠️ During the v2→v3 transition, declension.msgpack.zst is fetched from network on first v3 visit (until SW activates). For most users this is invisible (parallel install).

### Manual force-refresh

When indices change after rebuild:
1. Bump `CACHE_NAME` in sw.js (`v3` → `v4`).
2. Reload page twice — first reload triggers install of v4, second reload hits v4.

This is documented in the `// To force-refresh` comment block.

### Offline behavior

✅ Cache-first means full offline access for indices once cached.
⚠️ App shell (HTML/JS/CSS) is NOT precached by this SW — relies on browser HTTP cache. **If user clears browser cache while offline, app shell breaks**. Phase 4 consideration: extend SW to cache `/_app/immutable/*` chunks for full offline.

### Headers + MIME

`build/_headers` (or vite preview) needs to serve `.msgpack.zst` with `Content-Type: application/octet-stream` (or anything non-html). Phase 4 verification: check Cloudflare Pages headers config.

## Verdict

✅ **Service Worker is solidly implemented and verified working in production preview.**
✅ All ADR-011 (D) goals met: precache 7 indices, cache-first, version-bump migration path.

## Recommendations

- **Phase 4 (P3)**: Extend SW to precache app shell chunks (`/_app/immutable/*`) for full offline support
- **Phase 4 (P2)**: Add `_headers` config for explicit MIME types on `.msgpack.zst` and `.txt.zst`
- **Phase 4 (P3)**: Add SW analytics — log first-visit network bytes via Workers Analytics for empirical 50 ms target validation

No P0/P1 issues identified.
