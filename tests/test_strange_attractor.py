"""
Package: tests.test_strange_attractor
Tests for the Strange Attractor density fill (N08).

Covers: output shape, boundary constraints, determinism, all four attractor
types, preset variants, edge cases (empty mask, single cell), and pipeline
integration via render().
"""

import logging as _logging

import pytest

from justdoit.effects.generative import (
    strange_attractor_fill,
    _lorenz_trajectory,
    _rossler_trajectory,
    _dejong_trajectory,
    _clifford_trajectory,
    _build_density_grid,
    _DEJONG_PRESETS,
    _CLIFFORD_PRESETS,
)
from justdoit.core.glyph import glyph_to_mask
from justdoit.core.rasterizer import render, _FILL_FNS
from justdoit.fonts.builtin.block import BLOCK

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "tests.test_strange_attractor"
__updated__ = "2026-03-27 00:00:00"
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

# Use a reduced step count for tests to keep them fast
_FAST_STEPS = 5000


# =========================================================================
# Trajectory generator tests

def test_lorenz_trajectory_length():
    """Lorenz trajectory returns exactly the requested number of points."""
    pts = _lorenz_trajectory(steps=100)
    assert len(pts) == 100


def test_lorenz_trajectory_is_2d():
    """Each Lorenz point is a 2-tuple."""
    pts = _lorenz_trajectory(steps=10)
    for p in pts:
        assert len(p) == 2


def test_rossler_trajectory_length():
    """Rössler trajectory returns the correct number of points."""
    pts = _rossler_trajectory(steps=80)
    assert len(pts) == 80


def test_dejong_trajectory_length():
    """De Jong trajectory returns the correct number of points."""
    pts = _dejong_trajectory(steps=200, params=_DEJONG_PRESETS["default"])
    assert len(pts) == 200


def test_clifford_trajectory_length():
    """Clifford trajectory returns the correct number of points."""
    pts = _clifford_trajectory(steps=150, params=_CLIFFORD_PRESETS["default"])
    assert len(pts) == 150


def test_dejong_trajectory_bounded():
    """De Jong trajectory stays within a known finite range for default params."""
    pts = _dejong_trajectory(steps=500, params=_DEJONG_PRESETS["default"])
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    # De Jong map output is bounded by [-2, 2] by construction (sin/cos range)
    assert all(-3.0 <= x <= 3.0 for x in xs), "De Jong x out of expected range"
    assert all(-3.0 <= y <= 3.0 for y in ys), "De Jong y out of expected range"


def test_clifford_trajectory_bounded():
    """Clifford trajectory stays within a known finite range for default params."""
    pts = _clifford_trajectory(steps=500, params=_CLIFFORD_PRESETS["default"])
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    assert all(-4.0 <= x <= 4.0 for x in xs), "Clifford x out of expected range"
    assert all(-4.0 <= y <= 4.0 for y in ys), "Clifford y out of expected range"


# =========================================================================
# Density grid tests

def test_density_grid_shape():
    """_build_density_grid returns the requested bin dimensions."""
    pts = [(float(i), float(i % 5)) for i in range(100)]
    grid = _build_density_grid(pts, bin_rows=10, bin_cols=15)
    assert len(grid) == 10
    assert all(len(row) == 15 for row in grid)


def test_density_grid_normalised():
    """All density grid values are in [0.0, 1.0]."""
    pts = _dejong_trajectory(steps=1000, params=_DEJONG_PRESETS["default"])
    grid = _build_density_grid(pts, bin_rows=20, bin_cols=20)
    for row in grid:
        for val in row:
            assert 0.0 <= val <= 1.0, f"Density value {val} out of [0,1]"


def test_density_grid_max_is_one():
    """At least one cell should reach (or be very close to) 1.0."""
    pts = _lorenz_trajectory(steps=2000)
    grid = _build_density_grid(pts, bin_rows=30, bin_cols=30)
    max_val = max(v for row in grid for v in row)
    assert max_val > 0.9, f"Max density {max_val} much less than 1.0"


def test_density_grid_empty_pts():
    """Empty point list returns zero grid without error."""
    grid = _build_density_grid([], bin_rows=5, bin_cols=5)
    assert len(grid) == 5
    assert all(v == 0.0 for row in grid for v in row)


# =========================================================================
# Shape / dimension tests

def test_attractor_output_row_count_lorenz():
    """Output row count equals mask row count for lorenz."""
    result = strange_attractor_fill(_MASK_A, attractor="lorenz", steps=_FAST_STEPS)
    assert len(result) == len(_MASK_A)


def test_attractor_output_col_width_lorenz():
    """Each output row width equals the corresponding mask row width."""
    result = strange_attractor_fill(_MASK_A, attractor="lorenz", steps=_FAST_STEPS)
    for r, (mask_row, out_row) in enumerate(zip(_MASK_A, result)):
        assert len(out_row) == len(mask_row), f"Row {r} width mismatch"


def test_attractor_output_row_count_rossler():
    """Output row count equals mask row count for rossler."""
    result = strange_attractor_fill(_MASK_A, attractor="rossler", steps=_FAST_STEPS)
    assert len(result) == len(_MASK_A)


def test_attractor_output_row_count_dejong():
    """Output row count equals mask row count for dejong."""
    result = strange_attractor_fill(_MASK_A, attractor="dejong", steps=_FAST_STEPS)
    assert len(result) == len(_MASK_A)


def test_attractor_output_row_count_clifford():
    """Output row count equals mask row count for clifford."""
    result = strange_attractor_fill(_MASK_A, attractor="clifford", steps=_FAST_STEPS)
    assert len(result) == len(_MASK_A)


# =========================================================================
# Boundary constraint tests

def test_attractor_empty_cells_are_spaces():
    """Cells outside the glyph ink mask must always be spaces."""
    result = strange_attractor_fill(_MASK_A, attractor="lorenz", steps=_FAST_STEPS)
    for r, mask_row in enumerate(_MASK_A):
        for c, val in enumerate(mask_row):
            if val < 0.5:
                assert result[r][c] == " ", (
                    f"Non-space at empty cell ({r},{c}): '{result[r][c]}'"
                )


def test_attractor_ink_cells_not_all_spaces():
    """At least some ink cells must receive a non-space character."""
    result = strange_attractor_fill(_MASK_A, attractor="lorenz", steps=_FAST_STEPS)
    ink_chars = [
        result[r][c]
        for r, row in enumerate(_MASK_A)
        for c, val in enumerate(row)
        if val >= 0.5
    ]
    assert any(ch != " " for ch in ink_chars), "All ink cells are spaces"


# =========================================================================
# Edge cases

def test_attractor_empty_mask():
    """Empty mask returns empty list."""
    assert strange_attractor_fill([]) == []


def test_attractor_all_empty_cells():
    """All-empty mask returns space-only rows."""
    empty = [[0.0] * 5 for _ in range(3)]
    result = strange_attractor_fill(empty, attractor="lorenz", steps=500)
    for row in result:
        assert row == " " * 5


def test_attractor_single_cell_mask():
    """Single-cell fully-filled mask returns one character."""
    single = [[1.0]]
    result = strange_attractor_fill(single, attractor="dejong", steps=500)
    assert len(result) == 1
    assert len(result[0]) == 1
    assert result[0][0] != " "


def test_attractor_simple_mask_full_coverage():
    """Fully-filled mask: no ink cell should be a space."""
    result = strange_attractor_fill(_SIMPLE_MASK, attractor="lorenz", steps=_FAST_STEPS)
    for row in result:
        assert " " not in row, f"Unexpected space in fully-filled mask row: '{row}'"


# =========================================================================
# Determinism — attractor fill is deterministic (no RNG seed needed)

def test_attractor_lorenz_deterministic():
    """Lorenz fill is deterministic — two calls produce identical output."""
    a = strange_attractor_fill(_MASK_A, attractor="lorenz", steps=_FAST_STEPS)
    b = strange_attractor_fill(_MASK_A, attractor="lorenz", steps=_FAST_STEPS)
    assert a == b, "Lorenz fill is not deterministic"


def test_attractor_dejong_deterministic():
    """De Jong fill is deterministic."""
    a = strange_attractor_fill(_MASK_A, attractor="dejong", steps=_FAST_STEPS)
    b = strange_attractor_fill(_MASK_A, attractor="dejong", steps=_FAST_STEPS)
    assert a == b, "De Jong fill is not deterministic"


# =========================================================================
# Different attractors produce different patterns

def test_lorenz_vs_rossler_differ():
    """Lorenz and Rössler produce different fills for the same mask."""
    a = strange_attractor_fill(_MASK_A, attractor="lorenz", steps=_FAST_STEPS)
    b = strange_attractor_fill(_MASK_A, attractor="rossler", steps=_FAST_STEPS)
    assert a != b, "Lorenz and Rössler produced identical fills"


def test_lorenz_vs_dejong_differ():
    """Lorenz and De Jong produce different fills."""
    a = strange_attractor_fill(_MASK_A, attractor="lorenz", steps=_FAST_STEPS)
    b = strange_attractor_fill(_MASK_A, attractor="dejong", steps=_FAST_STEPS)
    assert a != b, "Lorenz and De Jong produced identical fills"


def test_dejong_vs_clifford_differ():
    """De Jong and Clifford produce different fills."""
    a = strange_attractor_fill(_MASK_A, attractor="dejong", steps=_FAST_STEPS)
    b = strange_attractor_fill(_MASK_A, attractor="clifford", steps=_FAST_STEPS)
    assert a != b, "De Jong and Clifford produced identical fills"


# =========================================================================
# Preset variation tests

def test_dejong_presets_differ():
    """Different De Jong presets produce different fills."""
    a = strange_attractor_fill(_MASK_A, attractor="dejong",
                               steps=_FAST_STEPS, preset="default")
    b = strange_attractor_fill(_MASK_A, attractor="dejong",
                               steps=_FAST_STEPS, preset="thorn")
    assert a != b, "De Jong 'default' and 'thorn' produced identical fills"


def test_clifford_presets_differ():
    """Different Clifford presets produce different fills."""
    a = strange_attractor_fill(_MASK_A, attractor="clifford",
                               steps=_FAST_STEPS, preset="default")
    b = strange_attractor_fill(_MASK_A, attractor="clifford",
                               steps=_FAST_STEPS, preset="spider")
    assert a != b, "Clifford 'default' and 'spider' produced identical fills"


def test_all_dejong_presets_run():
    """All named De Jong presets run without error."""
    for p in _DEJONG_PRESETS:
        result = strange_attractor_fill(_MASK_A, attractor="dejong",
                                        steps=_FAST_STEPS, preset=p)
        assert len(result) == len(_MASK_A), f"De Jong preset '{p}' wrong row count"


def test_all_clifford_presets_run():
    """All named Clifford presets run without error."""
    for p in _CLIFFORD_PRESETS:
        result = strange_attractor_fill(_MASK_A, attractor="clifford",
                                        steps=_FAST_STEPS, preset=p)
        assert len(result) == len(_MASK_A), f"Clifford preset '{p}' wrong row count"


# =========================================================================
# Error handling

def test_unknown_attractor_raises():
    """Unknown attractor name raises ValueError."""
    with pytest.raises(ValueError, match="Unknown attractor"):
        strange_attractor_fill(_MASK_A, attractor="bogus")


def test_unknown_dejong_preset_raises():
    """Unknown De Jong preset raises ValueError."""
    with pytest.raises(ValueError, match="Unknown De Jong preset"):
        strange_attractor_fill(_MASK_A, attractor="dejong", preset="nonexistent")


def test_unknown_clifford_preset_raises():
    """Unknown Clifford preset raises ValueError."""
    with pytest.raises(ValueError, match="Unknown Clifford preset"):
        strange_attractor_fill(_MASK_A, attractor="clifford", preset="nonexistent")


# =========================================================================
# Custom density chars

def test_custom_density_chars():
    """Custom density chars: output chars are all from the provided set."""
    chars = "XO."
    result = strange_attractor_fill(_MASK_A, attractor="lorenz",
                                    steps=_FAST_STEPS, density_chars=chars)
    valid = set(chars) | {" "}
    for r, row in enumerate(result):
        for c, ch in enumerate(row):
            assert ch in valid, f"Unexpected char '{ch}' at ({r},{c})"


# =========================================================================
# Different glyph masks

def test_different_masks_differ():
    """Different glyph masks produce different outputs."""
    a = strange_attractor_fill(_MASK_A, attractor="lorenz", steps=_FAST_STEPS)
    b = strange_attractor_fill(_MASK_H, attractor="lorenz", steps=_FAST_STEPS)
    assert a != b, "Different masks produced identical outputs"


# =========================================================================
# Step count effects

def test_more_steps_runs_without_error():
    """Higher step count doesn't raise."""
    result = strange_attractor_fill(_MASK_A, attractor="dejong", steps=20000)
    assert len(result) == len(_MASK_A)


def test_minimal_steps():
    """Minimal step count (1) doesn't raise and returns correct shape."""
    result = strange_attractor_fill(_MASK_A, attractor="lorenz", steps=1)
    assert len(result) == len(_MASK_A)


# =========================================================================
# Pipeline integration

def test_attractor_registered_in_fill_fns():
    """'attractor' key must be present in the rasterizer fill registry."""
    assert "attractor" in _FILL_FNS
    assert _FILL_FNS["attractor"] is strange_attractor_fill


def test_render_attractor_lorenz():
    """render(fill='attractor') works end-to-end with Lorenz."""
    result = render("A", font="block", fill="attractor")
    assert isinstance(result, str)
    assert len(result) > 0


def test_render_attractor_multichar():
    """render(fill='attractor') works on multi-character strings."""
    result = render("HI", font="block", fill="attractor")
    assert isinstance(result, str)
    assert len(result) > 0
