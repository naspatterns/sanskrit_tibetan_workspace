<script lang="ts">
	import type { LoadProgress } from '$lib/indices/types';

	let { progress }: { progress: LoadProgress | null } = $props();

	function fmtMB(bytes: number): string {
		return (bytes / 1024 / 1024).toFixed(1) + ' MB';
	}

	function fillPercent(stage: string): number {
		switch (stage) {
			case 'done':
				return 100;
			case 'decoding':
				return 90;
			case 'decompressing':
				return 60;
			case 'fetching':
				return 30;
			default:
				return 0;
		}
	}
</script>

<div class="splash">
	<h1>Sanskrit-Tibetan Workspace</h1>
	<p class="hint">사전 인덱스 로딩 중…</p>

	{#if progress}
		<div class="bars">
			{#each progress.status as s (s.name)}
				<div class="bar-row">
					<span class="bar-name">{s.name}</span>
					<div class="bar">
						<div
							class="bar-fill"
							class:done={s.stage === 'done'}
							class:error={s.stage === 'error'}
							style:width="{fillPercent(s.stage)}%"
						></div>
					</div>
					<span class="bar-stage">{s.stage}</span>
				</div>
			{/each}
		</div>

		<p class="overall">
			compressed {fmtMB(progress.totalCompressedBytes)} · decoded
			{fmtMB(progress.totalDecompressedBytes)}
		</p>
	{/if}
</div>

<style>
	.splash {
		max-width: 520px;
		margin: 4rem auto;
		padding: 0 1rem;
		font-family: -apple-system, ui-sans-serif, sans-serif;
	}
	h1 {
		font-size: 1.4rem;
		margin: 0 0 0.4rem;
	}
	.hint {
		color: #666;
		margin: 0 0 1.5rem;
	}
	.bars {
		display: grid;
		gap: 0.5rem;
	}
	.bar-row {
		display: grid;
		grid-template-columns: 110px 1fr 110px;
		gap: 0.6rem;
		align-items: center;
		font-size: 0.85rem;
	}
	.bar-name {
		color: #555;
		font-variant-numeric: tabular-nums;
	}
	.bar {
		height: 8px;
		background: #eee;
		border-radius: 4px;
		overflow: hidden;
	}
	.bar-fill {
		height: 100%;
		background: #4a90e2;
		transition: width 0.2s ease;
	}
	.bar-fill.done {
		background: #6a9;
	}
	.bar-fill.error {
		background: #c44;
	}
	.bar-stage {
		color: #888;
		font-size: 0.78rem;
		font-variant-numeric: tabular-nums;
	}
	.overall {
		margin-top: 1rem;
		color: #666;
		font-size: 0.85rem;
	}
</style>
