<script lang="ts">
	import { onMount } from 'svelte';
	import favicon from '$lib/assets/favicon.svg';
	import { loadAllIndices } from '$lib/indices/loader';
	import { setIndexBundle, isIndexLoaded } from '$lib/indices/store';
	import type { LoadProgress } from '$lib/indices/types';
	import SplashScreen from '$lib/components/SplashScreen.svelte';

	let { children } = $props();

	let progress = $state<LoadProgress | null>(null);
	let loaded = $state(false);
	let error = $state<string | null>(null);

	onMount(async () => {
		if (isIndexLoaded()) {
			loaded = true;
			return;
		}
		try {
			const bundle = await loadAllIndices((p) => {
				progress = p;
			});
			setIndexBundle(bundle);
			loaded = true;
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
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

{#if error}
	<div class="load-error">
		<h2>인덱스 로드 실패</h2>
		<pre>{error}</pre>
	</div>
{:else if !loaded}
	<SplashScreen {progress} />
{:else}
	{@render children()}
{/if}

<style>
	.load-error {
		max-width: 520px;
		margin: 4rem auto;
		padding: 1rem;
		color: #c44;
		border: 1px solid #c44;
		border-radius: 4px;
		font-family: -apple-system, ui-sans-serif, sans-serif;
	}
	.load-error h2 {
		margin: 0 0 0.5rem;
		font-size: 1.1rem;
	}
	.load-error pre {
		margin: 0;
		font-size: 0.85rem;
		white-space: pre-wrap;
	}
</style>
