# audit-C-sentinel200 — 200 query 자동 평가 (Phase 3.7 Option C)

- **종합**: ✅ 202/215 (94.0%) · ⚠️ 6/215 · ❌ 7/215
- 인덱스: tier0 10,000 keys · tier0-ext 10,000 · reverse_en 317,884 · reverse_ko 20,962

## 카테고리별

| Category | ✅ | ⚠️ | ❌ | Total | ✅% |
|---|---:|---:|---:|---:|---:|
| bo-wylie | 15 | 0 | 0 | 15 | 100% |
| dead-zone | 2 | 0 | 0 | 2 | 100% |
| edge | 21 | 0 | 2 | 23 | 91% |
| en-reverse | 40 | 0 | 0 | 40 | 100% |
| ko-reverse | 15 | 0 | 0 | 15 | 100% |
| prefix | 12 | 1 | 2 | 15 | 80% |
| skt-core | 10 | 0 | 0 | 10 | 100% |
| skt-long | 27 | 0 | 2 | 29 | 93% |
| skt-mid | 31 | 0 | 0 | 31 | 100% |
| typo | 4 | 1 | 0 | 5 | 80% |
| upasarga-prefix | 11 | 3 | 1 | 15 | 73% |
| zh-reverse | 14 | 1 | 0 | 15 | 93% |

## ❌ 실패 query

| # | Query | Cat | Ch | Expected | Top-5 |
|---|---|---|---|---|---|
| 146 | `śā` | prefix | prefix | śānti \| śāstra \| śākyamuni | śaṭ \| satya \| samāna \| sādhana \| saṃkhyā |
| 155 | `ut` | prefix | prefix | utpāda | uttara \| uta \| uttama \| utkatā \| utpala |
| 187 | `नमस्ते` | edge | skt | (none) | (none) |
| 188 | `汉字` | edge | skt | (none) | (none) |
| 194 | `vajracchedikā` | skt-long | skt | vajracchedikā | (none) |
| 200 | `śūraṅgama` | skt-long | skt | śūraṅgama | (none) |
| 206 | `anu` | upasarga-prefix | prefix | anukampā \| anumāna | anupa \| anuja \| anupūrva \| anudara \| anukta |

## ⚠️ 부분 매치

| # | Query | Cat | Ch | Expected | Top-5 |
|---|---|---|---|---|---|
| 128 | `心` | zh-reverse | zh | citta \| manas \| hṛd | jyeṣṭhā \| hṛdayam \| (5) Blatt 61; VERFRERX nigraha-Sila; PER |
| 153 | `su` | prefix | prefix | sukha \| sūtra \| sūrya | suṣumṇa \| suvarṇaprabhāsa \| sukhavatī \| sundaraṃ \| suta |
| 189 | `??` | typo | edge | (none) | ???????? |
| 210 | `su` | upasarga-prefix | prefix | sukha \| subhūti | suṣumṇa \| suvarṇaprabhāsa \| sukhavatī \| sundaraṃ \| suta |
| 211 | `rab tu` | upasarga-prefix | prefix | rab tu byung \| rab tu dga' \| r | rab tu dga' ba \| rab tu za \| rab tu bya \| rab tu bye \| rab t |
| 215 | `nye bar` | upasarga-prefix | prefix | nye bar | nye bar zhi ba \| nye bar len pa \| nye bar ded \| nye bar gos  |
