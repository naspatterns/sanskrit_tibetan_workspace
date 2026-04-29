// Unit tests for loader.ts internal helpers.
//
// Audit-D8-2 (Phase 3.6): loader.ts had 0 unit tests. This covers
// parseHeadwords, objectToMap, recomputeOverall — the deterministic
// helpers. Full pipeline integration (loadAllIndices) is not tested here
// because fzstd is decompress-only (we'd need a separate zstd encoder
// dependency or pre-built fixture files); that's tested manually via
// `npm run preview` + Track C sentinel demo.

import { describe, it, expect } from 'vitest';
import {
	objectToMap,
	parseHeadwords,
	recomputeOverall
} from './loader';
import type { IndexLoadStatus } from './types';

describe('parseHeadwords', () => {
	it('parses tab-separated norm \\t iast pairs', () => {
		const input = 'dharma\tdharma\nagni\tagni\nshanti\tśānti\n';
		const out = parseHeadwords(input);
		expect(out).toHaveLength(3);
		expect(out[0]).toEqual({ norm: 'dharma', iast: 'dharma' });
		expect(out[2]).toEqual({ norm: 'shanti', iast: 'śānti' });
	});

	it('skips blank lines', () => {
		const input = 'dharma\tdharma\n\nagni\tagni\n\n';
		const out = parseHeadwords(input);
		expect(out).toHaveLength(2);
	});

	it('skips lines without a tab', () => {
		const input = 'dharma\tdharma\nnotabhere\nagni\tagni\n';
		const out = parseHeadwords(input);
		expect(out).toHaveLength(2);
		expect(out.map((h) => h.norm)).toEqual(['dharma', 'agni']);
	});

	it('preserves input order (binary search dependency)', () => {
		const input = 'aa\taa\nab\tab\nba\tba\nca\tca\n';
		const out = parseHeadwords(input);
		expect(out.map((h) => h.norm)).toEqual(['aa', 'ab', 'ba', 'ca']);
	});

	it('returns empty array on empty input', () => {
		expect(parseHeadwords('')).toEqual([]);
		expect(parseHeadwords('\n\n')).toEqual([]);
	});

	it('handles iast containing extra tabs (only first split)', () => {
		// If somehow a tab leaks into iast, only first delimiter splits
		const input = 'dharma\tdharma\textra\n';
		const out = parseHeadwords(input);
		expect(out[0]).toEqual({ norm: 'dharma', iast: 'dharma\textra' });
	});
});

describe('objectToMap', () => {
	it('converts a record to a Map', () => {
		const m = objectToMap<number>({ a: 1, b: 2 });
		expect(m).toBeInstanceOf(Map);
		expect(m.size).toBe(2);
		expect(m.get('a')).toBe(1);
		expect(m.get('b')).toBe(2);
	});

	it('preserves insertion order', () => {
		const m = objectToMap<number>({ z: 1, a: 2, m: 3 });
		expect(Array.from(m.keys())).toEqual(['z', 'a', 'm']);
	});

	it('returns empty Map for empty object', () => {
		const m = objectToMap<number>({});
		expect(m.size).toBe(0);
	});
});

describe('recomputeOverall', () => {
	const make = (stages: IndexLoadStatus['stage'][]): IndexLoadStatus[] =>
		stages.map((s, i) => ({
			name: `idx${i}`,
			stage: s,
			bytesFetched: 0,
			compressedSize: 0,
			decompressedSize: 0
		}));

	it('returns "error" when any status is error', () => {
		expect(recomputeOverall(make(['done', 'error', 'fetching']))).toBe('error');
	});

	it('returns "done" when all are done', () => {
		expect(recomputeOverall(make(['done', 'done', 'done']))).toBe('done');
	});

	it('returns "decoding" when any is decoding or decompressing', () => {
		expect(recomputeOverall(make(['fetching', 'decoding', 'pending']))).toBe('decoding');
		expect(recomputeOverall(make(['fetching', 'decompressing', 'done']))).toBe('decoding');
	});

	it('returns "fetching" when fetching exists but no decode', () => {
		expect(recomputeOverall(make(['fetching', 'pending', 'pending']))).toBe('fetching');
	});

	it('returns "pending" when all pending', () => {
		expect(recomputeOverall(make(['pending', 'pending']))).toBe('pending');
	});

	it('error takes precedence over done', () => {
		// recomputeOverall checks error first
		expect(recomputeOverall(make(['done', 'done', 'error']))).toBe('error');
	});
});

// Note: loadAllIndices() integration test deferred — fzstd is decompress-only
// so we can't build zstd fixtures inside the test runner without a separate
// encoder dependency. End-to-end is verified via `npm run preview` + the
// Phase 3.5b Track C sentinel demo (audit-C-demo-guide.md).
