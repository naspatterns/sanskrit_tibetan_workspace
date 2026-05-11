// Phase 4.1 Mobile Rescue — runtime detection helpers.
//
// Decides whether to eagerly pre-load the 89 MB index bundle, or to skip
// it and route every search through the Phase 5 Edge API. The Edge API is
// authoritative for the full 2.98M-entry corpus, so "lazy" mode is a
// completely valid UX — just adds ~600ms per query (Korea→ICN cold).

const LS_KEY = 'stw-data-mode';

/** Stored preference, if any. Lets the user pin a mode via the settings
 * toggle so it survives reloads even when the network looks fast. */
export type DataMode = 'auto' | 'lazy' | 'full';

export function getStoredDataMode(): DataMode {
	if (typeof localStorage === 'undefined') return 'auto';
	const v = localStorage.getItem(LS_KEY);
	return v === 'lazy' || v === 'full' ? v : 'auto';
}

export function setStoredDataMode(m: DataMode): void {
	if (typeof localStorage === 'undefined') return;
	if (m === 'auto') localStorage.removeItem(LS_KEY);
	else localStorage.setItem(LS_KEY, m);
}

/** True when the user is on a likely-slow connection. Uses NetworkInformation
 * API where available (Chromium); otherwise falls back to a viewport heuristic
 * since 99% of small viewports are mobile anyway. */
function isProbablySlow(): boolean {
	if (typeof navigator === 'undefined') return false;
	type NetInfo = { effectiveType?: string; saveData?: boolean };
	const conn = (navigator as { connection?: NetInfo }).connection;
	if (conn) {
		if (conn.saveData) return true;
		if (conn.effectiveType && ['slow-2g', '2g', '3g'].includes(conn.effectiveType)) return true;
		// effectiveType === '4g' OR unknown → fall through to viewport check
	}
	if (typeof window !== 'undefined' && window.matchMedia) {
		// Treat phones as slow even on wifi — the 700 MB heap from a full bundle
		// causes RAM pressure / tab eviction on low-end Android more often than
		// the bandwidth alone would.
		if (window.matchMedia('(max-width: 768px)').matches) return true;
	}
	return false;
}

/** Resolve the effective mode by combining the stored preference with
 * runtime detection. Returns the mode the layout should act on. */
export function resolveDataMode(): 'lazy' | 'full' {
	const stored = getStoredDataMode();
	if (stored !== 'auto') return stored;
	return isProbablySlow() ? 'lazy' : 'full';
}
