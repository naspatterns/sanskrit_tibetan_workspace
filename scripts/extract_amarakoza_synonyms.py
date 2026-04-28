#!/usr/bin/env python3
"""Verse-level NLP for Amarakośa: page-raw OCR → synonym group rows.

Pipeline (best-effort heuristic — no external Sanskrit NLP dependency):

  1. Read `data/jsonl/equiv-amarakoza.jsonl` (1,119 page-raw rows, OCR'd).
  2. Per-volume cleaning: strip English headers, page footers, GRETIL metadata,
     commentary references like '(पा० ४.२.१६६)' and Aṣṭādhyāyī sūtra refs.
  3. Concatenate cleaned text across pages → continuous Devanagari stream.
  4. Split by verse-end markers `॥ N ॥` (where N is a Devanagari numeral) into
     verse blocks. Each block = mūla śloka + interleaved Kṣīrasvāmin/Sarvānanda
     commentary.
  5. Heuristically isolate the mūla portion (text before first commentary
     marker `क्षीर` / `टीका`).
  6. Tokenize mūla Devanagari → drop function words/particles → convert each
     surface form to IAST via scripts/lib/transliterate.devanagari_to_iast.
  7. Per-volume: track śloka number progression → reset-based varga numbering.
  8. Volume → kāṇḍa map (static, derived from TSS edition):
        vol1 → kāṇḍa 1 (Svargādi), 220p
        vol2 → kāṇḍa 2 (Bhūvargādi part 1), 400p
        vol3 → kāṇḍa 2 (Bhūvargādi part 2), 304p
        vol4 → kāṇḍa 3 (Sāmānyādi), 197p
  9. Emit `data/jsonl/equiv-amarakoza-synonyms.jsonl` with body.equivalents.synonyms
     (NEW schema field — see docs/schema.json update).

Synonym groups are coarse: 1 verse = 1 group. In reality Amarakośa often packs
2-3 groups per verse (svar/deva/sura all in one śloka), but reliable mid-verse
splitting requires lemma analysis (vidyut-prakriya etc., out of scope).

The output preserves the page-raw entries side-by-side so the existing
`equiv-amarakoza` slug remains usable as a fallback / archival.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.lib.transliterate import devanagari_to_iast, normalize  # noqa: E402

# ─────────────────────────────────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────────────────────────────────

INPUT_JSONL = ROOT / "data" / "jsonl" / "equiv-amarakoza.jsonl"
OUTPUT_JSONL = ROOT / "data" / "jsonl" / "equiv-amarakoza-synonyms.jsonl"
OUTPUT_META_DIR = ROOT / "data" / "sources" / "equiv-amarakoza-synonyms"
SLUG = "equiv-amarakoza-synonyms"

# Volume → kāṇḍa mapping (TSS 38/43/51/52 layout)
VOL_KANDA_MAP = {1: 1, 2: 2, 3: 2, 4: 3}
KANDA_NAMES = {1: "Svargādi", 2: "Bhūvargādi", 3: "Sāmānyādi"}

# Devanagari range
DEV_RE = re.compile(r"[ऀ-ॿ]")
DEV_DIGITS = "०१२३४५६७८९"

# Verse-end markers: `॥ N ॥` with N being 1-3 Devanagari digits.
# Sometimes the surrounding `॥` are mis-OCR'd as `||` or `॥।` — the regex
# accepts the canonical form only (more reliable; OCR variants land in body.plain).
VERSE_NUM_RE = re.compile(r"॥\s*([०-९]{1,3})\s*॥")

# Commentary markers — Kṣīrasvāmin (क्षीर) and Sarvānanda Ṭīkā (टीका).
# OCR errors common: क्षीर°, क्षी र०, क्षीरः, etc. Accept liberal forms.
COMMENTARY_MARKER_RE = re.compile(
    r"(?:"
    r"(?:क्षी?\s*र[\s°○ः०\.\-—]*)"           # Kṣīr° variants
    r"|(?:[दटी]ी?\s*का[\s°○ः०\.\-—]*)"       # Ṭīkā° variants (loose: 'दीका' OCR mishap too)
    r")"
)

# Aṣṭādhyāyī / Pāṇinian sūtra refs like "(पा० ४.२.१६६)" or "(So ४. १. १९)" —
# these are commentary citations, not synonyms.
SUTRA_REF_RE = re.compile(
    r"\([^()]*?०-९[^()]*?\)"
    r"|\([^()\s]*?[०-९]+\s*\.\s*[०-९]+\s*\.\s*[०-९]+\s*\)"
    r"|\([^()]{1,40}?\)"  # any short parenthetical (most are sūtra refs)
)

# Inline Devanagari quotation/citation markers (single dandas at end-of-citation,
# the curly Devanagari quote `’` and `‘`).
DEV_QUOTE_RE = re.compile(r"['‘’\"`„«»]")

# Stop tokens — Sanskrit grammatical particles, gender markers, common
# meta-words in Amarakośa that are not synonyms but structural words.
# Stored after `normalize()` (lowercase ASCII-ish, no diacritics).
_RAW_STOP = """
puṃ puṃsi puṃsoḥ puṃsau puṃsām puṃso puṃsi
strī striyāṃ striyām striyaḥ striyāḥ striyoḥ striyau
klī klīve klībe klīvayoḥ klībam klībaṃ
napuṃsake napuṃsakaṃ napuṃsaka napuṃsakam
tulyam tulye tulyau tulya tulyāḥ
samau samaṃ same samāḥ samā samaḥ
trayam traye traya trīṇi trayaḥ trayam triṣu
dvayam dvaya dvau dve dvayoḥ
catuṣkam catuṣka catur catvāri caturṣu
pañcakam pañcaka pañca pañcasu
saptakam saptaka saptau
ca tu vā atha api iti iva
syāt syuḥ syu syād stāt sa saḥ sā so
yathā tathā evam eva yat tat tu na ha
te tā tāḥ tau ta saḥ sā tat tasya tasmin tasmāt
asau ayaṃ iyaṃ amī ami eṣa eṣaḥ etat
mā māt ho hi vā vai cet kim kasya
ādi ādayaḥ ādiḥ ādīnāṃ ādīnām
atra tatra kvacit kṣaṇam yatra kutracit kutaḥ
itihāse itihāsa
om śrī śrīḥ amba ambā
patah pathah piṭhah pātṭhah
varganu vargah vargaḥ varga
kāṇḍa kāṇḍaṃ kāṇḍam kāṇḍe kāṇḍāḥ kāṇḍāni
ity iti tena yena kena
nāmaliṅgānuśāsanam nāmaliṅgānuśāsanaṃ nāmalinganusasanam namalinganusasana
ṭīkāsarvasvākhyavyākhyāsametam tikasarvasvakhyavyakhyasametam sarvasvakhyavyakhyasametam
sarvasvakhyavyasyasametam sarvasvakhyavyakhyasamatam sarvasv
amarakośa amarakoza
prathamaṃ prathamam dvitīyaṃ dvitīyam tṛtīyaṃ tṛtīyam rathamam dvit ditīyam
"""
STOP_TOKENS_IAST = {normalize(t) for t in _RAW_STOP.split() if t}

# Extra: drop tokens that are pure punctuation/digit transliteration leftovers.
# Allow only IAST-letter strings.
IAST_TOKEN_RE = re.compile(r"^[a-zāīūṛṝḷḹṃṁḥṅñṭḍṇśṣ'\-]+$")

# ─────────────────────────────────────────────────────────────────────────
#  Page → cleaned Devanagari stream
# ─────────────────────────────────────────────────────────────────────────

# Header/footer patterns that frequently precede/follow body text.
HEADER_PATTERNS = [
    re.compile(r"नामलिङ्ग[ाोौ]?[नचजञ]?[ुू]?[शस]?ासन[ंेम]"),  # नामलिङ्गानुशासनं w/ OCR variants
    re.compile(r"टीकासर्व[स]?्व[ाांाख्य]*"),                  # टीकासर्वस्वाख्य
    re.compile(r"व्याख्याद्व[यो]ोपेत"),                       # व्याख्यादयोपेतम्
    re.compile(r"काण्ड[ंेम]?"),    # काण्डं/काण्डे
]

ENGLISH_LINE_RE = re.compile(r"[A-Za-z]{4,}")  # any 4+ Latin letters → likely English/footer
LONE_NUMBER_RE = re.compile(r"^[०-९0-9\s\.,/\-]+$")  # page number lines

# Footnote / variant reading lines: "१. क. ख. ग. पाठः,  २. तेः ड. छ. पाठः"
FOOTNOTE_RE = re.compile(r"^[\s\.\d०-९]*[क-ह]\.[\s\d०-९क-ह\.,]*\s*पाठः?")
# Lines starting with footnote-marker pattern: number + dot + dotted abbreviations
FOOTNOTE_PREFIX_RE = re.compile(r"^[०-९\d]+\.\s*[क-हa-zA-Z]\s*[\.\,]")

# Citation in single quotes with HK/IAST contents — common commentary noise.
CITATION_RE = re.compile(r"['‘`][^'‘’`]{1,80}['’`]")


def dev_only_ratio(line: str) -> float:
    """Fraction of non-whitespace chars that are Devanagari."""
    chars = [c for c in line if not c.isspace()]
    if not chars:
        return 0.0
    return sum(1 for c in chars if "ऀ" <= c <= "ॿ") / len(chars)


def clean_page_text(text: str) -> str:
    """Drop English content, footers, headers, footnotes; keep Devanagari body.

    Strategy: line-level filter — keep lines that are >40% Devanagari and don't
    match header / footnote patterns. Within kept lines, strip OCR noise.
    """
    out_lines: list[str] = []
    for line in text.split("\n"):
        s = line.strip()
        if not s:
            continue
        # Page number alone
        if LONE_NUMBER_RE.match(s):
            continue
        # Predominantly English line (e.g. GRETIL header, page footer with English)
        if ENGLISH_LINE_RE.search(s) and dev_only_ratio(s) < 0.3:
            continue
        # Page header — has "नामलिङ्ग..."  AND  "[काण्ड..." pattern
        if any(p.search(s) for p in HEADER_PATTERNS) and dev_only_ratio(s) < 0.7:
            continue
        # Footnote / variant reading lines (very common in TSS edition margins)
        if FOOTNOTE_RE.match(s) or FOOTNOTE_PREFIX_RE.match(s):
            continue
        # Footnote-style line with multiple "X. पाठः" markers
        if "पाठः" in s and s.count(".") >= 2 and len(s) < 80:
            continue
        out_lines.append(s)
    return "\n".join(out_lines)


# ─────────────────────────────────────────────────────────────────────────
#  Verse splitter
# ─────────────────────────────────────────────────────────────────────────

def split_into_verses(stream: str) -> list[tuple[int | None, int, str]]:
    """Split a continuous Devanagari stream into (verse_num, marker_pos, verse_text).

    Per Amarakośa edition layout (TSS, with both commentaries):
        ┌─────────────────────────┬──────┬──────────────────────────┬──────┐
        │  commentary on (N-1)    │ ॥N-1║ │  mūla of N (~100 chars)   │ ॥N║ │
        └─────────────────────────┴──────┴──────────────────────────┴──────┘

    We capture the chunk between consecutive markers. The mūla of verse N is
    at the END of that chunk (just before ॥N॥). Caller uses
    `extract_mula_from_chunk` to isolate just that tail.

    The chunk BEFORE the first marker contains preface (title page, contents,
    publisher metadata) PLUS the mūla of verse 1 at its tail. We keep it, but
    callers will trim aggressively to the last ~300 chars.

    Returns: list of (verse_num, marker_start_pos, chunk_text). The marker_pos
    is the offset of `॥N॥` in the original stream (used for page back-mapping).
    """
    matches = list(VERSE_NUM_RE.finditer(stream))
    if not matches:
        return []

    out: list[tuple[int | None, int, str]] = []
    last_end = 0
    for m in matches:
        verse_text = stream[last_end : m.start()].strip()
        if verse_text:
            num = _dev_to_int(m.group(1))
            out.append((num, m.start(), verse_text + " ॥" + m.group(1) + "॥"))
        last_end = m.end()
    return out


# ─────────────────────────────────────────────────────────────────────────
#  Mūla isolation from chunk (chunk = "commentary on N-1" + "mūla of N + ॥N॥")
# ─────────────────────────────────────────────────────────────────────────

# Prose-end signals that often precede a mūla quote. Devanagari `--` and `—`
# are commentary citation closers. After these, mūla often follows.
# (Note: bare `॥` is NOT included — every chunk ends in `॥N॥` and that's the
# mūla-end marker itself, not a prose-end marker.)
PROSE_END_MARKERS = ["--", "—", "—-", "-—", "...", "इति।", "इति ॥"]

# Trailing verse-end marker `॥N॥` we appended in split_into_verses
TRAILING_VERSE_END_RE = re.compile(r"\s*॥\s*[०-९1-9]{1,3}\s*॥\s*$")

# Maximum mūla length (anuṣṭubh = 32 syllables ≈ 100-130 Devanagari chars,
# but with sandhi expansion + diacritics + occasional 6-pāda verses we allow
# up to ~280 chars).
MULA_MAX_CHARS = 320


def extract_mula_from_chunk(chunk: str) -> str:
    """Isolate the mūla śloka portion at the END of a chunk.

    Strategy: segment the chunk by daṇḍa (`।` and `॥`) and use the END
    segments. Amarakośa is anuṣṭubh (4 pādas of 8 syllables ≈ 25-35 Devanagari
    chars/pāda), with structure "pāda1 pāda2 | pāda3 pāda4 ॥N॥". So a clean
    chunk of "[commentary on N-1] | [mūla of N + ॥N॥]" yields:
        segments = [..., commentary segments, pāda3, pāda4 of mūla N]
    The LAST 2 segments (after stripping ॥N॥) are typically the second half
    of the mūla. Last 4 are the full mūla. Whether 2 or 4 work depends on
    OCR quality and presence of commentary citations with daṇḍas.

    We take LAST 4 segments if their lengths look pāda-like (avg ≤ 60 chars),
    else last 2 (defensive fallback).
    """
    if not chunk:
        return ""

    # Step 0: strip trailing ॥N॥ marker
    chunk_no_end = TRAILING_VERSE_END_RE.sub("", chunk).rstrip()
    if not chunk_no_end:
        return ""

    # Step 1: if commentary marker present in last 1000 chars, drop everything before it
    tail = chunk_no_end[-1500:]
    last_comment = None
    for m in COMMENTARY_MARKER_RE.finditer(tail):
        last_comment = m
    if last_comment is not None:
        tail = tail[last_comment.end() :]

    # Step 2: split by daṇḍa boundaries (। and ॥)
    segments = [s.strip() for s in re.split(r"[।॥]", tail) if s.strip()]
    if not segments:
        return ""

    # Drop short trailing fragments that might be page numbers / single chars
    while segments and len(segments[-1]) < 4:
        segments.pop()
    if not segments:
        return ""

    # Try last 4 (full śloka), then last 2 (half śloka)
    for n in (4, 2, 1):
        if len(segments) < n:
            continue
        last_n = segments[-n:]
        avg_len = sum(len(s) for s in last_n) / n
        # Pāda is ~25-50 Devanagari chars; commentary is longer and uneven.
        if 8 <= avg_len <= 70:
            joined = " | ".join(last_n)
            if len(joined) > MULA_MAX_CHARS:
                joined = joined[-MULA_MAX_CHARS:]
            return joined

    # Fallback: just take last segment
    return segments[-1][-MULA_MAX_CHARS:]


def _dev_to_int(s: str) -> int | None:
    try:
        return int("".join(str(DEV_DIGITS.index(c)) for c in s))
    except (ValueError, IndexError):
        return None


# ─────────────────────────────────────────────────────────────────────────
#  Mūla / commentary separation
# ─────────────────────────────────────────────────────────────────────────

def split_mula_commentary(chunk: str) -> tuple[str, str]:
    """Return (mūla, commentary) — mūla is the END of the chunk (just before
    ॥N॥); commentary is the rest.

    The chunk has structure: [commentary on N-1] + [mūla N + ॥N॥]. So mūla is
    at the tail; commentary precedes it. See `extract_mula_from_chunk`.
    """
    mula = extract_mula_from_chunk(chunk)
    if not mula:
        return "", chunk.strip()
    # Commentary = everything before the mūla portion
    commentary = chunk[: -len(mula)].strip() if mula in chunk else chunk
    return mula, commentary


# ─────────────────────────────────────────────────────────────────────────
#  Tokenization → IAST → synonym filter
# ─────────────────────────────────────────────────────────────────────────

# Tokens are runs of Devanagari letters + virama + matras + special marks
# (no whitespace, no punctuation, no Latin).
DEV_TOKEN_RE = re.compile(r"[ऀ-ॿ]+")


def tokenize_devanagari(text: str) -> list[str]:
    """Return list of raw Devanagari word tokens, OCR-stripping common suffixes
    that look like grammatical endings garbled by OCR."""
    # Drop sūtra refs / parentheticals
    text = re.sub(r"\([^()]{0,80}?\)", " ", text)
    # Drop quotation citations
    text = CITATION_RE.sub(" ", text)
    # Drop dandas (single/double) with surrounding spaces — verse boundary
    text = text.replace("॥", " ").replace("।", " ")
    # Strip OCR noise punctuation
    text = re.sub(r"[`'’‘\"\.\,\;\:\-—\|\[\]\{\}\*\+\=\<\>\@\#\$\%\&\^\~]+", " ", text)
    return DEV_TOKEN_RE.findall(text)


def token_to_iast(tok: str) -> str:
    """Convert Devanagari token → IAST + light cleanup.

    Strips trailing virama / Devanagari avagraha; collapses doubled vowels."""
    iast = devanagari_to_iast(tok)
    # NFC normalize
    iast = unicodedata.normalize("NFC", iast)
    # Strip trailing/leading punctuation
    iast = iast.strip("'.,-—|")
    # Collapse runs of identical chars (OCR doubling)
    return iast


def is_synonym_candidate(iast: str) -> bool:
    if not iast or len(iast) < 2:
        return False
    if not IAST_TOKEN_RE.match(iast):
        return False
    if iast.lower() in STOP_TOKENS_IAST:
        return False
    if normalize(iast) in STOP_TOKENS_IAST:
        return False
    # Drop tokens that are >half consonants in a row (OCR garbage)
    vowels = sum(1 for c in iast if c in "aāiīuūṛṝḷḹeo")
    if vowels == 0:
        return False
    return True


def extract_synonyms(mula: str, max_per_group: int = 30) -> list[str]:
    """Extract IAST synonym candidates from a mūla verse."""
    seen: dict[str, None] = {}
    for tok in tokenize_devanagari(mula):
        iast = token_to_iast(tok)
        if not is_synonym_candidate(iast):
            continue
        key = normalize(iast)
        if key not in seen:
            seen[key] = None
            if len(seen) >= max_per_group:
                break
    return list(seen.keys())[:max_per_group]


def pick_headword(synonyms: list[str]) -> str:
    """Select the best representative synonym as headword.

    Prefer a token that:
      - is 4-10 characters (typical noun length)
      - is vowel-rich (≥30% vowels)
      - is not already known OCR garbage signature

    Fallback: first synonym."""
    if not synonyms:
        return ""

    def score(s: str) -> float:
        if not s:
            return -100
        # Length score: prefer 4-10
        ll = len(s)
        if ll < 3:
            return -10
        len_score = -abs(ll - 6) * 0.3  # peak at 6
        vowels = sum(1 for c in s if c in "aāiīuūṛṝḷḹeo")
        vowel_ratio = vowels / max(1, ll)
        vowel_score = (vowel_ratio - 0.3) * 5  # >30% vowels = bonus
        # Penalty for trailing / leading single chars (OCR garble)
        garble_penalty = -2 if (s.startswith("'") or s.endswith("'")) else 0
        return len_score + vowel_score + garble_penalty

    return max(synonyms, key=score)


# ─────────────────────────────────────────────────────────────────────────
#  Varga numbering via reset detection
# ─────────────────────────────────────────────────────────────────────────

def assign_varga_numbers(verse_nums: list[int | None]) -> list[int]:
    """Given a sequence of detected śloka numbers per verse (some None for
    verses where the marker was missed), output a parallel list of varga
    numbers starting at 1.

    Reset rule: if current num drops by >=10 vs running max AND current num <=5,
    increment varga.
    """
    out = []
    varga = 1
    running_max = 0
    for n in verse_nums:
        if n is not None:
            if running_max >= 10 and n <= 5 and n < running_max - 10:
                varga += 1
                running_max = n
            else:
                running_max = max(running_max, n)
        out.append(varga)
    return out


# ─────────────────────────────────────────────────────────────────────────
#  Main pipeline
# ─────────────────────────────────────────────────────────────────────────

def run() -> dict:
    """Process all 1,119 page-raw rows → emit synonym JSONL. Return stats."""
    if not INPUT_JSONL.exists():
        print(f"ERROR: {INPUT_JSONL} not found", file=sys.stderr)
        return {"error": "input_missing"}

    rows_in = [json.loads(l) for l in INPUT_JSONL.open(encoding="utf-8")]
    print(f"Loaded {len(rows_in)} page-raw rows", flush=True)

    # Group by volume
    by_vol: dict[int, list[dict]] = {1: [], 2: [], 3: [], 4: []}
    for r in rows_in:
        v = r["source_meta"]["vol"]
        by_vol.setdefault(v, []).append(r)

    out_rows: list[dict] = []
    seq_counter = 0
    stats = {
        "by_vol": {},
        "total_verses": 0,
        "total_pages_used": 0,
        "synonyms_per_verse": [],
        "verses_with_num": 0,
        "verses_no_num": 0,
    }

    for vol in sorted(by_vol):
        pages = sorted(by_vol[vol], key=lambda r: r["source_meta"]["page"])
        # Concatenate cleaned text with page boundary markers (used to back-map
        # verses to first page)
        page_offsets: list[tuple[int, int, int, float]] = []  # (offset, page, end_offset, conf)
        chunks = []
        cursor = 0
        for r in pages:
            cleaned = clean_page_text(r["body"]["plain"])
            if not cleaned:
                continue
            page_offsets.append(
                (cursor, r["source_meta"]["page"], cursor + len(cleaned), r["source_meta"]["ocr_conf"])
            )
            chunks.append(cleaned)
            cursor += len(cleaned) + 1  # +1 for the joiner space
        stream = "\n".join(chunks)
        stats["total_pages_used"] += len(page_offsets)

        verses = split_into_verses(stream)
        if not verses:
            print(f"  vol{vol}: no verse markers detected", flush=True)
            continue

        # Drop the FIRST verse chunk — it spans the entire preface (title page,
        # contents, mangala-mālā), polluted with title-page Devanagari noise.
        # The actual mūla of verse 1 is at the very tail of that first chunk;
        # for cleaner output we sacrifice it (it's recoverable later via the
        # equiv-amarakoza page-raw rows).
        if verses and verses[0][0] == 1:
            # Keep verse 1 — its mūla is at tail of preface chunk, but trim
            # aggressively. The first-verse mūla is short enough that
            # extract_mula_from_chunk handles it.
            pass
        # If first detected verse is NOT 1 (e.g. śloka 71 from vol1 page 64
        # OCR mishap), drop the chunk leading up to it (it's certainly
        # cross-vol-boundary garbage).
        elif verses and verses[0][0] is not None and verses[0][0] > 5:
            verses = verses[1:]

        verse_nums = [v[0] for v in verses]
        varga_nums = assign_varga_numbers(verse_nums)
        n_with_num = sum(1 for n in verse_nums if n is not None)
        stats["verses_with_num"] += n_with_num
        stats["verses_no_num"] += len(verses) - n_with_num
        stats["by_vol"][vol] = {
            "kanda": VOL_KANDA_MAP[vol],
            "pages": len(page_offsets),
            "verses": len(verses),
            "verses_with_num": n_with_num,
            "varga_count": max(varga_nums) if varga_nums else 0,
        }

        def offset_to_page(off: int) -> tuple[int, float]:
            for s, p, e, c in page_offsets:
                if s <= off < e:
                    return p, c
            return (page_offsets[-1][1], page_offsets[-1][3]) if page_offsets else (0, 0.0)

        for (vnum, marker_off, chunk_text), varga in zip(verses, varga_nums):
            mula, commentary = split_mula_commentary(chunk_text)
            if not mula:
                continue
            synonyms = extract_synonyms(mula)
            # Need at least 2 tokens to be a meaningful "group"
            if len(synonyms) < 2:
                continue
            # Drop first-pass garbage: synonyms list dominated by
            # ultra-long tokens often = OCR mush + samāsa run-ons
            avg_len = sum(len(s) for s in synonyms) / len(synonyms)
            if avg_len > 20:  # generous cutoff — Sanskrit compounds can be long
                continue

            # Headword = best-scoring synonym (vowel-rich, medium length)
            headword_iast = pick_headword(synonyms)
            page, conf = offset_to_page(marker_off)
            kanda = VOL_KANDA_MAP[vol]

            seq_counter += 1
            row = {
                # `headword` is the canonical IAST representative — keeps the
                # `headword_norm == normalize_headword(headword)` invariant
                # required by verify.py. The full mūla śloka lives in
                # body.plain; the original Devanagari verse fragment also
                # ends up in source_meta.mula_devanagari for archival.
                "id": f"{SLUG}-{seq_counter:05d}",
                "dict": SLUG,
                "headword": headword_iast,
                "headword_iast": headword_iast,
                "headword_norm": normalize(headword_iast),
                "lang": "skt",
                "tier": 3,
                "priority": 50,
                "role": "thesaurus",
                "body": {
                    "plain": mula[:1000] if mula else chunk_text[-1000:],
                    "equivalents": {
                        "skt_iast": headword_iast,
                        "synonyms": synonyms,
                        "category": f"{kanda}.{varga}.{vnum}" if vnum else f"{kanda}.{varga}.?",
                        "note": commentary[:500] if commentary else "",
                    },
                },
                "license": "public-domain",
                "source_meta": {
                    "vol": vol,
                    "page": page,
                    "kanda": kanda,
                    "kanda_name": KANDA_NAMES[kanda],
                    "varga": varga,
                    "shloka_num": vnum,
                    "ocr_conf": conf,
                    "structure": "verse-extracted",
                    "mula_devanagari": mula[:300],
                    "extractor": "extract_amarakoza_synonyms.py v1 (heuristic, no external NLP)",
                },
            }
            out_rows.append(row)
            stats["synonyms_per_verse"].append(len(synonyms))

    stats["total_verses"] = len(out_rows)
    return stats, out_rows


def write_output(out_rows: list[dict], stats: dict) -> None:
    OUTPUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_JSONL.open("w", encoding="utf-8") as f:
        for r in out_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nWrote {len(out_rows):,} synonym-group rows → {OUTPUT_JSONL}", flush=True)

    OUTPUT_META_DIR.mkdir(parents=True, exist_ok=True)
    meta = {
        "slug": SLUG,
        "name": "Amarakośa synonym groups (verse-level NLP from equiv-amarakoza OCR)",
        "lang": "skt",
        "tier": 3,
        "priority": 50,  # one rank lower than equiv-amarakoza (49)
        "role": "thesaurus",
        "direction": "skt-thesaurus",
        "license": "public-domain",
        "derived_from": "equiv-amarakoza",
        "extraction": {
            "method": "heuristic verse-split + Devanagari→IAST tokenization",
            "tooling": "Python regex; no external Sanskrit NLP library",
            "vol_kanda_map": VOL_KANDA_MAP,
            "verse_marker": "॥ <Devanagari digit(s)> ॥",
            "stop_tokens": len(STOP_TOKENS_IAST),
            "note": (
                "Synonym groups are coarse: 1 verse = 1 group. Real Amarakośa "
                "often packs 2-3 groups per verse; finer split requires lemma "
                "analysis (vidyut-prakriya / dharmamitra), out of scope. "
                "Mūla/commentary boundary detected via Kṣīrasvāmin/Sarvānanda "
                "markers (क्षीर / टीका); commentary text preserved in note field."
            ),
        },
        "row_count": len(out_rows),
        "stats": {
            "by_vol": stats.get("by_vol", {}),
            "verses_with_shloka_num": stats.get("verses_with_num", 0),
            "verses_without_shloka_num": stats.get("verses_no_num", 0),
            "median_synonyms_per_group": (
                sorted(stats["synonyms_per_verse"])[len(stats["synonyms_per_verse"]) // 2]
                if stats.get("synonyms_per_verse")
                else 0
            ),
        },
    }
    meta_path = OUTPUT_META_DIR / "meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote meta → {meta_path}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true", help="dry run; print stats only")
    args = ap.parse_args()

    stats, rows = run()
    print(f"\n━━━ Pipeline stats ━━━")
    print(f"Total verses extracted: {stats['total_verses']:,}")
    print(f"  with detected śloka num: {stats['verses_with_num']}")
    print(f"  no śloka num attached:    {stats['verses_no_num']}")
    print(f"Pages used: {stats['total_pages_used']}")
    print(f"\nPer volume:")
    for v, vs in sorted(stats["by_vol"].items()):
        print(
            f"  vol{v}: kāṇḍa {vs['kanda']} ({KANDA_NAMES[vs['kanda']]}) — "
            f"{vs['pages']} pages → {vs['verses']} verse-blocks "
            f"({vs['verses_with_num']} numbered) → {vs['varga_count']} varga(s)"
        )
    if stats.get("synonyms_per_verse"):
        s = stats["synonyms_per_verse"]
        print(
            f"\nSynonyms per group: min={min(s)} median={sorted(s)[len(s)//2]} "
            f"max={max(s)} mean={sum(s)/len(s):.1f}"
        )

    if args.no_write:
        print("\n--no-write: skipped JSONL output")
        # Sample rows
        for r in rows[:3]:
            print(f"\n  Sample {r['id']} (k{r['source_meta']['kanda']}.v{r['source_meta']['varga']}.s{r['source_meta']['shloka_num']}):")
            print(f"    headword_iast: {r['headword_iast']}")
            print(f"    synonyms: {r['body']['equivalents']['synonyms']}")
        return 0

    write_output(rows, stats)
    return 0


if __name__ == "__main__":
    sys.exit(main())
