"""Tests for C13 apply_tone_curve() in justdoit/effects/color.py."""
import pytest
from justdoit.effects.color import apply_tone_curve, C13_CURVES


def _make_grid(values):
    """Helper: wrap a flat list into a 1-row 2D grid."""
    return [values]


# ---------------------------------------------------------------------------
# C13_CURVES constant
# ---------------------------------------------------------------------------
def test_c13_curves_constant():
    assert "linear" in C13_CURVES
    assert "reinhard" in C13_CURVES
    assert "aces" in C13_CURVES
    assert "blown_out" in C13_CURVES


# ---------------------------------------------------------------------------
# linear — identity
# ---------------------------------------------------------------------------
def test_linear_is_identity():
    grid = [[0.0, 0.25, 0.5, 0.75, 1.0]]
    result = apply_tone_curve(grid, "linear")
    assert result == grid


def test_linear_clamps_above_one():
    grid = [[1.5, 2.0]]
    result = apply_tone_curve(grid, "linear")
    assert result == [[1.0, 1.0]]


def test_linear_clamps_below_zero():
    grid = [[-0.5, -1.0]]
    result = apply_tone_curve(grid, "linear")
    assert result == [[0.0, 0.0]]


# ---------------------------------------------------------------------------
# reinhard — soft rolloff
# ---------------------------------------------------------------------------
def test_reinhard_output_less_than_input():
    grid = [[0.1, 0.3, 0.5, 0.7, 0.9]]
    result = apply_tone_curve(grid, "reinhard")
    for orig, remapped in zip(grid[0], result[0]):
        if orig > 0.0:
            assert remapped < orig, f"reinhard({orig}) = {remapped} should be < {orig}"


def test_reinhard_zero_maps_to_zero():
    result = apply_tone_curve([[0.0]], "reinhard")
    assert result[0][0] == 0.0


def test_reinhard_output_in_range():
    grid = [[i / 10 for i in range(11)]]
    result = apply_tone_curve(grid, "reinhard")
    for v in result[0]:
        assert 0.0 <= v <= 1.0


# ---------------------------------------------------------------------------
# aces — cinematic curve
# ---------------------------------------------------------------------------
def test_aces_output_in_range():
    grid = [[i / 10 for i in range(11)]]
    result = apply_tone_curve(grid, "aces")
    for v in result[0]:
        assert 0.0 <= v <= 1.0, f"aces output {v} out of range"


def test_aces_zero_maps_near_zero():
    result = apply_tone_curve([[0.0]], "aces")
    assert result[0][0] < 0.1


def test_aces_one_maps_near_one():
    # ACES Hill approximation: t=1.0 maps to ~0.80 (cinematic rolloff, not linear).
    # The output is in [0.0, 1.0] and is reasonably high — just not 1.0.
    result = apply_tone_curve([[1.0]], "aces")
    assert result[0][0] > 0.7


# ---------------------------------------------------------------------------
# blown_out — threshold behaviour
# ---------------------------------------------------------------------------
def test_blown_out_above_threshold_maps_to_one():
    # Default threshold = 0.7; value 0.8 → 1.0
    result = apply_tone_curve([[0.8]], "blown_out")
    assert result[0][0] == 1.0


def test_blown_out_at_threshold_maps_to_one():
    result = apply_tone_curve([[0.7]], "blown_out")
    assert result[0][0] == 1.0


def test_blown_out_below_threshold_scales_linearly():
    # 0.5 / 0.7 ≈ 0.7143
    result = apply_tone_curve([[0.5]], "blown_out")
    expected = 0.5 / 0.7
    assert abs(result[0][0] - expected) < 1e-6


def test_blown_out_zero_maps_to_zero():
    result = apply_tone_curve([[0.0]], "blown_out")
    assert result[0][0] == 0.0


# ---------------------------------------------------------------------------
# blown_out:N threshold suffix parsing
# ---------------------------------------------------------------------------
def test_blown_out_custom_threshold_parses():
    # blown_out:0.5 — value 0.6 → 1.0, value 0.3 → 0.3/0.5 = 0.6
    result = apply_tone_curve([[0.6, 0.3]], "blown_out:0.5")
    assert result[0][0] == 1.0
    assert abs(result[0][1] - 0.6) < 1e-6


def test_blown_out_custom_threshold_low():
    # blown_out:0.3 — value 0.5 → 1.0
    result = apply_tone_curve([[0.5]], "blown_out:0.3")
    assert result[0][0] == 1.0


def test_blown_out_threshold_clamped():
    # Threshold > 1.0 should clamp to 1.0 (no blow-out ever)
    result = apply_tone_curve([[0.8]], "blown_out:2.0")
    assert result[0][0] < 1.0  # 0.8 / 1.0 = 0.8 (not blown out)


# ---------------------------------------------------------------------------
# invalid curve raises ValueError
# ---------------------------------------------------------------------------
def test_invalid_curve_raises():
    with pytest.raises(ValueError, match="Unknown tone curve"):
        apply_tone_curve([[0.5]], "gamma")


def test_invalid_curve_prefix_raises():
    with pytest.raises(ValueError):
        apply_tone_curve([[0.5]], "nonexistent:0.5")


# ---------------------------------------------------------------------------
# output always in [0.0, 1.0]
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("curve", ["linear", "reinhard", "aces", "blown_out"])
def test_output_always_in_range(curve):
    # Include out-of-range inputs to test clamping
    grid = [[-1.0, 0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0]]
    result = apply_tone_curve(grid, curve)
    for v in result[0]:
        assert 0.0 <= v <= 1.0, f"curve={curve} produced out-of-range value {v}"


# ---------------------------------------------------------------------------
# 2D grid shape preserved
# ---------------------------------------------------------------------------
def test_shape_preserved_multi_row():
    grid = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
        [0.7, 0.8, 0.9],
    ]
    for curve in C13_CURVES:
        result = apply_tone_curve(grid, curve)
        assert len(result) == len(grid)
        for orig_row, out_row in zip(grid, result):
            assert len(out_row) == len(orig_row)


def test_empty_grid_returns_empty():
    assert apply_tone_curve([], "linear") == []


def test_empty_rows_preserved():
    grid = [[], [0.5, 0.5], []]
    result = apply_tone_curve(grid, "reinhard")
    assert len(result) == 3
    assert result[0] == []
    assert result[2] == []
