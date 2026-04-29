// Unit tests for parse.ts — Heritage Declension body.plain → 8×3 grid.
// Audit-D8-1 (Phase 3.6): parse.ts had 0 unit tests; this closes that gap.

import { describe, it, expect } from 'vitest';
import { parseTable, CASE_NAMES, NUMBER_NAMES, type DeclensionTable } from './parse';

describe('parseTable', () => {
	describe('happy path', () => {
		it('parses a complete masculine 8×3 grid (deva)', () => {
			// Realistic compact format — no whitespace between header and cells
			// (matches Heritage Declension XDXF output as found in JSONL).
			const body =
				'<deva>Declension table of [Mas.] deva Masculine ' +
				'Singular Dual Plural ' +
				'Nominativedevaḥ devau devāḥ ' +
				'Vocativedeva devau devāḥ ' +
				'Accusativedevam devau devān ' +
				'Instrumentaldevena devābhyām devaiḥ ' +
				'Dativedevāya devābhyām devebhyaḥ ' +
				'Ablativedevāt devābhyām devebhyaḥ ' +
				'Genitivedevasya devayoḥ devānām ' +
				'Locativedeve devayoḥ deveṣu';
			const tbl = parseTable(body);
			expect(tbl).not.toBeNull();
			expect(tbl!.gender).toBe('Masculine');
			expect(tbl!.cases).toHaveLength(8);
			expect(tbl!.cases[0].name).toBe('Nominative');
			expect(tbl!.cases[0].forms).toEqual(['devaḥ', 'devau', 'devāḥ']);
			expect(tbl!.cases[7].name).toBe('Locative');
			expect(tbl!.cases[7].forms[0]).toBe('deve');
		});

		it('parses Feminine gender', () => {
			const body =
				'[Fem.] devī Feminine ' +
				'Singular Dual Plural ' +
				'Nominativedevī devyau devyaḥ ' +
				'Vocativedevi devyau devyaḥ ' +
				'Accusativedevīm devyau devīḥ ' +
				'Instrumentaldevyā devībhyām devībhiḥ ' +
				'Dativedevyai devībhyām devībhyaḥ ' +
				'Ablativedevyāḥ devībhyām devībhyaḥ ' +
				'Genitivedevyāḥ devyoḥ devīnām ' +
				'Locativedevyām devyoḥ devīṣu';
			const tbl = parseTable(body);
			expect(tbl).not.toBeNull();
			expect(tbl!.gender).toBe('Feminine');
			expect(tbl!.cases).toHaveLength(8);
		});

		it('parses Neuter gender', () => {
			const body =
				'[Neu.] phala Neuter ' +
				'Singular Dual Plural ' +
				'Nominativephalam phale phalāni ' +
				'Vocativephala phale phalāni ' +
				'Accusativephalam phale phalāni ' +
				'Instrumentalphalena phalābhyām phalaiḥ ' +
				'Dativephalāya phalābhyām phalebhyaḥ ' +
				'Ablativephalāt phalābhyām phalebhyaḥ ' +
				'Genitivephalasya phalayoḥ phalānām ' +
				'Locativephale phalayoḥ phaleṣu';
			const tbl = parseTable(body);
			expect(tbl).not.toBeNull();
			expect(tbl!.gender).toBe('Neuter');
			expect(tbl!.cases).toHaveLength(8);
		});
	});

	describe('edge cases', () => {
		it('returns null when "Singular Dual Plural" header is missing', () => {
			expect(parseTable('Just some random text')).toBeNull();
			expect(parseTable('')).toBeNull();
			expect(parseTable('Nominative aḥ au āḥ')).toBeNull();
		});

		it('returns null when no cases match after the number header', () => {
			// Has the Singular Dual Plural marker but nothing after
			expect(parseTable('foo Singular Dual Plural ')).toBeNull();
		});

		it('falls back to gender = "Unknown" when header bracket is missing', () => {
			const body =
				'random text without bracket marker ' +
				'Singular Dual Plural ' +
				'Nominativeaḥ au āḥ ' +
				'Vocativea au āḥ ' +
				'Accusativeam au ān ' +
				'Instrumentalena ābhyām aiḥ ' +
				'Dativeāya ābhyām ebhyaḥ ' +
				'Ablativeāt ābhyām ebhyaḥ ' +
				'Genitiveasya ayoḥ ānām ' +
				'Locativee ayoḥ eṣu';
			const tbl = parseTable(body);
			expect(tbl).not.toBeNull();
			expect(tbl!.gender).toBe('Unknown');
			expect(tbl!.cases).toHaveLength(8);
		});

		it('pads missing forms to 3 per case with em-dash', () => {
			// Genitive only has 2 forms — should pad to 3 with '—'
			const body =
				'[Mas.] x Masculine ' +
				'Singular Dual Plural ' +
				'Nominativea b c ' +
				'Vocativea b c ' +
				'Accusativea b c ' +
				'Instrumentala b c ' +
				'Dativea b c ' +
				'Ablativea b c ' +
				'Genitiveonly two ' +
				'Locativea b c';
			const tbl = parseTable(body);
			expect(tbl).not.toBeNull();
			const genitive = tbl!.cases.find((c) => c.name === 'Genitive')!;
			expect(genitive.forms).toEqual(['only', 'two', '—']);
		});

		it('handles partial case lists (only Nom/Acc)', () => {
			const body =
				'[Mas.] x Masculine ' +
				'Singular Dual Plural ' +
				'Nominativea b c ' +
				'Accusatived e f';
			const tbl = parseTable(body);
			expect(tbl).not.toBeNull();
			expect(tbl!.cases).toHaveLength(2);
			expect(tbl!.cases[0].name).toBe('Nominative');
			expect(tbl!.cases[1].name).toBe('Accusative');
		});

		it('preserves IAST diacritics in forms (ṛ, ṝ, ṅ, ñ, ṭ, ḍ, ṇ, ś, ṣ, ḥ, ṁ)', () => {
			const body =
				'[Mas.] kṛṣṇa Masculine ' +
				'Singular Dual Plural ' +
				'Nominativekṛṣṇaḥ kṛṣṇau kṛṣṇāḥ ' +
				'Vocativekṛṣṇa kṛṣṇau kṛṣṇāḥ ' +
				'Accusativekṛṣṇam kṛṣṇau kṛṣṇān ' +
				'Instrumentalkṛṣṇena kṛṣṇābhyām kṛṣṇaiḥ ' +
				'Dativekṛṣṇāya kṛṣṇābhyām kṛṣṇebhyaḥ ' +
				'Ablativekṛṣṇāt kṛṣṇābhyām kṛṣṇebhyaḥ ' +
				'Genitivekṛṣṇasya kṛṣṇayoḥ kṛṣṇānām ' +
				'Locativekṛṣṇe kṛṣṇayoḥ kṛṣṇeṣu';
			const tbl = parseTable(body);
			expect(tbl!.cases[0].forms[0]).toBe('kṛṣṇaḥ');
			expect(tbl!.cases[7].forms[2]).toBe('kṛṣṇeṣu');
		});
	});

	describe('exports', () => {
		it('exports CASE_NAMES with 8 standard Sanskrit cases', () => {
			expect(CASE_NAMES).toHaveLength(8);
			expect(CASE_NAMES).toEqual([
				'Nominative',
				'Vocative',
				'Accusative',
				'Instrumental',
				'Dative',
				'Ablative',
				'Genitive',
				'Locative'
			]);
		});

		it('exports NUMBER_NAMES with 3 standard Sanskrit numbers', () => {
			expect(NUMBER_NAMES).toHaveLength(3);
			expect(NUMBER_NAMES).toEqual(['Singular', 'Dual', 'Plural']);
		});
	});

	describe('regression: realistic Heritage entry shape', () => {
		it('parses the typical concatenated XDXF body', () => {
			// This is the representative shape that decl-a01.jsonl produces:
			// case names act as inline labels with no whitespace separator.
			const body =
				'<deva>Declension table of [Mas.] aśva Masculine ' +
				'Singular Dual Plural ' +
				'Nominativeaśvaḥ aśvau aśvāḥ ' +
				'Vocativeaśva aśvau aśvāḥ ' +
				'Accusativeaśvam aśvau aśvān ' +
				'Instrumentalaśvena aśvābhyām aśvaiḥ ' +
				'Dativeaśvāya aśvābhyām aśvebhyaḥ ' +
				'Ablativeaśvāt aśvābhyām aśvebhyaḥ ' +
				'Genitiveaśvasya aśvayoḥ aśvānām ' +
				'Locativeaśve aśvayoḥ aśveṣu';
			const tbl = parseTable(body) as DeclensionTable;
			expect(tbl.gender).toBe('Masculine');
			expect(tbl.cases.map((c) => c.name)).toEqual([...CASE_NAMES]);
			expect(tbl.cases.every((c) => c.forms.length === 3)).toBe(true);
		});
	});
});
