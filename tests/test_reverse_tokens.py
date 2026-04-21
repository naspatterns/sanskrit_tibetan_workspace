"""Tests for scripts.lib.reverse_tokens (FB-8 reverse search preparation)."""
from scripts.lib.reverse_tokens import (
    MAX_TOKENS,
    STOPWORDS_EN,
    extract_en_tokens,
    extract_ko_tokens,
)


class TestExtractEnTokens:
    def test_basic(self):
        text = "fire; the god of fire; sacrificial fire"
        tokens = extract_en_tokens(text)
        assert "fire" in tokens
        assert "god" in tokens
        assert "sacrificial" in tokens
        # stopwords filtered
        assert "the" not in tokens
        assert "of" not in tokens

    def test_grammar_abbreviations_filtered(self):
        text = "m. fire; f. goddess; n. chariot"
        tokens = extract_en_tokens(text)
        # m./f./n. should be filtered as stopwords
        assert "m" not in tokens
        assert "f" not in tokens
        assert "n" not in tokens
        assert "fire" in tokens
        assert "goddess" in tokens

    def test_lowercase(self):
        text = "Fire God Sacrificial"
        tokens = extract_en_tokens(text)
        # All should be lowercased
        for t in tokens:
            assert t == t.lower()

    def test_max_tokens_cap(self):
        text = " ".join(f"word{i}" for i in range(50))
        tokens = extract_en_tokens(text)
        assert len(tokens) <= MAX_TOKENS

    def test_position_weight_order(self):
        # First word should come before later words if both pass filter
        text = "fire " + " ".join(["lorem"] * 50) + " xenophile"
        tokens = extract_en_tokens(text)
        # "fire" appears early → high weight; "xenophile" appears late → lower weight
        assert "fire" in tokens
        # Order: fire should be ranked above xenophile
        if "xenophile" in tokens:
            assert tokens.index("fire") < tokens.index("xenophile")

    def test_empty(self):
        assert extract_en_tokens("") == []

    def test_dedupe(self):
        text = "fire fire fire god god"
        tokens = extract_en_tokens(text)
        # No duplicates
        assert len(tokens) == len(set(tokens))

    def test_min_length(self):
        text = "a b c d dharma"
        tokens = extract_en_tokens(text)
        # 1-letter tokens should be filtered
        for t in tokens:
            assert len(t) >= 2

    def test_stopwords_coverage(self):
        # Sanity check: stopword list is reasonable size
        assert len(STOPWORDS_EN) >= 50


class TestExtractKoTokens:
    def test_basic_split(self):
        text = "불; 불의 신; 희생 불"
        tokens = extract_ko_tokens(text)
        assert "불" in tokens

    def test_hanja_bracket(self):
        """The signature FB-8 case: 법(法) must yield BOTH 법 and 法."""
        text = "법(法); 규범, 조례"
        tokens = extract_ko_tokens(text)
        assert "법" in tokens
        assert "法" in tokens
        assert "규범" in tokens
        assert "조례" in tokens

    def test_multiple_hanja_brackets(self):
        text = "법(法), 도(道), 덕(德)"
        tokens = extract_ko_tokens(text)
        # All hangul + all hanja
        for t in ["법", "法", "도", "道", "덕", "德"]:
            assert t in tokens, f"Expected {t} in tokens, got {tokens}"

    def test_punctuation_split(self):
        text = "불, 화신; 불꽃"
        tokens = extract_ko_tokens(text)
        assert "불" in tokens
        assert "화신" in tokens
        assert "불꽃" in tokens

    def test_english_filtered(self):
        text = "법(法) fire 규범"
        tokens = extract_ko_tokens(text)
        # Latin words should not appear
        assert "fire" not in tokens
        assert "법" in tokens

    def test_empty(self):
        assert extract_ko_tokens("") == []

    def test_dedupe(self):
        text = "불 불 불 불"
        tokens = extract_ko_tokens(text)
        assert len(tokens) == len(set(tokens))

    def test_max_tokens_cap(self):
        # Make a body with many unique Korean tokens
        text = " ".join(f"단어{i}" for i in range(50))
        tokens = extract_ko_tokens(text)
        assert len(tokens) <= MAX_TOKENS
