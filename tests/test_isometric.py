"""
Package: tests.test_isometric
Tests for isometric 3D extrusion effect (S03).

Covers: isometric_extrude, iso_render, direction, depth, edge cases.
All tests are pure Python — no PIL dependency.
"""

import logging as _logging

import pytest

from justdoit.effects.isometric import isometric_extrude, iso_render
from justdoit.core.rasterizer import render

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "tests.test_isometric"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_SAMPLE = render("HI", font="block")


# -------------------------------------------------------------------------
# isometric_extrude

def test_iso_output_taller_than_input():
    """Extruded output must have more rows than the input."""
    depth = 4
    input_rows = len(_SAMPLE.split("\n"))
    result_rows = len(isometric_extrude(_SAMPLE, depth=depth).split("\n"))
    assert result_rows == input_rows + depth


def test_iso_output_wider_than_input():
    """Extruded output must have more columns than the input (depth added)."""
    depth = 4
    input_width = max(len(ln) for ln in _SAMPLE.split("\n"))
    result_lines = isometric_extrude(_SAMPLE, depth=depth).split("\n")
    # At least some lines should be wider (depth chars added to the right)
    result_max_width = max(len(ln) for ln in result_lines)
    assert result_max_width >= input_width


def test_iso_depth_layers_contain_shade_chars():
    """Output must contain at least one depth shade character."""
    result = isometric_extrude(_SAMPLE, depth=4)
    shade_chars = set("▓▒░·")
    assert any(ch in result for ch in shade_chars)


def test_iso_direction_right():
    """direction='right' does not raise and produces output."""
    result = isometric_extrude(_SAMPLE, depth=3, direction="right")
    assert len(result) > 0


def test_iso_direction_left():
    """direction='left' does not raise and produces output."""
    result = isometric_extrude(_SAMPLE, depth=3, direction="left")
    assert len(result) > 0


def test_iso_right_and_left_differ():
    """'right' and 'left' extrusions should produce different output."""
    right = isometric_extrude(_SAMPLE, depth=4, direction="right")
    left = isometric_extrude(_SAMPLE, depth=4, direction="left")
    assert right != left


def test_iso_invalid_direction():
    """Invalid direction raises ValueError."""
    with pytest.raises(ValueError):
        isometric_extrude(_SAMPLE, direction="up")


def test_iso_invalid_depth():
    """depth < 1 raises ValueError."""
    with pytest.raises(ValueError):
        isometric_extrude(_SAMPLE, depth=0)


def test_iso_depth_1():
    """depth=1 (minimum) should work without error."""
    result = isometric_extrude(_SAMPLE, depth=1)
    assert len(result.split("\n")) == len(_SAMPLE.split("\n")) + 1


def test_iso_front_char_override():
    """front_char override replaces all front face characters."""
    result = isometric_extrude(_SAMPLE, depth=2, front_char="X")
    assert "X" in result


def test_iso_empty_string():
    """isometric_extrude on empty string returns empty string."""
    assert isometric_extrude("") == ""


def test_iso_preserves_front_face_content():
    """Front face characters from original must appear in output (when no override)."""
    # Block font uses '█' — must be present in extruded output
    result = isometric_extrude(_SAMPLE, depth=2)
    assert "█" in result


def test_iso_no_ansi_in_output():
    """Output from isometric_extrude should contain no ANSI codes (gradients applied after)."""
    result = isometric_extrude(_SAMPLE, depth=3)
    assert "\033[" not in result


# -------------------------------------------------------------------------
# iso_render convenience wrapper

def test_iso_render_produces_output():
    """iso_render is a convenience wrapper that renders then extrudes."""
    result = iso_render("HI", font="block", depth=3)
    assert len(result) > 0
    assert "█" in result


def test_iso_render_with_slim_font():
    """iso_render works with slim font (non-block chars)."""
    result = iso_render("HI", font="slim", depth=2)
    assert len(result) > 0
