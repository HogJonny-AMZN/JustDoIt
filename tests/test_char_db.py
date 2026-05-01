"""
Tests for justdoit.core.char_db — 6-zone shape-vector character database.
"""

import pytest

PIL = pytest.importorskip("PIL")

from justdoit.core.char_db import (
    PRINTABLE_ASCII,
    build_char_db,
    get_char_db,
    nearest_char,
    _DB_CACHE,
)


# -------------------------------------------------------------------------
# Build and structure tests

def test_build_char_db_returns_dict():
    db = build_char_db("ABC", cell_h=16, cell_w=8)
    assert isinstance(db, dict)
    assert len(db) == 3


def test_build_char_db_vectors_are_6d():
    db = build_char_db("AB", cell_h=16, cell_w=8)
    for ch, vec in db.items():
        assert len(vec) == 6, f"Expected 6D vector for {ch!r}, got {len(vec)}"


def test_build_char_db_values_in_range():
    db = build_char_db("XYZ !@#", cell_h=16, cell_w=8)
    for ch, vec in db.items():
        for v in vec:
            assert 0.0 <= v <= 1.0, f"Out-of-range value {v} for {ch!r}"


def test_build_full_charset():
    db = build_char_db(PRINTABLE_ASCII, cell_h=16, cell_w=8)
    assert len(db) == len(PRINTABLE_ASCII)


# -------------------------------------------------------------------------
# Cache tests

def test_get_char_db_cached():
    db1 = get_char_db("MN", cell_h=16, cell_w=8)
    db2 = get_char_db("MN", cell_h=16, cell_w=8)
    assert db1 is db2


def test_get_char_db_different_params_different_cache():
    db1 = get_char_db("AB", cell_h=16, cell_w=8)
    db2 = get_char_db("AB", cell_h=20, cell_w=10)
    assert db1 is not db2


# -------------------------------------------------------------------------
# nearest_char tests

def test_nearest_char_exact_match():
    db = {"A": [1.0, 0.0, 0.5, 0.5, 0.0, 1.0]}
    assert nearest_char([1.0, 0.0, 0.5, 0.5, 0.0, 1.0], db) == "A"


def test_nearest_char_closest():
    db = {
        "A": [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "B": [0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    }
    assert nearest_char([0.9, 0.1, 0.0, 0.0, 0.0, 0.0], db) == "A"
    assert nearest_char([0.1, 0.9, 0.0, 0.0, 0.0, 0.0], db) == "B"


def test_nearest_char_zero_vector():
    db = {
        " ": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "#": [0.8, 0.8, 0.8, 0.8, 0.8, 0.8],
    }
    assert nearest_char([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], db) == " "


def test_space_char_has_low_density():
    db = get_char_db(PRINTABLE_ASCII, cell_h=16, cell_w=8)
    vec = db.get(" ")
    assert vec is not None
    assert all(v < 0.3 for v in vec), f"Space char should have low density, got {vec}"
