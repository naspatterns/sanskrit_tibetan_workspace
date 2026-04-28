import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	compilerOptions: {
		// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
		runes: ({ filename }) => (filename.split(/[/\\]/).includes('node_modules') ? undefined : true)
	},
	kit: {
		// Static adapter — Phase 4 deploy target = Cloudflare Pages. The
		// indices in /public/indices/ are loaded eagerly at runtime via
		// fetch + Service Worker precache (ADR-011 D), so the app is fully
		// static (no SSR, no edge functions in Phase 3-4 scope).
		adapter: adapter({
			pages: 'build',
			assets: 'build',
			fallback: 'index.html', // SPA fallback for client-side routing
			precompress: false,
			strict: true
		})
	}
};

export default config;
