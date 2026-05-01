"""Tests for flame_float_grid() in justdoit/effects/generative.py."""
import pytest
from justdoit.effects.generative import flame_float_grid
from justdoit.core.glyph import glyph_to_mask
from justdoit.fonts import FONTS


def _simple_mask(rows=5, cols=5):
    """Return a fully-filled boolean-style float mask."""
    return [[1.0] * cols for _ in range(rows)]


def _block_mask(char="A"):
    """Return glyph_to_mask for a block-font character."""
    font = FONTS.get("block", {})
    glyph = font.get(char, font.get(" "))
    ink = "".join({c for row in glyph for c in row if c != " "}) or chr(9608)
    return glyph_to_mask(glyph, ink_chars=ink)


# ---------------------------------------------------------------------------
# Return type and shape
# ---------------------------------------------------------------------------
def test_returns_list_of_lists():
    mask = _simple_mask()
    result = flame_float_grid(mask, seed=0)
    assert isinstance(result, list)
    for row in result:
        assert isinstance(row, list)


def test_same_dimensions_as_mask():
    mask = _simple_mask(6, 8)
    result = flame_float_grid(mask, seed=0)
    assert len(result) == len(mask)
    for r_result, r_mask in zip(result, mask):
        assert len(r_result) == len(r_mask)


def test_block_glyph_dimensions():
    mask = _block_mask("J")
    result = flame_float_grid(mask, seed=1)
    assert len(result) == len(mask)
    cols_mask = max(len(r) for r in mask)
    cols_result = max(len(r) for r in result) if result else 0
    assert cols_result == cols_mask


# ---------------------------------------------------------------------------
# Value range
# ---------------------------------------------------------------------------
def test_all_values_in_range():
    mask = _simple_mask(8, 10)
    result = flame_float_grid(mask, seed=42)
    for row in result:
        for v in row:
            assert 0.0 <= v <= 1.0, f"value {v} out of [0.0, 1.0]"


def test_block_glyph_values_in_range():
    mask = _block_mask("A")
    result = flame_float_grid(mask, seed=7)
    for row in result:
        for v in row:
            assert 0.0 <= v <= 1.0


# ---------------------------------------------------------------------------
# Exterior cells are 0.0
# ---------------------------------------------------------------------------
def test_exterior_cells_are_zero():
    """Cells where mask < 0.5 (exterior) must be 0.0."""
    font = FONTS.get("block", {})
    glyph = font.get("A", font.get(" "))
    ink = "".join({c for row in glyph for c in row if c != " "}) or chr(9608)
    mask = glyph_to_mask(glyph, ink_chars=ink)
    result = flame_float_grid(mask, seed=0)

    rows = len(mask)
    cols = max(len(r) for r in mask) if mask else 0

    for r in range(rows):
        for c in range(cols):
            is_ink = (c < len(mask[r])) and (mask[r][c] >= 0.5)
            if not is_ink:
                assert result[r][c] == 0.0, (
                    f"exterior cell ({r},{c}) should be 0.0, got {result[r][c]}"
                )


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------
def test_deterministic_with_same_seed():
    mask = _simple_mask(6, 8)
    r1 = flame_float_grid(mask, seed=123)
    r2 = flame_float_grid(mask, seed=123)
    assert r1 == r2


def test_block_glyph_deterministic():
    mask = _block_mask("B")
    r1 = flame_float_grid(mask, seed=0)
    r2 = flame_float_grid(mask, seed=0)
    assert r1 == r2


# ---------------------------------------------------------------------------
# Different seeds give different results
# ---------------------------------------------------------------------------
def test_different_seeds_differ():
    mask = _simple_mask(8, 12)
    r1 = flame_float_grid(mask, seed=0)
    r2 = flame_float_grid(mask, seed=999)
    # Flatten and compare
    flat1 = [v for row in r1 for v in row]
    flat2 = [v for row in r2 for v in row]
    assert flat1 != flat2


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("preset", ["default", "hot", "cool", "embers"])
def test_valid_presets(preset):
    mask = _simple_mask()
    result = flame_float_grid(mask, preset=preset, seed=0)
    assert len(result) == len(mask)


def test_invalid_preset_raises():
    mask = _simple_mask()
    with pytest.raises(ValueError, match="Unknown flame preset"):
        flame_float_grid(mask, preset="inferno", seed=0)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------
def test_empty_mask_returns_empty():
    result = flame_float_grid([], seed=0)
    assert result == []


def test_fully_exterior_mask():
    """All-zero mask — no ink cells, all values should be 0.0."""
    mask = [[0.0] * 5 for _ in range(5)]
    result = flame_float_grid(mask, seed=0)
    assert len(result) == 5
    for row in result:
        assert all(v == 0.0 for v in row)
