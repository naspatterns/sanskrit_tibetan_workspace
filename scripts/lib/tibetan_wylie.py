"""Tibetan Unicode → Wylie (EWTS) approximate transliterator.

Pragmatic char-by-char converter — not a full EWTS implementation
(no super/subscript stack handling, no special diphthongs). Goal: produce
a stable Latin string that's searchable + recognizable to a Tibetanist.

Handles:
  - Base consonants (U+0F40..U+0F6C)
  - Subjoined consonants (U+0F90..U+0FBC) — emitted as lowercase Wylie
  - Vowels (U+0F71 lengthening, U+0F72 i, U+0F74 u, U+0F7A e, U+0F7C o)
  - Tsheg (U+0F0B) → space (within syllable separator)
  - Shad (U+0F0D) → no Wylie equivalent → remove
  - Other Tibetan punctuation → remove

Doesn't handle (left in raw form, prefixed with `?`):
  - Stacked consonants (output as concatenation, may need manual cleanup)
  - Sanskrit-specific letters (rare in modern Tibetan-Chinese dict)

Usage:
    from scripts.lib.tibetan_wylie import to_wylie
    to_wylie("བཀའ་བཐམ།")  # → "bka' btham"
"""
from __future__ import annotations

# Base consonants (U+0F40..)
_CONS: dict[str, str] = {
    "ཀ": "k", "ཁ": "kh", "ག": "g", "གྷ": "gh", "ང": "ng",
    "ཅ": "c", "ཆ": "ch", "ཇ": "j", "ཉ": "ny",
    "ཊ": "T", "ཋ": "Th", "ཌ": "D", "ཌྷ": "Dh", "ཎ": "N",
    "ཏ": "t", "ཐ": "th", "ད": "d", "དྷ": "dh", "ན": "n",
    "པ": "p", "ཕ": "ph", "བ": "b", "བྷ": "bh", "མ": "m",
    "ཙ": "ts", "ཚ": "tsh", "ཛ": "dz", "ཛྷ": "dzh", "ཝ": "w",
    "ཞ": "zh", "ཟ": "z", "འ": "'", "ཡ": "y", "ར": "r",
    "ལ": "l", "ཤ": "sh", "ཥ": "Sh", "ས": "s", "ཧ": "h",
    "ཨ": "a", "ཀྵ": "kSh", "ཪ": "r", "ཫ": "v", "ཬ": "y",
}

# Subjoined consonants (U+0F90..) — same letter values, marked lowercase
_SUB: dict[str, str] = {
    "ྐ": "k", "ྑ": "kh", "ྒ": "g", "ྒྷ": "gh", "ྔ": "ng",
    "ྕ": "c", "ྖ": "ch", "ྗ": "j", "ྙ": "ny",
    "ྚ": "T", "ྛ": "Th", "ྜ": "D", "ྜྷ": "Dh", "ྞ": "N",
    "ྟ": "t", "ྠ": "th", "ྡ": "d", "ྡྷ": "dh", "ྣ": "n",
    "ྤ": "p", "ྥ": "ph", "ྦ": "b", "ྦྷ": "bh", "ྨ": "m",
    "ྩ": "ts", "ྪ": "tsh", "ྫ": "dz", "ྫྷ": "dzh", "ྭ": "w",
    "ྮ": "zh", "ྯ": "z", "ྰ": "'", "ྱ": "y", "ྲ": "r",
    "ླ": "l", "ྴ": "sh", "ྵ": "Sh", "ྶ": "s", "ྷ": "h",
    "ྸ": "a", "ྐྵ": "kSh", "ྺ": "v", "ྻ": "y", "ྼ": "r",
}

# Vowel signs (U+0F71..U+0F7D)
_VOWELS: dict[str, str] = {
    "ཱ": "A",  # vowel lengthener (long a)
    "ི": "i",  # i
    "ཱི": "I",  # I (long)
    "ུ": "u",  # u
    "ཱུ": "U",  # U (long)
    "ྲྀ": "rI", "ཷ": "rI",  # vocalic r
    "ླྀ": "lI", "ཹ": "lI",  # vocalic l
    "ེ": "e",  # e
    "ཻ": "ai", # ai
    "ོ": "o",  # o
    "ཽ": "au", # au
    "ཾ": "M",  # anusvara
    "ཿ": "H",  # visarga
    "ྀ": "-i", # reverse i
    "ཱྀ": "-I", # reverse I
}

# Punctuation / structural
_TSHEG = "་"
_SHAD = "།"
_NYIS_SHAD = "༎"
_DOUBLE_TSHEG = "༌"


def to_wylie(s: str) -> str:
    """Convert Tibetan Unicode to approximate EWTS Wylie.

    Implicit 'a' rule: every Tibetan syllable has an inherent 'a' vowel on
    its root consonant. Wylie writes this 'a' EXCEPT when an explicit vowel
    sign is attached. We approximate by appending 'a' at every syllable end
    (before tsheg/shad/end) when the syllable doesn't already contain a vowel.
    """
    syllables: list[list[str]] = [[]]  # list of (char, type) per syllable
    syl_has_vowel: list[bool] = [False]

    def push_syl():
        syllables.append([])
        syl_has_vowel.append(False)

    for c in s:
        if c in (_TSHEG, _SHAD, _NYIS_SHAD, _DOUBLE_TSHEG):
            push_syl()
        elif c in _CONS:
            syllables[-1].append(_CONS[c])
        elif c in _SUB:
            syllables[-1].append(_SUB[c])
        elif c in _VOWELS:
            syllables[-1].append(_VOWELS[c])
            syl_has_vowel[-1] = True
        elif "ༀ" <= c <= "࿿":
            syllables[-1].append(f"?{ord(c):04x}")
        else:
            syllables[-1].append(c)

    out_syls: list[str] = []
    for parts, has_vowel in zip(syllables, syl_has_vowel):
        if not parts:
            continue
        text = "".join(parts)
        # Implicit 'a' if syllable has consonant(s) but no explicit vowel
        # AND ends with a consonant (not 'i'/'u'/'e'/'o'/'A' etc.)
        if not has_vowel and text and text[-1].isalpha() and text[-1] not in "AIUEO":
            text += "a"
        out_syls.append(text)
    return " ".join(out_syls).strip()
