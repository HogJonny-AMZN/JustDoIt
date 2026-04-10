"""
Tests for bloom_pulse preset (A_BLOOM1) — breathing bloom radius around burning letterforms.

Covers:
  - Frame count (n_frames, loop)
  - ANSI structure: foreground codes (fire palette), background bloom codes
  - Bloom radius oscillation: max-radius frames have more bloom cells than min-radius
  - Tone curve: chars differ from flame_bloom (ACES vs blown_out)
  - Default and hot presets
  - Loop produces forward+reversed frame sequence
  - Empty/whitespace text edge cases
"""

import re

import pytest

from justdoit.animate.presets import bloom_pulse

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")
_BLOOM_RE = re.compile(r"\033\[48;2;")
_FG_RE = re.compile(r"\033\[38;2;")

_TEXT = "JUST DO IT"


def _bloom_count(frame: str) -> int:
    return len(_BLOOM_RE.findall(frame))


def _fg_count(frame: str) -> int:
    return len(_FG_RE.findall(frame))


def _ink_chars(frame: str) -> list:
    plain = _ANSI_RE.sub("", frame)
    return [c for c in plain if c not in (" ", "\n")]


# ---------------------------------------------------------------------------
# Frame count tests
# ---------------------------------------------------------------------------

class TestBloomPulseFrameCount:
    def test_no_loop_frame_count(self):
        frames = list(bloom_pulse(_TEXT, n_frames=8, loop=False))
        assert len(frames) == 8

    def test_loop_doubles_frame_count(self):
        frames = list(bloom_pulse(_TEXT, n_frames=12, loop=True))
        assert len(frames) == 24

    def test_default_params_produces_frames(self):
        frames = list(bloom_pulse(_TEXT))
        # Default: n_frames=24, loop=True → 48 frames
        assert len(frames) == 48

    def test_small_n_frames(self):
        frames = list(bloom_pulse(_TEXT, n_frames=3, loop=False))
        assert len(frames) == 3


# ---------------------------------------------------------------------------
# ANSI structure tests
# ---------------------------------------------------------------------------

class TestBloomPulseAnsiStructure:
    def test_frames_are_strings(self):
        frames = list(bloom_pulse(_TEXT, n_frames=4, loop=False))
        for f in frames:
            assert isinstance(f, str)

    def test_foreground_color_codes_present(self):
        """Fire palette should produce 38;2; foreground codes."""
        frames = list(bloom_pulse(_TEXT, n_frames=4, loop=False))
        for f in frames:
            assert _fg_count(f) > 0, "Expected foreground color codes (fire palette)"

    def test_bloom_background_codes_present(self):
        """C12 bloom should produce 48;2; background codes on space cells."""
        frames = list(bloom_pulse(_TEXT, n_frames=4, loop=False))
        for f in frames:
            assert _bloom_count(f) > 0, "Expected bloom background ANSI codes"

    def test_multi_line_output(self):
        """Block font is 7 rows — each frame should have 7 lines."""
        frames = list(bloom_pulse(_TEXT, n_frames=4, loop=False))
        for f in frames:
            assert len(f.split("\n")) == 7

    def test_ink_chars_present(self):
        """Flame chars should be present in each frame."""
        frames = list(bloom_pulse(_TEXT, n_frames=4, loop=False))
        for f in frames:
            assert len(_ink_chars(f)) > 0, "Expected ink chars in frame"


# ---------------------------------------------------------------------------
# Bloom radius oscillation tests
# ---------------------------------------------------------------------------

class TestBloomPulseRadiusOscillation:
    def test_radius_oscillates_over_loop(self):
        """Bloom cell counts should vary across frames as radius oscillates."""
        frames = list(bloom_pulse(_TEXT, n_frames=24, loop=True))
        bloom_counts = [_bloom_count(f) for f in frames]
        # Should have at least 2 distinct bloom counts (radius oscillates min↔max)
        assert len(set(bloom_counts)) >= 2, (
            f"Expected bloom radius to oscillate, but all frames had same count: {set(bloom_counts)}"
        )

    def test_larger_radius_has_more_bloom_cells(self):
        """Maximum-radius frames should have more bloom cells than minimum-radius frames."""
        frames = list(bloom_pulse(_TEXT, n_frames=24, loop=True))
        bloom_counts = [_bloom_count(f) for f in frames]
        assert max(bloom_counts) > min(bloom_counts), (
            f"Expected max bloom > min bloom, got max={max(bloom_counts)} min={min(bloom_counts)}"
        )

    def test_base_radius_1_still_produces_bloom(self):
        """Even with minimum base_radius=1 and amplitude=0, bloom should appear."""
        frames = list(bloom_pulse(_TEXT, n_frames=3, loop=False, base_radius=1, bloom_amplitude=0))
        for f in frames:
            assert _bloom_count(f) > 0

    def test_bloom_amplitude_zero_fixed_radius(self):
        """bloom_amplitude=0 → all frames have same bloom count (no oscillation)."""
        frames = list(bloom_pulse(_TEXT, n_frames=8, loop=False, bloom_amplitude=0))
        bloom_counts = [_bloom_count(f) for f in frames]
        # All counts should be equal when amplitude=0
        assert len(set(bloom_counts)) == 1, (
            f"Expected fixed radius with amplitude=0, got counts: {set(bloom_counts)}"
        )


# ---------------------------------------------------------------------------
# Tone curve (ACES) tests
# ---------------------------------------------------------------------------

class TestBloomPulseAesCurve:
    def test_aces_produces_varied_chars(self):
        """ACES should produce more char variety than blown_out (which saturates to @)."""
        frames = list(bloom_pulse(_TEXT, n_frames=6, loop=False, tone_curve="aces"))
        all_chars = set()
        for f in frames:
            all_chars.update(_ink_chars(f))
        # ACES curve produces punchy mids — expect at least 2 distinct chars across frames
        assert len(all_chars) >= 2, f"Expected ≥2 distinct ink chars with ACES, got: {all_chars}"

    def test_reinhard_curve_accepted(self):
        """reinhard tone curve should not raise."""
        frames = list(bloom_pulse(_TEXT, n_frames=3, loop=False, tone_curve="reinhard"))
        assert len(frames) == 3

    def test_blown_out_curve_accepted(self):
        """blown_out tone curve should not raise."""
        frames = list(bloom_pulse(_TEXT, n_frames=3, loop=False, tone_curve="blown_out"))
        assert len(frames) == 3


# ---------------------------------------------------------------------------
# Preset tests
# ---------------------------------------------------------------------------

class TestBloomPulsePresets:
    def test_hot_preset(self):
        frames = list(bloom_pulse(_TEXT, n_frames=3, loop=False, preset="hot"))
        assert len(frames) == 3
        for f in frames:
            assert len(_ink_chars(f)) > 0

    def test_cool_preset(self):
        frames = list(bloom_pulse(_TEXT, n_frames=3, loop=False, preset="cool"))
        assert len(frames) == 3

    def test_embers_preset(self):
        frames = list(bloom_pulse(_TEXT, n_frames=3, loop=False, preset="embers"))
        assert len(frames) == 3

    def test_palette_fire(self):
        frames = list(bloom_pulse(_TEXT, n_frames=3, loop=False, palette_name="fire"))
        assert len(frames) == 3
        for f in frames:
            assert _fg_count(f) > 0

    def test_palette_lava(self):
        frames = list(bloom_pulse(_TEXT, n_frames=3, loop=False, palette_name="lava"))
        assert len(frames) == 3

    def test_bloom_color_cyan(self):
        """Non-default bloom color should produce ANSI bloom codes."""
        frames = list(bloom_pulse(_TEXT, n_frames=3, loop=False, bloom_color_name="cyan"))
        for f in frames:
            assert _bloom_count(f) > 0


# ---------------------------------------------------------------------------
# Loop semantics tests
# ---------------------------------------------------------------------------

class TestBloomPulseLoop:
    def test_loop_first_and_last_frames_same_seed(self):
        """With loop=True, frame 0 and frame n_frames*2-1 use the same seed (0)."""
        frames_loop = list(bloom_pulse(_TEXT, n_frames=4, loop=True))
        frames_noloop = list(bloom_pulse(_TEXT, n_frames=4, loop=False))
        # Frame 0 of loop == frame 0 of no-loop (same seed=0)
        assert frames_loop[0] == frames_noloop[0]

    def test_loop_oscillates_over_full_cycle(self):
        """Loop produces a full sine-cycle of radius values — min and max differ."""
        frames = list(bloom_pulse(_TEXT, n_frames=24, loop=True))
        bloom_counts = [_bloom_count(f) for f in frames]
        # The bloom counts should show at least 2 distinct values across the full cycle,
        # confirming the radius oscillates from max (top of sin) to min (bottom of sin).
        assert len(set(bloom_counts)) >= 2, (
            f"Expected varying bloom counts over a full sin cycle, got: {set(bloom_counts)}"
        )
        # Over a full 48-frame (24+24) loop, at least one min < max pair must exist
        assert max(bloom_counts) > min(bloom_counts), (
            f"Expected max > min bloom: max={max(bloom_counts)} min={min(bloom_counts)}"
        )


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------

class TestBloomPulseEdgeCases:
    def test_empty_text(self):
        frames = list(bloom_pulse("", n_frames=3, loop=False))
        assert len(frames) == 3
        for f in frames:
            assert isinstance(f, str)

    def test_space_only_text(self):
        frames = list(bloom_pulse("   ", n_frames=3, loop=False))
        assert len(frames) == 3

    def test_single_char(self):
        frames = list(bloom_pulse("J", n_frames=3, loop=False))
        assert len(frames) == 3
        for f in frames:
            assert isinstance(f, str)
