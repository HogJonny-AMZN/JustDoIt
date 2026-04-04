"""
Package: tests.test_layout
Tests for layout primitives — measure(), RenderTarget, fit_text(), terminal_size().

Covers: measure() correctness vs. actual render() output, RenderTarget arithmetic,
DISPLAYS presets, fit_text() truncation, terminal_size() fallback.
All tests are pure Python — no PIL dependency.
"""

import logging as _logging

import pytest

from justdoit.layout import (
    DISPLAYS,
    RenderTarget,
    fit_text,
    measure,
    terminal_size,
)

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "tests.test_layout"
__updated__ = "2026-04-04 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
# measure() — basic correctness

def test_measure_known_output():
    """measure() dimensions match actual render() output for block font."""
    from justdoit.core.rasterizer import render
    result = render("JUST DO IT", font="block", gap=1)
    lines = result.split("\n")
    actual_cols = max(len(l) for l in lines)
    actual_rows = len(lines)
    cols, rows = measure("JUST DO IT", font="block", gap=1)
    assert cols == actual_cols
    assert rows == actual_rows


def test_measure_empty():
    """Empty string returns (0, font_height) — block font is 7 rows tall."""
    cols, rows = measure("", font="block", gap=1)
    assert cols == 0
    assert rows == 7


def test_measure_single_char():
    """Single character returns positive cols and correct font height."""
    cols, rows = measure("A", font="block", gap=1)
    assert cols > 0
    assert rows == 7


def test_measure_gap_zero():
    """Gap=0 produces fewer columns than gap=1 for multi-char text."""
    cols_gap1, _ = measure("HI", font="block", gap=1)
    cols_gap0, _ = measure("HI", font="block", gap=0)
    assert cols_gap0 < cols_gap1


def test_measure_iso_depth():
    """iso_depth expands both cols and rows by the exact depth value."""
    base_cols, base_rows = measure("HI", font="block", gap=1)
    iso_cols, iso_rows = measure("HI", font="block", gap=1, iso_depth=4)
    assert iso_cols == base_cols + 4
    assert iso_rows == base_rows + 4


def test_measure_bloom():
    """bloom_radius expands both cols and rows by 2× the radius (both sides)."""
    base_cols, base_rows = measure("HI", font="block", gap=1)
    bloom_cols, bloom_rows = measure("HI", font="block", gap=1, bloom_radius=4)
    assert bloom_cols == base_cols + 8
    assert bloom_rows == base_rows + 8


def test_measure_figlet():
    """measure() matches render() output for a FIGlet font (slant)."""
    from justdoit.core.rasterizer import render
    cols, rows = measure("JUST DO IT", font="slant", gap=1)
    result = render("JUST DO IT", font="slant", gap=1)
    lines = result.split("\n")
    assert cols == max(len(l) for l in lines)


def test_measure_unknown_font():
    """Unknown font name raises ValueError."""
    with pytest.raises(ValueError):
        measure("HI", font="nonexistent_font")


def test_measure_warp_amplitude():
    """warp_amplitude > 0 expands cols by int(amplitude) + 1."""
    base_cols, base_rows = measure("HI", font="block", gap=1)
    warp_cols, warp_rows = measure("HI", font="block", gap=1, warp_amplitude=3.0)
    assert warp_cols == base_cols + int(3.0) + 1
    assert warp_rows == base_rows  # rows unaffected by warp


def test_measure_space_character():
    """Space character is measured using the space glyph width."""
    cols, rows = measure(" ", font="block", gap=1)
    assert cols > 0
    assert rows == 7


def test_measure_gap_matches_rasterizer_trailing():
    """measure() matches render() including rasterizer's trailing gap behavior."""
    # The rasterizer appends `row + spacer` unconditionally (including the last char),
    # so measure() must include the trailing gap to match actual render output.
    from justdoit.core.rasterizer import render
    for gap in (0, 1, 3):
        result = render("A", font="block", gap=gap)
        lines = result.split("\n")
        actual = max(len(l) for l in lines)
        cols, _ = measure("A", font="block", gap=gap)
        assert cols == actual, f"measure('A', gap={gap})={cols} != render width={actual}"


# -------------------------------------------------------------------------
# RenderTarget

def test_render_target_cell_size():
    """cell_size_px(12) at 96dpi returns 16.0px height, 9.6px width."""
    rt = RenderTarget(3840, 2160, dpi=96.0, scaling=1.0)
    cell_w, cell_h = rt.cell_size_px(12)
    assert abs(cell_h - 16.0) < 0.1    # 12pt * 96/72 = 16px
    assert abs(cell_w - 9.6) < 0.1    # 16px * 0.6


def test_render_target_max_columns():
    """max_columns(12) at 4K resolution matches expected integer division."""
    rt = RenderTarget(3840, 2160)
    cols = rt.max_columns(12)
    assert cols == int(3840 / 9.6)  # 400


def test_render_target_max_rows():
    """max_rows(12) at 4K resolution matches expected integer division."""
    rt = RenderTarget(3840, 2160)
    rows = rt.max_rows(12)
    assert rows == int(2160 / 16.0)  # 135


def test_render_target_max_font_pt():
    """max_font_pt returns a reasonable value for 'JUST DO IT' on 4K."""
    rt = RenderTarget(3840, 2160)
    cols, rows = measure("JUST DO IT", font="block", gap=1)
    pt = rt.max_font_pt(cols, rows)
    # With trailing gap included (rasterizer behavior), cols=64 rows=7.
    # At 4K 96dpi: pt=75 is the last size where 3840/cell_w >= 64.
    assert 60 <= pt <= 80


def test_render_target_hidpi():
    """HiDPI (scaling=2.0) yields a smaller max font pt than 100% scaling."""
    rt_100 = RenderTarget(3840, 2160, scaling=1.0)
    rt_200 = RenderTarget(3840, 2160, scaling=2.0)
    pt_100 = rt_100.max_font_pt(76, 19)
    pt_200 = rt_200.max_font_pt(76, 19)
    assert pt_200 < pt_100  # higher DPI scaling = smaller max pt


def test_render_target_effective_dpi():
    """effective_dpi = dpi * scaling."""
    rt = RenderTarget(1920, 1080, dpi=96.0, scaling=2.0)
    assert rt.effective_dpi == 192.0


def test_render_target_svg_font_size_px():
    """svg_font_size_px converts points to pixels using effective DPI."""
    rt = RenderTarget(3840, 2160, dpi=96.0, scaling=1.0)
    px = rt.svg_font_size_px(12)
    # 12pt * (96/72) = 16px
    assert px == 16


def test_render_target_from_string_basic():
    """from_string parses 'WxH' format correctly."""
    rt = RenderTarget.from_string("3840x2160")
    assert rt.display_w == 3840
    assert rt.display_h == 2160
    assert rt.scaling == 1.0


def test_render_target_from_string_with_scaling():
    """from_string parses 'WxH@Sx' scaling suffix."""
    rt = RenderTarget.from_string("3840x2160@2.0x")
    assert rt.display_w == 3840
    assert rt.display_h == 2160
    assert rt.scaling == 2.0


def test_render_target_from_string_fhd():
    """from_string handles FHD resolution."""
    rt = RenderTarget.from_string("1920x1080")
    assert rt.display_w == 1920
    assert rt.display_h == 1080


def test_render_target_from_string_invalid():
    """from_string raises ValueError for invalid format."""
    with pytest.raises(ValueError):
        RenderTarget.from_string("notaresolution")


def test_render_target_from_string_invalid_partial():
    """from_string raises ValueError for partial/malformed spec."""
    with pytest.raises(ValueError):
        RenderTarget.from_string("3840x")


def test_render_target_from_string_kwargs_passed():
    """from_string passes extra kwargs (e.g. dpi) to RenderTarget."""
    rt = RenderTarget.from_string("3840x2160", dpi=120.0)
    assert rt.dpi == 120.0


def test_render_target_fit_font_pt():
    """fit_font_pt wraps measure() + max_font_pt() correctly."""
    rt = RenderTarget(3840, 2160)
    pt_direct = rt.max_font_pt(*measure("JUST DO IT", font="block", gap=1))
    pt_via_fit = rt.fit_font_pt("JUST DO IT", font="block", gap=1)
    assert pt_direct == pt_via_fit


# -------------------------------------------------------------------------
# DISPLAYS presets

def test_displays_preset_4k():
    """DISPLAYS['4k'] has correct 4K resolution."""
    rt = DISPLAYS["4k"]
    assert rt.display_w == 3840
    assert rt.display_h == 2160


def test_displays_preset_fhd():
    """DISPLAYS['fhd'] has correct FHD resolution."""
    rt = DISPLAYS["fhd"]
    assert rt.display_w == 1920
    assert rt.display_h == 1080


def test_displays_preset_4k_hidpi():
    """DISPLAYS['4k-hidpi'] has scaling=2.0."""
    rt = DISPLAYS["4k-hidpi"]
    assert rt.display_w == 3840
    assert rt.scaling == 2.0


def test_displays_all_presets_exist():
    """All expected DISPLAYS presets are present."""
    expected = {"fhd", "qhd", "4k", "5k", "ultrawide", "4k-hidpi", "fhd-hidpi"}
    assert expected.issubset(set(DISPLAYS.keys()))


# -------------------------------------------------------------------------
# fit_text()

def test_fit_text_already_fits():
    """Short text that fits returns unchanged with correct col count."""
    text, cols = fit_text("HI", target_cols=200)
    assert text == "HI"
    assert cols <= 200


def test_fit_text_truncates():
    """Wide text is truncated to fit within target_cols."""
    text, cols = fit_text("JUST DO IT", target_cols=30, font="block")
    assert cols <= 30
    assert len(text) < len("JUST DO IT")


def test_fit_text_no_truncate_raises():
    """truncate=False raises ValueError when text exceeds target_cols."""
    with pytest.raises(ValueError):
        fit_text("JUST DO IT", target_cols=10, font="block", truncate=False)


def test_fit_text_suffix_included_in_width():
    """Truncation suffix is included in the final column measurement."""
    text, cols = fit_text("JUST DO IT", target_cols=40, font="block", truncation_suffix="...")
    assert cols <= 40


def test_fit_text_suffix_present_when_truncated():
    """Truncated result ends with the truncation suffix."""
    text, cols = fit_text("JUST DO IT", target_cols=30, font="block", truncation_suffix="...")
    assert text.endswith("...")


def test_fit_text_custom_suffix():
    """Custom truncation suffix appears at end of truncated text."""
    text, cols = fit_text("JUST DO IT", target_cols=30, font="block", truncation_suffix="~")
    assert text.endswith("~")
    assert cols <= 30


def test_fit_text_returns_tuple():
    """fit_text always returns a (str, int) tuple."""
    result = fit_text("HI", target_cols=200)
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], str)
    assert isinstance(result[1], int)


# -------------------------------------------------------------------------
# terminal_size()

def test_terminal_size_fallback():
    """terminal_size() returns valid (cols, rows) — at least the 80x24 fallback."""
    cols, rows = terminal_size()
    assert cols >= 1
    assert rows >= 1


def test_terminal_size_returns_tuple():
    """terminal_size() returns a (int, int) tuple."""
    result = terminal_size()
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], int)
    assert isinstance(result[1], int)


def test_terminal_size_fallback_values(monkeypatch):
    """terminal_size() returns (80, 24) when os.get_terminal_size raises OSError."""
    import os

    def _raise_oserror(*args, **kwargs):
        raise OSError("no tty")

    monkeypatch.setattr(os, "get_terminal_size", _raise_oserror)
    cols, rows = terminal_size()
    assert cols == 80
    assert rows == 24


# -------------------------------------------------------------------------
# fit_ttf_size() — requires Pillow

def test_fit_ttf_size_returns_int():
    """fit_ttf_size() returns an integer font size."""
    pytest.importorskip("PIL")
    ttf = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    import os
    if not os.path.isfile(ttf):
        pytest.skip("DejaVuSans.ttf not found on this system")
    from justdoit.layout import fit_ttf_size
    result = fit_ttf_size("HI", target_cols=200, font_path=ttf)
    assert isinstance(result, int)
    assert result > 0


def test_fit_ttf_size_output_fits_target():
    """fit_ttf_size() result produces render <= target_cols."""
    pytest.importorskip("PIL")
    ttf = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    import os
    if not os.path.isfile(ttf):
        pytest.skip("DejaVuSans.ttf not found on this system")
    from justdoit.layout import fit_ttf_size
    from justdoit.fonts.ttf import load_ttf_font
    target = 300
    size = fit_ttf_size("JUST DO IT", target_cols=target, font_path=ttf)
    fname = load_ttf_font(ttf, font_size=size)
    cols, _ = measure("JUST DO IT", font=fname, gap=1)
    assert cols <= target, f"render cols={cols} exceeds target={target}"


def test_fit_ttf_size_larger_than_min():
    """fit_ttf_size() returns a size >= size_min."""
    pytest.importorskip("PIL")
    ttf = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    import os
    if not os.path.isfile(ttf):
        pytest.skip("DejaVuSans.ttf not found on this system")
    from justdoit.layout import fit_ttf_size
    size = fit_ttf_size("HI", target_cols=500, font_path=ttf, size_min=12)
    assert size >= 12


def test_fit_ttf_size_larger_target_gives_larger_size():
    """Larger target_cols produces larger or equal TTF size."""
    pytest.importorskip("PIL")
    ttf = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    import os
    if not os.path.isfile(ttf):
        pytest.skip("DejaVuSans.ttf not found on this system")
    from justdoit.layout import fit_ttf_size
    size_small = fit_ttf_size("JUST DO IT", target_cols=150, font_path=ttf)
    size_large = fit_ttf_size("JUST DO IT", target_cols=400, font_path=ttf)
    assert size_large >= size_small


def test_find_default_ttf():
    """find_default_ttf() returns None or a valid file path."""
    from justdoit.layout import find_default_ttf
    import os
    result = find_default_ttf()
    if result is not None:
        assert os.path.isfile(result), f"find_default_ttf returned non-existent path: {result}"
