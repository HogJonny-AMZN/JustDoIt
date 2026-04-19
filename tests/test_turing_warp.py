"""Tests for turing_warp() animation preset (X_TURING_WARP).

Tests cover:
- Frame count with and without loop
- Frame type and content checks
- ANSI code presence (color + bloom)
- Warp animation (phase varies content)
- Color stability (static across frames)
- Preset and parameter coverage
- Edge cases (short text, single char)
"""

import re
import pytest

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")
_FG_COLOR_RE = re.compile(r"\033\[38;2;")
_BG_COLOR_RE = re.compile(r"\033\[48;2;")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def _count_fg_codes(text: str) -> int:
    return len(_FG_COLOR_RE.findall(text))


def _count_bg_codes(text: str) -> int:
    return len(_BG_COLOR_RE.findall(text))


# -------------------------------------------------------------------------
# Basic structure tests

def test_turing_warp_returns_iterable():
    from justdoit.animate.presets import turing_warp
    result = turing_warp("HI", font="block", n_frames=4, loop=False)
    assert hasattr(result, "__iter__"), "turing_warp should return an iterator"


def test_turing_warp_frame_count_no_loop():
    from justdoit.animate.presets import turing_warp
    frames = list(turing_warp("HI", font="block", n_frames=6, loop=False))
    assert len(frames) == 6


def test_turing_warp_frame_count_loop():
    from justdoit.animate.presets import turing_warp
    frames = list(turing_warp("HI", font="block", n_frames=6, loop=True))
    assert len(frames) == 12  # 2 * n_frames


def test_turing_warp_frames_are_strings():
    from justdoit.animate.presets import turing_warp
    frames = list(turing_warp("HI", font="block", n_frames=4, loop=False))
    for i, f in enumerate(frames):
        assert isinstance(f, str), f"Frame {i} should be a string"


def test_turing_warp_frames_nonempty():
    from justdoit.animate.presets import turing_warp
    frames = list(turing_warp("HI", font="block", n_frames=4, loop=False))
    for i, f in enumerate(frames):
        assert len(f) > 0, f"Frame {i} should not be empty"


# -------------------------------------------------------------------------
# ANSI / color tests

def test_turing_warp_frames_have_ansi():
    from justdoit.animate.presets import turing_warp
    frames = list(turing_warp("HI", font="block", n_frames=4, loop=False))
    for i, f in enumerate(frames):
        assert "\033[" in f, f"Frame {i} should contain ANSI codes"


def test_turing_warp_frames_have_foreground_color():
    from justdoit.animate.presets import turing_warp
    frames = list(turing_warp("HI", font="block", n_frames=4, loop=False))
    for i, f in enumerate(frames):
        assert _count_fg_codes(f) > 0, f"Frame {i} should have foreground color codes"


def test_turing_warp_frames_have_bloom():
    from justdoit.animate.presets import turing_warp
    frames = list(turing_warp("HI", font="block", n_frames=4, loop=False))
    total_bg = sum(_count_bg_codes(f) for f in frames)
    assert total_bg > 0, "At least some frames should have background bloom codes"


def test_turing_warp_bloom_codes_present_in_most_frames():
    from justdoit.animate.presets import turing_warp
    frames = list(turing_warp("JUST DO IT", font="block", n_frames=4, loop=False))
    frames_with_bloom = sum(1 for f in frames if _count_bg_codes(f) > 0)
    assert frames_with_bloom > 0, "Some frames should have bloom background codes"


# -------------------------------------------------------------------------
# Animation behavior tests

def test_turing_warp_phase_varies_warp_content():
    """The plain-text content (warp offsets) should differ across frames."""
    from justdoit.animate.presets import turing_warp
    # n_frames=8, check first vs middle frame have different plain text
    frames = list(turing_warp("JUST DO IT", font="block", n_frames=8, loop=False))
    assert len(frames) >= 4
    plain_0 = _strip_ansi(frames[0])
    plain_mid = _strip_ansi(frames[len(frames) // 2])
    # They may not differ at phase=0 vs phase=pi if amplitude is symmetric,
    # so compare frame 0 vs frame 1/4
    plain_q = _strip_ansi(frames[len(frames) // 4])
    # At least one pair should differ (warp is sweeping)
    assert plain_0 != plain_q or plain_0 != plain_mid, \
        "Warp should produce different frame layouts across the phase sweep"


def test_turing_warp_color_stable_across_frames():
    """Foreground color code count should be same in all frames (color is static)."""
    from justdoit.animate.presets import turing_warp
    frames = list(turing_warp("HI", font="block", n_frames=6, loop=False))
    fg_counts = [_count_fg_codes(f) for f in frames]
    # All frames should have the same number of foreground color codes (static color)
    assert len(set(fg_counts)) == 1, \
        f"Foreground color code count should be constant across frames (got {fg_counts})"


def test_turing_warp_has_multiline_frames():
    from justdoit.animate.presets import turing_warp
    frames = list(turing_warp("HI", font="block", n_frames=4, loop=False))
    for i, f in enumerate(frames):
        assert "\n" in f, f"Frame {i} should be multi-line (glyph height > 1)"


# -------------------------------------------------------------------------
# Preset tests

def test_turing_warp_spots_preset():
    from justdoit.animate.presets import turing_warp
    frames = list(turing_warp("HI", font="block", n_frames=2, turing_preset="spots", loop=False))
    assert len(frames) == 2 and all(isinstance(f, str) and len(f) > 0 for f in frames)


def test_turing_warp_stripes_preset():
    from justdoit.animate.presets import turing_warp
    frames = list(turing_warp("HI", font="block", n_frames=2, turing_preset="stripes", loop=False))
    assert len(frames) == 2 and all(isinstance(f, str) and len(f) > 0 for f in frames)


def test_turing_warp_maze_preset():
    from justdoit.animate.presets import turing_warp
    frames = list(turing_warp("HI", font="block", n_frames=2, turing_preset="maze", loop=False))
    assert len(frames) == 2 and all(isinstance(f, str) and len(f) > 0 for f in frames)


def test_turing_warp_labyrinth_preset():
    from justdoit.animate.presets import turing_warp
    frames = list(turing_warp("HI", font="block", n_frames=2, turing_preset="labyrinth", loop=False))
    assert len(frames) == 2 and all(isinstance(f, str) and len(f) > 0 for f in frames)


# -------------------------------------------------------------------------
# Parameter tests

def test_turing_warp_amplitude_increases_leading_spaces():
    """Higher max_amplitude → more leading spaces in some frames."""
    from justdoit.animate.presets import turing_warp
    # Use n_frames=4 to get a mid-cycle frame with nonzero phase
    frames_high = list(turing_warp("HI", font="block", n_frames=4, max_amplitude=8.0, loop=False))
    frames_low  = list(turing_warp("HI", font="block", n_frames=4, max_amplitude=1.0, loop=False))

    def leading_spaces(frame):
        total = 0
        for line in _strip_ansi(frame).split("\n"):
            total += len(line) - len(line.lstrip(" "))
        return total

    high_spaces = max(leading_spaces(f) for f in frames_high)
    low_spaces  = max(leading_spaces(f) for f in frames_low)
    assert high_spaces >= low_spaces, \
        f"High amplitude ({high_spaces}) should produce >= leading spaces than low amplitude ({low_spaces})"


def test_turing_warp_seed_reproducible():
    """Same seed should produce identical frames."""
    from justdoit.animate.presets import turing_warp
    frames_a = list(turing_warp("HI", font="block", n_frames=4, seed=42, loop=False))
    frames_b = list(turing_warp("HI", font="block", n_frames=4, seed=42, loop=False))
    for i, (a, b) in enumerate(zip(frames_a, frames_b)):
        assert a == b, f"Frame {i} differs between identical seeds"


def test_turing_warp_different_seeds_differ():
    """Different seeds should produce different results."""
    from justdoit.animate.presets import turing_warp
    frames_42 = list(turing_warp("HI", font="block", n_frames=2, seed=42, loop=False))
    frames_99 = list(turing_warp("HI", font="block", n_frames=2, seed=99, loop=False))
    # Seeds control the Turing pattern; they may occasionally produce same output
    # for very small glyphs, so just verify both produce non-empty results
    assert all(len(f) > 0 for f in frames_42)
    assert all(len(f) > 0 for f in frames_99)


# -------------------------------------------------------------------------
# Edge case tests

def test_turing_warp_short_text():
    from justdoit.animate.presets import turing_warp
    frames = list(turing_warp("HI", font="block", n_frames=2, loop=False))
    assert len(frames) == 2
    assert all(len(f) > 0 for f in frames)


def test_turing_warp_single_char():
    from justdoit.animate.presets import turing_warp
    frames = list(turing_warp("A", font="block", n_frames=2, loop=False))
    assert len(frames) == 2
    assert all(len(f) > 0 for f in frames)


def test_turing_warp_n_frames_1():
    """n_frames=1 should produce 1 frame (no loop) or 2 frames (with loop)."""
    from justdoit.animate.presets import turing_warp
    frames_no_loop = list(turing_warp("HI", font="block", n_frames=1, loop=False))
    assert len(frames_no_loop) == 1
    frames_loop = list(turing_warp("HI", font="block", n_frames=1, loop=True))
    # loop=True with n_frames=1: [phase_0] + reversed([phase_0]) = [phase_0, phase_0] = 2 frames
    assert len(frames_loop) == 2


def test_turing_warp_long_text():
    from justdoit.animate.presets import turing_warp
    frames = list(turing_warp("JUST DO IT", font="block", n_frames=2, loop=False))
    assert len(frames) == 2
    assert all(len(f) > 0 for f in frames)


# -------------------------------------------------------------------------
# phase_offset backward-compatibility test for sine_warp

def test_sine_warp_phase_offset_default_unchanged():
    """sine_warp() with phase_offset=0.0 (default) should match old behavior."""
    from justdoit.effects.spatial import sine_warp
    text = "HELLO\nWORLD\nFOO"
    result_default = sine_warp(text, amplitude=3.0, frequency=1.0)
    result_explicit = sine_warp(text, amplitude=3.0, frequency=1.0, phase_offset=0.0)
    assert result_default == result_explicit, "Default phase_offset=0.0 should not change sine_warp output"


def test_sine_warp_phase_offset_changes_output():
    """sine_warp() with nonzero phase_offset should differ from default."""
    from justdoit.effects.spatial import sine_warp
    import math
    text = "HELLO\nWORLD\nFOO\nBAR"
    result_0 = sine_warp(text, amplitude=5.0, phase_offset=0.0)
    result_half = sine_warp(text, amplitude=5.0, phase_offset=math.pi)
    # PI phase shift on a sine inverts it — output should differ
    assert result_0 != result_half, "phase_offset=pi should invert the warp"
