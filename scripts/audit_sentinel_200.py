"""Sentinel 200 — expanded auto-eval (Phase 3.7 follow-up Option C).

Strict superset of `audit_sentinel_50.py`. The 50 originals are reused
verbatim (same numbering); 150 additional queries cover mid/long-tail
Sanskrit terms, broader Tibetan, deeper EN/KO/ZH glosses, cross-channel
flow, and real philosophical phrases. Together they give a more
statistically meaningful coverage signal than the 50-query draft.

Output:
  data/reports/audit-2026-04-30/audit-C-sentinel200-results.csv
  data/reports/audit-2026-04-30/audit-C-sentinel200-summary.md

Usage:
  uv run python -m scripts.audit_sentinel_200
"""
from __future__ import annotations

import csv
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import msgpack
import zstandard as zstd

ROOT = Path(__file__).resolve().parent.parent
INDICES = ROOT / "public" / "indices"
OUT_CSV = ROOT / "data" / "reports" / "audit-2026-04-30" / "audit-C-sentinel200-results.csv"
OUT_MD = ROOT / "data" / "reports" / "audit-2026-04-30" / "audit-C-sentinel200-summary.md"


@dataclass
class Query:
    n: int
    text: str
    category: str
    channel: str
    expected: list[str] = field(default_factory=list)


# ─── Section 1: 50 original (Sentinel 50) ─────────────────────────
QUERIES: list[Query] = [
    # 1. SA core (10)
    Query(1, "dharma", "skt-core", "skt", ["dharma"]),
    Query(2, "ātman", "skt-core", "skt", ["ātman"]),
    Query(3, "karman", "skt-core", "skt", ["karman"]),
    Query(4, "agni", "skt-core", "skt", ["agni"]),
    Query(5, "prajñā", "skt-core", "skt", ["prajñā"]),
    Query(6, "śūnyatā", "skt-core", "skt", ["śūnyatā"]),
    Query(7, "bodhicitta", "skt-core", "skt", ["bodhicitta"]),
    Query(8, "tathāgata", "skt-core", "skt", ["tathāgata"]),
    Query(9, "mokṣa", "skt-core", "skt", ["mokṣa"]),
    Query(10, "saṃskāra", "skt-core", "skt", ["saṃskāra"]),
    # 2. Prefix (5)
    Query(11, "dha", "prefix", "prefix", ["dharma", "dhātu", "dhana"]),
    Query(12, "bud", "prefix", "prefix", ["buddha", "buddhi"]),
    Query(13, "pra", "prefix", "prefix", ["prajñā", "pratyaya"]),
    Query(14, "ana", "prefix", "prefix", ["anātman", "anitya", "ānanda"]),
    Query(15, "mahā", "prefix", "prefix", ["mahābhārata", "mahāyāna", "mahātman"]),
    # 3. Wylie (5)
    Query(16, "chos", "bo-wylie", "bo", ["chos"]),
    Query(17, "byang chub sems dpa'", "bo-wylie", "bo", ["byang chub sems dpa'", "bodhisattva"]),
    Query(18, "klong chen", "bo-wylie", "bo", ["klong chen"]),
    Query(19, "rdo rje", "bo-wylie", "bo", ["rdo rje", "vajra"]),
    Query(20, "'jam dpal", "bo-wylie", "bo", ["'jam dpal", "mañjuśrī"]),
    # 4. EN reverse (10)
    Query(21, "fire", "en-reverse", "en", ["agni"]),
    Query(22, "wisdom", "en-reverse", "en", ["prajñā", "jñāna", "buddhi"]),
    Query(23, "compassion", "en-reverse", "en", ["karuṇā", "anukampā", "dayā"]),
    Query(24, "emptiness", "en-reverse", "en", ["śūnyatā", "śūnya"]),
    Query(25, "liberation", "en-reverse", "en", ["mokṣa", "mukti"]),
    Query(26, "meditation", "en-reverse", "en", ["dhyāna", "samādhi"]),
    Query(27, "enlightenment", "en-reverse", "en", ["bodhi", "sambodhi"]),
    Query(28, "suffering", "en-reverse", "en", ["duḥkha"]),
    Query(29, "consciousness", "en-reverse", "en", ["vijñāna", "citta"]),
    Query(30, "righteousness", "en-reverse", "en", ["dharma"]),
    # 5. KO reverse (5)
    Query(31, "법", "ko-reverse", "ko", ["dharma"]),
    Query(32, "자비", "ko-reverse", "ko", ["karuṇā", "maitrī"]),
    Query(33, "지혜", "ko-reverse", "ko", ["prajñā", "jñāna"]),
    Query(34, "도", "ko-reverse", "ko", ["mārga", "panthan"]),
    Query(35, "불", "ko-reverse", "ko", ["agni", "buddha"]),
    # 6. ZH reverse (5)
    Query(36, "法", "zh-reverse", "zh", ["dharma"]),
    Query(37, "空", "zh-reverse", "zh", ["śūnyatā", "śūnya"]),
    Query(38, "菩薩", "zh-reverse", "zh", ["bodhisattva"]),
    Query(39, "涅槃", "zh-reverse", "zh", ["nirvāṇa"]),
    Query(40, "如來", "zh-reverse", "zh", ["tathāgata"]),
    # 7. Edge (5)
    Query(41, "mahābhārata", "edge", "skt", ["mahābhārata"]),
    Query(42, "jagannātha", "edge", "skt", ["jagannātha"]),
    Query(43, "tat tvam asi", "edge", "skt", ["tat", "tvam", "asi"]),
    Query(44, "oṃ", "edge", "skt", ["oṃ", "om"]),
    Query(45, "aham brahmāsmi", "edge", "skt", ["aham", "brahman", "asmi"]),
    # 8. Typo (3)
    Query(46, "dharmaaa", "typo", "edge", []),
    Query(47, "aaa", "typo", "edge", []),
    Query(48, "   ", "typo", "edge", []),
    # 9. Dead-zone (2)
    Query(49, "decl-a01", "dead-zone", "edge", []),
    Query(50, "aṃśanīya@aṃś", "dead-zone", "edge", []),

    # ─── Section 2: SA mid-freq (30) ───────────────────────────────
    Query(51, "veda", "skt-mid", "skt", ["veda"]),
    Query(52, "upaniṣad", "skt-mid", "skt", ["upaniṣad"]),
    Query(53, "brahman", "skt-mid", "skt", ["brahman"]),
    Query(54, "yoga", "skt-mid", "skt", ["yoga"]),
    Query(55, "indra", "skt-mid", "skt", ["indra"]),
    Query(56, "viṣṇu", "skt-mid", "skt", ["viṣṇu"]),
    Query(57, "śiva", "skt-mid", "skt", ["śiva"]),
    Query(58, "sūrya", "skt-mid", "skt", ["sūrya"]),
    Query(59, "candra", "skt-mid", "skt", ["candra"]),
    Query(60, "soma", "skt-mid", "skt", ["soma"]),
    Query(61, "nirvāṇa", "skt-mid", "skt", ["nirvāṇa"]),
    Query(62, "bodhi", "skt-mid", "skt", ["bodhi"]),
    Query(63, "saṃsāra", "skt-mid", "skt", ["saṃsāra"]),
    Query(64, "māyā", "skt-mid", "skt", ["māyā"]),
    Query(65, "kāma", "skt-mid", "skt", ["kāma"]),
    Query(66, "kalpa", "skt-mid", "skt", ["kalpa"]),
    Query(67, "tantra", "skt-mid", "skt", ["tantra"]),
    Query(68, "mantra", "skt-mid", "skt", ["mantra"]),
    Query(69, "vajra", "skt-mid", "skt", ["vajra"]),
    Query(70, "mudrā", "skt-mid", "skt", ["mudrā"]),
    Query(71, "guru", "skt-mid", "skt", ["guru"]),
    Query(72, "śiṣya", "skt-mid", "skt", ["śiṣya"]),
    Query(73, "ahiṃsā", "skt-mid", "skt", ["ahiṃsā"]),
    Query(74, "satya", "skt-mid", "skt", ["satya"]),
    Query(75, "puruṣa", "skt-mid", "skt", ["puruṣa"]),
    Query(76, "prakṛti", "skt-mid", "skt", ["prakṛti"]),
    Query(77, "kuṇḍalinī", "skt-mid", "skt", ["kuṇḍalinī"]),
    Query(78, "cakra", "skt-mid", "skt", ["cakra"]),
    Query(79, "rāma", "skt-mid", "skt", ["rāma"]),
    Query(80, "kṛṣṇa", "skt-mid", "skt", ["kṛṣṇa"]),

    # ─── Section 3: SA long-tail (20) ──────────────────────────────
    Query(81, "vipaśyanā", "skt-long", "skt", ["vipaśyanā", "vipassanā"]),
    Query(82, "abhidharma", "skt-long", "skt", ["abhidharma"]),
    Query(83, "śīla", "skt-long", "skt", ["śīla"]),
    Query(84, "dāna", "skt-long", "skt", ["dāna"]),
    Query(85, "kṣānti", "skt-long", "skt", ["kṣānti"]),
    Query(86, "vīrya", "skt-long", "skt", ["vīrya"]),
    Query(87, "smṛti", "skt-long", "skt", ["smṛti"]),
    Query(88, "śraddhā", "skt-long", "skt", ["śraddhā"]),
    Query(89, "vairāgya", "skt-long", "skt", ["vairāgya"]),
    Query(90, "viveka", "skt-long", "skt", ["viveka"]),
    Query(91, "trsnā", "skt-long", "skt", ["tṛṣṇā"]),
    Query(92, "upādāna", "skt-long", "skt", ["upādāna"]),
    Query(93, "avidyā", "skt-long", "skt", ["avidyā"]),
    Query(94, "anitya", "skt-long", "skt", ["anitya"]),
    Query(95, "anātman", "skt-long", "skt", ["anātman"]),
    Query(96, "skandha", "skt-long", "skt", ["skandha"]),
    Query(97, "rūpa", "skt-long", "skt", ["rūpa"]),
    Query(98, "vedanā", "skt-long", "skt", ["vedanā"]),
    Query(99, "saṃjñā", "skt-long", "skt", ["saṃjñā"]),
    Query(100, "vijñāna", "skt-long", "skt", ["vijñāna"]),

    # ─── Section 4: more EN reverse (15) ───────────────────────────
    Query(101, "moon", "en-reverse", "en", ["candra", "soma", "indu"]),
    Query(102, "sun", "en-reverse", "en", ["sūrya", "āditya"]),
    Query(103, "earth", "en-reverse", "en", ["pṛthivī", "bhūmi"]),
    Query(104, "water", "en-reverse", "en", ["jala", "ap", "ambu"]),
    Query(105, "wind", "en-reverse", "en", ["vāyu", "anila"]),
    Query(106, "death", "en-reverse", "en", ["mṛtyu", "yama", "māraṇa"]),
    Query(107, "love", "en-reverse", "en", ["kāma", "preman", "rāga"]),
    Query(108, "king", "en-reverse", "en", ["rāja", "nṛpa", "narendra"]),
    Query(109, "mind", "en-reverse", "en", ["manas", "citta", "cetas"]),
    Query(110, "heart", "en-reverse", "en", ["hṛd", "hṛdaya"]),
    Query(111, "self", "en-reverse", "en", ["ātman", "svayam"]),
    Query(112, "soul", "en-reverse", "en", ["ātman", "jīva"]),
    Query(113, "god", "en-reverse", "en", ["deva", "īśvara"]),
    Query(114, "duty", "en-reverse", "en", ["dharma", "kartavya"]),
    Query(115, "knowledge", "en-reverse", "en", ["jñāna", "vidyā"]),

    # ─── Section 5: more KO reverse (10) ───────────────────────────
    Query(116, "공", "ko-reverse", "ko", ["śūnyatā", "śūnya", "kha"]),
    Query(117, "마음", "ko-reverse", "ko", ["manas", "citta"]),
    Query(118, "신", "ko-reverse", "ko", ["deva", "īśvara"]),
    Query(119, "왕", "ko-reverse", "ko", ["rāja", "nṛpa"]),
    Query(120, "물", "ko-reverse", "ko", ["jala", "ap"]),
    Query(121, "지옥", "ko-reverse", "ko", ["naraka", "niraya"]),
    Query(122, "인연", "ko-reverse", "ko", ["nidāna", "pratyaya"]),
    Query(123, "해탈", "ko-reverse", "ko", ["mokṣa", "mukti"]),
    Query(124, "열반", "ko-reverse", "ko", ["nirvāṇa"]),
    Query(125, "보살", "ko-reverse", "ko", ["bodhisattva"]),

    # ─── Section 6: more ZH reverse (10) ───────────────────────────
    Query(126, "天", "zh-reverse", "zh", ["deva", "svarga"]),
    Query(127, "地", "zh-reverse", "zh", ["pṛthivī", "bhūmi"]),
    Query(128, "心", "zh-reverse", "zh", ["citta", "manas", "hṛd"]),
    Query(129, "苦", "zh-reverse", "zh", ["duḥkha"]),
    Query(130, "智慧", "zh-reverse", "zh", ["prajñā", "jñāna", "buddhi"]),
    Query(131, "道", "zh-reverse", "zh", ["mārga", "panthan"]),
    Query(132, "佛", "zh-reverse", "zh", ["buddha"]),
    Query(133, "禪", "zh-reverse", "zh", ["dhyāna"]),
    Query(134, "般若", "zh-reverse", "zh", ["prajñā"]),
    Query(135, "業", "zh-reverse", "zh", ["karman", "karma"]),

    # ─── Section 7: more Wylie (10) ────────────────────────────────
    Query(136, "sangs rgyas", "bo-wylie", "bo", ["sangs rgyas", "buddha"]),
    Query(137, "ye shes", "bo-wylie", "bo", ["ye shes", "jñāna"]),
    Query(138, "shes rab", "bo-wylie", "bo", ["shes rab", "prajñā"]),
    Query(139, "snying rje", "bo-wylie", "bo", ["snying rje", "karuṇā"]),
    Query(140, "byams pa", "bo-wylie", "bo", ["byams pa", "maitri"]),
    Query(141, "stong pa", "bo-wylie", "bo", ["stong pa", "śūnyatā"]),
    Query(142, "lam", "bo-wylie", "bo", ["lam", "mārga"]),
    Query(143, "rgyud", "bo-wylie", "bo", ["rgyud", "tantra"]),
    Query(144, "sgom", "bo-wylie", "bo", ["sgom", "bhāvanā"]),
    Query(145, "blo", "bo-wylie", "bo", ["blo"]),

    # ─── Section 8: prefix variations (10) ─────────────────────────
    Query(146, "śā", "prefix", "prefix", ["śānti", "śāstra", "śākyamuni"]),
    Query(147, "yo", "prefix", "prefix", ["yoga", "yogī"]),
    Query(148, "nir", "prefix", "prefix", ["nirvāṇa", "nirodha"]),
    Query(149, "sam", "prefix", "prefix", ["saṃskāra", "samādhi"]),
    Query(150, "vij", "prefix", "prefix", ["vijñāna"]),
    Query(151, "tri", "prefix", "prefix", ["triratna", "trikāya"]),
    Query(152, "ka", "prefix", "prefix", ["karma", "kāma", "kalpa"]),
    Query(153, "su", "prefix", "prefix", ["sukha", "sūtra", "sūrya"]),
    Query(154, "br", "prefix", "prefix", ["brahman", "brahma"]),
    Query(155, "ut", "prefix", "prefix", ["utpāda"]),

    # ─── Section 9: Multi-word phrases (10) ────────────────────────
    Query(156, "om mani padme hum", "edge", "skt", ["om", "om", "om", "om"]),
    Query(157, "buddha dharma sangha", "edge", "skt", ["buddha", "dharma", "sangha"]),
    Query(158, "namo buddhāya", "edge", "skt", ["namo", "buddha"]),
    Query(159, "bodhisattva mahāsattva", "edge", "skt", ["bodhisattva", "mahāsattva"]),
    Query(160, "śīla samādhi prajñā", "edge", "skt", ["śīla", "samādhi", "prajñā"]),
    Query(161, "guru yoga", "edge", "skt", ["guru", "yoga"]),
    Query(162, "yoga sūtra", "edge", "skt", ["yoga", "sūtra"]),
    Query(163, "satyam śivam sundaram", "edge", "skt", ["satyam", "śiva", "sundara"]),
    Query(164, "neti neti", "edge", "skt", ["neti"]),
    Query(165, "sat cit ānanda", "edge", "skt", ["sat", "cit", "ānanda"]),

    # ─── Section 10: More EN reverse common (15) ──────────────────
    Query(166, "path", "en-reverse", "en", ["mārga", "panthan"]),
    Query(167, "patience", "en-reverse", "en", ["kṣānti"]),
    Query(168, "wealth", "en-reverse", "en", ["dhana", "artha", "vasu", "sampatti"]),
    Query(169, "speech", "en-reverse", "en", ["vāc"]),
    Query(170, "body", "en-reverse", "en", ["śarīra", "kāya", "deha"]),
    Query(171, "merit", "en-reverse", "en", ["puṇya", "kuśala"]),
    Query(172, "evil", "en-reverse", "en", ["pāpa", "akuśala", "doṣa"]),
    Query(173, "prayer", "en-reverse", "en", ["prārthanā", "stuti"]),
    Query(174, "vow", "en-reverse", "en", ["vrata"]),
    Query(175, "monk", "en-reverse", "en", ["bhikṣu", "śramaṇa"]),
    Query(176, "sin", "en-reverse", "en", ["pāpa"]),
    Query(177, "victory", "en-reverse", "en", ["vijaya", "jaya"]),
    Query(178, "sacrifice", "en-reverse", "en", ["yajña", "homa"]),
    Query(179, "gift", "en-reverse", "en", ["dāna", "tyāga"]),
    Query(180, "teacher", "en-reverse", "en", ["guru", "ācārya", "śāstṛ", "upādhyāya"]),

    # ─── Section 11: Cross-channel + edge (10) ─────────────────────
    Query(181, "om", "edge", "skt", ["oṃ", "om"]),
    Query(182, "AUM", "edge", "skt", ["aum", "oṃ"]),
    Query(183, "Buddha", "edge", "skt", ["buddha"]),
    Query(184, "DHARMA", "edge", "skt", ["dharma"]),
    Query(185, " agni ", "edge", "skt", ["agni"]),
    Query(186, "Śiva", "edge", "skt", ["śiva"]),
    Query(187, "नमस्ते", "edge", "skt", []),  # devanagari - no convert here
    Query(188, "汉字", "edge", "skt", []),
    Query(189, "??", "typo", "edge", []),
    Query(190, "***", "typo", "edge", []),

    # ─── Section 12: Buddhist sūtra titles (10) ────────────────────
    Query(191, "prajñāpāramitā", "skt-long", "skt", ["prajñāpāramitā"]),
    Query(192, "saddharmapuṇḍarīka", "skt-long", "skt", ["saddharmapuṇḍarīka"]),
    Query(193, "laṅkāvatāra", "skt-long", "skt", ["laṅkāvatāra"]),
    Query(194, "vajracchedikā", "skt-long", "skt", ["vajracchedikā"]),
    Query(195, "hṛdaya", "skt-mid", "skt", ["hṛdaya"]),
    Query(196, "saṃdhinirmocana", "skt-long", "skt", ["saṃdhinirmocana"]),
    Query(197, "daśabhūmika", "skt-long", "skt", ["daśabhūmika"]),
    Query(198, "gaṇḍavyūha", "skt-long", "skt", ["gaṇḍavyūha"]),
    Query(199, "mahāparinirvāṇa", "skt-long", "skt", ["mahāparinirvāṇa"]),
    Query(200, "śūraṅgama", "skt-long", "skt", ["śūraṅgama"]),

    # ─── Section 13: Upasarga prefix (Phase 3.7 Depth 2) ────────────
    # Sanskrit: typing the upasarga should surface words USING that prefix
    Query(201, "pra", "upasarga-prefix", "prefix", ["prajñā", "pratyaya", "prakṛti"]),
    Query(202, "prati", "upasarga-prefix", "prefix", ["pratītyasamutpāda", "pratipad"]),
    Query(203, "sam", "upasarga-prefix", "prefix", ["samāna", "saṃskāra", "saṃjñā"]),
    Query(204, "vi", "upasarga-prefix", "prefix", ["vijñāna", "vinaya", "viveka"]),
    Query(205, "abhi", "upasarga-prefix", "prefix", ["abhidharma", "abhiṣeka"]),
    Query(206, "anu", "upasarga-prefix", "prefix", ["anukampā", "anumāna"]),
    Query(207, "upa", "upasarga-prefix", "prefix", ["upādhyāya", "upādāna"]),
    Query(208, "ud", "upasarga-prefix", "prefix", ["udaya", "udāna"]),
    Query(209, "ni", "upasarga-prefix", "prefix", ["nirodha", "nidāna"]),
    Query(210, "su", "upasarga-prefix", "prefix", ["sukha", "subhūti"]),

    # Tibetan upasarga equivalents (15)
    Query(211, "rab tu", "upasarga-prefix", "prefix",
          ["rab tu byung", "rab tu dga'", "rab tu mi gnas"]),
    Query(212, "rnam par", "upasarga-prefix", "prefix",
          ["rnam par shes pa", "rnam par snang mdzad", "rnam par dag"]),
    Query(213, "kun", "upasarga-prefix", "prefix",
          ["kun rdzob", "kun gzhi", "kun mkhyen", "kun dga'"]),
    Query(214, "mngon par", "upasarga-prefix", "prefix",
          ["mngon par shes pa", "mngon par dga' ba"]),
    Query(215, "nye bar", "upasarga-prefix", "prefix",
          ["nye bar"]),
]


# ─────────────────────────────────────────────────────────────────────
#  Index loaders + evaluators (shared with audit_sentinel_50.py)
# ─────────────────────────────────────────────────────────────────────
def load_msgpack_zst(path: Path):
    raw = path.read_bytes()
    return msgpack.unpackb(zstd.ZstdDecompressor().decompress(raw),
                           raw=False, strict_map_key=False)


def load_headwords(path: Path) -> list[tuple[str, str, int, str]]:
    """Load 4-column TSV (norm, iast, rank, upasarga). 2/3-col legacy OK."""
    raw = path.read_bytes()
    text = zstd.ZstdDecompressor().decompress(raw).decode("utf-8")
    out = []
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) >= 4:
            try:
                rank = int(parts[2])
            except ValueError:
                rank = 999_999
            out.append((parts[0], parts[1], rank, parts[3]))
        elif len(parts) == 3:
            try:
                rank = int(parts[2])
            except ValueError:
                rank = 999_999
            out.append((parts[0], parts[1], rank, ""))
        elif len(parts) == 2:
            out.append((parts[0], parts[1], 999_999, ""))
    return out


def normalize_skt(q: str) -> str:
    nfd = unicodedata.normalize("NFD", q.strip().lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def eval_skt(q: str, tier0: dict, tier0_bo: dict, tier0_ext: dict) -> list[str]:
    norm = normalize_skt(q)
    hits = []
    for src in (tier0, tier0_ext, tier0_bo):
        if norm in src:
            iast = src[norm].get("iast", norm)
            if iast not in hits:
                hits.append(iast)
    if hits:
        return hits[:5]
    if " " in norm:
        for token in norm.split():
            if not token:
                continue
            for src in (tier0, tier0_ext, tier0_bo):
                if token in src:
                    iast = src[token].get("iast", token)
                    if iast not in hits:
                        hits.append(iast)
                    break
            if len(hits) >= 5:
                break
    return hits[:5]


def eval_bo(q: str, tier0_bo: dict, tier0: dict, tier0_ext: dict) -> list[str]:
    norm = normalize_skt(q)
    hits = []
    for src in (tier0_bo, tier0, tier0_ext):
        if norm in src:
            iast = src[norm].get("iast", norm)
            if iast not in hits:
                hits.append(iast)
    return hits[:5]


def eval_prefix(q: str, headwords: list[tuple[str, str, int, str]]) -> list[str]:
    norm = normalize_skt(q)
    cands: list[tuple[str, str, int, str]] = []
    started = False
    for tup in headwords:
        if tup[0].startswith(norm):
            cands.append(tup)
            started = True
        elif started:
            break
    if not cands:
        return []
    upa_query = norm if any(c[3] == norm for c in cands) else ""
    def sort_key(c):
        upa_hit = 0 if (upa_query and c[3] == upa_query) else 1
        return (upa_hit, c[2], len(c[0]), c[0])
    cands.sort(key=sort_key)
    return [c[1] for c in cands[:5]]


def eval_reverse(q: str, reverse_idx: dict, reverse_meta: dict) -> list[str]:
    token = q.strip().lower() if q.isascii() else q.strip()
    if token not in reverse_idx:
        return []
    ids = reverse_idx[token][:5]
    out = []
    meta_ids = reverse_meta.get("ids", {}) if isinstance(reverse_meta, dict) else {}
    for eid in ids:
        slot = meta_ids.get(eid)
        if slot:
            out.append(slot[0])
        else:
            out.append(eid)
    return out


def eval_zh(q: str, equivalents: dict) -> list[str]:
    if q in equivalents:
        rows = equivalents[q]
        out = []
        seen = set()
        for r in rows[:10]:
            iast = r.get("skt_iast", "")
            if iast and iast not in seen:
                out.append(iast)
                seen.add(iast)
                if len(out) >= 5:
                    break
        return out
    return []


def eval_edge(q: str, tier0, tier0_bo, tier0_ext, headwords, eq) -> list[str]:
    if not q.strip():
        return []
    res = eval_skt(q, tier0, tier0_bo, tier0_ext)
    if res:
        return res
    res = eval_bo(q, tier0_bo, tier0, tier0_ext)
    if res:
        return res
    res = eval_prefix(q, headwords)
    if res:
        return res
    return []


def verdict(query: Query, results: list[str]) -> str:
    if not query.expected:
        if query.category in ("typo", "dead-zone"):
            return "✅" if not results else "⚠️"
        return "⚠️" if results else "❌"
    expected_set = {normalize_skt(e) for e in query.expected}
    results_norm = [normalize_skt(r) for r in results]
    if any(r in expected_set for r in results_norm):
        return "✅"
    for r in results_norm:
        for e in expected_set:
            if r in e or e in r:
                return "⚠️"
    return "❌"


def main() -> int:
    print("Loading indices…", file=sys.stderr)
    tier0 = load_msgpack_zst(INDICES / "tier0.msgpack.zst")
    tier0_bo = load_msgpack_zst(INDICES / "tier0-bo.msgpack.zst")
    ext_path = INDICES / "tier0-extended.msgpack.zst"
    tier0_ext = load_msgpack_zst(ext_path) if ext_path.exists() else {}
    headwords = load_headwords(INDICES / "headwords.txt.zst")
    reverse_en = load_msgpack_zst(INDICES / "reverse_en.msgpack.zst")
    reverse_ko = load_msgpack_zst(INDICES / "reverse_ko.msgpack.zst")
    reverse_meta = load_msgpack_zst(INDICES / "reverse_meta.msgpack.zst")
    equivalents = load_msgpack_zst(INDICES / "equivalents.msgpack.zst")

    print(f"  tier0: {len(tier0):,} · tier0-bo: {len(tier0_bo):,} · "
          f"tier0-ext: {len(tier0_ext):,}", file=sys.stderr)
    print(f"  headwords: {len(headwords):,} · reverse_en: {len(reverse_en):,} · "
          f"reverse_ko: {len(reverse_ko):,}", file=sys.stderr)

    rows = []
    summary = {"✅": 0, "⚠️": 0, "❌": 0}
    by_cat = {}

    for q in QUERIES:
        ch = q.channel
        if ch == "skt":
            hits = eval_skt(q.text, tier0, tier0_bo, tier0_ext)
        elif ch == "bo":
            hits = eval_bo(q.text, tier0_bo, tier0, tier0_ext)
        elif ch == "prefix":
            hits = eval_prefix(q.text, headwords)
        elif ch == "en":
            hits = eval_reverse(q.text, reverse_en, reverse_meta)
        elif ch == "ko":
            hits = eval_reverse(q.text, reverse_ko, reverse_meta)
        elif ch == "zh":
            hits = eval_zh(q.text, equivalents)
        else:
            hits = eval_edge(q.text, tier0, tier0_bo, tier0_ext,
                             headwords, equivalents)
        v = verdict(q, hits)
        summary[v] += 1
        by_cat.setdefault(q.category, {"✅": 0, "⚠️": 0, "❌": 0})[v] += 1
        rows.append({
            "n": q.n,
            "query": q.text,
            "category": q.category,
            "channel": q.channel,
            "expected": " | ".join(q.expected),
            "top_5": " | ".join(hits) if hits else "(none)",
            "verdict": v,
        })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["n", "query", "category",
                                            "channel", "expected", "top_5",
                                            "verdict"])
        w.writeheader()
        w.writerows(rows)
    print(f"\n✓ Wrote {OUT_CSV.relative_to(ROOT)}")

    total = sum(summary.values())
    lines = [
        "# audit-C-sentinel200 — 200 query 자동 평가 (Phase 3.7 Option C)",
        "",
        f"- **종합**: ✅ {summary['✅']}/{total} ({summary['✅']/total*100:.1f}%) · "
        f"⚠️ {summary['⚠️']}/{total} · ❌ {summary['❌']}/{total}",
        f"- 인덱스: tier0 {len(tier0):,} keys · tier0-ext {len(tier0_ext):,} · "
        f"reverse_en {len(reverse_en):,} · reverse_ko {len(reverse_ko):,}",
        "",
        "## 카테고리별",
        "",
        "| Category | ✅ | ⚠️ | ❌ | Total | ✅% |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for cat, sc in sorted(by_cat.items()):
        t = sum(sc.values())
        pct = sc["✅"] / t * 100 if t else 0
        lines.append(f"| {cat} | {sc['✅']} | {sc['⚠️']} | {sc['❌']} | {t} | {pct:.0f}% |")
    lines.append("")
    lines.append("## ❌ 실패 query")
    lines.append("")
    lines.append("| # | Query | Cat | Ch | Expected | Top-5 |")
    lines.append("|---|---|---|---|---|---|")
    for r in rows:
        if r["verdict"] == "❌":
            top = r["top_5"][:60].replace("|", "\\|")
            exp = (r["expected"] or "(none)")[:30].replace("|", "\\|")
            q = r["query"].replace("|", "\\|")
            lines.append(f"| {r['n']} | `{q}` | {r['category']} | {r['channel']} "
                         f"| {exp} | {top} |")
    lines.append("")
    lines.append("## ⚠️ 부분 매치")
    lines.append("")
    lines.append("| # | Query | Cat | Ch | Expected | Top-5 |")
    lines.append("|---|---|---|---|---|---|")
    for r in rows:
        if r["verdict"] == "⚠️":
            top = r["top_5"][:60].replace("|", "\\|")
            exp = (r["expected"] or "(none)")[:30].replace("|", "\\|")
            q = r["query"].replace("|", "\\|")
            lines.append(f"| {r['n']} | `{q}` | {r['category']} | {r['channel']} "
                         f"| {exp} | {top} |")
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"✓ Wrote {OUT_MD.relative_to(ROOT)}")
    print(f"\n총합: ✅ {summary['✅']}/{total} ({summary['✅']/total*100:.1f}%) · "
          f"⚠️ {summary['⚠️']} · ❌ {summary['❌']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
