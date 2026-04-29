# audit-A-indices — A3 + A4 + A5 combined

## A3 — equivalents cross-source dedup

- Keys: **480,732**
- Rows total: **660,775**
- Rows with ≥2 sources (dedup merge): **6,823** (1.03%)
- Keys touched by ≥1 multi-source row: **6,068**

### Sources histogram (per-row presence count)

| Source | Rows |
|---|---:|
| `equiv-yogacarabhumi-idx` | 234,588 |
| `equiv-bonwa-daijiten` | 84,540 |
| `equiv-negi` | 76,524 |
| `equiv-tib-chn-great` | 61,740 |
| `equiv-lokesh-chandra` | 43,968 |
| `equiv-84000` | 36,750 |
| `equiv-mahavyutpatti` | 33,702 |
| `equiv-hirakawa` | 32,968 |
| `equiv-hopkins-tsed` | 32,580 |
| `equiv-nti-reader` | 16,310 |
| `equiv-turfan-skt-de` | 9,316 |
| `equiv-karashima-lotus` | 4,061 |
| `equiv-amarakoza-synonyms` | 980 |
| `equiv-bodkye-hamsa` | 12 |

### Top 15 cross-source merges

| Combo | Count |
|---|---:|
| equiv-84000 + equiv-lokesh-chandra | 1,962 |
| equiv-bonwa-daijiten + equiv-turfan-skt-de | 1,677 |
| equiv-84000 + equiv-hopkins-tsed | 668 |
| equiv-lokesh-chandra + equiv-negi | 658 |
| equiv-hopkins-tsed + equiv-lokesh-chandra | 582 |
| equiv-84000 + equiv-negi | 282 |
| equiv-84000 + equiv-hopkins-tsed + equiv-lokesh-chandra | 240 |
| equiv-karashima-lotus + equiv-nti-reader | 230 |
| equiv-amarakoza-synonyms + equiv-bonwa-daijiten | 114 |
| equiv-mahavyutpatti + equiv-negi | 74 |
| equiv-amarakoza-synonyms + equiv-bonwa-daijiten + equiv-turfan-skt-de | 63 |
| equiv-hopkins-tsed + equiv-negi | 58 |
| equiv-84000 + equiv-lokesh-chandra + equiv-negi | 54 |
| equiv-mahavyutpatti + equiv-yogacarabhumi-idx | 33 |
| equiv-hopkins-tsed + equiv-lokesh-chandra + equiv-negi | 26 |

## A4 — reverse_en / reverse_ko sentinel precision

- reverse_en tokens: **317,878**
- reverse_ko tokens: **3,102**

### English seeds (10)

| Query | Expected | Hit? | Retrieved top-5 iast |
|---|---|---|---|
| `fire` | agni | ❌ | ?, ?, hotṛ, huta, hu |
| `water` | jala, ap, ambu, vāri, udaka | ❌ | ?, ?, heman, hala, srotas |
| `earth` | pṛthivī, bhūmi | ❌ | hala, ?, ?, seṭuḥ, sutrāman |
| `duty` | dharma, kartavya, vrata | ❌ | ?, saurika, ?, seva, ? |
| `soul` | ātman, jīva | ❌ | hṛdayam, ?, ?, śārīraka, śārīra |
| `knowledge` | jñāna, vidyā | ❌ | ?, ?, ?, ?, ? |
| `compassion` | karuṇā, anukampā, dayā | ❌ | ?, ?, ?, ?, ? |
| `wisdom` | prajñā, jñāna, buddhi | ❌ | ?, ?, ?, ?, ? |
| `mind` | manas, citta, cetas | ❌ | hṛdayam, smṛta, ?, ?, sphurita |
| `buddha` | buddha, tathāgata, sambuddha | ✅ | ?, ?, ?, sūcaka, saṃbuddha |

**English precision (top-5): 1/10**

### Korean seeds (10)

| Query | Expected | Hit? | Retrieved top-5 iast |
|---|---|---|---|
| `법` | dharma | ❌ | ?, sthāna, ?, ?, ? |
| `불` | agni, buddha | ❌ | holākā, ?, ?, ?, ? |
| `물` | jala, ap | ❌ | hrada, ?, heman, ?, ? |
| `지혜` | prajñā, jñāna | ❌ | ?, śūlika, ?, ?, medhā |
| `자비` | karuṇā, maitrī | ❌ | no rev hit |
| `마음` | manas, citta | ✅ | sumanas, ṣaṭtva, ?, ?, ? |
| `공` | śūnyatā, kha | ❌ | no rev hit |
| `도` | mārga, panthan, dao | ❌ | no rev hit |
| `신` | deva, īśvara | ❌ | ?, ?, ?, ?, ? |
| `왕` | rāja, nṛpa | ❌ | svārāj, ?, ?, ?, ? |

**Korean precision (top-5): 1/10**

## A5 — tier0 ↔ tier0-bo split

- tier0 keys: **10,000**
- tier0-bo keys: **10,000**
- intersection: **910** (9.10% of smaller)

- tier0 keys that look Wylie (space or apostrophe): **642**
- tier0-bo keys with Sanskrit diacritics: **0**

### Sample overlap (both indices have this norm)

- `'bras` — skt iast `'bras` | bo iast `'bras`
- `'bras bu` — skt iast `'bras bu` | bo iast `'bras bu`
- `'brel ba` — skt iast `'brel ba` | bo iast `'brel ba`
- `'brug sgra` — skt iast `'brug sgra` | bo iast `'brug sgra`
- `'bum` — skt iast `'bum` | bo iast `'bum`
- `'byung ba` — skt iast `'byung ba` | bo iast `'byung ba`
- `'byung po` — skt iast `'byung po` | bo iast `'byung po`
- `'chab pa` — skt iast `'chab pa` | bo iast `'chab pa`
- `'char ba` — skt iast `'char ba` | bo iast `'char ba`
- `'char ka` — skt iast `'char ka` | bo iast `'char ka`
- `'ching ba` — skt iast `'ching ba` | bo iast `'ching ba`
- `'dod chags` — skt iast `'dod chags` | bo iast `'dod chags`
- `'dod pa` — skt iast `'dod pa` | bo iast `'dod pa`
- `'dren pa` — skt iast `'dren pa` | bo iast `'dren pa`
- `'dres pa` — skt iast `'dres pa` | bo iast `'dres pa`
- `'du 'dzi` — skt iast `'du 'dzi` | bo iast `'du 'dzi`
- `'du ba` — skt iast `'du ba` | bo iast `'du ba`
- `'du byed` — skt iast `'du byed` | bo iast `'du byed`
- `'du shes` — skt iast `'du shes` | bo iast `'du shes`
- `'dul ba` — skt iast `'dul ba` | bo iast `'dul ba`
