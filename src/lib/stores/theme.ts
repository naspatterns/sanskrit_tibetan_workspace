// Three-state theme (FB-6, D16): light / dark / auto.
// Persisted to localStorage; applied to <html data-theme="…"> so theme.css
// CSS custom properties switch. View Transitions API for the crossfade
// when supported. Svelte 5 runes idiom — no nanostores wrapper needed.

export type Theme = 'light' | 'dark' | 'auto';

const STORAGE_KEY = 'stw-theme';

export function getStoredTheme(): Theme {
	if (typeof localStorage === 'undefined') return 'auto';
	const v = localStorage.getItem(STORAGE_KEY);
	return v === 'light' || v === 'dark' || v === 'auto' ? v : 'auto';
}

export function setStoredTheme(theme: Theme): void {
	if (typeof localStorage !== 'undefined') localStorage.setItem(STORAGE_KEY, theme);
}

export function applyTheme(theme: Theme): void {
	if (typeof document === 'undefined') return;
	document.documentElement.dataset.theme = theme;
}

export function nextTheme(current: Theme): Theme {
	return current === 'light' ? 'dark' : current === 'dark' ? 'auto' : 'light';
}
