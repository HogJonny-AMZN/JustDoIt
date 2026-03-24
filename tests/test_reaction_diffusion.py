"""
Package: tests.test_reaction_diffusion
Tests for reaction-diffusion fill (F04) — Gray-Scott model.

Covers: output shape, row widths, empty/ink cell handling, seeded
reproducibility, different seeds diverge, empty mask, all presets,
render() integration, and fill registry presence.
All tests are pure Python — no PIL dependency.
"""

import logging as _logging

import pytest

from justdoit.effects.generative import reaction_diffusion_fill, _RD_PRESETS
from justdoit.core.glyph import glyph_to_mask
from justdoit.core.rasterizer import render, _FILL_FNS
from justdoit.fonts.builtin.block import BLOCK

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "tests.test_reaction_diffusion"
__updated__ = "2026-03-24 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_GLYPH_A = BLOCK["A"]
_MASK_A  = glyph_to_mask(_GLYPH_A)


# -------------------------------------------------------------------------
# Shape and structure

def test_rd_fill_output_shape():
    """reaction_diffusion_fill output has same row count as input mask."""
    result = reaction_diffusion_fill(_MASK_A, seed=0, steps=10)
    assert len(result) == len(_MASK_A)


def test_rd_fill_row_widths_match():
    """reaction_diffusion_fill rows have same width as mask rows."""
    result = reaction_diffusion_fill(_MASK_A, seed=0, steps=10)
    for r, (orig, filled) in enumerate(zip(_MASK_A, result)):
        assert len(filled) == len(orig), f"Row {r} width mismatch"


def test_rd_fill_empty_cells_are_spaces():
    """reaction_diffusion_fill empty cells (mask < 0.5) must be spaces."""
    result = reaction_diffusion_fill(_MASK_A, seed=0, steps=10)
    for r, row in enumerate(_MASK_A):
        for c, val in enumerate(row):
            if val < 0.5:
                assert result[r][c] == " ", f"Empty cell ({r},{c}) not a space"


def test_rd_fill_ink_cells_nonempty():
    """reaction_diffusion_fill ink cells must contain a non-space character."""
    result = reaction_diffusion_fill(_MASK_A, seed=42, steps=50)
    ink_chars = [
        result[r][c]
        for r, row in enumerate(_MASK_A)
        for c, val in enumerate(row)
        if val >= 0.5
    ]
    assert any(ch != " " for ch in ink_chars), "All ink cells rendered as spaces"


# -------------------------------------------------------------------------
# Reproducibility

def test_rd_fill_seeded_reproducible():
    """reaction_diffusion_fill with the same seed produces identical output."""
    a = reaction_diffusion_fill(_MASK_A, seed=7, steps=20)
    b = reaction_diffusion_fill(_MASK_A, seed=7, steps=20)
    assert a == b


def test_rd_fill_different_seeds_differ():
    """reaction_diffusion_fill with different seeds produces different output."""
    a = reaction_diffusion_fill(_MASK_A, seed=0, steps=200)
    b = reaction_diffusion_fill(_MASK_A, seed=99, steps=200)
    assert a != b


# -------------------------------------------------------------------------
# Edge cases

def test_rd_fill_empty_mask():
    """reaction_diffusion_fill on empty mask returns empty list."""
    assert reaction_diffusion_fill([]) == []


# -------------------------------------------------------------------------
# Presets

@pytest.mark.parametrize("preset", list(_RD_PRESETS.keys()))
def test_rd_fill_all_presets_run(preset):
    """All named presets run without error."""
    result = reaction_diffusion_fill(_MASK_A, preset=preset, seed=0, steps=10)
    assert len(result) == len(_MASK_A)


def test_rd_fill_unknown_preset_raises():
    """Unknown preset name raises ValueError."""
    with pytest.raises(ValueError, match="Unknown RD preset"):
        reaction_diffusion_fill(_MASK_A, preset="nonexistent")


# -------------------------------------------------------------------------
# Integration

def test_rd_fill_via_render():
    """render(fill='rd') works end-to-end without error."""
    result = render("A", font="block", fill="rd")
    assert isinstance(result, str)
    assert len(result) > 0


def test_rd_in_fill_registry():
    """'rd' must be present in _FILL_FNS."""
    assert "rd" in _FILL_FNS
