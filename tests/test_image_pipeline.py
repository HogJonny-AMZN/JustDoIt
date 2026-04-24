"""
Tests for justdoit.core.image_pipeline — high-level image-to-ASCII entry points.
"""

import pytest

PIL = pytest.importorskip("PIL")

from PIL import Image

from justdoit.core.image_pipeline import (
    grid_to_ansi,
    grid_to_svg,
    render_pil_image_as_ascii,
    render_text_as_image,
)
from justdoit.layout import find_default_ttf


# -------------------------------------------------------------------------
# render_text_as_image tests

def test_render_text_as_image_smoke():
    font_path = find_default_ttf()
    if font_path is None:
        pytest.skip("No system TTF font found")
    grid = render_text_as_image("HI", font_path, output_cols=40, output_rows=10)
    assert len(grid) == 10
    assert all(len(row) == 40 for row in grid)


def test_render_text_as_image_no_color():
    font_path = find_default_ttf()
    if font_path is None:
        pytest.skip("No system TTF font found")
    grid = render_text_as_image("AB", font_path, output_cols=20, output_rows=5, color=False)
    assert len(grid) == 5
    for row in grid:
        for ch, rgb in row:
            assert rgb is None


def test_render_text_as_image_with_color():
    font_path = find_default_ttf()
    if font_path is None:
        pytest.skip("No system TTF font found")
    grid = render_text_as_image("X", font_path, output_cols=10, output_rows=5, color=True)
    # At least some cells should have color
    has_color = any(rgb is not None for row in grid for _, rgb in row)
    assert has_color


def test_render_text_as_image_contains_non_space():
    font_path = find_default_ttf()
    if font_path is None:
        pytest.skip("No system TTF font found")
    grid = render_text_as_image("W", font_path, output_cols=20, output_rows=10)
    non_space = [ch for row in grid for ch, _ in row if ch != " "]
    assert len(non_space) > 0, "Rendered text should contain non-space characters"


# -------------------------------------------------------------------------
# render_pil_image_as_ascii tests

def test_render_pil_image_as_ascii_smoke():
    img = Image.new("RGB", (80, 48), (128, 128, 128))
    grid = render_pil_image_as_ascii(img, cell_w=8, cell_h=16)
    assert len(grid) == 3
    assert len(grid[0]) == 10


def test_render_pil_image_as_ascii_no_color():
    img = Image.new("RGB", (16, 16), (255, 0, 0))
    grid = render_pil_image_as_ascii(img, cell_w=8, cell_h=16, color=False)
    _, rgb = grid[0][0]
    assert rgb is None


# -------------------------------------------------------------------------
# grid_to_ansi tests

def test_grid_to_ansi_basic():
    grid = [[("A", (255, 0, 0)), (" ", None)]]
    result = grid_to_ansi(grid)
    assert "\033[38;2;255;0;0mA\033[0m" in result
    assert " " in result


def test_grid_to_ansi_no_color():
    grid = [[("X", None), ("Y", None)]]
    result = grid_to_ansi(grid)
    assert result == "XY"


def test_grid_to_ansi_multiline():
    grid = [
        [("A", (255, 0, 0))],
        [("B", (0, 255, 0))],
    ]
    result = grid_to_ansi(grid)
    assert "\n" in result
    lines = result.split("\n")
    assert len(lines) == 2


# -------------------------------------------------------------------------
# grid_to_svg tests

def test_grid_to_svg_basic():
    grid = [[("A", (255, 0, 0)), (" ", None)]]
    svg = grid_to_svg(grid, font_size=14)
    assert "<?xml" in svg
    assert "<svg" in svg
    assert "A" in svg
    assert "#ff0000" in svg


def test_grid_to_svg_empty_grid():
    svg = grid_to_svg([], font_size=14)
    assert "<svg" in svg


def test_grid_to_svg_canvas_override():
    grid = [[("X", (0, 255, 0))]]
    svg = grid_to_svg(grid, font_size=14, canvas_width=800, canvas_height=600)
    assert 'width="800"' in svg
    assert 'height="600"' in svg


def test_grid_to_svg_spaces_skipped():
    grid = [[(" ", (255, 255, 255)), ("A", (255, 0, 0))]]
    svg = grid_to_svg(grid, font_size=14)
    # Space should not generate a <text> element
    text_elements = svg.count("<text ")
    assert text_elements == 1
