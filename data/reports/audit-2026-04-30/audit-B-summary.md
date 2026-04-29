# Track B — Data Completeness Summary

Date: 2026-04-30

## Verdict per item

| # | Item | Verdict | P-level | Linked report |
|---|---|---|---|---|
| B1 | Translation coverage re-baseline | ⚠️ ko 16.3%, EN-source 0% | P1 | `audit-A-translations.md` + `audit-B-coverage.md` |
| B2 | DE/FR/LA quality 498 sample | ❌ **score 1.87/4.0** — v1 ko is per-token substitution, not real translation. 0/424 reach 30% Hangul. | **P0-2 NEW** | `audit-B-eu-quality.md` |
| B3 | Tibetan tier0-bo coverage | ✅ **47/50 (94%)** sentinel hits, median 13 entries/headword | — | `B3-tibetan.log` |
| B4 | Equivalents source unbalance | ✅ Already in Track A (audit-A-indices.md A3) | — | `audit-A-indices.md` |
| B5 | OCR Tier C cost | 불광사전 ~$4.50, 梵語佛典 ~$0.30, defer until P1-2 done | P3 | `B5-ocr.log` |
| B6 | Long-tail distribution | ⚠️ 98.4% of unique words are long-tail; tier0 covers 15.7% of entries | Phase 5 design driver | `audit-B-coverage.md` §B6 |
| B7 | Dead zone leakage | ✅ **0 leaks** across 35 excluded dicts | — | `audit-B-coverage.md` §B7 |
| (bonus) | zh field contamination | ⚠️ 119K Wylie/IAST in zh field (equiv-yogacarabhumi-idx) | **P1 new** | `audit-A-zh-contamination.md` |

## Headline numbers

- **Tibetan top-10K**: 94% sentinel coverage, median 13 entries per headword. `klong chen` (Phase 3.3 success case): 9 definitions across 5 dicts.
- **Long-tail**: 1.19M unique headwords outside top-20K (98.4%). Covered only via Phase 5 Edge API.
- **Dead zone filter**: ✅ 35 excluded dicts contribute 0 entries to tier0 / tier0-bo / equivalents.
- **OCR pending**: 2 candidates (불광사전 2GB, 梵語佛典 62MB). 불광사전 useful for Korean coverage push (~$4.50). Both deferred until after Phase 4 deploy.
- **zh contamination**: 31.7% of zh-bearing equiv rows are Wylie/IAST (column-mapping defect in yogācārabhūmi extractor).

## What's good

- `body.plain` non-empty for 99.99924% (29 flagged)
- `headword_iast` 100% covered for Sanskrit/Pali entries
- Tibetan top-10K rich (94% coverage, 13 median entries/hw)
- Cross-source dedup working as designed
- exclude_from_search filter clean

## What needs Phase 3.6 attention

1. **P1-1** reverse_en priority sort (covered in Track A)
2. **P1-2** Korean coverage push for English-source dicts (~$30 batch)
3. **P1-3** zh field contamination fix (~2-4h Yogācārabhūmi re-extract)

## What needs Phase 4+

- **B5** OCR Tier C — 불광사전 한국어 보강 ($4.50, P2)
- Phase 5 Edge API + D1 — 84.3% long-tail entries

## B2 — DE/FR/LA quality summary (498 samples)

- Overall score **1.87/4.0** (between D and C)
- Distribution: A=3 · B=36 · C=354 · D=105
- Median Hangul ratio in DE/FR/LA: 5–7% (real translation would be 60-80%)
- 0/424 DE/FR/LA samples reach 30% Hangul
- 13.3% (66/498) byte-identical to source
- 2 dicts (bopp-comparative, vedic-rituals-hillebrandt) entirely empty `body.ko` (target_lang=en, scope mismatch + measurement bug in coverage report)

### Per-dict score (priority order for re-translation)

| Priority | Dict | Score | Notes |
|---:|---|---:|---|
| 1 | `pwg` | 1.95 | 122K entries, biggest impact |
| 2 | `pwk` | 1.89 | 135K entries |
| 3 | `cappeller-german` | 1.92 | 30K |
| 4 | `schmidt-nachtrage` | 1.81 | 28K |
| 5 | `stchoupak` | 1.94 | 24K (FR) |
| 6 | `burnouf` | 1.92 | 19K (FR) |
| 7 | `grassmann-vedic` | 1.85 | 10K |
| 8 | `bopp-latin` | 1.82 | 9K (LA) |

### Cost-benefit
- $225 batch ÷ ~390K entries = $0.00058/entry — strongly cost-effective
- Without fix: Korean users see mostly-DE/FR/LA prose with sprinkled Korean function words

## Track B handoff

✅ Track B complete. **P0-2 added to audit summary** (DE/FR/LA re-translation $225 batch, Phase 3.6 priority).

Next: Track D summary + Day 2 commit + Track C (sentinel queries → production preview demo).
