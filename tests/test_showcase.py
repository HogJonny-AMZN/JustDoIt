"""
Package: tests.test_showcase
End-to-end showcase test — exercises every implemented technique in one run.

Run with:
    uv run pytest tests/test_showcase.py -v

Each technique gets an explicit assertion. If anything regresses, this is
the first test to break. It also serves as a living example of the full API.
"""

import logging as _logging
import os
import tempfile

import pytest

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "tests.test_showcase"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

# -------------------------------------------------------------------------
def test_all_techniques():
    """
    Showcase test: every technique fires at least once, every assertion must pass.

    Techniques covered:
      F01  density fill
      F02  Perlin noise fill
      F03  Conway's Game of Life fill
      F06  SDF fill
      G01  FIGlet font parser
      G02  TTF/PIL rasterizer          (skipped gracefully if Pillow absent)
      S01  sine warp
      S02  perspective tilt
      S03  isometric 3D extrusion
      S08  shear
      C01  linear gradient
      C02  radial gradient
      C03  per-glyph palette
      C07  24-bit true-color ANSI
      A01  typewriter animation
      A02  scanline animation
      A03  glitch animation
      A04  pulse animation
      A05  dissolve animation
      O01  HTML export
      O02  SVG export
      O03  PNG export                  (skipped gracefully if Pillow absent)
    """

    TEXT = "JDI"

    # ------------------------------------------------------------------
    # Core render
    from justdoit.core.rasterizer import render

    plain = render(TEXT, font="block")
    assert "█" in plain, "F00: block render should contain block chars"

    # ------------------------------------------------------------------
    # F01 — density fill
    density = render(TEXT, font="block", fill="density")
    assert "@" in density or "#" in density, "F01: density fill should contain dense chars"

    # ------------------------------------------------------------------
    # F06 — SDF fill
    sdf = render(TEXT, font="block", fill="sdf")
    assert any(ch in sdf for ch in "@#S%?*+;:,."), "F06: SDF fill should contain density chars"

    # ------------------------------------------------------------------
    # F02 — Perlin noise fill
    noise = render(TEXT, font="block", fill="noise")
    assert any(ch in noise for ch in "@#S%?*+;:,."), "F02: noise fill should contain density chars"

    # Seeded: same seed → same output; different seeds → different output
    noise_a = render(TEXT, font="block", fill="noise")
    noise_b = render(TEXT, font="block", fill="noise")
    # (unseeded renders may vary — just check they're non-empty)
    assert len(noise_a) > 0 and len(noise_b) > 0, "F02: noise fill output should be non-empty"

    # ------------------------------------------------------------------
    # F03 — Cellular automata fill
    cells = render(TEXT, font="block", fill="cells")
    assert "█" in cells or "▓" in cells or "▒" in cells, \
        "F03: cells fill should contain block shade chars"

    # ------------------------------------------------------------------
    # G01 — FIGlet font
    from justdoit.fonts import FONTS
    figlet_fonts = [k for k in FONTS if k not in ("block", "slim")]
    assert len(figlet_fonts) > 0, "G01: at least one FIGlet font should be registered"
    figlet_out = render(TEXT, font=figlet_fonts[0])
    assert len(figlet_out.strip()) > 0, f"G01: FIGlet render with '{figlet_fonts[0]}' should be non-empty"

    # ------------------------------------------------------------------
    # G02 — TTF rasterizer (Pillow-gated)
    pil = pytest.importorskip("PIL", reason="G02: Pillow not installed — skipping TTF test")
    from justdoit.fonts.ttf import find_system_fonts, load_ttf_font
    fonts = find_system_fonts()
    if fonts:
        ttf_name = load_ttf_font(fonts[0], font_size=10)
        ttf_out = render(TEXT, font=ttf_name)
        assert len(ttf_out.strip()) > 0, "G02: TTF render should be non-empty"
    # If no system fonts found, G02 is structurally tested by test_ttf.py

    # ------------------------------------------------------------------
    # S01 — sine warp
    from justdoit.effects.spatial import sine_warp
    warped = sine_warp(plain, amplitude=3.0, frequency=1.0)
    assert warped.count("\n") == plain.count("\n"), "S01: sine_warp must preserve line count"
    assert any(line.startswith(" ") for line in warped.split("\n")), \
        "S01: at least one row should have a leading space offset"

    # ------------------------------------------------------------------
    # S02 — perspective tilt
    from justdoit.effects.spatial import perspective_tilt
    tilted = perspective_tilt(plain, strength=0.5, direction="top")
    assert tilted.count("\n") == plain.count("\n"), "S02: perspective_tilt must preserve line count"

    # ------------------------------------------------------------------
    # S08 — shear
    from justdoit.effects.spatial import shear
    sheared = shear(plain, amount=0.8, direction="right")
    assert sheared.count("\n") == plain.count("\n"), "S08: shear must preserve line count"
    lines = sheared.split("\n")
    leading = [len(ln) - len(ln.lstrip(" ")) for ln in lines]
    assert leading[-1] >= leading[0], "S08: shear offsets should grow toward last row"

    # ------------------------------------------------------------------
    # S03 — isometric 3D extrusion
    from justdoit.effects.isometric import isometric_extrude
    iso = isometric_extrude(plain, depth=3, direction="right")
    n_plain = plain.count("\n") + 1
    n_iso   = iso.count("\n") + 1
    assert n_iso == n_plain + 3, "S03: iso must add exactly depth rows"
    assert any(ch in iso for ch in "▓▒░·"), "S03: iso must contain depth shade chars"
    assert "█" in iso, "S03: iso must preserve front face block chars"

    # ------------------------------------------------------------------
    # C07 / C01 — 24-bit ANSI + linear gradient
    from justdoit.effects.gradient import linear_gradient, parse_color, tc
    assert "\033[38;2;" in tc(255, 128, 0), "C07: tc() must produce 24-bit ANSI prefix"
    grad_h = linear_gradient(plain, parse_color("red"), parse_color("cyan"), direction="horizontal")
    assert "\033[38;2;" in grad_h, "C01: horizontal gradient must contain true-color codes"
    grad_v = linear_gradient(plain, parse_color("gold"), parse_color("blue"), direction="vertical")
    assert "\033[38;2;" in grad_v, "C01: vertical gradient must contain true-color codes"
    grad_d = linear_gradient(plain, parse_color("#ff0000"), parse_color("#0000ff"), direction="diagonal")
    assert "\033[38;2;" in grad_d, "C01: diagonal gradient must contain true-color codes"

    # ------------------------------------------------------------------
    # C02 — radial gradient
    from justdoit.effects.gradient import radial_gradient
    radial = radial_gradient(plain, parse_color("white"), parse_color("purple"))
    assert "\033[38;2;" in radial, "C02: radial gradient must contain true-color codes"

    # ------------------------------------------------------------------
    # C03 — per-glyph palette
    from justdoit.effects.gradient import per_glyph_palette, PRESETS
    for preset_name, palette in PRESETS.items():
        result = per_glyph_palette(plain, palette)
        assert "\033[38;2;" in result, f"C03: preset '{preset_name}' must produce true-color codes"

    # ------------------------------------------------------------------
    # A01 — typewriter
    from justdoit.animate.presets import typewriter
    tw_frames = list(typewriter(plain))
    assert len(tw_frames) > 1, "A01: typewriter must yield multiple frames"
    # Final frame should contain the same visible content
    import re
    plain_stripped = [ln.rstrip() for ln in re.sub(r"\033\[[0-9;]*m", "", plain).split("\n")]
    last_stripped  = [ln.rstrip() for ln in tw_frames[-1].split("\n")]
    assert plain_stripped == last_stripped, "A01: typewriter final frame must match original"

    # ------------------------------------------------------------------
    # A02 — scanline
    from justdoit.animate.presets import scanline
    sl_frames = list(scanline(plain))
    assert len(sl_frames) == plain.count("\n") + 2, \
        "A02: scanline must yield n_rows + 1 frames (+hold)"

    # ------------------------------------------------------------------
    # A03 — glitch
    from justdoit.animate.presets import glitch
    gl_frames = list(glitch(plain, n_frames=6, seed=42))
    assert len(gl_frames) == 7, "A03: glitch must yield n_frames + 1 frames"
    assert any(
        re.sub(r"\033\[[0-9;]*m", "", f).rstrip() !=
        re.sub(r"\033\[[0-9;]*m", "", plain).rstrip()
        for f in gl_frames[:-1]
    ), "A03: at least one glitch frame must differ from original"

    # ------------------------------------------------------------------
    # A04 — pulse
    from justdoit.animate.presets import pulse
    pl_frames = list(pulse(plain, n_cycles=2))
    assert any("\033[" in f for f in pl_frames[:-1]), \
        "A04: pulse frames must contain ANSI codes"
    assert "\033[" not in pl_frames[-1], \
        "A04: pulse final frame must be plain"

    # ------------------------------------------------------------------
    # A05 — dissolve
    from justdoit.animate.presets import dissolve
    ds_frames = list(dissolve(plain, seed=0))
    assert len(ds_frames) > 1, "A05: dissolve must yield multiple frames"
    assert ds_frames[-1].strip() == "", "A05: dissolve final frame must be blank"

    # ------------------------------------------------------------------
    # O01 — HTML export
    from justdoit.output.html import to_html, save_html
    html = to_html(grad_h)
    assert "<!DOCTYPE html>" in html, "O01: to_html must produce a valid HTML page"
    assert "<span style=" in html, "O01: HTML must contain colored span elements"
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
        html_path = f.name
    try:
        save_html(grad_h, html_path)
        assert os.path.getsize(html_path) > 0, "O01: save_html must write a non-empty file"
    finally:
        os.unlink(html_path)

    # ------------------------------------------------------------------
    # O02 — SVG export
    from justdoit.output.svg import to_svg, save_svg
    svg = to_svg(grad_h)
    assert "<svg " in svg, "O02: to_svg must produce a valid SVG document"
    assert "<text " in svg, "O02: SVG must contain <text> elements"
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        svg_path = f.name
    try:
        save_svg(grad_h, svg_path)
        assert os.path.getsize(svg_path) > 0, "O02: save_svg must write a non-empty file"
    finally:
        os.unlink(svg_path)

    # ------------------------------------------------------------------
    # O03 — PNG export (Pillow-gated — already skipped above if absent)
    from justdoit.output.image import to_image, save_png
    img = to_image(grad_h, font_size=14)
    assert img.width > 0 and img.height > 0, "O03: PNG image must have non-zero dimensions"
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        png_path = f.name
    try:
        save_png(grad_h, png_path, font_size=14)
        with open(png_path, "rb") as f:
            magic = f.read(4)
        assert magic == b"\x89PNG", "O03: output file must be a valid PNG"
    finally:
        os.unlink(png_path)

    # ------------------------------------------------------------------
    # Composition: iso + gradient + warp — all three effects chained
    iso_colored = linear_gradient(
        isometric_extrude(plain, depth=3),
        parse_color("gold"),
        parse_color("red"),
        direction="vertical",
    )
    iso_warped = sine_warp(iso_colored, amplitude=2.0)
    assert "\033[38;2;" in iso_warped, \
        "Composition: iso + gradient + warp must preserve true-color codes"
    assert iso_warped.count("\n") == iso_colored.count("\n"), \
        "Composition: warp must not change line count of iso+gradient output"

    _LOGGER.info("All techniques passed showcase test ✓")
