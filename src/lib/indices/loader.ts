// Eager loader for all 5 indices (ADR-011 D). Fetches in parallel, decompresses
// with fzstd, decodes with @msgpack/msgpack (or TextDecoder for headwords).
// Returns an IndexBundle whose Map.get is the search engine's hot path (<1 ms).

import { decompress } from 'fzstd';
import { decode } from '@msgpack/msgpack';
import type {
	DeclensionRow,
	EquivRow,
	HeadwordEntry,
	IndexBundle,
	IndexLoadStatus,
	LoadProgress,
	ReverseMetaBundle,
	Tier0Entry,
} from './types';

interface IndexSpec {
	key: keyof IndexBundle;
	url: string;
	decoder: 'msgpack' | 'text';
}

const INDICES: IndexSpec[] = [
	{ key: 'tier0', url: '/indices/tier0.msgpack.zst', decoder: 'msgpack' },
	{ key: 'tier0Bo', url: '/indices/tier0-bo.msgpack.zst', decoder: 'msgpack' },
	// Phase 3.7 follow-up (Option A) — top-10K..20K Sanskrit. Separate file
	// because top-20K combined exceeds Cloudflare 25 MiB single-file limit.
	{ key: 'tier0Extended', url: '/indices/tier0-extended.msgpack.zst', decoder: 'msgpack' },
	{ key: 'equivalents', url: '/indices/equivalents.msgpack.zst', decoder: 'msgpack' },
	{ key: 'reverseEn', url: '/indices/reverse_en.msgpack.zst', decoder: 'msgpack' },
	{ key: 'reverseKo', url: '/indices/reverse_ko.msgpack.zst', decoder: 'msgpack' },
	// Phase 3.6 P0-1 — reverse search hit meta (id → [iast, dict_idx])
	{ key: 'reverseMeta', url: '/indices/reverse_meta.msgpack.zst', decoder: 'msgpack' },
	{ key: 'declension', url: '/indices/declension.msgpack.zst', decoder: 'msgpack' },
	{ key: 'headwords', url: '/indices/headwords.txt.zst', decoder: 'text' }
];

async function fetchAndDecode(
	spec: IndexSpec,
	status: IndexLoadStatus,
	onProgress: () => void
): Promise<unknown> {
	status.stage = 'fetching';
	onProgress();

	const resp = await fetch(spec.url);
	if (!resp.ok) {
		status.stage = 'error';
		status.errorMessage = `HTTP ${resp.status}`;
		onProgress();
		throw new Error(`fetch ${spec.url}: ${resp.status}`);
	}
	const compressed = new Uint8Array(await resp.arrayBuffer());
	status.bytesFetched = compressed.length;
	status.compressedSize = compressed.length;

	status.stage = 'decompressing';
	onProgress();
	// fzstd decompress is sync. Yield to the event loop so the splash UI
	// repaints between heavy operations (each index can take 100s of ms).
	await new Promise((r) => setTimeout(r, 0));
	const raw = decompress(compressed);
	status.decompressedSize = raw.length;

	status.stage = 'decoding';
	onProgress();
	await new Promise((r) => setTimeout(r, 0));
	const parsed = spec.decoder === 'msgpack' ? decode(raw) : new TextDecoder('utf-8').decode(raw);

	status.stage = 'done';
	onProgress();
	return parsed;
}

// Helpers exposed for unit testing (Phase 3.6 P1-D8-2). Internal to module
// otherwise — callers should use loadAllIndices().
export function objectToMap<V>(obj: unknown): Map<string, V> {
	return new Map(Object.entries(obj as Record<string, V>));
}

export function parseHeadwords(text: string): HeadwordEntry[] {
	const lines = text.split('\n');
	const out: HeadwordEntry[] = [];
	for (const line of lines) {
		if (!line) continue;
		const tab1 = line.indexOf('\t');
		if (tab1 === -1) continue;
		const tab2 = line.indexOf('\t', tab1 + 1);
		// Phase 3.7 follow-ups: tolerate three TSV layouts simultaneously.
		//   2-col legacy:    norm \t iast               (rank=999_999, upa="")
		//   3-col rank:      norm \t iast \t rank       (upa="")
		//   4-col upasarga:  norm \t iast \t rank \t upasarga
		if (tab2 === -1) {
			out.push({
				norm: line.slice(0, tab1),
				iast: line.slice(tab1 + 1),
				rank: 999_999,
				upasarga: ''
			});
			continue;
		}
		const tab3 = line.indexOf('\t', tab2 + 1);
		if (tab3 === -1) {
			const rank = Number(line.slice(tab2 + 1));
			out.push({
				norm: line.slice(0, tab1),
				iast: line.slice(tab1 + 1, tab2),
				rank: Number.isFinite(rank) ? rank : 999_999,
				upasarga: ''
			});
		} else {
			const rank = Number(line.slice(tab2 + 1, tab3));
			out.push({
				norm: line.slice(0, tab1),
				iast: line.slice(tab1 + 1, tab2),
				rank: Number.isFinite(rank) ? rank : 999_999,
				upasarga: line.slice(tab3 + 1)
			});
		}
	}
	// build_fst.py emits sorted by norm; preserve order for binary search.
	return out;
}

export function recomputeOverall(status: IndexLoadStatus[]): LoadProgress['overallStage'] {
	if (status.some((s) => s.stage === 'error')) return 'error';
	if (status.every((s) => s.stage === 'done')) return 'done';
	if (status.some((s) => s.stage === 'decoding' || s.stage === 'decompressing')) return 'decoding';
	if (status.some((s) => s.stage === 'fetching')) return 'fetching';
	return 'pending';
}

export async function loadAllIndices(
	onProgressUpdate: (progress: LoadProgress) => void
): Promise<IndexBundle> {
	const status: IndexLoadStatus[] = INDICES.map((s) => ({
		name: s.key,
		stage: 'pending',
		bytesFetched: 0,
		compressedSize: 0,
		decompressedSize: 0
	}));

	const emit = () => {
		const totalCompressedBytes = status.reduce((acc, s) => acc + s.compressedSize, 0);
		const totalDecompressedBytes = status.reduce((acc, s) => acc + s.decompressedSize, 0);
		onProgressUpdate({
			status: status.map((s) => ({ ...s })),
			overallStage: recomputeOverall(status),
			totalCompressedBytes,
			totalDecompressedBytes
		});
	};
	emit();

	const results = await Promise.all(
		INDICES.map((spec, i) => fetchAndDecode(spec, status[i], emit))
	);

	const [
		tier0Raw,
		tier0BoRaw,
		tier0ExtendedRaw,
		equivRaw,
		revEnRaw,
		revKoRaw,
		revMetaRaw,
		declRaw,
		headwordsRaw
	] = results;
	const bundle: IndexBundle = {
		tier0: objectToMap<Tier0Entry>(tier0Raw),
		tier0Bo: objectToMap<Tier0Entry>(tier0BoRaw),
		tier0Extended: objectToMap<Tier0Entry>(tier0ExtendedRaw),
		equivalents: objectToMap<EquivRow[]>(equivRaw),
		reverseEn: objectToMap<string[]>(revEnRaw),
		reverseKo: objectToMap<string[]>(revKoRaw),
		reverseMeta: parseReverseMeta(revMetaRaw),
		declension: objectToMap<DeclensionRow[]>(declRaw),
		headwords: parseHeadwords(headwordsRaw as string)
	};

	emit();
	return bundle;
}

/** Decode reverse_meta.msgpack.zst payload into a typed ReverseMetaBundle. */
export function parseReverseMeta(raw: unknown): ReverseMetaBundle {
	const obj = raw as { dicts?: string[]; ids?: Record<string, [string, number]> };
	return {
		dicts: obj.dicts ?? [],
		ids: new Map(Object.entries(obj.ids ?? {}))
	};
}
