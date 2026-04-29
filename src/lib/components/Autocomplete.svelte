<script lang="ts">
	import type { HeadwordEntry } from '$lib/indices/types';

	let {
		items,
		visible,
		onpick,
		onclose
	}: {
		items: HeadwordEntry[];
		visible: boolean;
		onpick: (iast: string) => void;
		onclose: () => void;
	} = $props();

	let selected = $state(0);

	$effect(() => {
		// Reset selection when items change.
		void items;
		selected = 0;
	});

	export function moveSelection(delta: number): boolean {
		if (!visible || items.length === 0) return false;
		selected = (selected + delta + items.length) % items.length;
		return true;
	}

	export function pickSelected(): boolean {
		if (!visible || items.length === 0) return false;
		const item = items[selected];
		onpick(item.iast);
		return true;
	}
</script>

{#if visible && items.length > 0}
	<ul
		class="dropdown"
		role="listbox"
		aria-label="autocomplete suggestions"
		onmousedown={(e) => {
			// prevent input blur before click
			e.preventDefault();
		}}
	>
		{#each items as item, i (item.norm)}
			<li>
				<button
					type="button"
					class="item"
					class:selected={i === selected}
					role="option"
					aria-selected={i === selected}
					onmousedown={(e) => e.preventDefault()}
					onclick={() => onpick(item.iast)}
					onmouseenter={() => (selected = i)}
				>
					<span class="iast">{item.iast}</span>
					{#if item.iast !== item.norm}
						<span class="norm">{item.norm}</span>
					{/if}
				</button>
			</li>
		{/each}
		<li class="hint">
			<kbd>↑↓</kbd> navigate · <kbd>Enter</kbd> select · <kbd>Esc</kbd> close
		</li>
	</ul>
{/if}

<style>
	.dropdown {
		position: absolute;
		top: 100%;
		left: 0;
		right: 0;
		max-height: 60vh;
		overflow-y: auto;
		background: var(--bg);
		border: 1px solid var(--border);
		border-top: none;
		border-radius: 0 0 6px 6px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
		list-style: none;
		padding: 0;
		margin: 0;
		z-index: 50;
	}
	li {
		padding: 0;
	}
	.item {
		width: 100%;
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: 0.5rem;
		padding: 0.4rem 0.7rem;
		background: transparent;
		border: none;
		text-align: left;
		font: inherit;
		color: var(--fg);
		cursor: pointer;
	}
	.item.selected,
	.item:hover {
		background: var(--bg-alt);
	}
	.item.selected {
		outline: 2px solid var(--accent);
		outline-offset: -2px;
	}
	.iast {
		font-size: 0.95rem;
	}
	.norm {
		color: var(--fg-muted);
		font-size: 0.78rem;
		font-variant-numeric: tabular-nums;
	}
	.hint {
		padding: 0.3rem 0.7rem;
		border-top: 1px solid var(--border);
		font-size: 0.75rem;
		color: var(--fg-muted);
	}
	kbd {
		background: var(--bg-alt);
		border: 1px solid var(--border);
		border-radius: 3px;
		padding: 0 0.25rem;
		font-family: inherit;
		font-size: 0.72rem;
	}
</style>
