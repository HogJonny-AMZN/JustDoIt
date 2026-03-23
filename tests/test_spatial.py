"""
Package: tests.test_spatial
Tests for spatial transformation effects (S01, S02, S08).

Covers: sine_warp, perspective_tilt, shear.
All tests are pure Python — no PIL dependency.
"""

import logging as _logging

import pytest

from justdoit.effects.spatial import sine_warp, perspective_tilt, shear
from justdoit.core.rasterizer import render

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "tests.test_spatial"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_SAMPLE = render("HI", font="block")


# -------------------------------------------------------------------------
# sine_warp (S01)

def test_sine_warp_returns_same_line_count():
    """sine_warp must not add or remove lines."""
    original = _SAMPLE.split("\n")
    warped = sine_warp(_SAMPLE, amplitude=2.0).split("\n")
    assert len(warped) == len(original)


def test_sine_warp_rows_padded_with_spaces():
    """Rows with a positive offset must start with spaces."""
    warped = sine_warp(_SAMPLE, amplitude=5.0, frequency=0.5)
    lines = warped.split("\n")
    # At least one row should have a leading space (amplitude is large enough)
    assert any(line.startswith(" ") for line in lines)


def test_sine_warp_zero_amplitude_unchanged():
    """amplitude=0 should return the original string unchanged."""
    assert sine_warp(_SAMPLE, amplitude=0.0) == _SAMPLE


def test_sine_warp_empty_string():
    """sine_warp on empty string returns empty string."""
    assert sine_warp("") == ""


# -------------------------------------------------------------------------
# perspective_tilt (S02)

def test_perspective_tilt_returns_same_line_count():
    """perspective_tilt must not add or remove lines."""
    original = _SAMPLE.split("\n")
    tilted = perspective_tilt(_SAMPLE, strength=0.5).split("\n")
    assert len(tilted) == len(original)


def test_perspective_tilt_top_narrows_first_row():
    """direction='top': first row should be shorter (more compressed) than a mid row."""
    lines = perspective_tilt(_SAMPLE, strength=0.8, direction="top").split("\n")
    # The block font's last row is blank — compare first to a non-blank row in the lower half.
    non_blank = [ln.rstrip() for ln in lines if ln.strip()]
    assert len(non_blank) >= 2, "Need at least two non-blank rows to compare"
    first_content = non_blank[0]
    last_content = non_blank[-1]
    assert len(first_content) <= len(last_content)


def test_perspective_tilt_bottom_narrows_last_row():
    """direction='bottom': last row should be shorter than first row."""
    lines = perspective_tilt(_SAMPLE, strength=0.8, direction="bottom").split("\n")
    first_stripped = lines[0].rstrip()
    last_stripped = lines[-1].rstrip()
    assert len(last_stripped) <= len(first_stripped)


def test_perspective_tilt_zero_strength_unchanged():
    """strength=0 should return the original string unchanged."""
    assert perspective_tilt(_SAMPLE, strength=0.0) == _SAMPLE


def test_perspective_tilt_invalid_direction():
    """Invalid direction raises ValueError."""
    with pytest.raises(ValueError):
        perspective_tilt(_SAMPLE, direction="sideways")


def test_perspective_tilt_empty_string():
    """perspective_tilt on empty string returns empty string."""
    assert perspective_tilt("") == ""


# -------------------------------------------------------------------------
# shear (S08)

def test_shear_returns_same_line_count():
    """shear must not add or remove lines."""
    original = _SAMPLE.split("\n")
    sheared = shear(_SAMPLE, amount=1.0).split("\n")
    assert len(sheared) == len(original)


def test_shear_offsets_increase_with_row():
    """Right shear: each row should have >= as many leading spaces as the previous."""
    lines = shear(_SAMPLE, amount=1.0, direction="right").split("\n")
    leading = [len(line) - len(line.lstrip(" ")) for line in lines]
    for i in range(1, len(leading)):
        assert leading[i] >= leading[i - 1]


def test_shear_zero_amount_unchanged():
    """amount=0 should return the original string unchanged."""
    assert shear(_SAMPLE, amount=0.0) == _SAMPLE


def test_shear_invalid_direction():
    """Invalid direction raises ValueError."""
    with pytest.raises(ValueError):
        shear(_SAMPLE, direction="diagonal")


def test_shear_empty_string():
    """shear on empty string returns empty string."""
    assert shear("") == ""
