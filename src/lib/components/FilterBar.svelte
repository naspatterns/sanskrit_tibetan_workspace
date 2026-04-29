<script lang="ts">
	import type { EntryLang } from '$lib/search/lang';

	let {
		langFilter = $bindable<EntryLang | 'all'>('all'),
		priorityMax = $bindable(100),
		totalEntries,
		visibleEntries
	}: {
		langFilter?: EntryLang | 'all';
		priorityMax?: number;
		totalEntries: number;
		visibleEntries: number;
	} = $props();

	const LANGS: ReadonlyArray<{ key: EntryLang | 'all'; label: string }> = [
		{ key: 'all', label: '전체' },
		{ key: 'sa', label: '산스 (Skt)' },
		{ key: 'bo', label: '티벳 (Bod)' },
		{ key: 'pi', label: 'Pāli' }
	];
</script>

<div class="filter-bar">
	<div class="lang-row">
		<span class="lbl">Lang</span>
		{#each LANGS as l}
			<button
				type="button"
				class="pill"
				class:active={langFilter === l.key}
				onclick={() => (langFilter = l.key)}
				aria-pressed={langFilter === l.key}
			>
				{l.label}
			</button>
		{/each}
	</div>
	<div class="prio-row">
		<label class="lbl" for="prio-range">Priority ≤ <strong>{priorityMax}</strong></label>
		<input
			id="prio-range"
			type="range"
			min="1"
			max="100"
			step="1"
			bind:value={priorityMax}
			class="slider"
		/>
		<span class="dim">{visibleEntries} / {totalEntries}</span>
	</div>
</div>

<style>
	.filter-bar {
		background: var(--bg-alt);
		border: 1px solid var(--border);
		border-radius: 6px;
		padding: 0.5rem 0.7rem;
		margin: 0 0 1rem;
		display: grid;
		gap: 0.4rem;
		font-size: 0.85rem;
	}
	.lang-row,
	.prio-row {
		display: flex;
		gap: 0.4rem;
		align-items: center;
	}
	.lbl {
		color: var(--fg-muted);
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		min-width: 4.5rem;
	}
	.pill {
		background: var(--bg);
		border: 1px solid var(--border);
		border-radius: 12px;
		padding: 0.2rem 0.6rem;
		cursor: pointer;
		color: var(--fg);
		font: inherit;
		font-size: 0.82rem;
	}
	.pill:hover {
		border-color: var(--accent);
	}
	.pill.active {
		background: var(--accent);
		color: var(--bg);
		border-color: var(--accent);
	}
	.slider {
		flex: 1;
		max-width: 280px;
		accent-color: var(--accent);
	}
	.dim {
		color: var(--fg-muted);
		font-size: 0.78rem;
		font-variant-numeric: tabular-nums;
	}
</style>
