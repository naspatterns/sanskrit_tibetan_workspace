<script lang="ts">
	import { onMount } from 'svelte';
	import favicon from '$lib/assets/favicon.svg';
	import { loadTiered } from '$lib/indices/loader';
	import { isCoreReady, isFullyLoaded } from '$lib/indices/store';
	import { resolveDataMode } from '$lib/indices/detect';
	import type { LoadProgress } from '$lib/indices/types';
	import ProgressBanner from '$lib/components/ProgressBanner.svelte';
	import SiteHeader from '$lib/components/SiteHeader.svelte';
	import SiteFooter from '$lib/components/SiteFooter.svelte';
	import '$lib/../styles/theme.css';
	import '$lib/../styles/fonts.css';
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
	<title>haMsa · Sanskrit-Tibetan Workspace</title>
	<meta
		name="description"
		content="Sanskrit · Tibetan · Pali · Chinese · Korean multi-dictionary lexicon. 3.8M entries across 148 dictionaries."
	/>
	<!--
		Sprint 1 A5 (2026-05-16): Noto Sans Devanagari is now self-hosted from
		/fonts/NotoSansDevanagari-subset.woff2 via src/styles/fonts.css.
		Removed fonts.googleapis.com (render-blocking stylesheet) and
		fonts.gstatic.com (font payload) — both also drop out of CSP.
	-->
	<link
		rel="preload"
		href="/fonts/NotoSansDevanagari-subset.woff2"
		as="font"
		type="font/woff2"
		crossorigin="anonymous"
	/>
	<!--
		Sprint 1 A2 (2026-05-16): preload the three `core` tier index files in
		parallel with the JS bundle. HTTP/2 multiplex pays the latency tax once
		and shaves ~200-500ms off TTI on desktop.

		`media="(min-width: 769px)"` mirrors detect.ts `isProbablySlow()` — the
		same threshold that flips users to lazy mode. Phones / narrow viewports
		skip the preload entirely so we don't waste their data plan downloading
		~38 MB they're not going to use.

		`fetchpriority="low"` keeps these from competing with the JS bundle for
		the first connection slots; browsers will still saturate the pipe with
		them in parallel afterwards.
	-->
	<link
		rel="preload"
		href="/indices/headwords.txt.zst"
		as="fetch"
		type="application/octet-stream"
		crossorigin="anonymous"
		media="(min-width: 769px)"
		fetchpriority="low"
	/>
	<link
		rel="preload"
		href="/indices/tier0.msgpack.zst"
		as="fetch"
		type="application/octet-stream"
		crossorigin="anonymous"
		media="(min-width: 769px)"
		fetchpriority="low"
	/>
	<link
		rel="preload"
		href="/indices/tier0-bo.msgpack.zst"
		as="fetch"
		type="application/octet-stream"
		crossorigin="anonymous"
		media="(min-width: 769px)"
		fetchpriority="low"
	/>
</svelte:head>

<div class="app-shell">
	<div class="content">
		<SiteHeader />
		{@render children()}
	</div>
	<SiteFooter />
</div>
<ProgressBanner {progress} {mode} />

<style>
	.app-shell {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
	}
	.content {
		max-width: 760px;
		margin: 0 auto;
		padding: 1.25rem 1rem 0;
		width: 100%;
		flex: 1;
	}
	/* Subtle background flourish — a very soft radial accent in the top-right.
	   Pure CSS, gradient is intentionally low-opacity so it doesn't compete
	   with text. */
	:global(body)::before {
		content: '';
		position: fixed;
		inset: 0;
		pointer-events: none;
		z-index: -1;
		background:
			radial-gradient(
				ellipse 800px 600px at 90% -10%,
				var(--accent-soft) 0%,
				transparent 60%
			);
		opacity: 0.45;
	}
	@media (max-width: 600px) {
		.content {
			padding: 0.75rem 0.85rem 0;
		}
	}
</style>
