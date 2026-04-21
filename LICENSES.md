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
