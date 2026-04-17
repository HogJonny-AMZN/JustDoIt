"""Tests for plasma_warp() preset (X_PLASMA_WARP) and sine_warp amplitude_map extension.

Tests cover:
- sine_warp amplitude_map extension (backward compat + per-row override)
- plasma_warp() smoke tests and structural properties
- Per-row amplitude variation (different rows warp differently)
- C11 colorization present in output
- C12 bloom present in output
- Seamless forward-back loop
- Empty and edge-case inputs
"""

import re
import pytest

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")
_BG_ANSI_RE = re.compile(r"\033\[48;2;(\d+);(\d+);(\d+)m")
_FG_ANSI_RE = re.compile(r"\033\[38;2;(\d+);(\d+);(\d+)m")


def _strip_ansi(s: str) -> str:
    return _ANSI_RE.sub("", s)


# ---------------------------------------------------------------------------
# sine_warp amplitude_map extension
# ---------------------------------------------------------------------------

class TestSineWarpAmplitudeMap:
    """Tests for the new amplitude_map parameter on sine_warp()."""

    def test_backward_compat_no_amplitude_map(self):
        """Calling sine_warp without amplitude_map must produce same result as before."""
        from justdoit.effects.spatial import sine_warp
        text = "HELLO\nWORLD\nFOO\nBAR\nBAZ\nA\nB"
        result1 = sine_warp(text, amplitude=3.0, frequency=1.0)
        result2 = sine_warp(text, amplitude=3.0, frequency=1.0, amplitude_map=None)
        assert result1 == result2

    def test_amplitude_map_applied_per_row(self):
        """With amplitude_map=[0,0,...], all rows should be unshifted."""
        from justdoit.effects.spatial import sine_warp
        text = "\n".join(["HELLO"] * 7)
        lines = text.split("\n")
        zero_map = [0.0] * len(lines)
        result = sine_warp(text, amplitude=5.0, frequency=1.0, amplitude_map=zero_map)
        for line in result.split("\n"):
            assert not line.startswith(" "), "With amplitude_map=0, no row should be padded"

    def test_amplitude_map_partial_override(self):
        """Rows beyond amplitude_map length fall back to global amplitude."""
        from justdoit.effects.spatial import sine_warp
        # 7 rows, map covers only 3 rows with 0.0 → first 3 rows unshifted
        text = "\n".join(["HELLO"] * 7)
        partial_map = [0.0, 0.0, 0.0]  # only covers rows 0-2
        result_partial = sine_warp(text, amplitude=4.0, frequency=1.0, amplitude_map=partial_map)
        result_full = sine_warp(text, amplitude=4.0, frequency=1.0, amplitude_map=None)
        rows_partial = result_partial.split("\n")
        rows_full = result_full.split("\n")
        # Rows 3-6 (beyond map) should match global amplitude behavior
        assert rows_partial[3:] == rows_full[3:]

    def test_amplitude_map_nonzero_different_from_uniform(self):
        """Non-uniform amplitude map should produce different output than uniform."""
        from justdoit.effects.spatial import sine_warp
        text = "\n".join(["HELLO"] * 7)
        varying_map = [1.0, 5.0, 1.0, 5.0, 1.0, 5.0, 1.0]
        result_varying = sine_warp(text, amplitude=3.0, frequency=1.0, amplitude_map=varying_map)
        result_uniform = sine_warp(text, amplitude=3.0, frequency=1.0)
        assert result_varying != result_uniform

    def test_amplitude_map_empty_text(self):
        """Empty text input should return empty string regardless of amplitude_map."""
        from justdoit.effects.spatial import sine_warp
        assert sine_warp("", amplitude=3.0, amplitude_map=[1.0, 2.0]) == ""

    def test_amplitude_map_preserves_content(self):
        """Characters must be preserved (possibly shifted) after amplitude_map warp."""
        from justdoit.effects.spatial import sine_warp
        text = "\n".join(["ABCDE"] * 7)
        amp_map = [float(i) for i in range(7)]
        result = sine_warp(text, amplitude=3.0, frequency=1.0, amplitude_map=amp_map)
        for line in result.split("\n"):
            stripped = line.strip()
            assert "ABCDE" in stripped or stripped == "", f"Content missing from row: {line!r}"


# ---------------------------------------------------------------------------
# plasma_warp() smoke tests
# ---------------------------------------------------------------------------

class TestPlasmaWarpBasic:
    """Basic structural and property tests for plasma_warp()."""

    def test_yields_frames(self):
        from justdoit.animate.presets import plasma_warp
        frames = list(plasma_warp("HI", n_frames=4, loop=False))
        assert len(frames) == 4

    def test_frame_count_loop_true(self):
        from justdoit.animate.presets import plasma_warp
        frames = list(plasma_warp("HI", n_frames=4, loop=True))
        assert len(frames) == 8  # forward + reverse

    def test_frame_count_loop_false(self):
        from justdoit.animate.presets import plasma_warp
        frames = list(plasma_warp("HI", n_frames=4, loop=False))
        assert len(frames) == 4

    def test_all_frames_non_empty(self):
        from justdoit.animate.presets import plasma_warp
        frames = list(plasma_warp("HI", n_frames=4, loop=False))
        assert all(f for f in frames)

    def test_frames_are_multiline(self):
        from justdoit.animate.presets import plasma_warp
        frames = list(plasma_warp("HI", n_frames=4, loop=False))
        assert all("\n" in f for f in frames), "All frames must be multi-line"

    def test_ansi_color_codes_present(self):
        """Frames must contain 24-bit foreground color codes (C11 colorization)."""
        from justdoit.animate.presets import plasma_warp
        frames = list(plasma_warp("HI", n_frames=4, loop=False))
        for frame in frames:
            assert _FG_ANSI_RE.search(frame), "Frame should contain foreground color ANSI codes"

    def test_bloom_background_codes_present(self):
        """Frames must contain 24-bit background codes (C12 bloom)."""
        from justdoit.animate.presets import plasma_warp
        frames = list(plasma_warp("HI", n_frames=4, loop=False, bloom_radius=3))
        for frame in frames:
            assert _BG_ANSI_RE.search(frame), "Frame should contain background bloom ANSI codes"

    def test_consistent_row_count(self):
        """All frames should have the same number of rows."""
        from justdoit.animate.presets import plasma_warp
        frames = list(plasma_warp("HI", n_frames=4, loop=False))
        row_counts = [len(f.split("\n")) for f in frames]
        assert len(set(row_counts)) == 1, f"Row counts differ across frames: {row_counts}"

    def test_single_char_input(self):
        from justdoit.animate.presets import plasma_warp
        frames = list(plasma_warp("A", n_frames=4, loop=False))
        assert len(frames) == 4
        assert all(f for f in frames)

    def test_multiple_words(self):
        from justdoit.animate.presets import plasma_warp
        frames = list(plasma_warp("JUST DO IT", n_frames=4, loop=False))
        assert len(frames) == 4
        assert all(f for f in frames)


# ---------------------------------------------------------------------------
# plasma_warp() per-row amplitude variation
# ---------------------------------------------------------------------------

class TestPlasmaWarpAmplitudeVariation:
    """Verify that different rows warp differently (the core of the cross-breed)."""

    def test_rows_have_different_leading_spaces(self):
        """Different rows should have different amounts of leading whitespace."""
        from justdoit.animate.presets import plasma_warp
        # Use a frame well into the plasma cycle (not t=0 where field may be uniform)
        frames = list(plasma_warp("JUST DO IT", n_frames=8, loop=False))
        # Check that across all frames, at least one frame has rows with different indent
        found_varied = False
        for frame in frames:
            leading_spaces = []
            for line in frame.split("\n"):
                clean = _strip_ansi(line)
                leading = len(clean) - len(clean.lstrip(" "))
                leading_spaces.append(leading)
            if len(set(leading_spaces)) > 1:
                found_varied = True
                break
        assert found_varied, "At least one frame should have rows with differing leading indent"

    def test_frames_differ_from_each_other(self):
        """Consecutive frames should differ (plasma is evolving)."""
        from justdoit.animate.presets import plasma_warp
        frames = list(plasma_warp("JUST DO IT", n_frames=8, loop=False))
        plain_frames = [_strip_ansi(f) for f in frames]
        unique = set(plain_frames)
        assert len(unique) > 1, "Frames should not all be identical"


# ---------------------------------------------------------------------------
# plasma_warp() preset and palette options
# ---------------------------------------------------------------------------

class TestPlasmaWarpOptions:
    """Test different preset and palette combinations."""

    def test_plasma_preset_tight(self):
        from justdoit.animate.presets import plasma_warp
        frames = list(plasma_warp("HI", n_frames=4, loop=False, plasma_preset="tight"))
        assert len(frames) == 4
        assert all(f for f in frames)

    def test_plasma_preset_slow(self):
        from justdoit.animate.presets import plasma_warp
        frames = list(plasma_warp("HI", n_frames=4, loop=False, plasma_preset="slow"))
        assert len(frames) == 4
        assert all(f for f in frames)

    def test_palette_bio(self):
        from justdoit.animate.presets import plasma_warp
        frames = list(plasma_warp("HI", n_frames=4, loop=False, palette_name="bio"))
        assert len(frames) == 4

    def test_palette_fire(self):
        from justdoit.animate.presets import plasma_warp
        frames = list(plasma_warp("HI", n_frames=4, loop=False, palette_name="fire"))
        assert len(frames) == 4

    def test_bloom_color_magenta(self):
        from justdoit.animate.presets import plasma_warp
        frames = list(plasma_warp("HI", n_frames=4, loop=False, bloom_color_name="magenta"))
        assert len(frames) == 4

    def test_fill_wave(self):
        """Non-plasma fill (wave) should still work — amplitude map from plasma."""
        from justdoit.animate.presets import plasma_warp
        frames = list(plasma_warp("HI", n_frames=4, loop=False, fill="wave"))
        assert len(frames) == 4
        assert all(f for f in frames)

    def test_high_amplitude(self):
        from justdoit.animate.presets import plasma_warp
        frames = list(plasma_warp("HI", n_frames=4, loop=False, max_amplitude=12.0))
        assert all(f for f in frames)

    def test_zero_bloom_radius(self):
        """Zero bloom radius should still produce valid frames (no bloom cells)."""
        from justdoit.animate.presets import plasma_warp
        frames = list(plasma_warp("HI", n_frames=4, loop=False, bloom_radius=0))
        assert len(frames) == 4
        assert all(f for f in frames)


# ---------------------------------------------------------------------------
# plasma_warp() loop and frame continuity
# ---------------------------------------------------------------------------

class TestPlasmaWarpLoop:
    """Test loop semantics (forward + reverse for seamless loop)."""

    def test_loop_first_frame_equals_last_forward_frame(self):
        """With loop=True, frame 0 should equal frame n_frames-1 (reverse starts at n_frames-1)."""
        from justdoit.animate.presets import plasma_warp
        n = 8
        frames = list(plasma_warp("HI", n_frames=n, loop=True))
        # Frame n-1 is last of forward sweep; frame n is first of reverse (= n-1 again)
        assert frames[n - 1] == frames[n], "Reverse loop should mirror the forward sequence"

    def test_n_frames_1_loop_false(self):
        from justdoit.animate.presets import plasma_warp
        frames = list(plasma_warp("HI", n_frames=1, loop=False))
        assert len(frames) == 1

    def test_n_frames_1_loop_true(self):
        from justdoit.animate.presets import plasma_warp
        frames = list(plasma_warp("HI", n_frames=1, loop=True))
        # n_frames=1 + loop: 1 frame + reversed([frame_0]) = 2 frames
        assert len(frames) == 2
