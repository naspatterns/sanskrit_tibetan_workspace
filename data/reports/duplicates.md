# Duplicate Detection Report

Compared 24 candidate pairs from v1 `dict.sqlite`.

## Methodology

- **Jaccard overlap**: size of headword_norm intersection ÷ union.
- **Body similarity**: sampled 20 intersecting headwords, stripped markup, computed `difflib.SequenceMatcher` ratio on first 2000 chars, averaged.
- **Thresholds**: STRICT (Jaccard ≥0.9 AND body_sim ≥0.8), PARTIAL (Jaccard ≥0.5), DIFFERENT otherwise.

## Summary

- STRICT duplicates: 2 pair(s) — merge candidates
- PARTIAL overlaps: 7 pair(s) — review each
- Different data: 15 pair(s) — keep both

## STRICT Duplicates (Merge)

| Dict A | Dict B | Count A | Count B | ∩ | Jaccard | Body Sim | Recommendation |
|---|---|---:|---:|---:|---:|---:|---|
| `bod-rgya.apple` | `apple_bod_rgya_tshig_mdzod` | 48,488 | 48,488 | 48,488 | 1.000 | 1.000 | canonical: `apple_bod_rgya_tshig_mdzod` (merge the other) |
| `tib_15-Hopkins-Skt1992` | `tib_15-Hopkins-Skt2015` | 14,034 | 14,529 | 13,962 | 0.956 | 0.874 | canonical: `tib_15-Hopkins-Skt2015` (merge the other) |

## PARTIAL Overlaps (Review)

| Dict A | Dict B | Count A | Count B | ∩ | Jaccard | Body Sim | Recommendation |
|---|---|---:|---:|---:|---:|---:|---|
| `ashtadhyayi-en.apple` | `ashtadhyayi-anv.apple` | 3,983 | 3,983 | 3,983 | 1.000 | 0.146 | canonical: `ashtadhyayi-anv.apple` (merge the other) |
| `tib_21-Mahavyutpatti-Skt` | `tib_63-Mahavyutpatti-Scan-1989` | 8,796 | 8,818 | 8,638 | 0.962 | 0.000 | canonical: `tib_63-Mahavyutpatti-Scan-1989` (merge the other) |
| `grasg_a.dict` | `grasg_p.gretil` | 9,911 | 9,849 | 9,231 | 0.877 | 0.868 | canonical: `grasg_a.dict` (merge the other) |
| `mwse.dict` | `mw-sdt.apple` | 157,069 | 148,083 | 141,651 | 0.866 | 0.766 | canonical: `mwse.dict` (merge the other) |
| `mwse.sandic` | `mw-sdt.apple` | 178,632 | 148,083 | 145,273 | 0.801 | 0.692 | canonical: `mwse.sandic` (merge the other) |
| `mwse.dict` | `mwse.sandic` | 157,069 | 178,632 | 147,274 | 0.782 | 0.623 | canonical: `mwse.dict` (merge the other) |
| `dhatupatha-kr.apple` | `dhatupatha-sa.apple` | 1,407 | 1,476 | 1,225 | 0.739 | 0.139 | canonical: `dhatupatha-sa.apple` (merge the other) |

## Different Data (Keep Both)

| Dict A | Dict B | Count A | Count B | ∩ | Jaccard | Body Sim | Recommendation |
|---|---|---:|---:|---:|---:|---:|---|
| `dhatupatha.sandic` | `dhatupatha-kr.apple` | 810 | 1,407 | 611 | 0.380 | 0.063 | keep both — distinct data |
| `dhatupatha.sandic` | `dhatupatha-sa.apple` | 810 | 1,476 | 618 | 0.371 | 0.197 | keep both — distinct data |
| `mahavyutpatti` | `tib_21-Mahavyutpatti-Skt` | 17,913 | 8,796 | 6,051 | 0.293 | 0.213 | keep both — distinct data |
| `mahavyutpatti` | `tib_63-Mahavyutpatti-Scan-1989` | 17,913 | 8,818 | 6,050 | 0.293 | 0.030 | keep both — distinct data |
| `mwse.dict` | `mwse72.dict` | 157,069 | 46,280 | 41,033 | 0.253 | 0.706 | keep both — distinct data |
| `mw-sdt.apple` | `mwse72.dict` | 148,083 | 46,280 | 38,829 | 0.250 | 0.445 | keep both — distinct data |
| `mwse.sandic` | `mwse72.dict` | 178,632 | 46,280 | 38,700 | 0.208 | 0.326 | keep both — distinct data |
| `apte-bi.apple` | `aptese.sandic` | 35,551 | 33,835 | 10,760 | 0.184 | 0.734 | keep both — distinct data |
| `vacaspatyam.apple` | `vcpss.dict` | 46,707 | 44,207 | 12,810 | 0.164 | 0.190 | keep both — distinct data |
| `macdse.dict` | `macdse.sandic` | 18,764 | 16,651 | 1,883 | 0.056 | 0.720 | keep both — distinct data |
| `tib_17-Hopkins-TibetanSynonyms1992` | `tib_17-Hopkins-TibetanSynonyms2015` | 277 | 172 | 20 | 0.047 | 0.774 | keep both — distinct data |
| `kalpadruma.apple` | `skdss.dict` | 38,288 | 37,987 | 2,358 | 0.032 | 0.168 | keep both — distinct data |
| `bloomfield.apple` | `vedconc.gretil` | 88,700 | 24,438 | 628 | 0.006 | 0.557 | keep both — distinct data |
| `aptees.dict` | `aptese.sandic` | 11,298 | 33,835 | 168 | 0.004 | 0.099 | keep both — distinct data |
| `aptees.dict` | `apte-bi.apple` | 11,298 | 35,551 | 136 | 0.003 | 0.218 | keep both — distinct data |


## Notes

- `canonical` is chosen by: format rank (XDXF > GRETIL > SANDIC > Apple) → entry count DESC → alphabetical.
- If user prefers a different canonical, override in slug-mapping.
- PARTIAL overlaps may represent different editions; consider keeping with distinct `edition` in meta.json.