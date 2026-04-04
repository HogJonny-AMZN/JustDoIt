"""
Package: tests.test_output_cast
Tests for asciinema v2 .cast output writer (cast.py).
"""

import json
import os
import tempfile

import pytest

from justdoit.output.cast import to_cast, save_cast

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "tests.test_output_cast"
__updated__ = "2026-03-30 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_FRAMES = ["Hello\nWorld", "Hello\nWorld!", "Hello\nWorld!!"]


# -------------------------------------------------------------------------
def test_header_valid_json():
    """First line of to_cast() output is valid JSON with version=2."""
    cast = to_cast(_FRAMES, fps=12.0, title="Test")
    first_line = cast.strip().split("\n")[0]
    header = json.loads(first_line)
    assert header["version"] == 2
    assert "width" in header
    assert "height" in header
    assert header["title"] == "Test"


def test_header_custom_dims():
    """to_cast() respects explicit cols/rows."""
    cast = to_cast(_FRAMES, cols=80, rows=24)
    header = json.loads(cast.strip().split("\n")[0])
    assert header["width"] == 80
    assert header["height"] == 24


def test_timestamps_monotonic():
    """Timestamps increase monotonically at exactly 1/fps intervals."""
    fps = 12.0
    cast = to_cast(_FRAMES, fps=fps)
    lines = cast.strip().split("\n")
    event_lines = lines[1:]
    dt = 1.0 / fps
    for i, line in enumerate(event_lines):
        ev = json.loads(line)
        assert abs(ev[0] - round(i * dt, 6)) < 1e-9


def test_event_type_is_output():
    """All events have type 'o'."""
    cast = to_cast(_FRAMES)
    lines = cast.strip().split("\n")[1:]
    for line in lines:
        ev = json.loads(line)
        assert ev[1] == "o"


def test_content_preserved():
    """Frame content appears in each event's data field."""
    cast = to_cast(_FRAMES)
    lines = cast.strip().split("\n")[1:]
    assert len(lines) == len(_FRAMES)
    for i, line in enumerate(lines):
        ev = json.loads(line)
        assert _FRAMES[i] in ev[2]


def test_clear_screen_prefix():
    """Each event data starts with the clear+home escape sequence."""
    cast = to_cast(_FRAMES)
    lines = cast.strip().split("\n")[1:]
    for line in lines:
        ev = json.loads(line)
        assert ev[2].startswith("\033[2J\033[H")


def test_auto_dims_wider_than_content():
    """Auto-detected dims are at least as wide as the content."""
    frames = ["ABCDE\nFGHIJ"]  # 5 cols, 2 rows
    cast = to_cast(frames)
    header = json.loads(cast.strip().split("\n")[0])
    assert header["width"] >= 5
    assert header["height"] >= 2


def test_frame_count_matches():
    """Number of event lines equals number of input frames."""
    cast = to_cast(_FRAMES)
    lines = cast.strip().split("\n")
    assert len(lines) - 1 == len(_FRAMES)


def test_empty_frames_raises():
    """to_cast() raises ValueError on empty frame list."""
    with pytest.raises(ValueError):
        to_cast([])


def test_bad_fps_raises():
    """to_cast() raises ValueError for non-positive fps."""
    with pytest.raises(ValueError):
        to_cast(_FRAMES, fps=0)


def test_save_cast_writes_file():
    """save_cast() creates a file containing valid asciinema JSON."""
    with tempfile.NamedTemporaryFile(suffix=".cast", delete=False) as f:
        path = f.name
    try:
        save_cast(_FRAMES, path, fps=24.0, title="SaveTest")
        assert os.path.exists(path)
        with open(path, encoding="utf-8") as f:
            content = f.read()
        header = json.loads(content.strip().split("\n")[0])
        assert header["version"] == 2
        assert header["title"] == "SaveTest"
    finally:
        os.unlink(path)
