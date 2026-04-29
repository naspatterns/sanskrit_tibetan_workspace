<script lang="ts">
	import type { Tier0Result } from '$lib/indices/types';

	let { entry, onclose }: { entry: Tier0Result; onclose: () => void } = $props();

	function onkeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') onclose();
	}
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
		aria-labelledby="entry-title"
		onclick={(e) => e.stopPropagation()}
		onkeydown={(e) => e.stopPropagation()}
		tabindex="0"
	>
		<button class="close" onclick={onclose} aria-label="닫기">×</button>
		<h3 id="entry-title">
			<span class="dict">{entry.short}</span>
			<span class="prio">[priority {entry.priority}]</span>
		</h3>
		<p class="meta">
			<code>{entry.id}</code>
			· tier {entry.tier}
			· target {entry.target_lang}
		</p>

		<h4>요약 (snippet)</h4>
		<p class="snippet">{entry.snippet_medium || entry.snippet_short || '(미제공)'}</p>

		{#if entry.ko}
			<h4>한국어</h4>
			<p class="ko">{entry.ko}</p>
		{/if}

		<p class="hint">
			전체 본문 (전문)은 Phase 5 Edge API 도입 후 제공 예정. 현재는 `snippet_medium` (~500자)
			까지 표시됩니다.
		</p>
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
		max-width: 640px;
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
		margin: 0 2rem 0.4rem 0;
		font-size: 1rem;
	}
	h4 {
		margin: 1rem 0 0.3rem;
		font-size: 0.85rem;
		color: var(--fg-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	.dict {
		color: var(--accent);
	}
	.prio {
		color: var(--fg-muted);
		font-weight: normal;
		font-size: 0.85rem;
	}
	.meta {
		color: var(--fg-muted);
		font-size: 0.82rem;
		margin: 0;
	}
	code {
		background: var(--bg-alt);
		padding: 0.05rem 0.3rem;
		border-radius: 3px;
		font-size: 0.82rem;
	}
	.snippet,
	.ko {
		font-size: 0.94rem;
		line-height: 1.55;
		margin: 0;
		white-space: pre-wrap;
	}
	.hint {
		margin-top: 1.2rem;
		padding-top: 0.8rem;
		border-top: 1px solid var(--border);
		font-size: 0.82rem;
		color: var(--fg-muted);
	}
	/* Phase 3.6 — mobile: full-screen modal. */
	@media (max-width: 768px) {
		.modal-bg {
			padding: 0;
			align-items: stretch;
		}
		.modal {
			max-height: 100vh;
			min-height: 100vh;
			border-radius: 0;
			border: none;
			padding: 1rem;
		}
	}
</style>
