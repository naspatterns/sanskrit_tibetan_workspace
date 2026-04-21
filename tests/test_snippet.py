"""Tests for scripts.lib.snippet (FB-1 smart snippets)."""
from scripts.lib.snippet import (
    SNIPPET_MEDIUM_MAX,
    SNIPPET_SHORT_MAX,
    extract_senses,
    extract_snippets,
    find_boundaries,
)


class TestFindBoundaries:
    def test_semicolon(self):
        text = "fire; the god of fire; sacrificial fire"
        b = find_boundaries(text)
        assert len(b) >= 2  # two semicolons + end

    def test_numbered_senses(self):
        text = "established order -2 virtue, righteousness -3 duty"
        b = find_boundaries(text)
        # Should detect -2 and -3 markers
        assert len(b) >= 3

    def test_empty(self):
        b = find_boundaries("")
        assert b == [0]


class TestExtractSnippets:
    def test_short_text(self):
        text = "fire"
        short, medium = extract_snippets(text)
        assert short == "fire"
        assert medium == "fire"

    def test_dharma_mw(self):
        """Based on MW 'dharma' example from docs/schema.json."""
        text = (
            "m. that which is established or firm, steadfast decree, statute, "
            "ordinance, law; usage, practice, customary observance or prescribed "
            "conduct, duty; right, justice"
        )
        short, medium = extract_snippets(text)
        assert len(short) <= SNIPPET_SHORT_MAX
        assert len(medium) <= SNIPPET_MEDIUM_MAX
        # snippet_short should contain the first clause ending at semicolon
        assert "decree" in short or "statute" in short
        # snippet_medium should include more content
        assert len(medium) >= len(short)

    def test_apte_numbered_senses(self):
        """Apte-style `-2 -3` numbered senses."""
        text = (
            "Religion; the customary observances of a caste, sect, &c.; law, "
            "usage, practice, custom, ordinance, statue. -2 Religious or moral "
            "merit, virtue, righteousness, good works. -3 Duty, prescribed "
            "course of conduct."
        )
        short, medium = extract_snippets(text)
        assert "Religion" in short
        assert len(short) <= SNIPPET_SHORT_MAX
        assert len(medium) <= SNIPPET_MEDIUM_MAX

    def test_empty(self):
        short, medium = extract_snippets("")
        assert short == ""
        assert medium == ""

    def test_long_no_boundaries(self):
        """Very long text with no natural boundaries → must still cap length."""
        text = "x" * 600
        short, medium = extract_snippets(text)
        # Must fit inside schema.json limits (snippet_short ≤180, snippet_medium ≤500)
        assert len(short) <= SNIPPET_SHORT_MAX
        assert len(medium) <= SNIPPET_MEDIUM_MAX


class TestExtractSenses:
    def test_apte_numbered(self):
        text = (
            "Religion; customary observances. -2 Religious merit, virtue. "
            "-3 Duty, prescribed conduct. -4 Law."
        )
        senses = extract_senses(text)
        assert len(senses) >= 3
        # Senses should have 'num' and 'text' keys
        for s in senses:
            assert "num" in s
            assert "text" in s

    def test_flat_no_senses(self):
        text = "simple definition with no numbering"
        senses = extract_senses(text)
        assert senses == []

    def test_empty(self):
        assert extract_senses("") == []
