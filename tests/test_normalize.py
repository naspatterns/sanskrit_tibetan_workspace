"""Tests for scripts.lib.normalize."""
from scripts.lib.normalize import (
    has_hk_signature,
    is_valid_iast,
    is_valid_wylie,
    normalize_whitespace,
)


class TestIsValidIAST:
    def test_plain_ascii(self):
        assert is_valid_iast("dharma")
        assert is_valid_iast("yoga")

    def test_with_diacritics(self):
        assert is_valid_iast("prajñā")
        assert is_valid_iast("pāramitā")
        assert is_valid_iast("saṃsāra")

    def test_capitalized(self):
        assert is_valid_iast("Dharma")
        assert is_valid_iast("Śiva")

    def test_with_allowed_punctuation(self):
        assert is_valid_iast("brahma-sūtra")
        assert is_valid_iast("a-kāra")

    def test_rejects_devanagari(self):
        assert not is_valid_iast("धर्म")

    def test_rejects_empty(self):
        assert not is_valid_iast("")

    def test_rejects_cjk(self):
        assert not is_valid_iast("法")


class TestHasHKSignature:
    def test_pure_iast_no_signature(self):
        assert not has_hk_signature("prajñā")
        assert not has_hk_signature("dharma")

    def test_hk_detected(self):
        # 'A' (long ā) + lowercase — HK signature
        assert has_hk_signature("prajJA")
        assert has_hk_signature("AtmA")

    def test_empty(self):
        assert not has_hk_signature("")

    def test_iast_with_diacritics_overrides_hk(self):
        # Even if it contains 'A', presence of ā disqualifies HK hypothesis
        assert not has_hk_signature("Ātmā")

    def test_all_uppercase_iast_not_hk(self):
        # Purāṇic Encyclopaedia uses uppercase IAST like 'ABALA' — NOT HK
        assert not has_hk_signature("ABALA")
        assert not has_hk_signature("ABHAYA")
        assert not has_hk_signature("A")


class TestIsValidWylie:
    def test_basic_wylie(self):
        assert is_valid_wylie("bod")
        assert is_valid_wylie("byang chub sems dpa'")

    def test_with_digits(self):
        assert is_valid_wylie("po1")

    def test_rejects_devanagari(self):
        assert not is_valid_wylie("धर्म")


class TestNormalizeWhitespace:
    def test_collapse_spaces(self):
        assert normalize_whitespace("a   b") == "a b"

    def test_trim(self):
        assert normalize_whitespace("  a b  ") == "a b"

    def test_tabs_and_newlines(self):
        assert normalize_whitespace("a\tb\nc") == "a b c"
