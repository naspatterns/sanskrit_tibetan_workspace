// Search helper. Stateless wrapper — Svelte 5 runes hold the actual reactive
// state in the component (+page.svelte). Module-level Svelte runes work too,
// but a single search page doesn't need cross-component reactivity yet.

import { search, type SearchResult } from '$lib/search/engine';
import { getIndexBundle } from '$lib/indices/store';

export function performSearch(query: string): SearchResult | null {
	if (!query.trim()) return null;
	// Phase 4.1 (2026-05-08): no isIndexLoaded() short-circuit. The bundle
	// starts with empty Maps and the engine handles that — every Map.get
	// just returns undefined. Empty local results then trigger the Phase 5
	// Edge API fallback in +page.svelte, so first-paint search works
	// before any index is loaded.
	return search(getIndexBundle(), query);
}
