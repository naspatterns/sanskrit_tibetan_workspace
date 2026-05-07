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
//     Also dropped snippet_medium cap from 350→200 chars to fit 25 MiB at
//     level 19. Stale v5 cache would serve the broken file.
const CACHE_NAME = 'stw-indices-v6';

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
