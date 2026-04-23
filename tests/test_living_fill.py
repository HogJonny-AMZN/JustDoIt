"""
Package: tests.test_living_fill
Tests for A06 Living Fill animation preset — Conway's Game of Life inside glyph masks.

Covers: non-empty output, frame count, frame shape consistency, exterior cells
are spaces, frames differ over time, loop mode doubles frames.
"""

import logging as _logging

import pytest

from justdoit.animate.presets import living_fill

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "tests.test_living_fill"
__updated__ = "2026-04-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_TEXT = "HI"
_N_FRAMES = 10


# -------------------------------------------------------------------------
def test_living_fill_non_empty():
    """living_fill yields non-empty frame strings."""
    frames = list(living_fill(_TEXT, n_frames=_N_FRAMES))
    assert len(frames) > 0
    for f in frames:
        assert len(f) > 0


# -------------------------------------------------------------------------
def test_living_fill_frame_count():
    """living_fill yields exactly n_frames frames when loop=False."""
    frames = list(living_fill(_TEXT, n_frames=_N_FRAMES, loop=False))
    assert len(frames) == _N_FRAMES


# -------------------------------------------------------------------------
def test_living_fill_loop_doubles_frames():
    """living_fill with loop=True yields 2*n_frames frames."""
    frames = list(living_fill(_TEXT, n_frames=_N_FRAMES, loop=True))
    assert len(frames) == 2 * _N_FRAMES


# -------------------------------------------------------------------------
def test_living_fill_frame_shape_consistent():
    """All frames have the same number of rows and consistent row widths."""
    frames = list(living_fill(_TEXT, n_frames=_N_FRAMES))
    row_counts = [len(f.split("\n")) for f in frames]
    assert len(set(row_counts)) == 1, "All frames must have same row count"

    # Check all rows in all frames have same width
    widths_per_frame = []
    for f in frames:
        rows = f.split("\n")
        widths_per_frame.append(tuple(len(r) for r in rows))
    assert len(set(widths_per_frame)) == 1, "All frames must have identical row widths"


# -------------------------------------------------------------------------
def test_living_fill_exterior_cells_are_spaces():
    """Exterior cells (outside glyph mask) must be spaces in every frame."""
    from justdoit.core.rasterizer import render

    # Get the ink mask from a density render
    rendered = render(_TEXT, font="block", fill="density")
    base_rows = rendered.split("\n")
    width = max(len(r) for r in base_rows)
    base_rows = [r.ljust(width) for r in base_rows]
    exterior = set()
    for r, row in enumerate(base_rows):
        for c, ch in enumerate(row):
            if ch == " ":
                exterior.add((r, c))

    frames = list(living_fill(_TEXT, n_frames=_N_FRAMES))
    for fi, f in enumerate(frames):
        rows = f.split("\n")
        for r, c in exterior:
            if r < len(rows) and c < len(rows[r]):
                assert rows[r][c] == " ", (
                    f"Frame {fi}: exterior cell ({r},{c}) is '{rows[r][c]}', expected space"
                )


# -------------------------------------------------------------------------
def test_living_fill_frames_differ():
    """Frames should differ over time — the CA is evolving."""
    frames = list(living_fill(_TEXT, n_frames=20, seed=42))
    # At least some frames must be different from frame 0
    unique_frames = set(frames)
    assert len(unique_frames) > 1, "All frames are identical — CA is not evolving"


# -------------------------------------------------------------------------
def test_living_fill_deterministic_with_seed():
    """Same seed produces identical frame sequences."""
    frames_a = list(living_fill(_TEXT, n_frames=5, seed=123))
    frames_b = list(living_fill(_TEXT, n_frames=5, seed=123))
    assert frames_a == frames_b
