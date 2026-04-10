"""Tests for flame_gradient_color (A08c) and flame_bloom (X_FLAME_BLOOM) presets."""
import re
import pytest
from justdoit.animate.presets import flame_gradient_color, flame_bloom

# ANSI escape pattern
_ANSI_RE = re.compile(r"\033\[[\d;]*m")

TEXT = "HI"  # short text for fast tests


# ---------------------------------------------------------------------------
# flame_gradient_color (A08c)
# ---------------------------------------------------------------------------
class TestFlameGradientColor:
    def test_non_empty_output(self):
        frames = list(flame_gradient_color(TEXT, n_frames=3, loop=False))
        assert len(frames) > 0
        assert all(len(f) > 0 for f in frames)

    def test_contains_newlines(self):
        frames = list(flame_gradient_color(TEXT, n_frames=3, loop=False))
        for frame in frames:
            assert "\n" in frame, "frame should be multi-line"

    def test_contains_ansi_codes(self):
        frames = list(flame_gradient_color(TEXT, n_frames=3, loop=False))
        for frame in frames:
            assert _ANSI_RE.search(frame), "frame should contain ANSI escape codes"

    def test_correct_frame_count_no_loop(self):
        frames = list(flame_gradient_color(TEXT, n_frames=5, loop=False))
        assert len(frames) == 5

    def test_correct_frame_count_loop_doubles(self):
        frames = list(flame_gradient_color(TEXT, n_frames=5, loop=True))
        assert len(frames) == 10

    def test_different_frames(self):
        frames = list(flame_gradient_color(TEXT, n_frames=6, loop=False))
        # Not all frames should be identical (flame is random per seed)
        unique = set(frames)
        assert len(unique) > 1, "frames should not all be identical"

    def test_24bit_foreground_color(self):
        """Should contain 24-bit foreground color codes: ESC[38;2;..."""
        frames = list(flame_gradient_color(TEXT, n_frames=3, loop=False))
        found = any(re.search(r"\033\[38;2;", f) for f in frames)
        assert found, "should contain 24-bit foreground color ANSI codes"

    def test_returns_iterator_lazily(self):
        """Generator should not error when iterated."""
        gen = flame_gradient_color(TEXT, n_frames=4, loop=False)
        first = next(gen)
        assert len(first) > 0

    @pytest.mark.parametrize("preset", ["default", "hot", "cool", "embers"])
    def test_valid_presets(self, preset):
        frames = list(flame_gradient_color(TEXT, n_frames=2, preset=preset, loop=False))
        assert len(frames) == 2


# ---------------------------------------------------------------------------
# flame_bloom (X_FLAME_BLOOM)
# ---------------------------------------------------------------------------
class TestFlameBloom:
    def test_non_empty_output(self):
        frames = list(flame_bloom(TEXT, n_frames=3, loop=False))
        assert len(frames) > 0
        assert all(len(f) > 0 for f in frames)

    def test_contains_newlines(self):
        frames = list(flame_bloom(TEXT, n_frames=3, loop=False))
        for frame in frames:
            assert "\n" in frame, "frame should be multi-line"

    def test_contains_ansi_codes(self):
        frames = list(flame_bloom(TEXT, n_frames=3, loop=False))
        for frame in frames:
            assert _ANSI_RE.search(frame), "frame should contain ANSI escape codes"

    def test_correct_frame_count_no_loop(self):
        frames = list(flame_bloom(TEXT, n_frames=5, loop=False))
        assert len(frames) == 5

    def test_correct_frame_count_loop_doubles(self):
        frames = list(flame_bloom(TEXT, n_frames=5, loop=True))
        assert len(frames) == 10

    def test_different_frames(self):
        frames = list(flame_bloom(TEXT, n_frames=6, loop=False))
        unique = set(frames)
        assert len(unique) > 1, "frames should not all be identical"

    def test_bloom_applies_background_ansi(self):
        """C12 bloom should produce background color codes: ESC[48;2;..."""
        frames = list(flame_bloom(TEXT, n_frames=4, loop=False))
        found = any(re.search(r"\033\[48;2;", f) for f in frames)
        assert found, "bloom should produce background ANSI codes \\033[48;2;"

    def test_24bit_foreground_color(self):
        """Should contain 24-bit foreground color codes from fire palette."""
        frames = list(flame_bloom(TEXT, n_frames=3, loop=False))
        found = any(re.search(r"\033\[38;2;", f) for f in frames)
        assert found, "should contain 24-bit foreground color ANSI codes"

    def test_returns_iterator_lazily(self):
        gen = flame_bloom(TEXT, n_frames=4, loop=False)
        first = next(gen)
        assert len(first) > 0

    @pytest.mark.parametrize("preset", ["default", "hot", "cool", "embers"])
    def test_valid_presets(self, preset):
        frames = list(flame_bloom(TEXT, n_frames=2, preset=preset, loop=False))
        assert len(frames) == 2

    def test_tone_curve_blown_out_applied(self):
        """blown_out tone curve should produce some solid @ chars (max density)."""
        frames = list(flame_bloom(TEXT, n_frames=8, preset="hot", loop=False))
        combined = "".join(re.sub(_ANSI_RE, "", f) for f in frames)
        # With blown_out, many cells should map to "@" (hottest char)
        assert "@" in combined, "blown_out core should produce '@' characters"

    def test_full_text_flame_bloom(self):
        """Integration: full phrase should work without error."""
        frames = list(flame_bloom("JUST DO IT", n_frames=4, loop=False))
        assert len(frames) == 4
        for frame in frames:
            assert len(frame) > 0
            assert "\n" in frame
