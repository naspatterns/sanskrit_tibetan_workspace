# Hirakawa OCR Noise Filter — Report

**Generated**: 2026-04-28 13:34 UTC

## Filter

- `source_meta.ocr_conf >= 60.0`
- `len(headword) <= 8`

Rows failing **either** condition are dropped.

## Result

| metric | rows |
|---|---:|
| input | 16,851 |
| kept | 16,484 |
| dropped | 367 (2.18%) |

### Drop reasons

| reason | count |
|---|---:|
| `low_conf` | 103 |
| `long_hw` | 258 |
| `low_conf+long_hw` | 6 |

### OCR confidence (page-level)

| bucket | input | kept | dropped |
|---|---:|---:|---:|
| `<50` | 23 | 0 | 23 |
| `50-59` | 86 | 0 | 86 |
| `60-69` | 5,210 | 5,141 | 69 |
| `70-79` | 11,380 | 11,198 | 182 |
| `80-89` | 148 | 141 | 7 |
| `90-99` | 4 | 4 | 0 |

### Headword length (CJK chars)

| bucket | input | kept | dropped |
|---|---:|---:|---:|
| `1` | 2,018 | 1,991 | 27 |
| `2` | 3,156 | 3,138 | 18 |
| `3` | 4,941 | 4,916 | 25 |
| `4` | 4,099 | 4,081 | 18 |
| `5` | 1,097 | 1,091 | 6 |
| `6` | 593 | 590 | 3 |
| `7` | 372 | 369 | 3 |
| `8` | 311 | 308 | 3 |
| `9-12` | 264 | 0 | 264 |

### Top 10 pages by drop count

| page | drops |
|---:|---:|
| 1283 | 13 |
| 1061 | 10 |
| 928 | 7 |
| 1203 | 7 |
| 1352 | 7 |
| 438 | 6 |
| 1215 | 6 |
| 267 | 5 |
| 35 | 4 |
| 51 | 4 |

### Sample dropped rows

| id | headword | len | conf | page | reason |
|---|---|---:|---:|---:|---|
| `equiv-hirakawa-000001` | `六漢識佛教語砍基礎之` | 10 | 41.7 | 20 | low_conf+long_hw |
| `equiv-hirakawa-000002` | `單音節語位廿二複音節語` | 11 | 41.7 | 20 | low_conf+long_hw |
| `equiv-hirakawa-000010` | `配列` | 2 | 44.5 | 35 | low_conf |
| `equiv-hirakawa-000011` | `次乜漢語六見出` | 7 | 44.5 | 35 | low_conf |
| `equiv-hirakawa-000012` | `本書忌收族六漢語佃見出` | 11 | 44.5 | 35 | low_conf+long_hw |
| `equiv-hirakawa-000013` | `語` | 1 | 44.5 | 35 | low_conf |
| `equiv-hirakawa-000014` | `辦` | 1 | 46.5 | 36 | low_conf |
| `equiv-hirakawa-000015` | `數順己配列` | 5 | 46.5 | 36 | low_conf |
| `equiv-hirakawa-000016` | `原則當` | 3 | 46.5 | 36 | low_conf |
| `equiv-hirakawa-000017` | `但` | 1 | 46.2 | 37 | low_conf |

## Verify (`scripts.verify` — equiv-hirakawa only)

| run | total | errors | warnings |
|---|---:|---:|---:|
| before filter | 16,851 | 0 | 16,851 |
| after filter | 16,484 | 0 | 16,484 |
| **delta** | **−367** | 0 | **−367** |

Warning reduction matches the dropped-row count one-to-one. The remaining
~16K warnings are a pre-existing `headword_norm` schema mismatch in the
extractor (the extractor stores the IAST normalization in `headword_norm`,
while `scripts.verify` recomputes it from the CJK `headword`). That issue
is independent of this filter and out of scope.

> Note: `scripts.verify` (full repo) currently exits at the meta-registry
> stage on unrelated `exclude_from_search` errors for `equiv-hopkins` and
> the `tib-hopkins-*` family. The numbers above were obtained by invoking
> `verify.verify_dict()` directly with `--dicts equiv-hirakawa` semantics.

## Notes

- Filter is applied in-place by `scripts/postprocess_hirakawa_filter.py`. Re-running the script on already-filtered data is a no-op.
- Surviving rows include the page-level OCR confidence in `source_meta.ocr_conf`, so downstream consumers can apply stricter filters at query time without re-running this pass.
- Audit trail: `data/sources/equiv-hirakawa/meta.json` records the filter thresholds and counts under the `filter` key.
- Optional Zone B index rebuild (`scripts.build_equivalents_index`) was skipped — that builder doesn't yet exist (Phase 2.5b §1, see `data/reports/equiv-pending-tasks.md`). When it lands, re-running it will pick up the −367 row delta automatically.
