<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { performSearch } from '$lib/stores/search';
	import { langBalancedTop, langBalancedRest } from '$lib/search/lang';
	import type { Tier0Result } from '$lib/indices/types';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';
	import EntryFull from '$lib/components/EntryFull.svelte';

	let query = $state('');
	const result = $derived(performSearch(query));
	let modalEntry = $state<Tier0Result | null>(null);

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

	function setQuery(next: string) {
		query = next;
		// Scroll back to top so the user sees the new exact match.
		if (typeof window !== 'undefined') window.scrollTo({ top: 0, behavior: 'smooth' });
	}

	function dictFromEntryId(id: string): string {
		return id.replace(/-\d+$/, '');
	}

	const zoneCEntries = $derived(result?.exact ? langBalancedTop(result.exact.entries, 3) : []);
	const zoneDEntries = $derived(result?.exact ? langBalancedRest(result.exact.entries, 3) : []);
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

		<!-- Tibetan / long-tail miss notice — only when equiv has hits but tier0 is empty. -->
		{#if !result.exact && result.equivalents.length > 0}
			<div class="notice">
				ⓘ 이 단어는 <strong>top-10K 정의 인덱스</strong> 밖입니다 — 대응어(Zone B)는 표시되지만,
				전문 prose 정의(Zone C)는 Phase 5 Edge API 도입 후 제공 예정. (티벳어 단어는 현재 약 0.5%만
				cover.)
			</div>
		{/if}

		{#if result.equivalents.length > 0}
			<section class="zone zone-b">
				<h2>대응어 · Equivalents <span class="count">{result.equivalents.length}</span></h2>
				<ul class="equiv-list">
					{#each result.equivalents.slice(0, 50) as row}
						<li class="equiv-row">
							{#if row.skt_iast}
								<button
									type="button"
									class="lang skt term-link"
									onclick={() => setQuery(row.skt_iast!)}
									title="이 산스크리트 단어로 새 검색">{row.skt_iast}</button
								>
							{/if}
							{#if row.tib_wylie}
								<span class="sep">↔</span>
								<button
									type="button"
									class="lang tib term-link"
									onclick={() => setQuery(row.tib_wylie!)}
									title="이 티벳어 단어로 새 검색">{row.tib_wylie}</button
								>
							{/if}
							{#if row.zh}
								<span class="sep">·</span>
								<button
									type="button"
									class="lang zh term-link"
									onclick={() => setQuery(row.zh!)}
									title="이 한자로 새 검색">{row.zh}</button
								>
							{/if}
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
						... {result.equivalents.length - 50}건 더 (페이지네이션은 follow-up)
					</p>
				{/if}
			</section>
		{/if}

		{#if zoneCEntries.length > 0}
			<section class="zone zone-c">
				<h2>
					정의 · Definitions
					<span class="count">{result.exact?.entries.length ?? 0}</span>
					<span class="dim">(언어별 top-3)</span>
				</h2>
				{#each zoneCEntries as entry (entry.id)}
					<button
						type="button"
						class="entry entry-clickable"
						onclick={() => (modalEntry = entry)}
						title="전문 보기"
					>
						<header class="entry-head">
							<span class="dict">{entry.short}</span>
							<span class="prio">[{entry.priority}]</span>
							<span class="dim">{entry.target_lang}</span>
						</header>
						<p class="snippet">{entry.snippet_short}</p>
						{#if entry.ko}<p class="ko">{entry.ko}</p>{/if}
					</button>
				{/each}

				{#if zoneDEntries.length > 0}
					<details class="zone-d">
						<summary>추가 사전 {zoneDEntries.length}개 보기</summary>
						{#each zoneDEntries as entry (entry.id)}
							<button
								type="button"
								class="entry entry-clickable"
								onclick={() => (modalEntry = entry)}
							>
								<header class="entry-head">
									<span class="dict">{entry.short}</span>
									<span class="prio">[{entry.priority}]</span>
									<span class="dim">{entry.target_lang}</span>
								</header>
								<p class="snippet">{entry.snippet_short}</p>
							</button>
						{/each}
					</details>
				{/if}
			</section>
		{/if}

		{#if result.reverse.length > 0}
			<section class="zone zone-rev">
				<h2>역검색 · Reverse</h2>
				{#each result.reverse as hit, i (hit.language + i)}
					<details class="rev-detail">
						<summary>
							<code>{hit.language}</code> · <code>{hit.token}</code> →
							<strong>{hit.entryIds.length}</strong> entries (펼치기)
						</summary>
						<ul class="rev-list">
							{#each hit.entryIds.slice(0, 30) as eid}
								{@const dict = dictFromEntryId(eid)}
								<li>
									<code>{eid}</code>
									<button
										type="button"
										class="ac-item"
										onclick={() => setQuery(dict)}
										title="이 사전으로 새 검색"
									>
										→ {dict}
									</button>
								</li>
							{/each}
							{#if hit.entryIds.length > 30}
								<li class="more">... {hit.entryIds.length - 30}개 더</li>
							{/if}
						</ul>
					</details>
				{/each}
			</section>
		{/if}

		{#if result.partial.length > 0 && !result.exact}
			<section class="zone zone-auto">
				<h2>자동완성 · Autocomplete</h2>
				<ul class="autocomplete">
					{#each result.partial as hw (hw.norm)}
						<li>
							<button type="button" onclick={() => setQuery(hw.iast)} class="ac-item">
								{hw.iast}
							</button>
						</li>
					{/each}
				</ul>
			</section>
		{/if}
	{/if}

	{#if modalEntry}
		<EntryFull entry={modalEntry} onclose={() => (modalEntry = null)} />
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
	.header-strip .dim,
	.dim {
		color: var(--fg-muted);
		font-size: 0.78rem;
	}
	.header-strip .dim {
		margin-left: 0.6rem;
	}
	.notice {
		background: var(--bg-alt);
		border-left: 3px solid var(--accent);
		padding: 0.6rem 0.8rem;
		margin: 0 0 1rem;
		font-size: 0.88rem;
		color: var(--fg);
		border-radius: 0 4px 4px 0;
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
	.term-link {
		background: transparent;
		border: none;
		padding: 0.05rem 0.2rem;
		margin: 0 -0.2rem;
		font-family: inherit;
		font-size: inherit;
		color: inherit;
		cursor: pointer;
		border-radius: 3px;
	}
	.term-link:hover {
		background: var(--bg-alt);
		color: var(--accent);
	}
	.lang.tib.term-link {
		color: var(--accent);
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
		display: block;
		width: 100%;
		text-align: left;
		margin-bottom: 0.8rem;
		padding: 0.5rem 0.6rem;
		background: var(--bg-alt);
		border: 1px solid transparent;
		border-radius: 4px;
		color: inherit;
		font-family: inherit;
		font-size: inherit;
	}
	.entry-clickable {
		cursor: pointer;
		transition: border-color 0.1s;
	}
	.entry-clickable:hover {
		border-color: var(--accent);
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
		line-height: 1.5;
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
	.rev-detail {
		margin: 0.3rem 0;
	}
	.rev-detail summary {
		cursor: pointer;
		padding: 0.3rem 0;
		font-size: 0.92rem;
	}
	.rev-list {
		list-style: none;
		padding: 0.4rem 0 0.4rem 1rem;
		margin: 0;
		font-size: 0.85rem;
	}
	.rev-list li {
		padding: 0.15rem 0;
		display: flex;
		gap: 0.4rem;
		align-items: center;
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
		font-size: 0.85rem;
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
