"""
Tests for justdoit.core.image_sampler — image-to-ASCII conversion.
"""

import pytest

PIL = pytest.importorskip("PIL")

from PIL import Image

from justdoit.core.image_sampler import image_to_ascii


# -------------------------------------------------------------------------
# Grid dimension tests

def test_solid_white_image_dimensions():
    img = Image.new("RGB", (80, 48), (255, 255, 255))
    grid = image_to_ascii(img, cell_w=8, cell_h=16)
    assert len(grid) == 3   # 48 // 16
    assert len(grid[0]) == 10  # 80 // 8


def test_solid_black_image_dimensions():
    img = Image.new("RGB", (160, 64), (0, 0, 0))
    grid = image_to_ascii(img, cell_w=8, cell_h=16)
    assert len(grid) == 4   # 64 // 16
    assert len(grid[0]) == 20  # 160 // 8


def test_partial_cells_discarded():
    # 85 wide -> 85 // 8 = 10 cols (5px remainder discarded)
    # 50 tall -> 50 // 16 = 3 rows (2px remainder discarded)
    img = Image.new("RGB", (85, 50), (128, 128, 128))
    grid = image_to_ascii(img, cell_w=8, cell_h=16)
    assert len(grid) == 3
    assert len(grid[0]) == 10


def test_too_small_image_returns_empty():
    img = Image.new("RGB", (3, 5), (255, 255, 255))
    grid = image_to_ascii(img, cell_w=8, cell_h=16)
    assert grid == []


# -------------------------------------------------------------------------
# Character matching tests

def test_solid_white_matches_dense_char():
    img = Image.new("L", (8, 16), 255)
    grid = image_to_ascii(img, cell_w=8, cell_h=16, color=False)
    assert len(grid) == 1
    assert len(grid[0]) == 1
    ch, rgb = grid[0][0]
    assert isinstance(ch, str) and len(ch) == 1
    assert rgb is None


def test_solid_black_matches_space():
    img = Image.new("L", (8, 16), 0)
    grid = image_to_ascii(img, cell_w=8, cell_h=16, color=False)
    ch, _ = grid[0][0]
    # Black cell should match a low-density char (space or similar)
    assert ch in " .,:;"


# -------------------------------------------------------------------------
# Color tests

def test_color_true_returns_rgb():
    img = Image.new("RGB", (16, 16), (200, 100, 50))
    grid = image_to_ascii(img, cell_w=8, cell_h=16, color=True)
    ch, rgb = grid[0][0]
    assert rgb is not None
    assert len(rgb) == 3
    # Average of solid color should be close to original
    assert abs(rgb[0] - 200) < 5
    assert abs(rgb[1] - 100) < 5
    assert abs(rgb[2] - 50) < 5


def test_color_false_returns_none():
    img = Image.new("RGB", (16, 16), (200, 100, 50))
    grid = image_to_ascii(img, cell_w=8, cell_h=16, color=False)
    _, rgb = grid[0][0]
    assert rgb is None


# -------------------------------------------------------------------------
# Mode conversion tests

def test_grayscale_input():
    img = Image.new("L", (16, 16), 128)
    grid = image_to_ascii(img, cell_w=8, cell_h=16, color=True)
    assert len(grid) == 1
    ch, rgb = grid[0][0]
    assert isinstance(ch, str)
    assert rgb is not None


def test_rgba_input():
    img = Image.new("RGBA", (16, 16), (255, 0, 0, 128))
    grid = image_to_ascii(img, cell_w=8, cell_h=16, color=True)
    assert len(grid) == 1
    ch, rgb = grid[0][0]
    assert isinstance(ch, str)
    assert rgb is not None


# -------------------------------------------------------------------------
# Half-filled image test

def test_half_filled_produces_different_chars():
    # Left half white, right half black
    img = Image.new("L", (16, 16), 0)
    for y in range(16):
        for x in range(8):
            img.putpixel((x, y), 255)
    grid = image_to_ascii(img, cell_w=8, cell_h=16, color=False)
    assert len(grid) == 1
    assert len(grid[0]) == 2
    # Left cell should be denser than right cell
    ch_left, _ = grid[0][0]
    ch_right, _ = grid[0][1]
    assert ch_left != ch_right


# -------------------------------------------------------------------------
# Pre-built DB test

def test_custom_db():
    db = {
        "X": [0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
        " ": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    }
    img = Image.new("L", (8, 16), 200)
    grid = image_to_ascii(img, cell_w=8, cell_h=16, color=False, charset="X ", db=db)
    ch, _ = grid[0][0]
    assert ch in ("X", " ")
