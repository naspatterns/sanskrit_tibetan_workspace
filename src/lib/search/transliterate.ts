// 1:1 TS port of `scripts/lib/transliterate.py` + v1 `docs/translit.js`.
// Python and TS sides MUST agree on the same input → IAST → norm pipeline
// so client search keys match the on-disk indices built by Python.
// detectScript() extends v1 with `cjk` + `korean` arms — needed because the
// v2 search engine routes by language channel (tier0 IAST / equivalents
// 3-channel / reverse_ko), unlike v1 which only routed by IAST normalization.

// ═══ Harvard-Kyoto → IAST ═══════════════════════════════════════════════

// Multi-char replacements applied first (order matters — `lRR` before `lR`).
const HK_MULTI: ReadonlyArray<readonly [string, string]> = [
	['lRR', 'ḹ'],
	['lR', 'ḷ'],
	['RR', 'ṝ'],
	['Th', 'ṭh'],
	['Dh', 'ḍh'],
	['~n', 'ñ']
];

const HK_SINGLE: Readonly<Record<string, string>> = {
	A: 'ā',
	I: 'ī',
	U: 'ū',
	R: 'ṛ',
	M: 'ṃ',
	H: 'ḥ',
	G: 'ṅ',
	J: 'ñ',
	T: 'ṭ',
	D: 'ḍ',
	N: 'ṇ',
	z: 'ś',
	S: 'ṣ'
};

export function hkToIAST(s: string): string {
	for (const [hk, iast] of HK_MULTI) {
		s = s.split(hk).join(iast);
	}
	let out = '';
	for (const ch of s) {
		out += HK_SINGLE[ch] ?? ch;
	}
	return out;
}

// ═══ Devanagari → IAST ══════════════════════════════════════════════════

const DEVA_INDEPENDENT_VOWELS: Readonly<Record<string, string>> = {
	'अ': 'a', 'आ': 'ā', 'इ': 'i', 'ई': 'ī',
	'उ': 'u', 'ऊ': 'ū', 'ऋ': 'ṛ', 'ॠ': 'ṝ',
	'ऌ': 'ḷ', 'ॡ': 'ḹ', 'ए': 'e', 'ऐ': 'ai',
	'ओ': 'o', 'औ': 'au'
};

const DEVA_CONSONANTS: Readonly<Record<string, string>> = {
	// Velars
	'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ṅ',
	// Palatals
	'च': 'c', 'छ': 'ch', 'ज': 'j', 'झ': 'jh', 'ञ': 'ñ',
	// Retroflexes
	'ट': 'ṭ', 'ठ': 'ṭh', 'ड': 'ḍ', 'ढ': 'ḍh', 'ण': 'ṇ',
	// Dentals
	'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
	// Labials
	'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
	// Semi-vowels
	'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v',
	// Sibilants
	'श': 'ś', 'ष': 'ṣ', 'स': 's',
	// Aspirate
	'ह': 'h'
};

const DEVA_MATRAS: Readonly<Record<string, string>> = {
	'ा': 'ā', 'ि': 'i', 'ी': 'ī',
	'ु': 'u', 'ू': 'ū', 'ृ': 'ṛ',
	'ॄ': 'ṝ', 'ॢ': 'ḷ', 'ॣ': 'ḹ',
	'े': 'e', 'ै': 'ai',
	'ो': 'o', 'ौ': 'au'
};

const DEVA_SPECIAL: Readonly<Record<string, string>> = {
	'ं': 'ṃ', // anusvāra
	'ः': 'ḥ', // visarga
	'ँ': 'm̐', // candrabindu (m + combining)
	'ऽ': "'", // avagraha
	'।': '|', // danda
	'॥': '||', // double danda
	'ॐ': 'oṃ' // oṃ
};

const VIRAMA = '्';

export function devanagariToIAST(s: string): string {
	const result: string[] = [];
	let i = 0;
	const n = s.length;
	while (i < n) {
		const ch = s[i];
		if (DEVA_INDEPENDENT_VOWELS[ch]) {
			result.push(DEVA_INDEPENDENT_VOWELS[ch]);
			i++;
			continue;
		}
		if (DEVA_CONSONANTS[ch]) {
			result.push(DEVA_CONSONANTS[ch]);
			i++;
			if (i < n && s[i] === VIRAMA) {
				// Virama suppresses inherent 'a'
				i++;
			} else if (i < n && DEVA_MATRAS[s[i]]) {
				result.push(DEVA_MATRAS[s[i]]);
				i++;
			} else {
				// Inherent 'a'
				result.push('a');
			}
			continue;
		}
		if (DEVA_SPECIAL[ch]) {
			result.push(DEVA_SPECIAL[ch]);
			i++;
			continue;
		}
		// Devanagari digits
		const cc = ch.charCodeAt(0);
		if (cc >= 0x0966 && cc <= 0x096F) {
			result.push(String(cc - 0x0966));
			i++;
			continue;
		}
		// Nukta — skip
		if (ch === '़') {
			i++;
			continue;
		}
		// Non-Devanagari — pass through
		result.push(ch);
		i++;
	}
	return result.join('');
}

// ═══ Script detection ═══════════════════════════════════════════════════

function hasDevanagari(s: string): boolean {
	for (const ch of s) {
		const c = ch.charCodeAt(0);
		if (c >= 0x0900 && c <= 0x097F) return true;
	}
	return false;
}

function hasCJK(s: string): boolean {
	for (const ch of s) {
		const c = ch.charCodeAt(0);
		// CJK Unified Ideographs (BMP) + Compatibility Ideographs.
		// Excludes surrogate-pair extensions — Buddhist canonical text uses BMP.
		if ((c >= 0x4e00 && c <= 0x9fff) || (c >= 0xf900 && c <= 0xfaff)) return true;
	}
	return false;
}

function hasHangul(s: string): boolean {
	for (const ch of s) {
		const c = ch.charCodeAt(0);
		// Hangul Syllables + Jamo
		if ((c >= 0xac00 && c <= 0xd7af) || (c >= 0x1100 && c <= 0x11ff)) return true;
	}
	return false;
}

// HK signature uppercase chars. 'z' alone is NOT a reliable HK signal —
// English words (amaze, azure) contain 'z'. Require an uppercase HK char.
// MUST match scripts/lib/transliterate.py _looks_like_hk exactly.
const HK_SIGNATURE_UPPER = new Set(['A', 'I', 'U', 'T', 'D', 'N', 'S', 'G', 'J', 'R', 'M', 'H']);
const IAST_DIACRITIC_CHARS = new Set([
	'ā', 'ī', 'ū', 'ṛ', 'ṝ', 'ḷ', 'ḹ', 'ṃ', 'ḥ', 'ṅ', 'ñ', 'ṭ', 'ḍ', 'ṇ', 'ś', 'ṣ'
]);

function looksLikeHK(s: string): boolean {
	let hasHKUpper = false;
	let hasLower = false;
	for (const ch of s) {
		if (HK_SIGNATURE_UPPER.has(ch)) hasHKUpper = true;
		if (ch >= 'a' && ch <= 'z') hasLower = true;
		if (IAST_DIACRITIC_CHARS.has(ch)) return false; // IAST present → not HK
	}
	return hasHKUpper && hasLower;
}

export type Script = 'empty' | 'devanagari' | 'hk' | 'iast' | 'cjk' | 'korean';

export function detectScript(s: string): Script {
	if (!s) return 'empty';
	if (hasDevanagari(s)) return 'devanagari';
	if (hasCJK(s)) return 'cjk';
	if (hasHangul(s)) return 'korean';
	if (looksLikeHK(s)) return 'hk';
	return 'iast'; // Latin + possibly IAST diacritics; Wylie also lands here
}

// ═══ Public API ═════════════════════════════════════════════════════════

export function toIAST(s: string, script?: Script): string {
	if (!s) return '';
	const detected = script ?? detectScript(s);
	if (detected === 'devanagari') return devanagariToIAST(s);
	if (detected === 'hk') return hkToIAST(s);
	return s;
}

/**
 * NFD + strip combining marks + lowercase + trim. No script conversion.
 * Used for non-Sanskrit channels (Wylie, Tibetan, Chinese, Korean) where
 * forcing IAST conversion would corrupt the input.
 */
export function normalize(s: string): string {
	if (!s) return '';
	return s.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase().trim();
}

/**
 * Full Sanskrit pipeline matching `scripts/lib/transliterate.py:normalize_headword`.
 * detect → IAST → NFD → strip combining marks → lowercase + trim.
 */
export function normalizeHeadword(s: string): string {
	if (!s) return '';
	return normalize(toIAST(s));
}
