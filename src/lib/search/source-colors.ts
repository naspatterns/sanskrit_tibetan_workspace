// Source slug → label + OKLCH chip color. Used by Zone B equivalents.
// v1 docs/app.js SOURCE_LABELS pattern + Phase 2.5 spawn merges.

export interface SourceStyle {
	label: string;
	hue: number; // OKLCH hue (0-360)
}

export const SOURCE_STYLES: Readonly<Record<string, SourceStyle>> = {
	'equiv-mahavyutpatti': { label: 'Mvy', hue: 280 }, // purple
	'equiv-negi': { label: 'Negi', hue: 240 }, // blue
	'equiv-lokesh-chandra': { label: 'LCh', hue: 150 }, // green
	'equiv-84000': { label: '84K', hue: 60 }, // amber
	'equiv-hopkins': { label: 'Hop', hue: 200 }, // cyan-blue
	'equiv-hopkins-tsed': { label: 'Hop-TS', hue: 195 }, // cyan
	'equiv-yogacarabhumi-idx': { label: 'YBh', hue: 330 }, // pink
	'equiv-yogacara-index': { label: 'YIdx', hue: 320 }, // pink-violet
	'equiv-nti-reader': { label: 'NTI', hue: 20 }, // red
	'equiv-hirakawa': { label: 'Hir', hue: 110 }, // lime-green
	'equiv-bonwa-daijiten': { label: 'Bon', hue: 290 }, // violet
	'equiv-tib-chn-great': { label: 'TibCn', hue: 170 }, // teal
	'equiv-turfan-skt-de': { label: 'Trf', hue: 35 }, // orange
	'equiv-karashima-lotus': { label: 'Kar', hue: 260 }, // indigo
	'equiv-bodkye-hamsa': { label: 'BkH', hue: 310 }, // fuchsia
	'equiv-lin-4lang': { label: 'Lin', hue: 220 }, // light blue
	'equiv-amarakoza': { label: 'Ama', hue: 25 }, // orange-red
	'equiv-amarakoza-synonyms': { label: 'Ama-Syn', hue: 30 }
};

export function styleFor(slug: string): SourceStyle {
	return SOURCE_STYLES[slug] ?? { label: slug, hue: 0 };
}

/** Inline style string for a source chip — light + dark friendly via OKLCH. */
export function chipStyle(slug: string): string {
	const { hue } = styleFor(slug);
	// Subtle background + saturated text via OKLCH. Works in both themes.
	return `background: oklch(0.92 0.04 ${hue}); color: oklch(0.35 0.16 ${hue});`;
}
