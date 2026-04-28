<script lang="ts">
	import {
		applyTheme,
		getStoredTheme,
		nextTheme,
		setStoredTheme,
		type Theme
	} from '$lib/stores/theme';

	let theme = $state<Theme>(getStoredTheme());

	$effect(() => {
		setStoredTheme(theme);
		applyTheme(theme);
	});

	const LABELS: Record<Theme, string> = {
		light: '☀',
		dark: '☾',
		auto: '◐'
	};

	function cycle() {
		theme = nextTheme(theme);
	}
</script>

<button
	class="theme-toggle"
	onclick={cycle}
	title="테마: {theme} (클릭으로 light → dark → auto)"
	aria-label="테마 변경"
>
	{LABELS[theme]}
</button>

<style>
	.theme-toggle {
		background: transparent;
		border: 1px solid var(--border);
		border-radius: 4px;
		padding: 0.3rem 0.55rem;
		cursor: pointer;
		color: var(--fg);
		font-size: 1rem;
		line-height: 1;
		font-family: inherit;
	}
	.theme-toggle:hover {
		background: var(--bg-alt);
	}
</style>
