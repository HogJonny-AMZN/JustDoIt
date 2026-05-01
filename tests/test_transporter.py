"""
Package: tests.test_transporter
Tests for A11 Transporter Materialize animation preset.

Covers: frame count, basic structure, determinism (seed).
"""

import logging as _logging

import pytest

from justdoit.animate.presets import transporter
from justdoit.core.rasterizer import render

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "tests.test_transporter"
__updated__ = "2026-04-26 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_SAMPLE = render("HI", font="block")
_TEXT = "HI"


# -------------------------------------------------------------------------
def test_transporter_generates_frames():
    """transporter yields at least one frame."""
    frames = list(transporter(_TEXT, n_frames=12))
    assert len(frames) > 0


# -------------------------------------------------------------------------
def test_transporter_frame_count_no_loop():
    """Without loop, transporter yields exactly n_frames frames."""
    n = 16
    frames = list(transporter(_TEXT, n_frames=n, loop=False))
    assert len(frames) == n


# -------------------------------------------------------------------------
def test_transporter_frame_count_with_loop():
    """With loop, transporter yields exactly 2 * n_frames frames."""
    n = 16
    frames = list(transporter(_TEXT, n_frames=n, loop=True))
    assert len(frames) == 2 * n


# -------------------------------------------------------------------------
def test_transporter_deterministic():
    """Same seed produces identical frame sequences."""
    a = list(transporter(_TEXT, n_frames=12, seed=99, loop=False))
    b = list(transporter(_TEXT, n_frames=12, seed=99, loop=False))
    assert a == b


# -------------------------------------------------------------------------
def test_transporter_different_seeds_differ():
    """Different seeds produce different frame sequences."""
    a = list(transporter(_TEXT, n_frames=12, seed=1, loop=False))
    b = list(transporter(_TEXT, n_frames=12, seed=2, loop=False))
    assert a != b


# -------------------------------------------------------------------------
def test_transporter_last_frame_has_ink():
    """The final materialize frame should contain dense block chars."""
    import re
    frames = list(transporter(_TEXT, n_frames=24, loop=False))
    last = frames[-1]
    plain = re.sub(r"\033\[[0-9;]*m", "", last)
    # Should contain at least one full block char
    assert "\u2588" in plain  # █


# -------------------------------------------------------------------------
def test_transporter_invalid_color_raises():
    """Unknown color raises ValueError."""
    with pytest.raises(ValueError, match="Unknown color"):
        list(transporter(_TEXT, n_frames=4, color="chartreuse"))
