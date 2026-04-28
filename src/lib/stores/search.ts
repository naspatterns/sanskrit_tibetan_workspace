// Search helper. Stateless wrapper — Svelte 5 runes hold the actual reactive
// state in the component (+page.svelte). Module-level Svelte runes work too,
// but a single search page doesn't need cross-component reactivity yet.

import { search, type SearchResult } from '$lib/search/engine';
import { getIndexBundle, isIndexLoaded } from '$lib/indices/store';

export function performSearch(query: string): SearchResult | null {
	if (!query.trim() || !isIndexLoaded()) return null;
	return search(getIndexBundle(), query);
}
