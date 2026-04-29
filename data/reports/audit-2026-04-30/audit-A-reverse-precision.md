# audit-A-reverse-precision (v2 with full JSONL id resolution)

- reverse_en tokens: **317,878**
- reverse_ko tokens: **3,102**
- JSONL id map size: **3,810,986**

## English seed precision (top-5 strict / top-20 loose)

**Strict (top-5): 2/15** · **Loose (top-20): 6/15**

| Query | Expected | rev hits | Top-5 iast | Top-5 dicts | Strict | Loose |
|---|---|---:|---|---|---|---|
| `fire` | agni | 100 | homiḥ, homaḥ, hotṛ, huta, hu | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ❌ | ❌ |
| `water` | jala, ap, ambu, vāri, udaka | 100 | hradaḥ, homiḥ, heman, halā, srotas | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ❌ | ❌ |
| `earth` | pṛthivī, bhūmi | 100 | halā, stūpaḥ, staṃbhinī, setuḥ, sutrāman | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ❌ | ❌ |
| `duty` | dharma, kartavya, vrata | 100 | sthāpita, saurika, saukhasuptikaḥ, sevā, sādharmyam | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ❌ | ❌ |
| `soul` | ātman, jīva | 100 | hṛdayam, saṃprasādaḥ, saṃsārin, śārīraka, śārīra | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ❌ | ❌ |
| `knowledge` | jñāna, vidyā | 100 | hṛṣṭiḥ, saṃmatiḥ, saṃbuddhiḥ, saṃpradāyaḥ, samudāgamaḥ | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ❌ | ❌ |
| `compassion` | karuṇā, anukampā, dayā | 100 | hṛṇī(ṇi)yā, haṃta, saujanyam, saṃyamaḥ, śukakaḥ | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ❌ | ✅ |
| `wisdom` | prajñā, jñāna, buddhi | 100 | saumedhikaḥ, vaiduṣī, vaiduṣyam, vijñānam, vayunam, bodhiḥ | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ✅ | ✅ |
| `mind` | manas, citta, cetas | 100 | hṛdayam, smṛta, smāraṇam, sphūrtiḥ, sphurita | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ❌ | ✅ |
| `buddha` | buddha, tathāgata, sambuddha | 100 | stūpaḥ, saumāyanaḥ, saugataḥ, sūcaka, saṃbuddha | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ✅ | ✅ |
| `love` | preman, rāga, kāma, sneha | 100 | hārdam, hasita, smiṭ, smāra, smaraḥ | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ❌ | ✅ |
| `death` | mṛtyu, marana, yama | 100 | paṃcāla, kozala, hāṃtraḥ, hātram, hanu --nū | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ❌ | ❌ |
| `king` | rāja, nṛpa, narendra | 100 | hastināpura, bhaṭṭi, udbhaṭa, hastina(nā)puram, hariścaṃdraḥ | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ❌ | ❌ |
| `moon` | candra, soma, indu | 100 | tripura-rī, holākā, hima, hāsas, snehuḥ | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ❌ | ✅ |
| `sun` | sūrya, āditya, savitṛ, ravi | 100 | heliḥ, hetiḥ, hartṛ, svātiḥ --tī, syona | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ❌ | ❌ |

## Korean seed precision (top-5 strict / top-20 loose)

**Strict (top-5): 6/15** · **Loose (top-20): 7/15**

| Query | Expected | rev hits | Top-5 iast | Top-5 dicts | Strict | Loose |
|---|---|---:|---|---|---|---|
| `법` | dharma | 100 | svadharma, sthāna, sudharma, siddhāntadharmāgama, sapramāṇa | pwk, pwk, pwk, +2 | ✅ | ✅ |
| `불` | agni, buddha | 100 | holaka, homi, homa, hutāśaśālā, hutāśavṛtti | pwk, pwk, pwk, +2 | ❌ | ❌ |
| `물` | jala, ap | 100 | hrada, homi, heman, himāmbhas, himavāri | pwk, pwk, pwk, +2 | ❌ | ✅ |
| `지혜` | prajñā, jñāna | 73 | sukratūy, śūlikā, vicakṣaṇatva, maidhāvaka, medhā | pwk, pwk, pwk, +2 | ❌ | ❌ |
| `자비` | karuṇā, maitrī | 0 | — |  | ❌ | ❌ |
| `마음` | manas, citta | 29 | sumanas, sattva, sañjñā, saṅkalpa, śaṅkitamanas | bopp-latin, bopp-latin, bopp-latin, +2 | ✅ | ✅ |
| `공` | śūnyatā, kha | 0 | — |  | ❌ | ❌ |
| `도` | mārga, panthan | 0 | — |  | ❌ | ❌ |
| `신` | deva, īśvara | 100 | hutāśana, hutāśa, hutavaha, hutabhoktar, hutabhuj | pwk, pwk, pwk, +2 | ❌ | ❌ |
| `왕` | rāja, nṛpa | 100 | svārāj, skandarāja, suvidat, suvida, samudranemīpati | pwk, pwk, pwk, +2 | ✅ | ✅ |
| `인연` | nidāna, pratyaya | 0 | — |  | ❌ | ❌ |
| `지옥` | naraka, niraya | 0 | — |  | ❌ | ❌ |
| `天` | deva, svarga | 12 | svargaḥ, devaḥ, devaloka, deva, svarga | equiv-mahavyutpatti, equiv-mahavyutpatti, equiv-nti-reader, +2 | ✅ | ✅ |
| `地` | pṛthivī, bhūmi | 9 | bhūtadhātrī, medinī, bhūmi, pṛthivī, pṛthivī-pradeśa | equiv-mahavyutpatti, equiv-mahavyutpatti, equiv-nti-reader, +2 | ✅ | ✅ |
| `心` | citta, manas, hṛd | 14 | maṇḍaḥ, garbhaḥ, hṛdayam, jyeṣṭhā, jyesthā | equiv-mahavyutpatti, equiv-mahavyutpatti, equiv-mahavyutpatti, +2 | ✅ | ✅ |

## Notes

- **Strict** = expected iast appears in top-5 of priority-sorted reverse_en/ko lookup (what UI shows by default).
- **Loose** = expected iast appears in top-20 (within reach if user expands).
- A high *loose* but low *strict* score means the *data* is correct but the *priority sort* is misranking.
- A low *loose* score means the reverse extraction itself missed the gloss — extraction tuning needed in `scripts/lib/reverse_tokens.py`.

## UX caveat (orthogonal to data correctness)

`src/routes/+page.svelte:359-371` currently renders reverse hits as raw entry_ids with a dict-slug button. Even when the underlying data is correct, the user cannot tell *which Sanskrit/Tibetan word* matched their English/Korean gloss without clicking through. This is a P0 UX issue tracked in Track C.
