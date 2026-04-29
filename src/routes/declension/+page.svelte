<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { getIndexBundle } from '$lib/indices/store';
	import { parseTable, NUMBER_NAMES } from '$lib/declension/parse';
	import { normalizeHeadword } from '$lib/search/transliterate';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';

	let query = $state('');
	const bundle = getIndexBundle(); // ready: layout splash already finished

	onMount(() => {
		query = page.url.searchParams.get('q') ?? '';
	});

	$effect(() => {
		if (typeof window === 'undefined') return;
		const target = query;
		const id = window.setTimeout(() => {
			const url = new URL(window.location.href);
			const cur = url.searchParams.get('q') ?? '';
			if (cur === target) return;
			if (target.trim()) url.searchParams.set('q', target);
			else url.searchParams.delete('q');
			goto(url.pathname + url.search, {
				keepFocus: true,
				noScroll: true,
				replaceState: true
			});
		}, 120);
		return () => clearTimeout(id);
	});

	const results = $derived(
		query.trim() ? (bundle.declension.get(normalizeHeadword(query)) ?? []) : []
	);
</script>

<main>
	<header class="topbar">
		<nav class="tabs" aria-label="primary tabs">
			<a href="/" class="tab">검색</a>
			<a href="/declension" class="tab active" aria-current="page">곡용</a>
		</nav>
		<input
			type="search"
			bind:value={query}
			placeholder="dharma · deva · ātman ..."
			autocomplete="off"
			autocorrect="off"
			autocapitalize="off"
			spellcheck="false"
			class="search-input"
		/>
		<ThemeToggle />
	</header>

	{#if !query.trim()}
		<p class="hint">
			산스크리트 단어를 입력하세요. Heritage Declension의 곡용표를 표시합니다.
			<br />검색 탭과 분리되어 정의/대응어 결과를 오염시키지 않습니다 (FB-5 / ADR-005).
		</p>
	{:else if results.length === 0}
		<p class="hint">
			"{query}" — 곡용표 없음 (top-10K Heritage Declension에 미등록).
		</p>
	{:else}
		<p class="meta-line">
			"{query}" → <strong>{results.length}</strong> paradigm{results.length > 1 ? 's' : ''}
		</p>
		{#each results as row (row.dict)}
			{@const tbl = parseTable(row.body)}
			<section class="paradigm">
				<header class="par-head">
					<span class="iast">{row.iast}</span>
					<span class="dict">{row.dict}</span>
					{#if tbl}<span class="gender">[{tbl.gender}]</span>{/if}
				</header>
				{#if tbl}
					<table class="decl-grid">
						<thead>
							<tr>
								<th></th>
								{#each NUMBER_NAMES as n}<th>{n}</th>{/each}
							</tr>
						</thead>
						<tbody>
							{#each tbl.cases as c (c.name)}
								<tr>
									<th class="case">{c.name}</th>
									{#each c.forms as f}<td>{f}</td>{/each}
								</tr>
							{/each}
						</tbody>
					</table>
				{:else}
					<pre class="raw">{row.body}</pre>
				{/if}
			</section>
		{/each}
	{/if}
</main>

<style>
	main {
		max-width: 760px;
		margin: 1.5rem auto;
		padding: 0 1rem;
		font-family: -apple-system, ui-sans-serif, sans-serif;
		color: var(--fg);
	}
	.topbar {
		display: flex;
		gap: 0.5rem;
		align-items: stretch;
		margin-bottom: 1rem;
	}
	.tabs {
		display: flex;
		gap: 0.3rem;
	}
	.tab {
		padding: 0.5rem 0.8rem;
		border: 1px solid var(--border);
		border-radius: 6px;
		text-decoration: none;
		color: var(--fg);
		font-size: 0.92rem;
	}
	.tab:hover {
		background: var(--bg-alt);
	}
	.tab.active {
		background: var(--accent);
		color: var(--bg);
		border-color: var(--accent);
	}
	.search-input {
		flex: 1;
		padding: 0.5rem 0.75rem;
		font-size: 1.05rem;
		border: 1px solid var(--border);
		border-radius: 6px;
		background: var(--bg);
		color: var(--fg);
		font-family: inherit;
	}
	.search-input:focus {
		outline: 2px solid var(--accent);
		outline-offset: -1px;
	}
	.hint {
		color: var(--fg-muted);
		font-size: 0.92rem;
	}
	.meta-line {
		font-size: 0.88rem;
		color: var(--fg-muted);
		margin: 0 0 1rem;
	}
	.paradigm {
		margin: 0 0 1.5rem;
		padding: 0.8rem;
		background: var(--bg-alt);
		border-radius: 6px;
	}
	.par-head {
		display: flex;
		gap: 0.6rem;
		align-items: baseline;
		margin-bottom: 0.6rem;
	}
	.iast {
		font-weight: 600;
		font-size: 1.05rem;
	}
	.dict {
		color: var(--fg-muted);
		font-size: 0.78rem;
	}
	.gender {
		color: var(--accent);
		font-size: 0.85rem;
	}
	.decl-grid {
		border-collapse: collapse;
		width: 100%;
		font-size: 0.92rem;
	}
	.decl-grid th,
	.decl-grid td {
		padding: 0.3rem 0.5rem;
		border-bottom: 1px solid var(--border);
		text-align: left;
		vertical-align: baseline;
	}
	.decl-grid thead th {
		background: var(--bg);
		font-weight: 600;
		font-size: 0.82rem;
		color: var(--fg-muted);
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}
	.decl-grid th.case {
		color: var(--fg-muted);
		font-size: 0.85rem;
	}
	.raw {
		font-size: 0.78rem;
		white-space: pre-wrap;
		font-family: ui-monospace, monospace;
		background: var(--bg);
		padding: 0.5rem;
		border-radius: 4px;
	}
</style>
