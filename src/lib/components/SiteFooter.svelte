<script lang="ts">
	// Phase 4 UI polish (2026-05-12) — minimal credit + meta footer.
</script>

<footer class="site-footer">
	<div class="row">
		<span class="credit">
			Designed by
			<a href="mailto:naspatterns@gmail.com" class="email">naspatterns@gmail.com</a>
		</span>
		<span class="meta">
			<a href="https://github.com/naspatterns/sanskrit_tibetan_workspace" rel="noopener" target="_blank">source</a>
			<span class="dot" aria-hidden="true">·</span>
			<a href="/declension">곡용</a>
			<span class="dot" aria-hidden="true">·</span>
			<span class="muted">v2 · 2026</span>
		</span>
	</div>
	<p class="sanskrit-mark" aria-hidden="true">
		ॐ <span class="quiet">satyam eva jayate</span> ॐ
	</p>
</footer>

<style>
	.site-footer {
		max-width: 760px;
		margin: 4rem auto 2rem;
		padding: 1.25rem 1rem 0;
		border-top: 1px solid var(--border);
		font-family: -apple-system, ui-sans-serif, sans-serif;
		font-size: 0.78rem;
		color: var(--fg-muted);
	}

	.row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		flex-wrap: wrap;
		gap: 0.6rem 1rem;
	}

	.credit {
		letter-spacing: 0.01em;
	}

	.email {
		color: var(--fg);
		text-decoration: none;
		font-weight: 500;
		background-image: linear-gradient(
			to right,
			var(--accent) 0%,
			var(--accent) 100%
		);
		background-position: 0 100%;
		background-repeat: no-repeat;
		background-size: 100% 1px;
		padding-bottom: 1px;
		transition: background-size 200ms ease;
	}

	.email:hover {
		background-size: 100% 2px;
	}

	.meta {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
	}

	.meta a {
		color: var(--fg-muted);
		text-decoration: none;
	}

	.meta a:hover {
		color: var(--fg);
	}

	.dot {
		opacity: 0.5;
	}

	.muted {
		opacity: 0.7;
	}

	.sanskrit-mark {
		margin: 1rem 0 0;
		text-align: center;
		font-family: var(--font-display);
		font-size: 0.85rem;
		color: var(--fg-muted);
		opacity: 0.55;
		letter-spacing: 0.12em;
	}

	.sanskrit-mark .quiet {
		font-family: -apple-system, ui-serif, serif;
		font-style: italic;
		font-size: 0.7rem;
		opacity: 0.85;
		margin: 0 0.4rem;
		letter-spacing: 0.05em;
	}

	@media (max-width: 600px) {
		.site-footer {
			margin-top: 3rem;
			padding-top: 1rem;
			font-size: 0.74rem;
		}
		.row {
			flex-direction: column;
			align-items: flex-start;
			gap: 0.4rem;
		}
		.sanskrit-mark {
			font-size: 0.78rem;
			margin-top: 0.75rem;
		}
	}
</style>
