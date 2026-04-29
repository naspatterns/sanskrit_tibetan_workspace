# audit-A-zh-contamination — equivalents `zh` field column-mapping defect

Date: 2026-04-30
Severity: **P1** (data correctness; affects 한자 search)

## Finding

Of 376,980 rows in `equivalents.msgpack.zst` that carry a non-empty `zh` field:

| Class | Count | Ratio |
|---|---:|---:|
| **cjk_only** (genuine 한자) | 191,726 | 50.9% |
| **mixed** (한자 + Latin) | 2,515 | 0.7% |
| **other** (digits / symbols) | 63,275 | 16.8% |
| **latin_only (Wylie or IAST in zh field)** | **119,464** | **31.7%** |

## Root cause

All 119,464 latin-contaminated rows have `sources = ['equiv-yogacarabhumi-idx']`.

Sample contamination:
```
'BDE BAR GSHEGS PA'      ← Tibetan Wylie (uppercase)
'BCOM LDAN 'DAS'         ← Tibetan Wylie
'STOBS BCU'              ← Tibetan Wylie
'sugata'                 ← Sanskrit IAST
'bhagavat'               ← Sanskrit IAST
'daśa balāni'            ← Sanskrit IAST
'daśa-bala'              ← Sanskrit IAST
```

This pattern indicates **column mapping error in `scripts/extract_equiv_yogacarabhumi.py`** (or whichever extractor produced `equiv-yogacarabhumi-idx`). The Yogācārabhūmi-Index source has 4 parallel columns (skt / tib / zh / def), and extraction has shoved Wylie/IAST into the `zh` slot for ~32% of entries.

## Impact

### Negative
- Search by 한자 input can match Wylie/IAST as `zh` channel hits (false positives).
- Search by Wylie input *also* hits the same misplaced entries via `zh` channel — produces duplicate-but-different-shape results.
- Equivalents UI displays "中文: bdebar gshegs pa" — confusing.

### Mitigated
- `equiv-yogacarabhumi-idx` is also the **largest** equiv source (234,588 rows total). The good news: ~115K of its rows have correct `zh`. Only ~119K are contaminated.
- The zh value, when wrong, is *still useful as Wylie or IAST* — search engine routes via `wylieKey` channel anyway in `engine.ts:99`. So this is more cosmetic than catastrophic.

### Effect on A4 reverse precision
- 한자 sentinels (天 / 地 / 心) all matched correctly in audit-A-reverse-precision.md — zh contamination did not surface there because reverse_ko is a separate index (not equivalents).
- Equivalents zh-channel lookup *would* surface contamination if the user types `bdebar` as a Wylie query; engine.ts line 100 only fires `tryEquiv(zhKey)` when `script === 'cjk'`, so Wylie-shaped queries skip zh channel anyway.

So the data is contaminated but the search UI is mostly tolerant. **Equivalents detail modal would show "zh: BDE BAR..."  which is wrong UI text.**

## Severity → P1 (Phase 3.6 fix)

- Not a P0 because search UX still functional (engine routing).
- Not a P3 because EquivDetail modal displays the wrong field label.

## Recommended fix

1. Inspect `scripts/extract_equiv_yogacarabhumi.py` (file likely under `scripts/extract_equiv_*` or `scripts/ocr/`).
2. Identify the column-mapping logic. Add a sanity guard: if a value contains *no* CJK codepoints and *all* characters are Latin, route it to the appropriate field (`tib_wylie` or `skt_iast`) based on uppercase/lowercase pattern.
3. Re-extract → re-build `equivalents.msgpack.zst`.
4. Re-measure with this audit script (target: latin_only ratio < 5%).

Estimated effort: ~2-4 hours (depends on extractor source data layout).

## Linked actions in audit summary

This finding adds to the Track A backlog:

- **P1-3 · zh field contamination in equiv-yogacarabhumi-idx** (~120K rows) — fix in Phase 3.6 alongside P1-1 (reverse priority sort).
