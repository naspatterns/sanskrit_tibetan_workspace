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

/** Phase 5 — Edge API fallback row from D1 (workers/src/index.ts).
 * Subset of full entry; full body lazy-fetched via /api/entry/:id (Phase 5e). */
export interface ApiSearchRow {
	id: string;
	headword_norm: string;
	headword_iast: string;
	dict_slug: string;
	priority: number;
	snippet_short: string | null;
	body_ko: string | null;
	target_lang: string;
}

export interface ApiSearchResponse {
	query: string;
	count: number;
	results: ApiSearchRow[];
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
	/** Phase 3.7 follow-up: 1-based top-10K rank (lower = more important).
	 * Long-tail headwords use 999_999. Used by prefix engine to re-rank
	 * match candidates so common terms surface above HTML extraction noise. */
	rank: number;
	/** Phase 3.7 follow-up: single canonical upasarga matching the start of
	 * `norm`, or empty string. For Sanskrit (`pra`, `prati`, `vi`, `sam`,
	 * `abhi`, etc.) and Tibetan equivalents (`rab tu`, `rnam par`, `kun`,
	 * `mngon par`). Single (not chained). Used by prefix engine to surface
	 * upasarga-tagged matches in a separate tier when the user types a
	 * known upasarga. */
	upasarga: string;
}

export interface IndexBundle {
	tier0: Map<string, Tier0Entry>;
	/** Phase 3.3 (D-Tib10K) — Tibetan top-10K. Same shape as tier0; the
	 * search engine merges entries when a key exists in both (cross-language
	 * headword like 'chos'). */
	tier0Bo: Map<string, Tier0Entry>;
	/** Phase 3.7 follow-up (Option A) — Sanskrit ranks 10001..20000. Same
	 * shape as tier0; the search engine union-lookups all three so canonical
	 * Buddhist/philosophical terms outside the top-10K (e.g. mid-frequency
	 * Vedic deities, secondary commentary terms) still ship with snippets. */
	tier0Extended: Map<string, Tier0Entry>;
	equivalents: Map<string, EquivRow[]>;
	reverseEn: Map<string, string[]>;
	reverseKo: Map<string, string[]>;
	headwords: HeadwordEntry[];
	/** Phase 3.5 — Heritage Declension paradigms keyed by headword_norm.
	 * Eager-loaded (2.1 MB compressed) to avoid the lazy-promise race
	 * hang in dev/HMR; the /declension route reads this directly. */
	declension: Map<string, DeclensionRow[]>;
	/** Phase 3.6 P0-1 — entry_id → [iast, dict_slug] meta for reverse search
	 * results. Without this, the UI shows raw entry_ids and users can't tell
	 * which Sanskrit/Tibetan word matched their English/Korean gloss.
	 * Compact schema: dict slugs deduped to a separate array (~148 strings),
	 * each id maps to [iast, dict_idx] to keep size under Cloudflare 25 MiB
	 * cap. snippet_short omitted — full body via Phase 5 D1 Edge API.
	 * Top-30 entries per token only (UI shows 30); deeper hits would need
	 * the same lazy fetch path. */
	reverseMeta: ReverseMetaBundle;
}

export interface ReverseMetaBundle {
	dicts: string[];
	/** entry_id → [headword_iast, dict_index_into_dicts] */
	ids: Map<string, [string, number]>;
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
