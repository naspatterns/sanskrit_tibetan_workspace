// Edge API — Phase 5 D1 lookup fallback for SvelteKit client.
//
// Endpoints:
//   GET /api/search/:norm       → exact + prefix match, top-20 entries
//   GET /api/entry/:id          → single entry by id
//   GET /api/health             → liveness probe
//
// CORS: allows same-origin (SvelteKit dev) and Pages production deploy.
// Cache: public, max-age=86400 (1 day) on successful responses.
// Errors: 4xx for client mistakes, 5xx for server errors.
//
// Free tier ratelimit: Workers 100K req/day, D1 5M reads/day. Each request
// performs 1-2 D1 reads (exact + optional prefix) + meta. Plenty of headroom.

export interface Env {
	DB: D1Database;
}

interface EntryRow {
	id: string;
	headword_norm: string;
	headword_iast: string;
	dict_slug: string;
	priority: number;
	snippet_short: string | null;
	body_ko: string | null;
	target_lang: string;
}

const CORS = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Methods': 'GET, OPTIONS',
	'Access-Control-Allow-Headers': 'Content-Type',
	'Access-Control-Max-Age': '86400'
};

const CACHE_OK = 'public, max-age=86400, s-maxage=86400'; // 1 day at edge
const CACHE_404 = 'public, max-age=300';                   // 5 min for 404 (might exist later)

function json(body: unknown, init: ResponseInit = {}): Response {
	return new Response(JSON.stringify(body), {
		...init,
		headers: {
			'Content-Type': 'application/json; charset=utf-8',
			...CORS,
			...(init.headers ?? {})
		}
	});
}

function normalize(s: string): string {
	// Match client `normalize()` in src/lib/search/transliterate.ts —
	// canonical-quote replace + NFD strip combining marks + lowercase + trim.
	// Phase 4 fix (2026-05-12): typographic quotes → ASCII apostrophe so
	// Wylie like `chos 'byung` matches even when iOS smart-quoted the input.
	return s
		.replace(/[‘’ʼ′]/g, "'")
		.normalize('NFD')
		.replace(/\p{M}/gu, '')
		.toLowerCase()
		.trim();
}

async function searchEntries(env: Env, q: string, limit = 20): Promise<EntryRow[]> {
	const norm = normalize(q);
	if (!norm) return [];

	// Step 1: exact match (uses idx_norm, ~1ms).
	const exact = await env.DB.prepare(
		'SELECT id, headword_norm, headword_iast, dict_slug, priority, ' +
		'snippet_short, body_ko, target_lang ' +
		'FROM entries WHERE headword_norm = ?1 ' +
		'ORDER BY priority ASC LIMIT ?2'
	)
		.bind(norm, limit)
		.all<EntryRow>();

	let rows = exact.results ?? [];

	// Step 2: if exact returned fewer than half the limit, augment with prefix
	// matches. Uses LIKE 'norm%' which uses idx_norm via leftmost prefix.
	// Skip if norm is too short (<= 2 chars) — would match too broadly.
	if (rows.length < limit / 2 && norm.length > 2) {
		const need = limit - rows.length;
		const prefix = await env.DB.prepare(
			'SELECT id, headword_norm, headword_iast, dict_slug, priority, ' +
			'snippet_short, body_ko, target_lang ' +
			'FROM entries WHERE headword_norm > ?1 AND headword_norm < ?2 ' +
			'ORDER BY priority ASC, headword_norm ASC LIMIT ?3'
		)
			.bind(norm, norm + '￿', need)
			.all<EntryRow>();
		// Dedup by id (exact + prefix can overlap)
		const seen = new Set(rows.map((r) => r.id));
		for (const r of prefix.results ?? []) {
			if (!seen.has(r.id)) {
				rows.push(r);
				seen.add(r.id);
			}
		}
	}

	return rows;
}

async function getEntry(env: Env, id: string): Promise<EntryRow | null> {
	const r = await env.DB.prepare(
		'SELECT id, headword_norm, headword_iast, dict_slug, priority, ' +
		'snippet_short, body_ko, target_lang ' +
		'FROM entries WHERE id = ?1 LIMIT 1'
	)
		.bind(id)
		.first<EntryRow>();
	return r;
}

export default {
	async fetch(request: Request, env: Env): Promise<Response> {
		// CORS preflight
		if (request.method === 'OPTIONS') {
			return new Response(null, { status: 204, headers: CORS });
		}
		if (request.method !== 'GET') {
			return json({ error: 'Method not allowed' }, { status: 405 });
		}

		const url = new URL(request.url);
		const path = url.pathname;

		// /api/health
		if (path === '/api/health') {
			return json({ ok: true, ts: Date.now() }, {
				headers: { 'Cache-Control': 'no-store' }
			});
		}

		// /api/search/:norm — top-20 by default; ?limit=N for override
		if (path.startsWith('/api/search/')) {
			const q = decodeURIComponent(path.slice('/api/search/'.length));
			if (!q) return json({ error: 'Empty query' }, { status: 400 });
			const limit = Math.min(50, Math.max(1, Number(url.searchParams.get('limit') ?? '20')));
			try {
				const results = await searchEntries(env, q, limit);
				return json(
					{ query: q, count: results.length, results },
					{ headers: { 'Cache-Control': results.length > 0 ? CACHE_OK : CACHE_404 } }
				);
			} catch (e) {
				return json({ error: String(e) }, { status: 500 });
			}
		}

		// /api/entry/:id
		if (path.startsWith('/api/entry/')) {
			const id = decodeURIComponent(path.slice('/api/entry/'.length));
			if (!id) return json({ error: 'Empty id' }, { status: 400 });
			try {
				const r = await getEntry(env, id);
				if (!r) {
					return json(
						{ error: 'Not found', id },
						{ status: 404, headers: { 'Cache-Control': CACHE_404 } }
					);
				}
				return json(r, { headers: { 'Cache-Control': CACHE_OK } });
			} catch (e) {
				return json({ error: String(e) }, { status: 500 });
			}
		}

		return json({ error: 'Not found', path }, { status: 404 });
	}
};
