<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { performSearch } from '$lib/stores/search';
	import { entryLang, langBalancedTop, langBalancedRest, type EntryLang } from '$lib/search/lang';
	import { isIndexLoaded, getIndexBundle } from '$lib/indices/store';
	import { chipStyle, styleFor } from '$lib/search/source-colors';
	import type { EquivRow, HeadwordEntry, Tier0Result } from '$lib/indices/types';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';
	import EntryFull from '$lib/components/EntryFull.svelte';
	import EquivDetail from '$lib/components/EquivDetail.svelte';
	import Autocomplete from '$lib/components/Autocomplete.svelte';
	import FilterBar from '$lib/components/FilterBar.svelte';

	let query = $state('');
	// 3.2.4 — Filter state (lang pills + priority slider).
	let langFilter = $state<EntryLang | 'all'>('all');
	let priorityMax = $state(100);
	// 3.4 — Equivalents pagination + detail modal.
	let equivPageSize = $state(50);
	let equivDetail = $state<EquivRow | null>(null);
	let inputFocused = $state(false);
	let inputEl = $state<HTMLInputElement | null>(null);
	let acRef = $state<{ moveSelection: (d: number) => boolean; pickSelected: () => boolean } | null>(
		null
	);

	const result = $derived(performSearch(query));
	let modalEntry = $state<Tier0Result | null>(null);

	// 3.2.1 — URL → store reactive sync. SvelteKit's $app/state page.url
	// updates on popstate / external goto. We mirror its q param into the
	// local state when it diverges (avoiding store→URL→store loops).
	$effect(() => {
		const urlQ = page.url.searchParams.get('q') ?? '';
		if (urlQ !== query) query = urlQ;
	});

	// 3.2.5 — store → URL (debounced 120ms; replaceState keeps history clean).
	// Svelte 5 $effect cleanup cancels in-flight timer when query changes again.
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

	// 3.2.6 — ?from=entry-id deep link (open EntryFull modal directly).
	onMount(() => {
		if (!isIndexLoaded()) return;
		const fromId = page.url.searchParams.get('from');
		if (!fromId) return;
		const bundle = getIndexBundle();
		for (const info of bundle.tier0.values()) {
			const hit = info.entries.find((e) => e.id === fromId);
			if (hit) {
				modalEntry = hit;
				return;
			}
		}
	});

	function setQuery(next: string) {
		query = next;
		if (typeof window !== 'undefined') window.scrollTo({ top: 0, behavior: 'smooth' });
	}

	function dictFromEntryId(id: string): string {
		return id.replace(/-\d+$/, '');
	}

	// 3.2.4 — Apply filter, then balance.
	const filteredEntries = $derived.by(() => {
		if (!result?.exact) return [];
		let xs = result.exact.entries;
		if (langFilter !== 'all') xs = xs.filter((e) => entryLang(e) === langFilter);
		if (priorityMax < 100) xs = xs.filter((e) => e.priority <= priorityMax);
		return xs;
	});
	const zoneCEntries = $derived(langBalancedTop(filteredEntries, 3));
	const zoneDEntries = $derived(langBalancedRest(filteredEntries, 3));

	// 3.2.2 — autocomplete suggestions (debounced via timer below).
	const autocompleteItems = $derived<HeadwordEntry[]>(
		query.trim() && result ? result.partial.slice(0, 12) : []
	);
	const showAutocomplete = $derived(
		inputFocused && autocompleteItems.length > 0 && query.trim().length > 0
	);

	// 3.2.3 — Keyboard shortcuts at the page level.
	function onKeyDown(e: KeyboardEvent) {
		// '/' focuses input (unless typing in another field).
		if (e.key === '/' && document.activeElement !== inputEl && !modalEntry) {
			e.preventDefault();
			inputEl?.focus();
			return;
		}
		// 'Escape' closes modal first, else blurs/clears input.
		if (e.key === 'Escape') {
			if (modalEntry) {
				modalEntry = null;
				return;
			}
			if (showAutocomplete) {
				inputEl?.blur();
				return;
			}
			if (document.activeElement === inputEl && query) {
				query = '';
				return;
			}
		}
		// Shift+D cycles theme (handled by ThemeToggle via window listener
		// in the toggle component itself? — we wire it here for now).
		if (e.key === 'D' && e.shiftKey && !modalEntry && document.activeElement !== inputEl) {
			e.preventDefault();
			document.querySelector<HTMLButtonElement>('.theme-toggle')?.click();
		}
	}

	function onInputKey(e: KeyboardEvent) {
		if (!showAutocomplete) return;
		if (e.key === 'ArrowDown') {
			if (acRef?.moveSelection(1)) e.preventDefault();
		} else if (e.key === 'ArrowUp') {
			if (acRef?.moveSelection(-1)) e.preventDefault();
		} else if (e.key === 'Enter') {
			if (acRef?.pickSelected()) e.preventDefault();
		}
	}
</script>

<svelte:window onkeydown={onKeyDown} />

<main>
	<header class="topbar">
		<div class="search-wrap">
			<input
				bind:this={inputEl}
				type="search"
				bind:value={query}
				placeholder="dharma · धर्म · chos · 般若 · 법    (/ 누르면 포커스)"
				autocomplete="off"
				autocorrect="off"
				autocapitalize="off"
				spellcheck="false"
				class="search-input"
				onfocus={() => (inputFocused = true)}
				onblur={() => (inputFocused = false)}
				onkeydown={onInputKey}
			/>
			<Autocomplete
				bind:this={acRef}
				items={autocompleteItems}
				visible={showAutocomplete}
				onpick={(iast) => {
					setQuery(iast);
					inputEl?.blur();
				}}
				onclose={() => inputEl?.blur()}
			/>
		</div>
		<ThemeToggle />
	</header>

	{#if !query.trim()}
		<p class="hint">
			검색어를 입력하세요. IAST · HK · Devanagari · Wylie · 한자 · 한국어 모두 지원.
			<br /><kbd>/</kbd> 검색 포커스 · <kbd>Esc</kbd> clear · <kbd>Shift+D</kbd> 다크모드
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

		{#if !result.exact && result.equivalents.length > 0}
			<div class="notice">
				ⓘ 이 단어는 <strong>top-10K 정의 인덱스</strong> 밖입니다 — 대응어(Zone B)는 표시되지만,
				전문 prose 정의(Zone C)는 Phase 5 Edge API 도입 후 제공 예정. (티벳어 단어는 현재 약 0.5%만
				cover. Phase 3.3에서 별도 `tier0-bo` 인덱스로 50%+ 확장 예정.)
			</div>
		{/if}

		{#if result.equivalents.length > 0}
			<section class="zone zone-b">
				<h2>대응어 · Equivalents <span class="count">{result.equivalents.length}</span></h2>
				<ul class="equiv-list">
					{#each result.equivalents.slice(0, equivPageSize) as row}
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
							<span class="source-chips">
								{#each row.sources as slug}
									<span class="chip" style={chipStyle(slug)} title={slug}>
										{styleFor(slug).label}
									</span>
								{/each}
							</span>
							<button
								type="button"
								class="detail-btn"
								onclick={() => (equivDetail = row)}
								title="대응어 상세 보기"
								aria-label="대응어 상세"
							>
								ⓘ
							</button>
						</li>
					{/each}
				</ul>
				{#if result.equivalents.length > equivPageSize}
					<button
						type="button"
						class="show-more"
						onclick={() => (equivPageSize += 50)}
					>
						... {result.equivalents.length - equivPageSize}건 더 보기 (다음 50개)
					</button>
				{:else if equivPageSize > 50 && result.equivalents.length > 0}
					<button
						type="button"
						class="show-more"
						onclick={() => (equivPageSize = 50)}
					>
						접기 (50개로)
					</button>
				{/if}
			</section>
		{/if}

		{#if result.exact && result.exact.entries.length > 0}
			<FilterBar
				bind:langFilter
				bind:priorityMax
				totalEntries={result.exact.entries.length}
				visibleEntries={filteredEntries.length}
			/>
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
	{/if}

	{#if modalEntry}
		<EntryFull entry={modalEntry} onclose={() => (modalEntry = null)} />
	{/if}
	{#if equivDetail}
		<EquivDetail row={equivDetail} onclose={() => (equivDetail = null)} />
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
	.search-wrap {
		flex: 1;
		position: relative;
	}
	.search-input {
		width: 100%;
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
	kbd {
		background: var(--bg-alt);
		border: 1px solid var(--border);
		border-radius: 3px;
		padding: 0 0.3rem;
		font-family: inherit;
		font-size: 0.85rem;
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
	.source-chips {
		margin-left: 0.6rem;
		display: inline-flex;
		gap: 0.25rem;
		flex-wrap: wrap;
	}
	.chip {
		display: inline-block;
		padding: 0 0.4rem;
		border-radius: 8px;
		font-size: 0.7rem;
		font-weight: 600;
		line-height: 1.4;
	}
	.detail-btn {
		margin-left: 0.4rem;
		padding: 0 0.35rem;
		background: transparent;
		border: 1px solid var(--border);
		border-radius: 50%;
		color: var(--fg-muted);
		cursor: pointer;
		font-size: 0.78rem;
		line-height: 1.3;
	}
	.detail-btn:hover {
		background: var(--bg-alt);
		color: var(--accent);
		border-color: var(--accent);
	}
	.show-more {
		display: block;
		width: 100%;
		margin-top: 0.5rem;
		padding: 0.4rem;
		background: var(--bg-alt);
		border: 1px solid var(--border);
		border-radius: 4px;
		color: var(--accent);
		cursor: pointer;
		font-family: inherit;
		font-size: 0.85rem;
	}
	.show-more:hover {
		border-color: var(--accent);
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
