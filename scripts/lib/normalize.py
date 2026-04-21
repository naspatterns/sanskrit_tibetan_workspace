"""IAST validation + normalization helpers (FB-4 support).

Works alongside transliterate.py which handles the actual script conversion.
This module focuses on *validating* that a string is well-formed IAST.
"""
from __future__ import annotations

import re
import unicodedata


# Allowed characters for Sanskrit/Pāli IAST headwords.
# Base Latin letters + diacritic-bearing IAST letters + common punctuation.
# ṁ/Ṁ (m with dot ABOVE) used in Pāli (Sri Lankan convention) alongside ṃ/Ṃ
# (m with dot below) used in Sanskrit. Both accepted.
_IAST_LETTERS = set(
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "āīūṛṝḷḹṃṁḥṅñṭḍṇśṣ"
    "ĀĪŪṚṜḶḸṂṀḤṄÑṬḌṆŚṢ"
)
_IAST_ALLOWED = _IAST_LETTERS | set(" '-.,()/|")

# HK "upper-case signature" characters. If these appear in a supposed IAST
# string, conversion probably failed. See transliterate._looks_like_hk().
_HK_UPPER_SIGNATURE = set("AIUTDNSGJRMH")


def is_valid_iast(s: str) -> bool:
    """True iff all characters are within the permitted IAST set.

    Intended for Sanskrit entries (lang=skt). Not applicable to Tibetan (Wylie
    uses additional characters) or Chinese.
    """
    if not s:
        return False
    # Normalize NFC so precomposed/decomposed forms both pass.
    normalized = unicodedata.normalize("NFC", s)
    return all(c in _IAST_ALLOWED for c in normalized)


def has_hk_signature(s: str) -> bool:
    """Heuristic: does this string contain HK upper-case signature chars?

    If True, the string is probably still in HK and not converted to IAST.
    Intended as a post-conversion validation — if we claim headword_iast is
    IAST but this returns True, the build likely has a bug.

    Rules (must match transliterate._looks_like_hk() exactly):
      - IAST diacritic present → NOT HK
      - All-uppercase (no lowercase) → NOT HK (e.g. 'ABALA' from Purāṇic
        Encyclopaedia is valid uppercase IAST, not HK)
      - Must have HK upper signature char AND lowercase char → HK suspect
    """
    if not s:
        return False
    has_iast_diacritics = any(c in "āīūṛṝḷḹṃḥṅñṭḍṇśṣ" for c in s)
    if has_iast_diacritics:
        return False
    has_hk_upper = any(c in _HK_UPPER_SIGNATURE for c in s)
    has_lower = any(c.islower() for c in s)
    return has_hk_upper and has_lower


# Wylie allowed character set (loose — Wylie uses a lot of punctuation).
# Keep lenient; we don't enforce strict Wylie syntax, just character class.
_WYLIE_ALLOWED = set(
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    " '-.,()/|_+"
)


def is_valid_wylie(s: str) -> bool:
    """Loose validation for Tibetan Wylie headwords (lang=bo)."""
    if not s:
        return False
    return all(c in _WYLIE_ALLOWED for c in s)


_WHITESPACE_RE = re.compile(r"\s+")


def normalize_whitespace(s: str) -> str:
    """Collapse runs of whitespace to single spaces, trim ends."""
    return _WHITESPACE_RE.sub(" ", s).strip()
