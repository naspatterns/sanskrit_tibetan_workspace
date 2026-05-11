// Holder for the IndexBundle + per-key load tracking.
//
// Phase 4.1 (2026-05-08) — switched from "atomic load or throw" to
// "always returns a bundle, mutate in place as tiers arrive". The bundle
// starts empty (all Maps zero-sized, headwords empty array) so the search
// engine can call Map.get(...) safely from the very first render. As each
// tier finishes loading, replace the relevant Maps in place. Anything not
// yet loaded falls through Map.get → undefined → +page.svelte's
// Phase 5 Edge API fallback covers the long tail.
//
// Why mutate in place vs swap whole object: callers cache `bundle` at
// component module scope (see +page.svelte). Replacing the object would
// strand them on the old empty Map. Mutating the inner Maps keeps refs live.
//
// The bundle is ~430 MB decompressed at full load (ADR-011 bench). Search
// results (small) are reactive — references into the bundle via Map.get.

import { createEmptyBundle, type IndexBundle, type LoadTier } from './types';

const bundle: IndexBundle = createEmptyBundle();
const loadedTiers = new Set<LoadTier>();
const loadedKeys = new Set<keyof IndexBundle>();

export function getIndexBundle(): IndexBundle {
	return bundle;
}

/** Replace the underlying data for a specific key. The bundle reference
 * itself never changes — only the Map/array inside. */
export function setBundleSlice<K extends keyof IndexBundle>(
	key: K,
	value: IndexBundle[K]
): void {
	// Assignment is fine because IndexBundle's fields are mutable refs and we
	// own the singleton.
	(bundle as Record<keyof IndexBundle, unknown>)[key] = value;
	loadedKeys.add(key);
}

export function markTierLoaded(tier: LoadTier): void {
	loadedTiers.add(tier);
}

export function isTierLoaded(tier: LoadTier): boolean {
	return loadedTiers.has(tier);
}

export function isKeyLoaded(key: keyof IndexBundle): boolean {
	return loadedKeys.has(key);
}

/** True when the core tier (headwords + tier0 + tier0Bo) is in. With this
 * the UI can do useful local autocomplete + top-hit lookups. Before this
 * fires, +page.svelte routes every query through the Edge API. */
export function isCoreReady(): boolean {
	return loadedTiers.has('core');
}

/** True when every tier has finished — local search is now fully
 * authoritative and Edge API is purely a long-tail fallback. */
export function isFullyLoaded(): boolean {
	return loadedTiers.has('core') && loadedTiers.has('extra') && loadedTiers.has('auxiliary');
}

// ─── Back-compat shim (Phase 3.1..3.7 callers used this name) ─────────
// Returns true once *any* tier has loaded so call-sites that just want to
// know "is it safe to look at bundle.tier0" keep working. Most current
// callers really want isCoreReady() — migrate them when convenient.
export function isIndexLoaded(): boolean {
	return loadedTiers.size > 0;
}
