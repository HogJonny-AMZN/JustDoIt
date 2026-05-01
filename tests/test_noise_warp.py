"""Tests for X_NOISE_WARP: Perlin Noise Phase-Map Sine Warp.

Covers:
  - noise_float_grid() companion function
  - phase_map extension to sine_warp()
  - noise_warp() animation preset
  - Structural properties: frame count, non-empty output, color codes, bloom
  - Distinctness from amplitude_map cross-breeds: phase_map creates non-uniform timing
  - Loop behavior (forward + reverse)
"""

import math
import re

import pytest

# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------
ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def _count_fg_codes(text: str) -> int:
    """Count foreground color ANSI codes (\033[38;2;...)."""
    return len(re.findall(r"\033\[38;2;[0-9;]+m", text))


def _count_bg_codes(text: str) -> int:
    """Count background color ANSI codes (\033[48;2;...)."""
    return len(re.findall(r"\033\[48;2;[0-9;]+m", text))


# -------------------------------------------------------------------------
# noise_float_grid tests
# -------------------------------------------------------------------------

class TestNoiseFloatGrid:
    """Tests for noise_float_grid() companion function."""

    def test_returns_list(self):
        from justdoit.effects.generative import noise_float_grid
        from justdoit.fonts import FONTS
        glyph = FONTS["block"]["A"]
        from justdoit.core.glyph import glyph_to_mask
        mask = glyph_to_mask(glyph)
        result = noise_float_grid(mask)
        assert isinstance(result, list)

    def test_shape_matches_mask(self):
        from justdoit.effects.generative import noise_float_grid
        from justdoit.fonts import FONTS
        from justdoit.core.glyph import glyph_to_mask
        glyph = FONTS["block"]["J"]
        mask = glyph_to_mask(glyph)
        result = noise_float_grid(mask)
        assert len(result) == len(mask)
        for r, row in enumerate(result):
            assert len(row) == len(mask[r]), f"row {r} length mismatch"

    def test_values_in_range(self):
        from justdoit.effects.generative import noise_float_grid
        from justdoit.fonts import FONTS
        from justdoit.core.glyph import glyph_to_mask
        glyph = FONTS["block"]["U"]
        mask = glyph_to_mask(glyph)
        result = noise_float_grid(mask)
        for r, row in enumerate(result):
            for c, v in enumerate(row):
                assert 0.0 <= v <= 1.0, f"out-of-range value {v} at ({r},{c})"

    def test_exterior_cells_are_zero(self):
        from justdoit.effects.generative import noise_float_grid
        from justdoit.fonts import FONTS
        from justdoit.core.glyph import glyph_to_mask
        glyph = FONTS["block"]["S"]
        mask = glyph_to_mask(glyph)
        result = noise_float_grid(mask)
        for r, row in enumerate(mask):
            for c, val in enumerate(row):
                if val < 0.5:
                    assert result[r][c] == 0.0, f"exterior cell ({r},{c}) non-zero: {result[r][c]}"

    def test_ink_cells_have_nonzero_values(self):
        from justdoit.effects.generative import noise_float_grid
        from justdoit.fonts import FONTS
        from justdoit.core.glyph import glyph_to_mask
        glyph = FONTS["block"]["T"]
        mask = glyph_to_mask(glyph)
        result = noise_float_grid(mask)
        ink_values = [result[r][c] for r in range(len(mask)) for c in range(len(mask[r])) if mask[r][c] >= 0.5]
        assert any(v > 0.0 for v in ink_values), "all ink cells are zero"

    def test_deterministic_with_seed(self):
        from justdoit.effects.generative import noise_float_grid
        from justdoit.fonts import FONTS
        from justdoit.core.glyph import glyph_to_mask
        glyph = FONTS["block"]["D"]
        mask = glyph_to_mask(glyph)
        r1 = noise_float_grid(mask, seed=7)
        r2 = noise_float_grid(mask, seed=7)
        assert r1 == r2, "same seed should produce identical output"

    def test_different_seeds_differ(self):
        from justdoit.effects.generative import noise_float_grid
        from justdoit.fonts import FONTS
        from justdoit.core.glyph import glyph_to_mask
        glyph = FONTS["block"]["O"]
        mask = glyph_to_mask(glyph)
        r1 = noise_float_grid(mask, seed=1)
        r2 = noise_float_grid(mask, seed=99)
        all_equal = all(
            r1[row][col] == r2[row][col]
            for row in range(len(r1))
            for col in range(len(r1[row]))
        )
        assert not all_equal, "different seeds should produce different grids"

    def test_scale_affects_output(self):
        from justdoit.effects.generative import noise_float_grid
        from justdoit.fonts import FONTS
        from justdoit.core.glyph import glyph_to_mask
        glyph = FONTS["block"]["I"]
        mask = glyph_to_mask(glyph)
        r1 = noise_float_grid(mask, scale=0.4, seed=1)
        r2 = noise_float_grid(mask, scale=1.5, seed=1)
        # Same seed, different scale → different values
        all_equal = all(
            r1[row][col] == r2[row][col]
            for row in range(len(r1))
            for col in range(len(r1[row]))
        )
        assert not all_equal

    def test_empty_mask_returns_empty(self):
        from justdoit.effects.generative import noise_float_grid
        assert noise_float_grid([]) == []

    def test_space_char_mask(self):
        from justdoit.effects.generative import noise_float_grid
        from justdoit.fonts import FONTS
        from justdoit.core.glyph import glyph_to_mask
        glyph = FONTS["block"].get(" ", FONTS["block"]["A"])
        mask = glyph_to_mask(glyph)
        result = noise_float_grid(mask)
        assert len(result) == len(mask)


# -------------------------------------------------------------------------
# sine_warp phase_map extension tests
# -------------------------------------------------------------------------

class TestSineWarpPhaseMap:
    """Tests for the new phase_map parameter on sine_warp()."""

    def test_phase_map_accepted(self):
        from justdoit.effects.spatial import sine_warp
        from justdoit.core.rasterizer import render
        text = render("HI", font="block")
        rows = text.count("\n") + 1
        phase_map = [i * 0.3 for i in range(rows)]
        result = sine_warp(text, amplitude=3.0, phase_map=phase_map)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_phase_map_none_is_backward_compatible(self):
        from justdoit.effects.spatial import sine_warp
        from justdoit.core.rasterizer import render
        text = render("HI", font="block")
        # Should behave identically to old call with no phase_map
        r1 = sine_warp(text, amplitude=3.0, phase_offset=1.0)
        r2 = sine_warp(text, amplitude=3.0, phase_offset=1.0, phase_map=None)
        assert r1 == r2

    def test_phase_map_changes_output(self):
        from justdoit.effects.spatial import sine_warp
        from justdoit.core.rasterizer import render
        text = render("HI", font="block")
        rows = text.count("\n") + 1
        r_no_map = sine_warp(text, amplitude=3.0)
        r_with_map = sine_warp(text, amplitude=3.0, phase_map=[math.pi] * rows)
        # With all-pi phase map rows should have different offsets than no map
        assert r_no_map != r_with_map

    def test_phase_map_zero_vector_matches_no_map(self):
        """phase_map=[0, 0, ...] should produce identical output to no phase_map."""
        from justdoit.effects.spatial import sine_warp
        from justdoit.core.rasterizer import render
        text = render("HI", font="block")
        rows = text.count("\n") + 1
        r1 = sine_warp(text, amplitude=3.0, phase_offset=0.5)
        r2 = sine_warp(text, amplitude=3.0, phase_offset=0.5, phase_map=[0.0] * rows)
        assert r1 == r2

    def test_phase_map_shorter_than_rows_uses_zero_fallback(self):
        """Rows beyond phase_map length should use zero additional phase."""
        from justdoit.effects.spatial import sine_warp
        from justdoit.core.rasterizer import render
        text = render("HI", font="block")
        rows = text.count("\n") + 1
        # Only provide phase for first 2 rows
        short_map = [0.0, 0.0]
        r1 = sine_warp(text, amplitude=3.0)
        r2 = sine_warp(text, amplitude=3.0, phase_map=short_map)
        assert r1 == r2, "short phase_map of all zeros should match no phase_map"

    def test_phase_map_and_amplitude_map_combine(self):
        """phase_map and amplitude_map should both be usable simultaneously."""
        from justdoit.effects.spatial import sine_warp
        from justdoit.core.rasterizer import render
        text = render("HI", font="block")
        rows = text.count("\n") + 1
        amp_map = [2.0 + i * 0.5 for i in range(rows)]
        phase_map = [i * 0.4 for i in range(rows)]
        result = sine_warp(text, amplitude_map=amp_map, phase_map=phase_map)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_phase_map_produces_non_uniform_row_offsets(self):
        """Different phase_map values per row should produce different leading spaces."""
        from justdoit.effects.spatial import sine_warp
        from justdoit.core.rasterizer import render
        # Use plain text with no ANSI for simple space counting
        text = "AAAA\nAAAA\nAAAA"
        # phase_map: row 0 gets pi/2 (peak), row 1 gets 0 (zero crossing), row 2 gets pi (trough)
        phase_map = [math.pi / 2, 0.0, math.pi]
        result = sine_warp(text, amplitude=5.0, frequency=0.0, phase_map=phase_map)
        lines = result.split("\n")
        leading = [len(l) - len(l.lstrip(" ")) for l in lines]
        # All three rows should have different leading space counts
        assert len(set(leading)) > 1, f"Expected varied offsets, got {leading}"


# -------------------------------------------------------------------------
# noise_warp preset tests
# -------------------------------------------------------------------------

class TestNoiseWarpPreset:
    """Tests for the noise_warp() animation preset."""

    def test_returns_iterator(self):
        from justdoit.animate.presets import noise_warp
        gen = noise_warp("HI", n_frames=4, loop=False)
        frames = list(gen)
        assert len(frames) == 4

    def test_loop_doubles_frame_count(self):
        from justdoit.animate.presets import noise_warp
        frames = list(noise_warp("HI", n_frames=6, loop=True))
        assert len(frames) == 12

    def test_frames_are_strings(self):
        from justdoit.animate.presets import noise_warp
        frames = list(noise_warp("HI", n_frames=4, loop=False))
        for i, f in enumerate(frames):
            assert isinstance(f, str), f"frame {i} is not a string"

    def test_frames_are_nonempty(self):
        from justdoit.animate.presets import noise_warp
        frames = list(noise_warp("HI", n_frames=4, loop=False))
        for i, f in enumerate(frames):
            assert len(f) > 0, f"frame {i} is empty"

    def test_frames_have_fg_color_codes(self):
        from justdoit.animate.presets import noise_warp
        frames = list(noise_warp("HI", n_frames=4, loop=False))
        for i, f in enumerate(frames):
            assert _count_fg_codes(f) > 0, f"frame {i} has no foreground color codes"

    def test_frames_have_bloom_bg_codes(self):
        from justdoit.animate.presets import noise_warp
        frames = list(noise_warp("HI", n_frames=4, loop=False, bloom_radius=2))
        for i, f in enumerate(frames):
            assert _count_bg_codes(f) > 0, f"frame {i} has no bloom background codes"

    def test_frames_vary_across_animation(self):
        """Different phase offsets should produce different leading-space layouts."""
        from justdoit.animate.presets import noise_warp
        frames = list(noise_warp("HI", n_frames=8, loop=False))
        plain_frames = [_strip_ansi(f) for f in frames]
        # Not all frames should be identical
        assert len(set(plain_frames)) > 1, "All frames are identical — animation is broken"

    def test_loop_frames_are_palindrome(self):
        """With loop=True, forward frames should mirror reverse frames (plain content)."""
        from justdoit.animate.presets import noise_warp
        n = 6
        frames = list(noise_warp("HI", n_frames=n, loop=True))
        plain = [_strip_ansi(f) for f in frames]
        fwd = plain[:n]
        rev = plain[n:]
        assert fwd == list(reversed(rev)), "loop frames are not palindromic"

    def test_static_color_same_across_frames(self):
        """Noise chars and colors are static (same seed) — only warp geometry changes."""
        from justdoit.animate.presets import noise_warp
        frames = list(noise_warp("HI", n_frames=4, loop=False, noise_seed=1))
        fg_counts = [_count_fg_codes(f) for f in frames]
        # Same number of colored cells per frame (static char render)
        assert len(set(fg_counts)) == 1, f"Foreground code count varies across frames: {fg_counts}"

    def test_different_seeds_produce_different_output(self):
        from justdoit.animate.presets import noise_warp
        frames1 = list(noise_warp("HI", n_frames=4, loop=False, noise_seed=1))
        frames2 = list(noise_warp("HI", n_frames=4, loop=False, noise_seed=99))
        plain1 = [_strip_ansi(f) for f in frames1]
        plain2 = [_strip_ansi(f) for f in frames2]
        assert plain1 != plain2, "different seeds should produce different outputs"

    def test_different_scales_produce_different_output(self):
        from justdoit.animate.presets import noise_warp
        frames1 = list(noise_warp("HI", n_frames=4, loop=False, noise_scale=0.2))
        frames2 = list(noise_warp("HI", n_frames=4, loop=False, noise_scale=1.2))
        plain1 = [_strip_ansi(f) for f in frames1]
        plain2 = [_strip_ansi(f) for f in frames2]
        assert plain1 != plain2

    def test_works_with_longer_text(self):
        from justdoit.animate.presets import noise_warp
        frames = list(noise_warp("JUST DO IT", n_frames=4, loop=False))
        assert len(frames) == 4
        for f in frames:
            assert len(_strip_ansi(f)) > 0

    def test_amplitude_zero_all_frames_identical_plain(self):
        """With amplitude=0, no warp occurs — all frames should have identical plain content."""
        from justdoit.animate.presets import noise_warp
        frames = list(noise_warp("HI", n_frames=6, loop=False, max_amplitude=0.0))
        plain = [_strip_ansi(f) for f in frames]
        assert len(set(plain)) == 1, "amplitude=0 should produce identical plain text"

    def test_bloom_disabled_no_bg_codes(self):
        """bloom_radius=0 should produce no background color codes."""
        from justdoit.animate.presets import noise_warp
        frames = list(noise_warp("HI", n_frames=4, loop=False, bloom_radius=0))
        for i, f in enumerate(frames):
            assert _count_bg_codes(f) == 0, f"frame {i} has unexpected bg codes with radius=0"

    def test_integration_render_noise_fill(self):
        """Sanity: noise fill itself works via render() before noise_warp processes it."""
        from justdoit.core.rasterizer import render
        result = render("HI", font="block", fill="noise", fill_kwargs={"seed": 1})
        assert isinstance(result, str)
        plain = _strip_ansi(result)
        assert any(c not in (" ", "\n") for c in plain)

    def test_single_char_text(self):
        from justdoit.animate.presets import noise_warp
        frames = list(noise_warp("A", n_frames=4, loop=False))
        assert len(frames) == 4
        for f in frames:
            assert len(f) > 0
