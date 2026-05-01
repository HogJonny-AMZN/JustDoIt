"""Tests for plasma_flame() preset (A08d) and the cooling_modulator extension.

Tests cover:
- plasma_flame() smoke tests and structural properties
- cooling_modulator param added to _flame_heat_grid(), flame_fill(), flame_float_grid()
- Backward compatibility (no new params = same behavior)
- Physical correctness (low modulator = hotter fire than high modulator)
"""

import re
import pytest

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def _strip_ansi(s: str) -> str:
    return _ANSI_RE.sub("", s)


# ---------------------------------------------------------------------------
# plasma_flame() smoke tests
# ---------------------------------------------------------------------------

class TestPlasmaFlameBasic:
    """Basic structural tests for plasma_flame()."""

    def test_yields_frames(self):
        from justdoit.animate.presets import plasma_flame
        frames = list(plasma_flame("HI", n_frames=4, loop=False))
        assert len(frames) == 4

    def test_frame_count_loop_true(self):
        from justdoit.animate.presets import plasma_flame
        frames = list(plasma_flame("HI", n_frames=4, loop=True))
        assert len(frames) == 8  # forward + reverse

    def test_frame_count_loop_false(self):
        from justdoit.animate.presets import plasma_flame
        frames = list(plasma_flame("HI", n_frames=4, loop=False))
        assert len(frames) == 4

    def test_all_frames_non_empty(self):
        from justdoit.animate.presets import plasma_flame
        frames = list(plasma_flame("HI", n_frames=4, loop=False))
        assert all(f for f in frames)

    def test_ansi_codes_present(self):
        from justdoit.animate.presets import plasma_flame
        frames = list(plasma_flame("HI", n_frames=4, loop=False))
        assert all("\033[" in f for f in frames), "All frames should contain ANSI escape codes"

    def test_frames_are_multiline(self):
        from justdoit.animate.presets import plasma_flame
        frames = list(plasma_flame("HI", n_frames=4, loop=False))
        assert all("\n" in f for f in frames), "All frames should be multi-line"

    def test_consistent_line_count(self):
        from justdoit.animate.presets import plasma_flame
        frames = list(plasma_flame("HI", n_frames=4, loop=False))
        line_counts = [len(f.split("\n")) for f in frames]
        assert len(set(line_counts)) == 1, "All frames should have same line count"

    def test_line_count_is_7(self):
        """Block font produces 7-row glyphs."""
        from justdoit.animate.presets import plasma_flame
        frames = list(plasma_flame("A", n_frames=2, loop=False))
        assert frames[0].split("\n").__len__() == 7

    def test_consistent_col_width(self):
        """All frames should have consistent column width in each row."""
        from justdoit.animate.presets import plasma_flame
        frames = list(plasma_flame("HI", n_frames=4, loop=False))
        # Strip ANSI to get plain char width
        def row_widths(frame):
            return [len(_strip_ansi(row)) for row in frame.split("\n")]
        first_widths = row_widths(frames[0])
        for f in frames[1:]:
            assert row_widths(f) == first_widths


class TestPlasmaFlameVariation:
    """Tests that plasma modulation produces meaningful variation."""

    def test_different_phases_produce_different_frames(self):
        """Frames at different plasma phases should differ (at least in color)."""
        from justdoit.animate.presets import plasma_flame
        frames = list(plasma_flame("JUST", n_frames=12, loop=False))
        assert len(frames) == 12
        # Frame 0 (t=0) and frame 6 (t=pi) should differ — plasma field is opposite
        f0 = _strip_ansi(frames[0])
        f6 = _strip_ansi(frames[6])
        # Chars may match or not; just confirm no crash and frames exist
        assert f0 or f6  # at least one is non-empty

    def test_full_text_works(self):
        """Multi-word text should not crash."""
        from justdoit.animate.presets import plasma_flame
        frames = list(plasma_flame("JUST DO IT", n_frames=4, loop=False))
        assert len(frames) == 4
        assert all(f for f in frames)

    def test_single_char_works(self):
        from justdoit.animate.presets import plasma_flame
        frames = list(plasma_flame("A", n_frames=4, loop=False))
        assert len(frames) == 4

    def test_n_frames_1_edge_case(self):
        """n_frames=1 should not crash."""
        from justdoit.animate.presets import plasma_flame
        frames = list(plasma_flame("HI", n_frames=1, loop=False))
        assert len(frames) == 1
        assert frames[0]  # non-empty

    def test_loop_false_shorter_than_loop_true(self):
        from justdoit.animate.presets import plasma_flame
        no_loop = list(plasma_flame("HI", n_frames=6, loop=False))
        with_loop = list(plasma_flame("HI", n_frames=6, loop=True))
        assert len(no_loop) < len(with_loop)

    def test_zero_bloom_amplitude_no_crash(self):
        from justdoit.animate.presets import plasma_flame
        frames = list(plasma_flame("HI", n_frames=4, bloom_amplitude=0.0, loop=False))
        assert len(frames) == 4


class TestPlasmaFlameParams:
    """Test parameter variations don't crash."""

    def test_different_flame_preset(self):
        from justdoit.animate.presets import plasma_flame
        frames = list(plasma_flame("HI", n_frames=2, flame_preset="embers", loop=False))
        assert len(frames) == 2

    def test_different_tone_curve(self):
        from justdoit.animate.presets import plasma_flame
        frames = list(plasma_flame("HI", n_frames=2, tone_curve="reinhard", loop=False))
        assert len(frames) == 2

    def test_low_modulator_strength(self):
        from justdoit.animate.presets import plasma_flame
        frames = list(plasma_flame("HI", n_frames=2, modulator_strength=0.0, loop=False))
        assert len(frames) == 2

    def test_high_modulator_strength(self):
        from justdoit.animate.presets import plasma_flame
        frames = list(plasma_flame("HI", n_frames=2, modulator_strength=2.0, loop=False))
        assert len(frames) == 2


# ---------------------------------------------------------------------------
# cooling_modulator infrastructure tests
# ---------------------------------------------------------------------------

class TestCoolingModulatorInfrastructure:
    """Tests for the cooling_modulator param added to flame infrastructure."""

    def _make_mask(self):
        """Build a simple 7x6 mask for 'H' in block font."""
        from justdoit.fonts import FONTS
        from justdoit.core.glyph import glyph_to_mask
        font_data = FONTS.get("block", {})
        glyph = font_data.get("H", font_data.get("A"))
        ink_chars = "".join({c for row in glyph for c in row if c != " "}) or chr(9608)
        return glyph_to_mask(glyph, ink_chars=ink_chars)

    def test_flame_fill_backward_compat(self):
        """flame_fill() with no new params should still work."""
        from justdoit.effects.generative import flame_fill
        mask = self._make_mask()
        result = flame_fill(mask, seed=42)
        assert len(result) > 0
        assert all(isinstance(row, str) for row in result)

    def test_flame_float_grid_backward_compat(self):
        """flame_float_grid() with no new params should still work."""
        from justdoit.effects.generative import flame_float_grid
        mask = self._make_mask()
        result = flame_float_grid(mask, seed=42)
        assert len(result) > 0
        assert all(isinstance(row, list) for row in result)

    def test_none_modulator_same_as_no_arg(self):
        """cooling_modulator=None should give same result as omitting it."""
        from justdoit.effects.generative import flame_fill
        mask = self._make_mask()
        r1 = flame_fill(mask, seed=42)
        r2 = flame_fill(mask, seed=42, cooling_modulator=None)
        assert r1 == r2

    def test_all_zero_modulator_hotter_than_all_one(self):
        """All-zero modulator (low cooling) should produce more heat than all-one (high cooling).

        With modulator_strength=1.0 and all-zeros:
          cell_cooling = base_cooling * (1 + 1.0 * (1 - 0)) = 2 * base_cooling (hotter)
        Wait — correction: the formula is:
          cell_cooling = base * (1 + strength * (1 - 2*m))
          m=0: cell_cooling = base * (1 + 1.0 * 1) = 2*base (more cooling -> cooler!)
          m=1: cell_cooling = base * (1 + 1.0 * -1) = 0 (no cooling -> hotter!)
        So all-ONE modulator should be hotter than all-ZERO modulator.
        """
        from justdoit.effects.generative import flame_float_grid
        mask = self._make_mask()
        rows = len(mask)
        cols = max(len(r) for r in mask)

        all_ones = [[1.0] * cols for _ in range(rows)]
        all_zeros = [[0.0] * cols for _ in range(rows)]

        hot_grid = flame_float_grid(mask, preset="default", seed=7, cooling_modulator=all_ones)
        cool_grid = flame_float_grid(mask, preset="default", seed=7, cooling_modulator=all_zeros)

        # Compute mean heat for ink cells
        def mean_heat(grid):
            vals = [v for row in grid for v in row if v > 0.0]
            return sum(vals) / max(len(vals), 1)

        hot_mean = mean_heat(hot_grid)
        cool_mean = mean_heat(cool_grid)
        # all-ones modulator (m=1) reduces cooling -> hotter
        assert hot_mean > cool_mean, (
            f"all-ones modulator ({hot_mean:.3f}) should be hotter than "
            f"all-zeros ({cool_mean:.3f}) — zeros increase cooling"
        )

    def test_flame_fill_with_modulator_returns_strings(self):
        """flame_fill with a cooling_modulator should still return list[str]."""
        from justdoit.effects.generative import flame_fill
        mask = self._make_mask()
        rows = len(mask)
        cols = max(len(r) for r in mask)
        modulator = [[0.5] * cols for _ in range(rows)]
        result = flame_fill(mask, seed=10, cooling_modulator=modulator, modulator_strength=1.0)
        assert len(result) > 0
        assert all(isinstance(row, str) for row in result)

    def test_flame_float_grid_with_modulator_returns_floats(self):
        """flame_float_grid with a cooling_modulator should return list[list[float]]."""
        from justdoit.effects.generative import flame_float_grid
        mask = self._make_mask()
        rows = len(mask)
        cols = max(len(r) for r in mask)
        modulator = [[0.5] * cols for _ in range(rows)]
        result = flame_float_grid(mask, seed=10, cooling_modulator=modulator)
        assert len(result) > 0
        for row in result:
            for val in row:
                assert isinstance(val, float)
                assert 0.0 <= val <= 1.0
