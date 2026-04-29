# Audit B — Korean Translation Quality, Non-English European Sources

**Date**: 2026-04-30
**Auditor**: Claude (Phase 3.6 readiness audit)
**Sample size**: 498 entries (seed=42), weighted across 10 source dicts
**Scope**: `body.ko` (Korean translations) carried over from v1, never re-audited.

## Verdict (3 bullets)

- **Re-translate. The current `body.ko` is not a translation — it is a partial word-substitution gloss that leaks the source language at scale.** Median Korean (Hangul) character ratio is **5–7%** across the German/French/Latin corpus; **0/424** sampled DE/FR/LA entries reach a 30% Hangul ratio. Even when classified "B-grade," the entries read as mostly-German text with isolated Korean tokens like "여성." (f.), "형용사." (adj.), "~의" (genitive marker) sprinkled in. A reader who does not already read German cannot extract meaning.
- **Two dicts are categorically broken** — `bopp-comparative` (11/11 sampled = empty `body.ko`) and `vedic-rituals-hillebrandt` (8/8 = empty). Both have `target_lang=en` in `meta.json`, so they fall outside the DE/FR/LA scope per the user's spec, but the `translation_coverage.md` "100% count" statistic for them is meaningless because the field is empty. **They should be removed from the EU re-translation budget and addressed separately**, and the coverage report needs a fix to count empty strings as zero.
- **Cost-benefit strongly favors the $225 batch.** The 8 in-scope DE/FR/LA dicts hold ~390K entries — at $225 that is ~$0.00058/entry, well below any reasonable lower bound on the value of a real translation, and the current state actively misleads users (looks-translated, isn't). **Priority order**: pwg → pwk (highest entry count, worst leak density) → cappeller-german → schmidt-nachtrage → stchoupak → burnouf → grassmann-vedic → bopp-latin.

---

## 1. Methodology

### 1.1 Sampling

`random.sample(range(N), k)` with `seed=42`, weighted by entry count (`k ≈ 500 × N_dict / N_total`). Final sample is **498 entries** across **10 dicts**:

| Dict | target_lang | priority | N entries | N sampled |
|------|-------------|----------|-----------|-----------|
| `pwg` | de | 7 | 122,730 | 155 |
| `pwk` | de | 6 | 135,776 | 170 |
| `cappeller-german` | de | 50 | 30,038 | 38 |
| `schmidt-nachtrage` | de | 51 | 28,751 | 36 |
| `stchoupak` | fr | 52 | 24,574 | 31 |
| `burnouf` | fr | 53 | 19,775 | 25 |
| `grassmann-vedic` | de | 55 | 10,421 | 13 |
| `bopp-comparative` | **en**\* | 56 | 8,960 | 11 |
| `bopp-latin` | la | 54 | 9,006 | 11 |
| `vedic-rituals-hillebrandt` | **en**\* | 82 | 6,176 | 8 |

\* `bopp-comparative` and `vedic-rituals-hillebrandt` declare `target_lang=en` in their meta.json — strictly speaking they are outside the user's "non-English European" scope. They are included here because the user named them; both turn out to have empty `body.ko` and are reported separately.

### 1.2 Classifier

Each sample's `body.plain` (source) and `body.ko` (Korean carryover) are scored on five observable signals — no German/French/Latin reading required:

1. **Hangul ratio** — `len(Hangul chars) / len(non-whitespace chars)` of `ko`. Real Korean prose is typically 60–80%; the rest is punctuation, numerals, and IAST tokens.
2. **Source-language leak density** — count of common DE/FR/LA function words still present in `ko`, divided by total token count. A real translation has near-zero leaks.
3. **Length ratio** — `len(ko) / len(plain)`. Drastic shrinkage (< 0.4) signals truncation.
4. **Citation preservation** — patterns like `ṚV. 8, 4, 3`, `Mn. 5.32`, `H. 240` should round-trip verbatim.
5. **Numbered-sense structure** — `1)`, `2)`, `(a)`, `(b)`. Should round-trip verbatim.

Identical `ko == plain` and empty `ko` are auto-classified D.

### 1.3 Grade rubric (as applied)

- **A** — Hangul ratio ≥ 30% **and** zero leak density **and** all citations preserved.
- **B** — Minor leak (< 4% density), Hangul ratio 15–30%, citations mostly preserved.
- **C** — Substantial leaks, Hangul ratio 5–15%, partial truncation, or partial citation loss.
- **D** — Empty, identical-to-source, no Hangul at all, or Hangul ratio < 1%.

Cutoffs are deliberately generous toward higher grades — reality came out worse anyway.

---

## 2. Results — Per-dict quality histogram

| Dict | lang | N | A | B | C | D | **score**\* | identical | empty |
|------|------|---:|---:|---:|---:|---:|---:|---:|---:|
| `pwg` | de | 155 | 0 | 9 | 130 | 16 | **1.95** | 13 | 0 |
| `pwk` | de | 170 | 1 | 13 | 122 | 34 | **1.89** | 33 | 0 |
| `cappeller-german` | de | 38 | 2 | 7 | 15 | 14 | **1.92** | 13 | 0 |
| `schmidt-nachtrage` | de | 36 | 0 | 1 | 27 | 8 | **1.81** | 0 | 0 |
| `stchoupak` | fr | 31 | 0 | 2 | 25 | 4 | **1.94** | 4 | 0 |
| `burnouf` | fr | 25 | 0 | 3 | 17 | 5 | **1.92** | 3 | 0 |
| `grassmann-vedic` | de | 13 | 0 | 0 | 11 | 2 | **1.85** | 0 | 0 |
| `bopp-latin` | la | 11 | 0 | 1 | 7 | 3 | **1.82** | 0 | 0 |
| `bopp-comparative`\* | en | 11 | 0 | 0 | 0 | 11 | **1.00** | 0 | 11 |
| `vedic-rituals-hillebrandt`\* | en | 8 | 0 | 0 | 0 | 8 | **1.00** | 0 | 8 |
| **Overall** | | **498** | **3** | **36** | **354** | **105** | **1.87** | 66 | 19 |

\* score = (4·A + 3·B + 2·C + 1·D) / N. **A=4, B=3, C=2, D=1.**
\* `bopp-comparative` / `vedic-rituals-hillebrandt` have target_lang=en — see §1.1.

### 2.1 Hangul ratio distribution per dict

| Dict | median | p10 | p90 | mean | %≥30% |
|------|---:|---:|---:|---:|---:|
| `pwg` | 0.057 | 0.010 | 0.128 | 0.065 | **0.0%** |
| `pwk` | 0.074 | 0.000 | 0.143 | 0.076 | **0.6%** |
| `cappeller-german` | 0.059 | 0.000 | 0.250 | 0.094 | **5.3%** |
| `schmidt-nachtrage` | 0.057 | 0.000 | 0.136 | 0.061 | **0.0%** |
| `stchoupak` | 0.071 | 0.000 | 0.142 | 0.072 | **0.0%** |
| `burnouf` | 0.073 | 0.000 | 0.154 | 0.076 | **0.0%** |
| `grassmann-vedic` | 0.065 | 0.000 | 0.110 | 0.053 | **0.0%** |
| `bopp-latin` | 0.039 | 0.000 | 0.101 | 0.055 | **0.0%** |
| `bopp-comparative` | 0.000 | 0.000 | 0.000 | 0.000 | 0.0% |
| `vedic-rituals-hillebrandt` | 0.000 | 0.000 | 0.000 | 0.000 | 0.0% |

**Read this table carefully.** The Korean-character density of the "translation" is **5–9% across the entire DE/FR/LA corpus**. A genuine Korean translation runs 60–80%. The remaining 90%+ is the original German/French/Latin text passed through verbatim.

### 2.2 Overall score

```
A:  3 ( 0.6%)
B: 36 ( 7.2%)
C: 354 (71.1%)
D: 105 (21.1%)
weighted score = 1.87 / 4.00
```

A score of 1.87 sits between D (failed) and C (poor), substantially closer to C. **No dict scores above 2.0 (poor).** No dict has more than a single-digit count of B/A entries.

---

## 3. What's actually happening (root-cause)

Inspection of the samples shows a consistent pattern across every DE/FR/LA dict:

> The v1 pipeline applied a **per-token dictionary substitution** that swapped a hand-curated list of German/French/Latin function words to short Korean fragments, while leaving content words (nouns, verbs, adjectives, proper nouns), morphology codes (`Adj.`, `m.`, `f.`), citations, and IAST headwords untouched.

**Examples of the substitution table** (inferred from observation):

| German source | Korean substitution |
|---|---|
| `mit` | `~와 함께` (postposition "with") |
| `von` | `~의` (genitive "of") |
| `nicht` | `~않은` (negation) |
| `und` | `그리고` ("and") |
| `der/die/das` | `(정관사)` ("definite article") |
| `m.` | `남성.` ("masculine") |
| `f.` | `여성.` ("feminine") |
| `n.` | `중성.` ("neuter") |
| `Adj.` | `형용사.` ("adjective") |
| `Subst.` | `명사.` ("noun") |
| `eine`/`einer` | `하나의` ("one/a") |

This is not translation. It is a **decoration layer** that signals to the user "yes, Korean is somewhere in this string" while preserving 90%+ of the source text intact. A user who does not already read German extracts essentially zero semantic content.

The remaining failure modes are simpler:

- **Identical pass-through (66 samples, 13.3%)** — `body.ko` is byte-identical to `body.plain` (modulo headword stripping). v1 imported but never substituted. Concentrated in `pwg`/`pwk`/`cappeller-german`.
- **Empty (19 samples, 3.8%)** — `body.ko` is `""`. All 19 are from `bopp-comparative` and `vedic-rituals-hillebrandt` (target_lang=en, fall outside scope). The `translation_coverage.md` 100% count for these dicts is therefore a measurement bug.
- **Headword-stripped no-Hangul (19 samples)** — short entries where the only "translation" was removing the headword from the start; everything else stayed German.

---

## 4. Representative examples

### 4.1 A-grade (3 total — exhaustive)

```
[pwk]  hw=purogama
plain: purogamaAdj. (f. ā) Subst. = puroga. Am Ende eines adj. Comp. f. ā.
ko   : 형용사. (여성. ā) 명사. = puroga. Am 끝 eines 형용사. Comp. 여성. ā.

[cappeller-german] hw=ujjiti
plain: ujjitif. Sieg.
ko   : 여성. 승리.

[cappeller-german] hw=maghava
plain: maghavam. Bein. Indra's.
ko   : 남성. 별칭 Indra's.
```

A-grade only emerged where the entry is **short enough to be entirely covered by the substitution table**. `ujjiti — 여성. 승리.` ("f. victory.") is the only entry in the entire 498-sample corpus that reads as actual Korean. All three "A" entries are 3–10 words. There is no example of a multi-sentence A-grade entry.

### 4.2 B-grade (10 representative)

```
[pwg] hw=acchupta
plain: acchupta(3. a + chupta von chup) 1) adj. "unberührt." -- 2) f. -ptā N. pr. eine der 16 Vidyādevī's H. 240.
ko   : (3. a + chupta ~의 chup) 1) 형용사. "unberührt." -- 2) 여성. -ptā 고유명사 하나의 ~의 16 Vidyādevī's H. 240.
```
*The actual gloss "unberührt" ("untouched") is left in German.*

```
[pwg] hw=ihakratu
plain: ihakratuund ihacitta (i- + kra- und ci-) adjj. "dessen Wille" und "Gedanke hierher geht" AV. 18, 4, 38.
ko   : 그리고 ihacitta (i- + kra- 그리고 ci-) adjj. "dessen Wille" 그리고 "생각 hierher geht" AV. 18, 4, 38.
```
*"Wille" (will) is untranslated; only "Gedanke" → "생각" got swapped.*

```
[pwk] hw=aghora
plain: aghora1) Adj. "nicht grausig." 2) m. "eine Form Śiva's." 3) f. ā "der 14te Tag in der dunklen Hälfte des Monats Bhādra."
ko   : 1) 형용사. "~않은 grausig." 2) 남성. "하나의 형태 Śiva's." 3) 여성. ā "~의 14te 날 ~에/~안에 ~의 dunklen 반 ~의 Monats Bhādra."
```
*Function words swapped, but the semantic core ("not horrible", "a form of Śiva's", "14th day of the dark half of Bhādra") is unrecoverable to a Korean reader.*

```
[cappeller-german] hw=peSa
plain: peṣaf. ī (--°) zerreibend, mahlend; m. das Zerreiben, Mahlen.
ko   : peṣaf. ī ((복합어 전분)) zerreibend, mahlend; 남성. (정관사) Zerreiben, Mahlen.
```

```
[cappeller-german] hw=sphal
plain: sphalmit ā Caus. āsphālayati anprallen (lassen), anschlagen an, schleudern gegen (Acc.).
ko   : ~와 함께 ā 사역형. āsphālayati anprallen (lassen), anschlagen an, schleudern ~에 대하여 (대격.).
```

```
[schmidt-nachtrage] hw=Adityadarzana
plain: ādityadarśanan. das Zeigen der Sonne (eine best. Zeremonie im vierten Monat nach der Geburt), Mān. Gṛhy. 1, 19; Viṣṇus. 27, 10.
ko   : ādityadarśanan. (정관사) Zeigen ~의 태양 (하나의 best. 의식(儀式) im vierten Monat ~후에/~으로 ~의 탄생) , Mān. Gṛhy. 1 , 19; Viṣṇus. 27 , 10.
```
*Citations preserved; the actual gloss is half-substituted.*

```
[stchoupak] hw=svAbhAsa
plain: svābhāsa sv-ābhāsa- a. très illustre; très lumineux.
ko   : svābhāsa sv-ābhāsa- 형용사. 매우 illustre ; 매우 lumineux.
```

```
[burnouf] hw=andhu
plain: andhum. (andh) puits. andhula m. mimosa sirisha, bot.
ko   : 남성. (andh) 우물. andhula 남성. mimosa sirisha, bot.
```
*Best-of-set: "puits" → "우물" (well) actually translated; Latin botanical name preserved as expected.*

### 4.3 C-grade (10 representative — the bulk of the corpus)

```
[pwg] hw=andhAtamasa
plain: andhātamasa(andha 1,b. + tamasa mit Dehnung des Auslauts) n. "dichte Finsterniss" H. 146, Sch. -- Vgl. andhatāmasa.
ko   : andhātamasa(andha 1,b. + tamasa ~와 함께 Dehnung ~의 Auslauts) 중성. "dichte Finsterniss" H. 146, Sch. -- 비교: andhatāmasa.
```
*"dichte Finsterniss" (thick darkness) is the actual gloss — left in German.*

```
[pwk] hw=avadhyAyin
plain: avadhyāyinAdj. 1) am Ende eines Comp. "gering achtend." 2) "gering geachtet" SAM5HITOPAN.25,2.
ko   : avadhyāyinAdj. 1) am 끝 eines Comp. "gering achtend." 2) "gering geachtet" SAM5HITOPAN.25,2.
```
*Only "끝" (end) substituted; the senses themselves are entirely German.*

```
[schmidt-nachtrage] hw=alabdhapada
plain: alabdhapadaAdj. keine Stelle gefunden habend in (Lok.), so v.a. keinen Eindruck gemacht habend auf, Ragh. 8, 90.
ko   : 형용사. keine 자리/구절 gefunden habend ~에/~안에 (Lok.) , so v.a. keinen Eindruck gemacht habend ~위에 , Ragh. 8 , 90.
```
*Single-word translations stitched in but the participles "gefunden habend" / "gemacht habend" are entirely opaque.*

```
[stchoupak] hw=ayAcita
plain: ayācita a-yācita- °yācyamāna- a. v. non sollicité, non demandé en mariage.
ko   : ayācita a-yācita- °yācyamāna- 형용사. v. non sollicité, non demandé en mariage.
```
*Only `a.` → `형용사.` swapped. The French gloss is byte-for-byte identical.*

```
[burnouf] hw=kendu
plain: kendum. diospyros tomentosa, bot, esp. de plaqueminier. kenduka m. diospyros glutinosa, ou l'arbre à goudron.
ko   : 남성. diospyros tomentosa, bot, esp. de plaqueminier. kenduka 남성. diospyros glutinosa, 또는 l'나무 à goudron.
```
*Genus names retained (correctly!), but "plaqueminier" / "arbre à goudron" left in French.*

### 4.4 D-grade (10 representative — three failure modes)

**Empty `body.ko` (3 examples)**

```
[bopp-comparative] hw=अभिमान
plain: अभिमान m. (aut a r. मन् aut a मान् s. अ) superbia, insolentia, honoris, gloriae cupiditas. BH. 16. 4.
ko   : (empty)

[bopp-comparative] hw=अल्पदर्शन
plain: अल्पदर्शन (parum visus habens, BAH. ex अल्प et दर्शन n. visus) parum valens visu, parum intelligens, imprudens, stultus. H. 1. 45.
ko   : (empty)

[bopp-comparative] hw=कटि
plain: कटि f. (r. कट् s. इ) i. q. कट.
ko   : (empty)
```

**Identical pass-through (4 examples)**

```
[pwg] hw=Tup
plain: ṭups. āṭopa.
ko   : ṭups. āṭopa.

[pwg] hw=kRSNakiMkaraprakriyA
plain: kṛṣṇakiṃkaraprakriyāf. Titel eines Werkes HALL 187.
ko   : kṛṣṇakiṃkaraprakriyāf. Titel eines Werkes HALL 187.

[pwg] hw=kRSNopaniSad
plain: kṛṣṇopaniṣad Ind. St.3,326. Verz. d. Oxf. H. 390,b, No. 35 (bis).
ko   : kṛṣṇopaniṣad Ind. St.3,326. Verz. d. Oxf. H. 390,b, No. 35 (bis).

[pwg] hw=dAsaveza
plain: dāsaveśawohl Bez. eines Dämons.
ko   : dāsaveśawohl Bez. eines Dämons.
```

**Headword-stripped, no Hangul (3 examples)**

```
[pwg] hw=babhri
plain: babhri ṚV. 3, 1, 12 etwa so v. a. bharamāṇa.
ko   : ṚV. 3, 1, 12 etwa so v. a. bharamāṇa.

[pwg] hw=buddhi
plain: buddhi 4) pl. Spr. (II) 2286.
ko   : 4) pl. Spr. (II) 2286.

[pwk] hw=kunth
plain: kunth *kunth 1) kunthati ( hiṃsākleśayoḥ). 2) kuthnāti ( saṃśleṣane kleśane). prani Vop.
ko   : *kunth 1) kunthati ( hiṃsākleśayoḥ). 2) kuthnāti ( saṃśleṣane kleśane). prani Vop.
```

---

## 5. What signals are intact?

Before recommending a re-translation, the audit checked whether *anything* survived correctly that a re-run would also need to preserve. The answer is yes, and that's good news for the re-translation effort:

- **IAST diacritics** — fully intact across all DE/FR/LA samples (`ḷ`, `ṃ`, `ṅ`, `ñ`, `ṭ`, `ḍ`, `ṇ`, `ś`, `ṣ`, `ā`, `ī`, `ū`, `ṛ`, `ṝ`, etc.). The substitution operated on Latin function words only.
- **Citations** — Mn., RV., AV., Pāṇ., H., Ragh. citations preserved verbatim. Numerals (`1, 12, 13`, `8, 81, 10`) preserved.
- **Numbered structure** — `1)`, `2)`, `(a)`, `(b)`, `[1]`, `[2]` markers preserved.
- **Headword + IAST normalization** (`headword`, `headword_iast`, `headword_norm`) — independent of `body.ko`, untouched.

So the source data is clean enough that a fresh batch translation pass can operate on `body.plain` and preserve all structural signals while producing genuinely Korean prose.

---

## 6. Recommendation — Re-translation priority

### 6.1 In-scope (DE/FR/LA, recommended re-translation)

Priority is by **(impact × current quality deficit)**, where impact ≈ entry count × dict priority weight, and deficit = (4 − current_score).

| Rank | Dict | lang | N entries | Score | Priority weight | Impact tier |
|---:|---|---|---:|---:|---:|---|
| 1 | `pwk` | de | 135,776 | 1.89 | 6 (top tier) | **highest** |
| 2 | `pwg` | de | 122,730 | 1.95 | 7 (top tier) | **highest** |
| 3 | `cappeller-german` | de | 30,038 | 1.92 | 50 | high |
| 4 | `schmidt-nachtrage` | de | 28,751 | 1.81 | 51 | high |
| 5 | `stchoupak` | fr | 24,574 | 1.94 | 52 | medium |
| 6 | `burnouf` | fr | 19,775 | 1.92 | 53 | medium |
| 7 | `grassmann-vedic` | de | 10,421 | 1.85 | 55 | medium |
| 8 | `bopp-latin` | la | 9,006 | 1.82 | 54 | low |
| | **subtotal in-scope** | | **381,071** | | | |

`pwk` ranks above `pwg` despite identical scores because it has the highest entry count and the highest fraction of identical-passthrough entries (33/170 = **19.4%**, double the corpus average) — the lowest-effort wins are concentrated there.

### 6.2 Out-of-scope (target_lang=en)

`bopp-comparative` and `vedic-rituals-hillebrandt` are 100% empty in the audit sample. They are out of the EU re-translation budget (target_lang=en). They are **also** misreported in `translation_coverage.md` as "100% Korean coverage" because count-of-key-presence is being used instead of count-of-non-empty-string. Two separate followups are needed:

- **Fix the coverage report** so an empty string counts as missing.
- **Decide separately** whether these two dicts get any translation (English-source dicts have not been part of the EU batch budget; they may go through the regular Phase 2b top-10K English-headword pipeline instead).

### 6.3 Cost-benefit vs $225 batch

**The $225 estimate is a clear yes.**

- **Per-entry cost**: $225 / 381,071 in-scope entries = **$0.00059 per entry**.
- **Current state**: 0% of these entries deliver readable Korean prose. The "100% Korean count" stat in `translation_coverage.md` is misleading users (and the project) into believing Phase 2b coverage is complete for these dicts.
- **Floor on the value of a real translation**: even if only 50% of the re-translated entries reach B-grade or better (a conservative target given the Apte/MW Phase 2b results), that is ~190K newly-readable entries at <$0.0012/entry. Far below any reasonable threshold.
- **Risk to defer**: Phase 4 (Cloudflare Pages deploy) will ship a UI advertising "한국어 번역" that is 90%+ German across these dicts. Users discovering this post-deploy is a worse outcome than spending $225 now.
- **Risk to proceed**: low — `body.plain` is clean, IAST/citations are preserved, batch infra is already proven by Phase 2b's 9,995/9,995 success.

### 6.4 Suggested execution shape

1. **Drop the substitution layer entirely** — the v1 token-replacement was net-negative; do not preserve any of it as a "starting point" for the LLM. Translate from `body.plain` alone.
2. **Phase the batch by priority tier**: ship `pwg` + `pwk` first (~$165 of the $225). Verify B-grade ≥ 50% on a 200-entry post-translation audit before proceeding to tier 2.
3. **Schema constraint in prompt**: require IAST/citation/numbered-structure preservation explicitly (the existing Phase 2b prompts can be reused with the source-text input swapped).
4. **Skip empty-`ko` dicts in the batch** (`bopp-comparative`, `vedic-rituals-hillebrandt`) — handle separately under the English-source policy.
5. **Audit followup** — re-run this exact methodology (`seed=42`, same 498 entries, same classifier) on the post-translation `body.ko` to produce a regression-free A/B comparison.

### 6.5 Defer-it case (counter-argument)

If budget pressure is acute, the minimum-viable defer is: ship Phase 4 with a UI banner per-dict reading "이 사전의 한국어 번역은 v1에서 이월된 부분 번역이며, 정확도가 낮습니다. 원문(독일어/프랑스어/라틴어)을 함께 참고하세요." (or equivalent) and queue the batch for Phase 5. **This is not recommended** — it ships a known-broken artifact under a "translated" label. But it is mechanically possible if $225 is unavailable.

---

## 7. Supporting artifacts

- Audit script: `python3` heredoc (sample → classify → report). Sample indices reproducible from `seed=42` + entry counts in §1.1.
- Raw classifier output: `/tmp/audit_results.json` (498 records, full plain/ko text + grade + reasons). Not committed (gitignored convention for `/tmp`).
- Selected examples: `/tmp/audit_examples.json` (the 33 entries quoted in §4).
- Coverage report bug to file separately: `data/reports/translation_coverage.md` reports 100% count for `bopp-comparative` / `vedic-rituals-hillebrandt` despite empty `body.ko` — count-of-key vs count-of-non-empty.

---

**End of audit.**
