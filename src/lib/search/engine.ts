// Search engine — single function `search(bundle, query)` → typed SearchResult.
// All channels resolved in one shot via Map.get (each <1 ms). No fetch, no
// async — the IndexBundle is loaded eagerly per ADR-011 (D).
//
// Channel routing:
//   tier0          ← norm(query) for the IAST-side definition lookup
//   equivalents    ← 3 channels (IAST norm / Wylie norm / 한자 raw) merged unique
//   reverse_en     ← lowercased ASCII query (English gloss → entry IDs)
//   reverse_ko     ← raw Korean query (Korean gloss → entry IDs)
//   headwords      ← sorted prefix binary-search for autocomplete

import type {
	EquivRow,
	HeadwordEntry,
	IndexBundle,
	Tier0Entry
} from '$lib/indices/types';
import { detectScript, normalize, normalizeHeadword, type Script } from './transliterate';

export interface ReverseHit {
	language: 'en' | 'ko';
	token: string;
	entryIds: string[];
}

export interface SearchResult {
	query: string;
	detectedScript: Script;
	exact: Tier0Entry | null;
	equivalents: EquivRow[];
	reverse: ReverseHit[];
	partial: HeadwordEntry[];
	durationMs: number;
}

export interface SearchOptions {
	partialLimit?: number;
}

export function search(
	bundle: IndexBundle,
	rawQuery: string,
	options: SearchOptions = {}
): SearchResult {
	const t0 = performance.now();
	const partialLimit = options.partialLimit ?? 20;

	const trimmed = rawQuery.trim();
	if (!trimmed) {
		return {
			query: rawQuery,
			detectedScript: 'empty',
			exact: null,
			equivalents: [],
			reverse: [],
			partial: [],
			durationMs: 0
		};
	}

	const script = detectScript(trimmed);

	// Per-channel keys.
	const iastKey = normalizeHeadword(trimmed); // skt-side
	const wylieKey = normalize(trimmed); // tib/Latin-side, no script conv
	const zhKey = trimmed; // CJK as-is

	// 1. Exact tier0 (definition top-3 + rest). Phase 3.3 (D-Tib10K) — union
	// over Sanskrit and Tibetan top-10K. Phase 3.7 (Option A) — also union
	// against tier0-extended (top-10K..20K). When a headword exists in
	// multiple, merge entries (preserving sktInfo iast as primary).
	const sktInfo = bundle.tier0.get(iastKey);
	const sktExtInfo = bundle.tier0Extended.get(iastKey);
	const boInfo = bundle.tier0Bo.get(iastKey);
	const sources: Tier0Entry[] = [];
	if (sktInfo) sources.push(sktInfo);
	if (sktExtInfo && sktExtInfo !== sktInfo) sources.push(sktExtInfo);
	if (boInfo && boInfo !== sktInfo && boInfo !== sktExtInfo) sources.push(boInfo);
	let exact: Tier0Entry | null = sources.length === 0
		? null
		: sources.length === 1
			? sources[0]
			: {
					iast: sources[0].iast,
					// Concatenate; client-side langBalancedTop will balance Zone C.
					entries: sources.flatMap((s) => s.entries)
				};

	// Phase 3.7 (Option E): multi-word fallback. When a phrase like
	// `tat tvam asi` doesn't match the joined key, split on whitespace and
	// merge tier0 entries for each token. Useful for upaniṣadic mahāvākyas
	// and short Sanskrit citations. Skip if exact already hit (single-word
	// behaviour preserved).
	if (!exact && iastKey.includes(' ')) {
		const multiSources: Tier0Entry[] = [];
		const seenIasts = new Set<string>();
		for (const token of iastKey.split(/\s+/).filter(Boolean)) {
			for (const map of [bundle.tier0, bundle.tier0Extended, bundle.tier0Bo]) {
				const slot = map.get(token);
				if (slot && !seenIasts.has(slot.iast)) {
					multiSources.push(slot);
					seenIasts.add(slot.iast);
					break; // first source for this token
				}
			}
		}
		if (multiSources.length > 0) {
			exact = {
				iast: multiSources.map((s) => s.iast).join(' '),
				entries: multiSources.flatMap((s) => s.entries)
			};
		}
	}

	// 2. Equivalents — try all 3 channels, merge unique row references.
	// Build-side rows are interned per dedup key, so reference equality is
	// a valid uniqueness test even across multiple Map.get returns.
	const equivSeen = new Set<EquivRow>();
	const equivalents: EquivRow[] = [];
	const tryEquiv = (key: string) => {
		if (!key) return;
		const rows = bundle.equivalents.get(key);
		if (!rows) return;
		for (const r of rows) {
			if (!equivSeen.has(r)) {
				equivSeen.add(r);
				equivalents.push(r);
			}
		}
	};
	tryEquiv(iastKey);
	if (wylieKey !== iastKey) tryEquiv(wylieKey);
	if (script === 'cjk') tryEquiv(zhKey);

	// 3. Reverse lookup (English / Korean gloss → entry IDs).
	// Reverse channels keyed differently:
	//   reverseEn: lowercase ASCII tokens (no diacritics, no HK signatures)
	//   reverseKo: raw Hangul / Hanja tokens
	const reverse: ReverseHit[] = [];
	if (script === 'iast' && /^[a-z'\-]+$/.test(trimmed.toLowerCase())) {
		const ids = bundle.reverseEn.get(trimmed.toLowerCase());
		if (ids) reverse.push({ language: 'en', token: trimmed.toLowerCase(), entryIds: ids });
	}
	if (script === 'korean') {
		const ids = bundle.reverseKo.get(trimmed);
		if (ids) reverse.push({ language: 'ko', token: trimmed, entryIds: ids });
	}

	// 4. Prefix autocomplete from headwords.txt (sorted by norm).
	const partial = prefixSearch(bundle.headwords, iastKey, partialLimit);

	return {
		query: rawQuery,
		detectedScript: script,
		exact,
		equivalents,
		reverse,
		partial,
		durationMs: performance.now() - t0
	};
}

// Lower-bound binary search → walk forward while prefix matches.
// Phase 3.7 follow-up: collect ALL matching candidates (common prefix matches
// 1-10K entries; sorting is cheap), then sort by:
//   1. upasarga-match bonus (when prefix exactly is a known upasarga, entries
//      tagged with that upasarga rank above untagged ones)
//   2. rank ASC (top-10K first)
//   3. norm length ASC, alphabetic
// Returns top `limit`. Surfaces common terms above HTML extraction noise —
// e.g. `dha` returns dharma/dhātu/dhana instead of dha/dhaaraa/dhaa.
//
// Hard cap defends against pathological prefixes (e.g. empty string).
const PREFIX_CANDIDATE_CAP = 20_000;

function prefixSearch(
	headwords: HeadwordEntry[],
	prefix: string,
	limit: number
): HeadwordEntry[] {
	if (!prefix || headwords.length === 0) return [];
	let lo = 0;
	let hi = headwords.length;
	while (lo < hi) {
		const mid = (lo + hi) >>> 1;
		if (headwords[mid].norm < prefix) {
			lo = mid + 1;
		} else {
			hi = mid;
		}
	}
	const candidates: HeadwordEntry[] = [];
	for (let i = lo; i < headwords.length && candidates.length < PREFIX_CANDIDATE_CAP; i++) {
		if (!headwords[i].norm.startsWith(prefix)) break;
		candidates.push(headwords[i]);
	}
	if (candidates.length === 0) return [];
	// Phase 3.7 follow-up — upasarga awareness. If the user's typed prefix
	// exactly matches one of the canonical upasarga forms recorded in
	// `entry.upasarga` for ANY of our candidates, treat that as a strong
	// signal: surface upasarga-tagged words first. Computed lazily from the
	// candidate set itself (no extra index — the upasarga string IS the
	// prefix when this applies).
	const upasargaQuery = candidates.some((c) => c.upasarga === prefix) ? prefix : '';
	candidates.sort((a, b) => {
		if (upasargaQuery) {
			const aHit = a.upasarga === upasargaQuery ? 0 : 1;
			const bHit = b.upasarga === upasargaQuery ? 0 : 1;
			if (aHit !== bHit) return aHit - bHit;
		}
		if (a.rank !== b.rank) return a.rank - b.rank;
		if (a.norm.length !== b.norm.length) return a.norm.length - b.norm.length;
		return a.norm < b.norm ? -1 : a.norm > b.norm ? 1 : 0;
	});
	return candidates.slice(0, limit);
}
