"""
Package: tests.test_slime_mold
Tests for the Physarum polycephalum slime mold simulation fill (N10).

Covers: output shape, boundary constraints, determinism, edge cases,
parameter variants, and pipeline integration via render().
"""

import logging as _logging
import math

import pytest

from justdoit.effects.generative import slime_mold_fill
from justdoit.core.glyph import glyph_to_mask
from justdoit.core.rasterizer import render, _FILL_FNS
from justdoit.fonts.builtin.block import BLOCK

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "tests.test_slime_mold"
__updated__ = "2026-03-26 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_GLYPH_A = BLOCK["A"]
_GLYPH_H = BLOCK["H"]
_MASK_A  = glyph_to_mask(_GLYPH_A)
_MASK_H  = glyph_to_mask(_GLYPH_H)

# A minimal hand-crafted 5×5 mask (checkerboard of ink)
_SIMPLE_MASK = [
    [1.0, 1.0, 1.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0, 1.0],
]


# -------------------------------------------------------------------------
# Shape / dimension tests

def test_slime_output_row_count():
    """Output has the same number of rows as the input mask."""
    result = slime_mold_fill(_MASK_A, seed=0, steps=20, n_agents=20)
    assert len(result) == len(_MASK_A)


def test_slime_output_col_width():
    """Each output row has the same width as the corresponding mask row."""
    result = slime_mold_fill(_MASK_A, seed=0, steps=20, n_agents=20)
    for r, (mask_row, out_row) in enumerate(zip(_MASK_A, result)):
        assert len(out_row) == len(mask_row), f"Row {r} width mismatch"


def test_slime_output_empty_mask():
    """Empty mask returns empty list."""
    assert slime_mold_fill([]) == []


def test_slime_output_all_empty_cells():
    """All-empty mask (no ink) returns space-only rows."""
    empty = [[0.0] * 5 for _ in range(3)]
    result = slime_mold_fill(empty, seed=0, steps=10, n_agents=5)
    for row in result:
        assert row == " " * 5


# -------------------------------------------------------------------------
# Boundary constraint tests

def test_slime_empty_cells_are_spaces():
    """Cells outside the ink mask must always be rendered as spaces."""
    result = slime_mold_fill(_MASK_A, seed=7, steps=50, n_agents=50)
    for r, mask_row in enumerate(_MASK_A):
        for c, val in enumerate(mask_row):
            if val < 0.5:
                assert result[r][c] == " ", (
                    f"Non-space character '{result[r][c]}' in empty cell ({r},{c})"
                )


def test_slime_ink_cells_nonempty():
    """Ink cells must receive a non-space character after simulation."""
    result = slime_mold_fill(_MASK_A, seed=42, steps=80, n_agents=100)
    ink_chars = [
        result[r][c]
        for r, row in enumerate(_MASK_A)
        for c, val in enumerate(row)
        if val >= 0.5
    ]
    assert len(ink_chars) > 0
    assert any(ch != " " for ch in ink_chars), "All ink cells rendered as spaces"


# -------------------------------------------------------------------------
# Determinism / reproducibility

def test_slime_seeded_reproducible():
    """Same seed and parameters must produce identical output."""
    a = slime_mold_fill(_MASK_A, seed=1, steps=40, n_agents=50)
    b = slime_mold_fill(_MASK_A, seed=1, steps=40, n_agents=50)
    assert a == b, "Seeded runs produced different results"


def test_slime_different_seeds_vary():
    """Different seeds must produce different output (with high probability)."""
    a = slime_mold_fill(_MASK_A, seed=10, steps=60, n_agents=80)
    b = slime_mold_fill(_MASK_A, seed=11, steps=60, n_agents=80)
    assert a != b, "Different seeds produced identical output"


# -------------------------------------------------------------------------
# Parameter variation tests

def test_slime_minimal_agents():
    """Works with a single agent and minimal steps."""
    result = slime_mold_fill(_MASK_A, seed=0, steps=5, n_agents=1)
    assert len(result) == len(_MASK_A)


def test_slime_many_agents():
    """Works with more agents than ink cells."""
    result = slime_mold_fill(_SIMPLE_MASK, seed=0, steps=10, n_agents=200)
    assert len(result) == len(_SIMPLE_MASK)


def test_slime_zero_steps():
    """Zero simulation steps should not raise; returns valid shape."""
    result = slime_mold_fill(_MASK_A, seed=0, steps=0, n_agents=20)
    assert len(result) == len(_MASK_A)
    for r, mask_row in enumerate(_MASK_A):
        assert len(result[r]) == len(mask_row)


def test_slime_zero_decay():
    """Decay=0.0 (no evaporation) should not raise."""
    result = slime_mold_fill(_MASK_A, seed=0, steps=30, n_agents=30, decay=0.0)
    assert len(result) == len(_MASK_A)


def test_slime_full_decay():
    """Decay=1.0 (instant evaporation) should not raise; output is valid shape."""
    result = slime_mold_fill(_MASK_A, seed=0, steps=30, n_agents=30, decay=1.0)
    assert len(result) == len(_MASK_A)


def test_slime_custom_density_chars():
    """Custom density_chars are respected — output chars are from the provided set."""
    chars = "XO."
    result = slime_mold_fill(_MASK_A, seed=0, steps=30, n_agents=40,
                             density_chars=chars)
    valid = set(chars) | {" "}
    for r, row in enumerate(result):
        for c, ch in enumerate(row):
            assert ch in valid, f"Unexpected char '{ch}' at ({r},{c})"


def test_slime_sensor_angle_variation():
    """Different sensor angles produce different trace patterns."""
    a = slime_mold_fill(_MASK_H, seed=5, steps=60, n_agents=80,
                        sensor_angle=math.radians(15))
    b = slime_mold_fill(_MASK_H, seed=5, steps=60, n_agents=80,
                        sensor_angle=math.radians(45))
    assert a != b, "Different sensor angles produced identical output"


def test_slime_different_glyphs_differ():
    """Different glyph masks produce different outputs (same seed)."""
    a = slime_mold_fill(_MASK_A, seed=99, steps=60, n_agents=80)
    b = slime_mold_fill(_MASK_H, seed=99, steps=60, n_agents=80)
    assert a != b, "Different glyph masks produced identical output"


# -------------------------------------------------------------------------
# Pipeline integration

def test_slime_via_render():
    """render(fill='slime') works end-to-end without error."""
    result = render("A", font="block", fill="slime")
    assert isinstance(result, str)
    assert len(result) > 0


def test_slime_via_render_multichar():
    """render(fill='slime') works on multi-character strings."""
    result = render("HI", font="block", fill="slime")
    assert isinstance(result, str)
    assert len(result) > 0


def test_slime_fill_registered():
    """'slime' key must be present in the rasterizer fill registry."""
    assert "slime" in _FILL_FNS
    assert _FILL_FNS["slime"] is slime_mold_fill
