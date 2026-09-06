"""The small markdown renderer used for the primers.

Worth testing directly because the primers wrap heavily across source lines,
and because it renders untrusted-ish text into HTML.
"""

from __future__ import annotations

from app.web.filters import render_markdown


class TestBlocks:
    def test_headings_shift_down_one_level(self):
        """The page already has an h1, so primer h1 becomes h2."""
        assert "<h2>Top</h2>" in str(render_markdown("# Top"))
        assert "<h3>Sub</h3>" in str(render_markdown("## Sub"))

    def test_wrapped_paragraph_joins(self):
        out = str(render_markdown("One line\nand its continuation."))
        assert out.count("<p>") == 1
        assert "One line and its continuation." in out

    def test_wrapped_list_item_stays_one_item(self):
        out = str(render_markdown("- First item that\n  wraps over two lines\n- Second"))
        assert out.count("<li>") == 2
        assert "First item that wraps over two lines" in out

    def test_numbered_and_bulleted_lists_are_distinct(self):
        out = str(render_markdown("1. one\n2. two\n\n- a\n- b"))
        assert "<ol>" in out and "<ul>" in out

    def test_wrapped_blockquote_is_one_paragraph(self):
        out = str(render_markdown("> A quote that\n> wraps."))
        assert out.count("<blockquote>") == 1
        assert "<p>A quote that wraps.</p>" in out

    def test_blank_line_closes_open_blocks(self):
        out = str(render_markdown("- item\n\nParagraph"))
        assert out.index("</ul>") < out.index("<p>Paragraph</p>")

    def test_empty_input_is_safe(self):
        assert str(render_markdown("")) == ""


class TestInline:
    def test_bold_and_italic_and_code(self):
        out = str(render_markdown("**bold** and *italic* and `code`"))
        assert "<strong>bold</strong>" in out
        assert "<em>italic</em>" in out
        assert "<code>code</code>" in out

    def test_html_is_escaped_before_formatting(self):
        out = str(render_markdown("<script>alert(1)</script>"))
        assert "<script>" not in out
        assert "&lt;script&gt;" in out

    def test_escaping_survives_inline_markup(self):
        out = str(render_markdown("**<img src=x onerror=y>**"))
        assert "<img" not in out
        assert "<strong>" in out


class TestRealPrimers:
    def test_every_primer_renders_without_leaking_markdown(self, seeded):
        from app import db
        from app.academy import content
        from app.academy.modules import MODULE_KEYS

        with db.session() as conn:
            for key in MODULE_KEYS:
                primer = content.get_primer(conn, key)
                out = str(render_markdown(primer["body"]))
                assert "<h3>" in out and "<p>" in out
                # No raw markdown syntax should survive into the output.
                for line in out.splitlines():
                    assert not line.startswith("## ")
                    assert not line.startswith("- ")
                assert "**" not in out
