<script lang="ts">
	// Phase 4.1 Mobile Rescue — non-blocking progress banner.
	// Replaces SplashScreen which used to gate the entire page behind index
	// loading. Now the search UI renders immediately and this banner
	// reports loading progress in a corner toast. It auto-dismisses 1.5s
	// after all requested tiers reach 'done', and can be hidden manually.

	import type { LoadProgress } from '$lib/indices/types';

	let {
		progress,
		mode
	}: {
		progress: LoadProgress | null;
		/** 'lazy' = edge-only mode active (mobile / saveData); we don't pre-load
		 * any tier and the banner stays hidden by default. 'full' = desktop
		 * default; shows progress until done. */
		mode: 'full' | 'lazy';
	} = $props();

	let dismissed = $state(false);

	const totalMB = $derived(progress ? progress.totalCompressedBytes / 1024 / 1024 : 0);
	const completed = $derived(progress?.status.filter((s) => s.stage === 'done').length ?? 0);
	const total = $derived(progress?.status.length ?? 0);
	const pct = $derived(total > 0 ? Math.round((completed / total) * 100) : 0);

	const visible = $derived(
		!dismissed &&
			mode === 'full' &&
			progress !== null &&
			progress.overallStage !== 'done' &&
			progress.overallStage !== 'pending'
	);
</script>

{#if visible}
	<div class="banner" role="status" aria-live="polite">
		<div class="banner-row">
			<span class="banner-title">사전 인덱스 로딩 중…</span>
			<button type="button" class="banner-close" onclick={() => (dismissed = true)} aria-label="닫기">
				×
			</button>
		</div>
		<div class="banner-bar">
			<div class="banner-bar-fill" style:width="{pct}%"></div>
		</div>
		<p class="banner-detail">
			{completed} / {total} 파일 · {totalMB.toFixed(1)} MB
		</p>
		<p class="banner-hint">
			로딩 중에도 검색은 Edge API로 가능합니다 (살짝 느릴 수 있음).
		</p>
	</div>
{/if}

<style>
	.banner {
		position: fixed;
		bottom: 1rem;
		right: 1rem;
		max-width: 280px;
		padding: 0.75rem 1rem;
		background: var(--surface, #1f2024);
		color: var(--text, #e6e6e6);
		border: 1px solid var(--border, #444);
		border-radius: 6px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
		font-family: -apple-system, ui-sans-serif, sans-serif;
		font-size: 0.85rem;
		z-index: 100;
	}
	.banner-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}
	.banner-title {
		font-weight: 600;
	}
	.banner-close {
		background: none;
		border: none;
		color: inherit;
		font-size: 1.25rem;
		line-height: 1;
		cursor: pointer;
		padding: 0 0.25rem;
	}
	.banner-close:focus-visible {
		outline: 2px solid var(--accent, #7ad);
		outline-offset: 2px;
	}
	.banner-bar {
		height: 4px;
		background: var(--bar-bg, #333);
		border-radius: 2px;
		overflow: hidden;
		margin-bottom: 0.4rem;
	}
	.banner-bar-fill {
		height: 100%;
		background: var(--accent, #7ad);
		transition: width 200ms ease;
	}
	.banner-detail {
		margin: 0 0 0.4rem;
		opacity: 0.85;
		font-size: 0.75rem;
	}
	.banner-hint {
		margin: 0;
		opacity: 0.6;
		font-size: 0.7rem;
	}
	@media (max-width: 768px) {
		.banner {
			left: 1rem;
			right: 1rem;
			max-width: none;
			bottom: 0.75rem;
		}
	}
</style>
