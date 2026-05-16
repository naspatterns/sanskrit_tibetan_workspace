# audit-C-sentinel — 50 query 자동 평가

- **종합**: ✅ 50/50 · ⚠️ 0/50 · ❌ 0/50
- 평가 시점: 인덱스 — tier0 10,000 keys · reverse_en 317,884 · reverse_ko 20,962

## 카테고리별

| Category | ✅ | ⚠️ | ❌ | Total |
|---|---:|---:|---:|---:|
| bo-wylie | 5 | 0 | 0 | 5 |
| dead-zone | 2 | 0 | 0 | 2 |
| edge | 5 | 0 | 0 | 5 |
| en-reverse | 10 | 0 | 0 | 10 |
| ko-reverse | 5 | 0 | 0 | 5 |
| prefix | 5 | 0 | 0 | 5 |
| skt-core | 10 | 0 | 0 | 10 |
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
| 6 | `śūnyatā` | skt-core | skt | śūnyatā | śūnyatā | ✅ |
| 7 | `bodhicitta` | skt-core | skt | bodhicitta | bodhicitta | ✅ |
| 8 | `tathāgata` | skt-core | skt | tathāgata | tathāgata | ✅ |
| 9 | `mokṣa` | skt-core | skt | mokṣa | mokṣa | ✅ |
| 10 | `saṃskāra` | skt-core | skt | saṃskāra | saṃskāra | ✅ |
| 11 | `dha` | prefix | prefix | dharma \| dhātu \| dhana | dharaṇa \| dhārma \| dharmakāya \| dhara \| dharmaḥ | ✅ |
| 12 | `bud` | prefix | prefix | buddha \| buddhi | buddha \| budha \| budh \| buḍ \| buddhi | ✅ |
| 13 | `pra` | prefix | prefix | prajñā \| pratyaya | prajñā \| pratyaya \| praṇa \| prakṛti \| prajāpati | ✅ |
| 14 | `ana` | prefix | prefix | anātman \| anitya \| ānanda | ananda \| anātman \| anāhata \| āṇatta \| anāgāmī | ✅ |
| 15 | `mahā` | prefix | prefix | mahābhārata \| mahāyāna \| mahāt | mahā \| mahāsattva \| mahāyāna \| mahābhārata \| mahāvākya | ✅ |
| 16 | `chos` | bo-wylie | bo | chos | chos | ✅ |
| 17 | `byang chub sems dpa'` | bo-wylie | bo | byang chub sems dpa' \| bodhisa | byang chub sems dpa' | ✅ |
| 18 | `klong chen` | bo-wylie | bo | klong chen | klong chen | ✅ |
| 19 | `rdo rje` | bo-wylie | bo | rdo rje \| vajra | rdo rje | ✅ |
| 20 | `'jam dpal` | bo-wylie | bo | 'jam dpal \| mañjuśrī | 'jam dpal | ✅ |
| 21 | `fire` | en-reverse | en | agni | pāvaka \| agni \| vahni \| vahni \| anala | ✅ |
| 22 | `wisdom` | en-reverse | en | prajñā \| jñāna \| buddhi | vidyā \| prajñā \| prajñā \| vidyā \| jñāna | ✅ |
| 23 | `compassion` | en-reverse | en | karuṇā \| anukampā \| dayā | karuṇā \| karuṇā \| karuṇā \| karuṇā \| karuṇā | ✅ |
| 24 | `emptiness` | en-reverse | en | śūnyatā \| śūnya | śūnyatā \| śūnyatā \| śūnyatā \| śūnyatā \| śūnyatā | ✅ |
| 25 | `liberation` | en-reverse | en | mokṣa \| mukti | mokṣa \| mokṣa \| mukti \| mokṣa \| mukti | ✅ |
| 26 | `meditation` | en-reverse | en | dhyāna \| samādhi | dhyāna \| dhyāna \| dhyāna \| samādhi \| samādhi | ✅ |
| 27 | `enlightenment` | en-reverse | en | bodhi \| sambodhi | bodhi \| bodhi \| bodhi \| bodhi \| bodhi | ✅ |
| 28 | `suffering` | en-reverse | en | duḥkha | duḥkha \| duḥkha \| duḥkha \| duḥkha \| duḥkha | ✅ |
| 29 | `consciousness` | en-reverse | en | vijñāna \| citta | cetas \| citta \| saṃjñā \| saṃjñā \| cetas | ✅ |
| 30 | `righteousness` | en-reverse | en | dharma | dharma \| dharma \| dharma \| dharma \| dharma | ✅ |
| 31 | `법` | ko-reverse | ko | dharma | dharma \| dharma \| dharma \| dharma \| dharma | ✅ |
| 32 | `자비` | ko-reverse | ko | karuṇā \| maitrī | karuṇā \| karuṇa \| karuṇa \| karuṇa \| karuṇa | ✅ |
| 33 | `지혜` | ko-reverse | ko | prajñā \| jñāna | prajñā \| prajñā \| jñāna \| jñāna \| buddhi | ✅ |
| 34 | `도` | ko-reverse | ko | mārga \| panthan | mārga \| mārga \| mārga \| mārga \| mārga | ✅ |
| 35 | `불` | ko-reverse | ko | agni \| buddha | buddha \| agni \| buddha \| buddha \| buddha | ✅ |
| 36 | `法` | zh-reverse | zh | dharma | _1966 dharma; vidhi; bhava \| 617290 anga; artha; akara; agam | ✅ |
| 37 | `空` | zh-reverse | zh | śūnyatā \| śūnya | śūnyatā \| antari-kṣa \| nabha \| vandhya \| ākāśa | ✅ |
| 38 | `菩薩` | zh-reverse | zh | bodhisattva | bodhisattva | ✅ |
| 39 | `涅槃` | zh-reverse | zh | nirvāṇa | nirvāṇa \| nirvṛti \| MYA NGAN LAS 'DA' BA \| MYA NGAN LAS 'DAS | ✅ |
| 40 | `如來` | zh-reverse | zh | tathāgata | tathāgataḥ \| tathāgata | ✅ |
| 41 | `mahābhārata` | edge | skt | mahābhārata | mahābhārata | ✅ |
| 42 | `jagannātha` | edge | skt | jagannātha | jagannātha | ✅ |
| 43 | `tat tvam asi` | edge | skt | tat \| tvam \| asi | taṭ \| tvaṃ \| asī | ✅ |
| 44 | `oṃ` | edge | skt | oṃ \| om | om | ✅ |
| 45 | `aham brahmāsmi` | edge | skt | aham \| brahman \| asmi | aham | ✅ |
| 46 | `dharmaaa` | typo | edge | (none) | (none) | ✅ |
| 47 | `aaa` | typo | edge | (none) | (none) | ✅ |
| 48 | `   ` | typo | edge | (none) | (none) | ✅ |
| 49 | `decl-a01` | dead-zone | edge | (none) | (none) | ✅ |
| 50 | `aṃśanīya@aṃś` | dead-zone | edge | (none) | (none) | ✅ |
