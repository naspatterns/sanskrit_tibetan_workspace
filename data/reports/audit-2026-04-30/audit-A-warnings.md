# audit-A-warnings — verify.py warning category breakdown

Scanned: **3,810,986 entries** across **148 dicts**.

## Warning category totals

| Category | Count |
|---|---:|
| FB-4 IAST invalid | 94,708 |
| norm mismatch | 87,786 |
| FB-4 HK signature | 6,974 |
| body-empty | 29 |

## Top 15 dicts by warning volume

| Dict | Total | Breakdown |
|---|---:|---|
| `equiv-yogacarabhumi-idx` | 93,413 | FB-4 IAST invalid=72,321, norm mismatch=21,092 |
| `tib-bod-rgya-tshig-mdzod` | 48,488 | norm mismatch=48,488 |
| `equiv-hirakawa` | 16,484 | norm mismatch=16,484 |
| `macdonell-sandic` | 11,960 | FB-4 IAST invalid=11,960 |
| `equiv-bonwa-daijiten` | 6,447 | FB-4 HK signature=6,162, norm mismatch=285 |
| `apte-sandic` | 4,497 | FB-4 IAST invalid=4,497 |
| `bloomfield-vedic-concordance` | 4,185 | FB-4 IAST invalid=4,158, FB-4 HK signature=27 |
| `equiv-amarakoza` | 2,238 | FB-4 IAST invalid=1,119, norm mismatch=1,119 |
| `equiv-turfan-skt-de` | 914 | FB-4 HK signature=777, norm mismatch=105, FB-4 IAST invalid=32 |
| `abhyankar-grammar` | 98 | FB-4 IAST invalid=98 |
| `equiv-mahavyutpatti` | 82 | FB-4 IAST invalid=82 |
| `tib-mahavyutpatti-skt-tib` | 78 | FB-4 IAST invalid=78 |
| `equiv-84000` | 77 | norm mismatch=77 |
| `equiv-nti-reader` | 53 | FB-4 IAST invalid=43, FB-4 HK signature=8, norm mismatch=2 |
| `vedic-rituals-hillebrandt` | 50 | FB-4 IAST invalid=50 |

## body-empty distribution

| Dict | body-empty count |
|---|---:|
| `tib-ives-waldo` | 26 |
| `tib-dan-martin` | 1 |
| `tib-jim-valby` | 1 |
| `tib-tshig-mdzod-chen-mo` | 1 |

## Flag histogram (entry-level flags[])

| Flag | Count |
|---|---:|
| `headword-script-mixed` | 51 |
| `body-empty` | 29 |

## Sample warnings per category (up to 8 each)

### FB-4 IAST invalid

- abhyankar-grammar: 'a (1)' in abhyankar-grammar-000006
- abhyankar-grammar: 'a (ೱ) k (ೱ)' in abhyankar-grammar-000007
- abhyankar-grammar: 'a ೱ p (ೱ)' in abhyankar-grammar-000008
- abhyankar-grammar: 'a:kāra' in abhyankar-grammar-000009
- abhyankar-grammar: 'aḥ ( : )' in abhyankar-grammar-000013
- abhyankar-grammar: 'aka (1)' in abhyankar-grammar-000014
- abhyankar-grammar: 'ak ( 1 )' in abhyankar-grammar-000037
- abhyankar-grammar: 'aprayeाga' in abhyankar-grammar-000332

### FB-4 HK signature

- bloomfield-vedic-concordance: 'agne vanya (TS. vithout agne)' in bloomfield-vedic-concordance-001929
- bloomfield-vedic-concordance: 'atho adhivikartanam (APMB. -cartanam)' in bloomfield-vedic-concordance-003524
- bloomfield-vedic-concordance: 'abhi yonimayohatam (SV.VS. ayohate)' in bloomfield-vedic-concordance-007291
- bloomfield-vedic-concordance: 'indro yad abhinad valam (GB. balam)' in bloomfield-vedic-concordance-018234
- bloomfield-vedic-concordance: 'ed u madhvo (SV.PB| madhor) madintaram' in bloomfield-vedic-concordance-024184
- bloomfield-vedic-concordance: "ena enasyo'karam (TB. 'karat)" in bloomfield-vedic-concordance-024195
- bloomfield-vedic-concordance: 'kakup (TB. kakuc) chanda ihendriyam' in bloomfield-vedic-concordance-025415
- bloomfield-vedic-concordance: 'tato na vicikitsati (VSKh|IIshAU. vijugupsate)' in bloomfield-vedic-concordance-031968

### norm mismatch

- equiv-84000: "'dzam bu na da" vs "'dsam bu na da" in equiv-84000-000417
- equiv-84000: "'dzam bu na da" vs "'dsam bu na da" in equiv-84000-000418
- equiv-84000: 'a tsarya dzi na mi tra' vs 'a tsarya dsi na mi tra' in equiv-84000-001348
- equiv-84000: "gshin rje'i 'jig rten" vs "nshin rje'i 'jig rten" in equiv-84000-001353
- equiv-84000: 'a mo g+ha ra dza' vs 'a mo g+ha ra dsa' in equiv-84000-001398
- equiv-84000: 'a pa ra dzi te' vs 'a pa ra dsi te' in equiv-84000-001420
- equiv-84000: 'ardzu nah' vs 'ardsu nah' in equiv-84000-001465
- equiv-84000: 'b+ha ra dwa dza' vs 'b+ha ra dwa dsa' in equiv-84000-001474
