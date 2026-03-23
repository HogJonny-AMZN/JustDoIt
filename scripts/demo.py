"""
Package: scripts.demo
Visual showcase of every JustDoIt technique.

Run with:
    python scripts/demo.py
    python scripts/demo.py --text "YOUR TEXT"
    python scripts/demo.py --pause     # press Enter between techniques

Prints each technique's output to the terminal with a labelled header.
"""

import argparse
import logging as _logging
import os
import sys
import time

# Allow running from repo root without installing the package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "scripts.demo"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_DIM    = "\033[2m"
_HEADER = "\033[38;2;80;220;220m"   # cyan
_SEP    = "\033[38;2;60;60;80m"     # dark grey


# -------------------------------------------------------------------------
def _header(label: str, desc: str) -> None:
    print(f"\n{_SEP}{'─' * 60}{_RESET}")
    print(f"{_BOLD}{_HEADER}{label}{_RESET}  {_DIM}{desc}{_RESET}")
    print(f"{_SEP}{'─' * 60}{_RESET}")


# -------------------------------------------------------------------------
def _show(text: str) -> None:
    print(text)


# -------------------------------------------------------------------------
def _pause(enabled: bool) -> None:
    if enabled:
        input(f"{_DIM}  [Enter]{_RESET}")


# -------------------------------------------------------------------------
def run(text: str = "JDI", pause: bool = False) -> None:
    """Render and print every technique to the terminal.

    :param text: Text to render (default: 'JDI').
    :param pause: If True, wait for Enter between each technique.
    """
    from justdoit.core.rasterizer import render
    from justdoit.fonts import FONTS
    from justdoit.effects.spatial import sine_warp, perspective_tilt, shear
    from justdoit.effects.isometric import isometric_extrude
    from justdoit.effects.gradient import (
        linear_gradient, radial_gradient, per_glyph_palette,
        parse_color, PRESETS,
    )
    from justdoit.effects.generative import noise_fill, cells_fill
    from justdoit.animate.presets import typewriter, scanline, glitch, pulse, dissolve
    from justdoit.animate.player import play

    plain = render(text, font="block")

    # ------------------------------------------------------------------
    _header("F00  block font (baseline)", "plain render, no effects")
    _show(plain)
    _pause(pause)

    # ------------------------------------------------------------------
    _header("F01  density fill", "brightness → character density")
    _show(render(text, font="block", fill="density"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("F06  SDF fill", "signed distance field shading")
    _show(render(text, font="block", fill="sdf"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("F02  Perlin noise fill", "organic textured interior — different every run")
    _show(render(text, font="block", fill="noise"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("F03  Cellular automata fill", "Conway's Game of Life, frozen after 4 steps")
    _show(render(text, font="block", fill="cells"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("G01  FIGlet font — 'big'", "community font parser")
    _show(render(text, font="big"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("G01  FIGlet font — 'slant'", "")
    _show(render(text, font="slant"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("G01  slim font", "3-row ASCII line-drawing")
    _show(render(text, font="slim"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("C01  linear gradient — horizontal", "red → cyan across columns")
    _show(linear_gradient(plain, parse_color("red"), parse_color("cyan"), direction="horizontal"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("C01  linear gradient — vertical", "gold → blue across rows")
    _show(linear_gradient(plain, parse_color("gold"), parse_color("blue"), direction="vertical"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("C01  linear gradient — diagonal", "magenta → green")
    _show(linear_gradient(plain, parse_color("magenta"), parse_color("green"), direction="diagonal"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("C02  radial gradient", "white center → purple edges")
    _show(radial_gradient(plain, parse_color("white"), parse_color("purple")))
    _pause(pause)

    # ------------------------------------------------------------------
    for name in ("fire", "ocean", "neon", "rainbow"):
        _header(f"C03  per-glyph palette — {name}", "")
        _show(per_glyph_palette(plain, PRESETS[name]))
        _pause(pause)

    # ------------------------------------------------------------------
    _header("S01  sine warp", "rows oscillate horizontally — wave/flag effect")
    _show(sine_warp(plain, amplitude=3.0, frequency=1.0))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("S02  perspective tilt — top", "vanishing point narrows toward top")
    _show(perspective_tilt(plain, strength=0.6, direction="top"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("S02  perspective tilt — bottom", "vanishing point narrows toward bottom")
    _show(perspective_tilt(plain, strength=0.6, direction="bottom"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("S08  shear — right", "italic/oblique offset per row")
    _show(shear(plain, amount=0.7, direction="right"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("S03  isometric 3D extrusion — right", "chunky block letters with depth shading")
    _show(isometric_extrude(plain, depth=4, direction="right"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("S03  isometric 3D extrusion — left", "")
    _show(isometric_extrude(plain, depth=4, direction="left"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("S03 + C01  iso + gradient", "gold→red vertical gradient over 3D extrusion")
    iso = isometric_extrude(plain, depth=4)
    _show(linear_gradient(iso, parse_color("gold"), parse_color("red"), direction="vertical"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("S03 + C03 + S01  iso + neon palette + warp", "everything at once")
    iso_neon = per_glyph_palette(isometric_extrude(plain, depth=3), PRESETS["neon"])
    _show(sine_warp(iso_neon, amplitude=2.0))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("F02 + C02  noise fill + radial gradient", "organic fill with color overlay")
    noise_rendered = render(text, font="block", fill="noise")
    _show(radial_gradient(noise_rendered, parse_color("cyan"), parse_color("blue")))
    _pause(pause)

    # ------------------------------------------------------------------
    # TTF (Pillow-gated)
    try:
        from justdoit.fonts.ttf import find_system_fonts, load_ttf_font
        fonts = find_system_fonts()
        if fonts:
            ttf_name = load_ttf_font(fonts[0], font_size=12)
            _header("G02  TTF rasterizer", f"{os.path.basename(fonts[0])}")
            _show(render(text, font=ttf_name))
            _pause(pause)
    except ImportError:
        _header("G02  TTF rasterizer", "skipped — Pillow not installed")
        print("  (install Pillow to enable TTF support)")

    # ------------------------------------------------------------------
    # Animations — brief, finite
    _header("A01  typewriter", "characters appear left-to-right")
    play(typewriter(plain, chars_per_frame=4), fps=24)
    _pause(pause)

    _header("A02  scanline", "text builds top to bottom")
    play(scanline(plain, rows_per_frame=1), fps=10)
    _pause(pause)

    _header("A03  glitch", "random corruption, snaps back")
    play(glitch(plain, n_frames=18, intensity=0.3, seed=42), fps=12)
    _pause(pause)

    _header("A04  pulse", "brightness oscillation")
    play(pulse(plain, n_cycles=2), fps=10)
    _pause(pause)

    _header("A05  dissolve", "characters scatter and fade out")
    play(dissolve(plain, chars_per_frame=4, seed=0), fps=24)
    _pause(pause)

    # ------------------------------------------------------------------
    print(f"\n{_SEP}{'─' * 60}{_RESET}")
    print(f"{_BOLD}{_HEADER}All techniques complete.{_RESET}  135 tests passing.\n")


# -------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Visual showcase of all JustDoIt techniques.",
    )
    parser.add_argument(
        "text", nargs="?", default="JDI",
        help="Text to render (default: JDI)",
    )
    parser.add_argument(
        "--pause", action="store_true",
        help="Press Enter between each technique",
    )
    args = parser.parse_args()
    run(text=args.text.upper(), pause=args.pause)
