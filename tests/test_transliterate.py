"""Tests for scripts.lib.transliterate (copied from v1)."""
from scripts.lib.transliterate import (
    detect_and_convert_to_iast,
    devanagari_to_iast,
    hk_to_iast,
    normalize,
    normalize_headword,
    slp1_to_iast,
)


class TestHKToIAST:
    def test_basic_vowels(self):
        assert hk_to_iast("A") == "ā"
        assert hk_to_iast("I") == "ī"
        assert hk_to_iast("U") == "ū"

    def test_retroflex(self):
        assert hk_to_iast("T") == "ṭ"
        assert hk_to_iast("D") == "ḍ"
        assert hk_to_iast("N") == "ṇ"

    def test_sibilants(self):
        assert hk_to_iast("z") == "ś"
        assert hk_to_iast("S") == "ṣ"

    def test_vocalic_r(self):
        assert hk_to_iast("R") == "ṛ"
        assert hk_to_iast("RR") == "ṝ"

    def test_word_examples(self):
        assert hk_to_iast("dharma") == "dharma"
        assert hk_to_iast("prajJApAramitA") == "prajñāpāramitā"
        assert hk_to_iast("ajJa") == "ajña"


class TestDevanagariToIAST:
    def test_dharma(self):
        assert devanagari_to_iast("धर्म") == "dharma"

    def test_bodhisattva(self):
        assert devanagari_to_iast("बोधिसत्त्व") == "bodhisattva"

    def test_prajnaparamita(self):
        assert devanagari_to_iast("प्रज्ञापारमिता") == "prajñāpāramitā"

    def test_empty(self):
        assert devanagari_to_iast("") == ""


class TestSLP1ToIAST:
    def test_basic(self):
        assert slp1_to_iast("Darma") == "ḍarma"  # SLP1 'D' = ḍ

    def test_vowels(self):
        assert slp1_to_iast("AtmA") == "ātmā"


class TestDetectAndConvert:
    def test_devanagari_detected(self):
        assert detect_and_convert_to_iast("धर्म") == "dharma"

    def test_hk_detected(self):
        assert detect_and_convert_to_iast("prajJA") == "prajñā"

    def test_iast_passthrough(self):
        assert detect_and_convert_to_iast("dharma") == "dharma"
        assert detect_and_convert_to_iast("prajñā") == "prajñā"

    def test_empty(self):
        assert detect_and_convert_to_iast("") == ""

    def test_english_word_not_misread(self):
        # 'z' alone is not a reliable HK signature — see transliterate.py docstring
        # "amaze" should NOT be converted to "amaśe"
        assert detect_and_convert_to_iast("amaze") == "amaze"


class TestNormalize:
    def test_nfd_strip(self):
        # ā decomposes to a + combining macron; normalize strips combining marks
        assert normalize("ā") == "a"
        assert normalize("dharma") == "dharma"
        assert normalize("prajñā") == "prajna"

    def test_lowercase(self):
        assert normalize("DHARMA") == "dharma"

    def test_trim(self):
        assert normalize("  dharma  ") == "dharma"


class TestNormalizeHeadword:
    def test_devanagari_pipeline(self):
        assert normalize_headword("धर्म") == "dharma"

    def test_hk_pipeline(self):
        assert normalize_headword("prajJApAramitA") == "prajnaparamita"

    def test_iast_pipeline(self):
        assert normalize_headword("prajñā") == "prajna"

    def test_mixed_case(self):
        assert normalize_headword("Dharma") == "dharma"
