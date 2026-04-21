"""HTML / XDXF markup stripping for body text extraction.

v1 stores each entry's body with the original markup (XDXF for Cologne dicts,
HTML for Apple .dictionary bundles, SANDIC XML, etc.). This module reduces
them to clean plain text suitable for:
  - Smart snippet extraction (needs sentence boundaries intact)
  - Reverse token extraction (needs alphabet words intact)

Design principle: *do no semantic harm*. We strip tags but preserve all
readable content, including cross-references and examples. Fancy structure
parsing (e.g. sense detection from `<sense>` elements) is handled elsewhere.
"""
from __future__ import annotations

import html
import re
import unicodedata

from bs4 import BeautifulSoup
from lxml import etree as lxml_etree
from lxml import html as lxml_html


_WHITESPACE_RE = re.compile(r"[ \t\u00A0]+")
_NEWLINES_RE = re.compile(r"\n{2,}")
_SPACE_AROUND_PUNCT_RE = re.compile(r"\s+([,;.:])")


def strip_markup(
    markup: str,
    source_format: str = "xdxf",
    flags: list[str] | None = None,
) -> str:
    """Strip HTML/XDXF markup and return clean plain text.

    Args:
        markup: Raw body content from v1 dict.sqlite.
        source_format: Hint for parser selection. `xdxf`, `sandic`, `gretil`
            use lxml. `apple_dict` uses BeautifulSoup (more lenient for
            malformed HTML common in Apple dictionary bundles).
        flags: Optional list receiving QA flags when cleanup degraded. The
            string `"body-markup-fallback"` is appended if the primary parser
            failed and regex fallback was used. Callers can attach this to
            the entry's `flags` field.

    Returns:
        Plain text with normalized whitespace. Semicolons, periods, numbers,
        and cross-reference markers preserved.
    """
    if not markup:
        return ""

    # Fast path: no markup at all
    if "<" not in markup and "&" not in markup:
        return _clean_whitespace(markup)

    try:
        if source_format == "apple_dict":
            text = _strip_bs4(markup)
        else:
            text = _strip_lxml(markup)
    except (lxml_etree.LxmlError, ValueError, TypeError, AttributeError):
        # Narrow catch: lxml parsing / bs4 value errors on malformed markup.
        # MemoryError, KeyboardInterrupt, etc. propagate so real bugs surface.
        if flags is not None:
            flags.append("body-markup-fallback")
        text = _strip_regex(markup)

    return _clean_whitespace(text)


def _strip_lxml(markup: str) -> str:
    """lxml-based stripping. Fast and strict."""
    # Wrap in a root element so fragments parse without warnings.
    wrapped = f"<root>{markup}</root>"
    tree = lxml_html.fragment_fromstring(wrapped, create_parent=False)
    return tree.text_content()


def _strip_bs4(markup: str) -> str:
    """BeautifulSoup-based stripping. Lenient for malformed Apple dict HTML."""
    soup = BeautifulSoup(markup, "lxml")
    # Replace <br> with newlines before extracting text
    for br in soup.find_all("br"):
        br.replace_with("\n")
    return soup.get_text(separator=" ")


_TAG_RE = re.compile(r"<[^>]+>")


def _strip_regex(markup: str) -> str:
    """Last-resort fallback: regex tag stripping."""
    text = _TAG_RE.sub(" ", markup)
    return html.unescape(text)


def _clean_whitespace(text: str) -> str:
    """Normalize whitespace while preserving paragraph structure."""
    # Unicode NFC so diacritics are in precomposed form
    text = unicodedata.normalize("NFC", text)
    # Collapse runs of inline whitespace
    text = _WHITESPACE_RE.sub(" ", text)
    # Collapse multiple blank lines to one
    text = _NEWLINES_RE.sub("\n", text)
    # Remove whitespace before punctuation
    text = _SPACE_AROUND_PUNCT_RE.sub(r"\1", text)
    return text.strip()
