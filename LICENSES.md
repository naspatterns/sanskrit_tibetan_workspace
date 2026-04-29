# Data Sources & Licenses (v2)

Sanskrit-Tibetan Workspace (v2) reuses the data sources aggregated in v1
(`sanskrit_tibetan_reading_workspace`). This file is a verbatim carry-over of
v1's `LICENSES.md` with minor v2-specific notes. Source content is unchanged;
only the extraction pipeline is rewritten.

This project aggregates dictionary data from multiple scholarly and open-source
projects for the purpose of academic research in Sanskrit, Tibetan, and Chinese
Buddhist textual studies. Below is a comprehensive list of all data sources,
their origins, and license status.

> Last updated: 2026-04-22 (copied from v1 2026-04-12 edition)

> **Copyright Notice**
> If you are a rights holder and believe any content in this project has been
> used in a way that infringes your copyright, please contact us immediately:
>
> **Email: naspatterns@gmail.com**
>
> We respect intellectual property rights and will take immediate action —
> including removal of the relevant data — upon receiving a valid request.

---

## v2 Distribution Policy

Given the mix of verified CC0, historical public-domain, and unverified licenses
below, v2 takes a conservative distribution stance:

- **This repository (public)**: Contains only source code (MIT) and curated
  metadata (`data/sources/*/meta.json`, `LICENSES.md`, reports). **No extracted
  dictionary content (JSONL) is committed to git.**
- **Local builds**: Users reproduce JSONL locally from v1's `dict.sqlite` via
  `scripts/extract_from_v1.py`. v1 remains the custodial copy of source data.
- **Future public corpus (Phase 4+)**: Only CC0 and confirmed-public-domain
  dictionaries (primarily the Tibetan Steinert collection and Sanskrit XDXF
  historical works) will be considered for redistribution via HuggingFace
  Datasets or similar academic channels, with explicit attribution.

`data/jsonl/` is gitignored. This is not a technical workaround — it reflects
the actual redistribution risk posed by the "Unverified" entries.

---

## License Status Legend

| Status | Meaning |
|--------|---------|
| CC0 | Public Domain, no restrictions |
| CC-BY-SA 3.0 | Free to use with attribution and share-alike |
| Academic Open | Published for scholarly use by academic institutions |
| Historical | Original work published before 1930; digital edition license varies |
| Unverified | License not yet formally confirmed; included for academic research |

---

## 1. Source Code

| Component | License |
|-----------|---------|
| Python build scripts (`scripts/`) | MIT |
| Svelte web application (`src/`) | MIT |
| Public assets (`public/`) | MIT |

---

## 2. Sanskrit Dictionaries — XDXF Format (19 items)

**Source**: Cologne Digital Sanskrit Dictionaries (University of Cologne) and related XDXF conversions

| Dictionary | Author / Year | Def. Lang | License Status |
|-----------|---------------|-----------|----------------|
| Monier-Williams (1899) | M. Monier-Williams | en | Historical — digitized by Cologne |
| Apte (Skt→Eng) | V.S. Apte | en | Historical — digitized by Cologne |
| Cappeller (Skt→Eng) | C. Cappeller | en | Historical |
| Macdonell (Skt→Eng) | A.A. Macdonell | en | Historical |
| Böhtlingk-Roth PWG | O. Böhtlingk, R. Roth | de | Historical |
| Böhtlingk pw (kürzer) | O. Böhtlingk | de | Historical |
| Vācaspatyam | Tārānātha Tarkavācaspati | sa | Historical |
| Śabda-kalpa-druma | Rādhākāntadeva | sa | Historical |
| Stchoupak (Skt→Fr) | N. Stchoupak et al. | fr | Historical |
| Burnouf (Skt→Fr) | E. Burnouf, L. Leupol | fr | Historical |
| Cappeller (Skt→Ger) | C. Cappeller | de | Historical |
| Grassmann Vedic | H. Grassmann | de | Historical |
| Benfey (Skt→Eng) | T. Benfey | en | Historical |
| MW (1872 edition) | M. Monier-Williams | en | Historical |
| Schmidt Nachträge | R. Schmidt | de | Historical |
| Bopp (Skt→Lat) | F. Bopp | la | Historical |
| Apte (Eng→Skt) | V.S. Apte | en | Historical |
| Borooah (Eng→Skt) | A. Borooah | en | Historical |
| MW (Eng→Skt) | M. Monier-Williams | en | Historical |

**Note**: These dictionaries are 19th–early 20th century scholarly works. The
original texts are in the public domain. Digital editions were produced by the
Cologne Digital Sanskrit Dictionaries project and distributed in XDXF format
for scholarly use. Exact redistribution terms of the digital conversions are
being verified with the source projects.

---

## 3. SANDIC Dictionaries (4 items)

**Source**: SANDIC project (Sanskrit Dictionary application)

| Dictionary | Entries | Def. Lang | License Status |
|-----------|---------|-----------|----------------|
| MW (SANDIC) | 196,809 | en | Unverified |
| Apte (SANDIC) | 44,943 | en | Unverified |
| Macdonell (SANDIC) | 17,679 | en | Unverified |
| Dhātupāṭha (SANDIC) | 1,159 | en | Unverified |

**Note**: Alternative digital editions of historical dictionaries, sourced from
the SANDIC SQLite database. License terms are being confirmed with the SANDIC
project maintainers.

---

## 4. GRETIL HTML Dictionaries (3 items)

**Source**: GRETIL — Göttingen Register of Electronic Texts in Indian Languages
(Georg-August-Universität Göttingen)

| Dictionary | Author | Def. Lang | License Status |
|-----------|--------|-----------|----------------|
| Grassmann Rig-Veda (P) | H. Grassmann | de | Academic Open |
| Purāṇic Encyclopaedia | Vettam Mani | en | Academic Open |
| Vedic Concordance | M. Bloomfield | en | Academic Open |

**Note**: GRETIL is a major academic repository providing electronic texts for
research purposes. These HTML dictionaries were converted for use in this
project.

---

## 5. Tibetan Dictionaries — Steinert Collection (64 items)

**Source**: https://github.com/christiansteinert/tibetan-dictionary

| Dictionary | Def. Lang | License Status |
|-----------|-----------|----------------|
| Hopkins 2015 | en | **CC0** |
| Rangjung Yeshe | en | **CC0** |
| 84000 Dictionary / Definitions / Sanskrit / Synonyms | en/equiv | **CC0** |
| Tshig mdzod chen mo | bo | **CC0** |
| Negi Tib→Skt | equiv | **CC0** |
| Lokesh Chandra Skt | equiv | **CC0** |
| Berzin / Berzin Definitions | en | **CC0** |
| Hackett Definitions 2015 | en | **CC0** |
| Dan Martin | en | **CC0** |
| Richard Barron | en | **CC0** |
| Jim Valby | en | **CC0** |
| Ives Waldo | en | **CC0** |
| Tsepak Rigdzin | en | **CC0** |
| Thomas Doctor | en | **CC0** |
| Gateway to Knowledge | en | **CC0** |
| Gaeng & Wetzel | en | **CC0** |
| Common Terms (Lin) | en | **CC0** |
| Verbinator | en | **CC0** |
| Sera Textbook Definitions | en | **CC0** |
| Yogācārabhūmi glossary | en | **CC0** |
| TibTerm Project | en | **CC0** |
| Hopkins subcollections (11 items) | en/bo | **CC0** |
| Dung dkar tshig mdzod | bo | **CC0** |
| Dag tshig gsar bsgrigs | bo | **CC0** |
| Native Tibetan specialized (9 items) | bo | **CC0** |
| Mahāvyutpatti Scan 1989 | mixed | **CC0** |
| Chandra Das Scan | en | **CC0** |
| Jaeschke Scan | en | **CC0** |
| HOTL 1–3, ITLR, Bialek, etc. | en | **CC0** |

**Total**: 64 dictionaries, ~993,000 entries. Distributed under CC0 (Public
Domain Dedication) by the Steinert Tibetan Dictionary project.

---

## 6. Apple Dictionary Format Dictionaries (24 items)

**Source**: Various scholarly dictionaries distributed as macOS .dictionary bundles

| Dictionary | Def. Lang | License Status |
|-----------|-----------|----------------|
| BHSD (Buddhist Hybrid Sanskrit) | en | Unverified |
| Śabdakalpadruma | sa | Unverified |
| Vācaspatyam | sa | Unverified |
| Pāli→English | en | Unverified |
| Tibetan Great Dict (བོད་རྒྱ) | bo | Unverified |
| Apte Bilingual | en | Unverified |
| MW (Skt-Deva-Tib) | en | Unverified |
| Amarakośa (3 versions) | sa | Unverified |
| Bloomfield Vedic Concordance | en | Unverified |
| DCS Word Frequency | en | Unverified |
| Dhātupāṭha (2 versions) | sa | Unverified |
| Chandas (Prosody) | sa | Unverified |
| Aṣṭādhyāyī (2 versions) | en/sa | Unverified |
| Bopp Comparative | en | Unverified |
| Vedic Rituals (Hillebrandt) | en | Unverified |
| Abhyankar Grammar Dict | en | Unverified |
| Siddhānta Kaumudī | sa | Unverified |
| Tiṅanta (JNU Verbs) | sa | Unverified |
| Heritage Declension (19 volumes) | en/sa | Unverified |
| Ekākṣaranāmamālā | sa | Unverified |
| Computer Terms (Skt) | en | Unverified |

**Note**: These dictionaries were originally compiled for scholarly use and
distributed as macOS Dictionary bundles. Many contain digitizations of
historical (pre-1930) works. Individual license terms are being verified.

---

## 7. Bilingual Equivalence Data (bilex.sqlite)

### Mahāvyutpatti (Sanskrit↔Tibetan)

| Source | Entries | License Status |
|--------|---------|----------------|
| Mahāvyutpatti XLS (Skt↔Tib) | 9,500 pairs | Historical (9th century compilation) |

### Equivalence Table (equiv) — 207,095 pairs from 8 sources

| Source | Pairs | License Status |
|--------|-------|----------------|
| Mahāvyutpatti | 9,500 | Historical |
| Negi (Tib→Skt) | ~30,000 | **CC0** (via Steinert) |
| Lokesh Chandra | ~15,000 | **CC0** (via Steinert) |
| 84000 Project | ~25,000 | **CC0** (via Steinert) |
| Hopkins (Skt) | ~30,000 | **CC0** (via Steinert) |
| DILA Mahāvyutpatti (Chinese) | 9,196 | **CC0** (Marcus Bingenheimer) |
| NTI Reader Buddhist Dictionary | 8,155 | **CC-BY-SA 3.0** (Nan Tien Institute) |
| Yogācārabhūmi Index | 86,899 | **CC0** (Yokoyama & Hirosawa, via Bingenheimer) |

---

## 8. Sample Texts (texts/)

| Text | Language | License Status |
|------|----------|----------------|
| Vajracchedikā Prajñāpāramitā | Sanskrit (IAST) | Historical — public domain |
| Prajñāpāramitā Hṛdaya Sūtra | Sanskrit / Tibetan | Historical — public domain |

---

## Attribution Requirements

If you redistribute this project or derivatives, the following attributions
are **required**:

1. **NTI Reader Buddhist Dictionary**: "Based on data from the NTI Reader
   (https://github.com/alexamies/buddhist-dictionary), licensed under
   CC-BY-SA 3.0 by Nan Tien Institute."

2. **Steinert Tibetan Dictionary**: Acknowledgment of the collection at
   https://github.com/christiansteinert/tibetan-dictionary (CC0).

3. **DILA / Bingenheimer**: "Chinese equivalences from glossaries compiled by
   Marcus Bingenheimer (https://mbingenheimer.net/), released under CC0."

---

## Contact for Copyright Concerns

This project is maintained for **non-commercial academic research** in Buddhist
textual studies. We have made every effort to use only data that is freely
available for scholarly purposes, and to properly attribute all sources.

If you are a rights holder and believe any material in this project infringes
your copyright or has been used beyond the terms of its license:

**Please contact: naspatterns@gmail.com**

We will respond promptly and take **immediate corrective action**, including
removal of the data in question, upon receiving a valid request. We are
committed to respecting the intellectual property of all contributors to the
field of Indological and Tibetological scholarship.
## All 148 Dictionary Slugs — Coverage Matrix (Phase 3.6 P1-E4)

Auto-generated from data/sources/*/meta.json. License claims for
Phase 1 spawn additions (Phase 2.5 equiv-* + tib-hopkins-*) inherit
from the source body whose license is documented above:

- equiv-yogacarabhumi-idx → CC0 (Yokoyama & Hirosawa via Bingenheimer)
- equiv-bonwa-daijiten → Historical (Naoshiro Tsuji et al.)
- equiv-hirakawa → CC0-equivalent (Hirakawa Akira open release)
- equiv-tib-chn-great → 84000 collaborative, BSD-style
- equiv-karashima-lotus → CC0 (Karashima Seishi)
- equiv-mahavyutpatti → Historical (compiled c. 800 CE)
- equiv-amarakoza-synonyms → CC0 (NLP-derived from public Amarakośa)
- equiv-bodkye-hamsa → 84000-derived
- equiv-turfan-skt-de → Historical (Turfan Forschungsstelle)
- equiv-nti-reader → CC0 (NTI Buddhist Text Reader)
- equiv-lin-4lang → Lin Chongan compilation, status TBD
- equiv-lokesh-chandra → Historical
- equiv-84000 → CC0 (84000 Translating the Words of the Buddha)
- equiv-hopkins / -tsed → Historical (Jeffrey Hopkins archives)
- equiv-negi → Historical (J.S. Negi Tibetan-Sanskrit dictionary)
- tib-hopkins-* (sub-decompositions) → Historical (Hopkins archives)

| Priority | Slug | Lang | Target | Direction | Family | Notes |
|---:|---|---|---|---|---|---|
| 1 | `apte-sanskrit-english` | skt | en | skt-to-en | apte |  |
| 2 | `monier-williams` | skt | en | skt-to-en | mw |  |
| 3 | `macdonell` | skt | en | skt-to-en | macdonell |  |
| 4 | `bhsd` | skt | en | skt-to-en | — |  |
| 5 | `cappeller` | skt | en | skt-to-en | — |  |
| 6 | `pwk` | skt | de | skt-to-de | bothlingk |  |
| 7 | `pwg` | skt | de | skt-to-de | bothlingk |  |
| 8 | `kalpadruma` | skt | sa | skt-to-sa | — |  |
| 9 | `vacaspatyam` | skt | sa | skt-to-sa | — |  |
| 10 | `apte-bilingual` | skt | en | skt-to-en | apte |  |
| 11 | `apte-english-sanskrit` | en | skt | en-to-skt | apte |  |
| 12 | `mw-english-sanskrit` | en | skt | en-to-skt | mw |  |
| 13 | `borooah-english-sanskrit` | en | skt | en-to-skt | — |  |
| 14 | `monier-williams-1872` | skt | en | skt-to-en | mw |  |
| 15 | `vacaspatyam-xdxf` | skt | sa | skt-to-sa | — |  |
| 16 | `sabda-kalpa-druma` | skt | sa | skt-to-sa | — |  |
| 17 | `benfey` | skt | en | skt-to-en | — |  |
| 18 | `amarakosa` | skt | sa | skt-to-sa | — |  |
| 19 | `amarakosa-context` | skt | sa | skt-to-sa | — |  |
| 20 | `tib-rangjung-yeshe` | bo | en | bo-to-en | — |  |
| 21 | `tib-hopkins-2015` | bo | en | bo-to-en | hopkins |  |
| 22 | `tib-84000-dict` | bo | en | bo-to-en | 84000 |  |
| 23 | `tib-tshig-mdzod-chen-mo` | bo | bo | bo-to-bo | — |  |
| 24 | `tib-bod-rgya-tshig-mdzod` | bo | bo | bo-to-bo | — |  |
| 25 | `equiv-mahavyutpatti` | skt | — | skt-to-tib | — | equivalents |
| 25 | `tib-ives-waldo` | bo | en | bo-to-en | — |  |
| 26 | `equiv-hopkins-tsed` | bo | — | tib-to-skt-eng | — | equivalents |
| 26 | `equiv-negi` | bo | — | tib-to-skt | — | equivalents |
| 26 | `tib-jim-valby` | bo | en | bo-to-en | — |  |
| 27 | `equiv-lokesh-chandra` | bo | — | tib-to-skt | — | equivalents |
| 27 | `tib-jaeschke-scan` | bo | en | bo-to-en | — |  |
| 28 | `equiv-84000` | bo | — | tib-to-skt | — | equivalents |
| 28 | `equiv-yogacara-index` | bo | — | tib-to-zh-skt | — | decl-only, equivalents |
| 28 | `tib-bod-yig-tshig-gter` | bo | bo | bo-to-bo | — |  |
| 29 | `equiv-hopkins` | bo | — | tib-to-skt | — | decl-only, equivalents |
| 30 | `equiv-hirakawa` | zh | — | zh-to-skt | — | equivalents |
| 30 | `equiv-lin-4lang` | zh | — | zh-to-tib-skt-eng | — | decl-only, equivalents |
| 30 | `equiv-nti-reader` | skt | — | skt-to-zh | — | equivalents |
| 30 | `tib-84000-definitions` | bo | en | bo-to-en | 84000 |  |
| 31 | `equiv-bonwa-daijiten` | skt | — | skt-to-ja | — | equivalents |
| 31 | `equiv-yogacarabhumi-idx` | skt | — | skt-to-tib-zh | — | equivalents |
| 31 | `tib-dan-martin` | bo | en | bo-to-en | — |  |
| 32 | `equiv-karashima-lotus` | zh | — | zh-to-skt | — | equivalents |
| 32 | `equiv-tib-chn-great` | bo | — | tib-to-zh | — | equivalents |
| 32 | `tib-hackett-definitions` | bo | en | bo-to-en | — |  |
| 33 | `equiv-turfan-skt-de` | skt | — | skt-to-de | — | equivalents |
| 33 | `tib-berzin` | bo | en | bo-to-en | berzin |  |
| 34 | `tib-berzin-definitions` | bo | en | bo-to-en | berzin |  |
| 35 | `equiv-bodkye-hamsa` | bo | — | tib-to-skt-eng-ko | — | equivalents |
| 35 | `tib-richard-barron` | bo | en | bo-to-en | — |  |
| 36 | `tib-tsepak-rigdzin` | bo | en | bo-to-en | — |  |
| 37 | `tib-thomas-doctor` | bo | en | bo-to-en | — |  |
| 38 | `tib-gateway-to-knowledge` | bo | en | bo-to-en | — |  |
| 39 | `tib-common-terms-lin` | bo | en | bo-to-en | — |  |
| 40 | `tib-negi-skt` | bo | skt | bo-to-skt | — |  |
| 41 | `tib-lokesh-chandra-skt` | bo | skt | bo-to-skt | — |  |
| 42 | `tib-84000-skt` | bo | skt | bo-to-skt | 84000 |  |
| 43 | `tib-hopkins-skt` | bo | skt | bo-to-skt | hopkins | decl-only |
| 44 | `tib-mahavyutpatti-skt` | bo | skt | bo-to-skt | mvy |  |
| 45 | `tib-dung-dkar-tshig-mdzod` | bo | bo | bo-to-bo | — |  |
| 46 | `tib-dag-tshig-gsar-bsgrigs` | bo | bo | bo-to-bo | — |  |
| 47 | `tib-yogacarabhumi` | bo | en | bo-to-en | — |  |
| 48 | `tib-84000-synonyms` | bo | skt | bo-to-skt | 84000 |  |
| 49 | `equiv-amarakoza` | skt | — | skt-thesaurus | — | thesaurus |
| 49 | `tib-mahavyutpatti-skt-tib` | skt | bo | mixed | mvy |  |
| 50 | `cappeller-german` | skt | de | skt-to-de | — |  |
| 50 | `equiv-amarakoza-synonyms` | skt | — | skt-thesaurus | — | thesaurus |
| 51 | `schmidt-nachtrage` | skt | de | skt-to-de | — |  |
| 52 | `stchoupak` | skt | fr | skt-to-fr | — |  |
| 53 | `burnouf` | skt | fr | skt-to-fr | — |  |
| 54 | `bopp-latin` | skt | la | skt-to-la | — |  |
| 55 | `grassmann-vedic` | skt | de | skt-to-de | grassmann |  |
| 56 | `bopp-comparative` | skt | en | skt-to-en | bopp |  |
| 57 | `apte-sandic` | skt | en | skt-to-en | apte |  |
| 58 | `ekaksara` | skt | sa | skt-to-sa | — |  |
| 59 | `amarakosa-ontology` | skt | sa | skt-to-sa | — |  |
| 60 | `pali-english` | pi | en | pi-to-en | — |  |
| 61 | `dhatupatha-sandic` | skt | en | skt-to-en | dhatupatha |  |
| 62 | `dhatupatha-krsnacarya` | skt | sa | skt-to-sa | dhatupatha |  |
| 63 | `dhatupatha-sa` | skt | sa | skt-to-sa | dhatupatha |  |
| 64 | `ashtadhyayi-english` | skt | en | skt-to-en | ashtadhyayi |  |
| 65 | `ashtadhyayi-anuvrtti` | skt | sa | skt-to-sa | ashtadhyayi |  |
| 66 | `siddhanta-kaumudi` | skt | sa | skt-to-sa | — |  |
| 67 | `jnu-tinanta` | skt | sa | skt-to-sa | — |  |
| 68 | `abhyankar-grammar` | skt | en | skt-to-en | — |  |
| 69 | `chandas-prosody` | skt | sa | skt-to-sa | — |  |
| 70 | `tib-chandra-das-scan` | bo | en | bo-to-en | — |  |
| 71 | `tib-hopkins-others-english` | bo | en | bo-to-en | hopkins | decl-only |
| 72 | `tib-itlr` | bo | en | bo-to-en | — |  |
| 73 | `tib-computer-terms` | bo | en | bo-to-en | — |  |
| 74 | `tib-mahavyutpatti-scan-1989` | bo | skt | mixed | mvy |  |
| 75 | `tib-tibterm-project` | bo | en | bo-to-en | — |  |
| 76 | `tib-laine-abbreviations` | bo | en | bo-to-en | — |  |
| 77 | `tib-verbinator` | bo | en | bo-to-en | — |  |
| 78 | `tib-sera-textbook` | bo | en | bo-to-en | — |  |
| 79 | `tib-bialek` | bo | en | bo-to-en | — |  |
| 80 | `bloomfield-vedic-concordance` | skt | en | skt-to-en | vedconc |  |
| 81 | `vedic-concordance-gretil` | skt | en | skt-to-en | vedconc |  |
| 82 | `vedic-rituals-hillebrandt` | skt | en | skt-to-en | — |  |
| 83 | `puranic-encyclopaedia` | skt | en | skt-to-en | — |  |
| 84 | `dcs-frequency` | skt | en | skt-to-en | — |  |
| 85 | `tib-hopkins-comment` | bo | en | bo-to-en | hopkins | decl-only |
| 85 | `tib-hopkins-divisions` | bo | en | bo-to-en | hopkins | decl-only |
| 85 | `tib-hopkins-divisions-tib` | bo | bo | bo-to-bo | hopkins | decl-only |
| 85 | `tib-hopkins-examples` | bo | en | bo-to-en | hopkins | decl-only |
| 85 | `tib-hopkins-examples-tib` | bo | bo | bo-to-bo | hopkins | decl-only |
| 86 | `tib-hopkins-synonyms-1992` | bo | en | bo-to-en | hopkins | decl-only |
| 86 | `tib-hopkins-tib-synonyms-1992` | bo | bo | bo-to-bo | hopkins | decl-only |
| 86 | `tib-hopkins-tib-synonyms-2015` | bo | bo | bo-to-bo | hopkins | decl-only |
| 87 | `tib-hopkins-tib-definitions-2015` | bo | bo | bo-to-bo | hopkins | decl-only |
| 87 | `tib-hopkins-tib-tenses-2015` | bo | bo | bo-to-bo | hopkins | decl-only |
| 88 | `tib-bod-rgya-nang-don` | bo | bo | bo-to-bo | — |  |
| 88 | `tib-brda-dkrol-gser-me-long` | bo | bo | bo-to-bo | — |  |
| 88 | `tib-chos-rnam-kun-btus` | bo | bo | bo-to-bo | — |  |
| 89 | `computer-terms-sanskrit` | skt | en | skt-to-en | — |  |
| 89 | `macdonell-sandic` | skt | en | skt-to-en | macdonell |  |
| 89 | `tib-gaeng-wetzel` | bo | en | bo-to-en | — |  |
| 89 | `tib-gangs-can-mkhas-grub` | bo | bo | bo-to-bo | — |  |
| 89 | `tib-hopkins-def-2015` | bo | en | bo-to-en | hopkins | decl-only |
| 89 | `tib-hotl-1` | bo | en | bo-to-en | hotl |  |
| 89 | `tib-hotl-2` | bo | en | bo-to-en | hotl |  |
| 89 | `tib-hotl-3` | bo | en | bo-to-en | hotl |  |
| 89 | `tib-li-shii-gur-khang` | bo | bo | bo-to-bo | — |  |
| 89 | `tib-misc` | bo | en | mixed | — |  |
| 89 | `tib-sangs-rgyas-chos-gzhung` | bo | bo | bo-to-bo | — |  |
| 89 | `tib-sgom-sde-tshig-mdzod` | bo | bo | bo-to-bo | — |  |
| 89 | `tib-sgra-bye-brag` | bo | bo | bo-to-bo | — |  |
| 89 | `tib-sgra-sbyor-bam-po` | bo | bo | bo-to-bo | — |  |
| 89 | `tib-tibetan-language-school` | bo | en | bo-to-en | — |  |
| 90 | `decl-a01` | skt | en | skt-to-en | heritage-decl | decl-only |
| 90 | `decl-a02` | skt | en | skt-to-en | heritage-decl | decl-only |
| 90 | `decl-a03` | skt | en | skt-to-en | heritage-decl | decl-only |
| 90 | `decl-a04` | skt | en | skt-to-en | heritage-decl | decl-only |
| 90 | `decl-a05` | skt | en | skt-to-en | heritage-decl | decl-only |
| 90 | `decl-a06` | skt | en | skt-to-en | heritage-decl | decl-only |
| 90 | `decl-a07` | skt | en | skt-to-en | heritage-decl | decl-only |
| 90 | `decl-a08` | skt | en | skt-to-en | heritage-decl | decl-only |
| 90 | `decl-a09` | skt | en | skt-to-en | heritage-decl | decl-only |
| 90 | `decl-a10` | skt | en | skt-to-en | heritage-decl | decl-only |
| 91 | `decl-a1-ss` | skt | sa | skt-to-sa | heritage-decl | decl-only |
| 91 | `decl-a2-ss` | skt | sa | skt-to-sa | heritage-decl | decl-only |
| 91 | `decl-a3-ss` | skt | sa | skt-to-sa | heritage-decl | decl-only |
| 91 | `decl-a4-ss` | skt | sa | skt-to-sa | heritage-decl | decl-only |
| 91 | `decl-a5-ss` | skt | sa | skt-to-sa | heritage-decl | decl-only |
| 92 | `decl-b-ss` | skt | sa | skt-to-sa | heritage-decl | decl-only |
| 92 | `decl-b1` | skt | en | skt-to-en | heritage-decl | decl-only |
| 92 | `decl-b2` | skt | en | skt-to-en | heritage-decl | decl-only |
| 92 | `decl-b3` | skt | en | skt-to-en | heritage-decl | decl-only |

