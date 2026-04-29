<script lang="ts">
	import type { EquivRow } from '$lib/indices/types';
	import { chipStyle, styleFor } from '$lib/search/source-colors';

	let { row, onclose }: { row: EquivRow; onclose: () => void } = $props();

	function onkeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') onclose();
	}

	const fields: ReadonlyArray<{ key: keyof EquivRow; label: string }> = [
		{ key: 'skt_iast', label: 'Sanskrit (IAST)' },
		{ key: 'tib_wylie', label: 'Tibetan (Wylie)' },
		{ key: 'zh', label: '한자 (中文)' },
		{ key: 'ja', label: 'Japanese' },
		{ key: 'de', label: 'Deutsch' },
		{ key: 'ko', label: '한국어' },
		{ key: 'en', label: 'English' },
		{ key: 'category', label: 'Category' },
		{ key: 'note', label: 'Note' }
	];
</script>

<svelte:window onkeydown={onkeydown} />

<div
	class="modal-bg"
	role="button"
	tabindex="-1"
	aria-label="Close detail"
	onclick={onclose}
	onkeydown={(e) => {
		if (e.key === 'Enter' || e.key === ' ') onclose();
	}}
>
	<div
		class="modal"
		role="dialog"
		aria-modal="true"
		aria-labelledby="equiv-title"
		onclick={(e) => e.stopPropagation()}
		onkeydown={(e) => e.stopPropagation()}
		tabindex="0"
	>
		<button class="close" onclick={onclose} aria-label="닫기">×</button>
		<h3 id="equiv-title">대응어 상세 · Equivalent</h3>

		<dl class="fields">
			{#each fields as f}
				{@const v = row[f.key] as string | undefined}
				{#if v}
					<dt>{f.label}</dt>
					<dd>{v}</dd>
				{/if}
			{/each}
			{#if row.synonyms && row.synonyms.length > 0}
				<dt>Synonyms (Amarakośa)</dt>
				<dd>{row.synonyms.join(' · ')}</dd>
			{/if}
		</dl>

		<h4>출처 사전 ({row.sources.length})</h4>
		<ul class="sources-list">
			{#each row.sources as slug}
				{@const s = styleFor(slug)}
				<li>
					<span class="chip" style={chipStyle(slug)}>{s.label}</span>
					<code>{slug}</code>
				</li>
			{/each}
		</ul>
	</div>
</div>

<style>
	.modal-bg {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.55);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 100;
		padding: 1rem;
		cursor: pointer;
	}
	.modal {
		background: var(--bg);
		color: var(--fg);
		max-width: 600px;
		width: 100%;
		max-height: 80vh;
		overflow-y: auto;
		padding: 1.5rem;
		border-radius: 8px;
		border: 1px solid var(--border);
		position: relative;
		cursor: auto;
		font-family: -apple-system, ui-sans-serif, sans-serif;
	}
	.close {
		position: absolute;
		top: 0.6rem;
		right: 0.6rem;
		width: 2rem;
		height: 2rem;
		border: 1px solid var(--border);
		background: transparent;
		color: var(--fg);
		border-radius: 50%;
		cursor: pointer;
		font-size: 1.1rem;
		line-height: 1;
	}
	.close:hover {
		background: var(--bg-alt);
	}
	h3 {
		margin: 0 2rem 0.8rem 0;
		font-size: 1rem;
	}
	h4 {
		margin: 1.2rem 0 0.4rem;
		font-size: 0.85rem;
		color: var(--fg-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	.fields {
		display: grid;
		grid-template-columns: max-content 1fr;
		gap: 0.4rem 0.8rem;
		margin: 0;
	}
	dt {
		color: var(--fg-muted);
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		align-self: baseline;
	}
	dd {
		margin: 0;
		font-size: 0.95rem;
	}
	.sources-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}
	.sources-list li {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	.chip {
		display: inline-block;
		padding: 0.1rem 0.5rem;
		border-radius: 10px;
		font-size: 0.78rem;
		font-weight: 600;
		min-width: 3rem;
		text-align: center;
	}
	code {
		font-size: 0.78rem;
		color: var(--fg-muted);
	}
</style>
