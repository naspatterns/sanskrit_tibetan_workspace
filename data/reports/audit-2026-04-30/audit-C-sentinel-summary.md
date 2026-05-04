# audit-C-sentinel — 50 query 자동 평가

- **종합**: ✅ 24/50 · ⚠️ 9/50 · ❌ 17/50
- 평가 시점: 인덱스 — tier0 10,000 keys · reverse_en 317,878 · reverse_ko 20,958

## 카테고리별

| Category | ✅ | ⚠️ | ❌ | Total |
|---|---:|---:|---:|---:|
| bo-wylie | 5 | 0 | 0 | 5 |
| dead-zone | 2 | 0 | 0 | 2 |
| edge | 1 | 0 | 4 | 5 |
| en-reverse | 2 | 3 | 5 | 10 |
| ko-reverse | 0 | 1 | 4 | 5 |
| prefix | 0 | 5 | 0 | 5 |
| skt-core | 6 | 0 | 4 | 10 |
| typo | 3 | 0 | 0 | 3 |
| zh-reverse | 5 | 0 | 0 | 5 |

## Query별 결과

| # | Query | Cat | Ch | Expected | Top-5 | Verdict |
|---|---|---|---|---|---|---|
| 1 | `dharma` | skt-core | skt | dharma | dhārma | ✅ |
| 2 | `ātman` | skt-core | skt | ātman | ātman | ✅ |
| 3 | `karman` | skt-core | skt | karman | karman | ✅ |
| 4 | `agni` | skt-core | skt | agni | agni | ✅ |
| 5 | `prajñā` | skt-core | skt | prajñā | prajñā | ✅ |
| 6 | `śūnyatā` | skt-core | skt | śūnyatā | (none) | ❌ |
| 7 | `bodhicitta` | skt-core | skt | bodhicitta | (none) | ❌ |
| 8 | `tathāgata` | skt-core | skt | tathāgata | (none) | ❌ |
| 9 | `mokṣa` | skt-core | skt | mokṣa | mokṣa | ✅ |
| 10 | `saṃskāra` | skt-core | skt | saṃskāra | (none) | ❌ |
| 11 | `dha` | prefix | prefix | dharma \| dhātu \| dhana | dha \| dhâ ͜ ana \| dhā asi \| dha du ra \| dha man | ⚠️ |
| 12 | `bud` | prefix | prefix | buddha \| buddhi | buḍ \| bud bsnyegs thob gsum \| bud bud \| བུད་དྷ་ \| bud d+ha b | ⚠️ |
| 13 | `pra` | prefix | prefix | prajñā \| pratyaya | pra \| pra ͜ â-rambha \| pra ͜ adhi ͜ ita \| pra ͜ adhva [fore- | ⚠️ |
| 14 | `ana` | prefix | prefix | anātman \| anitya \| ānanda | anā \| ĀNA I \| ĀNA II \| aṇa(na)ka \| anaa | ⚠️ |
| 15 | `mahā` | prefix | prefix | mahābhārata \| mahāyāna \| mahāt | mahā \| mahâ ͜ aitareya \| mahâ ͜ ikkha \| mahâ ͜ indra \| mahâ  | ⚠️ |
| 16 | `chos` | bo-wylie | bo | chos | chos | ✅ |
| 17 | `byang chub sems dpa'` | bo-wylie | bo | byang chub sems dpa' \| bodhisa | byang chub sems dpa' | ✅ |
| 18 | `klong chen` | bo-wylie | bo | klong chen | klong chen | ✅ |
| 19 | `rdo rje` | bo-wylie | bo | rdo rje \| vajra | rdo rje | ✅ |
| 20 | `'jam dpal` | bo-wylie | bo | 'jam dpal \| mañjuśrī | 'jam dpal | ✅ |
| 21 | `fire` | en-reverse | en | agni | raḥ \| vami \| sāgni \| vāśiḥ \| peruḥ | ⚠️ |
| 22 | `wisdom` | en-reverse | en | prajñā \| jñāna \| buddhi | worldly-wisdom \| mkhyen pa \| ye shes kyi pha rol tu phyin pa | ❌ |
| 23 | `compassion` | en-reverse | en | karuṇā \| anukampā \| dayā | ghṛṇā \| karuṇā \| u \| dayā \| mṛḍīka | ✅ |
| 24 | `emptiness` | en-reverse | en | śūnyatā \| śūnya | śūna \| śūnyatā \| riktatā \| tucchya \| śūnyatā | ✅ |
| 25 | `liberation` | en-reverse | en | mokṣa \| mukti | vimokṣaḥ \| parimukti \| nirmokṣaḥ \| mocana \| mokṣaṇa | ⚠️ |
| 26 | `meditation` | en-reverse | en | dhyāna \| samādhi | yogas \| yogas \| nididhyāsana \| sa \| yaḥ | ⚠️ |
| 27 | `enlightenment` | en-reverse | en | bodhi \| sambodhi | lokaḥ \| kratuḥ \| enlightenment \| byang mchog \| byang lnga po | ❌ |
| 28 | `suffering` | en-reverse | en | duḥkha | vātakin \| udvegin \| vaisarpa \| udāvartin \| taapin | ❌ |
| 29 | `consciousness` | en-reverse | en | vijñāna \| citta | pramā \| saṃjñā \| pratisaṃkhyā \| vitti \| saṃvid | ❌ |
| 30 | `righteousness` | en-reverse | en | dharma | righteousness \| self-righteousness \| righteousness \| saudhar | ❌ |
| 31 | `법` | ko-reverse | ko | dharma | sudharma \| dharmavidyā \| dharmadhātu \| dharm \| dharmin | ⚠️ |
| 32 | `자비` | ko-reverse | ko | karuṇā \| maitrī | prasaadaḥ \| rtse \| snying rje tshad med \| byams \| thugs brts | ❌ |
| 33 | `지혜` | ko-reverse | ko | prajñā \| jñāna | paṇḍitiman \| śūlikā \| sukratūy \| manīṣitā \| vicakṣaṇatva | ❌ |
| 34 | `도` | ko-reverse | ko | mārga \| panthan | ay \| sad \| vac \| tarj \| garh | ❌ |
| 35 | `불` | ko-reverse | ko | agni \| buddha | raḥ \| vami \| homaḥ \| dīpta \| davaḥ | ❌ |
| 36 | `法` | zh-reverse | zh | dharma | _1966 dharma; vidhi; bhava \| 617290 anga; artha; akara; agam | ✅ |
| 37 | `空` | zh-reverse | zh | śūnyatā \| śūnya | śūnyatā \| antari-kṣa \| nabha \| vandhya \| ākāśa | ✅ |
| 38 | `菩薩` | zh-reverse | zh | bodhisattva | bodhisattva | ✅ |
| 39 | `涅槃` | zh-reverse | zh | nirvāṇa | nirvāṇa \| 涅槃 \| nirvāṇa; nirvṛti; parinirvṛtaḥ; nirvāṇa-(bhūm | ✅ |
| 40 | `如來` | zh-reverse | zh | tathāgata | tathāgataḥ \| tathāgata | ✅ |
| 41 | `mahābhārata` | edge | skt | mahābhārata | (none) | ❌ |
| 42 | `jagannātha` | edge | skt | jagannātha | (none) | ❌ |
| 43 | `tat tvam asi` | edge | skt | (none) | (none) | ❌ |
| 44 | `oṃ` | edge | skt | oṃ \| om | om | ✅ |
| 45 | `aham brahmāsmi` | edge | skt | (none) | (none) | ❌ |
| 46 | `dharmaaa` | typo | edge | (none) | (none) | ✅ |
| 47 | `aaa` | typo | edge | (none) | (none) | ✅ |
| 48 | `   ` | typo | edge | (none) | (none) | ✅ |
| 49 | `decl-a01` | dead-zone | edge | (none) | (none) | ✅ |
| 50 | `aṃśanīya@aṃś` | dead-zone | edge | (none) | (none) | ✅ |
