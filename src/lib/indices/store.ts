// Non-reactive holder for the loaded IndexBundle.
//
// The bundle is ~430 MB decompressed (heap +793 MB total per ADR-011 bench).
// Putting that through Svelte's reactive store machinery would invalidate
// every dependent on every set — wasteful when the value is immutable after
// load. Search results (small) are reactive instead and reference into the
// bundle via Map.get.

import type { IndexBundle } from './types';

let bundle: IndexBundle | null = null;

export function setIndexBundle(b: IndexBundle): void {
	bundle = b;
}

export function getIndexBundle(): IndexBundle {
	if (!bundle) {
		throw new Error('IndexBundle not loaded yet — call setIndexBundle() first.');
	}
	return bundle;
}

export function isIndexLoaded(): boolean {
	return bundle !== null;
}
