"""
Tests for justdoit.effects.shape_fill (F07 — shape-vector fill).
"""

import pytest

from justdoit.core.glyph import glyph_to_mask
from justdoit.effects.shape_fill import (
    SHAPE_CHARS,
    _edge_char,
    _get_char_db,
    _nearest_char,
    _sdf_val,
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
# SDF lookup tests (pure Python — no Pillow)

def test_sdf_val_in_bounds():
    sdf = [[0.1, 0.5], [0.8, 1.0]]
    assert _sdf_val(sdf, 0, 0, 2, 2) == pytest.approx(0.1)
    assert _sdf_val(sdf, 1, 1, 2, 2) == pytest.approx(1.0)


def test_sdf_val_clamps_negative():
    sdf = [[0.5, 0.9], [0.2, 0.7]]
    # Out-of-bounds indices should clamp
    assert _sdf_val(sdf, -1, 0, 2, 2) == _sdf_val(sdf, 0, 0, 2, 2)
    assert _sdf_val(sdf, 0, -1, 2, 2) == _sdf_val(sdf, 0, 0, 2, 2)


def test_sdf_val_clamps_overflow():
    sdf = [[0.5, 0.9], [0.2, 0.7]]
    assert _sdf_val(sdf, 5, 0, 2, 2) == _sdf_val(sdf, 1, 0, 2, 2)
    assert _sdf_val(sdf, 0, 5, 2, 2) == _sdf_val(sdf, 0, 1, 2, 2)


# -------------------------------------------------------------------------
# Edge character tests (pure Python — no Pillow)

def test_edge_char_returns_string():
    # Flat horizontal gradient (high right, low left) → "-"
    sdf = [[0.0] * 5 for _ in range(5)]
    for r in range(5):
        for c in range(5):
            sdf[r][c] = c * 0.2  # gradient in x direction
    ch = _edge_char(sdf, 2, 2, 5, 5)
    assert isinstance(ch, str) and len(ch) == 1


def test_edge_char_horizontal_gradient_gives_dash():
    # Pure x-gradient → angle near 0° → "-"
    sdf = [[c * 0.2 for c in range(5)] for _ in range(5)]
    ch = _edge_char(sdf, 2, 2, 5, 5)
    assert ch == "-"


def test_edge_char_vertical_gradient_gives_pipe():
    # Pure y-gradient → angle near 90° → "|"
    sdf = [[r * 0.2 for _ in range(5)] for r in range(5)]
    ch = _edge_char(sdf, 2, 2, 5, 5)
    assert ch == "|"


def test_edge_char_flat_field_gives_plus():
    # Uniform SDF → near-zero gradient → "+"
    sdf = [[0.5] * 5 for _ in range(5)]
    ch = _edge_char(sdf, 2, 2, 5, 5)
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


def test_shape_fill_interior_chars_present():
    # A large solid block should produce interior density characters
    mask = [[1.0] * 20 for _ in range(20)]
    result = shape_fill(mask)
    interior_chars = set("@#S%*+;:,.")
    all_chars = set("".join(result))
    assert all_chars & interior_chars, f"Expected interior chars, got: {all_chars}"


def test_shape_fill_exterior_is_space():
    # Surrounded by a thick border of zeros — outer cells must be space
    mask = [[0.0] * 10 for _ in range(10)]
    for r in range(3, 7):
        for c in range(3, 7):
            mask[r][c] = 1.0
    result = shape_fill(mask)
    # Corner cells are pure exterior
    assert result[0][0] == " "
    assert result[0][9] == " "
    assert result[9][0] == " "
    assert result[9][9] == " "
