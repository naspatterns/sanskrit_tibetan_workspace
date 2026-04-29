// Heuristic language tag for Tier 0 entries — needed for lang-balanced
// top-3 routing in Zone C. The tier0 entry only carries `dict` (slug)
// and `target_lang`, neither of which directly says "this is a Sanskrit
// dict" vs "Tibetan dict". We classify by dict slug prefix.

import type { Tier0Result } from '$lib/indices/types';

export type EntryLang = 'sa' | 'bo' | 'pi' | 'other';

export function entryLang(entry: Tier0Result): EntryLang {
	// target_lang is the language of the definition prose. Tibetan dicts
	// emit `bo`; Sanskrit-side dicts emit `en`/`de`/`fr`/`la`/`sa`.
	if (entry.target_lang === 'bo') return 'bo';
	if (entry.target_lang === 'pi') return 'pi';
	const d = entry.dict;
	if (d.startsWith('tib-')) return 'bo';
	if (d.includes('-pali') || d.includes('pali-')) return 'pi';
	// Sanskrit-side: apte/monier/macdonell/bhsd/cappeller/bopp/...
	return 'sa';
}

/**
 * Lang-balanced top-N: take up to N best per language by priority,
 * concatenate skt → bo → others. Prevents Zone C from being dominated
 * by Sanskrit dicts when the query is a Tibetan word (or vice versa).
 */
export function langBalancedTop(entries: Tier0Result[], perLang = 3): Tier0Result[] {
	const groups = new Map<EntryLang, Tier0Result[]>();
	for (const e of entries) {
		const lang = entryLang(e);
		if (!groups.has(lang)) groups.set(lang, []);
		groups.get(lang)!.push(e);
	}
	// Each group already arrives priority-asc (build_tier0 sorts).
	const sa = groups.get('sa')?.slice(0, perLang) ?? [];
	const bo = groups.get('bo')?.slice(0, perLang) ?? [];
	const pi = groups.get('pi')?.slice(0, perLang) ?? [];
	const other = groups.get('other')?.slice(0, perLang) ?? [];
	return [...sa, ...bo, ...pi, ...other];
}

/** Remaining after lang-balanced top-N is taken — for Zone D. */
export function langBalancedRest(entries: Tier0Result[], perLang = 3): Tier0Result[] {
	const top = new Set(langBalancedTop(entries, perLang).map((e) => e.id));
	return entries.filter((e) => !top.has(e.id));
}
