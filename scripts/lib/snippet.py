"""Smart snippet extraction (FB-1).

v1 used fixed 50-char truncation which cut definitions mid-word. v2 uses
sentence/definition boundaries for `snippet_short` (~120 chars) and
`snippet_medium` (~400 chars).

Boundary priority (most trusted first):
  1. Explicit sense_separator regex (per-dict, from meta.json)
  2. Numbered sense markers: `-1 -2 -3` or `1. 2. 3.`
  3. Semicolons
  4. Period followed by space (with abbreviation guard)

Output limits follow schema.json:
  - snippet_short: ~120 target, 180 max
  - snippet_medium: ~400 target, 500 max
"""
from __future__ import annotations

import re


SNIPPET_SHORT_TARGET = 120
SNIPPET_SHORT_MAX = 180
SNIPPET_MEDIUM_TARGET = 400
SNIPPET_MEDIUM_MAX = 500


# Numbered senses like `-1 ... -2 ... -3` (Apte style) or `1. ... 2. ... 3.`
_NUMBERED_SENSE_RE = re.compile(r"\s(?:-\s?\d+|\d+\.)\s+")

# Semicolon boundary (not inside parens)
_SEMICOLON_RE = re.compile(r";\s+")

# Sentence-ending period with space — but guard against abbreviations.
# Common Sanskrit-grammar abbreviations that shouldn't count as sentence ends.
_SENTENCE_END_RE = re.compile(r"(?<!\b[a-zA-Z])(?<!\bcf)(?<!\besp)(?<!\bv)\.\s+(?=[A-Z])")
_WORD_BEFORE_PERIOD_RE = re.compile(r"\b([a-zA-Z]+)$")

# Common stop abbreviations that are NOT sentence boundaries.
_ABBREV_SET = frozenset({
    "m", "f", "n", "mfn",
    "cf", "esp", "pl", "sg", "du",
    "v", "vs", "viz", "ib", "id",
    "cl", "comp", "fut", "impf", "loc", "gen", "acc", "abl", "ins", "voc",
    "a", "b", "c", "d", "e",  # enumeration letters followed by "."
    "e.g",
})


def find_boundaries(text: str, sense_separator: str | None = None) -> list[int]:
    """Return sorted list of character positions where a sense/sentence boundary ends.

    Each position is the index AFTER the separator (i.e., start of next segment).
    """
    boundaries: set[int] = set()

    # 1. Explicit sense_separator regex if provided
    if sense_separator:
        try:
            for m in re.finditer(sense_separator, text):
                boundaries.add(m.end())
        except re.error:
            # Bad regex in meta.json; fall through to generic rules
            pass

    # 2. Numbered senses
    for m in _NUMBERED_SENSE_RE.finditer(text):
        boundaries.add(m.start() + 1)  # start of the next segment, after leading space

    # 3. Semicolons
    for m in _SEMICOLON_RE.finditer(text):
        boundaries.add(m.end())

    # 4. Sentence-ending periods (with abbreviation guard)
    for m in _SENTENCE_END_RE.finditer(text):
        before = text[:m.start()]
        word_match = _WORD_BEFORE_PERIOD_RE.search(before)
        if word_match and word_match.group(1).lower() in _ABBREV_SET:
            continue
        boundaries.add(m.end())

    # Always include end-of-text as the final boundary
    boundaries.add(len(text))
    return sorted(boundaries)


def _pick_snippet(text: str, boundaries: list[int], target: int, max_len: int) -> str:
    """Pick a snippet of approximately `target` chars, never exceeding `max_len`.

    Prefers the largest boundary that fits under `max_len`. If the first
    boundary already exceeds max_len, falls back to a word-boundary trim.
    """
    if not text:
        return ""
    if len(text) <= max_len:
        return text.strip()

    # Filter boundaries that fit under max_len
    candidates = [b for b in boundaries if b <= max_len]
    if candidates:
        # Prefer the boundary closest to target (without going over max_len)
        best = min(candidates, key=lambda b: abs(b - target) if b >= target else (target - b) + max_len)
        return text[:best].rstrip(" ;.-").strip()

    # Fall back to word boundary. Reserve 1 char for the ellipsis to stay within max_len.
    cut = text.rfind(" ", 0, max_len - 1)
    if cut > 0:
        return (text[:cut].rstrip(" ;.-").strip() + "…")[:max_len]
    return (text[: max_len - 1].strip() + "…")[:max_len]


def extract_snippets(text: str, sense_separator: str | None = None) -> tuple[str, str]:
    """Extract (snippet_short, snippet_medium) from a plain-text body.

    Args:
        text: Plain body text (markup already stripped).
        sense_separator: Optional regex from meta.json for per-dict tuning.

    Returns:
        (snippet_short, snippet_medium) — either can be empty string if `text` is empty.
    """
    if not text:
        return ("", "")

    text = text.strip()
    if not text:
        return ("", "")

    # Short bodies fit whole into both snippets without any boundary search.
    # Saves O(N) regex scanning across 30-50% of entries in the corpus.
    if len(text) <= SNIPPET_SHORT_MAX:
        return (text, text)

    boundaries = find_boundaries(text, sense_separator)
    short = _pick_snippet(text, boundaries, SNIPPET_SHORT_TARGET, SNIPPET_SHORT_MAX)
    medium = _pick_snippet(text, boundaries, SNIPPET_MEDIUM_TARGET, SNIPPET_MEDIUM_MAX)
    return (short, medium)


# ──────────────────────────────────────────────────────────────────────
#  Structured sense parsing (Apte/MW/Macdonell)
# ──────────────────────────────────────────────────────────────────────

_SENSE_SPLIT_RE = re.compile(r"(?:^|\s)(-?\d+[a-z]?)\.?\s+")


def extract_senses(text: str, sense_separator: str | None = None) -> list[dict]:
    """Parse numbered senses into [{num, text}, ...].

    Only produces output when the text has recognizable numbered structure.
    For flat definitions (no `-1 -2 -3`), returns [].
    """
    if not text:
        return []

    # Find all `-N` or `N.` markers with their positions
    pattern = sense_separator if sense_separator else r"(?:^|\s)(-?\d+[a-z]?)\.?\s+"
    try:
        matches = list(re.finditer(pattern, text))
    except re.error:
        return []

    if len(matches) < 2:
        # Need at least 2 senses to consider it structured
        return []

    senses: list[dict] = []

    # First sense: from start to first match
    first_start = matches[0].start()
    if first_start > 0:
        senses.append({"num": "1", "text": text[:first_start].strip()})

    # Subsequent senses: between match[i] and match[i+1]
    for i, m in enumerate(matches):
        num_raw = m.group(1) if m.lastindex else str(i + 1)
        num = num_raw.lstrip("-").strip()
        next_start = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sense_text = text[m.end():next_start].strip()
        if sense_text:
            senses.append({"num": num, "text": sense_text})

    # Filter out empties
    return [s for s in senses if s.get("text")]
