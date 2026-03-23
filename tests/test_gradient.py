"""
Package: tests.test_gradient
Tests for true-color gradient and palette effects (C01, C02, C03, C07).

Covers: parse_color, tc, linear_gradient, radial_gradient, per_glyph_palette.
All tests are pure Python — no PIL dependency.
"""

import logging as _logging

import pytest

from justdoit.effects.gradient import (
    parse_color, tc,
    linear_gradient, radial_gradient, per_glyph_palette,
    PRESETS, NAMED_COLORS,
)
from justdoit.core.rasterizer import render

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "tests.test_gradient"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_SAMPLE = render("HI", font="block")


# -------------------------------------------------------------------------
# parse_color

def test_parse_color_named():
    """Named colors resolve to correct RGB tuples."""
    assert parse_color("red") == (255, 50, 50)
    assert parse_color("cyan") == (80, 220, 220)


def test_parse_color_hex():
    """Hex strings (with and without #) parse correctly."""
    assert parse_color("ff0000") == (255, 0, 0)
    assert parse_color("#00ff80") == (0, 255, 128)


def test_parse_color_invalid():
    """Unknown color spec raises ValueError."""
    with pytest.raises(ValueError):
        parse_color("notacolor")


# -------------------------------------------------------------------------
# tc (true-color code)

def test_tc_produces_ansi_escape():
    """tc() returns a string containing the 24-bit ANSI escape prefix."""
    code = tc(255, 128, 0)
    assert "\033[38;2;" in code
    assert "255;128;0" in code


def test_tc_resets_are_present_in_gradient():
    """linear_gradient output contains reset codes."""
    result = linear_gradient(_SAMPLE, (255, 0, 0), (0, 0, 255))
    assert "\033[0m" in result


# -------------------------------------------------------------------------
# linear_gradient (C01)

def test_linear_gradient_returns_same_line_count():
    """linear_gradient must not add or remove lines."""
    original = _SAMPLE.split("\n")
    result = linear_gradient(_SAMPLE, (255, 0, 0), (0, 0, 255)).split("\n")
    assert len(result) == len(original)


def test_linear_gradient_horizontal_contains_true_color():
    """Horizontal gradient output must contain 24-bit ANSI codes."""
    result = linear_gradient(_SAMPLE, (255, 0, 0), (0, 0, 255), direction="horizontal")
    assert "\033[38;2;" in result


def test_linear_gradient_vertical():
    """Vertical gradient does not raise and preserves line count."""
    result = linear_gradient(_SAMPLE, (0, 255, 0), (0, 0, 255), direction="vertical")
    assert len(result.split("\n")) == len(_SAMPLE.split("\n"))


def test_linear_gradient_diagonal():
    """Diagonal gradient does not raise and preserves line count."""
    result = linear_gradient(_SAMPLE, (255, 255, 0), (0, 0, 128), direction="diagonal")
    assert len(result.split("\n")) == len(_SAMPLE.split("\n"))


def test_linear_gradient_invalid_direction():
    """Invalid direction raises ValueError."""
    with pytest.raises(ValueError):
        linear_gradient(_SAMPLE, (255, 0, 0), (0, 0, 255), direction="sideways")


def test_linear_gradient_empty_string():
    """linear_gradient on empty string returns empty string."""
    assert linear_gradient("", (255, 0, 0), (0, 0, 255)) == ""


# -------------------------------------------------------------------------
# radial_gradient (C02)

def test_radial_gradient_returns_same_line_count():
    """radial_gradient must not add or remove lines."""
    original = _SAMPLE.split("\n")
    result = radial_gradient(_SAMPLE, (255, 255, 255), (0, 0, 100)).split("\n")
    assert len(result) == len(original)


def test_radial_gradient_contains_true_color():
    """Radial gradient output must contain 24-bit ANSI codes."""
    result = radial_gradient(_SAMPLE, (255, 255, 0), (0, 0, 200))
    assert "\033[38;2;" in result


def test_radial_gradient_empty_string():
    """radial_gradient on empty string returns empty string."""
    assert radial_gradient("", (255, 0, 0), (0, 0, 255)) == ""


# -------------------------------------------------------------------------
# per_glyph_palette (C03)

def test_per_glyph_palette_returns_same_line_count():
    """per_glyph_palette must not add or remove lines."""
    original = _SAMPLE.split("\n")
    result = per_glyph_palette(_SAMPLE, PRESETS["fire"]).split("\n")
    assert len(result) == len(original)


def test_per_glyph_palette_contains_true_color():
    """per_glyph_palette output must contain 24-bit ANSI codes."""
    result = per_glyph_palette(_SAMPLE, PRESETS["neon"])
    assert "\033[38;2;" in result


def test_per_glyph_palette_empty_palette_raises():
    """Empty palette raises ValueError."""
    with pytest.raises(ValueError):
        per_glyph_palette(_SAMPLE, [])


def test_per_glyph_palette_all_presets():
    """All built-in palette presets apply without error."""
    for name, palette in PRESETS.items():
        result = per_glyph_palette(_SAMPLE, palette)
        assert "\033[38;2;" in result, f"Preset '{name}' produced no true-color codes"


def test_per_glyph_palette_empty_string():
    """per_glyph_palette on empty string returns empty string."""
    assert per_glyph_palette("", PRESETS["ocean"]) == ""
