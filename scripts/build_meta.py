"""Generate data/sources/<slug>/meta.json for all 130 dictionaries.

Encodes the Phase 1 slug · priority · direction · license mapping confirmed
by the user. Applies duplicate merges (5 drops from the original 135):
  - bod-rgya.apple merged with apple_bod_rgya_tshig_mdzod (strict dup, identical)
  - tib_15-Hopkins-Skt2015 supersedes tib_15-Hopkins-Skt1992 (newer edition)
  - grasg_a.dict supersedes grasg_p.gretil (Grassmann, XDXF preferred)
  - mwse.sandic dropped (MW option A — aggressive merge)
  - mw-sdt.apple dropped (MW option A)

FB-8 reverse dicts moved to priority 11-13 (Apte Eng→Skt, MW Eng→Skt,
Borooah Eng→Skt). Academic canonical abbreviations kept (BHSD, MVY, DCS).

Usage: uv run python -m scripts.build_meta [--verify]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# ────────────────────────────────────────────────────────────────────
#  Source URLs (from LICENSES.md)
# ────────────────────────────────────────────────────────────────────

URL_COLOGNE = "https://www.sanskrit-lexicon.uni-koeln.de/"
URL_STEINERT = "https://github.com/christiansteinert/tibetan-dictionary"
URL_GRETIL = "http://gretil.sub.uni-goettingen.de/gretil.html"
URL_84000 = "https://84000.co/"

# Common sense separators
SEP_APTE = r";|\s-\s?\d+[a-z]?\s|\s\d+[a-z]?\.\s"
SEP_MW = r";|\s-?\d+[a-z]?\s"
SEP_DEFAULT = r";"
SEP_BHSD = r";|\s\(\d+\)\s"


# ────────────────────────────────────────────────────────────────────
#  Dictionary registry — 130 rows
# ────────────────────────────────────────────────────────────────────

# Fields (tuple form for compactness):
#   priority, slug, short_name, name, v1_name, lang, target_lang, direction,
#   tier, family, license, source_format, edition, expected_entries,
#   input_script, sense_separator, exclude_from_search, used_by, source_url, merged_from
#
# None for optional fields when unknown. `merged_from` lists v1 names that were
# merged into this canonical (tracked for audit).

DICTS: list[dict] = [
    # ═══ Priority 1-9: Sanskrit 핵심 학술 사전 ═══
    {
        "priority": 1, "slug": "apte-sanskrit-english", "short_name": "Apte",
        "name": "Apte Practical Sanskrit-English Dictionary (1890)",
        "v1_name": "aptese.dict",
        "lang": "skt", "target_lang": "en", "direction": "skt-to-en",
        "tier": 1, "family": "apte",
        "license": "public-domain", "source_format": "xdxf",
        "source_url": URL_COLOGNE + "scans/AP90Scan/",
        "edition": "1890", "expected_entries": 31750,
        "input_script": "hk", "sense_separator": SEP_APTE,
    },
    {
        "priority": 2, "slug": "monier-williams", "short_name": "MW",
        "name": "Monier-Williams Sanskrit-English Dictionary (1899)",
        "v1_name": "mwse.dict",
        "lang": "skt", "target_lang": "en", "direction": "skt-to-en",
        "tier": 1, "family": "mw",
        "license": "public-domain", "source_format": "xdxf",
        "source_url": URL_COLOGNE + "scans/MWScan/",
        "edition": "1899", "expected_entries": 223501,
        "input_script": "hk", "sense_separator": SEP_MW,
    },
    {
        "priority": 3, "slug": "macdonell", "short_name": "Macdonell",
        "name": "A Practical Sanskrit Dictionary (Macdonell, 1924)",
        "v1_name": "macdse.dict",
        "lang": "skt", "target_lang": "en", "direction": "skt-to-en",
        "tier": 1, "family": "macdonell",
        "license": "public-domain", "source_format": "xdxf",
        "source_url": URL_COLOGNE + "scans/MDScan/",
        "edition": "1924", "expected_entries": 20787,
        "input_script": "hk", "sense_separator": SEP_MW,
    },
    {
        "priority": 4, "slug": "bhsd", "short_name": "BHSD",
        "name": "Buddhist Hybrid Sanskrit Dictionary (Edgerton, 1953)",
        "v1_name": "bhsd.apple",
        "lang": "skt", "target_lang": "en", "direction": "skt-to-en",
        "tier": 1, "license": "unverified", "source_format": "apple_dict",
        "edition": "1953", "expected_entries": 17807,
        "input_script": "iast", "sense_separator": SEP_BHSD,
    },
    {
        "priority": 5, "slug": "cappeller", "short_name": "Cappeller",
        "name": "Cappeller Sanskrit-English Dictionary (1891)",
        "v1_name": "cappse.dict",
        "lang": "skt", "target_lang": "en", "direction": "skt-to-en",
        "tier": 1, "license": "public-domain", "source_format": "xdxf",
        "source_url": URL_COLOGNE + "scans/CAEScan/",
        "edition": "1891", "expected_entries": 39872,
        "input_script": "hk", "sense_separator": SEP_DEFAULT,
    },
    {
        "priority": 6, "slug": "pwk", "short_name": "PW",
        "name": "Böhtlingk — Sanskrit-Wörterbuch in kürzerer Fassung",
        "v1_name": "pwk.dict",
        "lang": "skt", "target_lang": "de", "direction": "skt-to-de",
        "tier": 1, "family": "bothlingk",
        "license": "public-domain", "source_format": "xdxf",
        "source_url": URL_COLOGNE + "scans/PWKScan/",
        "edition": "1879-1889", "expected_entries": 135776,
        "input_script": "hk", "sense_separator": SEP_DEFAULT,
    },
    {
        "priority": 7, "slug": "pwg", "short_name": "PWG",
        "name": "Böhtlingk & Roth — Sanskrit-Wörterbuch (großes Wörterbuch)",
        "v1_name": "pwg.dict",
        "lang": "skt", "target_lang": "de", "direction": "skt-to-de",
        "tier": 1, "family": "bothlingk",
        "license": "public-domain", "source_format": "xdxf",
        "source_url": URL_COLOGNE + "scans/PWGScan/",
        "edition": "1855-1875", "expected_entries": 122730,
        "input_script": "hk", "sense_separator": SEP_DEFAULT,
    },
    {
        "priority": 8, "slug": "kalpadruma", "short_name": "ŚKD",
        "name": "Śabdakalpadruma (Rādhākāntadeva)",
        "v1_name": "kalpadruma.apple",
        "lang": "skt", "target_lang": "sa", "direction": "skt-to-sa",
        "tier": 1, "license": "unverified", "source_format": "apple_dict",
        "edition": "1886", "expected_entries": 42200,
        "input_script": "devanagari", "sense_separator": SEP_DEFAULT,
    },
    {
        "priority": 9, "slug": "vacaspatyam", "short_name": "Vācaspatyam",
        "name": "Vācaspatyam (Tārānātha Tarkavācaspati)",
        "v1_name": "vacaspatyam.apple",
        "lang": "skt", "target_lang": "sa", "direction": "skt-to-sa",
        "tier": 1, "license": "unverified", "source_format": "apple_dict",
        "edition": "1873-1884", "expected_entries": 48351,
        "input_script": "devanagari", "sense_separator": SEP_DEFAULT,
    },
    # ═══ Priority 10-19: Sanskrit 보조 + 역방향 (FB-8) ═══
    {
        "priority": 10, "slug": "apte-bilingual", "short_name": "Apte-Bi",
        "name": "Apte Bilingual Sanskrit Dictionary",
        "v1_name": "apte-bi.apple",
        "lang": "skt", "target_lang": "en", "direction": "skt-to-en",
        "tier": 2, "family": "apte",
        "license": "unverified", "source_format": "apple_dict",
        "expected_entries": 122555,
        "input_script": "iast", "sense_separator": SEP_APTE,
    },
    {
        "priority": 11, "slug": "apte-english-sanskrit", "short_name": "Apte-ES",
        "name": "Apte English-Sanskrit Dictionary",
        "v1_name": "aptees.dict",
        "lang": "en", "target_lang": "skt", "direction": "en-to-skt",
        "tier": 2, "family": "apte",
        "license": "public-domain", "source_format": "xdxf",
        "source_url": URL_COLOGNE + "scans/AE/",
        "edition": "1884", "expected_entries": 11314,
        "input_script": "iast",
    },
    {
        "priority": 12, "slug": "mw-english-sanskrit", "short_name": "MW-ES",
        "name": "Monier-Williams English-Sanskrit Dictionary",
        "v1_name": "mwes.dict",
        "lang": "en", "target_lang": "skt", "direction": "en-to-skt",
        "tier": 2, "family": "mw",
        "license": "public-domain", "source_format": "xdxf",
        "source_url": URL_COLOGNE + "scans/MW72Scan/",
        "edition": "1851", "expected_entries": 32503,
        "input_script": "iast",
    },
    {
        "priority": 13, "slug": "borooah-english-sanskrit", "short_name": "Borooah",
        "name": "Borooah English-Sanskrit Dictionary",
        "v1_name": "bores.dict",
        "lang": "en", "target_lang": "skt", "direction": "en-to-skt",
        "tier": 2, "license": "public-domain", "source_format": "xdxf",
        "source_url": URL_COLOGNE + "scans/BORScan/",
        "edition": "1877-1887", "expected_entries": 24608,
        "input_script": "iast",
    },
    {
        "priority": 14, "slug": "monier-williams-1872", "short_name": "MW1872",
        "name": "Monier-Williams Sanskrit-English Dictionary (1872 edition)",
        "v1_name": "mwse72.dict",
        "lang": "skt", "target_lang": "en", "direction": "skt-to-en",
        "tier": 2, "family": "mw",
        "license": "public-domain", "source_format": "xdxf",
        "source_url": URL_COLOGNE + "scans/MW72Scan/",
        "edition": "1872", "expected_entries": 55367,
        "input_script": "hk", "sense_separator": SEP_MW,
    },
    {
        "priority": 15, "slug": "vacaspatyam-xdxf", "short_name": "Vācaspatyam-X",
        "name": "Vācaspatyam (XDXF edition)",
        "v1_name": "vcpss.dict",
        "lang": "skt", "target_lang": "sa", "direction": "skt-to-sa",
        "tier": 2, "license": "public-domain", "source_format": "xdxf",
        "source_url": URL_COLOGNE + "scans/VCPScan/",
        "expected_entries": 48370, "input_script": "devanagari",
    },
    {
        "priority": 16, "slug": "sabda-kalpa-druma", "short_name": "ŚKD-X",
        "name": "Śabda-kalpa-druma (XDXF edition)",
        "v1_name": "skdss.dict",
        "lang": "skt", "target_lang": "sa", "direction": "skt-to-sa",
        "tier": 2, "license": "public-domain", "source_format": "xdxf",
        "source_url": URL_COLOGNE + "scans/SKDScan/",
        "expected_entries": 42203, "input_script": "devanagari",
    },
    {
        "priority": 17, "slug": "benfey", "short_name": "Benfey",
        "name": "Benfey Sanskrit-English Dictionary (1866)",
        "v1_name": "benfse.dict",
        "lang": "skt", "target_lang": "en", "direction": "skt-to-en",
        "tier": 2, "license": "public-domain", "source_format": "xdxf",
        "source_url": URL_COLOGNE + "scans/BENScan/",
        "edition": "1866", "expected_entries": 17322,
        "input_script": "hk", "sense_separator": SEP_DEFAULT,
    },
    {
        "priority": 18, "slug": "amarakosa", "short_name": "Amarakośa",
        "name": "Amarakośa (Sanskrit thesaurus)",
        "v1_name": "amara.apple",
        "lang": "skt", "target_lang": "sa", "direction": "skt-to-sa",
        "tier": 2, "license": "unverified", "source_format": "apple_dict",
        "expected_entries": 3137, "input_script": "devanagari",
    },
    {
        "priority": 19, "slug": "amarakosa-context", "short_name": "Amara-Ctx",
        "name": "Amarakośa with contextual annotations",
        "v1_name": "amara-ctx.apple",
        "lang": "skt", "target_lang": "sa", "direction": "skt-to-sa",
        "tier": 2, "license": "unverified", "source_format": "apple_dict",
        "expected_entries": 3790, "input_script": "devanagari",
    },
    # ═══ Priority 20-29: Tibetan 주요 ═══
    {
        "priority": 20, "slug": "tib-rangjung-yeshe", "short_name": "RY",
        "name": "Rangjung Yeshe Tibetan-English Dictionary",
        "v1_name": "tib_02-RangjungYeshe",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 1, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 73730,
        "input_script": "wylie",
    },
    {
        "priority": 21, "slug": "tib-hopkins-2015", "short_name": "Hopkins",
        "name": "Hopkins Tibetan-English Dictionary (2015)",
        "v1_name": "tib_01-Hopkins2015",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 1, "family": "hopkins", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "edition": "2015",
        "expected_entries": 17720, "input_script": "wylie",
    },
    {
        "priority": 22, "slug": "tib-84000-dict", "short_name": "84000",
        "name": "84000 Tibetan-English Dictionary",
        "v1_name": "tib_43-84000Dict",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 1, "family": "84000", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_84000, "expected_entries": 25356,
        "input_script": "wylie",
    },
    {
        "priority": 23, "slug": "tib-tshig-mdzod-chen-mo", "short_name": "TshigMdzod",
        "name": "Tshig mdzod chen mo (native Tibetan dictionary)",
        "v1_name": "tib_25-tshig-mdzod-chen-mo-Tib",
        "lang": "bo", "target_lang": "bo", "direction": "bo-to-bo",
        "tier": 1, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 51030,
        "input_script": "wylie",
    },
    {
        "priority": 24, "slug": "tib-bod-rgya-tshig-mdzod", "short_name": "BodRgya",
        "name": "Bod rgya tshig mdzod chen mo",
        "v1_name": "bod-rgya.apple",
        "lang": "bo", "target_lang": "bo", "direction": "bo-to-bo",
        "tier": 1, "license": "unverified", "source_format": "apple_dict",
        "expected_entries": 48488, "input_script": "wylie",
        # Merged duplicates
        "merged_from": ["bod-rgya.apple", "apple_bod_rgya_tshig_mdzod"],
    },
    {
        "priority": 25, "slug": "tib-ives-waldo", "short_name": "IvesWaldo",
        "name": "Ives Waldo Tibetan-English Glossary",
        "v1_name": "tib_08-IvesWaldo",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 2, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 120946,
        "input_script": "wylie",
    },
    {
        "priority": 26, "slug": "tib-jim-valby", "short_name": "JimValby",
        "name": "Jim Valby Tibetan-English",
        "v1_name": "tib_07-JimValby",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 2, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 64221,
        "input_script": "wylie",
    },
    {
        "priority": 27, "slug": "tib-jaeschke-scan", "short_name": "Jaeschke",
        "name": "Jaeschke Tibetan-English Dictionary (Scan)",
        "v1_name": "tib_66-Jaeschke_Scan",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 2, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "edition": "1881",
        "expected_entries": 154112, "input_script": "wylie",
    },
    {
        "priority": 28, "slug": "tib-bod-yig-tshig-gter", "short_name": "BodYigGter",
        "name": "Bod yig tshig gter rgya mtsho",
        "v1_name": "tib_62-bod_yig_tshig_gter_rgya_mtsho",
        "lang": "bo", "target_lang": "bo", "direction": "bo-to-bo",
        "tier": 2, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 81935,
        "input_script": "wylie",
    },
    # ═══ Priority 30-39: Tibetan tier 2 영어 정의 ═══
    {
        "priority": 30, "slug": "tib-84000-definitions", "short_name": "84000-Def",
        "name": "84000 Definitions",
        "v1_name": "tib_44-84000Definitions",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 2, "family": "84000", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_84000, "expected_entries": 26239,
        "input_script": "wylie",
    },
    {
        "priority": 31, "slug": "tib-dan-martin", "short_name": "DanMartin",
        "name": "Dan Martin Tibetan-English",
        "v1_name": "tib_09-DanMartin",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 2, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 20196,
        "input_script": "wylie",
    },
    {
        "priority": 32, "slug": "tib-hackett-definitions", "short_name": "Hackett",
        "name": "Hackett Definitions (2015)",
        "v1_name": "tib_05-Hackett-Def2015",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 2, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "edition": "2015",
        "expected_entries": 3184, "input_script": "wylie",
    },
    {
        "priority": 33, "slug": "tib-berzin", "short_name": "Berzin",
        "name": "Berzin Tibetan-English",
        "v1_name": "tib_03-Berzin",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 2, "family": "berzin", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 1197,
        "input_script": "wylie",
    },
    {
        "priority": 34, "slug": "tib-berzin-definitions", "short_name": "Berzin-Def",
        "name": "Berzin Definitions",
        "v1_name": "tib_04-Berzin-Def",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 2, "family": "berzin", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 888,
        "input_script": "wylie",
    },
    {
        "priority": 35, "slug": "tib-richard-barron", "short_name": "Barron",
        "name": "Richard Barron Tibetan-English",
        "v1_name": "tib_10-RichardBarron",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 2, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 4742,
        "input_script": "wylie",
    },
    {
        "priority": 36, "slug": "tib-tsepak-rigdzin", "short_name": "TsepakRigdzin",
        "name": "Tsepak Rigdzin Tibetan-English",
        "v1_name": "tib_33-TsepakRigdzin",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 2, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 2695,
        "input_script": "wylie",
    },
    {
        "priority": 37, "slug": "tib-thomas-doctor", "short_name": "ThomasDoctor",
        "name": "Thomas Doctor Tibetan-English",
        "v1_name": "tib_35-ThomasDoctor",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 2, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 502,
        "input_script": "wylie",
    },
    {
        "priority": 38, "slug": "tib-gateway-to-knowledge", "short_name": "GatewayK",
        "name": "Gateway to Knowledge",
        "v1_name": "tib_23-GatewayToKnowledge",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 2, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 522,
        "input_script": "wylie",
    },
    {
        "priority": 39, "slug": "tib-common-terms-lin", "short_name": "CommonT-Lin",
        "name": "Common Terms (Lin)",
        "v1_name": "tib_40-CommonTerms-Lin",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 2, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 2325,
        "input_script": "wylie",
    },
    # ═══ Priority 40-49: Tibetan 전문 (Skt equiv + native) ═══
    {
        "priority": 40, "slug": "tib-negi-skt", "short_name": "Negi",
        "name": "Negi Tibetan-Sanskrit Dictionary",
        "v1_name": "tib_50-NegiSkt",
        "lang": "bo", "target_lang": "skt", "direction": "bo-to-skt",
        "tier": 2, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 79293,
        "input_script": "wylie",
    },
    {
        "priority": 41, "slug": "tib-lokesh-chandra-skt", "short_name": "Lokesh",
        "name": "Lokesh Chandra Sanskrit",
        "v1_name": "tib_49-LokeshChandraSkt",
        "lang": "bo", "target_lang": "skt", "direction": "bo-to-skt",
        "tier": 2, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 15961,
        "input_script": "wylie",
    },
    {
        "priority": 42, "slug": "tib-84000-skt", "short_name": "84000-Skt",
        "name": "84000 Sanskrit",
        "v1_name": "tib_46-84000Skt",
        "lang": "bo", "target_lang": "skt", "direction": "bo-to-skt",
        "tier": 2, "family": "84000", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_84000, "expected_entries": 15705,
        "input_script": "wylie",
    },
    {
        "priority": 43, "slug": "tib-hopkins-skt", "short_name": "Hopkins-Skt",
        "name": "Hopkins Sanskrit (2015, supersedes 1992)",
        "v1_name": "tib_15-Hopkins-Skt2015",
        "lang": "bo", "target_lang": "skt", "direction": "bo-to-skt",
        "tier": 2, "family": "hopkins", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "edition": "2015",
        "expected_entries": 14757, "input_script": "wylie",
        "merged_from": ["tib_15-Hopkins-Skt1992", "tib_15-Hopkins-Skt2015"],
    },
    {
        "priority": 44, "slug": "tib-mahavyutpatti-skt", "short_name": "MVY-Skt",
        "name": "Mahāvyutpatti Sanskrit (Steinert)",
        "v1_name": "tib_21-Mahavyutpatti-Skt",
        "lang": "bo", "target_lang": "skt", "direction": "bo-to-skt",
        "tier": 2, "family": "mvy", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 9586,
        "input_script": "wylie",
    },
    {
        "priority": 45, "slug": "tib-dung-dkar-tshig-mdzod", "short_name": "DungDkar",
        "name": "Dung dkar tshig mdzod chen mo (native)",
        "v1_name": "tib_34-dung-dkar-tshig-mdzod-chen-mo-Tib",
        "lang": "bo", "target_lang": "bo", "direction": "bo-to-bo",
        "tier": 2, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 13310,
        "input_script": "wylie",
    },
    {
        "priority": 46, "slug": "tib-dag-tshig-gsar-bsgrigs", "short_name": "DagTshig",
        "name": "Dag tshig gsar bsgrigs (native)",
        "v1_name": "tib_37-dag_tshig_gsar_bsgrigs-Tib",
        "lang": "bo", "target_lang": "bo", "direction": "bo-to-bo",
        "tier": 2, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 6938,
        "input_script": "wylie",
    },
    {
        "priority": 47, "slug": "tib-yogacarabhumi", "short_name": "YBh",
        "name": "Yogācārabhūmi glossary",
        "v1_name": "tib_22-Yoghacharabhumi-glossary",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 2, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 16028,
        "input_script": "wylie",
    },
    {
        "priority": 48, "slug": "tib-84000-synonyms", "short_name": "84000-Syn",
        "name": "84000 Synonyms",
        "v1_name": "tib_45-84000Synonyms",
        "lang": "bo", "target_lang": "skt", "direction": "bo-to-skt",
        "tier": 2, "family": "84000", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_84000, "expected_entries": 6029,
        "input_script": "wylie",
    },
    {
        "priority": 49, "slug": "tib-mahavyutpatti-skt-tib", "short_name": "MVY",
        "name": "Mahāvyutpatti (Skt↔Tib bilingual)",
        "v1_name": "mahavyutpatti",
        "lang": "skt", "target_lang": "bo", "direction": "mixed",
        "tier": 1, "family": "mvy", "license": "public-domain", "source_format": "xdxf",
        "expected_entries": 19069, "input_script": "iast",
    },
    # ═══ Priority 50-59: Sanskrit tier 2 유럽어 ═══
    {
        "priority": 50, "slug": "cappeller-german", "short_name": "Cappeller-G",
        "name": "Cappeller Sanskrit-Deutsch Wörterbuch",
        "v1_name": "cappsg.dict",
        "lang": "skt", "target_lang": "de", "direction": "skt-to-de",
        "tier": 2, "license": "public-domain", "source_format": "xdxf",
        "source_url": URL_COLOGNE + "scans/CAPDEU/",
        "expected_entries": 30038, "input_script": "hk",
    },
    {
        "priority": 51, "slug": "schmidt-nachtrage", "short_name": "Schmidt",
        "name": "Schmidt Nachträge zum Petersburger Wörterbuch",
        "v1_name": "schnzsw.dict",
        "lang": "skt", "target_lang": "de", "direction": "skt-to-de",
        "tier": 2, "license": "public-domain", "source_format": "xdxf",
        "source_url": URL_COLOGNE + "scans/SCHScan/",
        "expected_entries": 28751, "input_script": "hk",
    },
    {
        "priority": 52, "slug": "stchoupak", "short_name": "Stchoupak",
        "name": "Stchoupak Dictionnaire Sanskrit-Français",
        "v1_name": "stcsf.dict",
        "lang": "skt", "target_lang": "fr", "direction": "skt-to-fr",
        "tier": 2, "license": "public-domain", "source_format": "xdxf",
        "source_url": URL_COLOGNE + "scans/STCScan/",
        "expected_entries": 24574, "input_script": "hk",
    },
    {
        "priority": 53, "slug": "burnouf", "short_name": "Burnouf",
        "name": "Burnouf Dictionnaire classique Sanskrit-Français",
        "v1_name": "bursf.dict",
        "lang": "skt", "target_lang": "fr", "direction": "skt-to-fr",
        "tier": 2, "license": "public-domain", "source_format": "xdxf",
        "source_url": URL_COLOGNE + "scans/BURScan/",
        "edition": "1866", "expected_entries": 19775, "input_script": "hk",
    },
    {
        "priority": 54, "slug": "bopp-latin", "short_name": "Bopp-L",
        "name": "Bopp Sanskrit-Latin Glossarium",
        "v1_name": "boppsl.dict",
        "lang": "skt", "target_lang": "la", "direction": "skt-to-la",
        "tier": 2, "license": "public-domain", "source_format": "xdxf",
        "source_url": URL_COLOGNE + "scans/BOPScan/",
        "edition": "1847", "expected_entries": 9006, "input_script": "hk",
    },
    {
        "priority": 55, "slug": "grassmann-vedic", "short_name": "Grassmann",
        "name": "Grassmann Wörterbuch zum Rig-Veda",
        "v1_name": "grasg_a.dict",
        "lang": "skt", "target_lang": "de", "direction": "skt-to-de",
        "tier": 2, "family": "grassmann", "license": "public-domain", "source_format": "xdxf",
        "source_url": URL_COLOGNE + "scans/GRAScan/",
        "edition": "1873-1875", "expected_entries": 10778, "input_script": "hk",
        "merged_from": ["grasg_a.dict", "grasg_p.gretil"],
    },
    {
        "priority": 56, "slug": "bopp-comparative", "short_name": "Bopp-Comp",
        "name": "Bopp Comparative Grammar (Sanskrit)",
        "v1_name": "bopp.apple",
        "lang": "skt", "target_lang": "en", "direction": "skt-to-en",
        "tier": 2, "family": "bopp", "license": "unverified", "source_format": "apple_dict",
        "expected_entries": 8960, "input_script": "iast",
    },
    {
        "priority": 57, "slug": "apte-sandic", "short_name": "Apte-SD",
        "name": "Apte (SANDIC edition)",
        "v1_name": "aptese.sandic",
        "lang": "skt", "target_lang": "en", "direction": "skt-to-en",
        "tier": 3, "family": "apte", "license": "unverified", "source_format": "sandic",
        "expected_entries": 44943, "input_script": "iast",
    },
    {
        "priority": 58, "slug": "ekaksara", "short_name": "Ekākṣara",
        "name": "Ekākṣaranāmamālā (monosyllabic thesaurus)",
        "v1_name": "ekaksara.apple",
        "lang": "skt", "target_lang": "sa", "direction": "skt-to-sa",
        "tier": 3, "license": "unverified", "source_format": "apple_dict",
        "expected_entries": 391, "input_script": "devanagari",
    },
    {
        "priority": 59, "slug": "amarakosa-ontology", "short_name": "Amara-Onto",
        "name": "Amarakośa (ontology view)",
        "v1_name": "amara-onto.apple",
        "lang": "skt", "target_lang": "sa", "direction": "skt-to-sa",
        "tier": 3, "license": "unverified", "source_format": "apple_dict",
        "expected_entries": 11582, "input_script": "devanagari",
    },
    # ═══ Priority 60-69: Sanskrit 전문 grammar + Pāli ═══
    {
        "priority": 60, "slug": "pali-english", "short_name": "Pāli-En",
        "name": "Pāli-English Dictionary",
        "v1_name": "pali-en.apple",
        "lang": "pi", "target_lang": "en", "direction": "pi-to-en",
        "tier": 1, "license": "unverified", "source_format": "apple_dict",
        "expected_entries": 49000, "input_script": "iast", "sense_separator": SEP_DEFAULT,
    },
    {
        "priority": 61, "slug": "dhatupatha-sandic", "short_name": "Dhātu-SD",
        "name": "Dhātupāṭha (SANDIC)",
        "v1_name": "dhatupatha.sandic",
        "lang": "skt", "target_lang": "en", "direction": "skt-to-en",
        "tier": 2, "family": "dhatupatha", "license": "unverified", "source_format": "sandic",
        "expected_entries": 1159, "input_script": "iast",
    },
    {
        "priority": 62, "slug": "dhatupatha-krsnacarya", "short_name": "Dhātu-Kṛ",
        "name": "Dhātupāṭha (Kṛṣṇācārya commentary)",
        "v1_name": "dhatupatha-kr.apple",
        "lang": "skt", "target_lang": "sa", "direction": "skt-to-sa",
        "tier": 2, "family": "dhatupatha", "license": "unverified", "source_format": "apple_dict",
        "expected_entries": 2101, "input_script": "devanagari",
    },
    {
        "priority": 63, "slug": "dhatupatha-sa", "short_name": "Dhātu",
        "name": "Dhātupāṭha (Sanskrit plain)",
        "v1_name": "dhatupatha-sa.apple",
        "lang": "skt", "target_lang": "sa", "direction": "skt-to-sa",
        "tier": 2, "family": "dhatupatha", "license": "unverified", "source_format": "apple_dict",
        "expected_entries": 2282, "input_script": "devanagari",
    },
    {
        "priority": 64, "slug": "ashtadhyayi-english", "short_name": "Aṣṭ-En",
        "name": "Aṣṭādhyāyī (English translation)",
        "v1_name": "ashtadhyayi-en.apple",
        "lang": "skt", "target_lang": "en", "direction": "skt-to-en",
        "tier": 2, "family": "ashtadhyayi", "license": "unverified", "source_format": "apple_dict",
        "expected_entries": 3983, "input_script": "iast",
    },
    {
        "priority": 65, "slug": "ashtadhyayi-anuvrtti", "short_name": "Aṣṭ-Anv",
        "name": "Aṣṭādhyāyī (Anuvṛtti commentary)",
        "v1_name": "ashtadhyayi-anv.apple",
        "lang": "skt", "target_lang": "sa", "direction": "skt-to-sa",
        "tier": 2, "family": "ashtadhyayi", "license": "unverified", "source_format": "apple_dict",
        "expected_entries": 3983, "input_script": "devanagari",
    },
    {
        "priority": 66, "slug": "siddhanta-kaumudi", "short_name": "Siddh-K",
        "name": "Siddhānta Kaumudī",
        "v1_name": "siddh-kaumudi.apple",
        "lang": "skt", "target_lang": "sa", "direction": "skt-to-sa",
        "tier": 2, "license": "unverified", "source_format": "apple_dict",
        "expected_entries": 4815, "input_script": "devanagari",
    },
    {
        "priority": 67, "slug": "jnu-tinanta", "short_name": "JNU-Tiṅ",
        "name": "Tiṅanta (JNU Verb Database)",
        "v1_name": "jnu-tinanta.apple",
        "lang": "skt", "target_lang": "sa", "direction": "skt-to-sa",
        "tier": 2, "license": "unverified", "source_format": "apple_dict",
        "expected_entries": 5630, "input_script": "devanagari",
    },
    {
        "priority": 68, "slug": "abhyankar-grammar", "short_name": "Abhyankar",
        "name": "Abhyankar Dictionary of Sanskrit Grammar",
        "v1_name": "abhyankar.apple",
        "lang": "skt", "target_lang": "en", "direction": "skt-to-en",
        "tier": 2, "license": "unverified", "source_format": "apple_dict",
        "expected_entries": 4350, "input_script": "iast",
    },
    {
        "priority": 69, "slug": "chandas-prosody", "short_name": "Chandas",
        "name": "Chandas (Sanskrit Prosody)",
        "v1_name": "chandas.apple",
        "lang": "skt", "target_lang": "sa", "direction": "skt-to-sa",
        "tier": 2, "license": "unverified", "source_format": "apple_dict",
        "expected_entries": 1199, "input_script": "devanagari",
    },
    # ═══ Priority 70-79: Tibetan tier 3 + Hopkins subcollections ═══
    {
        "priority": 70, "slug": "tib-chandra-das-scan", "short_name": "ChandraDas",
        "name": "Chandra Das Tibetan-English (Scan)",
        "v1_name": "tib_65-ChandraDas_Scan",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 3, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "edition": "1902",
        "expected_entries": 20773, "input_script": "wylie",
    },
    {
        "priority": 71, "slug": "tib-hopkins-others-english", "short_name": "Hopkins-OE",
        "name": "Hopkins (others, English) 2015",
        "v1_name": "tib_20-Hopkins-others'English2015",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 3, "family": "hopkins", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "edition": "2015",
        "expected_entries": 6511, "input_script": "wylie",
    },
    {
        "priority": 72, "slug": "tib-itlr", "short_name": "ITLR",
        "name": "ITLR (International Tibetan Literature Resources)",
        "v1_name": "tib_52-ITLR",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 3, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 5654,
        "input_script": "wylie",
    },
    {
        "priority": 73, "slug": "tib-computer-terms", "short_name": "CompTerms",
        "name": "Computer Terms (Tibetan)",
        "v1_name": "tib_36-ComputerTerms",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 3, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 5683,
        "input_script": "wylie",
    },
    {
        "priority": 74, "slug": "tib-mahavyutpatti-scan-1989", "short_name": "MVY-Scan",
        "name": "Mahāvyutpatti (Scan 1989)",
        "v1_name": "tib_63-Mahavyutpatti-Scan-1989",
        "lang": "bo", "target_lang": "skt", "direction": "mixed",
        "tier": 3, "family": "mvy", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "edition": "1989",
        "expected_entries": 9583, "input_script": "wylie",
    },
    {
        "priority": 75, "slug": "tib-tibterm-project", "short_name": "TibTerm",
        "name": "TibTerm Project",
        "v1_name": "tib_48-TibTermProject",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 3, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 7965,
        "input_script": "wylie",
    },
    {
        "priority": 76, "slug": "tib-laine-abbreviations", "short_name": "Laine",
        "name": "Laine Abbreviations",
        "v1_name": "tib_51-LaineAbbreviations",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 3, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 7468,
        "input_script": "wylie",
    },
    {
        "priority": 77, "slug": "tib-verbinator", "short_name": "Verbinator",
        "name": "Verbinator (Tibetan verb paradigms)",
        "v1_name": "tib_26-Verbinator",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 3, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 4330,
        "input_script": "wylie",
    },
    {
        "priority": 78, "slug": "tib-sera-textbook", "short_name": "Sera",
        "name": "Sera Textbook Definitions",
        "v1_name": "tib_42-Sera-Textbook-Definitions",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 3, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 1223,
        "input_script": "wylie",
    },
    {
        "priority": 79, "slug": "tib-bialek", "short_name": "Bialek",
        "name": "Bialek Tibetan-English",
        "v1_name": "tib_53-Bialek",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 3, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 2145,
        "input_script": "wylie",
    },
    # ═══ Priority 80-89: archival + Vedic + Hopkins 부분집합 + native Tibetan ═══
    {
        "priority": 80, "slug": "bloomfield-vedic-concordance", "short_name": "Bloomfield",
        "name": "Bloomfield Vedic Concordance",
        "v1_name": "bloomfield.apple",
        "lang": "skt", "target_lang": "en", "direction": "skt-to-en",
        "tier": 3, "family": "vedconc", "license": "unverified", "source_format": "apple_dict",
        "expected_entries": 88837, "input_script": "iast",
    },
    {
        "priority": 81, "slug": "vedic-concordance-gretil", "short_name": "VedConc",
        "name": "Vedic Concordance (GRETIL)",
        "v1_name": "vedconc.gretil",
        "lang": "skt", "target_lang": "en", "direction": "skt-to-en",
        "tier": 3, "family": "vedconc", "license": "academic-open", "source_format": "gretil",
        "source_url": URL_GRETIL, "expected_entries": 80654, "input_script": "hk",
    },
    {
        "priority": 82, "slug": "vedic-rituals-hillebrandt", "short_name": "VedRit",
        "name": "Vedic Rituals (Hillebrandt)",
        "v1_name": "vedic-rituals.apple",
        "lang": "skt", "target_lang": "en", "direction": "skt-to-en",
        "tier": 3, "license": "unverified", "source_format": "apple_dict",
        "expected_entries": 6176, "input_script": "iast",
    },
    {
        "priority": 83, "slug": "puranic-encyclopaedia", "short_name": "PurEnc",
        "name": "Purāṇic Encyclopaedia (Vettam Mani)",
        "v1_name": "pese.gretil",
        "lang": "skt", "target_lang": "en", "direction": "skt-to-en",
        "tier": 3, "license": "academic-open", "source_format": "gretil",
        "source_url": URL_GRETIL, "expected_entries": 8832, "input_script": "iast",
    },
    {
        "priority": 84, "slug": "dcs-frequency", "short_name": "DCS",
        "name": "DCS (Digital Corpus of Sanskrit) Word Frequency",
        "v1_name": "dcs-freq.apple",
        "lang": "skt", "target_lang": "en", "direction": "skt-to-en",
        "tier": 3, "license": "unverified", "source_format": "apple_dict",
        "expected_entries": 72804, "input_script": "iast",
    },
    {
        "priority": 85, "slug": "tib-hopkins-examples", "short_name": "Hopkins-Ex",
        "name": "Hopkins Examples 2015",
        "v1_name": "tib_13-Hopkins-Examples",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 3, "family": "hopkins", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "edition": "2015",
        "expected_entries": 265, "input_script": "wylie",
    },
    {
        "priority": 85, "slug": "tib-hopkins-examples-tib", "short_name": "Hopkins-ExT",
        "name": "Hopkins Examples (Tibetan) 2015",
        "v1_name": "tib_14-Hopkins-Examples,Tib",
        "lang": "bo", "target_lang": "bo", "direction": "bo-to-bo",
        "tier": 3, "family": "hopkins", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "edition": "2015",
        "expected_entries": 265, "input_script": "wylie",
    },
    {
        "priority": 85, "slug": "tib-hopkins-comment", "short_name": "Hopkins-Cmt",
        "name": "Hopkins Comments",
        "v1_name": "tib_06-Hopkins-Comment",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 3, "family": "hopkins", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 1958, "input_script": "wylie",
    },
    {
        "priority": 85, "slug": "tib-hopkins-divisions", "short_name": "Hopkins-Div",
        "name": "Hopkins Divisions 2015",
        "v1_name": "tib_11-Hopkins-Divisions2015",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 3, "family": "hopkins", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "edition": "2015",
        "expected_entries": 185, "input_script": "wylie",
    },
    {
        "priority": 85, "slug": "tib-hopkins-divisions-tib", "short_name": "Hopkins-DivT",
        "name": "Hopkins Divisions (Tibetan) 2015",
        "v1_name": "tib_12-Hopkins-Divisions,Tib2015",
        "lang": "bo", "target_lang": "bo", "direction": "bo-to-bo",
        "tier": 3, "family": "hopkins", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "edition": "2015",
        "expected_entries": 178, "input_script": "wylie",
    },
    {
        "priority": 86, "slug": "tib-hopkins-synonyms-1992", "short_name": "Hopkins-Syn92",
        "name": "Hopkins Synonyms 1992",
        "v1_name": "tib_16-Hopkins-Synonyms1992",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 3, "family": "hopkins", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "edition": "1992",
        "expected_entries": 45, "input_script": "wylie",
    },
    {
        "priority": 86, "slug": "tib-hopkins-tib-synonyms-1992", "short_name": "Hopkins-TSyn92",
        "name": "Hopkins Tibetan Synonyms 1992",
        "v1_name": "tib_17-Hopkins-TibetanSynonyms1992",
        "lang": "bo", "target_lang": "bo", "direction": "bo-to-bo",
        "tier": 3, "family": "hopkins", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "edition": "1992",
        "expected_entries": 277, "input_script": "wylie",
    },
    {
        "priority": 86, "slug": "tib-hopkins-tib-synonyms-2015", "short_name": "Hopkins-TSyn15",
        "name": "Hopkins Tibetan Synonyms 2015",
        "v1_name": "tib_17-Hopkins-TibetanSynonyms2015",
        "lang": "bo", "target_lang": "bo", "direction": "bo-to-bo",
        "tier": 3, "family": "hopkins", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "edition": "2015",
        "expected_entries": 177, "input_script": "wylie",
    },
    {
        "priority": 87, "slug": "tib-hopkins-tib-definitions-2015", "short_name": "Hopkins-TDef",
        "name": "Hopkins Tibetan Definitions 2015",
        "v1_name": "tib_18-Hopkins-TibetanDefinitions2015",
        "lang": "bo", "target_lang": "bo", "direction": "bo-to-bo",
        "tier": 3, "family": "hopkins", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "edition": "2015",
        "expected_entries": 234, "input_script": "wylie",
    },
    {
        "priority": 87, "slug": "tib-hopkins-tib-tenses-2015", "short_name": "Hopkins-TTen",
        "name": "Hopkins Tibetan Tenses 2015",
        "v1_name": "tib_19-Hopkins-TibetanTenses2015",
        "lang": "bo", "target_lang": "bo", "direction": "bo-to-bo",
        "tier": 3, "family": "hopkins", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "edition": "2015",
        "expected_entries": 4846, "input_script": "wylie",
    },
    {
        "priority": 88, "slug": "tib-bod-rgya-nang-don", "short_name": "BodRgyaND",
        "name": "Bod rgya nang don rig pai tshig mdzod",
        "v1_name": "tib_54-bod_rgya_nang_don_rig_pai_tshig_mdzod",
        "lang": "bo", "target_lang": "bo", "direction": "bo-to-bo",
        "tier": 3, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 8947, "input_script": "wylie",
    },
    {
        "priority": 88, "slug": "tib-brda-dkrol-gser-me-long", "short_name": "BrdaDkrol",
        "name": "Brda dkrol gser gyi me long",
        "v1_name": "tib_55-brda_dkrol_gser_gyi_me_long",
        "lang": "bo", "target_lang": "bo", "direction": "bo-to-bo",
        "tier": 3, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 7930, "input_script": "wylie",
    },
    {
        "priority": 88, "slug": "tib-chos-rnam-kun-btus", "short_name": "ChosRnam",
        "name": "Chos rnam kun btus",
        "v1_name": "tib_56-chos_rnam_kun_btus",
        "lang": "bo", "target_lang": "bo", "direction": "bo-to-bo",
        "tier": 3, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 11512, "input_script": "wylie",
    },
    {
        "priority": 89, "slug": "tib-li-shii-gur-khang", "short_name": "LiShii",
        "name": "Li shii gur khang",
        "v1_name": "tib_57-li_shii_gur_khang",
        "lang": "bo", "target_lang": "bo", "direction": "bo-to-bo",
        "tier": 3, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 851, "input_script": "wylie",
    },
    {
        "priority": 89, "slug": "tib-sgom-sde-tshig-mdzod", "short_name": "SgomSde",
        "name": "Sgom sde tshig mdzod chen mo",
        "v1_name": "tib_58-sgom_sde_tshig_mdzod_chen_mo",
        "lang": "bo", "target_lang": "bo", "direction": "bo-to-bo",
        "tier": 3, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 13409, "input_script": "wylie",
    },
    {
        "priority": 89, "slug": "tib-sgra-bye-brag", "short_name": "SgraByeBrag",
        "name": "Sgra bye brag tu rtogs byed chen mo",
        "v1_name": "tib_59-sgra_bye_brag_tu_rtogs_byed_chen_mo",
        "lang": "bo", "target_lang": "bo", "direction": "bo-to-bo",
        "tier": 3, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 11156, "input_script": "wylie",
    },
    {
        "priority": 89, "slug": "tib-sangs-rgyas-chos-gzhung", "short_name": "SangsRG",
        "name": "Sangs rgyas chos gzhung tshig mdzod",
        "v1_name": "tib_60-sngas_rgyas_chos_gzhung_tshig_mdzod",
        "lang": "bo", "target_lang": "bo", "direction": "bo-to-bo",
        "tier": 3, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 10977, "input_script": "wylie",
    },
    {
        "priority": 89, "slug": "tib-gangs-can-mkhas-grub", "short_name": "GangsCan",
        "name": "Gangs can mkhas grub rim byon ming mdzod",
        "v1_name": "tib_61-gangs_can_mkhas_grub_rim_byon_ming_mdzod",
        "lang": "bo", "target_lang": "bo", "direction": "bo-to-bo",
        "tier": 3, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 2242, "input_script": "wylie",
    },
    {
        "priority": 89, "slug": "tib-sgra-sbyor-bam-po", "short_name": "SgraSbyor",
        "name": "Sgra sbyor bam po gnyis pa",
        "v1_name": "tib_64-sgra-sbyor-bam-po-gnyis-pa",
        "lang": "bo", "target_lang": "bo", "direction": "bo-to-bo",
        "tier": 3, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 418, "input_script": "wylie",
    },
    {
        "priority": 89, "slug": "tib-hotl-1", "short_name": "HOTL-1",
        "name": "HOTL 1 (History of Tibet, vol. 1)",
        "v1_name": "tib_67-hotl1",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 3, "family": "hotl", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 622, "input_script": "wylie",
    },
    {
        "priority": 89, "slug": "tib-hotl-2", "short_name": "HOTL-2",
        "name": "HOTL 2",
        "v1_name": "tib_67-hotl2",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 3, "family": "hotl", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 639, "input_script": "wylie",
    },
    {
        "priority": 89, "slug": "tib-hotl-3", "short_name": "HOTL-3",
        "name": "HOTL 3",
        "v1_name": "tib_67-hotl3",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 3, "family": "hotl", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 249, "input_script": "wylie",
    },
    {
        "priority": 89, "slug": "tib-tibetan-language-school", "short_name": "TibLangSch",
        "name": "Tibetan Language School",
        "v1_name": "tib_68-tibetanlanguage-school",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 3, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 438, "input_script": "wylie",
    },
    {
        "priority": 89, "slug": "tib-gaeng-wetzel", "short_name": "GaengW",
        "name": "Gaeng & Wetzel Tibetan Glossary",
        "v1_name": "tib_38-Gaeng,Wetzel",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 3, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 332, "input_script": "wylie",
    },
    {
        "priority": 89, "slug": "tib-hopkins-def-2015", "short_name": "Hopkins-Def",
        "name": "Hopkins Definitions 2015",
        "v1_name": "tib_05-Hopkins-Def2015",
        "lang": "bo", "target_lang": "en", "direction": "bo-to-en",
        "tier": 3, "family": "hopkins", "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "edition": "2015",
        "expected_entries": 237, "input_script": "wylie",
    },
    {
        "priority": 89, "slug": "tib-misc", "short_name": "TibMisc",
        "name": "Tibetan Miscellaneous",
        "v1_name": "tib_47-Misc",
        "lang": "bo", "target_lang": "en", "direction": "mixed",
        "tier": 3, "license": "CC0", "source_format": "xdxf",
        "source_url": URL_STEINERT, "expected_entries": 42, "input_script": "wylie",
    },
    {
        "priority": 89, "slug": "computer-terms-sanskrit", "short_name": "CompSkt",
        "name": "Computer Terms (Sanskrit)",
        "v1_name": "computer-skt.apple",
        "lang": "skt", "target_lang": "en", "direction": "skt-to-en",
        "tier": 3, "license": "unverified", "source_format": "apple_dict",
        "expected_entries": 1499, "input_script": "iast",
    },
    {
        "priority": 89, "slug": "macdonell-sandic", "short_name": "Macdonell-SD",
        "name": "Macdonell (SANDIC edition)",
        "v1_name": "macdse.sandic",
        "lang": "skt", "target_lang": "en", "direction": "skt-to-en",
        "tier": 3, "family": "macdonell", "license": "unverified", "source_format": "sandic",
        "expected_entries": 17679, "input_script": "iast",
    },
    # ═══ Priority 90-99: Heritage Declension — exclude_from_search = true (FB-5) ═══
    # Series A san→eng (10 volumes)
    *[
        {
            "priority": 90, "slug": f"decl-a{i:02d}", "short_name": f"Decl-A{i:02d}",
            "name": f"Heritage Declension A-{i:02d} (Sanskrit → English)",
            "v1_name": f"decl-a{i:02d}.apple",
            "lang": "skt", "target_lang": "en", "direction": "skt-to-en",
            "tier": 3, "family": "heritage-decl", "license": "unverified",
            "source_format": "apple_dict",
            "expected_entries": n, "input_script": "iast",
            "exclude_from_search": True, "used_by": "declension-tab",
        }
        for i, n in enumerate(
            [30299, 30234, 30080, 29980, 30262, 29983, 30734, 30469, 30651, 18277],
            start=1,
        )
    ],
    # Series A san→san (5 volumes)
    *[
        {
            "priority": 91, "slug": f"decl-a{i}-ss", "short_name": f"Decl-A{i}-SS",
            "name": f"Heritage Declension A-{i} (Sanskrit → Sanskrit)",
            "v1_name": f"decl-a{i}-ss.apple",
            "lang": "skt", "target_lang": "sa", "direction": "skt-to-sa",
            "tier": 3, "family": "heritage-decl", "license": "unverified",
            "source_format": "apple_dict",
            "expected_entries": n, "input_script": "iast",
            "exclude_from_search": True, "used_by": "declension-tab",
        }
        for i, n in enumerate(
            [60260, 59905, 60082, 60407, 51513],
            start=1,
        )
    ],
    # Series B
    {
        "priority": 92, "slug": "decl-b1", "short_name": "Decl-B1",
        "name": "Heritage Declension B-1 (Sanskrit → English)",
        "v1_name": "decl-b1.apple",
        "lang": "skt", "target_lang": "en", "direction": "skt-to-en",
        "tier": 3, "family": "heritage-decl", "license": "unverified", "source_format": "apple_dict",
        "expected_entries": 30181, "input_script": "iast",
        "exclude_from_search": True, "used_by": "declension-tab",
    },
    {
        "priority": 92, "slug": "decl-b2", "short_name": "Decl-B2",
        "name": "Heritage Declension B-2 (Sanskrit → English)",
        "v1_name": "decl-b2.apple",
        "lang": "skt", "target_lang": "en", "direction": "skt-to-en",
        "tier": 3, "family": "heritage-decl", "license": "unverified", "source_format": "apple_dict",
        "expected_entries": 30242, "input_script": "iast",
        "exclude_from_search": True, "used_by": "declension-tab",
    },
    {
        "priority": 92, "slug": "decl-b3", "short_name": "Decl-B3",
        "name": "Heritage Declension B-3 (Sanskrit → English)",
        "v1_name": "decl-b3.apple",
        "lang": "skt", "target_lang": "en", "direction": "skt-to-en",
        "tier": 3, "family": "heritage-decl", "license": "unverified", "source_format": "apple_dict",
        "expected_entries": 6381, "input_script": "iast",
        "exclude_from_search": True, "used_by": "declension-tab",
    },
    {
        "priority": 92, "slug": "decl-b-ss", "short_name": "Decl-B-SS",
        "name": "Heritage Declension B (Sanskrit → Sanskrit)",
        "v1_name": "decl-b-ss.apple",
        "lang": "skt", "target_lang": "sa", "direction": "skt-to-sa",
        "tier": 3, "family": "heritage-decl", "license": "unverified", "source_format": "apple_dict",
        "expected_entries": 80866, "input_script": "iast",
        "exclude_from_search": True, "used_by": "declension-tab",
    },
]


# ────────────────────────────────────────────────────────────────────
#  Generation + validation
# ────────────────────────────────────────────────────────────────────

META_REQUIRED = {
    "slug", "name", "short_name", "v1_name",
    "lang", "target_lang", "direction",
    "priority", "tier", "license", "source_format",
}
META_OPTIONAL = {
    "family", "source_url", "edition", "import_script",
    "expected_entries", "input_script", "sense_separator",
    "exclude_from_search", "used_by", "merged_from",
}


def sanitize(meta: dict) -> dict:
    """Drop None/empty values and emit deterministic key order."""
    out: dict = {}
    # Required fields first, in fixed order for readable JSON
    order = [
        "slug", "name", "short_name", "v1_name", "family",
        "lang", "target_lang", "direction",
        "priority", "tier",
        "license", "source_format", "source_url", "edition",
        "expected_entries", "input_script", "sense_separator",
        "exclude_from_search", "used_by", "merged_from",
    ]
    for key in order:
        if key in meta and meta[key] is not None and meta[key] != "":
            out[key] = meta[key]
    return out


def validate(dicts: list[dict]) -> list[str]:
    """Return list of validation errors. Empty = OK."""
    errors: list[str] = []
    slugs = [d["slug"] for d in dicts]
    v1_names = [d["v1_name"] for d in dicts if "v1_name" in d]

    # Uniqueness
    if len(slugs) != len(set(slugs)):
        dups = [s for s in slugs if slugs.count(s) > 1]
        errors.append(f"Duplicate slugs: {set(dups)}")
    if len(v1_names) != len(set(v1_names)):
        # merged_from entries legitimately collapse multiple v1 names into one
        seen = set()
        for d in dicts:
            name = d.get("v1_name")
            if name is None:
                continue
            if name in seen:
                errors.append(f"v1_name used twice (should merge): {name}")
            seen.add(name)

    # Priority range
    for d in dicts:
        p = d.get("priority")
        if not isinstance(p, int) or not (1 <= p <= 100):
            errors.append(f"{d['slug']}: priority out of range: {p}")

    # Required fields
    for d in dicts:
        missing = META_REQUIRED - set(d.keys())
        if missing:
            errors.append(f"{d['slug']}: missing required fields: {missing}")
        unknown = set(d.keys()) - META_REQUIRED - META_OPTIONAL
        if unknown:
            errors.append(f"{d['slug']}: unknown fields: {unknown}")

    # exclude_from_search must be paired with used_by
    for d in dicts:
        if d.get("exclude_from_search") and "used_by" not in d:
            errors.append(f"{d['slug']}: exclude_from_search=true without used_by")

    return errors


def write_all(dicts: list[dict], out_root: Path) -> list[Path]:
    paths: list[Path] = []
    for d in dicts:
        out_dir = out_root / d["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "meta.json"
        out_file.write_text(
            json.dumps(sanitize(d), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        paths.append(out_file)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("data/sources"))
    parser.add_argument("--check-only", action="store_true", help="Validate only, don't write.")
    args = parser.parse_args()

    errors = validate(DICTS)
    if errors:
        print("Validation errors:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"Validation OK. {len(DICTS)} dictionaries.")

    # Distribution by priority band
    bands: dict[int, int] = {}
    for d in DICTS:
        band = (d["priority"] - 1) // 10
        bands[band] = bands.get(band, 0) + 1
    print("\nPriority distribution:")
    for band in sorted(bands):
        lo, hi = band * 10 + 1, band * 10 + 10
        print(f"  [{lo:2d}-{hi:2d}] {bands[band]:3d} dicts")

    excluded = sum(1 for d in DICTS if d.get("exclude_from_search"))
    print(f"\nExcluded from search (FB-5): {excluded}")
    reverse = sum(1 for d in DICTS if d["direction"].startswith("en-to-"))
    print(f"Reverse Eng→Skt (FB-8): {reverse}")

    if args.check_only:
        return 0

    args.out.mkdir(parents=True, exist_ok=True)
    paths = write_all(DICTS, args.out)
    print(f"\n✓ Wrote {len(paths)} meta.json files under {args.out}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
