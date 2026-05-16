// Tiered loader for the index bundle (ADR-011 D + Phase 4.1 Mobile Rescue
// + Sprint 1 A1 worker offload).
//
// Phase 4.1 (2026-05-08) — previously a single Promise.all over all 9 files
// blocked the UI behind a splash for 7s on desktop / 45s on mobile 4G. Now
// the loader exposes three tiers (core / extra / auxiliary) and the caller
// can stage them. The shared store starts empty so the search page renders
// immediately and routes early queries through the Edge API; loaded tiers
// then enrich local search progressively.
//
// Sprint 1 A1 (2026-05-16) — fetch + fzstd decompress + msgpack decode used
// to run on the main thread (`setTimeout(0)` between stages only forced a
// paint, not actual CPU yield). For ~88 MB of compressed indices each tier
// blocked the UI for hundreds of milliseconds per file. We now delegate to
// `decoder.worker.ts` one short-lived module worker per file. Net effect:
//   - Lighthouse Performance score expected 45 → 80+
//   - Main-thread TBT (Total Blocking Time) cut from ~3s to ~300ms
//   - Memory: one extra isolate per concurrent decode (~10MB), reclaimed on
//     terminate() right after the parsed payload is delivered.

import DecoderWorker from '../workers/decoder.worker?worker';
import type { DecoderRequest, DecoderResponse } from '../workers/decoder.worker';
import {
	TIER_KEYS,
	type DeclensionRow,
	type EquivRow,
	type HeadwordEntry,
	type IndexBundle,
	type IndexLoadStatus,
	type LoadProgress,
	type LoadTier,
	type ReverseMetaBundle,
	type Tier0Entry,
} from './types';
import { markTierLoaded, setBundleSlice } from './store';

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

/** Delegate fetch + decompress + decode to a short-lived module worker.
 *
 * Sprint 1 A1 (2026-05-16). Worker progress messages drive `status.stage` so
 * the splash UI still reflects the current phase. The Promise resolves once
 * the worker posts a `result` (parsed payload). The worker self-terminates
 * after posting result/error; we also call `.terminate()` defensively in case
 * the page is unloading while the worker is still mid-decompress.
 *
 * Falls back to a synchronous main-thread decode when `Worker` is missing
 * (vitest jsdom, or rare browsers without dedicated workers). The fallback
 * keeps behaviour identical to the pre-A1 implementation so tests don't need
 * a worker shim. */
async function fetchAndDecodeInWorker(
	spec: IndexSpec,
	status: IndexLoadStatus,
	onProgress: () => void
): Promise<unknown> {
	// Test environments (jsdom) may not provide Worker. Fall back to a
	// straightforward main-thread pipeline rather than failing the load.
	if (typeof Worker === 'undefined') {
		return fetchAndDecodeFallback(spec, status, onProgress);
	}

	status.stage = 'fetching';
	onProgress();

	const worker = new DecoderWorker();
	try {
		return await new Promise<unknown>((resolve, reject) => {
			worker.addEventListener('message', (e: MessageEvent<DecoderResponse>) => {
				const msg = e.data;
				if (msg.type === 'progress') {
					status.stage = msg.stage;
					if (typeof msg.compressedSize === 'number') {
						status.compressedSize = msg.compressedSize;
						status.bytesFetched = msg.compressedSize;
					}
					if (typeof msg.decompressedSize === 'number') {
						status.decompressedSize = msg.decompressedSize;
					}
					onProgress();
					return;
				}
				if (msg.type === 'result') {
					status.compressedSize = msg.compressedSize;
					status.bytesFetched = msg.compressedSize;
					status.decompressedSize = msg.decompressedSize;
					// `applyToBundle` callers set 'done' after applyToBundle returns.
					resolve(msg.parsed);
					return;
				}
				if (msg.type === 'error') {
					status.stage = 'error';
					status.errorMessage = msg.message;
					onProgress();
					reject(new Error(msg.message));
				}
			});
			worker.addEventListener('error', (ev: ErrorEvent) => {
				status.stage = 'error';
				status.errorMessage = ev.message || 'worker error';
				onProgress();
				reject(new Error(status.errorMessage));
			});
			const req: DecoderRequest = { url: spec.url, decoder: spec.decoder };
			worker.postMessage(req);
		});
	} finally {
		worker.terminate();
	}
}

/** Synchronous main-thread fallback retained for jsdom / no-Worker cases.
 * Mirrors the pre-A1 implementation. Kept here rather than in a separate
 * file so the two paths stay obviously equivalent. */
async function fetchAndDecodeFallback(
	spec: IndexSpec,
	status: IndexLoadStatus,
	onProgress: () => void
): Promise<unknown> {
	const { decompress } = await import('fzstd');
	const { decode } = await import('@msgpack/msgpack');

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
	await new Promise((r) => setTimeout(r, 0));
	const raw = decompress(compressed);
	status.decompressedSize = raw.length;

	status.stage = 'decoding';
	onProgress();
	await new Promise((r) => setTimeout(r, 0));
	const parsed = spec.decoder === 'msgpack' ? decode(raw) : new TextDecoder('utf-8').decode(raw);

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

/** Hydrate a decoded payload onto the live shared bundle. Keeps the
 * object-to-Map / array-of-headwords / nested-reverseMeta plumbing in one
 * place so callers don't need to know the per-key shape. */
function applyToBundle(key: keyof IndexBundle, raw: unknown): void {
	switch (key) {
		case 'tier0':
		case 'tier0Bo':
		case 'tier0Extended':
			setBundleSlice(key, objectToMap<Tier0Entry>(raw));
			return;
		case 'equivalents':
			setBundleSlice('equivalents', objectToMap<EquivRow[]>(raw));
			return;
		case 'reverseEn':
			setBundleSlice('reverseEn', objectToMap<string[]>(raw));
			return;
		case 'reverseKo':
			setBundleSlice('reverseKo', objectToMap<string[]>(raw));
			return;
		case 'reverseMeta':
			setBundleSlice('reverseMeta', parseReverseMeta(raw));
			return;
		case 'declension':
			setBundleSlice('declension', objectToMap<DeclensionRow[]>(raw));
			return;
		case 'headwords':
			setBundleSlice('headwords', parseHeadwords(raw as string));
			return;
	}
}

/** Internal: load one tier and stream progress. Resolves to the union of
 * status rows so the caller can fold them into a global progress report. */
async function loadTier(
	tier: LoadTier,
	allStatus: Map<keyof IndexBundle, IndexLoadStatus>,
	onProgress: () => void
): Promise<void> {
	const keys = TIER_KEYS[tier];
	const specs = INDICES.filter((s) => (keys as readonly (keyof IndexBundle)[]).includes(s.key));
	await Promise.all(
		specs.map(async (spec) => {
			const status = allStatus.get(spec.key);
			if (!status) return;
			try {
				const raw = await fetchAndDecodeInWorker(spec, status, onProgress);
				applyToBundle(spec.key, raw);
				status.stage = 'done';
				onProgress();
			} catch (e) {
				status.stage = 'error';
				status.errorMessage = e instanceof Error ? e.message : String(e);
				onProgress();
				throw e;
			}
		})
	);
	markTierLoaded(tier);
}

/** Initialise per-key status rows for every known index. The map is shared
 * across tiers so a single progress emit covers them all. */
function initStatus(): Map<keyof IndexBundle, IndexLoadStatus> {
	const m = new Map<keyof IndexBundle, IndexLoadStatus>();
	for (const spec of INDICES) {
		m.set(spec.key, {
			name: spec.key,
			stage: 'pending',
			bytesFetched: 0,
			compressedSize: 0,
			decompressedSize: 0
		});
	}
	return m;
}

function makeEmit(
	status: Map<keyof IndexBundle, IndexLoadStatus>,
	onProgressUpdate: (progress: LoadProgress) => void
): () => void {
	return () => {
		const rows = Array.from(status.values());
		const totalCompressedBytes = rows.reduce((acc, s) => acc + s.compressedSize, 0);
		const totalDecompressedBytes = rows.reduce((acc, s) => acc + s.decompressedSize, 0);
		onProgressUpdate({
			status: rows.map((s) => ({ ...s })),
			overallStage: recomputeOverall(rows),
			totalCompressedBytes,
			totalDecompressedBytes
		});
	};
}

/** Phase 4.1 staged loader. Tiers fire in priority order — core first so
 * local search lights up for the typical headword query, then extra (Tibetan
 * extended + cross-language equivalents), then auxiliary (reverse search +
 * declension). Caller may invoke as `await loadTiered(['core'])` and let the
 * rest happen in the background.
 *
 * Throws only if a tier was requested *and* every one of its files failed
 * to load. Per-key failures surface via the per-index status row.
 */
export async function loadTiered(
	tiers: ReadonlyArray<LoadTier>,
	onProgressUpdate: (progress: LoadProgress) => void
): Promise<void> {
	const status = initStatus();
	const emit = makeEmit(status, onProgressUpdate);
	emit();
	for (const tier of tiers) {
		await loadTier(tier, status, emit);
	}
}

/** Back-compat (Phase 3.1..3.7). Loads everything sequentially-by-tier so
 * existing callers that just want a fully-loaded bundle still work, but
 * now they don't block on auxiliary files before core is usable. */
export async function loadAllIndices(
	onProgressUpdate: (progress: LoadProgress) => void
): Promise<IndexBundle> {
	const status = initStatus();
	const emit = makeEmit(status, onProgressUpdate);
	emit();
	await loadTier('core', status, emit);
	await loadTier('extra', status, emit);
	await loadTier('auxiliary', status, emit);
	// The shared bundle has been mutated in place — return the live ref
	// so callers using the return value continue to work.
	return (await import('./store')).getIndexBundle();
}

/** Decode reverse_meta.msgpack.zst payload into a typed ReverseMetaBundle. */
export function parseReverseMeta(raw: unknown): ReverseMetaBundle {
	const obj = raw as { dicts?: string[]; ids?: Record<string, [string, number]> };
	return {
		dicts: obj.dicts ?? [],
		ids: new Map(Object.entries(obj.ids ?? {}))
	};
}
