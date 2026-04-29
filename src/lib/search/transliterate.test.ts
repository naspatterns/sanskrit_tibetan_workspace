// Full port of tests/test_transliterate.py + Step 5 sanity tests.
// Python and TS sides MUST agree on every input → output here so client
// search keys match Python-built indices (ADR-004).
//
// SLP1 conversion is in Python only (v1 translit.js + v2 transliterate.ts
// don't expose it — none of v2's input paths use SLP1). Skipped here.

import { describe, it, expect } from 'vitest';
import {
	devanagariToIAST,
	detectScript,
	hkToIAST,
	normalize,
	normalizeHeadword,
	toIAST
} from './transliterate';

describe('hkToIAST', () => {
	describe('basic vowels', () => {
		it('A → ā', () => expect(hkToIAST('A')).toBe('ā'));
		it('I → ī', () => expect(hkToIAST('I')).toBe('ī'));
		it('U → ū', () => expect(hkToIAST('U')).toBe('ū'));
	});

	describe('retroflex', () => {
		it('T → ṭ', () => expect(hkToIAST('T')).toBe('ṭ'));
		it('D → ḍ', () => expect(hkToIAST('D')).toBe('ḍ'));
		it('N → ṇ', () => expect(hkToIAST('N')).toBe('ṇ'));
	});

	describe('sibilants', () => {
		it('z → ś (palatal sibilant)', () => expect(hkToIAST('z')).toBe('ś'));
		it('S → ṣ (retroflex sibilant)', () => expect(hkToIAST('S')).toBe('ṣ'));
	});

	describe('vocalic r and l', () => {
		it('R → ṛ', () => expect(hkToIAST('R')).toBe('ṛ'));
		it('RR → ṝ', () => expect(hkToIAST('RR')).toBe('ṝ'));
		it('lR → ḷ', () => expect(hkToIAST('lR')).toBe('ḷ'));
		it('lRR → ḹ', () => expect(hkToIAST('lRR')).toBe('ḹ'));
	});

	describe('word examples', () => {
		it('dharma passthrough (no HK signature chars)', () => {
			expect(hkToIAST('dharma')).toBe('dharma');
		});
		it('prajJApAramitA → prajñāpāramitā', () => {
			expect(hkToIAST('prajJApAramitA')).toBe('prajñāpāramitā');
		});
		it('ajJa → ajña', () => expect(hkToIAST('ajJa')).toBe('ajña'));
		it('TIkA → ṭīkā', () => expect(hkToIAST('TIkA')).toBe('ṭīkā'));
		it('SAnti → ṣānti (S=ṣ, A=ā)', () => expect(hkToIAST('SAnti')).toBe('ṣānti'));
		it('zAnti → śānti (z=ś)', () => expect(hkToIAST('zAnti')).toBe('śānti'));
	});

	describe('multi-char applied before single-char', () => {
		it('lRR before lR before RR (klRRpta → kḹpta)', () => {
			expect(hkToIAST('klRRpta')).toBe('kḹpta');
		});
		it('mixed: kRRSNa → kṝṣṇa', () => expect(hkToIAST('kRRSNa')).toBe('kṝṣṇa'));
	});
});

describe('devanagariToIAST', () => {
	it('धर्म → dharma', () => expect(devanagariToIAST('धर्म')).toBe('dharma'));
	it('बोधिसत्त्व → bodhisattva', () => {
		expect(devanagariToIAST('बोधिसत्त्व')).toBe('bodhisattva');
	});
	it('प्रज्ञापारमिता → prajñāpāramitā', () => {
		expect(devanagariToIAST('प्रज्ञापारमिता')).toBe('prajñāpāramitā');
	});
	it('संस्कृत → saṃskṛta (anusvāra)', () => {
		expect(devanagariToIAST('संस्कृत')).toBe('saṃskṛta');
	});
	it('दुःख → duḥkha (visarga)', () => expect(devanagariToIAST('दुःख')).toBe('duḥkha'));
	it('empty → empty', () => expect(devanagariToIAST('')).toBe(''));
});

describe('detectScript', () => {
	it('empty string → empty', () => expect(detectScript('')).toBe('empty'));
	it('Devanagari content → devanagari', () => expect(detectScript('धर्म')).toBe('devanagari'));
	it('HK uppercase signature → hk', () => expect(detectScript('SAnti')).toBe('hk'));
	it('IAST diacritics → iast', () => expect(detectScript('śānti')).toBe('iast'));
	it('plain Latin (could be IAST or Wylie) → iast', () => {
		expect(detectScript('dharma')).toBe('iast');
	});
	it('CJK Unified Ideograph → cjk', () => expect(detectScript('般若')).toBe('cjk'));
	it('Korean Hangul → korean', () => expect(detectScript('법')).toBe('korean'));
	it('Hangul + Hanja mix → korean (Hangul wins detection priority)', () => {
		expect(detectScript('법(法)')).toBe('cjk'); // CJK detected first
	});
	it("English-only 'amaze' must not be misread as HK", () => {
		// 'z' alone is not an HK signature; needs uppercase HK char too.
		expect(detectScript('amaze')).toBe('iast');
	});
	it('Wylie multi-syllable lands in iast bucket', () => {
		expect(detectScript('byang chub sems dpa')).toBe('iast');
	});
});

describe('toIAST', () => {
	it('Devanagari → IAST', () => expect(toIAST('धर्म')).toBe('dharma'));
	it('HK → IAST', () => expect(toIAST('prajJA')).toBe('prajñā'));
	it('IAST passthrough', () => {
		expect(toIAST('dharma')).toBe('dharma');
		expect(toIAST('prajñā')).toBe('prajñā');
	});
	it('English word passthrough (not misread as HK)', () => {
		expect(toIAST('amaze')).toBe('amaze');
	});
	it('explicit script override skips detection', () => {
		expect(toIAST('SAnti', 'hk')).toBe('ṣānti');
		expect(toIAST('SAnti', 'iast')).toBe('SAnti'); // forced passthrough
	});
});

describe('normalize (NFD + strip combining + lowercase + trim, no script conv)', () => {
	it('strips combining marks (ā → a)', () => expect(normalize('ā')).toBe('a'));
	it('strips multiple diacritics (prajñā → prajna)', () => {
		expect(normalize('prajñā')).toBe('prajna');
	});
	it('plain ASCII passthrough', () => expect(normalize('dharma')).toBe('dharma'));
	it('lowercase', () => expect(normalize('DHARMA')).toBe('dharma'));
	it('trim whitespace', () => expect(normalize('  dharma  ')).toBe('dharma'));
	it('Wylie passes through (no IAST conversion applied)', () => {
		expect(normalize('Byang Chub')).toBe('byang chub');
	});
	it('CJK passes through unchanged', () => expect(normalize('般若')).toBe('般若'));
	it('empty → empty', () => expect(normalize('')).toBe(''));
});

describe('normalizeHeadword (full Sanskrit pipeline)', () => {
	it('Devanagari → IAST → norm', () => {
		expect(normalizeHeadword('धर्म')).toBe('dharma');
	});
	it('HK → IAST → norm', () => {
		expect(normalizeHeadword('prajJApAramitA')).toBe('prajnaparamita');
	});
	it('IAST → norm only', () => expect(normalizeHeadword('prajñā')).toBe('prajna'));
	it('mixed case Latin', () => expect(normalizeHeadword('Dharma')).toBe('dharma'));
	it('zAnti → santi (HK z=ś, then strip diacritic)', () => {
		expect(normalizeHeadword('zAnti')).toBe('santi');
	});
	it('SAnti → santi (HK S=ṣ, then strip diacritic)', () => {
		expect(normalizeHeadword('SAnti')).toBe('santi');
	});
	it('empty → empty', () => expect(normalizeHeadword('')).toBe(''));
});
