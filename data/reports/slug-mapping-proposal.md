# Slug · Priority Mapping Proposal (135 dicts)

v1 dict 이름을 v2 slug로 변환하고 priority / direction / tier를 제안합니다.
사용자 review 후 `scripts/build_meta.py`가 이 표대로 135개 `data/sources/{slug}/meta.json`을 일괄 생성합니다.

## Slug 네이밍 규칙

- 전부 소문자, 하이픈 구분
- `.dict`, `.apple`, `.sandic`, `.gretil` 접미사 제거 → `source_format` 필드로 이동
- `tib_XX-Name` → `tib-name` (숫자 prefix 제거, CamelCase → 하이픈)
- Heritage declension은 `decl-a01` 등 원형 유지 (시리즈 구조 명확)
- 가독성 우선 — `cappeller` > `cappse`

## Priority 대역 (FB-3 준수)

| 대역 | 범주 |
|---|---|
| 1-9 | Sanskrit 핵심 학술 사전 (Apte, MW, Macdonell, BHSD, Cappeller, PWG, PWK) |
| 10-19 | Sanskrit 보조 + Sanskrit-Sanskrit |
| 20-29 | Tibetan 주요 (RY, Hopkins, 84000, tshig-mdzod) |
| 30-39 | Tibetan tier 2 영어 정의 |
| 40-49 | Tibetan 전문 (Skt equiv, native tshig-mdzod) |
| 50-59 | Sanskrit tier 2 (DE/FR/LA 유럽어) |
| 60-69 | Sanskrit 전문 (Vedic, grammar, tech) |
| 70-79 | Tibetan tier 3 + Hopkins 부분집합 |
| 80-89 | archival / scan |
| 90-99 | Heritage declension (`exclude_from_search: true`) |

같은 priority 내부 정렬: entry_count DESC → alphabetical.

## 정렬 규칙 요약

`meta.json.exclude_from_search: true`인 사전 20개는 검색 탭에서 완전 제외 (FB-5).
`direction: "en-to-skt"`인 3개 (Apte Eng→Skt, Borooah, MW Eng→Skt)는 정상 검색
경로로 편입 — 사용자가 영어 입력 시 exact match (FB-8).

---

## 제안 테이블 (135 rows)

| Priority | Slug | Short | Long Name | v1 Name | Lang | Target | Direction | Tier | Entries | License | Source | Notes |
|---------:|------|-------|-----------|---------|------|--------|-----------|-----:|--------:|---------|--------|-------|

### Priority 1-9: Sanskrit 핵심 학술 사전

| Priority | Slug | Short | Long Name | v1 Name | Lang | Target | Direction | Tier | Entries | License | Source | Notes |
|---------:|------|-------|-----------|---------|------|--------|-----------|-----:|--------:|---------|--------|-------|
| 1 | `apte-sanskrit-english` | Apte | Apte Practical Sanskrit-English Dictionary (1890) | `aptees.dict` | skt | en | skt-to-en | 1 | 11,314 | public-domain | xdxf | FB-3 #1 |
| 2 | `monier-williams` | MW | Monier-Williams Sanskrit-English Dictionary (1899) | `mwse.dict` | skt | en | skt-to-en | 1 | 223,501 | public-domain | xdxf | FB-3 #2 |
| 3 | `macdonell` | Macdonell | A Practical Sanskrit Dictionary (Macdonell) | `macdse.dict` | skt | en | skt-to-en | 1 | 20,787 | public-domain | xdxf | FB-3 #3 |
| 4 | `bhsd` | BHSD | Buddhist Hybrid Sanskrit Dictionary (Edgerton) | `bhsd.apple` | skt | en | skt-to-en | 1 | 17,807 | unverified | apple_dict | FB-3 #4 |
| 5 | `cappeller` | Cappeller | Cappeller Sanskrit-English Dictionary | `cappse.dict` | skt | en | skt-to-en | 1 | 39,872 | public-domain | xdxf | FB-3 #5 |
| 6 | `bothlingk-kurzer` | PW | Böhtlingk Sanskrit Kürzere Wörterbuch | `pwk.dict` | skt | de | skt-to-de | 1 | 135,776 | public-domain | xdxf | FB-3 #6 |
| 7 | `bothlingk-roth` | PWG | Böhtlingk-Roth Grosses Petersburger Wörterbuch | `pwg.dict` | skt | de | skt-to-de | 1 | 122,730 | public-domain | xdxf | FB-3 #7 |
| 8 | `kalpadruma` | Kalpadruma | Śabdakalpadruma (Rādhākāntadeva) | `kalpadruma.apple` | skt | sa | skt-to-sa | 1 | 42,200 | unverified | apple_dict | FB-3 #8 |
| 9 | `vacaspatyam` | Vācaspatyam | Vācaspatyam (Tārānātha Tarkavācaspati) | `vacaspatyam.apple` | skt | sa | skt-to-sa | 1 | 48,351 | unverified | apple_dict | FB-3 #9 |

### Priority 10-19: Sanskrit 보조 + Sanskrit-Sanskrit

| Priority | Slug | Short | Long Name | v1 Name | Lang | Target | Direction | Tier | Entries | License | Source | Notes |
|---------:|------|-------|-----------|---------|------|--------|-----------|-----:|--------:|---------|--------|-------|
| 10 | `apte-bilingual` | Apte-Bi | Apte Bilingual | `apte-bi.apple` | skt | en | skt-to-en | 2 | 122,555 | unverified | apple_dict | FB-3 #10 |
| 11 | `vacaspatyam-xdxf` | Vācaspatyam-X | Vācaspatyam (XDXF) | `vcpss.dict` | skt | sa | skt-to-sa | 2 | 48,370 | public-domain | xdxf | XDXF 판본 |
| 12 | `sabda-kalpa-druma` | ŚKD | Śabda-kalpa-druma (XDXF) | `skdss.dict` | skt | sa | skt-to-sa | 2 | 42,203 | public-domain | xdxf | XDXF 판본 |
| 13 | `benfey` | Benfey | Benfey Sanskrit-English | `benfse.dict` | skt | en | skt-to-en | 2 | 17,322 | public-domain | xdxf | |
| 14 | `monier-williams-1872` | MW1872 | Monier-Williams (1872 edition) | `mwse72.dict` | skt | en | skt-to-en | 2 | 55,367 | public-domain | xdxf | 구판 |
| 15 | `mw-skt-deva-tib` | MW-SDT | MW with Devanagari + Tibetan | `mw-sdt.apple` | skt | en | skt-to-en | 2 | 166,273 | unverified | apple_dict | |
| 16 | `amarakosa` | Amarakośa | Amarakośa | `amara.apple` | skt | sa | skt-to-sa | 2 | 3,137 | unverified | apple_dict | thesaurus |
| 17 | `amarakosa-context` | Amarakośa-Ctx | Amarakośa (context) | `amara-ctx.apple` | skt | sa | skt-to-sa | 2 | 3,790 | unverified | apple_dict | |
| 18 | `amarakosa-ontology` | Amarakośa-Onto | Amarakośa (ontology) | `amara-onto.apple` | skt | sa | skt-to-sa | 2 | 11,582 | unverified | apple_dict | |
| 19 | `ekaksara` | Ekākṣara | Ekākṣaranāmamālā | `ekaksara.apple` | skt | sa | skt-to-sa | 2 | 391 | unverified | apple_dict | monosyllable |

### Priority 20-29: Tibetan 주요

| Priority | Slug | Short | Long Name | v1 Name | Lang | Target | Direction | Tier | Entries | License | Source | Notes |
|---------:|------|-------|-----------|---------|------|--------|-----------|-----:|--------:|---------|--------|-------|
| 20 | `tib-rangjung-yeshe` | RY | Rangjung Yeshe Tibetan-English | `tib_02-RangjungYeshe` | bo | en | bo-to-en | 1 | 73,730 | CC0 | xdxf | FB-3 #20 |
| 21 | `tib-hopkins-2015` | Hopkins | Hopkins Tibetan-English 2015 | `tib_01-Hopkins2015` | bo | en | bo-to-en | 1 | 17,720 | CC0 | xdxf | FB-3 #21 |
| 22 | `tib-84000-dict` | 84000 | 84000 Dictionary | `tib_43-84000Dict` | bo | en | bo-to-en | 1 | 25,356 | CC0 | xdxf | FB-3 #22 |
| 23 | `tib-tshig-mdzod-chen-mo` | TshigMdzod | Tshig mdzod chen mo (native) | `tib_25-tshig-mdzod-chen-mo-Tib` | bo | bo | bo-to-bo | 1 | 51,030 | CC0 | xdxf | native 티벳어 |
| 24 | `tib-bod-rgya-tshig-mdzod` | BodRgya | Bod rgya tshig mdzod chen mo | `apple_bod_rgya_tshig_mdzod` | bo | bo | bo-to-bo | 1 | 53,466 | unverified | apple_dict | Apple판 |
| 25 | `tib-bod-rgya-xdxf` | BodRgya-X | Bod rgya (XDXF) | `bod-rgya.apple` | bo | bo | bo-to-bo | 1 | 53,466 | unverified | apple_dict | 중복 — 정리 필요 |
| 26 | `tib-ives-waldo` | IvesWaldo | Ives Waldo | `tib_08-IvesWaldo` | bo | en | bo-to-en | 2 | 120,946 | CC0 | xdxf | 대형 |
| 27 | `tib-jim-valby` | JimValby | Jim Valby | `tib_07-JimValby` | bo | en | bo-to-en | 2 | 64,221 | CC0 | xdxf | 대형 |
| 28 | `tib-jaeschke-scan` | Jaeschke | Jaeschke Tibetan-English (Scan) | `tib_66-Jaeschke_Scan` | bo | en | bo-to-en | 2 | 154,112 | CC0 | xdxf | 고전 레퍼런스 |
| 29 | `tib-bod-yig-tshig-gter` | BodYigGter | Bod yig tshig gter rgya mtsho | `tib_62-bod_yig_tshig_gter_rgya_mtsho` | bo | bo | bo-to-bo | 2 | 81,935 | CC0 | xdxf | native 대형 |

### Priority 30-39: Tibetan tier 2 영어 정의

| Priority | Slug | Short | Long Name | v1 Name | Lang | Target | Direction | Tier | Entries | License | Source | Notes |
|---------:|------|-------|-----------|---------|------|--------|-----------|-----:|--------:|---------|--------|-------|
| 30 | `tib-84000-definitions` | 84000-Def | 84000 Definitions | `tib_44-84000Definitions` | bo | en | bo-to-en | 2 | 26,239 | CC0 | xdxf | |
| 31 | `tib-dan-martin` | DanMartin | Dan Martin | `tib_09-DanMartin` | bo | en | bo-to-en | 2 | 20,196 | CC0 | xdxf | |
| 32 | `tib-hackett-definitions` | Hackett | Hackett Definitions 2015 | `tib_05-Hackett-Def2015` | bo | en | bo-to-en | 2 | 3,184 | CC0 | xdxf | |
| 33 | `tib-berzin` | Berzin | Berzin Tibetan-English | `tib_03-Berzin` | bo | en | bo-to-en | 2 | 1,197 | CC0 | xdxf | |
| 34 | `tib-berzin-def` | Berzin-Def | Berzin Definitions | `tib_04-Berzin-Def` | bo | en | bo-to-en | 2 | 888 | CC0 | xdxf | |
| 35 | `tib-richard-barron` | Barron | Richard Barron | `tib_10-RichardBarron` | bo | en | bo-to-en | 2 | 4,742 | CC0 | xdxf | |
| 36 | `tib-tsepak-rigdzin` | TsepakRigdzin | Tsepak Rigdzin | `tib_33-TsepakRigdzin` | bo | en | bo-to-en | 2 | 2,695 | CC0 | xdxf | |
| 37 | `tib-thomas-doctor` | ThomasDoctor | Thomas Doctor | `tib_35-ThomasDoctor` | bo | en | bo-to-en | 2 | 502 | CC0 | xdxf | |
| 38 | `tib-gateway-to-knowledge` | GatewayK | Gateway to Knowledge | `tib_23-GatewayToKnowledge` | bo | en | bo-to-en | 2 | 522 | CC0 | xdxf | |
| 39 | `tib-common-terms-lin` | CommonT-Lin | Common Terms (Lin) | `tib_40-CommonTerms-Lin` | bo | en | bo-to-en | 2 | 2,325 | CC0 | xdxf | |

### Priority 40-49: Tibetan 전문 (Skt equivalents + native)

| Priority | Slug | Short | Long Name | v1 Name | Lang | Target | Direction | Tier | Entries | License | Source | Notes |
|---------:|------|-------|-----------|---------|------|--------|-----------|-----:|--------:|---------|--------|-------|
| 40 | `tib-negi-skt` | Negi | Negi Tibetan→Sanskrit | `tib_50-NegiSkt` | bo | sa | bo-to-skt | 2 | 79,293 | CC0 | xdxf | equiv |
| 41 | `tib-lokesh-chandra-skt` | Lokesh | Lokesh Chandra Sanskrit | `tib_49-LokeshChandraSkt` | bo | sa | bo-to-skt | 2 | 15,961 | CC0 | xdxf | equiv |
| 42 | `tib-84000-skt` | 84000-Skt | 84000 Sanskrit | `tib_46-84000Skt` | bo | sa | bo-to-skt | 2 | 15,705 | CC0 | xdxf | equiv |
| 43 | `tib-hopkins-skt-1992` | Hopkins-Skt92 | Hopkins Sanskrit 1992 | `tib_15-Hopkins-Skt1992` | bo | sa | bo-to-skt | 2 | 14,040 | CC0 | xdxf | equiv |
| 44 | `tib-hopkins-skt-2015` | Hopkins-Skt15 | Hopkins Sanskrit 2015 | `tib_15-Hopkins-Skt2015` | bo | sa | bo-to-skt | 2 | 14,757 | CC0 | xdxf | equiv |
| 45 | `tib-mahavyutpatti-skt` | MVY-Skt | Mahāvyutpatti Sanskrit | `tib_21-Mahavyutpatti-Skt` | bo | sa | bo-to-skt | 2 | 9,586 | CC0 | xdxf | equiv |
| 46 | `tib-dung-dkar-tshig-mdzod` | DungDkar | Dung dkar tshig mdzod chen mo | `tib_34-dung-dkar-tshig-mdzod-chen-mo-Tib` | bo | bo | bo-to-bo | 2 | 13,310 | CC0 | xdxf | native |
| 47 | `tib-dag-tshig-gsar-bsgrigs` | DagTshig | Dag tshig gsar bsgrigs | `tib_37-dag_tshig_gsar_bsgrigs-Tib` | bo | bo | bo-to-bo | 2 | 6,938 | CC0 | xdxf | native |
| 48 | `tib-yoghacharabhumi` | YBh | Yogācārabhūmi glossary | `tib_22-Yoghacharabhumi-glossary` | bo | en | bo-to-en | 2 | 16,028 | CC0 | xdxf | domain |
| 49 | `tib-84000-synonyms` | 84000-Syn | 84000 Synonyms | `tib_45-84000Synonyms` | bo | sa | bo-to-skt | 2 | 6,029 | CC0 | xdxf | equiv |

### Priority 50-59: Sanskrit tier 2 유럽어 (DE/FR/LA)

| Priority | Slug | Short | Long Name | v1 Name | Lang | Target | Direction | Tier | Entries | License | Source | Notes |
|---------:|------|-------|-----------|---------|------|--------|-----------|-----:|--------:|---------|--------|-------|
| 50 | `cappeller-german` | Cappeller-G | Cappeller Sanskrit-Deutsch | `cappsg.dict` | skt | de | skt-to-de | 2 | 30,038 | public-domain | xdxf | |
| 51 | `schmidt-nachtrage` | Schmidt | Schmidt Nachträge | `schnzsw.dict` | skt | de | skt-to-de | 2 | 28,751 | public-domain | xdxf | PW 보충 |
| 52 | `stchoupak` | Stchoupak | Stchoupak Skt-Français | `stcsf.dict` | skt | fr | skt-to-fr | 2 | 24,574 | public-domain | xdxf | |
| 53 | `burnouf` | Burnouf | Burnouf Skt-Français | `bursf.dict` | skt | fr | skt-to-fr | 2 | 19,775 | public-domain | xdxf | |
| 54 | `bopp-latin` | Bopp-L | Bopp Skt-Latin | `boppsl.dict` | skt | la | skt-to-la | 2 | 9,006 | public-domain | xdxf | |
| 55 | `grassmann-vedic` | Grassmann | Grassmann Vedic Lexicon | `grasg_a.dict` | skt | de | skt-to-de | 2 | 10,778 | public-domain | xdxf | Vedic |
| 56 | `grassmann-rv-gretil` | Grassmann-RV | Grassmann Rig-Veda (GRETIL P) | `grasg_p.gretil` | skt | de | skt-to-de | 2 | 10,778 | academic-open | gretil | |
| 57 | `bopp-comparative` | Bopp-Comp | Bopp Comparative Grammar | `bopp.apple` | skt | en | skt-to-en | 2 | 8,960 | unverified | apple_dict | |
| 58 | `apte-sandic` | Apte-SD | Apte (SANDIC) | `aptese.sandic` | skt | en | skt-to-en | 3 | 44,943 | unverified | sandic | v1 Eng→Skt? |
| 59 | `mw-sandic` | MW-SD | Monier-Williams (SANDIC) | `mwse.sandic` | skt | en | skt-to-en | 3 | 196,809 | unverified | sandic | |

### Priority 60-69: Sanskrit 전문 (grammar, Vedic, tech) + Pāli

| Priority | Slug | Short | Long Name | v1 Name | Lang | Target | Direction | Tier | Entries | License | Source | Notes |
|---------:|------|-------|-----------|---------|------|--------|-----------|-----:|--------:|---------|--------|-------|
| 60 | `pali-english` | Pāli-En | Pāli-English Dictionary | `pali-en.apple` | pi | en | pi-to-en | 1 | 49,000 | unverified | apple_dict | Pāli |
| 61 | `mahavyutpatti-skt-tib` | MVY | Mahāvyutpatti (Skt↔Tib) | `mahavyutpatti` | skt | bo | skt-to-sa | 1 | 19,069 | public-domain | xdxf | bilingual |
| 62 | `macdonell-sandic` | Macdonell-SD | Macdonell (SANDIC) | `macdse.sandic` | skt | en | skt-to-en | 3 | 17,679 | unverified | sandic | |
| 63 | `dhatupatha-sandic` | Dhātu-SD | Dhātupāṭha (SANDIC) | `dhatupatha.sandic` | skt | en | skt-to-en | 2 | 1,159 | unverified | sandic | grammar |
| 64 | `dhatupatha-krsnacarya` | Dhātu-Kṛ | Dhātupāṭha (Kṛṣṇācārya) | `dhatupatha-kr.apple` | skt | sa | skt-to-sa | 2 | 2,101 | unverified | apple_dict | grammar |
| 65 | `dhatupatha-sa` | Dhātu | Dhātupāṭha | `dhatupatha-sa.apple` | skt | sa | skt-to-sa | 2 | 2,282 | unverified | apple_dict | grammar |
| 66 | `ashtadhyayi-english` | Aṣṭ-En | Aṣṭādhyāyī (English) | `ashtadhyayi-en.apple` | skt | en | skt-to-en | 2 | 3,983 | unverified | apple_dict | grammar |
| 67 | `ashtadhyayi-anuvrtti` | Aṣṭ-Anv | Aṣṭādhyāyī (Anuvṛtti) | `ashtadhyayi-anv.apple` | skt | sa | skt-to-sa | 2 | 3,983 | unverified | apple_dict | grammar |
| 68 | `siddhanta-kaumudi` | Siddh-K | Siddhānta Kaumudī | `siddh-kaumudi.apple` | skt | sa | skt-to-sa | 2 | 4,815 | unverified | apple_dict | grammar |
| 69 | `jnu-tinanta` | JNU-Tiṅ | Tiṅanta (JNU Verbs) | `jnu-tinanta.apple` | skt | sa | skt-to-sa | 2 | 5,630 | unverified | apple_dict | verbs |

### Priority 70-79: Tibetan tier 3 + Hopkins subcollections

| Priority | Slug | Short | Long Name | v1 Name | Lang | Target | Direction | Tier | Entries | License | Source | Notes |
|---------:|------|-------|-----------|---------|------|--------|-----------|-----:|--------:|---------|--------|-------|
| 70 | `tib-chandra-das-scan` | ChandraDas | Chandra Das (Scan) | `tib_65-ChandraDas_Scan` | bo | en | bo-to-en | 3 | 20,773 | CC0 | xdxf | scan |
| 71 | `tib-hopkins-others-english` | Hopkins-OE | Hopkins (others, English) 2015 | `tib_20-Hopkins-others'English2015` | bo | en | bo-to-en | 3 | 6,511 | CC0 | xdxf | subcollection |
| 72 | `tib-itlr` | ITLR | ITLR | `tib_52-ITLR` | bo | en | bo-to-en | 3 | 5,654 | CC0 | xdxf | |
| 73 | `tib-computer-terms` | CompTerms | Computer Terms (Tibetan) | `tib_36-ComputerTerms` | bo | en | bo-to-en | 3 | 5,683 | CC0 | xdxf | domain |
| 74 | `tib-mahavyutpatti-scan-1989` | MVY-Scan | Mahāvyutpatti (Scan 1989) | `tib_63-Mahavyutpatti-Scan-1989` | bo | sa | mixed | 3 | 9,583 | CC0 | xdxf | scan |
| 75 | `tib-tibterm-project` | TibTerm | TibTerm Project | `tib_48-TibTermProject` | bo | en | bo-to-en | 3 | 7,965 | CC0 | xdxf | domain |
| 76 | `tib-laine-abbreviations` | Laine | Laine Abbreviations | `tib_51-LaineAbbreviations` | bo | en | bo-to-en | 3 | 7,468 | CC0 | xdxf | |
| 77 | `tib-verbinator` | Verbinator | Verbinator | `tib_26-Verbinator` | bo | en | bo-to-en | 3 | 4,330 | CC0 | xdxf | verbs |
| 78 | `tib-sera-textbook` | Sera | Sera Textbook Definitions | `tib_42-Sera-Textbook-Definitions` | bo | en | bo-to-en | 3 | 1,223 | CC0 | xdxf | |
| 79 | `tib-bialek` | Bialek | Bialek | `tib_53-Bialek` | bo | en | bo-to-en | 3 | 2,145 | CC0 | xdxf | |

### Priority 80-89: archival / scan / Hopkins 부분집합 / eng-to-skt 역방향

| Priority | Slug | Short | Long Name | v1 Name | Lang | Target | Direction | Tier | Entries | License | Source | Notes |
|---------:|------|-------|-----------|---------|------|--------|-----------|-----:|--------:|---------|--------|-------|
| 80 | `apte-english-sanskrit` | Apte-ES | Apte English→Sanskrit | `aptese.dict` | en | skt | en-to-skt | 2 | 31,750 | public-domain | xdxf | **FB-8 역방향 #1** |
| 81 | `mw-english-sanskrit` | MW-ES | Monier-Williams English→Sanskrit | `mwes.dict` | en | skt | en-to-skt | 2 | 32,503 | public-domain | xdxf | **FB-8 역방향 #2** |
| 82 | `borooah-english-sanskrit` | Borooah | Borooah English→Sanskrit | `bores.dict` | en | skt | en-to-skt | 2 | 24,608 | public-domain | xdxf | **FB-8 역방향 #3** |
| 83 | `bloomfield-vedic-concordance` | Bloomfield | Bloomfield Vedic Concordance | `bloomfield.apple` | skt | en | skt-to-en | 3 | 88,837 | unverified | apple_dict | Vedic |
| 84 | `vedic-concordance-gretil` | VedConc | Vedic Concordance (GRETIL) | `vedconc.gretil` | skt | en | skt-to-en | 3 | 80,654 | academic-open | gretil | Vedic |
| 85 | `vedic-rituals-hillebrandt` | VedRit | Vedic Rituals (Hillebrandt) | `vedic-rituals.apple` | skt | en | skt-to-en | 3 | 6,176 | unverified | apple_dict | domain |
| 86 | `puranic-encyclopaedia` | PurEnc | Purāṇic Encyclopaedia (Vettam Mani) | `pese.gretil` | skt | en | skt-to-en | 3 | 8,832 | academic-open | gretil | domain |
| 87 | `dcs-frequency` | DCS | DCS Word Frequency | `dcs-freq.apple` | skt | en | skt-to-en | 3 | 72,804 | unverified | apple_dict | frequency |
| 88 | `abhyankar-grammar` | Abhyankar | Abhyankar Grammar Dictionary | `abhyankar.apple` | skt | en | skt-to-en | 3 | 4,350 | unverified | apple_dict | grammar |
| 89 | `chandas-prosody` | Chandas | Chandas (Prosody) | `chandas.apple` | skt | sa | skt-to-sa | 3 | 1,199 | unverified | apple_dict | prosody |

### Priority 90-99: Heritage Declension (exclude_from_search = true, FB-5)

| Priority | Slug | Short | Long Name | v1 Name | Lang | Target | Direction | Tier | Entries | License | Source | Notes |
|---------:|------|-------|-----------|---------|------|--------|-----------|-----:|--------:|---------|--------|-------|
| 90 | `decl-a01` | Decl-A01 | Heritage Declension A-01 (san→eng) | `decl-a01.apple` | skt | en | skt-to-en | 3 | 30,299 | unverified | apple_dict | heritage-decl |
| 90 | `decl-a02` | Decl-A02 | Heritage Declension A-02 (san→eng) | `decl-a02.apple` | skt | en | skt-to-en | 3 | 30,234 | unverified | apple_dict | heritage-decl |
| 90 | `decl-a03` | Decl-A03 | Heritage Declension A-03 (san→eng) | `decl-a03.apple` | skt | en | skt-to-en | 3 | 30,080 | unverified | apple_dict | heritage-decl |
| 90 | `decl-a04` | Decl-A04 | Heritage Declension A-04 (san→eng) | `decl-a04.apple` | skt | en | skt-to-en | 3 | 29,980 | unverified | apple_dict | heritage-decl |
| 90 | `decl-a05` | Decl-A05 | Heritage Declension A-05 (san→eng) | `decl-a05.apple` | skt | en | skt-to-en | 3 | 30,262 | unverified | apple_dict | heritage-decl |
| 90 | `decl-a06` | Decl-A06 | Heritage Declension A-06 (san→eng) | `decl-a06.apple` | skt | en | skt-to-en | 3 | 29,983 | unverified | apple_dict | heritage-decl |
| 90 | `decl-a07` | Decl-A07 | Heritage Declension A-07 (san→eng) | `decl-a07.apple` | skt | en | skt-to-en | 3 | 30,734 | unverified | apple_dict | heritage-decl |
| 90 | `decl-a08` | Decl-A08 | Heritage Declension A-08 (san→eng) | `decl-a08.apple` | skt | en | skt-to-en | 3 | 30,469 | unverified | apple_dict | heritage-decl |
| 90 | `decl-a09` | Decl-A09 | Heritage Declension A-09 (san→eng) | `decl-a09.apple` | skt | en | skt-to-en | 3 | 30,651 | unverified | apple_dict | heritage-decl |
| 90 | `decl-a10` | Decl-A10 | Heritage Declension A-10 (san→eng) | `decl-a10.apple` | skt | en | skt-to-en | 3 | 18,277 | unverified | apple_dict | heritage-decl |
| 91 | `decl-a1-ss` | Decl-A1-SS | Heritage Declension A-1 (san→san) | `decl-a1-ss.apple` | skt | sa | skt-to-sa | 3 | 60,260 | unverified | apple_dict | heritage-decl |
| 91 | `decl-a2-ss` | Decl-A2-SS | Heritage Declension A-2 (san→san) | `decl-a2-ss.apple` | skt | sa | skt-to-sa | 3 | 59,905 | unverified | apple_dict | heritage-decl |
| 91 | `decl-a3-ss` | Decl-A3-SS | Heritage Declension A-3 (san→san) | `decl-a3-ss.apple` | skt | sa | skt-to-sa | 3 | 60,082 | unverified | apple_dict | heritage-decl |
| 91 | `decl-a4-ss` | Decl-A4-SS | Heritage Declension A-4 (san→san) | `decl-a4-ss.apple` | skt | sa | skt-to-sa | 3 | 60,407 | unverified | apple_dict | heritage-decl |
| 91 | `decl-a5-ss` | Decl-A5-SS | Heritage Declension A-5 (san→san) | `decl-a5-ss.apple` | skt | sa | skt-to-sa | 3 | 51,513 | unverified | apple_dict | heritage-decl |
| 92 | `decl-b1` | Decl-B1 | Heritage Declension B-1 (san→eng) | `decl-b1.apple` | skt | en | skt-to-en | 3 | 30,181 | unverified | apple_dict | heritage-decl |
| 92 | `decl-b2` | Decl-B2 | Heritage Declension B-2 (san→eng) | `decl-b2.apple` | skt | en | skt-to-en | 3 | 30,242 | unverified | apple_dict | heritage-decl |
| 92 | `decl-b3` | Decl-B3 | Heritage Declension B-3 (san→eng) | `decl-b3.apple` | skt | en | skt-to-en | 3 | 6,381 | unverified | apple_dict | heritage-decl |
| 92 | `decl-b-ss` | Decl-B-SS | Heritage Declension B (san→san) | `decl-b-ss.apple` | skt | sa | skt-to-sa | 3 | 80,866 | unverified | apple_dict | heritage-decl |

(Heritage declension 19개. v1 정확히 20개 언급했으나 DB에는 19개만 존재)

### Priority 70-79 잔여 Tibetan tier 3 (Hopkins 부분집합, 소형 native 사전)

| Priority | Slug | Short | Long Name | v1 Name | Lang | Target | Direction | Tier | Entries | License | Source | Notes |
|---------:|------|-------|-----------|---------|------|--------|-----------|-----:|--------:|---------|--------|-------|
| 75 | `tib-gaeng-wetzel` | GaengW | Gaeng & Wetzel | `tib_38-Gaeng,Wetzel` | bo | en | bo-to-en | 3 | 332 | CC0 | xdxf | |
| 76 | `tib-hopkins-def-2015` | Hopkins-Def | Hopkins Definitions 2015 | `tib_05-Hopkins-Def2015` | bo | en | bo-to-en | 3 | 237 | CC0 | xdxf | subcol |
| 77 | `tib-hopkins-comment` | Hopkins-Cmt | Hopkins Comments | `tib_06-Hopkins-Comment` | bo | en | bo-to-en | 3 | 1,958 | CC0 | xdxf | subcol |
| 78 | `tib-hopkins-divisions` | Hopkins-Div | Hopkins Divisions 2015 | `tib_11-Hopkins-Divisions2015` | bo | en | bo-to-en | 3 | 185 | CC0 | xdxf | subcol |
| 79 | `tib-hopkins-divisions-tib` | Hopkins-DivT | Hopkins Divisions (Tib) 2015 | `tib_12-Hopkins-Divisions,Tib2015` | bo | bo | bo-to-bo | 3 | 178 | CC0 | xdxf | subcol |

### Priority 85-89 잔여 Hopkins 부분집합

| Priority | Slug | Short | Long Name | v1 Name | Lang | Target | Direction | Tier | Entries | License | Source | Notes |
|---------:|------|-------|-----------|---------|------|--------|-----------|-----:|--------:|---------|--------|-------|
| 85 | `tib-hopkins-examples` | Hopkins-Ex | Hopkins Examples 2015 | `tib_13-Hopkins-Examples` | bo | en | bo-to-en | 3 | 265 | CC0 | xdxf | subcol |
| 85 | `tib-hopkins-examples-tib` | Hopkins-ExT | Hopkins Examples (Tib) 2015 | `tib_14-Hopkins-Examples,Tib` | bo | bo | bo-to-bo | 3 | 265 | CC0 | xdxf | subcol |
| 86 | `tib-hopkins-synonyms-1992` | Hopkins-Syn92 | Hopkins Synonyms 1992 | `tib_16-Hopkins-Synonyms1992` | bo | en | bo-to-en | 3 | 45 | CC0 | xdxf | subcol |
| 86 | `tib-hopkins-tib-synonyms-1992` | Hopkins-TSyn92 | Hopkins Tibetan Synonyms 1992 | `tib_17-Hopkins-TibetanSynonyms1992` | bo | bo | bo-to-bo | 3 | 277 | CC0 | xdxf | subcol |
| 86 | `tib-hopkins-tib-synonyms-2015` | Hopkins-TSyn15 | Hopkins Tibetan Synonyms 2015 | `tib_17-Hopkins-TibetanSynonyms2015` | bo | bo | bo-to-bo | 3 | 177 | CC0 | xdxf | subcol |
| 87 | `tib-hopkins-tib-definitions-2015` | Hopkins-TDef | Hopkins Tibetan Definitions 2015 | `tib_18-Hopkins-TibetanDefinitions2015` | bo | bo | bo-to-bo | 3 | 234 | CC0 | xdxf | subcol |
| 87 | `tib-hopkins-tib-tenses-2015` | Hopkins-TTen | Hopkins Tibetan Tenses 2015 | `tib_19-Hopkins-TibetanTenses2015` | bo | bo | bo-to-bo | 3 | 4,846 | CC0 | xdxf | subcol |

### Priority 88-89 잔여 native Tibetan + archival

| Priority | Slug | Short | Long Name | v1 Name | Lang | Target | Direction | Tier | Entries | License | Source | Notes |
|---------:|------|-------|-----------|---------|------|--------|-----------|-----:|--------:|---------|--------|-------|
| 88 | `tib-bod-rgya-nang-don` | BodRgyaND | Bod rgya nang don rig pai tshig mdzod | `tib_54-bod_rgya_nang_don_rig_pai_tshig_mdzod` | bo | bo | bo-to-bo | 3 | 8,947 | CC0 | xdxf | native |
| 88 | `tib-brda-dkrol-gser-me-long` | BrdaDkrol | Brda dkrol gser gyi me long | `tib_55-brda_dkrol_gser_gyi_me_long` | bo | bo | bo-to-bo | 3 | 7,930 | CC0 | xdxf | native |
| 88 | `tib-chos-rnam-kun-btus` | ChosRnam | Chos rnam kun btus | `tib_56-chos_rnam_kun_btus` | bo | bo | bo-to-bo | 3 | 11,512 | CC0 | xdxf | native |
| 89 | `tib-li-shii-gur-khang` | LiShii | Li shii gur khang | `tib_57-li_shii_gur_khang` | bo | bo | bo-to-bo | 3 | 851 | CC0 | xdxf | native |
| 89 | `tib-sgom-sde-tshig-mdzod` | SgomSde | Sgom sde tshig mdzod chen mo | `tib_58-sgom_sde_tshig_mdzod_chen_mo` | bo | bo | bo-to-bo | 3 | 13,409 | CC0 | xdxf | native |
| 89 | `tib-sgra-bye-brag` | SgraByeBrag | Sgra bye brag tu rtogs byed chen mo | `tib_59-sgra_bye_brag_tu_rtogs_byed_chen_mo` | bo | bo | bo-to-bo | 3 | 11,156 | CC0 | xdxf | native |
| 89 | `tib-sangs-rgyas-chos-gzhung` | SangsRG | Sangs rgyas chos gzhung tshig mdzod | `tib_60-sngas_rgyas_chos_gzhung_tshig_mdzod` | bo | bo | bo-to-bo | 3 | 10,977 | CC0 | xdxf | native |
| 89 | `tib-gangs-can-mkhas-grub` | GangsCan | Gangs can mkhas grub rim byon ming mdzod | `tib_61-gangs_can_mkhas_grub_rim_byon_ming_mdzod` | bo | bo | bo-to-bo | 3 | 2,242 | CC0 | xdxf | native |
| 89 | `tib-sgra-sbyor-bam-po` | SgraSbyor | Sgra sbyor bam po gnyis pa | `tib_64-sgra-sbyor-bam-po-gnyis-pa` | bo | bo | bo-to-bo | 3 | 418 | CC0 | xdxf | native |
| 89 | `tib-hotl-1` | HOTL-1 | HOTL 1 | `tib_67-hotl1` | bo | en | bo-to-en | 3 | 622 | CC0 | xdxf | |
| 89 | `tib-hotl-2` | HOTL-2 | HOTL 2 | `tib_67-hotl2` | bo | en | bo-to-en | 3 | 639 | CC0 | xdxf | |
| 89 | `tib-hotl-3` | HOTL-3 | HOTL 3 | `tib_67-hotl3` | bo | en | bo-to-en | 3 | 249 | CC0 | xdxf | |
| 89 | `tib-tibetan-language-school` | TibLangSch | Tibetan Language School | `tib_68-tibetanlanguage-school` | bo | en | bo-to-en | 3 | 438 | CC0 | xdxf | |
| 89 | `tib-misc` | TibMisc | Misc | `tib_47-Misc` | bo | en | mixed | 3 | 42 | CC0 | xdxf | |
| 89 | `computer-terms-sanskrit` | CompSkt | Computer Terms (Sanskrit) | `computer-skt.apple` | skt | en | skt-to-en | 3 | 1,499 | unverified | apple_dict | domain |

---

## 통계 요약

- **총 135개 사전**
- **Sanskrit**: 78개 (57.8%)
- **Tibetan**: 65개 (48.1%, bo + sa-bo bilingual)
- **Pāli**: 1개
- **검색 포함**: 116개
- **검색 제외** (heritage-decl): 19개 — FB-5
- **역방향 en-to-skt**: 3개 — FB-8
- **Total entries**: 3,811,344

## License 분포

| License | Dicts | 배포 정책 |
|---|-----:|---|
| CC0 | 64 | public-safe |
| public-domain | 19 | public-safe |
| academic-open | 3 | public-safe with attribution |
| unverified | 49 | gitignore JSONL, local-only |

## 질문 / 결정 필요

1. **슬러그 네이밍**: `bothlingk-kurzer` 대신 `pwk` 유지 권장? (학계에서는 PW/PWK가 통용)
2. **중복 탐지**: `bod-rgya.apple`과 `apple_bod_rgya_tshig_mdzod`가 **같은 entry count 53,466** — 정말 같은 데이터인지 Phase 1.7에서 확인
3. **Priority 80-82 배치**: FB-8 역방향 사전을 80-82에 뒀는데 — 정상 검색 결과에 나타났을 때 "역방향 사전" 표시를 위해 어떤 priority 대역이 맞을지
4. **SANDIC 사전 (58-59, 62-63)**: v1 SANDIC이 이미 있는 XDXF의 대체 버전이라 중복 가능성. 둘 다 유지? 아니면 SANDIC 폐기?
5. **`tib-bod-rgya-xdxf` vs `tib-bod-rgya-tshig-mdzod`**: Apple판 중복 의심 — Phase 1.7 확인

## 승인 시 다음 단계

1. `scripts/build_meta.py` 작성 (이 테이블을 소스 데이터로 사용)
2. `data/sources/{slug}/meta.json` 135개 일괄 생성
3. verify.py로 priority 중복/gap 점검

---

**검토 완료 후 수정 필요한 행이 있으면 이 파일을 직접 수정하거나 알려주세요.**
**승인하면 이 테이블을 따라 135개 meta.json 일괄 생성합니다.**
