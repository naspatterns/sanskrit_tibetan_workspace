<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { performSearch } from '$lib/stores/search';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';

	let query = $state('');
	const result = $derived(performSearch(query));

	// Hydrate from ?q= on first paint.
	onMount(() => {
		const q = page.url.searchParams.get('q') ?? '';
		query = q;
	});

	// Two-way URL sync (replaceState — back-button doesn't fill with keystrokes).
	$effect(() => {
		if (typeof window === 'undefined') return;
		const url = new URL(window.location.href);
		if (query.trim()) url.searchParams.set('q', query);
		else url.searchParams.delete('q');
		if (url.search !== window.location.search) {
			goto(url.pathname + url.search, {
				keepFocus: true,
				noScroll: true,
				replaceState: true
			});
		}
	});

	function chooseSuggestion(iast: string) {
		query = iast;
	}
</script>

<main>
	<header class="topbar">
		<input
			type="search"
			bind:value={query}
			placeholder="dharma · धर्म · chos · 般若 · 법"
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
			검색어를 입력하세요. IAST · HK · Devanagari · Wylie · 한자 · 한국어 모두 지원.
		</p>
	{:else if !result}
		<p class="hint">로딩 중…</p>
	{:else}
		<div class="header-strip">
			<strong>"{result.query}"</strong>
			<span class="meta">정의 {result.exact?.entries.length ?? 0}</span>
			<span class="meta">대응어 {result.equivalents.length}</span>
			<span class="meta">역검색 {result.reverse.length}</span>
			<span class="meta">완성 {result.partial.length}</span>
			<span class="dim">· {result.detectedScript} · {result.durationMs.toFixed(2)}ms</span>
		</div>

		{#if result.equivalents.length > 0}
			<section class="zone zone-b">
				<h2>대응어 · Equivalents <span class="count">{result.equivalents.length}</span></h2>
				<ul class="equiv-list">
					{#each result.equivalents.slice(0, 50) as row}
						<li class="equiv-row">
							{#if row.skt_iast}<span class="lang skt">{row.skt_iast}</span>{/if}
							{#if row.tib_wylie}<span class="sep">↔</span><span class="lang tib"
									>{row.tib_wylie}</span
								>{/if}
							{#if row.zh}<span class="sep">·</span><span class="lang zh">{row.zh}</span>{/if}
							{#if row.ja}<span class="sep">·</span><span class="lang ja">{row.ja}</span>{/if}
							{#if row.de}<span class="sep">·</span><span class="lang de">{row.de}</span>{/if}
							{#if row.ko}<span class="sep">·</span><span class="lang ko">{row.ko}</span>{/if}
							{#if row.en}<span class="sep">·</span><span class="lang en">{row.en}</span>{/if}
							{#if row.category}<span class="cat">{row.category}</span>{/if}
							<span class="sources">{row.sources.join(' · ')}</span>
						</li>
					{/each}
				</ul>
				{#if result.equivalents.length > 50}
					<p class="more">
						... {result.equivalents.length - 50}건 더 (전체 보기는 Step 6 후속에서)
					</p>
				{/if}
			</section>
		{/if}

		{#if result.exact}
			<section class="zone zone-c">
				<h2>정의 · Definitions <span class="count">{result.exact.entries.length}</span></h2>
				{#each result.exact.entries.slice(0, 3) as entry (entry.id)}
					<article class="entry">
						<header class="entry-head">
							<span class="dict">{entry.short}</span>
							<span class="prio">[{entry.priority}]</span>
						</header>
						<p class="snippet">{entry.snippet_short}</p>
						{#if entry.ko}<p class="ko">{entry.ko}</p>{/if}
					</article>
				{/each}

				{#if result.exact.entries.length > 3}
					<details class="zone-d">
						<summary>추가 사전 {result.exact.entries.length - 3}개 보기</summary>
						{#each result.exact.entries.slice(3) as entry (entry.id)}
							<article class="entry">
								<header class="entry-head">
									<span class="dict">{entry.short}</span>
									<span class="prio">[{entry.priority}]</span>
								</header>
								<p class="snippet">{entry.snippet_short}</p>
							</article>
						{/each}
					</details>
				{/if}
			</section>
		{/if}

		{#if result.reverse.length > 0}
			<section class="zone zone-rev">
				<h2>역검색 · Reverse</h2>
				{#each result.reverse as hit}
					<p>
						<code>{hit.language}</code> · <code>{hit.token}</code> →
						<strong>{hit.entryIds.length}</strong> entries
					</p>
				{/each}
			</section>
		{/if}

		{#if result.partial.length > 0 && !result.exact}
			<section class="zone zone-auto">
				<h2>자동완성 · Autocomplete</h2>
				<ul class="autocomplete">
					{#each result.partial as hw (hw.norm)}
						<li>
							<button type="button" onclick={() => chooseSuggestion(hw.iast)} class="ac-item">
								{hw.iast}
							</button>
						</li>
					{/each}
				</ul>
			</section>
		{/if}
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
		align-items: center;
		margin-bottom: 1rem;
	}
	.search-input {
		flex: 1;
		padding: 0.5rem 0.75rem;
		font-size: 1.05rem;
		border: 1px solid var(--border);
		border-radius: 6px;
		background: var(--bg);
		color: var(--fg);
	}
	.search-input:focus {
		outline: 2px solid var(--accent);
		outline-offset: -1px;
	}
	.hint {
		color: var(--fg-muted);
		font-size: 0.92rem;
	}
	.header-strip {
		font-size: 0.88rem;
		padding: 0.4rem 0.6rem;
		border-bottom: 1px solid var(--border);
		margin-bottom: 1rem;
	}
	.header-strip .meta {
		margin-left: 0.6rem;
		color: var(--fg-muted);
	}
	.header-strip .dim {
		margin-left: 0.6rem;
		color: var(--fg-muted);
		font-size: 0.78rem;
	}
	.zone {
		margin-bottom: 1.5rem;
	}
	.zone h2 {
		font-size: 0.95rem;
		color: var(--fg-muted);
		font-weight: 600;
		margin: 0 0 0.4rem;
		padding-bottom: 0.2rem;
		border-bottom: 1px solid var(--border);
	}
	.count {
		color: var(--fg-muted);
		font-weight: normal;
		font-size: 0.85rem;
		margin-left: 0.4rem;
	}
	.equiv-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}
	.equiv-row {
		font-size: 0.92rem;
		padding: 0.25rem 0;
		border-bottom: 1px dashed var(--border);
	}
	.lang.skt {
		font-weight: 600;
	}
	.lang.tib {
		color: var(--accent);
	}
	.lang.zh,
	.lang.ja {
		font-family: 'Noto Sans CJK KR', sans-serif;
	}
	.sep {
		color: var(--fg-muted);
		margin: 0 0.3rem;
	}
	.cat {
		margin-left: 0.5rem;
		color: var(--fg-muted);
		font-size: 0.82rem;
	}
	.sources {
		margin-left: 0.6rem;
		color: var(--fg-muted);
		font-size: 0.78rem;
	}
	.more {
		color: var(--fg-muted);
		font-size: 0.82rem;
		font-style: italic;
	}
	.entry {
		margin-bottom: 0.8rem;
		padding: 0.5rem 0.6rem;
		background: var(--bg-alt);
		border-radius: 4px;
	}
	.entry-head {
		display: flex;
		gap: 0.4rem;
		margin-bottom: 0.3rem;
		font-size: 0.82rem;
		color: var(--fg-muted);
	}
	.dict {
		font-weight: 600;
		color: var(--fg);
	}
	.snippet {
		margin: 0;
		font-size: 0.94rem;
	}
	.ko {
		margin: 0.4rem 0 0;
		font-size: 0.88rem;
		color: var(--fg-muted);
	}
	.zone-d summary {
		cursor: pointer;
		color: var(--accent);
		font-size: 0.88rem;
		padding: 0.3rem 0;
	}
	.autocomplete {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
	}
	.ac-item {
		background: var(--bg-alt);
		border: 1px solid var(--border);
		border-radius: 12px;
		padding: 0.25rem 0.6rem;
		cursor: pointer;
		color: var(--fg);
		font-family: inherit;
		font-size: 0.88rem;
	}
	.ac-item:hover {
		background: var(--accent);
		color: var(--bg);
	}
	code {
		background: var(--bg-alt);
		padding: 0.1rem 0.3rem;
		border-radius: 3px;
		font-size: 0.85rem;
	}
</style>
