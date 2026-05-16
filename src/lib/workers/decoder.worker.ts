/// <reference lib="webworker" />
// decoder.worker.ts — Sprint 1 A1.
//
// Off-loads fetch + fzstd decompress + msgpack/text decode from the main
// thread. Each index file gets its own short-lived worker (parallelism is
// already provided by Promise.all in loader.ts; spawning a fresh isolate per
// file is cheaper than building a long-lived pool and avoids cross-task
// cleanup bookkeeping).
//
// Message protocol (main → worker):
//   { url: string, decoder: 'msgpack' | 'text' }
//
// Message protocol (worker → main):
//   { type: 'progress', stage, compressedSize?, decompressedSize? }
//   { type: 'result',   parsed, compressedSize, decompressedSize }
//   { type: 'error',    message }
//
// The worker self-terminates after sending a `result` or `error` message —
// callers in loader.ts also call .terminate() defensively after Promise
// settle to release the isolate even when the worker is mid-progress.

import { decompress } from 'fzstd';
import { decode } from '@msgpack/msgpack';

export type LoadStage = 'fetching' | 'decompressing' | 'decoding';

export interface DecoderRequest {
	url: string;
	decoder: 'msgpack' | 'text';
}

export type DecoderResponse =
	| {
			type: 'progress';
			stage: LoadStage;
			compressedSize?: number;
			decompressedSize?: number;
	  }
	| {
			type: 'result';
			parsed: unknown;
			compressedSize: number;
			decompressedSize: number;
	  }
	| {
			type: 'error';
			message: string;
	  };

// Single shared scope — workers have one isolate; this module is the body.
const ctx = self as unknown as DedicatedWorkerGlobalScope;

ctx.addEventListener('message', async (e: MessageEvent<DecoderRequest>) => {
	const { url, decoder } = e.data;
	try {
		ctx.postMessage({ type: 'progress', stage: 'fetching' } satisfies DecoderResponse);

		const resp = await fetch(url);
		if (!resp.ok) throw new Error(`fetch ${url}: HTTP ${resp.status}`);
		const compressed = new Uint8Array(await resp.arrayBuffer());

		ctx.postMessage({
			type: 'progress',
			stage: 'decompressing',
			compressedSize: compressed.length
		} satisfies DecoderResponse);

		const raw = decompress(compressed);

		ctx.postMessage({
			type: 'progress',
			stage: 'decoding',
			compressedSize: compressed.length,
			decompressedSize: raw.length
		} satisfies DecoderResponse);

		const parsed =
			decoder === 'msgpack' ? decode(raw) : new TextDecoder('utf-8').decode(raw);

		// `parsed` is structured-cloned across the boundary. For Map-ish
		// objects (`{ [norm]: { iast, entries: [...] } }`) the clone happens
		// off main-thread on the sender side; the main thread only pays the
		// receive cost (~50ms for ~30MB nested structures, vs the 300ms+
		// of decode it replaces). Net win is large.
		ctx.postMessage({
			type: 'result',
			parsed,
			compressedSize: compressed.length,
			decompressedSize: raw.length
		} satisfies DecoderResponse);
	} catch (err) {
		ctx.postMessage({
			type: 'error',
			message: err instanceof Error ? err.message : String(err)
		} satisfies DecoderResponse);
	}
});
