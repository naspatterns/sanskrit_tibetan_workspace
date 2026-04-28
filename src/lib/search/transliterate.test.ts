// Sanity tests mirroring scripts/lib/transliterate.py invariants.
// Step 11 will expand this to a full port of tests/test_transliterate.py.

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
	it('converts uppercase HK signature chars (S=ṣ, z=ś)', () => {
		// S→ṣ (capital sa = retroflex sibilant); z→ś (palatal sibilant).
		expect(hkToIAST('SAnti')).toBe('ṣānti');
		expect(hkToIAST('zAnti')).toBe('śānti');
		expect(hkToIAST('dharma')).toBe('dharma');
		expect(hkToIAST('prajJApAramitA')).toBe('prajñāpāramitā');
		expect(hkToIAST('TIkA')).toBe('ṭīkā');
	});

	it('handles multi-char before single-char (lRR before lR before RR)', () => {
		expect(hkToIAST('klRRpta')).toBe('kḹpta');
		expect(hkToIAST('kRRSNa')).toBe('kṝṣṇa');
	});
});

describe('devanagariToIAST', () => {
	it('converts simple words with implicit + explicit vowels', () => {
		expect(devanagariToIAST('धर्म')).toBe('dharma');
		expect(devanagariToIAST('बोधिसत्त्व')).toBe('bodhisattva');
		expect(devanagariToIAST('प्रज्ञापारमिता')).toBe('prajñāpāramitā');
	});

	it('handles anusvāra and visarga', () => {
		expect(devanagariToIAST('संस्कृत')).toBe('saṃskṛta');
		expect(devanagariToIAST('दुःख')).toBe('duḥkha');
	});
});

describe('detectScript', () => {
	it('routes to the right channel', () => {
		expect(detectScript('')).toBe('empty');
		expect(detectScript('धर्म')).toBe('devanagari');
		expect(detectScript('SAnti')).toBe('hk');
		expect(detectScript('śānti')).toBe('iast');
		expect(detectScript('dharma')).toBe('iast');
		expect(detectScript('般若')).toBe('cjk');
		expect(detectScript('법')).toBe('korean');
	});

	it('Wylie passes as iast (no separate detection — both share Latin keys)', () => {
		expect(detectScript('byang chub')).toBe('iast');
		expect(detectScript('chos')).toBe('iast');
	});
});

describe('toIAST', () => {
	it('passes IAST through unchanged', () => {
		expect(toIAST('śānti')).toBe('śānti');
	});

	it('auto-detects + converts', () => {
		expect(toIAST('zAnti')).toBe('śānti');
		expect(toIAST('SAnti')).toBe('ṣānti');
		expect(toIAST('धर्म')).toBe('dharma');
	});
});

describe('normalize', () => {
	it('strips combining marks + lowercases without IAST conversion', () => {
		expect(normalize('śānti')).toBe('santi');
		expect(normalize('Dharma')).toBe('dharma');
		expect(normalize('byang chub')).toBe('byang chub');
		expect(normalize('般若')).toBe('般若');
		expect(normalize('  trimmed  ')).toBe('trimmed');
	});
});

describe('normalizeHeadword', () => {
	it('matches Python normalize_headword for HK + Devanagari + IAST inputs', () => {
		expect(normalizeHeadword('śānti')).toBe('santi');
		expect(normalizeHeadword('zAnti')).toBe('santi');  // z→ś→s after diacritic strip
		expect(normalizeHeadword('SAnti')).toBe('santi');  // S→ṣ→s after diacritic strip
		expect(normalizeHeadword('धर्म')).toBe('dharma');
		expect(normalizeHeadword('Dharma')).toBe('dharma');
		expect(normalizeHeadword('prajJApAramitA')).toBe('prajnaparamita');
	});

	it('returns empty for empty input', () => {
		expect(normalizeHeadword('')).toBe('');
	});
});
