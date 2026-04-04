"""
Package: tests.test_cli
Tests for the JustDoIt CLI — argument parsing, new size/scale flags, output behaviour.

Covers:
  - Basic render (smoke test — renders without crashing)
  - --measure: prints dimensions and display fit table, exits 0
  - --target: parses display spec, prints sizing info to stderr
  - --target + --save-svg: auto-sizes SVG font from display spec
  - --svg-font-size: explicit SVG font size override
  - --fit: truncates text to fit column budget
  - --list-fonts / --list-colors: info flags exit cleanly
  - Error paths: unknown font, unknown fill, bad --target spec
"""

import logging as _logging
import os
import re
import sys
import tempfile
from io import StringIO
from unittest import mock

import pytest

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "tests.test_cli"
__updated__ = "2026-04-04 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
# Helper: invoke cli.main() with argv, capture stdout/stderr, return exit code

def _run(argv: list[str]) -> tuple[str, str, int]:
    """Run cli.main() with the given argv list.

    Captures stdout and stderr, swallows SystemExit.

    :param argv: Argument list (first element should be 'justdoit').
    :returns: (stdout_str, stderr_str, exit_code) tuple.
    """
    from justdoit.cli import main

    stdout_buf = StringIO()
    stderr_buf = StringIO()
    exit_code = 0

    with mock.patch("sys.argv", argv):
        with mock.patch("sys.stdout", stdout_buf):
            with mock.patch("sys.stderr", stderr_buf):
                try:
                    main()
                except SystemExit as e:
                    exit_code = int(e.code) if e.code is not None else 0

    return stdout_buf.getvalue(), stderr_buf.getvalue(), exit_code


# -------------------------------------------------------------------------
# Basic render

def test_cli_basic_render():
    """CLI renders text to stdout without error."""
    stdout, stderr, code = _run(["justdoit", "HI"])
    assert code == 0
    assert len(stdout) > 0
    # Block font renders visible characters
    assert any(c not in (" ", "\n") for c in stdout)


def test_cli_render_slim_font():
    """CLI renders with --font slim."""
    stdout, stderr, code = _run(["justdoit", "HI", "--font", "slim"])
    assert code == 0
    assert len(stdout) > 0


def test_cli_render_with_color():
    """CLI renders with --color cyan without error."""
    stdout, stderr, code = _run(["justdoit", "HI", "--color", "cyan"])
    assert code == 0
    # ANSI escape codes present
    assert "\033[" in stdout


def test_cli_render_with_fill():
    """CLI renders with --fill density without error."""
    stdout, stderr, code = _run(["justdoit", "HI", "--fill", "density"])
    assert code == 0
    assert len(stdout) > 0


def test_cli_no_args_exits_nonzero():
    """CLI with no arguments exits with non-zero code."""
    _, _, code = _run(["justdoit"])
    assert code != 0


# -------------------------------------------------------------------------
# --measure

def test_cli_measure_exits_zero():
    """--measure exits with code 0."""
    _, _, code = _run(["justdoit", "JUST DO IT", "--measure"])
    assert code == 0


def test_cli_measure_prints_dimensions():
    """--measure output contains 'cols x rows' line."""
    stdout, _, _ = _run(["justdoit", "JUST DO IT", "--measure"])
    assert "cols x" in stdout or "cols" in stdout
    assert "rows" in stdout


def test_cli_measure_prints_display_table():
    """--measure output includes display fit table with known display names."""
    stdout, _, _ = _run(["justdoit", "JUST DO IT", "--measure"])
    assert "4k" in stdout
    assert "fhd" in stdout
    assert "pt" in stdout


def test_cli_measure_does_not_render():
    """--measure exits before rendering — no block chars in stdout."""
    stdout, _, _ = _run(["justdoit", "JUST DO IT", "--measure"])
    # Block font uses these chars; they should NOT appear in measure output
    assert "█" not in stdout
    assert "██" not in stdout


def test_cli_measure_with_iso():
    """--measure with --iso accounts for isometric depth in dimensions."""
    stdout_plain, _, _ = _run(["justdoit", "HI", "--measure"])
    stdout_iso, _, _ = _run(["justdoit", "HI", "--measure", "--iso", "4"])
    # Extract col values from "N cols x M rows"
    def _extract_cols(s):
        m = re.search(r"(\d+)\s+cols", s)
        return int(m.group(1)) if m else None
    cols_plain = _extract_cols(stdout_plain)
    cols_iso = _extract_cols(stdout_iso)
    assert cols_plain is not None
    assert cols_iso is not None
    assert cols_iso > cols_plain


# -------------------------------------------------------------------------
# --target

def test_cli_target_renders_normally():
    """--target without --save-svg still renders ASCII art to stdout."""
    stdout, _, code = _run(["justdoit", "HI", "--target", "3840x2160"])
    assert code == 0
    assert len(stdout) > 0


def test_cli_target_prints_sizing_to_stderr():
    """--target outputs sizing info to stderr (not stdout)."""
    stdout, stderr, _ = _run(["justdoit", "HI", "--target", "3840x2160"])
    assert "Max font size" in stderr or "max" in stderr.lower()
    assert "pt" in stderr


def test_cli_target_info_not_in_stdout():
    """--target sizing info does NOT appear in stdout (should be stderr only)."""
    stdout, _, _ = _run(["justdoit", "HI", "--target", "3840x2160"])
    assert "Max font size" not in stdout


def test_cli_target_with_scaling():
    """--target with @Sx scaling suffix is accepted."""
    _, stderr, code = _run(["justdoit", "HI", "--target", "3840x2160@2.0x"])
    assert code == 0
    assert "2.0x" in stderr or "scaling" in stderr.lower()


def test_cli_target_invalid_spec_exits_nonzero():
    """Invalid --target spec exits with non-zero code and error to stderr."""
    _, stderr, code = _run(["justdoit", "HI", "--target", "notaresolution"])
    assert code != 0
    assert "Error" in stderr or "error" in stderr.lower()


# -------------------------------------------------------------------------
# --target + --save-svg (auto-size)

def test_cli_target_save_svg_auto_sizes_font():
    """--target + --save-svg produces SVG with font-size > 14 (auto-sized)."""
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        path = f.name
    try:
        _, _, code = _run(["justdoit", "HI", "--target", "3840x2160", "--save-svg", path])
        assert code == 0
        svg = open(path).read()
        # Extract font-size value
        m = re.search(r'font-size="(\d+)"', svg)
        assert m is not None, "No font-size found in SVG"
        font_size = int(m.group(1))
        assert font_size > 14, f"Expected auto-sized font > 14px, got {font_size}px"
    finally:
        os.unlink(path)


def test_cli_target_save_svg_uses_correct_font_size():
    """--target 3840x2160 produces SVG with font-size matching RenderTarget calculation."""
    from justdoit.layout import measure, RenderTarget
    cols, rows = measure("HI", font="block", gap=1)
    rt = RenderTarget(3840, 2160)
    expected_px = rt.svg_font_size_px(rt.max_font_pt(cols, rows))

    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        path = f.name
    try:
        _run(["justdoit", "HI", "--target", "3840x2160", "--save-svg", path])
        svg = open(path).read()
        m = re.search(r'font-size="(\d+)"', svg)
        assert m is not None
        assert int(m.group(1)) == expected_px
    finally:
        os.unlink(path)


# -------------------------------------------------------------------------
# --svg-font-size

def test_cli_svg_font_size_explicit():
    """--svg-font-size N produces SVG with exactly that font size."""
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        path = f.name
    try:
        _, _, code = _run(["justdoit", "HI", "--save-svg", path, "--svg-font-size", "72"])
        assert code == 0
        svg = open(path).read()
        m = re.search(r'font-size="(\d+)"', svg)
        assert m is not None
        assert int(m.group(1)) == 72
    finally:
        os.unlink(path)


def test_cli_svg_font_size_default():
    """--save-svg without --svg-font-size uses default 14px."""
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        path = f.name
    try:
        _run(["justdoit", "HI", "--save-svg", path])
        svg = open(path).read()
        m = re.search(r'font-size="(\d+)"', svg)
        assert m is not None
        assert int(m.group(1)) == 14
    finally:
        os.unlink(path)


def test_cli_svg_font_size_overrides_target():
    """--svg-font-size overrides --target auto-sizing."""
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        path = f.name
    try:
        _run(["justdoit", "HI", "--target", "3840x2160",
              "--save-svg", path, "--svg-font-size", "24"])
        svg = open(path).read()
        m = re.search(r'font-size="(\d+)"', svg)
        assert m is not None
        assert int(m.group(1)) == 24   # explicit wins over auto-sized
    finally:
        os.unlink(path)


def test_cli_svg_scales_canvas_with_font_size():
    """Larger --svg-font-size produces proportionally larger SVG canvas."""
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        path14 = f.name
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        path72 = f.name
    try:
        _run(["justdoit", "HI", "--save-svg", path14, "--svg-font-size", "14"])
        _run(["justdoit", "HI", "--save-svg", path72, "--svg-font-size", "72"])

        def _canvas(path):
            s = open(path).read()
            m = re.search(r'<svg [^>]*width="(\d+)" height="(\d+)"', s)
            return int(m.group(1)), int(m.group(2))

        w14, h14 = _canvas(path14)
        w72, h72 = _canvas(path72)
        assert w72 > w14
        assert h72 > h14
        # Ratio should be close to 72/14 = 5.14
        ratio = w72 / w14
        assert 4.5 < ratio < 5.8, f"Canvas width ratio {ratio:.2f} outside expected range"
    finally:
        os.unlink(path14)
        os.unlink(path72)


# -------------------------------------------------------------------------
# --fit

def test_cli_fit_renders_without_error():
    """--fit N renders without error."""
    stdout, stderr, code = _run(["justdoit", "JUST DO IT", "--fit", "80"])
    assert code == 0
    assert len(stdout) > 0


def test_cli_fit_truncates_wide_text():
    """--fit produces narrower output than unfit render for very wide text."""
    stdout_full, _, _ = _run(["justdoit", "JUST DO IT BUT MUCH LONGER", "--gap", "1"])
    stdout_fit, _, _ = _run(["justdoit", "JUST DO IT BUT MUCH LONGER", "--fit", "80", "--gap", "1"])

    def _max_line_width(s):
        # strip ANSI codes
        plain = re.sub(r"\033\[[0-9;]*m", "", s)
        return max((len(l) for l in plain.split("\n") if l), default=0)

    assert _max_line_width(stdout_fit) <= _max_line_width(stdout_full)


def test_cli_fit_note_goes_to_stderr():
    """--fit truncation note is written to stderr, not stdout."""
    stdout, stderr, _ = _run(
        ["justdoit", "JUST DO IT BUT MUCH LONGER TEXT HERE", "--fit", "40"]
    )
    # If truncation happened, note should be in stderr
    if "Note:" in stderr:
        assert "Note:" not in stdout


def test_cli_fit_already_fits_no_truncation():
    """--fit with a large budget doesn't truncate short text."""
    stdout_normal, _, _ = _run(["justdoit", "HI"])
    stdout_fit, _, _ = _run(["justdoit", "HI", "--fit", "200"])
    # Output should be identical (no truncation needed)
    assert stdout_normal == stdout_fit


# -------------------------------------------------------------------------
# --list-fonts / --list-colors

def test_cli_list_fonts_exits_zero():
    """--list-fonts exits with code 0."""
    _, _, code = _run(["justdoit", "--list-fonts"])
    assert code == 0


def test_cli_list_fonts_prints_block():
    """--list-fonts output includes 'block'."""
    stdout, _, _ = _run(["justdoit", "--list-fonts"])
    assert "block" in stdout


def test_cli_list_colors_exits_zero():
    """--list-colors exits with code 0."""
    _, _, code = _run(["justdoit", "--list-colors"])
    assert code == 0


def test_cli_list_colors_prints_cyan():
    """--list-colors output includes 'cyan'."""
    stdout, _, _ = _run(["justdoit", "--list-colors"])
    assert "cyan" in stdout


# -------------------------------------------------------------------------
# Error paths

def test_cli_unknown_font_exits_nonzero():
    """Unknown --font value exits with non-zero code."""
    _, _, code = _run(["justdoit", "HI", "--font", "nonexistent_font_xyz"])
    assert code != 0


def test_cli_unknown_fill_exits_nonzero():
    """Unknown --fill value exits with non-zero code."""
    _, _, code = _run(["justdoit", "HI", "--fill", "nonexistent_fill_xyz"])
    assert code != 0


def test_cli_save_svg_creates_file():
    """--save-svg creates a valid file on disk."""
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        path = f.name
    try:
        _, _, code = _run(["justdoit", "HI", "--save-svg", path])
        assert code == 0
        assert os.path.exists(path)
        content = open(path).read()
        assert content.startswith("<?xml")
    finally:
        os.unlink(path)
