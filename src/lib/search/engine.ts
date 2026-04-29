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
	// over Sanskrit and Tibetan top-10K. When a headword exists in both
	// (e.g. 'chos' is in skt cross-ref and bo native), merge entries.
	const sktInfo = bundle.tier0.get(iastKey);
	const boInfo = bundle.tier0Bo.get(iastKey);
	const exact: Tier0Entry | null =
		sktInfo && boInfo
			? {
					iast: sktInfo.iast,
					// Concatenate; client-side langBalancedTop will balance Zone C.
					entries: [...sktInfo.entries, ...boInfo.entries]
				}
			: (sktInfo ?? boInfo ?? null);

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

// Lower-bound binary search → walk forward while prefix matches, capped.
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
	const out: HeadwordEntry[] = [];
	for (let i = lo; i < headwords.length && out.length < limit; i++) {
		if (!headwords[i].norm.startsWith(prefix)) break;
		out.push(headwords[i]);
	}
	return out;
}
