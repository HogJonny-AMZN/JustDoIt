"""Tests for X_FRACTAL_CLASSIC — fractal_float_grid() and fractal_color_cycle()."""

import re
import pytest
from justdoit.effects.generative import fractal_float_grid
from justdoit.animate.presets import fractal_color_cycle


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_mask(rows: int = 5, cols: int = 8, fill: float = 1.0) -> list:
    """Create a uniform mask (all ink or all empty)."""
    return [[fill] * cols for _ in range(rows)]


def sparse_mask(rows: int = 5, cols: int = 8) -> list:
    """Create a mask with ink only in the top-left quadrant."""
    m = [[0.0] * cols for _ in range(rows)]
    for r in range(rows // 2 + 1):
        for c in range(cols // 2 + 1):
            m[r][c] = 1.0
    return m


ANSI_RE = re.compile(r"\033\[[0-9;]*m")


# ---------------------------------------------------------------------------
# fractal_float_grid — basic structure
# ---------------------------------------------------------------------------
def test_fractal_float_grid_returns_list():
    mask = make_mask()
    result = fractal_float_grid(mask)
    assert isinstance(result, list)


def test_fractal_float_grid_dimensions():
    rows, cols = 6, 10
    mask = make_mask(rows, cols)
    result = fractal_float_grid(mask)
    assert len(result) == rows
    for row in result:
        assert len(row) == cols


def test_fractal_float_grid_values_in_range():
    mask = make_mask()
    result = fractal_float_grid(mask)
    for row in result:
        for v in row:
            assert 0.0 <= v <= 1.0, f"Value {v} out of [0,1]"


def test_fractal_float_grid_outside_mask_is_zero():
    mask = sparse_mask(6, 10)
    result = fractal_float_grid(mask)
    for r in range(6):
        for c in range(10):
            if mask[r][c] < 0.5:
                assert result[r][c] == 0.0, f"Expected 0.0 outside mask at ({r},{c})"


def test_fractal_float_grid_inside_mask_has_values():
    mask = make_mask(8, 12)
    result = fractal_float_grid(mask)
    all_vals = [v for row in result for v in row]
    # At least some values should be non-zero (exterior cells)
    assert any(v > 0.0 for v in all_vals)


def test_fractal_float_grid_empty_mask():
    result = fractal_float_grid([])
    assert result == []


def test_fractal_float_grid_all_empty_mask():
    mask = make_mask(4, 6, fill=0.0)
    result = fractal_float_grid(mask)
    for row in result:
        for v in row:
            assert v == 0.0


def test_fractal_float_grid_different_params_produce_different_grids():
    mask = make_mask(8, 12)
    g1 = fractal_float_grid(mask, cx=-0.745, cy=0.113, zoom=0.6)
    g2 = fractal_float_grid(mask, cx=0.0, cy=0.65, zoom=0.3)
    # The grids should differ
    flat1 = [v for row in g1 for v in row]
    flat2 = [v for row in g2 for v in row]
    assert flat1 != flat2


def test_fractal_float_grid_zoom_affects_result():
    mask = make_mask(8, 12)
    g1 = fractal_float_grid(mask, zoom=0.5)
    g2 = fractal_float_grid(mask, zoom=2.0)
    flat1 = [v for row in g1 for v in row]
    flat2 = [v for row in g2 for v in row]
    assert flat1 != flat2


def test_fractal_float_grid_julia_mode():
    mask = make_mask(8, 12)
    result = fractal_float_grid(mask, julia=True, julia_c=complex(-0.7, 0.27))
    assert isinstance(result, list)
    assert len(result) == 8
    for row in result:
        for v in row:
            assert 0.0 <= v <= 1.0


def test_fractal_float_grid_julia_differs_from_mandelbrot():
    mask = make_mask(8, 12)
    mandelbrot = fractal_float_grid(mask, cx=-0.5, cy=0.0, zoom=1.0, julia=False)
    julia = fractal_float_grid(mask, cx=-0.5, cy=0.0, zoom=1.0, julia=True)
    flat_m = [v for row in mandelbrot for v in row]
    flat_j = [v for row in julia for v in row]
    assert flat_m != flat_j


# ---------------------------------------------------------------------------
# ESCAPE_PALETTE registration
# ---------------------------------------------------------------------------
def test_escape_palette_in_registry():
    from justdoit.effects.color import PALETTE_REGISTRY, ESCAPE_PALETTE
    assert "escape" in PALETTE_REGISTRY
    assert PALETTE_REGISTRY["escape"] is ESCAPE_PALETTE


def test_escape_palette_has_correct_length():
    from justdoit.effects.color import ESCAPE_PALETTE
    assert len(ESCAPE_PALETTE) == 12


def test_escape_palette_values_are_rgb_tuples():
    from justdoit.effects.color import ESCAPE_PALETTE
    for entry in ESCAPE_PALETTE:
        assert len(entry) == 3
        for ch in entry:
            assert 0 <= ch <= 255


# ---------------------------------------------------------------------------
# fractal_color_cycle — generator behavior
# ---------------------------------------------------------------------------
def test_fractal_color_cycle_is_iterator():
    from typing import Iterator
    gen = fractal_color_cycle(text_plain="HI", n_frames=4)
    assert hasattr(gen, "__iter__")
    assert hasattr(gen, "__next__")


def test_fractal_color_cycle_yields_strings():
    frames = list(fractal_color_cycle(text_plain="HI", n_frames=4))
    assert len(frames) > 0
    for f in frames:
        assert isinstance(f, str)


def test_fractal_color_cycle_frames_nonempty():
    frames = list(fractal_color_cycle(text_plain="HI", n_frames=4))
    for f in frames:
        assert len(f.strip()) > 0


def test_fractal_color_cycle_contains_ansi_codes():
    frames = list(fractal_color_cycle(text_plain="HI", n_frames=4))
    found = any(ANSI_RE.search(f) for f in frames)
    assert found, "Expected ANSI escape codes in colored frames"


def test_fractal_color_cycle_frame_count_with_loop():
    n = 8
    frames = list(fractal_color_cycle(text_plain="HI", n_frames=n, loop=True))
    # loop=True: forward (n) + reversed (n) = 2*n
    assert len(frames) == 2 * n


def test_fractal_color_cycle_frame_count_no_loop():
    n = 6
    frames = list(fractal_color_cycle(text_plain="HI", n_frames=n, loop=False))
    assert len(frames) == n


def test_fractal_color_cycle_frames_vary():
    frames = list(fractal_color_cycle(text_plain="HI", n_frames=8, loop=False))
    # Palette cycling should produce different frames
    unique = len(set(frames))
    assert unique > 1, "Expected palette cycling to produce varied frames"


def test_fractal_color_cycle_julia_mode():
    frames = list(fractal_color_cycle(
        text_plain="HI",
        n_frames=4,
        julia=True,
        julia_c=complex(-0.7, 0.27),
        loop=False,
    ))
    assert len(frames) == 4
    for f in frames:
        assert isinstance(f, str)


def test_fractal_color_cycle_custom_palette():
    frames = list(fractal_color_cycle(
        text_plain="HI",
        n_frames=4,
        palette_name="fire",
        loop=False,
    ))
    assert len(frames) == 4
    assert any(ANSI_RE.search(f) for f in frames)


def test_fractal_color_cycle_default_text():
    frames = list(fractal_color_cycle(n_frames=4, loop=False))
    assert len(frames) == 4
    for f in frames:
        assert isinstance(f, str)
        assert len(f.strip()) > 0
