"""
Package: tests.test_gallery_profiles
Tests for gallery profile infrastructure in scripts/generate_gallery.py.

Covers:
  - GalleryProfile dataclass field values
  - PROFILES dict contents and correctness
  - _validate_text() — raises on empty, warns on wide
  - _generate_for_profile() — creates SVGs and README at correct font size
  - SVG font-size scales linearly across profiles
  - Profile output directories are separate
"""

import logging
import logging as _logging
import re
import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

import pytest

# -------------------------------------------------------------------------
# module global scope — import gallery script components
# generate_gallery.py is a script, not a package; import via sys.path

import importlib.util
import os

_SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "generate_gallery.py"

# Load the module under a stable name
_spec = importlib.util.spec_from_file_location("generate_gallery", _SCRIPT_PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

GalleryProfile = _mod.GalleryProfile
PROFILES = _mod.PROFILES
_validate_text = _mod._validate_text
_generate_for_profile = _mod._generate_for_profile

_MODULE_NAME = "tests.test_gallery_profiles"
__updated__ = "2026-04-04 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
# GalleryProfile dataclass

def test_gallery_profile_standard_values():
    """Standard profile has correct svg_font_size and readme_img_width."""
    p = PROFILES["standard"]
    assert p.svg_font_size == 14
    assert p.readme_img_width == 480
    assert p.name == "standard"


def test_gallery_profile_wide_values():
    """Wide profile has correct svg_font_size and readme_img_width."""
    p = PROFILES["wide"]
    assert p.svg_font_size == 28
    assert p.readme_img_width == 800
    assert p.name == "wide"


def test_gallery_profile_4k_values():
    """4k profile has correct svg_font_size and readme_img_width."""
    p = PROFILES["4k"]
    assert p.svg_font_size == 72
    assert p.readme_img_width == 1600
    assert p.name == "4k"


def test_gallery_profiles_all_present():
    """All three expected profiles exist in PROFILES dict."""
    assert "standard" in PROFILES
    assert "wide" in PROFILES
    assert "4k" in PROFILES


def test_gallery_profile_font_sizes_ordered():
    """Profile svg_font_sizes increase: standard < wide < 4k."""
    assert PROFILES["standard"].svg_font_size < PROFILES["wide"].svg_font_size
    assert PROFILES["wide"].svg_font_size < PROFILES["4k"].svg_font_size


def test_gallery_profile_img_widths_ordered():
    """Profile readme_img_widths increase: standard < wide < 4k."""
    assert PROFILES["standard"].readme_img_width < PROFILES["wide"].readme_img_width
    assert PROFILES["wide"].readme_img_width < PROFILES["4k"].readme_img_width


def test_gallery_profile_output_dirs_differ():
    """Each profile has a distinct output directory."""
    dirs = [p.output_dir for p in PROFILES.values()]
    assert len(set(dirs)) == len(dirs), "All profile output_dirs must be unique"


def test_gallery_profile_default_text():
    """All profiles default to 'JUST DO IT' as render text."""
    for profile in PROFILES.values():
        assert profile.text == "JUST DO IT"


def test_gallery_profile_is_dataclass():
    """GalleryProfile is a dataclass with expected fields."""
    import dataclasses
    fields = {f.name for f in dataclasses.fields(GalleryProfile)}
    assert "name" in fields
    assert "svg_font_size" in fields
    assert "readme_img_width" in fields
    assert "output_dir" in fields
    assert "text" in fields


# -------------------------------------------------------------------------
# _validate_text()

def test_validate_text_valid_input():
    """_validate_text does not raise or warn for normal text."""
    stderr_buf = StringIO()
    with mock.patch("sys.stderr", stderr_buf):
        _validate_text("JUST DO IT")
    assert stderr_buf.getvalue() == ""


def test_validate_text_empty_raises():
    """_validate_text raises ValueError for text that produces 0 columns."""
    # An empty string produces cols=0
    with pytest.raises(ValueError, match="empty output"):
        _validate_text("")


def test_validate_text_wide_warns():
    """_validate_text warns to stderr for text rendering > 400 columns."""
    # Build a string wide enough to exceed 400 cols at block font
    # block font: each char ~6-7 cols + gap, so ~60 chars needed
    wide_text = "A" * 70
    stderr_buf = StringIO()
    with mock.patch("sys.stderr", stderr_buf):
        _validate_text(wide_text)
    assert "Warning" in stderr_buf.getvalue() or "warning" in stderr_buf.getvalue().lower()


# -------------------------------------------------------------------------
# _generate_for_profile() — SVG font size in output

def test_generate_for_profile_creates_svgs():
    """_generate_for_profile creates SVG files in the profile output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        profile = GalleryProfile(
            name="test",
            svg_font_size=14,
            readme_img_width=480,
            output_dir=Path(tmpdir),
        )
        _generate_for_profile(profile, "HI")
        svgs = list(Path(tmpdir).glob("*.svg"))
        assert len(svgs) > 0, "Expected at least one SVG file"


def test_generate_for_profile_svgs_have_correct_font_size():
    """_generate_for_profile produces SVGs with the profile's svg_font_size."""
    with tempfile.TemporaryDirectory() as tmpdir:
        profile = GalleryProfile(
            name="test",
            svg_font_size=28,
            readme_img_width=800,
            output_dir=Path(tmpdir),
        )
        _generate_for_profile(profile, "HI")
        svgs = list(Path(tmpdir).glob("*.svg"))
        assert svgs, "No SVGs generated"
        # Check first SVG for correct font size
        svg_content = svgs[0].read_text()
        m = re.search(r'font-size="(\d+)"', svg_content)
        assert m is not None, f"No font-size found in {svgs[0].name}"
        assert int(m.group(1)) == 28, f"Expected font-size 28, got {m.group(1)}"


def test_generate_for_profile_creates_readme():
    """_generate_for_profile creates a README.md in the output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        profile = GalleryProfile(
            name="test",
            svg_font_size=14,
            readme_img_width=480,
            output_dir=Path(tmpdir),
        )
        _generate_for_profile(profile, "HI")
        readme = Path(tmpdir) / "README.md"
        assert readme.exists(), "README.md not created"
        assert readme.stat().st_size > 0


def test_generate_for_profile_readme_uses_img_width():
    """README.md contains the profile's readme_img_width in img tags."""
    with tempfile.TemporaryDirectory() as tmpdir:
        profile = GalleryProfile(
            name="test",
            svg_font_size=14,
            readme_img_width=999,   # distinctive value
            output_dir=Path(tmpdir),
        )
        _generate_for_profile(profile, "HI")
        readme = (Path(tmpdir) / "README.md").read_text()
        assert 'width="999"' in readme, "README does not use profile's readme_img_width"


def test_generate_for_profile_72px_canvas_larger_than_14px():
    """4k profile (72px) produces larger SVG canvas than standard (14px)."""
    with tempfile.TemporaryDirectory() as tmpdir14:
        with tempfile.TemporaryDirectory() as tmpdir72:
            p14 = GalleryProfile("std", 14, 480, Path(tmpdir14))
            p72 = GalleryProfile("4k",  72, 1600, Path(tmpdir72))
            _generate_for_profile(p14, "HI")
            _generate_for_profile(p72, "HI")

            def _get_canvas(dirpath):
                svgs = list(Path(dirpath).glob("S-F00*.svg"))
                if not svgs:
                    svgs = list(Path(dirpath).glob("*.svg"))
                assert svgs, f"No SVGs found in {dirpath}"
                s = svgs[0].read_text()
                m = re.search(r'<svg [^>]*width="(\d+)" height="(\d+)"', s)
                return int(m.group(1)), int(m.group(2))

            w14, h14 = _get_canvas(tmpdir14)
            w72, h72 = _get_canvas(tmpdir72)
            assert w72 > w14, f"72px canvas ({w72}px) not wider than 14px canvas ({w14}px)"
            assert h72 > h14


# -------------------------------------------------------------------------
# SVG output targets — font_size parameter (test_output_targets.py extension)

def test_to_svg_font_size_14():
    """to_svg() at font_size=14 produces small canvas."""
    from justdoit.output.svg import to_svg
    from justdoit.core.rasterizer import render
    plain = render("HI", font="block")
    svg = to_svg(plain, font_size=14)
    m = re.search(r'font-size="(\d+)"', svg)
    assert m and int(m.group(1)) == 14


def test_to_svg_font_size_72():
    """to_svg() at font_size=72 produces larger canvas than font_size=14."""
    from justdoit.output.svg import to_svg
    from justdoit.core.rasterizer import render
    plain = render("HI", font="block")
    svg14 = to_svg(plain, font_size=14)
    svg72 = to_svg(plain, font_size=72)

    def _width(svg):
        m = re.search(r'<svg [^>]*width="(\d+)"', svg)
        return int(m.group(1))

    assert _width(svg72) > _width(svg14)


def test_save_svg_font_size_explicit(tmp_path):
    """save_svg() with explicit font_size writes correct value to file."""
    from justdoit.output.svg import save_svg
    from justdoit.core.rasterizer import render
    plain = render("HI", font="block")
    out = tmp_path / "test.svg"
    save_svg(plain, str(out), font_size=48)
    svg = out.read_text()
    m = re.search(r'font-size="(\d+)"', svg)
    assert m and int(m.group(1)) == 48


def test_save_svg_default_font_size(tmp_path):
    """save_svg() without font_size uses 14px default."""
    from justdoit.output.svg import save_svg
    from justdoit.core.rasterizer import render
    plain = render("HI", font="block")
    out = tmp_path / "test.svg"
    save_svg(plain, str(out))
    svg = out.read_text()
    m = re.search(r'font-size="(\d+)"', svg)
    assert m and int(m.group(1)) == 14


def test_svg_canvas_scales_proportionally(tmp_path):
    """SVG canvas width/height scale proportionally with font_size."""
    from justdoit.output.svg import to_svg
    from justdoit.core.rasterizer import render
    plain = render("HI", font="block")

    def _dims(fs):
        svg = to_svg(plain, font_size=fs)
        m = re.search(r'<svg [^>]*width="(\d+)" height="(\d+)"', svg)
        return int(m.group(1)), int(m.group(2))

    w14, h14 = _dims(14)
    w28, h28 = _dims(28)
    w72, h72 = _dims(72)

    # Each doubling of font_size should ~double canvas dimensions
    assert w28 > w14
    assert w72 > w28
    assert h28 > h14
    assert h72 > h28

    # Ratio check: 28/14 ≈ 2.0, 72/14 ≈ 5.14
    ratio_28_14 = w28 / w14
    ratio_72_14 = w72 / w14
    assert 1.8 < ratio_28_14 < 2.3, f"28px/14px ratio {ratio_28_14:.2f} out of range"
    assert 4.5 < ratio_72_14 < 5.8, f"72px/14px ratio {ratio_72_14:.2f} out of range"
