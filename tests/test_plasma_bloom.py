"""Tests for plasma_bloom animation preset (X_PLASMA_BLOOM).

Covers:
- Basic output structure (frame count, non-empty, string type)
- Chromatic bloom: background ANSI codes present on bloom cells
- Foreground 24-bit color codes: spectral colorization applied
- Loop behavior: 2×n_frames when loop=True
- Single cycle (loop=False): exactly n_frames
- Plasma preset propagation (tight, slow, diagonal)
- Palette propagation (spectral, lava, fire)
- Radius and falloff params
- Multi-line frames (7 rows for block font "HI")
- Chromatic bloom color varies across frames (hue shifts with plasma)
"""

import re
import pytest
from justdoit.animate.presets import plasma_bloom

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")

# Pattern for 24-bit ANSI foreground: \033[38;2;r;g;bm
_FG_COLOR_RE = re.compile(r"\033\[38;2;(\d+);(\d+);(\d+)m")

# Pattern for 24-bit ANSI background: \033[48;2;r;g;bm  (bloom cells)
_BG_COLOR_RE = re.compile(r"\033\[48;2;(\d+);(\d+);(\d+)m")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _count_bg_codes(frame: str) -> int:
    return len(_BG_COLOR_RE.findall(frame))


def _count_fg_codes(frame: str) -> int:
    return len(_FG_COLOR_RE.findall(frame))


def _all_frames(gen) -> list:
    return list(gen)


# ---------------------------------------------------------------------------
# Basic structure
# ---------------------------------------------------------------------------

class TestPlasmaBloomBasic:
    def test_returns_iterator(self):
        gen = plasma_bloom("HI", n_frames=4, loop=False)
        import collections.abc
        assert isinstance(gen, collections.abc.Iterator)

    def test_frame_count_no_loop(self):
        frames = _all_frames(plasma_bloom("HI", n_frames=6, loop=False))
        assert len(frames) == 6

    def test_frame_count_with_loop(self):
        frames = _all_frames(plasma_bloom("HI", n_frames=8, loop=True))
        assert len(frames) == 16  # forward + reverse

    def test_frames_are_strings(self):
        frames = _all_frames(plasma_bloom("HI", n_frames=4, loop=False))
        for f in frames:
            assert isinstance(f, str)

    def test_frames_non_empty(self):
        frames = _all_frames(plasma_bloom("HI", n_frames=4, loop=False))
        for f in frames:
            assert len(f.strip()) > 0

    def test_frames_are_multiline(self):
        frames = _all_frames(plasma_bloom("HI", n_frames=4, loop=False))
        for f in frames:
            assert "\n" in f

    def test_default_n_frames_loop(self):
        # Default is 36 frames → 72 total with loop
        frames = _all_frames(plasma_bloom("HI"))
        assert len(frames) == 72


# ---------------------------------------------------------------------------
# Chromatic bloom: background ANSI codes
# ---------------------------------------------------------------------------

class TestChromatiBloom:
    def test_background_codes_present(self):
        """Bloom cells carry background ANSI codes \033[48;2;...m"""
        frames = _all_frames(plasma_bloom("HI", n_frames=4, radius=3, loop=False))
        for frame in frames:
            bg_count = _count_bg_codes(frame)
            assert bg_count > 0, f"No bloom background codes found in frame"

    def test_foreground_codes_present(self):
        """Ink cells carry 24-bit foreground color codes."""
        frames = _all_frames(plasma_bloom("HI", n_frames=4, loop=False))
        for frame in frames:
            fg_count = _count_fg_codes(frame)
            assert fg_count > 0, f"No foreground color codes found in frame"

    def test_chromatic_bloom_colors_vary(self):
        """Different frames should produce different bloom hues (mean plasma shifts)."""
        frames = _all_frames(plasma_bloom("HI", n_frames=12, radius=4, loop=False))
        # Extract unique bloom RGB tuples across frames
        all_bloom_rgbs = set()
        for frame in frames:
            for r, g, b in _BG_COLOR_RE.findall(frame):
                all_bloom_rgbs.add((r, g, b))
        # Should have multiple distinct bloom colors across the plasma cycle
        assert len(all_bloom_rgbs) >= 3, (
            f"Expected ≥3 distinct bloom colors across {len(frames)} frames, "
            f"got {len(all_bloom_rgbs)}: {all_bloom_rgbs}"
        )

    def test_bloom_radius_affects_cell_count(self):
        """Larger radius → more bloom background cells per frame."""
        frames_small = _all_frames(plasma_bloom("HI", n_frames=4, radius=1, loop=False))
        frames_large = _all_frames(plasma_bloom("HI", n_frames=4, radius=5, loop=False))
        small_total = sum(_count_bg_codes(f) for f in frames_small)
        large_total = sum(_count_bg_codes(f) for f in frames_large)
        assert large_total > small_total

    def test_radius_zero_no_bloom(self):
        """radius=0 → no bloom background codes."""
        frames = _all_frames(plasma_bloom("HI", n_frames=4, radius=0, loop=False))
        for frame in frames:
            assert _count_bg_codes(frame) == 0


# ---------------------------------------------------------------------------
# Spectrum interpolation (bloom color in expected hue range)
# ---------------------------------------------------------------------------

class TestSpectrumInterpolation:
    def test_bloom_color_components_in_range(self):
        """All bloom RGB components should be valid 0–255."""
        frames = _all_frames(plasma_bloom("HI", n_frames=8, radius=3, loop=False))
        for frame in frames:
            for r, g, b in _BG_COLOR_RE.findall(frame):
                assert 0 <= int(r) <= 255
                assert 0 <= int(g) <= 255
                assert 0 <= int(b) <= 255

    def test_bloom_color_nonzero(self):
        """Bloom cells should not be pure black (all zeros)."""
        frames = _all_frames(plasma_bloom("HI", n_frames=4, radius=3, loop=False))
        for frame in frames:
            for r, g, b in _BG_COLOR_RE.findall(frame):
                assert (int(r), int(g), int(b)) != (0, 0, 0)


# ---------------------------------------------------------------------------
# Presets and palettes
# ---------------------------------------------------------------------------

class TestPresetsAndPalettes:
    @pytest.mark.parametrize("preset", ["default", "tight", "slow", "diagonal"])
    def test_plasma_presets(self, preset):
        frames = _all_frames(plasma_bloom("HI", n_frames=4, preset=preset, loop=False))
        assert len(frames) == 4
        for f in frames:
            assert len(f.strip()) > 0

    @pytest.mark.parametrize("palette", ["spectral", "lava", "fire", "bio"])
    def test_palette_propagation(self, palette):
        frames = _all_frames(plasma_bloom("HI", n_frames=4, palette_name=palette, loop=False))
        assert len(frames) == 4
        # Foreground colors should reflect the palette — just check they're present
        for f in frames:
            assert _count_fg_codes(f) > 0

    def test_spectral_palette_produces_varied_fg_colors(self):
        """Spectral palette → multiple distinct foreground RGB values."""
        frames = _all_frames(plasma_bloom("HI", n_frames=4, palette_name="spectral", loop=False))
        all_fg = set()
        for f in frames:
            for r, g, b in _FG_COLOR_RE.findall(f):
                all_fg.add((r, g, b))
        assert len(all_fg) >= 3


# ---------------------------------------------------------------------------
# Font parameter
# ---------------------------------------------------------------------------

class TestFont:
    def test_block_font(self):
        frames = _all_frames(plasma_bloom("HI", font="block", n_frames=4, loop=False))
        assert len(frames) == 4

    def test_slim_font(self):
        frames = _all_frames(plasma_bloom("HI", font="slim", n_frames=4, loop=False))
        assert len(frames) == 4


# ---------------------------------------------------------------------------
# Text input variations
# ---------------------------------------------------------------------------

class TestTextInput:
    def test_single_char(self):
        frames = _all_frames(plasma_bloom("A", n_frames=4, loop=False))
        assert all(len(f.strip()) > 0 for f in frames)

    def test_lowercase_text(self):
        """Text is uppercased internally."""
        frames = _all_frames(plasma_bloom("hello", n_frames=4, loop=False))
        assert all(len(f.strip()) > 0 for f in frames)

    def test_longer_text(self):
        frames = _all_frames(plasma_bloom("JUST DO IT", n_frames=4, loop=False))
        assert all(len(f.strip()) > 0 for f in frames)

    def test_multiword_text_wider_frames(self):
        """'JUST DO IT' renders wider than 'HI' so rows should be longer."""
        frames_wide = _all_frames(plasma_bloom("JUST DO IT", n_frames=4, loop=False))
        frames_narrow = _all_frames(plasma_bloom("HI", n_frames=4, loop=False))
        # First frame: "JUST DO IT" should have more visible chars
        wide_vis = len(_ANSI_RE.sub("", frames_wide[0]))
        narrow_vis = len(_ANSI_RE.sub("", frames_narrow[0]))
        assert wide_vis > narrow_vis


# ---------------------------------------------------------------------------
# Loop symmetry
# ---------------------------------------------------------------------------

class TestLoopSymmetry:
    def test_loop_first_half_matches_forward(self):
        """With loop=True, first n_frames frames match loop=False frames."""
        frames_loop = _all_frames(plasma_bloom("HI", n_frames=6, loop=True))
        frames_noloop = _all_frames(plasma_bloom("HI", n_frames=6, loop=False))
        for i, (fl, fn) in enumerate(zip(frames_loop[:6], frames_noloop)):
            assert fl == fn, f"Frame {i} mismatch between loop and no-loop"

    def test_loop_second_half_is_reversed(self):
        """Second half of looped frames should match reverse of first half."""
        frames_loop = _all_frames(plasma_bloom("HI", n_frames=6, loop=True))
        forward = frames_loop[:6]
        backward = frames_loop[6:]
        assert backward == list(reversed(forward))


# ---------------------------------------------------------------------------
# Falloff
# ---------------------------------------------------------------------------

class TestFalloff:
    def test_high_falloff_more_bloom(self):
        """Higher falloff → brighter bloom at distance → more cells above noise floor."""
        frames_hi = _all_frames(plasma_bloom("HI", n_frames=4, radius=4, falloff=0.95, loop=False))
        frames_lo = _all_frames(plasma_bloom("HI", n_frames=4, radius=4, falloff=0.5, loop=False))
        hi_total = sum(_count_bg_codes(f) for f in frames_hi)
        lo_total = sum(_count_bg_codes(f) for f in frames_lo)
        # high falloff = slower decay = more cells above black threshold
        assert hi_total >= lo_total
