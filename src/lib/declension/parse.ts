// Parse the body.plain text of a Heritage Declension entry into a 8×3 grid.
// Source format:
//
//   "<deva>Declension table of [Mas.] <iast> Masculine
//    Singular Dual Plural
//    Nominative<s> <d> <p>
//    Vocative<s> <d> <p>
//    Accusative<s> <d> <p>
//    Instrumental<s> <d> <p>
//    Dative<s> <d> <p>
//    Ablative<s> <d> <p>
//    Genitive<s> <d> <p>
//    Locative<s> <d> <p>"
//
// In practice the upstream JSONL has all fields concatenated without
// whitespace separators ("Nominativeaḥ au āḥ Vocativea au āḥ ..."). We use a
// case-name regex to slice between cases, then split each slice into 3 forms.

export const CASE_NAMES = [
	'Nominative',
	'Vocative',
	'Accusative',
	'Instrumental',
	'Dative',
	'Ablative',
	'Genitive',
	'Locative'
] as const;
export type CaseName = (typeof CASE_NAMES)[number];

export const NUMBER_NAMES = ['Singular', 'Dual', 'Plural'] as const;
export type NumberName = (typeof NUMBER_NAMES)[number];

export interface DeclensionTable {
	gender: string; // Masculine / Feminine / Neuter
	cases: { name: CaseName; forms: string[] }[];
}

const HEADER_RE = /\[([^\]]+)\]\s*([^\s]+)\s*(Masculine|Feminine|Neuter)/;
const CASE_SPLIT_RE = new RegExp(
	`(${CASE_NAMES.join('|')})`,
	'g'
);

/** Parse the body.plain into a structured table. Returns null when the
 *  format doesn't match — caller falls back to raw text display. */
export function parseTable(body: string): DeclensionTable | null {
	const headerMatch = HEADER_RE.exec(body);
	const gender = headerMatch?.[3] ?? 'Unknown';

	// Slice everything after "Plural " — the numbers header sits between
	// the gender word and the first case.
	const start = body.search(/Singular\s*Dual\s*Plural/);
	if (start < 0) return null;
	const tail = body.slice(start).replace(/^Singular\s*Dual\s*Plural\s*/, '');

	// Split by case names, keeping the names as separators.
	const parts = tail.split(CASE_SPLIT_RE).filter((s) => s.length > 0);
	const cases: DeclensionTable['cases'] = [];
	for (let i = 0; i < parts.length - 1; i += 2) {
		const name = parts[i] as CaseName;
		const formsBlob = parts[i + 1].trim();
		// Split on whitespace; expect exactly 3 forms.
		const forms = formsBlob.split(/\s+/).slice(0, 3);
		while (forms.length < 3) forms.push('—');
		cases.push({ name, forms });
	}
	if (cases.length === 0) return null;
	return { gender, cases };
}
