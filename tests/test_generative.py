"""
Package: tests.test_generative
Tests for generative fill effects — Perlin noise (F02) and cellular automata (F03).

Covers: noise_fill, cells_fill, seeded reproducibility, mask shape preservation,
and integration via render(fill='noise') and render(fill='cells').
All tests are pure Python — no PIL dependency.
"""

import logging as _logging

import pytest

from justdoit.effects.generative import noise_fill, cells_fill, _build_perm, _perlin2d
from justdoit.core.glyph import glyph_to_mask
from justdoit.core.rasterizer import render, _FILL_FNS
from justdoit.fonts.builtin.block import BLOCK

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "tests.test_generative"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_GLYPH_A = BLOCK["A"]
_MASK_A  = glyph_to_mask(_GLYPH_A)


# -------------------------------------------------------------------------
# Perlin internals

def test_perlin_perm_length():
    """_build_perm() returns exactly 512 elements."""
    assert len(_build_perm(0)) == 512


def test_perlin_value_range():
    """_perlin2d() returns values in approximately -1.0 to 1.0."""
    perm = _build_perm(42)
    for x in range(10):
        for y in range(10):
            v = _perlin2d(x * 0.3, y * 0.3, perm)
            assert -2.0 <= v <= 2.0, f"Out of range at ({x},{y}): {v}"


def test_perlin_deterministic_with_seed():
    """Same seed produces identical noise values."""
    perm1 = _build_perm(7)
    perm2 = _build_perm(7)
    assert perm1 == perm2
    assert _perlin2d(1.5, 2.3, perm1) == _perlin2d(1.5, 2.3, perm2)


def test_perlin_different_seeds_differ():
    """Different seeds produce different permutations."""
    perm1 = _build_perm(1)
    perm2 = _build_perm(2)
    assert perm1 != perm2


# -------------------------------------------------------------------------
# noise_fill (F02)

def test_noise_fill_output_shape():
    """noise_fill output has same row count as input mask."""
    result = noise_fill(_MASK_A, seed=0)
    assert len(result) == len(_MASK_A)


def test_noise_fill_row_width():
    """noise_fill rows have same width as mask rows."""
    result = noise_fill(_MASK_A, seed=0)
    for r, (orig, filled) in enumerate(zip(_MASK_A, result)):
        assert len(filled) == len(orig), f"Row {r} width mismatch"


def test_noise_fill_ink_cells_nonempty():
    """noise_fill ink cells (mask >= 0.5) must not be spaces."""
    result = noise_fill(_MASK_A, seed=1)
    for r, row in enumerate(_MASK_A):
        for c, val in enumerate(row):
            if val >= 0.5:
                assert result[r][c] != " ", f"Ink cell ({r},{c}) rendered as space"


def test_noise_fill_empty_cells_are_spaces():
    """noise_fill empty cells (mask < 0.5) must be spaces."""
    result = noise_fill(_MASK_A, seed=2)
    for r, row in enumerate(_MASK_A):
        for c, val in enumerate(row):
            if val < 0.5:
                assert result[r][c] == " ", f"Empty cell ({r},{c}) not a space"


def test_noise_fill_seeded_reproducible():
    """noise_fill with the same seed produces identical output."""
    a = noise_fill(_MASK_A, seed=99)
    b = noise_fill(_MASK_A, seed=99)
    assert a == b


def test_noise_fill_different_seeds_vary():
    """noise_fill with different seeds produces different output."""
    a = noise_fill(_MASK_A, seed=0)
    b = noise_fill(_MASK_A, seed=1)
    assert a != b


def test_noise_fill_empty_mask():
    """noise_fill on empty mask returns empty list."""
    assert noise_fill([]) == []


def test_noise_fill_via_render():
    """render(fill='noise') works end-to-end without error."""
    result = render("A", font="block", fill="noise")
    assert isinstance(result, str)
    assert len(result) > 0


# -------------------------------------------------------------------------
# cells_fill (F03)

def test_cells_fill_output_shape():
    """cells_fill output has same row count as input mask."""
    result = cells_fill(_MASK_A, seed=0)
    assert len(result) == len(_MASK_A)


def test_cells_fill_row_width():
    """cells_fill rows have same width as mask rows."""
    result = cells_fill(_MASK_A, seed=0)
    for r, (orig, filled) in enumerate(zip(_MASK_A, result)):
        assert len(filled) == len(orig), f"Row {r} width mismatch"


def test_cells_fill_empty_cells_are_spaces():
    """cells_fill empty cells must be spaces."""
    result = cells_fill(_MASK_A, seed=3)
    for r, row in enumerate(_MASK_A):
        for c, val in enumerate(row):
            if val < 0.5:
                assert result[r][c] == " ", f"Empty cell ({r},{c}) not a space"


def test_cells_fill_ink_cells_nonempty():
    """cells_fill ink cells must contain a non-space character."""
    result = cells_fill(_MASK_A, steps=4, seed=42, alive_prob=0.5)
    ink_cells = [
        result[r][c]
        for r, row in enumerate(_MASK_A)
        for c, val in enumerate(row)
        if val >= 0.5
    ]
    assert any(ch != " " for ch in ink_cells), "All ink cells rendered as spaces"


def test_cells_fill_seeded_reproducible():
    """cells_fill with the same seed produces identical output."""
    a = cells_fill(_MASK_A, seed=7)
    b = cells_fill(_MASK_A, seed=7)
    assert a == b


def test_cells_fill_different_seeds_vary():
    """cells_fill with different seeds should usually produce different output."""
    a = cells_fill(_MASK_A, seed=10, alive_prob=0.5)
    b = cells_fill(_MASK_A, seed=11, alive_prob=0.5)
    assert a != b


def test_cells_fill_steps_zero():
    """cells_fill with steps=0 (no evolution) should not error."""
    result = cells_fill(_MASK_A, steps=0, seed=0)
    assert len(result) == len(_MASK_A)


def test_cells_fill_empty_mask():
    """cells_fill on empty mask returns empty list."""
    assert cells_fill([]) == []


def test_cells_fill_via_render():
    """render(fill='cells') works end-to-end without error."""
    result = render("A", font="block", fill="cells")
    assert isinstance(result, str)
    assert len(result) > 0


# -------------------------------------------------------------------------
# Fill registry

def test_fill_registry_contains_noise_and_cells():
    """_FILL_FNS must contain 'noise' and 'cells' keys."""
    assert "noise" in _FILL_FNS
    assert "cells" in _FILL_FNS
