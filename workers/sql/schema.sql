-- D1 schema for stw-entries (Phase 5 Edge API + D1).
--
-- One row per dictionary entry, light schema (no body_plain/body_html to fit
-- D1 free tier 1 GB cap). Body is omitted because:
--   1. snippet_short (≤180 chars) covers most preview needs in Zone C
--   2. body_ko (Korean) included so Korean reverse search can show context
--   3. Full body (5-30 KB per entry) deferred to Phase 5e R2 lazy fetch
--
-- Indexes:
--   - idx_norm: WHERE headword_norm = ? — primary search lookup (most common)
--   - idx_dict_priority: WHERE dict_slug = ? ORDER BY priority — for "show
--     all entries from this dictionary" UI (Phase 6+)
--
-- Row size estimate:
--   id: 25 bytes (e.g. "monier-williams-063097")
--   norm: 30 bytes
--   iast: 35 bytes (with diacritics, UTF-8)
--   dict_slug: 25 bytes
--   priority: 4 bytes
--   snippet_short: 200 bytes avg (max 180 chars × 1-2 byte UTF-8)
--   body_ko: 250 bytes avg (mostly empty for most entries)
--   target_lang: 4 bytes
--   = ~580 bytes/row × 3.81M = ~2.2 GB
--
-- → Free tier 1 GB cap exceeded. Solution: import only top-1.5M
-- (rank ≤ 1.5M from frequency.json) → ~870 MB.
-- Long-tail beyond top-1.5M (rare lexical entries, archived
-- compounds, abbreviation tables) covered by reverse search +
-- Phase 5e future R2 split if needed.

DROP TABLE IF EXISTS entries;

CREATE TABLE entries (
    id              TEXT PRIMARY KEY,
    headword_norm   TEXT NOT NULL,
    headword_iast   TEXT NOT NULL,
    dict_slug       TEXT NOT NULL,
    priority        INTEGER NOT NULL,
    snippet_short   TEXT,
    body_ko         TEXT,
    target_lang     TEXT NOT NULL
);

CREATE INDEX idx_norm ON entries(headword_norm);
CREATE INDEX idx_dict_priority ON entries(dict_slug, priority);
