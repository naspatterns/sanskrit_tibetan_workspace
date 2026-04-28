// Eager loader for all 5 indices (ADR-011 D). Fetches in parallel, decompresses
// with fzstd, decodes with @msgpack/msgpack (or TextDecoder for headwords).
// Returns an IndexBundle whose Map.get is the search engine's hot path (<1 ms).

import { decompress } from 'fzstd';
import { decode } from '@msgpack/msgpack';
import type {
	EquivRow,
	HeadwordEntry,
	IndexBundle,
	IndexLoadStatus,
	LoadProgress,
	Tier0Entry,
} from './types';

interface IndexSpec {
	key: keyof IndexBundle;
	url: string;
	decoder: 'msgpack' | 'text';
}

const INDICES: IndexSpec[] = [
	{ key: 'tier0', url: '/indices/tier0.msgpack.zst', decoder: 'msgpack' },
	{ key: 'equivalents', url: '/indices/equivalents.msgpack.zst', decoder: 'msgpack' },
	{ key: 'reverseEn', url: '/indices/reverse_en.msgpack.zst', decoder: 'msgpack' },
	{ key: 'reverseKo', url: '/indices/reverse_ko.msgpack.zst', decoder: 'msgpack' },
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

function objectToMap<V>(obj: unknown): Map<string, V> {
	return new Map(Object.entries(obj as Record<string, V>));
}

function parseHeadwords(text: string): HeadwordEntry[] {
	const lines = text.split('\n');
	const out: HeadwordEntry[] = [];
	for (const line of lines) {
		if (!line) continue;
		const tab = line.indexOf('\t');
		if (tab === -1) continue;
		out.push({ norm: line.slice(0, tab), iast: line.slice(tab + 1) });
	}
	// build_fst.py emits sorted by norm; preserve order for binary search.
	return out;
}

function recomputeOverall(status: IndexLoadStatus[]): LoadProgress['overallStage'] {
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

	const [tier0Raw, equivRaw, revEnRaw, revKoRaw, headwordsRaw] = results;
	const bundle: IndexBundle = {
		tier0: objectToMap<Tier0Entry>(tier0Raw),
		equivalents: objectToMap<EquivRow[]>(equivRaw),
		reverseEn: objectToMap<string[]>(revEnRaw),
		reverseKo: objectToMap<string[]>(revKoRaw),
		headwords: parseHeadwords(headwordsRaw as string)
	};

	emit();
	return bundle;
}
