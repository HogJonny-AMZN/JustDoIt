"""
Package: tests.test_generative
Tests for generative fill effects — Perlin noise (F02) and cellular automata (F03).

Covers: noise_fill, cells_fill, seeded reproducibility, mask shape preservation,
and integration via render(fill='noise') and render(fill='cells').
All tests are pure Python — no PIL dependency.
"""

import logging as _logging

import pytest

from justdoit.effects.generative import noise_fill, cells_fill, _build_perm, _perlin2d, wave_fill, fractal_fill, voronoi_fill
from justdoit.core.glyph import glyph_to_mask
from justdoit.core.rasterizer import render, _FILL_FNS
from justdoit.fonts.builtin.block import BLOCK

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "tests.test_generative"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_GLYPH_A = BLOCK["A"]
_MASK_A  = glyph_to_mask(_GLYPH_A)


# -------------------------------------------------------------------------
# Perlin internals

def test_perlin_perm_length():
    """_build_perm() returns exactly 512 elements."""
    assert len(_build_perm(0)) == 512


def test_perlin_value_range():
    """_perlin2d() returns values in approximately -1.0 to 1.0."""
    perm = _build_perm(42)
    for x in range(10):
        for y in range(10):
            v = _perlin2d(x * 0.3, y * 0.3, perm)
            assert -2.0 <= v <= 2.0, f"Out of range at ({x},{y}): {v}"


def test_perlin_deterministic_with_seed():
    """Same seed produces identical noise values."""
    perm1 = _build_perm(7)
    perm2 = _build_perm(7)
    assert perm1 == perm2
    assert _perlin2d(1.5, 2.3, perm1) == _perlin2d(1.5, 2.3, perm2)


def test_perlin_different_seeds_differ():
    """Different seeds produce different permutations."""
    perm1 = _build_perm(1)
    perm2 = _build_perm(2)
    assert perm1 != perm2


# -------------------------------------------------------------------------
# noise_fill (F02)

def test_noise_fill_output_shape():
    """noise_fill output has same row count as input mask."""
    result = noise_fill(_MASK_A, seed=0)
    assert len(result) == len(_MASK_A)


def test_noise_fill_row_width():
    """noise_fill rows have same width as mask rows."""
    result = noise_fill(_MASK_A, seed=0)
    for r, (orig, filled) in enumerate(zip(_MASK_A, result)):
        assert len(filled) == len(orig), f"Row {r} width mismatch"


def test_noise_fill_ink_cells_nonempty():
    """noise_fill ink cells (mask >= 0.5) must not be spaces."""
    result = noise_fill(_MASK_A, seed=1)
    for r, row in enumerate(_MASK_A):
        for c, val in enumerate(row):
            if val >= 0.5:
                assert result[r][c] != " ", f"Ink cell ({r},{c}) rendered as space"


def test_noise_fill_empty_cells_are_spaces():
    """noise_fill empty cells (mask < 0.5) must be spaces."""
    result = noise_fill(_MASK_A, seed=2)
    for r, row in enumerate(_MASK_A):
        for c, val in enumerate(row):
            if val < 0.5:
                assert result[r][c] == " ", f"Empty cell ({r},{c}) not a space"


def test_noise_fill_seeded_reproducible():
    """noise_fill with the same seed produces identical output."""
    a = noise_fill(_MASK_A, seed=99)
    b = noise_fill(_MASK_A, seed=99)
    assert a == b


def test_noise_fill_different_seeds_vary():
    """noise_fill with different seeds produces different output."""
    a = noise_fill(_MASK_A, seed=0)
    b = noise_fill(_MASK_A, seed=1)
    assert a != b


def test_noise_fill_empty_mask():
    """noise_fill on empty mask returns empty list."""
    assert noise_fill([]) == []


def test_noise_fill_via_render():
    """render(fill='noise') works end-to-end without error."""
    result = render("A", font="block", fill="noise")
    assert isinstance(result, str)
    assert len(result) > 0


# -------------------------------------------------------------------------
# cells_fill (F03)

def test_cells_fill_output_shape():
    """cells_fill output has same row count as input mask."""
    result = cells_fill(_MASK_A, seed=0)
    assert len(result) == len(_MASK_A)


def test_cells_fill_row_width():
    """cells_fill rows have same width as mask rows."""
    result = cells_fill(_MASK_A, seed=0)
    for r, (orig, filled) in enumerate(zip(_MASK_A, result)):
        assert len(filled) == len(orig), f"Row {r} width mismatch"


def test_cells_fill_empty_cells_are_spaces():
    """cells_fill empty cells must be spaces."""
    result = cells_fill(_MASK_A, seed=3)
    for r, row in enumerate(_MASK_A):
        for c, val in enumerate(row):
            if val < 0.5:
                assert result[r][c] == " ", f"Empty cell ({r},{c}) not a space"


def test_cells_fill_ink_cells_nonempty():
    """cells_fill ink cells must contain a non-space character."""
    result = cells_fill(_MASK_A, steps=4, seed=42, alive_prob=0.5)
    ink_cells = [
        result[r][c]
        for r, row in enumerate(_MASK_A)
        for c, val in enumerate(row)
        if val >= 0.5
    ]
    assert any(ch != " " for ch in ink_cells), "All ink cells rendered as spaces"


def test_cells_fill_seeded_reproducible():
    """cells_fill with the same seed produces identical output."""
    a = cells_fill(_MASK_A, seed=7)
    b = cells_fill(_MASK_A, seed=7)
    assert a == b


def test_cells_fill_different_seeds_vary():
    """cells_fill with different seeds should usually produce different output."""
    a = cells_fill(_MASK_A, seed=10, alive_prob=0.5)
    b = cells_fill(_MASK_A, seed=11, alive_prob=0.5)
    assert a != b


def test_cells_fill_steps_zero():
    """cells_fill with steps=0 (no evolution) should not error."""
    result = cells_fill(_MASK_A, steps=0, seed=0)
    assert len(result) == len(_MASK_A)


def test_cells_fill_empty_mask():
    """cells_fill on empty mask returns empty list."""
    assert cells_fill([]) == []


def test_cells_fill_via_render():
    """render(fill='cells') works end-to-end without error."""
    result = render("A", font="block", fill="cells")
    assert isinstance(result, str)
    assert len(result) > 0


# -------------------------------------------------------------------------
# Wave Interference fill — F09

_SIMPLE_MASK: list = [
    [1.0, 1.0, 1.0, 0.0],
    [1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0],
]


def test_wave_fill_shape():
    """wave_fill preserves row/col shape and exterior cells are spaces."""
    result = wave_fill(_SIMPLE_MASK)
    assert len(result) == 3
    assert len(result[0]) == 4
    assert result[0][3] == " "   # exterior
    assert result[1][2] == " "   # exterior
    assert result[2][1] == " "   # exterior


def test_wave_fill_presets():
    """All four wave presets produce valid output on a real glyph mask."""
    for preset in ("default", "moire", "radial", "fine"):
        result = wave_fill(_MASK_A, preset=preset)
        assert len(result) == len(_MASK_A), f"preset={preset}: wrong row count"
        assert all(len(row) == len(_MASK_A[0]) for row in result), f"preset={preset}: col mismatch"


def test_wave_fill_invalid_preset():
    """wave_fill raises ValueError for unknown preset."""
    with pytest.raises(ValueError):
        wave_fill(_MASK_A, preset="nonsense")


def test_wave_fill_via_render():
    """render(fill='wave') works end-to-end without error."""
    result = render("HI", font="block", fill="wave")
    assert isinstance(result, str)
    assert len(result) > 0


# -------------------------------------------------------------------------
# Fractal fill — F05

def test_fractal_fill_shape():
    """fractal_fill preserves row/col shape and exterior cells are spaces."""
    result = fractal_fill(_SIMPLE_MASK)
    assert len(result) == 3
    assert len(result[0]) == 4
    assert result[0][3] == " "   # exterior
    assert result[1][2] == " "   # exterior
    assert result[2][1] == " "   # exterior


def test_fractal_fill_presets():
    """All five fractal presets produce valid output on a real glyph mask."""
    for preset in ("default", "seahorse", "lightning", "julia_swirl", "julia_rabbit"):
        result = fractal_fill(_MASK_A, preset=preset)
        assert len(result) == len(_MASK_A), f"preset={preset}: wrong row count"
        assert all(len(row) == len(_MASK_A[0]) for row in result), f"preset={preset}: col mismatch"


def test_fractal_fill_julia():
    """fractal_fill with mode='julia' via julia_swirl preset works."""
    result = fractal_fill(_MASK_A, preset="julia_swirl")
    assert len(result) == len(_MASK_A)
    # At least one non-space character must be present
    assert any(ch != " " for row in result for ch in row)


def test_fractal_fill_invalid_preset():
    """fractal_fill raises ValueError for unknown preset."""
    with pytest.raises(ValueError):
        fractal_fill(_MASK_A, preset="nonsense")


def test_fractal_fill_via_render():
    """render(fill='fractal') works end-to-end without error."""
    result = render("HI", font="block", fill="fractal")
    assert isinstance(result, str)
    assert len(result) > 0


# -------------------------------------------------------------------------
# Voronoi fill — F07

def test_voronoi_fill_shape():
    """voronoi_fill preserves row/col shape and exterior cells are spaces."""
    result = voronoi_fill(_SIMPLE_MASK)
    assert len(result) == 3
    assert len(result[0]) == 4
    assert result[0][3] == " "   # exterior
    assert result[1][2] == " "   # exterior
    assert result[2][1] == " "   # exterior


def test_voronoi_fill_output_type():
    """voronoi_fill returns a list of strings."""
    result = voronoi_fill(_MASK_A)
    assert isinstance(result, list)
    assert all(isinstance(row, str) for row in result)


def test_voronoi_fill_dimensions():
    """voronoi_fill row count and col width match mask dimensions."""
    result = voronoi_fill(_MASK_A)
    assert len(result) == len(_MASK_A)
    assert all(len(row) == len(_MASK_A[0]) for row in result)


def test_voronoi_fill_nonempty_interior():
    """voronoi_fill produces at least one non-space character for a real glyph."""
    result = voronoi_fill(_MASK_A)
    assert any(ch != " " for row in result for ch in row)


def test_voronoi_fill_seeded_reproducible():
    """Same seed produces identical output (deterministic)."""
    r1 = voronoi_fill(_MASK_A, seed=99)
    r2 = voronoi_fill(_MASK_A, seed=99)
    assert r1 == r2


def test_voronoi_fill_different_seeds_vary():
    """Different seeds produce different outputs."""
    r1 = voronoi_fill(_MASK_A, seed=1)
    r2 = voronoi_fill(_MASK_A, seed=2)
    # Not guaranteed to differ for every glyph, but almost always will
    assert r1 != r2


def test_voronoi_fill_presets():
    """All named presets produce valid output on a real glyph mask."""
    for preset in ("default", "cracked", "fine", "coarse", "cells"):
        result = voronoi_fill(_MASK_A, preset=preset, seed=42)
        assert len(result) == len(_MASK_A), f"preset={preset}: wrong row count"
        assert all(len(row) == len(_MASK_A[0]) for row in result), f"preset={preset}: col mismatch"
        assert any(ch != " " for row in result for ch in row), f"preset={preset}: all spaces"


def test_voronoi_fill_invalid_preset():
    """voronoi_fill raises ValueError for unknown preset."""
    with pytest.raises(ValueError):
        voronoi_fill(_MASK_A, preset="nonsense")


def test_voronoi_fill_empty_mask():
    """voronoi_fill handles all-zero mask gracefully."""
    empty = [[0.0, 0.0], [0.0, 0.0]]
    result = voronoi_fill(empty)
    assert result == ["  ", "  "]


def test_voronoi_fill_n_seeds_override():
    """n_seeds parameter overrides auto-scaling."""
    result = voronoi_fill(_MASK_A, n_seeds=4, seed=42)
    assert len(result) == len(_MASK_A)
    assert any(ch != " " for row in result for ch in row)


def test_voronoi_fill_via_render():
    """render(fill='voronoi') works end-to-end without error."""
    result = render("HI", font="block", fill="voronoi")
    assert isinstance(result, str)
    assert len(result) > 0


# -------------------------------------------------------------------------
# Fill registry

def test_fill_registry_contains_noise_and_cells():
    """_FILL_FNS must contain 'noise' and 'cells' keys."""
    assert "noise" in _FILL_FNS
    assert "cells" in _FILL_FNS


# =============================================================================
# A10 — Plasma Wave Fill tests
# =============================================================================

from justdoit.effects.generative import plasma_fill


def test_plasma_fill_basic():
    """plasma_fill returns correct shape with all-ink mask."""
    mask = [[1.0, 1.0, 0.0], [1.0, 1.0, 0.0]]
    result = plasma_fill(mask)
    assert len(result) == 2
    assert all(len(r) == 3 for r in result)
    # Exterior cells (mask < 0.5) must be spaces
    assert result[0][2] == " "
    assert result[1][2] == " "


def test_plasma_fill_exterior_is_space():
    """plasma_fill outputs space for all cells where mask < 0.5."""
    mask = [[0.0, 1.0, 0.0], [1.0, 0.0, 1.0]]
    result = plasma_fill(mask)
    assert result[0][0] == " "
    assert result[0][2] == " "
    assert result[1][1] == " "


def test_plasma_fill_ink_not_space():
    """plasma_fill outputs non-space chars for ink cells (mask >= 0.5)."""
    mask = [[1.0] * 5 for _ in range(4)]
    result = plasma_fill(mask)
    for row in result:
        for ch in row:
            assert ch != " "


def test_plasma_fill_time_varies():
    """Different t values produce different fills (animated plasma)."""
    mask = [[1.0] * 6 for _ in range(4)]
    r1 = plasma_fill(mask, t=0.0)
    r2 = plasma_fill(mask, t=1.5)
    # t shifts phase — output should differ
    assert r1 != r2


def test_plasma_fill_t_produces_variation():
    """t at different points in the cycle produces varied output.

    The plasma formula uses different phase multipliers for each wave
    (t, t*1.3, t*0.7, t*0.9), so the *combined* period is longer than 2π.
    We verify that across the range [0, 3π] we see at least 3 distinct frames.
    """
    import math
    mask = [[1.0] * 6 for _ in range(4)]
    t_values = [0.0, math.pi * 0.5, math.pi, math.pi * 1.5, math.pi * 2.0, math.pi * 3.0]
    frames = [tuple(plasma_fill(mask, t=t)) for t in t_values]
    unique = set(frames)
    assert len(unique) >= 3, f"Expected ≥3 distinct frames, got {len(unique)}"


def test_plasma_fill_presets():
    """All named presets render without error."""
    mask = [[1.0] * 6 for _ in range(4)]
    for preset in ["default", "tight", "slow", "diagonal"]:
        result = plasma_fill(mask, preset=preset)
        assert len(result) == 4
        assert all(len(r) == 6 for r in result)


def test_plasma_fill_unknown_preset():
    """Unknown preset raises ValueError."""
    import pytest
    with pytest.raises(ValueError, match="Unknown plasma preset"):
        plasma_fill([[1.0]], preset="nonexistent")


def test_plasma_fill_empty_mask():
    """plasma_fill handles all-zero mask gracefully."""
    empty = [[0.0, 0.0], [0.0, 0.0]]
    result = plasma_fill(empty)
    assert result == ["  ", "  "]


def test_plasma_fill_single_cell():
    """plasma_fill handles single-cell ink mask."""
    result = plasma_fill([[1.0]])
    assert len(result) == 1
    assert len(result[0]) == 1
    assert result[0][0] != " "


def test_plasma_via_render():
    """render(fill='plasma') works end-to-end."""
    result = render("HI", font="block", fill="plasma")
    assert isinstance(result, str)
    assert len(result) > 0


def test_plasma_tight_via_render():
    """render(fill='plasma_tight') works end-to-end."""
    result = render("HI", font="block", fill="plasma_tight")
    assert isinstance(result, str)
    assert len(result) > 0


def test_plasma_slow_via_render():
    """render(fill='plasma_slow') works end-to-end."""
    result = render("HI", font="block", fill="plasma_slow")
    assert isinstance(result, str)
    assert len(result) > 0


def test_plasma_diagonal_via_render():
    """render(fill='plasma_diagonal') works end-to-end."""
    result = render("HI", font="block", fill="plasma_diagonal")
    assert isinstance(result, str)
    assert len(result) > 0


def test_plasma_fill_kwargs_via_render():
    """render(fill='plasma', fill_kwargs={'t': 1.0}) passes t to plasma_fill."""
    r1 = render("HI", font="block", fill="plasma", fill_kwargs={"t": 0.0})
    r2 = render("HI", font="block", fill="plasma", fill_kwargs={"t": 1.5})
    # Different t → different output
    assert r1 != r2


def test_plasma_wave_animation():
    """plasma_wave preset yields correct number of frames."""
    from justdoit.animate.presets import plasma_wave
    frames = list(plasma_wave("HI", font="block", n_frames=6, loop=False))
    assert len(frames) == 6
    assert all(isinstance(f, str) for f in frames)
    assert all(len(f) > 0 for f in frames)


def test_plasma_wave_animation_loop():
    """plasma_wave with loop=True yields 2×n_frames frames."""
    from justdoit.animate.presets import plasma_wave
    frames = list(plasma_wave("HI", font="block", n_frames=6, loop=True))
    assert len(frames) == 12


def test_plasma_wave_animation_varies():
    """plasma_wave yields frames that differ (plasma is actually animating)."""
    from justdoit.animate.presets import plasma_wave
    frames = list(plasma_wave("HI", font="block", n_frames=6, loop=False))
    # Not all frames should be identical
    unique_frames = set(frames)
    assert len(unique_frames) > 1


def test_fill_registry_contains_plasma():
    """_FILL_FNS must contain plasma keys."""
    assert "plasma" in _FILL_FNS
    assert "plasma_tight" in _FILL_FNS
    assert "plasma_slow" in _FILL_FNS
    assert "plasma_diagonal" in _FILL_FNS
