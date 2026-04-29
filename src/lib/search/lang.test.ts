// Tests for lang.ts — entry-language heuristic + lang-balanced top/rest.

import { describe, it, expect } from 'vitest';
import { entryLang, langBalancedTop, langBalancedRest } from './lang';
import type { Tier0Result } from '$lib/indices/types';

function mk(over: Partial<Tier0Result>): Tier0Result {
	return {
		dict: 'apte-sanskrit-english',
		short: 'Apte',
		priority: 1,
		tier: 1,
		id: 'apte-sanskrit-english-001',
		snippet_short: '',
		snippet_medium: '',
		ko: '',
		target_lang: 'en',
		...over
	};
}

describe('entryLang', () => {
	it('Tibetan target_lang → bo', () => {
		expect(entryLang(mk({ dict: 'tib-rangjung-yeshe', target_lang: 'bo' }))).toBe('bo');
		// even with non-tib- prefix
		expect(entryLang(mk({ dict: 'equiv-hopkins-tsed', target_lang: 'bo' }))).toBe('bo');
	});
	it('tib- prefix without target_lang=bo → bo', () => {
		expect(entryLang(mk({ dict: 'tib-hopkins-2015', target_lang: 'en' }))).toBe('bo');
	});
	it('Pali → pi', () => {
		expect(entryLang(mk({ dict: 'pali-english', target_lang: 'en' }))).toBe('pi');
		expect(entryLang(mk({ dict: 'something-pali', target_lang: 'pi' }))).toBe('pi');
	});
	it('Sanskrit dicts default to sa', () => {
		expect(entryLang(mk({ dict: 'apte-sanskrit-english', target_lang: 'en' }))).toBe('sa');
		expect(entryLang(mk({ dict: 'monier-williams', target_lang: 'en' }))).toBe('sa');
		expect(entryLang(mk({ dict: 'cappeller-german', target_lang: 'de' }))).toBe('sa');
	});
});

describe('langBalancedTop', () => {
	const entries: Tier0Result[] = [
		mk({ dict: 'apte-sanskrit-english', priority: 1, id: 'a-1' }),
		mk({ dict: 'monier-williams', priority: 2, id: 'mw-1' }),
		mk({ dict: 'macdonell', priority: 3, id: 'm-1' }),
		mk({ dict: 'bhsd', priority: 4, id: 'b-1' }),
		mk({ dict: 'tib-rangjung-yeshe', priority: 20, target_lang: 'en', id: 't-1' }),
		mk({ dict: 'tib-hopkins-2015', priority: 21, target_lang: 'en', id: 't-2' }),
		mk({ dict: 'tib-84000-dict', priority: 22, target_lang: 'en', id: 't-3' }),
		mk({ dict: 'tib-jim-valby', priority: 23, target_lang: 'en', id: 't-4' })
	];

	it('takes top-N per language and concatenates skt → bo → pi → other', () => {
		const top = langBalancedTop(entries, 3);
		expect(top.map((e) => e.id)).toEqual(['a-1', 'mw-1', 'm-1', 't-1', 't-2', 't-3']);
	});

	it('rest contains everything not in top', () => {
		const top = langBalancedTop(entries, 3);
		const rest = langBalancedRest(entries, 3);
		const topIds = new Set(top.map((e) => e.id));
		expect(rest.every((e) => !topIds.has(e.id))).toBe(true);
		expect(rest.map((e) => e.id)).toEqual(['b-1', 't-4']);
	});

	it('handles empty input', () => {
		expect(langBalancedTop([], 3)).toEqual([]);
		expect(langBalancedRest([], 3)).toEqual([]);
	});
});
