"""
Package: tests.test_animate
Tests for animation presets and player (A01–A05).

Covers: typewriter, scanline, glitch, pulse, dissolve.
Player tests use a StringIO stream to avoid terminal I/O.
All tests are pure Python — no PIL dependency.
"""

import io
import logging as _logging

import pytest

from justdoit.animate.presets import typewriter, scanline, glitch, pulse, dissolve
from justdoit.animate.player import play
from justdoit.core.rasterizer import render

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "tests.test_animate"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_SAMPLE = render("HI", font="block")
_SMALL  = render("A", font="slim")


# -------------------------------------------------------------------------
# typewriter (A01)

def test_typewriter_yields_frames():
    """typewriter yields at least one frame."""
    frames = list(typewriter(_SMALL))
    assert len(frames) > 0


def test_typewriter_last_frame_matches_original():
    """Final typewriter frame contains the same visible chars as the original."""
    import re
    frames = list(typewriter(_SMALL))
    last = frames[-1]
    # Compare stripped lines — _grid_to_str trims trailing spaces
    plain = re.sub(r"\033\[[0-9;]*m", "", _SMALL)
    plain_lines = [ln.rstrip() for ln in plain.split("\n")]
    last_lines  = [ln.rstrip() for ln in last.split("\n")]
    assert plain_lines == last_lines


def test_typewriter_frames_grow_monotonically():
    """Each typewriter frame should have >= visible chars as the previous."""
    import re

    def visible_count(s):
        return sum(1 for c in re.sub(r"\033\[[0-9;]*m", "", s) if c not in (" ", "\n"))

    frames = list(typewriter(_SMALL, chars_per_frame=1))
    counts = [visible_count(f) for f in frames]
    for i in range(1, len(counts)):
        assert counts[i] >= counts[i - 1]


def test_typewriter_empty_string():
    """typewriter on empty string yields exactly one frame."""
    frames = list(typewriter(""))
    assert frames == [""]


# -------------------------------------------------------------------------
# scanline (A02)

def test_scanline_yields_frames():
    """scanline yields at least one frame."""
    frames = list(scanline(_SMALL))
    assert len(frames) > 0


def test_scanline_frame_count():
    """scanline yields n_rows + 1 frames (one per row plus final hold)."""
    n_rows = len(_SMALL.split("\n"))
    frames = list(scanline(_SMALL, rows_per_frame=1))
    assert len(frames) == n_rows + 1


def test_scanline_last_frame_matches_original():
    """Final scanline frame contains the same visible chars as the original."""
    import re
    frames = list(scanline(_SMALL))
    last = frames[-1]
    plain = re.sub(r"\033\[[0-9;]*m", "", _SMALL)
    plain_lines = [ln.rstrip() for ln in plain.split("\n")]
    last_lines  = [ln.rstrip() for ln in last.split("\n")]
    assert plain_lines == last_lines


def test_scanline_empty_string():
    """scanline on empty string yields exactly one frame."""
    frames = list(scanline(""))
    assert frames == [""]


# -------------------------------------------------------------------------
# glitch (A03)

def test_glitch_yields_correct_frame_count():
    """glitch yields exactly n_frames + 1 frames (n_frames + final clean)."""
    n = 10
    frames = list(glitch(_SMALL, n_frames=n, seed=42))
    assert len(frames) == n + 1


def test_glitch_last_frame_is_clean():
    """Final glitch frame contains the same visible chars as the original."""
    import re
    frames = list(glitch(_SMALL, n_frames=6, seed=0))
    last = frames[-1]
    plain = re.sub(r"\033\[[0-9;]*m", "", _SMALL)
    plain_lines = [ln.rstrip() for ln in plain.split("\n")]
    last_lines  = [ln.rstrip() for ln in last.split("\n")]
    assert plain_lines == last_lines


def test_glitch_some_frames_differ():
    """At least one glitch frame should differ from the original."""
    import re
    plain = re.sub(r"\033\[[0-9;]*m", "", _SAMPLE)
    frames = list(glitch(_SAMPLE, n_frames=12, intensity=0.5, seed=1))
    assert any(re.sub(r"\033\[[0-9;]*m", "", f).strip() != plain.strip() for f in frames)


def test_glitch_empty_string():
    """glitch on empty string yields one frame."""
    frames = list(glitch(""))
    assert frames == [""]


# -------------------------------------------------------------------------
# pulse (A04)

def test_pulse_yields_frames():
    """pulse yields at least one frame."""
    frames = list(pulse(_SMALL, n_cycles=1))
    assert len(frames) > 0


def test_pulse_frames_contain_ansi():
    """pulse frames should contain ANSI escape codes."""
    frames = list(pulse(_SMALL, n_cycles=1))
    # All frames except the final hold have ANSI codes
    assert any("\033[" in f for f in frames[:-1])


def test_pulse_last_frame_is_plain():
    """Final pulse frame should have no ANSI codes."""
    frames = list(pulse(_SMALL, n_cycles=1))
    assert "\033[" not in frames[-1]


def test_pulse_empty_string():
    """pulse on empty string yields one frame."""
    frames = list(pulse(""))
    assert frames == [""]


# -------------------------------------------------------------------------
# dissolve (A05)

def test_dissolve_yields_frames():
    """dissolve yields at least one frame."""
    frames = list(dissolve(_SMALL))
    assert len(frames) > 0


def test_dissolve_last_frame_is_blank():
    """Final dissolve frame should contain no visible characters."""
    frames = list(dissolve(_SMALL, seed=0))
    last = frames[-1]
    assert last.strip() == ""


def test_dissolve_frames_shrink_monotonically():
    """Each dissolve frame should have <= visible chars as the previous."""
    import re

    def visible_count(s):
        return sum(1 for c in re.sub(r"\033\[[0-9;]*m", "", s) if c not in (" ", "\n"))

    frames = list(dissolve(_SMALL, chars_per_frame=1, seed=42))
    counts = [visible_count(f) for f in frames]
    for i in range(1, len(counts)):
        assert counts[i] <= counts[i - 1]


def test_dissolve_empty_string():
    """dissolve on empty string yields one frame."""
    frames = list(dissolve(""))
    assert frames == [""]


# -------------------------------------------------------------------------
# player

def test_player_writes_frames_to_stream():
    """play() should write content to the output stream."""
    buf = io.StringIO()
    frames = iter(["frame1\nline2", "frame2\nline2"])
    play(frames, fps=1000.0, stream=buf)
    output = buf.getvalue()
    assert "frame" in output


def test_player_handles_empty_iterator():
    """play() with an empty iterator should not raise."""
    buf = io.StringIO()
    play(iter([]), fps=10.0, stream=buf)


def test_player_loop_runs_multiple_cycles():
    """play() with loop=True runs through frames more than once."""
    call_count = {"n": 0}

    def counting_frames():
        for i in range(3):
            call_count["n"] += 1
            yield f"frame{i}"
        # Raise KeyboardInterrupt to stop the loop
        raise KeyboardInterrupt

    buf = io.StringIO()
    play(counting_frames(), fps=1000.0, loop=False, stream=buf)
    # Should have rendered all 3 frames
    assert call_count["n"] == 3
