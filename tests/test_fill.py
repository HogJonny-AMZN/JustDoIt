import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from justdoit.core.glyph import glyph_to_mask, mask_to_sdf
from justdoit.effects.fill import density_fill, sdf_fill
from justdoit.core.rasterizer import render

# A simple 3-row glyph: a filled 4x3 block with hollow center
_TEST_GLYPH = [
    "████",
    "█  █",
    "████",
]


def test_glyph_to_mask_shape():
    mask = glyph_to_mask(_TEST_GLYPH)
    assert len(mask) == 3
    assert all(len(row) == 4 for row in mask)


def test_glyph_to_mask_values():
    mask = glyph_to_mask(_TEST_GLYPH)
    # Row 0: all ink
    assert mask[0] == [1.0, 1.0, 1.0, 1.0]
    # Row 1: ink, space, space, ink
    assert mask[1][0] == 1.0
    assert mask[1][1] == 0.0
    assert mask[1][2] == 0.0
    assert mask[1][3] == 1.0
    # Row 2: all ink
    assert mask[2] == [1.0, 1.0, 1.0, 1.0]


def test_mask_to_sdf_range():
    mask = glyph_to_mask(_TEST_GLYPH)
    sdf = mask_to_sdf(mask)
    for row in sdf:
        for val in row:
            assert 0.0 <= val <= 1.0, f"SDF value {val} out of range"


def test_density_fill_output_shape():
    mask = glyph_to_mask(_TEST_GLYPH)
    filled = density_fill(mask)
    assert len(filled) == len(_TEST_GLYPH)
    for orig_row, filled_row in zip(_TEST_GLYPH, filled):
        assert len(filled_row) == len(orig_row)


def test_density_fill_no_spaces_inside():
    # Use a fully solid glyph — all cells should map to non-space chars.
    solid = ["████", "████", "████"]
    mask = glyph_to_mask(solid)
    filled = density_fill(mask)
    for row in filled:
        assert ' ' not in row, f"Space found in solid fill row: {row!r}"


def test_render_with_fill():
    result = render('HI', fill='density')
    assert isinstance(result, str)
    assert len(result) > 0


def test_render_fill_vs_default():
    default_out = render('HI')
    density_out = render('HI', fill='density')
    assert default_out != density_out
