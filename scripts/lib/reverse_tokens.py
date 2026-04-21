"""Reverse-search token extraction (FB-8).

For each entry, we extract lightweight gloss tokens from body text so that
users can later search Eng→Skt/Bo or Ko→original (FB-8). Tokens are stored
inline in each JSONL entry under `reverse.en[]` and `reverse.ko[]`; a
separate script in Phase 2 aggregates them into msgpack indices.

Design:
  - English: lowercase alphabetic only, stopwords (incl. scholarly grammar
    abbreviations) removed, position-weighted, deduplicated, capped at 20.
  - Korean: whitespace/punctuation split. Hanja in parens `법(法)` yields
    BOTH tokens (`법` and `法`) since users may search either form. No
    morphological analysis in Phase 1 (particles pass through as-is).

Position weighting:
  - Tokens appearing in the first 30 chars → weight 1.0
  - 30-100 chars → 0.7
  - beyond → 0.4
Dedup keeps the highest-weight occurrence. Output is ordered by weight DESC.
"""
from __future__ import annotations

import re


MAX_TOKENS = 20

# ───────────────────────────────────────────────────────────────────
#  English stopwords + scholarly abbreviations
# ───────────────────────────────────────────────────────────────────

STOPWORDS_EN: frozenset[str] = frozenset({
    # Generic English stopwords
    "the", "a", "an", "of", "to", "from", "with", "by", "in", "on", "at",
    "for", "as", "or", "and", "but", "is", "are", "was", "were", "be",
    "been", "being", "it", "its", "this", "that", "these", "those",
    "which", "who", "whom", "what", "when", "where", "how", "why",
    "if", "then", "than", "so", "not", "no", "nor", "also", "too",
    "there", "here", "such", "any", "all", "some", "other", "another",
    "one", "two", "three", "first", "second", "third",
    "very", "more", "most", "less", "least",
    "has", "have", "had", "do", "does", "did", "done", "being",
    "can", "could", "may", "might", "must", "shall", "should", "will", "would",

    # Sanskrit/Tibetan/Pāli grammar abbreviations commonly in dictionaries
    "m", "f", "n", "mfn",          # masc/fem/neut
    "mf", "nf", "mn",
    "pl", "sg", "du",              # plural/singular/dual
    "cf", "esp", "viz", "ib", "id", "etc", "i.e", "e.g",
    "cl", "cls",                   # class (verb roots)
    "comp",                        # comparative
    "fut", "impf", "prs", "pft", "aor",
    "loc", "gen", "acc", "abl", "ins", "voc", "nom", "dat",
    "w", "wrt",                    # with/written
    "ep", "eq",
    "sc",                          # scilicet
    "opp",                         # opposite
    "lit",                         # literally
    "lex",                         # lexical
    "p", "pp",                     # page / past participle
    "adj", "adv", "prep", "conj", "interj", "pron",
    "ind", "partc",                # indeclinable / participle
    "nb", "ns",
    "l", "ll",                     # line(s)
    "v", "vs",                     # verse(s) / versus
    "dh",                          # dhātupāṭha reference
    "ib", "idem", "ditto",
    "see", "also", "cf",
    "rv", "av", "tb", "sb", "mbh", "br", "ms",  # Vedic text refs (too generic to keep)
    "skt", "bo", "pā", "tib", "sans", "sanskrit", "tibetan",
    "engl", "english", "germ", "german", "fr", "french", "lat", "latin",
})


# Allowed token characters: lowercase ASCII letters only
_EN_TOKEN_RE = re.compile(r"[a-zA-Z]{2,}")


def extract_en_tokens(text: str, max_tokens: int = MAX_TOKENS) -> list[str]:
    """Extract English gloss tokens from a plain-text body.

    Args:
        text: Plain body text (markup stripped).
        max_tokens: Cap on output size.

    Returns:
        List of unique lowercase tokens, ordered by position weight DESC.
    """
    if not text:
        return []

    scored: dict[str, float] = {}
    for m in _EN_TOKEN_RE.finditer(text):
        tok = m.group(0).lower()
        if tok in STOPWORDS_EN:
            continue
        pos = m.start()
        weight = _position_weight(pos)
        if weight > scored.get(tok, 0.0):
            scored[tok] = weight

    # Sort by weight DESC, then alphabetic for determinism
    ordered = sorted(scored.items(), key=lambda kv: (-kv[1], kv[0]))
    return [tok for tok, _ in ordered[:max_tokens]]


def _position_weight(pos: int) -> float:
    if pos < 30:
        return 1.0
    if pos < 100:
        return 0.7
    return 0.4


# ───────────────────────────────────────────────────────────────────
#  Korean tokenizer (with Hanja bracket handling)
# ───────────────────────────────────────────────────────────────────

# Matches: a bracketed Hanja annotation `법(法)` where outer is Hangul,
# inner is Han ideograph(s). Used to emit both tokens.
_HANJA_BRACKET_RE = re.compile(
    r"([\uAC00-\uD7AF]+)\s*\(\s*([\u4E00-\u9FFF]+)\s*\)"
)

# General Korean/Hanja split: split on whitespace + punctuation, then filter.
_KO_SPLIT_RE = re.compile(r"[,;:/()\[\]\"'·\s。、]+")

# Character ranges
_HANGUL_RE = re.compile(r"[\uAC00-\uD7AF]")
_HAN_RE = re.compile(r"[\u4E00-\u9FFF]")


def extract_ko_tokens(text: str, max_tokens: int = MAX_TOKENS) -> list[str]:
    """Extract Korean (and Hanja) gloss tokens from a body.ko field.

    Handles `법(法)` by emitting both `법` and `法`. Particles are NOT stripped
    in Phase 1; Phase 2 may integrate mecab-ko for morphological analysis.
    """
    if not text:
        return []

    scored: dict[str, float] = {}

    # Hanja-bracket expansion happens first: `법(法)` → emit both sides.
    for m in _HANJA_BRACKET_RE.finditer(text):
        hangul, hanja = m.group(1), m.group(2)
        pos = m.start()
        weight = _position_weight(pos)
        if weight > scored.get(hangul, 0.0):
            scored[hangul] = weight
        if weight > scored.get(hanja, 0.0):
            scored[hanja] = weight

    # Generic split picks up remaining tokens; dedup by max-weight means
    # re-processing already-emitted bracket tokens is harmless.
    for chunk in _KO_SPLIT_RE.split(text):
        chunk = chunk.strip()
        if not chunk:
            continue
        # A chunk may contain mixed hangul+hanja like "법法" — rare but possible.
        # Keep as-is if it's pure hangul or pure hanja; otherwise split into runs.
        for run in _split_mixed_runs(chunk):
            if len(run) < 1:
                continue
            # Skip tokens that are neither hangul nor hanja (e.g. leftover Latin)
            if not (_HANGUL_RE.search(run) or _HAN_RE.search(run)):
                continue
            pos = text.find(run)
            weight = _position_weight(pos) if pos >= 0 else 0.4
            if weight > scored.get(run, 0.0):
                scored[run] = weight

    ordered = sorted(scored.items(), key=lambda kv: (-kv[1], kv[0]))
    return [tok for tok, _ in ordered[:max_tokens]]


def _split_mixed_runs(chunk: str) -> list[str]:
    """Split a chunk into runs of same script (hangul vs han vs other).

    'abc법法def' → ['abc', '법', '法', 'def']
    '법法'       → ['법', '法']
    '법'         → ['법']
    """
    runs: list[str] = []
    current: list[str] = []
    current_kind: str | None = None

    for ch in chunk:
        if _HANGUL_RE.match(ch):
            kind = "hangul"
        elif _HAN_RE.match(ch):
            kind = "han"
        else:
            kind = "other"

        if kind != current_kind:
            if current:
                runs.append("".join(current))
            current = [ch]
            current_kind = kind
        else:
            current.append(ch)

    if current:
        runs.append("".join(current))
    return runs
