# audit-C-sentinel200 — 200 query 자동 평가 (Phase 3.7 Option C)

- **종합**: ✅ 191/200 (95.5%) · ⚠️ 2/200 · ❌ 7/200
- 인덱스: tier0 10,000 keys · tier0-ext 10,000 · reverse_en 317,884 · reverse_ko 20,962

## 카테고리별

| Category | ✅ | ⚠️ | ❌ | Total | ✅% |
|---|---:|---:|---:|---:|---:|
| bo-wylie | 15 | 0 | 0 | 15 | 100% |
| dead-zone | 2 | 0 | 0 | 2 | 100% |
| edge | 21 | 0 | 2 | 23 | 91% |
| en-reverse | 40 | 0 | 0 | 40 | 100% |
| ko-reverse | 15 | 0 | 0 | 15 | 100% |
| prefix | 12 | 0 | 3 | 15 | 80% |
| skt-core | 10 | 0 | 0 | 10 | 100% |
| skt-long | 27 | 0 | 2 | 29 | 93% |
| skt-mid | 31 | 0 | 0 | 31 | 100% |
| typo | 4 | 1 | 0 | 5 | 80% |
| zh-reverse | 14 | 1 | 0 | 15 | 93% |

## ❌ 실패 query

| # | Query | Cat | Ch | Expected | Top-5 |
|---|---|---|---|---|---|
| 146 | `śā` | prefix | prefix | śānti \| śāstra \| śākyamuni | śaṭ \| satya \| samāna \| sādhana \| saṃkhyā |
| 149 | `sam` | prefix | prefix | saṃskāra \| samādhi | samāna \| saṃkhyā \| saṃjñā \| samudaya \| saṃyāma |
| 155 | `ut` | prefix | prefix | utpāda | uttara \| uta \| uttama \| utkatā \| utpala |
| 187 | `नमस्ते` | edge | skt | (none) | (none) |
| 188 | `汉字` | edge | skt | (none) | (none) |
| 194 | `vajracchedikā` | skt-long | skt | vajracchedikā | (none) |
| 200 | `śūraṅgama` | skt-long | skt | śūraṅgama | (none) |

## ⚠️ 부분 매치

| # | Query | Cat | Ch | Expected | Top-5 |
|---|---|---|---|---|---|
| 128 | `心` | zh-reverse | zh | citta \| manas \| hṛd | jyeṣṭhā \| hṛdayam \| (5) Blatt 61; VERFRERX nigraha-Sila; PER |
| 189 | `??` | typo | edge | (none) | ???????? |
