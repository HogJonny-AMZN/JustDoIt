"""
Tests for justdoit.effects.shape_fill (F07 — shape-vector fill).
"""

import pytest

from justdoit.core.glyph import glyph_to_mask
from justdoit.effects.shape_fill import (
    SHAPE_CHARS,
    _get_char_db,
    _nearest_char,
    _sample_cell,
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
# Mask sampling tests (pure Python — no Pillow)

def test_sample_cell_interior():
    # All-ink mask → all zones should be ~1.0
    mask = [[1.0] * 4 for _ in range(4)]
    vec = _sample_cell(mask, 2, 2)
    assert len(vec) == 6
    assert all(v == pytest.approx(1.0) for v in vec)


def test_sample_cell_exterior():
    # All-empty mask → all zones should be 0.0
    mask = [[0.0] * 4 for _ in range(4)]
    vec = _sample_cell(mask, 2, 2)
    assert all(v == pytest.approx(0.0) for v in vec)


def test_sample_cell_left_edge():
    # Ink on left, empty on right — ML should exceed MR
    mask = [
        [0.0, 0.0, 0.0, 0.0],
        [1.0, 1.0, 0.0, 0.0],
        [1.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0],
    ]
    vec = _sample_cell(mask, 2, 1)  # cell at the ink/empty boundary
    ul, ur, ml, mr, ll, lr = vec
    assert ml > mr, f"Expected ML > MR at left edge, got ML={ml}, MR={mr}"


def test_sample_cell_boundary_clamping():
    # Sampling at corners should not raise IndexError
    mask = [[1.0] * 3 for _ in range(3)]
    _sample_cell(mask, 0, 0)
    _sample_cell(mask, 0, 2)
    _sample_cell(mask, 2, 0)
    _sample_cell(mask, 2, 2)


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
# Full shape_fill integration tests (Pillow-gated)

def test_shape_fill_output_shape():
    pytest.importorskip("PIL")
    mask = [[1.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    result = shape_fill(mask)
    assert len(result) == 3
    assert all(len(row) == 3 for row in result)


def test_shape_fill_output_is_strings():
    pytest.importorskip("PIL")
    mask = [[float(c % 2) for c in range(5)] for _ in range(5)]
    result = shape_fill(mask)
    assert all(isinstance(row, str) for row in result)


def test_shape_fill_empty_mask():
    pytest.importorskip("PIL")
    mask = [[0.0] * 4 for _ in range(4)]
    result = shape_fill(mask)
    assert all(set(row) <= {" "} for row in result), "Empty mask should produce spaces"


def test_shape_fill_via_render():
    pytest.importorskip("PIL")
    from justdoit.core.rasterizer import render
    result = render("AB", font="block", fill="shape")
    assert isinstance(result, str)
    assert len(result.strip()) > 0


def test_shape_fill_deterministic():
    pytest.importorskip("PIL")
    mask = glyph_to_mask([" ██ ", "█  █", "████", "█  █", "█  █", "    ", "    "])
    r1 = shape_fill(mask)
    r2 = shape_fill(mask)
    assert r1 == r2


def test_shape_fill_custom_charset():
    pytest.importorskip("PIL")
    charset = "@#. "
    mask = [[1.0, 1.0, 0.0], [0.0, 1.0, 0.0]]
    result = shape_fill(mask, charset=charset)
    for row in result:
        for ch in row:
            assert ch in charset, f"Unexpected char {ch!r} not in charset {charset!r}"
