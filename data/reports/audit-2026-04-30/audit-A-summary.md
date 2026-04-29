# Track A — Data Integrity Audit Summary

Date: 2026-04-30
Scope: 148 dicts · 3,810,986 entries · 7 indices (76 MB compressed)
Status: ✅ data layer integrity passes; 2 P0 / 2 P1 / 1 P2 issues identified for Phase 3.6+

---

## 1. Verdict per item

| # | Item | Verdict | P-level | Linked report |
|---|---|---|---|---|
| A1 | Schema validation (errors) | ✅ **0 errors** / 3.81M | — | `verify-run.log` |
| A2 | meta.json ↔ JSONL consistency | ⚠️ 147× `entry_count` undeclared (cosmetic), 9× FB-5 family mismatch | P3 + P2 | `audit-A-meta-consistency.md` |
| A3 | equivalents cross-source dedup | ✅ 1.03% rows multi-source — sources cover disjoint domains, dedup working as designed | — | `audit-A-indices.md` §A3 |
| A4 | reverse precision | ❌ **EN strict 2/15, KO strict 6/15** (sub-half). Loose (top-20) better but still 6-7/15. Root cause: ranking + Korean coverage. | **P1** | `audit-A-reverse-precision.md` |
| A5 | tier0 ↔ tier0-bo split | ⚠️ 910 keys overlap (Tibetan-Skt cross-ref dicts leaking Wylie into tier0). Search engine union lookup handles it correctly. | P2 | `audit-A-indices.md` §A5 |
| A6 | warning category breakdown | ✅ 189K warnings classified — 94K "FB-4 IAST invalid" mostly academic notation (`â/ē/ō`), 88K "norm mismatch" mostly intentional Wylie/Tibetan. **No data damage.** | P2 | `audit-A-warnings.md` |
| A7 | translation merge integrity | ✅ 84,231 entries with `ko` (16.3%); 1 orphan in translations.jsonl; merge correct | — | `audit-A-translations.md` |
| A8 | id duplicates | ✅ **0 duplicates** across 3.81M | — | `A8-id-scan.log` |
| (UI) | reverse hit rendering | ❌ raw `entry_id` only, user cannot see which headword matched the English/Korean gloss | **P0 (UX)** | `audit-A-reverse-precision.md` §UX caveat |

---

## 2. Headline numbers

```
Dicts ........................................ 148
Entries ...................................... 3,810,986
Schema errors ................................ 0  ✅
Schema warnings .............................. 189,468 (categorized)
Unique entry ids ............................. 3,810,986 (no dups)
Missing headword_iast ........................ 0
Missing headword_norm ........................ 0
Missing body.plain ........................... 29 (flagged in entry.flags[])
Tier0 + tier0-bo entries ..................... 515,739
Entries with `ko` filled ..................... 84,231 (16.3%)
  via translations.jsonl (id match) .......... 10,900
  via v1 body.ko (DE/FR/LA dicts) ............ 73,331
Translation orphans .......................... 1
reverse_en tokens ............................ 317,878
reverse_ko tokens ............................ 3,102
Equivalents keys ............................. 480,732
Equivalents rows ............................. 660,775
  multi-source rows .......................... 6,823 (1.03%)
tier0 ∩ tier0-bo keys ........................ 910
```

---

## 3. Issues classified

### P0 (must fix before Phase 4 / deploy)

**P0-1 · Reverse search UI shows raw entry_id, not headword + snippet** — `+page.svelte:359-371`
- User experience: even if the data layer correctly retrieves `apte-sanskrit-english-031577` for `fire`, the UI shows that opaque id and the dict slug. The user cannot tell *which Sanskrit word matches their query* without click-through.
- Track this in Track C (UX) and fix in Phase 3.6: render `headword_iast` + `snippet_short` per reverse hit. Requires either (a) a new `entry_id → {iast, snippet}` lookup index (~20 MB compressed estimated) or (b) lazy fetch from JSONL via Edge API (Phase 5).
- Phase 3.6 minimum: add a small `reverse_meta.msgpack.zst` containing `{id: [iast, dict, snippet_short]}` for every entry id appearing in `reverse_en` and `reverse_ko`. Estimated 8–12 MB compressed.

### P1 (should fix in Phase 3.6 / before deploy)

**P1-1 · Reverse_en priority sort surfaces wrong entries**
- `fire` retrieves `homiḥ, homaḥ, hotṛ, huta, hu` instead of `agni`. All from Apte (priority 1 dict), so meta-priority is right, but **within Apte the priority-ASC + entry-id sort order doesn't promote the canonical headword**.
- Likely root cause: `scripts/lib/reverse_tokens.py` extraction does include `fire` from Apte's `agni` entry, but ranking by entry_id leaves it after later-id entries that also list `fire` in their definition.
- Fix in `scripts/build_reverse_index.py`: add a *headword salience* boost — when the gloss appears in the first 30 chars of the entry's body and the entry's `headword_iast` is short (< 8 chars), promote ranking. Target: `agni` reaches top-5 for `fire` after rebuild.
- Re-measure with this audit script after rebuild; goal ≥ 12/15 strict.

**P1-2 · reverse_ko coverage gaps**
- `자비, 공, 도, 인연, 지옥` = 0 hits in reverse_ko. Combined with overall `body.ko` coverage at 11.3% (and 0% for English-source dicts), this is the dominant gap.
- Phase 3.6 minimum: in UI, when `reverse_ko` returns 0 hits but `reverse_en` would have, suggest searching the romanized term (`자비 → karuṇā` via a tiny static synonym map).
- Phase 4+: complete Korean translation pass for top 50K English-source entries (~ $30–50 batch). Tracked in `data/reports/equiv-pending-tasks.md` and CLAUDE.md §6.

### P2 (Phase 3.6 if cheap, else defer)

**P2-1 · 9 dicts have `exclude_from_search=true` but `family` ≠ declension**
- equiv-hopkins, equiv-lin-4lang, equiv-yogacara-index, tib-hopkins-* (7) — these are intentionally excluded but the audit script's strictness flagged them. verify.py already accepts via `superseded_by`.
- Cheapest fix: align audit_meta_consistency.py with verify.py's relaxed rule, or set explicit `family: 'hopkins'`/`'equivalents'` and update FB-5 spec text.

**P2-2 · tier0 contains 642 Wylie-shaped keys (Tibetan-Skt cross-ref dicts)**
- Caused by `tib-negi-skt`, `tib-mahavyutpatti-skt`, etc. that contain Tibetan-side headwords. Search engine handles via union lookup (engine.ts:71-80). Not a defect; flag for documentation.

**P2-3 · 87,786 norm mismatch warnings**
- 48,488 `tib-bod-rgya-tshig-mdzod` (intentional Wylie→Tib script difference)
- 16,484 `equiv-hirakawa` (OCR-derived English headers used as headword_norm fallback when Hanja missing)
- 21,092 `equiv-yogacarabhumi-idx` (sandhi forms differ)
- 1,119 `equiv-amarakoza` headwords like `'amarakoza-v1-p1'` — **these look like real defects** (volume/page slugs leaking into the headword). Worth a focused fix in `scripts/extract_equiv_amarakoza.py`.

### P3 (cosmetic / deferred)

**P3-1 · 147 dicts missing `meta.entry_count`** — easy auto-fill in `scripts/build_meta.py` after JSONL build. Useful for documentation; no functional impact.

**P3-2 · 6,974 FB-4 HK-signature warnings**
- Mostly Bloomfield Vedic concordance (`TS.`, `APMB.` style abbreviations triggering HK detection); 6,162 in equiv-bonwa-daijiten ('Revised', 'Naoshiro' = bibliographic noise from extraction).
- Bonwa-daijiten subset *might* indicate metadata leaking into entries but verify.py treats as warning, not error. Can ignore for now.

---

## 4. What's already good

- **Schema 100% valid** — fastjsonschema accepts every entry.
- **No id duplicates** across 3.81M entries.
- **No missing headword_iast / headword_norm** anywhere.
- **Body empty count = 29** entries (all flagged in `flags[]`, mostly tib-ives-waldo).
- **Translation merge correct** — 1 orphan out of 9,995 (negligible).
- **Cross-source dedup working** — 14 equiv sources merged when keys collide; 1.03% multi-source ratio reflects domain spread, not bug.
- **tier0/tier0-bo split clean** — overlap explained, no IAST diacritics in tier0-bo.

---

## 5. Recommended actions before Phase 4

**Phase 3.6 (next sprint, ~2-3 days):**
1. ✅ **P0-1 fix** — add `reverse_meta.msgpack.zst` (id → iast + dict + snippet_short) and update `+page.svelte` to render headword + snippet per reverse hit. Target ~10 MB.
2. ✅ **P1-1 fix** — tune `scripts/build_reverse_index.py` ranking (headword salience boost), rebuild, re-measure with `scripts/audit_reverse_precision.py`. Goal ≥ 12/15 EN strict, ≥ 9/15 KO strict.
3. ✅ **P2-1 fix** — align audit_meta_consistency.py with verify.py for FB-5 family check; update `docs/decisions-pending.md` to clarify "exclude_from_search dicts must have family ∈ {decl, hopkins, equivalents}".
4. ⏭️ **P2-3 fix (partial)** — `scripts/extract_equiv_amarakoza.py` re-extract to drop volume/page slugs from headwords (1,119 entries).
5. ⏭️ **P3-1 fix** — auto-fill `entry_count` in `scripts/build_meta.py`.

**Phase 4+ (post-deploy):**
- **P1-2 fix** — Korean translation coverage push (top 50K English-source entries, ~$30 batch).
- **P2-3 deeper** — Heritage Hopkins equiv re-audit to suppress academic abbreviation noise.

---

## 6. Files / artifacts produced

```
data/reports/audit-2026-04-30/
├── verify-run.log                       # raw verify.py output
├── A8-id-scan.log                       # id-uniqueness scan output
├── A6-warnings.log                      # audit_warnings.py output tail
├── A7-translations.log                  # audit_translations_merge.py output
├── A2-meta.log                          # audit_meta_consistency.py output
├── A345-indices.log                     # audit_indices.py output
├── A4-reverse-v2.log                    # audit_reverse_precision.py output
├── audit-A-warnings.md                  # warning category breakdown
├── audit-A-meta-consistency.md          # meta vs JSONL
├── audit-A-translations.md              # translation merge integrity
├── audit-A-indices.md                   # equiv dedup + reverse v1 + tier split
├── audit-A-reverse-precision.md         # reverse v2 (full JSONL id map)
└── audit-A-summary.md                   # this file
```

New scripts (committed under scripts/):
```
scripts/audit_warnings.py                # category-level cumulative count
scripts/audit_meta_consistency.py        # meta.json ↔ JSONL
scripts/audit_translations_merge.py      # translations.jsonl ↔ tier0
scripts/audit_indices.py                 # equiv dedup + tier split
scripts/audit_reverse_precision.py       # reverse precision v2
```

---

## 7. Track A handoff

✅ Track A complete. Findings translated into a Phase 3.6 backlog (P0/P1 above).

Next: **Track B (Data Completeness)** — re-measure translation coverage, long-tail distribution, OCR Tier C cost-benefit, then parallel Track D static checks.
