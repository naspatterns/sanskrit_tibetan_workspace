// Service Worker — index precache (ADR-011 D).
//
// First visit:  cold fetch fills the cache (network bytes).
// Subsequent:   cache-first hit ~50 ms vs. ~3.5 s cold (5 indices · 64 MB).
//
// Cache name is versioned so a future rebuild can bump and clear stale
// caches via the activate handler. To force-refresh after rebuilding the
// indices, bump the suffix below and reload twice (install + activate).

// v2: Phase 3.3 added tier0-bo (Tibetan top-10K).
const CACHE_NAME = 'stw-indices-v2';

const PRECACHE_URLS = [
	'/indices/tier0.msgpack.zst',
	'/indices/tier0-bo.msgpack.zst',
	'/indices/equivalents.msgpack.zst',
	'/indices/reverse_en.msgpack.zst',
	'/indices/reverse_ko.msgpack.zst',
	'/indices/headwords.txt.zst'
];

self.addEventListener('install', (event) => {
	event.waitUntil(
		caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS))
	);
	// Activate immediately on first load — splash bar progress is live, the
	// SW just makes the *next* visit instant. No reason to wait for refresh.
	self.skipWaiting();
});

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

self.addEventListener('fetch', (event) => {
	const url = new URL(event.request.url);
	if (!url.pathname.startsWith('/indices/')) return; // not ours

	event.respondWith(
		caches.open(CACHE_NAME).then(async (cache) => {
			const cached = await cache.match(event.request);
			if (cached) return cached;
			// Cache miss (e.g. first visit before install completed) —
			// fetch + opportunistic cache fill.
			const resp = await fetch(event.request);
			if (resp.ok) cache.put(event.request, resp.clone());
			return resp;
		})
	);
});
