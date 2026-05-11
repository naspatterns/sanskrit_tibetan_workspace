<script lang="ts">
	// Phase 4 UI polish (2026-05-12) — brand + identity for every page.
	// The name "haMsa" is the project's Sanskrit motif (हंस = swan, a
	// recurring symbol of discernment in Vedānta + Buddhist literature).
	// Lower-case "haMsa" with capital M echoes the project folder convention
	// the maintainer uses on disk; the Devanagari हंस sits above as the
	// visual anchor.
</script>

<header class="site-header">
	<a href="/" class="brand" aria-label="haMsa Sanskrit-Tibetan Workspace">
		<span class="mark" aria-hidden="true">हंस</span>
		<span class="lockup">
			<span class="name">ha<em>M</em>sa</span>
			<span class="tagline">Sanskrit · Tibetan · Pali · 漢字 · 한국어 lexicon</span>
		</span>
	</a>
	<div class="stats" aria-label="corpus statistics">
		<span class="stat">
			<strong>3.8M</strong>
			<span>entries</span>
		</span>
		<span class="divider" aria-hidden="true">·</span>
		<span class="stat">
			<strong>148</strong>
			<span>dictionaries</span>
		</span>
	</div>
</header>

<style>
	.site-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		padding: 0.6rem 0.25rem 0.9rem;
		border-bottom: 1px solid var(--border);
		margin-bottom: 1.25rem;
	}

	.brand {
		display: flex;
		align-items: center;
		gap: 0.7rem;
		text-decoration: none;
		color: inherit;
		min-width: 0;
	}

	.brand:focus-visible {
		outline: 2px solid var(--accent);
		outline-offset: 4px;
		border-radius: var(--radius-sm);
	}

	.mark {
		font-family: var(--font-display);
		font-size: 1.9rem;
		line-height: 1;
		background: var(--gradient-accent);
		-webkit-background-clip: text;
		background-clip: text;
		color: transparent;
		letter-spacing: -0.02em;
		font-weight: 600;
		transform: translateY(-1px);
	}

	.lockup {
		display: flex;
		flex-direction: column;
		gap: 0.05rem;
		min-width: 0;
	}

	.name {
		font-weight: 700;
		font-size: 1.15rem;
		letter-spacing: 0.01em;
		color: var(--fg);
	}

	.name em {
		font-style: normal;
		font-weight: 600;
		background: var(--gradient-accent);
		-webkit-background-clip: text;
		background-clip: text;
		color: transparent;
	}

	.tagline {
		font-size: 0.74rem;
		color: var(--fg-muted);
		letter-spacing: 0.01em;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.stats {
		display: flex;
		align-items: baseline;
		gap: 0.4rem;
		color: var(--fg-muted);
		font-size: 0.78rem;
		font-variant-numeric: tabular-nums;
		flex-shrink: 0;
	}

	.stat {
		display: inline-flex;
		align-items: baseline;
		gap: 0.25rem;
	}

	.stat strong {
		color: var(--fg);
		font-size: 0.95rem;
		font-weight: 600;
	}

	.divider {
		opacity: 0.5;
	}

	@media (max-width: 600px) {
		.site-header {
			padding-top: 0.4rem;
			padding-bottom: 0.7rem;
			margin-bottom: 1rem;
		}
		.mark {
			font-size: 1.6rem;
		}
		.name {
			font-size: 1rem;
		}
		.tagline {
			display: none;
		}
		.stats {
			font-size: 0.72rem;
		}
		.stat strong {
			font-size: 0.85rem;
		}
	}
</style>
