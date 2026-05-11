<script lang="ts">
	import { onMount } from 'svelte';
	import favicon from '$lib/assets/favicon.svg';
	import { loadTiered } from '$lib/indices/loader';
	import { isCoreReady, isFullyLoaded } from '$lib/indices/store';
	import { resolveDataMode } from '$lib/indices/detect';
	import type { LoadProgress } from '$lib/indices/types';
	import ProgressBanner from '$lib/components/ProgressBanner.svelte';
	import '$lib/../styles/theme.css';
	import { applyTheme, getStoredTheme } from '$lib/stores/theme';

	let { children } = $props();

	let progress = $state<LoadProgress | null>(null);
	// Phase 4.1 (2026-05-08): never block on indices. The page renders
	// immediately and routes early searches through the Phase 5 Edge API.
	// `mode` decides whether we *also* pre-load the local bundle in the
	// background (full) or rely entirely on the Edge API (lazy).
	let mode = $state<'full' | 'lazy'>('full');

	onMount(async () => {
		applyTheme(getStoredTheme());

		// Resolve preference once on mount. Re-resolving later would cause
		// load thrash if the connection flapped from 3G ↔ 4G mid-load.
		mode = resolveDataMode();

		if (mode === 'full' && !isFullyLoaded()) {
			// Don't await — the page can already render with empty indices and
			// search falls back to Edge API until tiers complete.
			loadTiered(['core', 'extra', 'auxiliary'], (p) => {
				progress = p;
			}).catch((e) => {
				// Tier-level error doesn't break the UI — Edge API still serves
				// every query. Just log so we notice in DevTools.
				console.warn('Index tier load failed:', e);
			});
		} else if (mode === 'lazy' && !isCoreReady()) {
			// Lazy mode: don't fetch anything proactively. The page works via
			// Edge API. (Future enhancement: prefetch `core` when the user
			// hovers the search bar — `requestIdleCallback` candidate.)
		}

		// Register Service Worker — production only (Vite dev has its own SW
		// reload model that conflicts with cache-first behavior).
		if ('serviceWorker' in navigator && import.meta.env.PROD) {
			navigator.serviceWorker.register('/sw.js').catch((e) => {
				console.error('SW registration failed:', e);
			});
		}
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

{@render children()}
<ProgressBanner {progress} {mode} />
