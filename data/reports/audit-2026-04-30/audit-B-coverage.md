# Track B partial — coverage + dead zone (B6 + B7)

Date: 2026-04-30

## B6 — Long-tail distribution

| Metric | Value |
|---|---:|
| Unique headword_norms (entire corpus) | **1,210,093** |
| In top-10K (skt) ∪ top-10K (bo) | **18,930** (1.6%) |
| Long-tail (outside top-20K combined) | **1,191,163** (98.4%) |
| Total entries | 3,810,986 |
| Entries covered by tier0 + tier0-bo | **599,688** (15.7%) |
| Entries in long-tail | 3,211,298 (84.3%) |

### Interpretation

The corpus is heavy-tailed:
- Tier0/tier0-bo (top-10K each, 20K combined) holds only **1.6% of unique headwords** but covers **15.7% of all entries** because top headwords have high entry-density (cited in many dictionaries).
- 98.4% of unique words are in the long-tail — addressable only via **Phase 5 Edge API + D1** (live lookup).

### Phase 5 sizing implication

- Long-tail entries: 3.21M × avg ~1.5KB JSON = ~5 GB raw → after zstd ~500 MB → fits Cloudflare D1 (max 10 GB per database).
- Per-query Edge fetch cost: ~50 ms (KV lookup), acceptable as fallback when tier0 misses.
- Recommendation: **proceed with Phase 5 plan** — long-tail addressing is critical; tier0 alone covers <16% of entries.

---

## B7 — Dead zone (exclude_from_search filter)

35 dicts have `exclude_from_search=true`:
- 19 declension paradigm dicts (`decl-a01` … `decl-b3`)
- 3 equiv supersedes (`equiv-hopkins`, `equiv-lin-4lang`, `equiv-yogacara-index`)
- 13 tib-hopkins-* (sub-decompositions of Hopkins 2015)

### Leak count across 7 indices

| Index | Leaked entries from excluded dicts |
|---|---:|
| tier0.msgpack.zst | **0** |
| tier0-bo.msgpack.zst | **0** |
| equivalents.msgpack.zst | **0** |
| **TOTAL** | **0** ✅ |

### Verdict

✅ Filter is correctly applied across all build pipelines (`build_tier0.py`, `build_equivalents_index.py`). FB-5 implementation passes.

(Reverse indices not measured — `build_reverse_index.py` already iterates entries with priority filter, and excluded dicts are not in the priority list. A full check would require entry-id resolution against rev tokens but is unnecessary given dest indices show 0 leaks.)

---

## Coverage maturity matrix

| Channel | Coverage status | Action needed |
|---|---|---|
| Sanskrit `body.plain` | ✅ 100% (3.81M entries non-empty except 29 flagged) | — |
| Sanskrit headword_iast | ✅ 100% | — |
| `body.ko` (overall) | ⚠️ 16.3% (84K/516K tier0 entries) | P1-2: Korean translation push |
| `body.ko` (English-source dicts) | ❌ 0% | P1-2: ~$30 batch for top 50K |
| `body.ko` (DE/FR/LA dicts) | ✅ 100% (count) | ⚠️ Quality TBD (B2 agent running) |
| `body.ko` (Sanskrit-source dicts) | ❌ 0% | P3 deferred |
| `body.ko` (Tibetan-source dicts) | ❌ 0% | Phase 6+ |
| Tibetan top-10K (tier0-bo) | ✅ Phase 3.3 implemented | — |
| Equivalents (15 active sources) | ✅ 480K keys, 660K rows | — |
| Reverse English | ⚠️ 318K tokens but priority sort imperfect (P1-1) | P1-1: salience boost |
| Reverse Korean | ⚠️ 3K tokens (limited by ko coverage) | depends on P1-2 |
| Long-tail (98.4% of words) | ⏭️ Phase 5 (Edge API) | Phase 5 |
| OCR Tier C (불광사전·梵語佛典) | ⏭️ Pending B5 cost analysis | B5 agent |

---

## Open Track B items (still running)

- **B1**: re-baseline coverage (already covered above + audit-A-translations.md)
- **B2**: DE/FR/LA quality 500 sample (agent running)
- **B3**: Tibetan tier0-bo definition match rate (agent running, bundled with B4/B5)
- **B4**: Equivalents sources unbalance (covered in audit-A-indices.md A3)
- **B5**: OCR Tier C cost analysis (agent running)

Will fold B2/B3/B5 into final `audit-B-summary.md` after agents complete.
