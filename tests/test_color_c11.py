"""
Tests for C11 — fill_float_colorize() and palette constants.
"""

import pytest
from justdoit.effects.color import (
    fill_float_colorize,
    FIRE_PALETTE,
    LAVA_PALETTE,
    SPECTRAL_PALETTE,
    BIO_PALETTE,
    PALETTE_REGISTRY,
    _lerp_palette,
    _tc_c11,
)


# -------------------------------------------------------------------------
class TestPaletteConstants:
    def test_all_four_palettes_registered(self):
        assert {"fire", "lava", "spectral", "bio"}.issubset(set(PALETTE_REGISTRY.keys()))

    def test_fire_palette_is_list_of_tuples(self):
        for entry in FIRE_PALETTE:
            assert isinstance(entry, (list, tuple)) and len(entry) == 3

    def test_lava_palette_is_list_of_tuples(self):
        for entry in LAVA_PALETTE:
            assert isinstance(entry, (list, tuple)) and len(entry) == 3

    def test_spectral_palette_is_list_of_tuples(self):
        for entry in SPECTRAL_PALETTE:
            assert isinstance(entry, (list, tuple)) and len(entry) == 3

    def test_bio_palette_is_list_of_tuples(self):
        for entry in BIO_PALETTE:
            assert isinstance(entry, (list, tuple)) and len(entry) == 3

    def test_registry_palette_fire_matches_constant(self):
        assert PALETTE_REGISTRY["fire"] is FIRE_PALETTE

    def test_registry_palette_spectral_matches_constant(self):
        assert PALETTE_REGISTRY["spectral"] is SPECTRAL_PALETTE


# -------------------------------------------------------------------------
class TestLerpPalette:
    def test_lerp_t0_returns_first_entry(self):
        palette = [(0, 0, 0), (255, 255, 255)]
        r, g, b = _lerp_palette(palette, 0.0)
        assert r == 0 and g == 0 and b == 0

    def test_lerp_t1_returns_last_entry(self):
        palette = [(0, 0, 0), (255, 255, 255)]
        r, g, b = _lerp_palette(palette, 1.0)
        assert r == 255 and g == 255 and b == 255

    def test_lerp_t_midpoint(self):
        palette = [(0, 0, 0), (100, 100, 100)]
        r, g, b = _lerp_palette(palette, 0.5)
        assert 45 <= r <= 55  # linear midpoint ~50

    def test_lerp_clamps_below_zero(self):
        palette = [(10, 10, 10), (200, 200, 200)]
        r, g, b = _lerp_palette(palette, -1.0)
        assert r == 10 and g == 10 and b == 10

    def test_lerp_clamps_above_one(self):
        palette = [(10, 10, 10), (200, 200, 200)]
        r, g, b = _lerp_palette(palette, 2.0)
        assert r == 200 and g == 200 and b == 200

    def test_lerp_single_entry(self):
        palette = [(42, 42, 42)]
        r, g, b = _lerp_palette(palette, 0.5)
        assert r == 42 and g == 42 and b == 42


# -------------------------------------------------------------------------
class TestTcC11:
    def test_tc_format(self):
        code = _tc_c11(255, 128, 0)
        assert code == "\033[38;2;255;128;0m"

    def test_tc_zero_values(self):
        code = _tc_c11(0, 0, 0)
        assert code == "\033[38;2;0;0;0m"


# -------------------------------------------------------------------------
class TestFillFloatColorize:
    def _make_simple_grid(self, text: str, val: float) -> list:
        """Build a float_grid of uniform value for all characters in text."""
        lines = text.split("\n")
        grid = []
        for line in lines:
            grid.append([val] * len(line))
        return grid

    def test_space_cells_remain_unchanged(self):
        text = "  X  "
        grid = [[0.0, 0.0, 0.5, 0.0, 0.0]]
        result = fill_float_colorize(text, grid, SPECTRAL_PALETTE)
        # The line in the result should start and end with spaces
        line = result.split("\n")[0]
        assert line.startswith("  ")
        assert "X" in line

    def test_output_contains_ansi_24bit_code(self):
        text = "HI"
        grid = [[0.5, 0.5]]
        result = fill_float_colorize(text, grid, FIRE_PALETTE)
        assert "\033[38;2;" in result

    def test_empty_text_returns_empty(self):
        result = fill_float_colorize("", [], FIRE_PALETTE)
        assert result == ""

    def test_all_spaces_no_ansi(self):
        text = "   "
        grid = [[0.0, 0.0, 0.0]]
        result = fill_float_colorize(text, grid, FIRE_PALETTE)
        # No ANSI codes — all spaces
        assert "\033" not in result

    def test_existing_ansi_stripped_and_replaced(self):
        # pre-colored text with old codes should get new codes
        text = "\033[91mA\033[0m"
        grid = [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]  # generous grid
        result = fill_float_colorize(text, grid, FIRE_PALETTE)
        # Should contain 24-bit code, not the original 91m
        assert "\033[38;2;" in result

    def test_float_grid_out_of_bounds_defaults_to_zero(self):
        # float_grid shorter than text — shouldn't crash
        text = "HELLO"
        grid = [[0.5]]  # only 1 row, 1 col — rest default to 0.0
        result = fill_float_colorize(text, grid, FIRE_PALETTE)
        assert "\033[38;2;" in result

    def test_multiline_text(self):
        text = "AB\nCD"
        grid = [[0.0, 1.0], [0.5, 0.5]]
        result = fill_float_colorize(text, grid, SPECTRAL_PALETTE)
        lines = result.split("\n")
        assert len(lines) == 2

    def test_uniform_midpoint_palette(self):
        """All cells at t=0.5 should get the same midpoint color."""
        text = "ABC"
        grid = [[0.5, 0.5, 0.5]]
        result = fill_float_colorize(text, grid, [(0, 0, 0), (100, 100, 100)])
        # Midpoint of (0,0,0)→(100,100,100) at t=0.5 ≈ (50,50,50)
        assert "\033[38;2;50;50;50m" in result


# -------------------------------------------------------------------------
class TestFillFloatColorizeWithRender:
    """Integration tests — fill_float_colorize applied to actual render() output."""

    def test_works_with_render_output(self):
        from justdoit.core.rasterizer import render
        rendered = render("HI", fill="voronoi_cracked")
        lines = rendered.split("\n")
        n_rows = len(lines)
        n_cols = max(len(line) for line in lines)
        # Build a uniform float grid
        float_grid = [[0.5] * n_cols for _ in range(n_rows)]
        result = fill_float_colorize(rendered, float_grid, SPECTRAL_PALETTE)
        assert "\033[38;2;" in result
        assert result.count("\n") == rendered.count("\n")
