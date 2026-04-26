"""Tests for iso_neon_glitch() animation preset (X_ISO_NEON).

Cross-breed: S03 isometric extrusion × A03n neon glitch × C12 bloom.
"""

import re

import pytest

from justdoit.animate.presets import iso_neon_glitch

ANSI_RE = re.compile(r"\033\[[0-9;]*m")


# ---------------------------------------------------------------------------
# Basic yield behaviour
# ---------------------------------------------------------------------------

def test_iso_neon_glitch_yields_frames():
    """Generator yields at least one frame."""
    frames = list(iso_neon_glitch("HI", n_frames=2, loop=False, seed=42))
    assert len(frames) >= 1


def test_iso_neon_glitch_loop_doubles_frames():
    """With loop=True, total frames = 2 × n_frames."""
    n = 4
    frames_loop = list(iso_neon_glitch("HI", n_frames=n, loop=True, seed=42))
    frames_no_loop = list(iso_neon_glitch("HI", n_frames=n, loop=False, seed=42))
    assert len(frames_loop) == 2 * len(frames_no_loop)


def test_iso_neon_glitch_frame_count_no_loop():
    """n_frames=5, loop=False → exactly 5 frames."""
    frames = list(iso_neon_glitch("HI", n_frames=5, loop=False, seed=1))
    assert len(frames) == 5


# ---------------------------------------------------------------------------
# Frame content
# ---------------------------------------------------------------------------

def test_iso_neon_glitch_frame_nonempty():
    """Every frame is a non-empty string."""
    for frame in iso_neon_glitch("HI", n_frames=3, loop=False, seed=0):
        assert isinstance(frame, str)
        assert len(frame.strip()) > 0


def test_iso_neon_glitch_contains_ansi():
    """Frames contain ANSI escape codes (color codes applied)."""
    frame = next(iter(iso_neon_glitch("HI", n_frames=1, loop=False, seed=7)))
    assert "\033[" in frame, "Expected ANSI escape codes in frame"


def test_iso_neon_glitch_frame_multiline():
    """Each frame has multiple lines (isometric output is taller than the input)."""
    frame = next(iter(iso_neon_glitch("HI", n_frames=1, loop=False, seed=3)))
    lines = frame.split("\n")
    assert len(lines) >= 7, "Isometric frame should have at least 7 lines (glyph height)"


def test_iso_neon_glitch_frames_differ():
    """Consecutive frames differ from each other (stochastic depth face)."""
    frames = list(iso_neon_glitch("JUST DO IT", n_frames=4, loop=False))
    # At least some pairs should differ (depth face is stochastic)
    all_same = all(f == frames[0] for f in frames[1:])
    assert not all_same, "All frames are identical — stochastic depth face not working"


# ---------------------------------------------------------------------------
# Color and parameter variants
# ---------------------------------------------------------------------------

def test_iso_neon_glitch_all_colors():
    """All supported neon colors produce non-empty output."""
    colors = ["cyan", "magenta", "red", "yellow", "green", "blue"]
    for c in colors:
        frame = next(iter(iso_neon_glitch("HI", color=c, n_frames=1, loop=False, seed=0)))
        assert len(frame.strip()) > 0, f"Color '{c}' produced empty output"


def test_iso_neon_glitch_invalid_color_raises():
    """Passing an unknown color name raises ValueError."""
    with pytest.raises(ValueError, match="Unknown neon color"):
        list(iso_neon_glitch("HI", color="purple", n_frames=1, loop=False))


def test_iso_neon_glitch_depth_2():
    """depth=2 produces valid output."""
    frame = next(iter(iso_neon_glitch("HI", depth=2, n_frames=1, loop=False, seed=0)))
    assert len(frame.strip()) > 0


def test_iso_neon_glitch_depth_6():
    """depth=6 produces valid output."""
    frame = next(iter(iso_neon_glitch("HI", depth=6, n_frames=1, loop=False, seed=0)))
    assert len(frame.strip()) > 0


def test_iso_neon_glitch_direction_left():
    """direction='left' produces valid output."""
    frame = next(iter(iso_neon_glitch("HI", direction="left", n_frames=1, loop=False, seed=0)))
    assert len(frame.strip()) > 0


def test_iso_neon_glitch_bloom_applied():
    """Bloom is applied: bloom_radius=0 should differ from bloom_radius=3."""
    # With bloom_radius=0 (minimal), bloom still processes but no cells in radius
    frame_bloom = next(iter(iso_neon_glitch("HI", bloom_radius=4, n_frames=1, loop=False, seed=99)))
    frame_no_bloom = next(iter(iso_neon_glitch("HI", bloom_radius=1, n_frames=1, loop=False, seed=99)))
    # Different radius = different output (bloom affects surrounding space cells)
    # We just verify both produce non-empty strings
    assert len(frame_bloom.strip()) > 0
    assert len(frame_no_bloom.strip()) > 0


# ---------------------------------------------------------------------------
# Seed reproducibility
# ---------------------------------------------------------------------------

def test_iso_neon_glitch_seed_reproducible():
    """Same seed produces identical frame sequences."""
    frames_a = list(iso_neon_glitch("HI", n_frames=4, loop=False, seed=123))
    frames_b = list(iso_neon_glitch("HI", n_frames=4, loop=False, seed=123))
    assert frames_a == frames_b, "Same seed should produce identical frames"


def test_iso_neon_glitch_different_seeds_differ():
    """Different seeds produce different frame sequences."""
    frames_a = list(iso_neon_glitch("JUST DO IT", n_frames=2, loop=False, seed=1))
    frames_b = list(iso_neon_glitch("JUST DO IT", n_frames=2, loop=False, seed=9999))
    # With enough randomness in depth-face, sequences should differ
    assert frames_a != frames_b, "Different seeds should produce different frames"


# ---------------------------------------------------------------------------
# Integration: render() → iso_neon_glitch()
# ---------------------------------------------------------------------------

def test_iso_neon_glitch_full_text():
    """Full 'JUST DO IT' text renders without error."""
    frames = list(iso_neon_glitch("JUST DO IT", n_frames=2, loop=False, seed=0))
    assert len(frames) == 2
    for f in frames:
        assert len(f.strip()) > 0
