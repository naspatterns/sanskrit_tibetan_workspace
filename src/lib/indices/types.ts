// IndexBundle — shape of all 5 indices after fetch+fzstd+msgpack/text decode.
//
// Source of truth for the on-disk schemas:
//   - tier0/equivalents:        scripts/build_tier0.py / scripts/build_equivalents_index.py
//   - reverse_en/reverse_ko:    scripts/build_reverse_index.py
//   - headwords.txt:            scripts/build_fst.py (one "<norm>\t<iast>" per line, sorted)

export interface Tier0Result {
	dict: string;
	short: string;
	priority: number;
	tier: number;
	id: string;
	snippet_short: string;
	snippet_medium: string;
	ko: string;
	target_lang: string;
}

export interface Tier0Entry {
	iast: string;
	entries: Tier0Result[];
}

export interface EquivRow {
	sources: string[];
	skt_iast?: string;
	tib_wylie?: string;
	zh?: string;
	ko?: string;
	en?: string;
	ja?: string;
	de?: string;
	category?: string;
	note?: string;
	synonyms?: string[];
}

export interface HeadwordEntry {
	norm: string;
	iast: string;
}

export interface IndexBundle {
	tier0: Map<string, Tier0Entry>;
	/** Phase 3.3 (D-Tib10K) — Tibetan top-10K. Same shape as tier0; the
	 * search engine merges entries when a key exists in both (cross-language
	 * headword like 'chos'). */
	tier0Bo: Map<string, Tier0Entry>;
	equivalents: Map<string, EquivRow[]>;
	reverseEn: Map<string, string[]>;
	reverseKo: Map<string, string[]>;
	headwords: HeadwordEntry[];
	/** Phase 3.5 — Heritage Declension paradigms keyed by headword_norm.
	 * Eager-loaded (2.1 MB compressed) to avoid the lazy-promise race
	 * hang in dev/HMR; the /declension route reads this directly. */
	declension: Map<string, DeclensionRow[]>;
}

export interface DeclensionRow {
	iast: string;
	body: string;
	dict: string;
}

// ─── Loader progress ────────────────────────────────────────────────────

export type LoadStage = 'pending' | 'fetching' | 'decompressing' | 'decoding' | 'done' | 'error';

export interface IndexLoadStatus {
	name: string;
	stage: LoadStage;
	bytesFetched: number;
	compressedSize: number;
	decompressedSize: number;
	errorMessage?: string;
}

export interface LoadProgress {
	status: IndexLoadStatus[];
	overallStage: 'pending' | 'fetching' | 'decoding' | 'done' | 'error';
	totalCompressedBytes: number;
	totalDecompressedBytes: number;
}
