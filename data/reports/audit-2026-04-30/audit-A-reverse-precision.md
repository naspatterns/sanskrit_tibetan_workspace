# audit-A-reverse-precision (v2 with full JSONL id resolution)

- reverse_en tokens: **317,878**
- reverse_ko tokens: **20,962**
- JSONL id map size: **3,815,934**

## English seed precision (top-5 strict / top-20 loose)

**Strict (top-5): 9/15** · **Loose (top-20): 10/15**

| Query | Expected | rev hits | Top-5 iast | Top-5 dicts | Strict | Loose |
|---|---|---:|---|---|---|---|
| `fire` | agni | 100 | raḥ, vami, sāgni, vāśiḥ, peruḥ | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ❌ | ❌ |
| `water` | jala, ap, ambu, vāri, udaka | 100 | xap, xara, yoniḥ, xaṇaḥ, xaara | apte-bilingual, apte-bilingual, apte-bilingual, +2 | ✅ | ✅ |
| `earth` | pṛthivī, bhūmi | 100 | ḷ, gmā, kuḥ, sahā, mahī | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ❌ | ❌ |
| `duty` | dharma, kartavya, vrata | 100 | kartva, dutyupahāsa, kara, upadharma, kṛ | monier-williams, monier-williams, macdonell, +2 | ✅ | ✅ |
| `soul` | ātman, jīva | 100 | vāsuḥ, vedātman, viśvātman, yajñātman, viśvātman | apte-sanskrit-english, monier-williams, monier-williams, +2 | ✅ | ✅ |
| `knowledge` | jñāna, vidyā | 100 | ṇaḥ, vidyā, saṃvid, vidman, vāsanā | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ✅ | ✅ |
| `compassion` | karuṇā, anukampā, dayā | 100 | ghṛṇā, karuṇā, u, dayā, mṛḍīka | apte-sanskrit-english, apte-sanskrit-english, monier-williams, +2 | ✅ | ✅ |
| `wisdom` | prajñā, jñāna, buddhi | 100 | worldly-wisdom, mkhyen pa, ye shes kyi pha rol tu phyin pa, sher, ye shes pa | mw-english-sanskrit, tib-rangjung-yeshe, tib-rangjung-yeshe, +2 | ❌ | ✅ |
| `mind` | manas, citta, cetas | 100 | tūṣṇīm, vyapekṣ, nitarām, tadānīm, viśvadānīm | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ❌ | ❌ |
| `buddha` | buddha, tathāgata, sambuddha | 100 | buddha, tāra, jina, gaya, kāla | apte-sanskrit-english, monier-williams, monier-williams, +2 | ✅ | ✅ |
| `love` | preman, rāga, kāma, sneha | 100 | śṛṃgārakaḥ, pratisnehaḥ, zuci, vena, māra | apte-sanskrit-english, apte-sanskrit-english, monier-williams, +2 | ✅ | ✅ |
| `death` | mṛtyu, marana, yama | 100 | viṣya, mṛtiḥ, maraḥ, haṃtuḥ, mṛtyuḥ | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ✅ | ✅ |
| `king` | rāja, nṛpa, narendra | 100 | rāyaḥ, kuṃtiḥ, mūleraḥ, malikaḥ, nahuṣaḥ | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ❌ | ❌ |
| `moon` | candra, soma, indu | 100 | soman, sumaḥ, papiḥ, tṛpat, snehuḥ | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ✅ | ✅ |
| `sun` | sūrya, āditya, savitṛ, ravi | 100 | śuṣṇaḥ, varṇuḥ, suvanaḥ, tapasaḥ, vivasvat | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ❌ | ❌ |

## Korean seed precision (top-5 strict / top-20 loose)

**Strict (top-5): 15/15** · **Loose (top-20): 15/15**

| Query | Expected | rev hits | Top-5 iast | Top-5 dicts | Strict | Loose |
|---|---|---:|---|---|---|---|
| `법` | dharma | 100 | dharma, dharma, dharma, dharma, dharma | monier-williams, monier-williams, monier-williams, +2 | ✅ | ✅ |
| `불` | agni, buddha | 100 | buddha, agni, buddha, buddha, buddha | apte-sanskrit-english, monier-williams, monier-williams, +2 | ✅ | ✅ |
| `물` | jala, ap | 100 | ap, vāri, jala, ap, ap | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ✅ | ✅ |
| `지혜` | prajñā, jñāna | 100 | prajñā, prajñā, jñāna, jñāna, buddhi | apte-sanskrit-english, apte-sanskrit-english, monier-williams, +2 | ✅ | ✅ |
| `자비` | karuṇā, maitrī | 96 | karuṇā, karuṇa, karuṇa, karuṇa, karuṇa | apte-sanskrit-english, apte-sanskrit-english, monier-williams, +2 | ✅ | ✅ |
| `마음` | manas, citta | 100 | hṛd, manas, cetas, citta, hṛd | apte-sanskrit-english, apte-sanskrit-english, apte-sanskrit-english, +2 | ✅ | ✅ |
| `공` | śūnyatā, kha | 100 | śūnya, kha, kha, kha, kha | apte-sanskrit-english, monier-williams, monier-williams, +2 | ✅ | ✅ |
| `도` | mārga, panthan | 100 | mārga, mārga, mārga, mārga, mārga | monier-williams, monier-williams, monier-williams, +2 | ✅ | ✅ |
| `신` | deva, īśvara | 100 | deva, īśvara, deva, deva, deva | apte-sanskrit-english, apte-sanskrit-english, monier-williams, +2 | ✅ | ✅ |
| `왕` | rāja, nṛpa | 100 | rāja, rāja, nṛpa, nṛpa, nṛpa | monier-williams, monier-williams, monier-williams, +2 | ✅ | ✅ |
| `인연` | nidāna, pratyaya | 86 | nidāna, nidāna, nidāna, nidāna, pratyaya | monier-williams, monier-williams, monier-williams, +2 | ✅ | ✅ |
| `지옥` | naraka, niraya | 98 | niraya, naraka, niraya, naraka, niraya | monier-williams, monier-williams, macdonell, +2 | ✅ | ✅ |
| `天` | deva, svarga | 100 | deva, deva, deva, deva, deva | apte-sanskrit-english, monier-williams, monier-williams, +2 | ✅ | ✅ |
| `地` | pṛthivī, bhūmi | 100 | pṛthivī, bhūmi, bhūmi, bhūmi, bhūmi | apte-sanskrit-english, monier-williams, monier-williams, +2 | ✅ | ✅ |
| `心` | citta, manas, hṛd | 18 | chitta, nyon yid, garbhaḥ, hṛdayam, jyeṣṭhā | apte-bilingual, tib-rangjung-yeshe, equiv-mahavyutpatti, +2 | ✅ | ✅ |

## Notes

- **Strict** = expected iast appears in top-5 of priority-sorted reverse_en/ko lookup (what UI shows by default).
- **Loose** = expected iast appears in top-20 (within reach if user expands).
- A high *loose* but low *strict* score means the *data* is correct but the *priority sort* is misranking.
- A low *loose* score means the reverse extraction itself missed the gloss — extraction tuning needed in `scripts/lib/reverse_tokens.py`.

## UX caveat (orthogonal to data correctness)

`src/routes/+page.svelte:359-371` currently renders reverse hits as raw entry_ids with a dict-slug button. Even when the underlying data is correct, the user cannot tell *which Sanskrit/Tibetan word* matched their English/Korean gloss without clicking through. This is a P0 UX issue tracked in Track C.
