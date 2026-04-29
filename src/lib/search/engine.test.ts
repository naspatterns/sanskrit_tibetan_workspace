// Engine tests — synthetic IndexBundle to isolate routing logic from data.
// Step 11 will add a smoke test against the real loaded bundle.

import { describe, it, expect } from 'vitest';
import { search } from './engine';
import type { IndexBundle } from '$lib/indices/types';

function makeBundle(): IndexBundle {
	return {
		tier0: new Map([
			[
				'dharma',
				{
					iast: 'dharma',
					entries: [
						{
							dict: 'apte-sanskrit-english',
							short: 'Apte',
							priority: 1,
							tier: 1,
							id: 'apte-sanskrit-english-001',
							snippet_short: 'religion, duty',
							snippet_medium: 'religion, duty, virtue, righteousness',
							ko: '법',
							target_lang: 'en'
						}
					]
				}
			]
		]),
		tier0Bo: new Map(),
		declension: new Map(),
		equivalents: new Map([
			[
				'dharma',
				[{ sources: ['equiv-mahavyutpatti'], skt_iast: 'dharma', tib_wylie: 'chos', zh: '法' }]
			],
			[
				'chos',
				[{ sources: ['equiv-hopkins-tsed'], skt_iast: 'dharma', tib_wylie: 'chos', zh: '法' }]
			],
			[
				'法',
				[{ sources: ['equiv-nti-reader'], skt_iast: 'dharma', tib_wylie: 'chos', zh: '法' }]
			]
		]),
		reverseEn: new Map([['duty', ['apte-sanskrit-english-001', 'monier-williams-001']]]),
		reverseKo: new Map([['법', ['apte-sanskrit-english-001']]]),
		reverseMeta: {
			dicts: ['apte-sanskrit-english', 'monier-williams'],
			ids: new Map<string, [string, number]>([
				['apte-sanskrit-english-001', ['dharma', 0]],
				['monier-williams-001', ['dharma', 1]]
			])
		},
		headwords: [
			{ norm: 'dharma', iast: 'dharma' },
			{ norm: 'dharma-cakra', iast: 'dharma-cakra' },
			{ norm: 'dharmin', iast: 'dharmin' }
		]
	};
}

describe('search engine', () => {
	it('finds exact tier0 hit for IAST input', () => {
		const r = search(makeBundle(), 'dharma');
		expect(r.detectedScript).toBe('iast');
		expect(r.exact?.iast).toBe('dharma');
		expect(r.exact?.entries).toHaveLength(1);
	});

	it('returns equivalents from the IAST channel', () => {
		const r = search(makeBundle(), 'dharma');
		expect(r.equivalents).toHaveLength(1);
		expect(r.equivalents[0].sources).toContain('equiv-mahavyutpatti');
	});

	it('Wylie input hits the tib_wylie equivalents channel', () => {
		const r = search(makeBundle(), 'chos');
		expect(r.detectedScript).toBe('iast'); // Latin → iast bucket
		expect(r.equivalents).toHaveLength(1);
		expect(r.equivalents[0].tib_wylie).toBe('chos');
	});

	it('CJK input hits the zh equivalents channel', () => {
		const r = search(makeBundle(), '法');
		expect(r.detectedScript).toBe('cjk');
		expect(r.equivalents).toHaveLength(1);
		expect(r.equivalents[0].zh).toBe('法');
	});

	it('Devanagari input is normalized + finds exact', () => {
		const r = search(makeBundle(), 'धर्म');
		expect(r.detectedScript).toBe('devanagari');
		expect(r.exact?.iast).toBe('dharma');
	});

	it('HK input is normalized + finds exact', () => {
		const r = search(makeBundle(), 'Dharma');
		// 'D' is HK signature → looksLikeHK true → script = 'hk'
		expect(r.detectedScript).toBe('hk');
		expect(r.exact?.iast).toBe('dharma');
	});

	it('reverse English lookup for ASCII gloss', () => {
		const r = search(makeBundle(), 'duty');
		expect(r.reverse).toHaveLength(1);
		expect(r.reverse[0].language).toBe('en');
		expect(r.reverse[0].entryIds).toContain('apte-sanskrit-english-001');
	});

	it('reverse Korean lookup for Hangul query', () => {
		const r = search(makeBundle(), '법');
		expect(r.detectedScript).toBe('korean');
		expect(r.reverse).toHaveLength(1);
		expect(r.reverse[0].language).toBe('ko');
	});

	it('prefix autocomplete from headwords.txt', () => {
		const r = search(makeBundle(), 'dh');
		expect(r.partial).toHaveLength(3);
		expect(r.partial.map((h) => h.norm)).toEqual(['dharma', 'dharma-cakra', 'dharmin']);
	});

	it('partial limit is honored', () => {
		const r = search(makeBundle(), 'dh', { partialLimit: 1 });
		expect(r.partial).toHaveLength(1);
	});

	it('empty / whitespace-only query returns empty result', () => {
		const r = search(makeBundle(), '   ');
		expect(r.detectedScript).toBe('empty');
		expect(r.exact).toBeNull();
		expect(r.equivalents).toEqual([]);
		expect(r.reverse).toEqual([]);
		expect(r.partial).toEqual([]);
		expect(r.durationMs).toBe(0);
	});

	it('reports query latency in durationMs', () => {
		const r = search(makeBundle(), 'dharma');
		expect(r.durationMs).toBeGreaterThan(0);
		expect(r.durationMs).toBeLessThan(50); // way more than enough headroom
	});
});
