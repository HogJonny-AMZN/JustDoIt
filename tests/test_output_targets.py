"""
Package: tests.test_output_targets
Tests for HTML, SVG, and PNG output targets (O01, O02, O03).

All tests exercise the public API and validate structure of the output.
PNG tests are gated on Pillow via pytest.importorskip.
"""

import logging as _logging
import os
import tempfile

import pytest

from justdoit.output.ansi_parser import parse, effective_color, DEFAULT_COLOR
from justdoit.output.html import to_html, save_html
from justdoit.output.svg import to_svg, save_svg
from justdoit.core.rasterizer import render
from justdoit.effects.gradient import linear_gradient

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "tests.test_output_targets"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_PLAIN   = render("HI", font="block")
_COLORED = linear_gradient(_PLAIN, (255, 0, 0), (0, 0, 255))


# -------------------------------------------------------------------------
# ansi_parser

def test_parse_plain_text():
    """parse() on plain text returns correct chars with no color."""
    tokens = parse("AB")
    chars = [ch for ch, _ in tokens if ch != "\n"]
    assert chars == ["A", "B"]
    assert all(color is None for _, color in tokens)


def test_parse_truecolor():
    """parse() extracts 24-bit RGB color from true-color ANSI codes."""
    text = "\033[38;2;255;128;0mX\033[0m"
    tokens = [(ch, color) for ch, color in parse(text) if ch != "\n"]
    assert tokens[0] == ("X", (255, 128, 0))


def test_parse_reset():
    """parse() resets color on \033[0m."""
    text = "\033[38;2;255;0;0mA\033[0mB"
    tokens = [(ch, color) for ch, color in parse(text) if ch not in ("\n",)]
    assert tokens[0] == ("A", (255, 0, 0))
    assert tokens[1] == ("B", None)


def test_effective_color_none():
    """effective_color(None) returns DEFAULT_COLOR."""
    assert effective_color(None) == DEFAULT_COLOR


def test_effective_color_tuple():
    """effective_color((r,g,b)) returns the tuple unchanged."""
    assert effective_color((1, 2, 3)) == (1, 2, 3)


# -------------------------------------------------------------------------
# HTML output (O01)

def test_html_full_page_structure():
    """to_html() full page contains DOCTYPE, html, head, body, pre."""
    html = to_html(_PLAIN)
    assert "<!DOCTYPE html>" in html
    assert "<html>" in html
    assert "<pre>" in html
    assert "</pre>" in html
    assert "</html>" in html


def test_html_snippet_no_doctype():
    """to_html() with full_page=False returns only a <pre> snippet."""
    html = to_html(_PLAIN, full_page=False)
    assert html.startswith("<pre>")
    assert "<!DOCTYPE" not in html


def test_html_contains_span_for_colored():
    """to_html() on colored text contains <span style=...> elements."""
    html = to_html(_COLORED, full_page=False)
    assert "<span style=" in html


def test_html_contains_visible_chars():
    """to_html() output contains at least some visible block characters."""
    html = to_html(_PLAIN, full_page=False)
    assert "█" in html


def test_html_escapes_special_chars():
    """to_html() properly escapes < > & in content."""
    from justdoit.output.html import to_html as _to_html
    html = _to_html("<test>&", full_page=False)
    assert "&lt;" in html
    assert "&gt;" in html
    assert "&amp;" in html


def test_save_html_writes_file():
    """save_html() creates a file at the given path."""
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
        path = f.name
    try:
        save_html(_PLAIN, path)
        assert os.path.exists(path)
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "<pre>" in content
    finally:
        os.unlink(path)


# -------------------------------------------------------------------------
# SVG output (O02)

def test_svg_structure():
    """to_svg() returns a valid SVG document."""
    svg = to_svg(_PLAIN)
    assert svg.startswith("<?xml")
    assert "<svg " in svg
    assert "</svg>" in svg


def test_svg_contains_text_elements():
    """to_svg() contains <text> elements for visible characters."""
    svg = to_svg(_PLAIN)
    assert "<text " in svg


def test_svg_colored_has_fill():
    """to_svg() on colored text includes fill= attributes."""
    svg = to_svg(_COLORED)
    assert 'fill="#' in svg


def test_svg_background_rect():
    """to_svg() includes a background <rect>."""
    svg = to_svg(_PLAIN)
    assert "<rect " in svg


def test_svg_custom_bg():
    """to_svg() respects bg_color parameter."""
    svg = to_svg(_PLAIN, bg_color="#222233")
    assert "#222233" in svg


def test_save_svg_writes_file():
    """save_svg() creates a file at the given path."""
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        path = f.name
    try:
        save_svg(_PLAIN, path)
        assert os.path.exists(path)
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "<svg " in content
    finally:
        os.unlink(path)


# -------------------------------------------------------------------------
# PNG output (O03) — gated on Pillow

def test_png_to_image_returns_image():
    """to_image() returns a PIL Image of non-zero size."""
    pytest.importorskip("PIL")
    from justdoit.output.image import to_image
    img = to_image(_PLAIN, font_size=14)
    assert img.width > 0
    assert img.height > 0


def test_png_to_image_colored():
    """to_image() works with true-color gradient input."""
    pytest.importorskip("PIL")
    from justdoit.output.image import to_image
    img = to_image(_COLORED, font_size=14)
    assert img.width > 0


def test_save_png_writes_file():
    """save_png() creates a valid PNG file."""
    pytest.importorskip("PIL")
    from justdoit.output.image import save_png
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name
    try:
        save_png(_PLAIN, path, font_size=14)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
        # Verify PNG magic bytes
        with open(path, "rb") as f:
            magic = f.read(4)
        assert magic == b"\x89PNG"
    finally:
        os.unlink(path)
