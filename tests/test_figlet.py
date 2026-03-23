import sys
import os
import glob

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from justdoit.fonts.figlet import parse_flf
from justdoit.core.rasterizer import render

_FONTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'justdoit', 'fonts', 'figlet_fonts')
_BIG_FLF = os.path.join(_FONTS_DIR, 'big.flf')


def test_parse_flf_returns_dict():
    font = parse_flf(_BIG_FLF)
    assert isinstance(font, dict)


def test_parse_flf_has_alphabet():
    font = parse_flf(_BIG_FLF)
    for ch in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        assert ch in font, f"Missing char '{ch}' in parsed font"


def test_parse_flf_consistent_height():
    font = parse_flf(_BIG_FLF)
    heights = {len(glyph) for glyph in font.values()}
    assert len(heights) == 1, f"Inconsistent glyph heights: {heights}"


def test_figlet_font_renders():
    result = render('HI', font='big')
    assert isinstance(result, str)
    assert len(result) > 0


def test_figlet_font_differs_from_block():
    big_out = render('HI', font='big')
    block_out = render('HI', font='block')
    assert big_out != block_out


def test_all_bundled_figlet_fonts_load():
    flf_files = glob.glob(os.path.join(_FONTS_DIR, '*.flf'))
    assert len(flf_files) > 0, "No .flf files found in figlet_fonts/"
    for path in flf_files:
        font = parse_flf(path)
        assert isinstance(font, dict), f"parse_flf returned non-dict for {path}"
        assert len(font) > 0, f"Empty font dict for {path}"
