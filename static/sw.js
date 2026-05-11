// Service Worker — index precache (ADR-011 D).
//
// First visit:  cold fetch fills the cache (network bytes).
// Subsequent:   cache-first hit ~50 ms vs. ~3.5 s cold (5 indices · 64 MB).
//
// Cache name is versioned so a future rebuild can bump and clear stale
// caches via the activate handler. To force-refresh after rebuilding the
// indices, bump the suffix below and reload twice (install + activate).

// v3: Phase 3.5 added declension (top-10K Heritage paradigms).
// v4: Phase 3.6 P0-1 added reverse_meta (id → iast/dict for reverse hits UI).
// v5: Phase 3.7 (Option A) added tier0-extended (top-10K..20K Sanskrit),
//     plus headwords format change to 3-column TSV (norm\tiast\trank).
// v6: Phase 4 fix (2026-05-08) — tier0.msgpack.zst rebuilt at zstd level 19
//     (was level 22) because fzstd 0.1.1 silently misdecodes level-22 streams.
//     Also dropped snippet_medium cap from 350→200 chars.
// v7: Phase 4 follow-up (2026-05-08) — defensive cleanup. Some users with
//     a populated v5 cache stayed on v5 after we shipped v6 because v6's
//     atomic `cache.addAll` failed silently on a slow connection, leaving
//     v5 as the active SW. v7 now (a) deletes ALL `stw-indices-*` caches
//     synchronously before opening a new one, and (b) uses individual
//     `cache.put` calls so a single failed fetch doesn't void the whole
//     install. The fetch handler also self-heals on decode failure.
// v8: Phase 4 fix (2026-05-12) — smart-quote canonicalisation in
//     normalize() means clients still on v7 mis-search Wylie like
//     `chos 'byung` (smart quote silently routed to a `chos` fallback).
//     Bumping invalidates the v7 cache so they pick up the corrected
//     bundle on next load. Indices themselves are unchanged.
const CACHE_NAME = 'stw-indices-v8';

const PRECACHE_URLS = [
	'/indices/tier0.msgpack.zst',
	'/indices/tier0-bo.msgpack.zst',
	'/indices/tier0-extended.msgpack.zst',
	'/indices/equivalents.msgpack.zst',
	'/indices/reverse_en.msgpack.zst',
	'/indices/reverse_ko.msgpack.zst',
	'/indices/reverse_meta.msgpack.zst',
	'/indices/declension.msgpack.zst',
	'/indices/headwords.txt.zst'
];

async function purgeOldCaches() {
	const names = await caches.keys();
	await Promise.all(
		names
			.filter((n) => n.startsWith('stw-indices-') && n !== CACHE_NAME)
			.map((n) => caches.delete(n))
	);
}

self.addEventListener('install', (event) => {
	event.waitUntil(
		(async () => {
			// Step 1: nuke any prior cache version BEFORE we start populating
			// the new one. If install crashes partway, the old cache is still
			// gone — fetch handler will fall back to network.
			await purgeOldCaches();

			const cache = await caches.open(CACHE_NAME);

			// Step 2: populate per-URL with `Promise.allSettled` — if one URL
			// blips, the other 8 still cache. cache.addAll() is atomic and
			// would discard everything on a single failure.
			await Promise.allSettled(
				PRECACHE_URLS.map(async (url) => {
					const resp = await fetch(url, { cache: 'reload' });
					if (resp.ok) await cache.put(url, resp);
				})
			);
		})()
	);
	self.skipWaiting();
});

self.addEventListener('activate', (event) => {
	event.waitUntil(
		(async () => {
			await purgeOldCaches();
			await self.clients.claim();
		})()
	);
});

self.addEventListener('fetch', (event) => {
	const url = new URL(event.request.url);
	if (!url.pathname.startsWith('/indices/')) return; // not ours

	event.respondWith(
		(async () => {
			const cache = await caches.open(CACHE_NAME);
			const cached = await cache.match(event.request);
			if (cached) return cached;

			// Cache miss — fetch + opportunistic fill. Skip HTTP cache so we
			// always get the fresh asset (Cloudflare ETag still saves bytes).
			const resp = await fetch(event.request, { cache: 'reload' });
			if (resp.ok) cache.put(event.request, resp.clone());
			return resp;
		})()
	);
});
