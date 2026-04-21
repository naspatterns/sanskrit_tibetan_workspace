"""Tests for scripts.lib.html_utils."""
from scripts.lib.html_utils import strip_markup


class TestStripMarkupXDXF:
    def test_no_markup(self):
        assert strip_markup("plain text") == "plain text"

    def test_strip_basic_tags(self):
        assert strip_markup("<i>m.</i> fire") == "m. fire"

    def test_strip_nested(self):
        result = strip_markup("<b><i>dharma</i></b>: virtue")
        assert "dharma" in result
        assert "virtue" in result
        assert "<" not in result

    def test_html_entities(self):
        result = strip_markup("a &amp; b")
        assert "a" in result and "b" in result

    def test_empty(self):
        assert strip_markup("") == ""


class TestStripMarkupApple:
    def test_basic(self):
        html = '<div class="entry"><span>dharma</span> — virtue</div>'
        result = strip_markup(html, source_format="apple_dict")
        assert "dharma" in result
        assert "virtue" in result

    def test_br_to_newline(self):
        html = "line1<br/>line2"
        result = strip_markup(html, source_format="apple_dict")
        assert "line1" in result
        assert "line2" in result


class TestWhitespaceCleanup:
    def test_collapse_spaces(self):
        assert strip_markup("<i>a</i>   <i>b</i>") == "a b"

    def test_trim(self):
        assert strip_markup("  text  ") == "text"

    def test_space_before_punctuation(self):
        assert strip_markup("hello <i>world</i> , foo") == "hello world, foo"
