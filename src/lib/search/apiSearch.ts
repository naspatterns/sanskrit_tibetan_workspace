// Phase 5 — Edge API fallback for the SvelteKit client.
//
// When the synchronous in-memory search misses (no tier0/extended/bo hit
// AND no equivalents row keyed by the query), the UI calls this module to
// fetch from the D1-backed Workers API at `https://stw-api.naspatterns.workers.dev`.
//
// Response is shaped as `ApiSearchResponse` (see indices/types.ts). The UI
// renders rows in Zone C just like local tier0 entries; full body is lazy-
// fetched on click via /api/entry/:id (TODO Phase 5e).
//
// AbortSignal support: callers can cancel an in-flight request when the user
// types a new character (debounced) — preventing stale results from
// overwriting fresh local search output.

import type { ApiSearchResponse } from '$lib/indices/types';

// Workers API origin. In production behind same-domain via Pages Functions
// rewrite, this would be relative `/api/...`. For now it's the bare
// workers.dev URL since Pages routing isn't set up yet.
const API_ORIGIN = 'https://stw-api.naspatterns.workers.dev';

export interface SearchEdgeOptions {
	limit?: number;
	signal?: AbortSignal;
}

export async function searchEdgeApi(
	query: string,
	options: SearchEdgeOptions = {}
): Promise<ApiSearchResponse | null> {
	const trimmed = query.trim();
	if (!trimmed) return null;
	const limit = Math.min(50, Math.max(1, options.limit ?? 20));
	const url = `${API_ORIGIN}/api/search/${encodeURIComponent(trimmed)}?limit=${limit}`;
	try {
		const res = await fetch(url, { signal: options.signal });
		if (!res.ok) {
			console.warn(`[apiSearch] HTTP ${res.status} for ${trimmed}`);
			return null;
		}
		const data = (await res.json()) as ApiSearchResponse;
		return data;
	} catch (err) {
		// Abort is expected when user types fast; don't pollute console.
		if (err instanceof Error && err.name === 'AbortError') return null;
		console.warn('[apiSearch] fetch failed:', err);
		return null;
	}
}

// Sprint 1 A4 — Edge-served autocomplete for lazy-mode users. Local
// autocomplete reads from `bundle.headwords` which is part of the core
// tier; lazy users never load that file so the dropdown is empty until
// a query lands. This RPC closes the gap.

export interface AutocompleteEdgeItem {
	norm: string;
	iast: string;
}

export interface AutocompleteEdgeResponse {
	prefix: string;
	count: number;
	results: AutocompleteEdgeItem[];
}

export async function autocompleteEdgeApi(
	prefix: string,
	options: SearchEdgeOptions = {}
): Promise<AutocompleteEdgeResponse | null> {
	const trimmed = prefix.trim();
	if (trimmed.length < 2) return null;
	const limit = Math.min(20, Math.max(1, options.limit ?? 10));
	const url = `${API_ORIGIN}/api/autocomplete/${encodeURIComponent(trimmed)}?limit=${limit}`;
	try {
		const res = await fetch(url, { signal: options.signal });
		if (!res.ok) {
			console.warn(`[apiSearch] autocomplete HTTP ${res.status} for ${trimmed}`);
			return null;
		}
		const data = (await res.json()) as AutocompleteEdgeResponse;
		return data;
	} catch (err) {
		if (err instanceof Error && err.name === 'AbortError') return null;
		console.warn('[apiSearch] autocomplete fetch failed:', err);
		return null;
	}
}
