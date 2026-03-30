"""
Package: tests.test_output_apng
Tests for APNG animation output writer (apng.py).

All tests are gated on Pillow via pytest.importorskip.
"""

import io
import os
import tempfile

import pytest

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "tests.test_output_apng"
__updated__ = "2026-03-30 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_FRAMES = [
    "Hello\nWorld",
    "Hello\nWorld!",
    "Hello\nWorld!!",
    "Hello\nWorld!!!",
]

_PNG_MAGIC = b"\x89PNG"


# -------------------------------------------------------------------------
def test_apng_png_magic_bytes():
    """to_apng() output starts with PNG magic bytes."""
    pytest.importorskip("PIL")
    from justdoit.output.apng import to_apng
    data = to_apng(_FRAMES, fps=12.0)
    assert data[:4] == _PNG_MAGIC


def test_apng_frame_count():
    """to_apng() produces non-empty bytes for all frames."""
    pytest.importorskip("PIL")
    from justdoit.output.apng import to_apng
    data = to_apng(_FRAMES, fps=24.0)
    assert len(data) > 100  # sanity: real PNG has substantial size


def test_apng_custom_bg_color():
    """to_apng() accepts custom background color."""
    pytest.importorskip("PIL")
    from justdoit.output.apng import to_apng
    data = to_apng(_FRAMES, fps=12.0, bg_color="#222222")
    assert data[:4] == _PNG_MAGIC


def test_apng_loop_param():
    """to_apng() accepts loop=0 (infinite) and loop=1 (play-once)."""
    pytest.importorskip("PIL")
    from justdoit.output.apng import to_apng
    data_inf = to_apng(_FRAMES, fps=12.0, loop=0)
    data_once = to_apng(_FRAMES, fps=12.0, loop=1)
    assert data_inf[:4] == _PNG_MAGIC
    assert data_once[:4] == _PNG_MAGIC


def test_frame_to_image_dims():
    """frame_to_image() returns a PIL Image with non-zero dimensions."""
    pytest.importorskip("PIL")
    from justdoit.output.apng import frame_to_image
    img = frame_to_image("Hello\nWorld", font_size=14)
    assert img.width > 0
    assert img.height > 0


def test_frame_to_image_ansi_colored():
    """frame_to_image() handles ANSI colored frames without error."""
    pytest.importorskip("PIL")
    from justdoit.output.apng import frame_to_image
    colored = "\033[91mHi\033[0m\nThere"
    img = frame_to_image(colored, font_size=14)
    assert img.width > 0


def test_apng_empty_frames_raises():
    """to_apng() raises ValueError on empty frame list."""
    pytest.importorskip("PIL")
    from justdoit.output.apng import to_apng
    with pytest.raises(ValueError):
        to_apng([])


def test_save_apng_writes_file():
    """save_apng() creates a valid PNG file at the given path."""
    pytest.importorskip("PIL")
    from justdoit.output.apng import save_apng
    with tempfile.NamedTemporaryFile(suffix=".apng", delete=False) as f:
        path = f.name
    try:
        save_apng(_FRAMES, path, fps=12.0)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
        with open(path, "rb") as f:
            magic = f.read(4)
        assert magic == _PNG_MAGIC
    finally:
        os.unlink(path)
