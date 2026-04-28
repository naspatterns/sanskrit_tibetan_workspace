<script lang="ts">
	// Step 3 placeholder — exposes the loaded IndexBundle for sanity checking
	// in DevTools while Step 4 (search engine) is built. Real search UI
	// arrives in Step 6.

	import { getIndexBundle } from '$lib/indices/store';

	const bundle = getIndexBundle();
	const stats = {
		tier0: bundle.tier0.size,
		equivalents: bundle.equivalents.size,
		reverseEn: bundle.reverseEn.size,
		reverseKo: bundle.reverseKo.size,
		headwords: bundle.headwords.length
	};

	// Pin globally so DevTools console can poke at it during development.
	if (typeof window !== 'undefined') {
		(window as unknown as { __IDX__: typeof bundle }).__IDX__ = bundle;
	}
</script>

<main>
	<h1>Sanskrit-Tibetan Workspace</h1>
	<p>인덱스 로드 완료. (Step 3) 검색 UI는 Step 4-6에서 추가 예정.</p>

	<table>
		<thead>
			<tr><th>index</th><th class="num">size</th></tr>
		</thead>
		<tbody>
			<tr><td>tier0 (headwords)</td><td class="num">{stats.tier0.toLocaleString()}</td></tr>
			<tr><td>equivalents (lookup keys)</td><td class="num">{stats.equivalents.toLocaleString()}</td></tr>
			<tr><td>reverseEn (tokens)</td><td class="num">{stats.reverseEn.toLocaleString()}</td></tr>
			<tr><td>reverseKo (tokens)</td><td class="num">{stats.reverseKo.toLocaleString()}</td></tr>
			<tr><td>headwords (sorted entries)</td><td class="num">{stats.headwords.toLocaleString()}</td></tr>
		</tbody>
	</table>

	<p class="hint">
		DevTools 콘솔에서 <code>window.__IDX__</code> 로 인덱스 직접 접근 가능.
	</p>
</main>

<style>
	main {
		max-width: 640px;
		margin: 3rem auto;
		padding: 0 1rem;
		font-family: -apple-system, ui-sans-serif, sans-serif;
	}
	h1 {
		font-size: 1.4rem;
		margin: 0 0 0.4rem;
	}
	table {
		border-collapse: collapse;
		width: 100%;
		margin: 1rem 0;
	}
	th,
	td {
		padding: 0.4rem 0.6rem;
		border-bottom: 1px solid #eee;
		text-align: left;
	}
	th {
		background: #f7f7f7;
	}
	td.num,
	th.num {
		text-align: right;
		font-variant-numeric: tabular-nums;
	}
	.hint {
		color: #666;
		font-size: 0.85rem;
	}
	code {
		background: #f7f7f7;
		padding: 0.1rem 0.3rem;
		border-radius: 3px;
		font-size: 0.85rem;
	}
</style>
