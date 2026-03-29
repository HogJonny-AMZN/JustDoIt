"""
Tests for justdoit.effects.shape_fill (F07 — shape-vector fill).
"""

import pytest

from justdoit.core.glyph import glyph_to_mask
from justdoit.effects.shape_fill import (
    SHAPE_CHARS,
    _cell_char,
    _get_char_db,
    _nearest_char,
    shape_fill,
)


# -------------------------------------------------------------------------
# Shape DB tests (Pillow-gated)

def test_char_db_builds():
    pytest.importorskip("PIL")
    db = _get_char_db(SHAPE_CHARS)
    assert len(db) == len(SHAPE_CHARS)


def test_char_db_vectors_are_6d():
    pytest.importorskip("PIL")
    db = _get_char_db(SHAPE_CHARS)
    for ch, vec in db.items():
        assert len(vec) == 6, f"Expected 6D vector for {ch!r}, got {len(vec)}"


def test_char_db_values_in_range():
    pytest.importorskip("PIL")
    db = _get_char_db(SHAPE_CHARS)
    for ch, vec in db.items():
        for v in vec:
            assert 0.0 <= v <= 1.0, f"Out-of-range value {v} for {ch!r}"


def test_char_db_cached():
    pytest.importorskip("PIL")
    db1 = _get_char_db(SHAPE_CHARS)
    db2 = _get_char_db(SHAPE_CHARS)
    assert db1 is db2


def test_space_char_is_near_zero():
    pytest.importorskip("PIL")
    db = _get_char_db(SHAPE_CHARS)
    vec = db.get(" ")
    assert vec is not None
    assert all(v < 0.3 for v in vec), f"Space char should have low density, got {vec}"


# -------------------------------------------------------------------------
# _cell_char tests (pure Python — no Pillow)

def _make_mask(rows, cols, ink_set):
    """Helper: build a mask where (r,c) in ink_set → 1.0, else 0.0."""
    return [[1.0 if (r, c) in ink_set else 0.0 for c in range(cols)] for r in range(rows)]


def test_cell_char_interior_is_dense():
    # A cell fully surrounded by ink on all 4 cardinal sides → dense interior char
    # Use a 3×3 all-ink mask; center cell has all 4 neighbors filled
    mask = [[1.0] * 3 for _ in range(3)]
    ch = _cell_char(mask, 1, 1, 3, 3)
    assert ch in "@#S%*+;:,. ", f"Expected interior char, got {ch!r}"
    # Center of 3×3 all-ink: all 8 neighbors filled → deepest interior char
    assert ch == "@"


def test_cell_char_top_only_empty_gives_dash():
    # Cell has ink below, left, right but empty above → horizontal boundary → "-"
    mask = [
        [0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0],
    ]
    ch = _cell_char(mask, 1, 1, 3, 3)
    assert ch == "-", f"Expected '-', got {ch!r}"


def test_cell_char_left_only_empty_gives_pipe():
    # Cell has ink above, below, right but empty left → vertical boundary → "|"
    mask = [
        [0.0, 1.0, 1.0],
        [0.0, 1.0, 1.0],
        [0.0, 1.0, 1.0],
    ]
    ch = _cell_char(mask, 1, 1, 3, 3)
    assert ch == "|", f"Expected '|', got {ch!r}"


def test_cell_char_top_left_empty_gives_slash():
    # Cell has ink below and right, empty top and left → upper-left corner → "/"
    mask = [
        [0.0, 0.0, 0.0],
        [0.0, 1.0, 1.0],
        [0.0, 1.0, 1.0],
    ]
    ch = _cell_char(mask, 1, 1, 3, 3)
    assert ch == "/", f"Expected '/', got {ch!r}"


def test_cell_char_top_right_empty_gives_backslash():
    # Empty top and right → upper-right corner → "\\"
    mask = [
        [0.0, 0.0, 0.0],
        [1.0, 1.0, 0.0],
        [1.0, 1.0, 0.0],
    ]
    ch = _cell_char(mask, 1, 1, 3, 3)
    assert ch == "\\", f"Expected '\\\\', got {ch!r}"


def test_cell_char_bottom_left_empty_gives_backslash():
    # Empty bottom and left → lower-left corner → "\\"
    mask = [
        [0.0, 1.0, 1.0],
        [0.0, 1.0, 1.0],
        [0.0, 0.0, 0.0],
    ]
    ch = _cell_char(mask, 1, 1, 3, 3)
    assert ch == "\\", f"Expected '\\\\', got {ch!r}"


def test_cell_char_bottom_right_empty_gives_slash():
    # Empty bottom and right → lower-right corner → "/"
    mask = [
        [1.0, 1.0, 0.0],
        [1.0, 1.0, 0.0],
        [0.0, 0.0, 0.0],
    ]
    ch = _cell_char(mask, 1, 1, 3, 3)
    assert ch == "/", f"Expected '/', got {ch!r}"


def test_cell_char_oob_treated_as_empty():
    # Cell at corner of grid — out-of-bounds neighbors treated as empty
    mask = [[1.0, 1.0], [1.0, 1.0]]
    # Top-left corner: top OOB, left OOB → top+left empty → "/"
    ch = _cell_char(mask, 0, 0, 2, 2)
    assert ch == "/", f"Expected '/', got {ch!r}"


def test_cell_char_isolated_gives_plus():
    # Single ink cell surrounded by empty on all 4 sides → "+"
    mask = [[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.0]]
    ch = _cell_char(mask, 1, 1, 3, 3)
    assert ch == "+"


# -------------------------------------------------------------------------
# Nearest-char tests (pure Python — no Pillow)

def test_nearest_char_exact_match():
    db = {"A": [1.0, 0.0, 0.5, 0.5, 0.0, 1.0]}
    assert _nearest_char([1.0, 0.0, 0.5, 0.5, 0.0, 1.0], db) == "A"


def test_nearest_char_closest():
    db = {
        "A": [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "B": [0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    }
    assert _nearest_char([0.9, 0.1, 0.0, 0.0, 0.0, 0.0], db) == "A"
    assert _nearest_char([0.1, 0.9, 0.0, 0.0, 0.0, 0.0], db) == "B"


# -------------------------------------------------------------------------
# Full shape_fill integration tests (pure Python — no Pillow required)

def test_shape_fill_output_shape():
    mask = [[1.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    result = shape_fill(mask)
    assert len(result) == 3
    assert all(len(row) == 3 for row in result)


def test_shape_fill_output_is_strings():
    mask = [[float(c % 2) for c in range(5)] for _ in range(5)]
    result = shape_fill(mask)
    assert all(isinstance(row, str) for row in result)


def test_shape_fill_empty_mask():
    mask = [[0.0] * 4 for _ in range(4)]
    result = shape_fill(mask)
    assert all(set(row) <= {" "} for row in result), "Empty mask should produce spaces"


def test_shape_fill_exterior_cells_are_spaces():
    mask = [[0.0] * 5 for _ in range(5)]
    for r in range(1, 4):
        for c in range(1, 4):
            mask[r][c] = 1.0
    result = shape_fill(mask)
    assert result[0][0] == " "
    assert result[4][4] == " "


def test_shape_fill_via_render():
    from justdoit.core.rasterizer import render
    result = render("AB", font="block", fill="shape")
    assert isinstance(result, str)
    assert len(result.strip()) > 0


def test_shape_fill_deterministic():
    mask = glyph_to_mask([" ██ ", "█  █", "████", "█  █", "█  █", "    ", "    "])
    r1 = shape_fill(mask)
    r2 = shape_fill(mask)
    assert r1 == r2


def test_shape_fill_vertical_stroke_gives_pipes():
    # A single-cell-wide vertical stroke → all cells should be "|"
    mask = [[0.0, 1.0, 0.0] for _ in range(5)]
    result = shape_fill(mask)
    for row in result:
        assert row[1] == "|", f"Expected '|' in vertical stroke, got {row[1]!r}"


def test_shape_fill_horizontal_stroke_gives_dashes():
    # A single-cell-tall horizontal stripe → all cells should be "-"
    mask = [
        [0.0, 0.0, 0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0, 1.0, 1.0],
        [0.0, 0.0, 0.0, 0.0, 0.0],
    ]
    result = shape_fill(mask)
    for ch in result[1]:
        assert ch == "-", f"Expected '-' in horizontal stroke, got {ch!r}"


def test_shape_fill_rectangle_corners():
    # 5×5 filled rectangle → corners should be /  \\  \\  /
    mask = [[1.0] * 5 for _ in range(5)]
    result = shape_fill(mask)
    assert result[0][0] == "/",  "Top-left corner should be '/'"
    assert result[0][4] == "\\", "Top-right corner should be '\\\\'"
    assert result[4][0] == "\\", "Bottom-left corner should be '\\\\'"
    assert result[4][4] == "/",  "Bottom-right corner should be '/'"
