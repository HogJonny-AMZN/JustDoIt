"""
Package: tests.test_turing
Tests for Turing activator-inhibitor fill (N09) — FitzHugh-Nagumo model.

Covers: output shape, row widths, exterior cells = space, seeded reproducibility,
different seeds diverge, empty mask, all named presets, render() integration,
fill registry presence, custom steps override, and scale parameter.

All tests are pure Python — no PIL dependency.
"""

import logging as _logging

import pytest

from justdoit.effects.generative import turing_fill, _TURING_PRESETS
from justdoit.core.glyph import glyph_to_mask
from justdoit.core.rasterizer import render, _FILL_FNS
from justdoit.fonts.builtin.block import BLOCK

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "tests.test_turing"
__updated__ = "2026-03-30 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_GLYPH_O = BLOCK["O"]
_MASK_O = glyph_to_mask(_GLYPH_O)

_GLYPH_A = BLOCK["A"]
_MASK_A = glyph_to_mask(_GLYPH_A)

# A simple 4×4 synthetic mask — 2×2 ink interior
_SMALL_MASK = [
    [0.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 1.0, 0.0],
    [0.0, 1.0, 1.0, 0.0],
    [0.0, 0.0, 0.0, 0.0],
]


# =========================================================================
# Shape and structure
# =========================================================================

def test_turing_output_row_count():
    """turing_fill output has same row count as input mask."""
    result = turing_fill(_MASK_O, preset="stripes", seed=42, steps=20)
    assert len(result) == len(_MASK_O)


def test_turing_output_row_widths():
    """Every output row has same column count as input mask row."""
    result = turing_fill(_MASK_O, preset="stripes", seed=42, steps=20)
    for r, row in enumerate(result):
        assert len(row) == len(_MASK_O[r]), f"Row {r} width mismatch"


def test_turing_exterior_cells_are_spaces():
    """Cells outside the glyph mask (mask < 0.5) must be space chars."""
    result = turing_fill(_MASK_O, preset="stripes", seed=42, steps=20)
    for r, row in enumerate(result):
        for c, ch in enumerate(row):
            if c >= len(_MASK_O[r]) or _MASK_O[r][c] < 0.5:
                assert ch == " ", (
                    f"Exterior cell ({r},{c}) should be ' ', got {ch!r}"
                )


def test_turing_interior_cells_not_all_spaces():
    """At least some interior cells must be non-space characters."""
    result = turing_fill(_MASK_O, preset="stripes", seed=42, steps=20)
    ink_chars = [
        ch
        for r, row in enumerate(result)
        for c, ch in enumerate(row)
        if c < len(_MASK_O[r]) and _MASK_O[r][c] >= 0.5
    ]
    assert any(ch != " " for ch in ink_chars), "All interior cells are spaces — fill produced nothing"


# =========================================================================
# Reproducibility
# =========================================================================

def test_turing_seeded_reproducible():
    """Same seed produces identical output."""
    r1 = turing_fill(_MASK_A, preset="spots", seed=7, steps=20)
    r2 = turing_fill(_MASK_A, preset="spots", seed=7, steps=20)
    assert r1 == r2, "Seeded turing_fill should be deterministic"


def test_turing_different_seeds_differ():
    """Different seeds should produce different output (with overwhelming probability)."""
    r1 = turing_fill(_MASK_A, preset="stripes", seed=1, steps=100)
    r2 = turing_fill(_MASK_A, preset="stripes", seed=9999, steps=100)
    # Join rows to compare full output
    assert "".join(r1) != "".join(r2), "Different seeds should produce different fill patterns"


# =========================================================================
# Edge cases
# =========================================================================

def test_turing_empty_mask():
    """Empty mask returns empty list without errors."""
    result = turing_fill([], preset="stripes", seed=0)
    assert result == []


def test_turing_all_exterior_mask():
    """All-exterior mask returns rows of spaces."""
    mask = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    result = turing_fill(mask, preset="stripes", seed=0, steps=5)
    assert len(result) == 2
    for row in result:
        assert all(ch == " " for ch in row)


def test_turing_small_mask():
    """Synthetic 4×4 mask with 2×2 ink patch runs without errors."""
    result = turing_fill(_SMALL_MASK, preset="spots", seed=42, steps=20)
    assert len(result) == 4
    for r, row in enumerate(result):
        assert len(row) == 4


def test_turing_small_mask_exterior_spaces():
    """Exterior cells in small synthetic mask are spaces."""
    result = turing_fill(_SMALL_MASK, preset="stripes", seed=0, steps=20)
    # Corners and border cells should all be spaces
    for c in range(4):
        assert result[0][c] == " ", f"Top border row[0][{c}] should be space"
        assert result[3][c] == " ", f"Bottom border row[3][{c}] should be space"
    for r in range(4):
        assert result[r][0] == " ", f"Left border row[{r}][0] should be space"
        assert result[r][3] == " ", f"Right border row[{r}][3] should be space"


# =========================================================================
# Named presets
# =========================================================================

@pytest.mark.parametrize("preset", list(_TURING_PRESETS.keys()))
def test_turing_all_presets(preset):
    """All named presets run without errors and produce correct output shape."""
    result = turing_fill(_MASK_O, preset=preset, seed=0, steps=20)
    assert len(result) == len(_MASK_O)
    for r, row in enumerate(result):
        assert len(row) == len(_MASK_O[r])


def test_turing_unknown_preset_raises():
    """Unknown preset name raises ValueError."""
    with pytest.raises(ValueError, match="Unknown Turing preset"):
        turing_fill(_MASK_O, preset="nonexistent_pattern_xyz")


# =========================================================================
# Parameter overrides
# =========================================================================

def test_turing_steps_override():
    """Custom steps parameter is accepted and produces valid output."""
    result = turing_fill(_MASK_A, preset="maze", seed=42, steps=5)
    assert len(result) == len(_MASK_A)
    for r, row in enumerate(result):
        assert len(row) == len(_MASK_A[r])


def test_turing_scale_2():
    """Scale=2 (lower resolution) produces valid output shape."""
    result = turing_fill(_MASK_O, preset="stripes", seed=0, steps=10, scale=2)
    assert len(result) == len(_MASK_O)
    for r, row in enumerate(result):
        assert len(row) == len(_MASK_O[r])


def test_turing_scale_6():
    """Scale=6 (higher resolution) produces valid output shape."""
    result = turing_fill(_MASK_O, preset="spots", seed=0, steps=10, scale=6)
    assert len(result) == len(_MASK_O)
    for r, row in enumerate(result):
        assert len(row) == len(_MASK_O[r])


def test_turing_custom_density_chars():
    """Custom density_chars are used and only those chars appear in ink cells."""
    custom_chars = "#. "
    result = turing_fill(_MASK_O, preset="spots", seed=42, steps=20, density_chars=custom_chars)
    allowed = set(custom_chars)
    for r, row in enumerate(result):
        for c, ch in enumerate(row):
            assert ch in allowed, f"Unexpected char {ch!r} at ({r},{c}) with custom density_chars={custom_chars!r}"


# =========================================================================
# Fill registry and render() integration
# =========================================================================

def test_turing_in_fill_registry():
    """'turing' key must be present in _FILL_FNS registry."""
    assert "turing" in _FILL_FNS, "turing fill not registered in _FILL_FNS"


def test_turing_fill_registry_callable():
    """The value registered under 'turing' must be callable."""
    assert callable(_FILL_FNS["turing"]), "_FILL_FNS['turing'] is not callable"


def test_turing_via_render_hi():
    """render('HI', fill='turing') produces non-empty output."""
    out = render("HI", fill="turing")
    assert len(out) > 0, "render('HI', fill='turing') returned empty string"


def test_turing_via_render_just_do_it():
    """render('JUST DO IT', fill='turing') produces multi-line output."""
    out = render("JUST DO IT", fill="turing")
    lines = out.split("\n")
    assert len(lines) > 1, "render('JUST DO IT', fill='turing') should produce multiple lines"


def test_turing_via_render_output_not_blank():
    """render() with turing fill should contain at least some non-space characters."""
    out = render("HI", fill="turing")
    non_space = [ch for ch in out if ch not in (" ", "\n")]
    assert len(non_space) > 0, "render('HI', fill='turing') produced only spaces"
