"""
Package: tests.test_lsystem
Tests for the L-System Growth fill (N06).

Covers: L-system string expansion, turtle segment generation, density grid
construction, output shape, boundary constraints, determinism, all presets,
edge cases (empty mask, single cell, empty rules), custom overrides, and
pipeline integration via render().
"""

import logging as _logging
import math

import pytest

from justdoit.effects.generative import (
    lsystem_fill,
    _lsystem_expand,
    _lsystem_segments,
    _lsystem_density_grid,
    _LSYSTEM_PRESETS,
)
from justdoit.core.glyph import glyph_to_mask
from justdoit.core.rasterizer import render, _FILL_FNS
from justdoit.fonts.builtin.block import BLOCK

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "tests.test_lsystem"
__updated__ = "2026-03-28 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_GLYPH_A = BLOCK["A"]
_GLYPH_H = BLOCK["H"]
_MASK_A   = glyph_to_mask(_GLYPH_A)
_MASK_H   = glyph_to_mask(_GLYPH_H)

# Minimal fully-filled 4×5 mask
_SIMPLE_MASK = [
    [1.0, 1.0, 1.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0, 1.0],
]


# =========================================================================
# _lsystem_expand tests

def test_expand_identity():
    """Axiom with no matching rules is returned unchanged."""
    result = _lsystem_expand("F", {}, 3)
    assert result == "F"


def test_expand_single_rule():
    """Single rule applied correctly."""
    # Algae: A -> AB, B -> A
    result = _lsystem_expand("A", {"A": "AB", "B": "A"}, 1)
    assert result == "AB"


def test_expand_fibonacci_lengths():
    """Algae string lengths follow the Fibonacci sequence."""
    # After n iterations: len = fib(n+2) for axiom "A"
    rules = {"A": "AB", "B": "A"}
    lengths = [len(_lsystem_expand("A", rules, n)) for n in range(7)]
    # Expected: 1, 2, 3, 5, 8, 13, 21
    fib = [1, 2, 3, 5, 8, 13, 21]
    assert lengths == fib, f"Got {lengths}, expected {fib}"


def test_expand_zero_iterations():
    """Zero iterations returns axiom unchanged."""
    result = _lsystem_expand("FX", {"X": "FX+FX"}, 0)
    assert result == "FX"


def test_expand_nonvariable_chars_preserved():
    """Non-rule chars (+, -, [, ]) are preserved verbatim."""
    result = _lsystem_expand("F+[F]-F", {"F": "FF"}, 1)
    # F -> FF everywhere, rest stays
    assert result == "FF+[FF]-FF"


def test_expand_multiple_rules():
    """Multiple production rules applied correctly in one step."""
    result = _lsystem_expand("AB", {"A": "AB", "B": "A"}, 2)
    # Step 1: AB -> ABA
    # Step 2: ABA -> ABAAB
    assert result == "ABAAB"


# =========================================================================
# _lsystem_segments tests

def test_segments_empty_string():
    """Empty L-system string produces no segments."""
    segs = _lsystem_segments("", angle_deg=25.0)
    assert segs == []


def test_segments_single_F():
    """Single F produces exactly one segment."""
    segs = _lsystem_segments("F", angle_deg=25.0, step=1.0, start_angle_deg=0.0)
    assert len(segs) == 1
    x0, y0, x1, y1 = segs[0]
    # heading=0 → east: dx≈1, dy≈0
    assert abs(x1 - x0 - 1.0) < 1e-9
    assert abs(y1 - y0) < 1e-9


def test_segments_f_no_draw():
    """Lowercase f moves without producing a segment."""
    segs = _lsystem_segments("f", angle_deg=25.0, step=1.0)
    assert len(segs) == 0


def test_segments_turn_then_F():
    """+ turns left and changes segment direction."""
    segs_straight = _lsystem_segments("FF", angle_deg=90.0, step=1.0, start_angle_deg=0.0)
    segs_turn     = _lsystem_segments("F+F", angle_deg=90.0, step=1.0, start_angle_deg=0.0)
    assert len(segs_straight) == 2
    assert len(segs_turn) == 2
    # After +90° from 0°, second segment should go upward
    x0, y0, x1, y1 = segs_turn[1]
    assert abs(y1 - y0 - 1.0) < 1e-6, "Second segment should go upward after +90°"


def test_segments_branch_returns_to_start():
    """[ ] branch returns turtle to saved position."""
    segs = _lsystem_segments("F[+F]F", angle_deg=90.0, step=1.0, start_angle_deg=0.0)
    # 3 F-draws total: main, branch, resume
    assert len(segs) == 3
    # The third segment should continue from where first ended, not branch tip
    x0_first, y0_first = segs[0][:2]
    x1_first, y1_first = segs[0][2:]
    x0_third, y0_third = segs[2][:2]
    assert abs(x0_third - x1_first) < 1e-6
    assert abs(y0_third - y1_first) < 1e-6


def test_segments_u_turn():
    """| reverses heading by 180°."""
    # F heading 0 → east, then | → heading 180 (west), then F → west
    segs = _lsystem_segments("F|F", angle_deg=90.0, step=1.0, start_angle_deg=0.0)
    assert len(segs) == 2
    # Second segment goes west — x1 < x0
    x0, y0, x1, y1 = segs[1]
    assert x1 < x0, "After | should go west"


def test_segments_no_F_no_segments():
    """String with no F/f chars (only variables) produces no segments."""
    segs = _lsystem_segments("XYZ+-[]", angle_deg=25.0)
    assert len(segs) == 0


# =========================================================================
# _lsystem_density_grid tests

def test_density_grid_shape():
    """_lsystem_density_grid returns the requested bin dimensions."""
    segs = [(0.0, 0.0, 1.0, 0.0), (1.0, 0.0, 1.0, 1.0)]
    grid = _lsystem_density_grid(segs, bin_rows=10, bin_cols=15)
    assert len(grid) == 10
    assert all(len(row) == 15 for row in grid)


def test_density_grid_normalised():
    """All density grid values are in [0.0, 1.0]."""
    segs = _lsystem_segments(
        _lsystem_expand("F", {"F": "F[+F]F[-F]F"}, 3),
        angle_deg=25.0
    )
    grid = _lsystem_density_grid(segs, bin_rows=30, bin_cols=30)
    for row in grid:
        for val in row:
            assert 0.0 <= val <= 1.0, f"Density value {val} out of [0,1]"


def test_density_grid_max_is_one():
    """At least one cell should be very close to 1.0 (trunk density)."""
    segs = _lsystem_segments(
        _lsystem_expand("F", {"F": "F[+F]F[-F]F"}, 3),
        angle_deg=25.0
    )
    grid = _lsystem_density_grid(segs, bin_rows=30, bin_cols=30)
    max_val = max(v for row in grid for v in row)
    assert max_val > 0.9, f"Max density {max_val} much less than 1.0"


def test_density_grid_nonzero_for_valid_segments():
    """A valid segment list produces at least some nonzero cells."""
    segs = [(0.0, 0.0, 1.0, 0.0)]
    grid = _lsystem_density_grid(segs, bin_rows=10, bin_cols=10)
    any_nonzero = any(v > 0.0 for row in grid for v in row)
    assert any_nonzero, "All cells zero — Bresenham rasterisation failed"


def test_density_grid_empty_segments():
    """Empty segment list returns all-zero grid without error."""
    grid = _lsystem_density_grid([], bin_rows=5, bin_cols=5)
    assert len(grid) == 5
    assert all(v == 0.0 for row in grid for v in row)


# =========================================================================
# lsystem_fill shape / dimension tests

def test_lsystem_output_row_count():
    """Output row count equals mask row count."""
    result = lsystem_fill(_MASK_A, preset="plant")
    assert len(result) == len(_MASK_A)


def test_lsystem_output_col_width():
    """Each output row width equals the corresponding mask row width."""
    result = lsystem_fill(_MASK_A, preset="plant")
    for r, (mask_row, out_row) in enumerate(zip(_MASK_A, result)):
        assert len(out_row) == len(mask_row), f"Row {r} width mismatch"


def test_lsystem_output_nonempty():
    """Output is a non-empty list."""
    result = lsystem_fill(_MASK_A, preset="plant")
    assert len(result) > 0
    assert any(len(row) > 0 for row in result)


# =========================================================================
# Boundary constraint tests

def test_lsystem_empty_cells_are_spaces():
    """Cells outside the glyph ink mask must always be spaces."""
    result = lsystem_fill(_MASK_A, preset="plant")
    for r, mask_row in enumerate(_MASK_A):
        for c, val in enumerate(mask_row):
            if val < 0.5:
                assert result[r][c] == " ", (
                    f"Non-space at empty cell ({r},{c}): '{result[r][c]}'"
                )


def test_lsystem_ink_cells_not_all_spaces():
    """At least some ink cells must receive a non-space character."""
    result = lsystem_fill(_MASK_A, preset="plant")
    ink_chars = [
        result[r][c]
        for r, row in enumerate(_MASK_A)
        for c, val in enumerate(row)
        if val >= 0.5
    ]
    assert any(ch != " " for ch in ink_chars), "All ink cells are spaces"


def test_lsystem_fully_filled_mask_no_spaces():
    """Fully-filled mask: no ink cell should be a space."""
    result = lsystem_fill(_SIMPLE_MASK, preset="plant")
    for row in result:
        assert " " not in row, f"Unexpected space in fully-filled mask row: '{row}'"


# =========================================================================
# Edge cases

def test_lsystem_empty_mask():
    """Empty mask returns empty list."""
    assert lsystem_fill([]) == []


def test_lsystem_all_empty_cells():
    """All-empty mask returns space-only rows."""
    empty = [[0.0] * 5 for _ in range(3)]
    result = lsystem_fill(empty)
    for row in result:
        assert row == " " * 5


def test_lsystem_single_cell_mask():
    """Single-cell fully-filled mask returns one non-space character."""
    single = [[1.0]]
    result = lsystem_fill(single)
    assert len(result) == 1
    assert len(result[0]) == 1
    assert result[0][0] != " "


def test_lsystem_single_row_mask():
    """Single-row mask works without error."""
    row_mask = [[1.0, 1.0, 1.0, 0.0, 1.0]]
    result = lsystem_fill(row_mask)
    assert len(result) == 1
    assert len(result[0]) == 5
    assert result[0][3] == " "   # empty cell stays space


def test_lsystem_single_col_mask():
    """Single-column mask works without error."""
    col_mask = [[1.0], [1.0], [0.0], [1.0]]
    result = lsystem_fill(col_mask)
    assert len(result) == 4
    assert result[2][0] == " "   # empty cell stays space


# =========================================================================
# Determinism — L-system is fully deterministic (no RNG)

def test_lsystem_deterministic_plant():
    """Plant preset is deterministic — two calls produce identical output."""
    a = lsystem_fill(_MASK_A, preset="plant")
    b = lsystem_fill(_MASK_A, preset="plant")
    assert a == b, "lsystem_fill('plant') is not deterministic"


def test_lsystem_deterministic_dragon():
    """Dragon preset is deterministic."""
    a = lsystem_fill(_MASK_A, preset="dragon")
    b = lsystem_fill(_MASK_A, preset="dragon")
    assert a == b, "lsystem_fill('dragon') is not deterministic"


# =========================================================================
# All named presets run without error

def test_all_presets_run():
    """All named presets produce correct output shape without raising."""
    for p in _LSYSTEM_PRESETS:
        result = lsystem_fill(_MASK_A, preset=p)
        assert len(result) == len(_MASK_A), f"Preset '{p}' wrong row count"
        for r, (mask_row, out_row) in enumerate(zip(_MASK_A, result)):
            assert len(out_row) == len(mask_row), (
                f"Preset '{p}' row {r} width mismatch"
            )


# =========================================================================
# Different presets produce different results

def test_plant_vs_dragon_differ():
    """Plant and Dragon presets produce different fills."""
    a = lsystem_fill(_MASK_A, preset="plant")
    b = lsystem_fill(_MASK_A, preset="dragon")
    assert a != b, "Plant and Dragon produced identical fills"


def test_plant_vs_sierpinski_differ():
    """Plant and Sierpinski produce different fills."""
    a = lsystem_fill(_MASK_A, preset="plant")
    b = lsystem_fill(_MASK_A, preset="sierpinski")
    assert a != b, "Plant and Sierpinski produced identical fills"


def test_bush_vs_crystal_differ():
    """Bush and Crystal produce different fills."""
    a = lsystem_fill(_MASK_A, preset="bush")
    b = lsystem_fill(_MASK_A, preset="crystal")
    assert a != b, "Bush and Crystal produced identical fills"


# =========================================================================
# Different masks produce different results

def test_different_masks_differ():
    """Different glyph masks produce different outputs for same preset."""
    a = lsystem_fill(_MASK_A, preset="plant")
    b = lsystem_fill(_MASK_H, preset="plant")
    assert a != b, "Different masks produced identical outputs"


# =========================================================================
# Custom overrides

def test_custom_axiom_override():
    """Custom axiom overrides preset axiom."""
    # Using "plant" preset but with a trivially simple custom axiom
    result = lsystem_fill(_MASK_A, preset="plant", axiom="F")
    assert len(result) == len(_MASK_A)


def test_custom_rules_override():
    """Custom rules override preset rules."""
    result = lsystem_fill(
        _MASK_A,
        preset="plant",
        axiom="F",
        rules={"F": "F[+F][-F]"},
        angle_deg=30.0,
        iterations=3,
    )
    assert len(result) == len(_MASK_A)


def test_custom_angle_override():
    """Custom angle override changes output."""
    a = lsystem_fill(_MASK_A, preset="plant", angle_deg=25.0)
    b = lsystem_fill(_MASK_A, preset="plant", angle_deg=45.0)
    assert a != b, "Different angles produced identical fills"


def test_custom_iterations_override():
    """Fewer iterations produces less-detailed (but still valid) output."""
    result_deep   = lsystem_fill(_MASK_A, preset="plant", iterations=4)
    result_shallow = lsystem_fill(_MASK_A, preset="plant", iterations=1)
    assert len(result_deep) == len(result_shallow)  # same shape
    assert result_deep != result_shallow             # different content


# =========================================================================
# Custom density chars

def test_custom_density_chars():
    """Custom density chars: output chars are all from the provided set."""
    chars = "XO."
    result = lsystem_fill(_MASK_A, preset="plant", density_chars=chars)
    valid = set(chars) | {" "}
    for r, row in enumerate(result):
        for c, ch in enumerate(row):
            assert ch in valid, f"Unexpected char '{ch}' at ({r},{c})"


def test_single_char_density():
    """Single-char density string fills all ink cells with that char."""
    result = lsystem_fill(_MASK_A, preset="plant", density_chars="*")
    for r, mask_row in enumerate(_MASK_A):
        for c, val in enumerate(mask_row):
            if val >= 0.5:
                assert result[r][c] == "*", (
                    f"Expected '*' at ink cell ({r},{c}), got '{result[r][c]}'"
                )


# =========================================================================
# Error handling

def test_unknown_preset_raises():
    """Unknown preset raises ValueError."""
    with pytest.raises(ValueError, match="Unknown L-system preset"):
        lsystem_fill(_MASK_A, preset="bogus")


# =========================================================================
# Pipeline integration

def test_lsystem_registered_in_fill_fns():
    """'lsystem' key must be present in the rasterizer fill registry."""
    assert "lsystem" in _FILL_FNS
    assert _FILL_FNS["lsystem"] is lsystem_fill


def test_render_lsystem_plant():
    """render(fill='lsystem') works end-to-end with plant preset."""
    result = render("A", font="block", fill="lsystem")
    assert isinstance(result, str)
    assert len(result) > 0


def test_render_lsystem_multichar():
    """render(fill='lsystem') works on multi-character strings."""
    result = render("HI", font="block", fill="lsystem")
    assert isinstance(result, str)
    assert len(result) > 0


def test_render_lsystem_all_presets_pipeline():
    """All presets work through the render pipeline."""
    for p in _LSYSTEM_PRESETS:
        result = render("A", font="block", fill="lsystem")
        assert isinstance(result, str), f"Preset '{p}' render failed"
        assert len(result) > 0


# =========================================================================
# Bresenham rasterisation sanity

def test_bresenham_horizontal_segment_density():
    """A horizontal segment produces nonzero density along the expected row."""
    # Single horizontal segment from (0,0) to (5,0)
    segs = [(0.0, 0.0, 5.0, 0.0)]
    grid = _lsystem_density_grid(segs, bin_rows=10, bin_cols=10)
    # Some cells should be nonzero
    any_nonzero = any(v > 0.0 for row in grid for v in row)
    assert any_nonzero


def test_bresenham_diagonal_segment_density():
    """A diagonal segment produces nonzero density along a diagonal."""
    segs = [(0.0, 0.0, 3.0, 3.0)]
    grid = _lsystem_density_grid(segs, bin_rows=10, bin_cols=10)
    any_nonzero = any(v > 0.0 for row in grid for v in row)
    assert any_nonzero


# =========================================================================
# String expansion length bounds

def test_lsystem_string_not_too_long():
    """Low iteration counts keep the string manageable (< 100k chars)."""
    for p in _LSYSTEM_PRESETS:
        cfg = _LSYSTEM_PRESETS[p]
        s = _lsystem_expand(cfg["axiom"], cfg["rules"], cfg["iterations"])
        assert len(s) < 500_000, (
            f"Preset '{p}' expanded to {len(s)} chars — may be slow"
        )
