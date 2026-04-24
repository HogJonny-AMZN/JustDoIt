"""
Tests for justdoit/fonts/ttf.py — TTF/PIL rasterizer (technique G02).

Tests that don't require PIL run unconditionally.
Tests that require PIL are skipped if PIL is not installed.
"""

import inspect
import sys
import os
import unittest.mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Detect PIL availability once
try:
    import PIL  # noqa: F401
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ---------------------------------------------------------------------------
# Tests that never require PIL
# ---------------------------------------------------------------------------

def test_find_system_fonts_returns_list():
    """find_system_fonts() must return a list (may be empty)."""
    from justdoit.fonts.ttf import find_system_fonts
    result = find_system_fonts()
    assert isinstance(result, list)


def test_require_pil_raises_if_missing():
    """_require_pil() raises ImportError with a helpful message when PIL absent."""
    from justdoit.fonts import ttf as ttf_module
    # Temporarily hide PIL from the module's import machinery
    with unittest.mock.patch.dict(sys.modules, {'PIL': None}):
        try:
            ttf_module._require_pil()
            assert False, "_require_pil() should have raised ImportError"
        except ImportError as exc:
            msg = str(exc)
            assert 'Pillow' in msg or 'pip' in msg, (
                f"Error message should mention Pillow/pip, got: {msg!r}"
            )


def test_rasterize_skips_gracefully_no_pil():
    """Importing the ttf module itself must not crash even without PIL."""
    # If we got here the import already succeeded (module-level code is safe)
    import justdoit.fonts.ttf  # noqa: F401  — just verify no crash


def test_load_ttf_font_signature():
    """load_ttf_font must accept (font_path, name=None, font_size=12)."""
    from justdoit.fonts.ttf import load_ttf_font
    sig = inspect.signature(load_ttf_font)
    params = list(sig.parameters)
    assert 'font_path' in params
    assert 'name' in params
    assert 'font_size' in params
    # name and font_size should have defaults
    assert sig.parameters['name'].default is None
    assert sig.parameters['font_size'].default == 12


# ---------------------------------------------------------------------------
# Tests that require PIL
# ---------------------------------------------------------------------------

def _find_test_font():
    """Return a font path suitable for testing, or None."""
    from justdoit.fonts.ttf import find_system_fonts
    fonts = find_system_fonts()
    return fonts[0] if fonts else None


if PIL_AVAILABLE:
    def test_rasterize_ttf_with_real_font():
        """rasterize_ttf() returns a non-empty dict with list-of-string values."""
        font_path = _find_test_font()
        if font_path is None:
            print("SKIP: no system fonts found")
            return
        from justdoit.fonts.ttf import rasterize_ttf
        result = rasterize_ttf(font_path, font_size=12, chars='ABC')
        assert isinstance(result, dict)
        assert len(result) > 0
        for ch, rows in result.items():
            assert isinstance(rows, list), f"Glyph for {ch!r} is not a list"
            for row in rows:
                assert isinstance(row, str), f"Row in glyph {ch!r} is not a str"

    def test_rasterize_consistent_height():
        """All glyphs from rasterize_ttf() must have the same number of rows."""
        font_path = _find_test_font()
        if font_path is None:
            print("SKIP: no system fonts found")
            return
        from justdoit.fonts.ttf import rasterize_ttf
        result = rasterize_ttf(font_path, font_size=12, chars='ABCDEFGHIJ')
        heights = {len(rows) for rows in result.values()}
        assert len(heights) == 1, f"Inconsistent glyph heights: {heights}"

    def test_render_with_ttf_font():
        """render() works end-to-end after loading a TTF font."""
        font_path = _find_test_font()
        if font_path is None:
            print("SKIP: no system fonts found")
            return
        from justdoit.fonts.ttf import load_ttf_font
        from justdoit.core.rasterizer import render
        name = load_ttf_font(font_path, font_size=12)
        result = render('HI', font=name)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_trimmed_height_less_than_font_size():
        """Trimmed glyphs should be shorter than font_size (blank rows removed)."""
        font_path = _find_test_font()
        if font_path is None:
            print("SKIP: no system fonts found")
            return
        from justdoit.fonts.ttf import rasterize_ttf
        fs = 50
        result = rasterize_ttf(font_path, font_size=fs, chars='ABCJ')
        height = len(result['A'])
        assert height < fs, f"Trimmed height {height} should be < font_size {fs}"

    def test_no_uniform_leading_blank_rows():
        """At least one glyph must have ink in the first row after trim."""
        font_path = _find_test_font()
        if font_path is None:
            print("SKIP: no system fonts found")
            return
        from justdoit.fonts.ttf import rasterize_ttf
        result = rasterize_ttf(font_path, font_size=50, chars='ABCJ')
        non_space = {ch: rows for ch, rows in result.items() if ch != ' '}
        has_ink_top = any(
            any(c != ' ' for c in rows[0]) for rows in non_space.values()
        )
        assert has_ink_top, "No glyph has ink in the first row — trim failed"

    def test_no_uniform_trailing_blank_rows():
        """At least one glyph must have ink in the last row after trim."""
        font_path = _find_test_font()
        if font_path is None:
            print("SKIP: no system fonts found")
            return
        from justdoit.fonts.ttf import rasterize_ttf
        result = rasterize_ttf(font_path, font_size=50, chars='ABCJ')
        non_space = {ch: rows for ch, rows in result.items() if ch != ' '}
        has_ink_bot = any(
            any(c != ' ' for c in rows[-1]) for rows in non_space.values()
        )
        assert has_ink_bot, "No glyph has ink in the last row — trim failed"

    def test_space_glyph_matches_trimmed_height():
        """Space glyph height must match other glyphs after trimming."""
        font_path = _find_test_font()
        if font_path is None:
            print("SKIP: no system fonts found")
            return
        from justdoit.fonts.ttf import rasterize_ttf
        result = rasterize_ttf(font_path, font_size=50, chars='ABCJ ')
        heights = {len(rows) for rows in result.values()}
        assert len(heights) == 1, f"Inconsistent heights after trim: {heights}"
