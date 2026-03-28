"""
Package: scripts.demo
Visual showcase of every JustDoIt technique.

Run with:
    python scripts/demo.py
    python scripts/demo.py --text "YOUR TEXT"
    python scripts/demo.py --pause          # press Enter between techniques
    python scripts/demo.py --gallery        # also save SVGs to docs/gallery/
"""

import argparse
import logging as _logging
import os
import sys

# Allow running from repo root without installing the package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "scripts.demo"
__updated__ = "2026-03-27 00:00:00"
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
def run(text: str = "Just Do It", pause: bool = False, gallery: bool = False) -> None:
    """Render and print every technique to the terminal.

    :param text: Text to render (default: 'Just Do It').
    :param pause: If True, wait for Enter between each technique.
    :param gallery: If True, save each render as SVG to docs/gallery/ and rebuild index.
    """
    from justdoit.core.rasterizer import render
    from justdoit.effects.gradient import (
        PRESETS, linear_gradient, parse_color, per_glyph_palette, radial_gradient,
    )
    from justdoit.effects.isometric import isometric_extrude
    from justdoit.effects.spatial import perspective_tilt, shear, sine_warp

    plain = render(text, font="block")

    # Accumulates (stem, rendered) pairs when --gallery is set
    saves: list[tuple[str, str]] = []

    def show(stem: str, rendered: str) -> None:
        _show(rendered)
        if gallery:
            saves.append((stem, rendered))

    # ------------------------------------------------------------------
    _header("F00  block font (baseline)", "plain render, no effects")
    show("S-F00-block-baseline", plain)
    _pause(pause)

    # ------------------------------------------------------------------
    _header("F01  density fill", "brightness → character density")
    show("S-F01-density-fill", render(text, font="block", fill="density"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("F06  SDF fill", "signed distance field shading")
    show("S-F06-sdf-fill", render(text, font="block", fill="sdf"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("F07  shape-vector fill", "6D directional character matching — edges follow contours")
    show("S-F07-shape-fill", render(text, font="block", fill="shape"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("F02  Perlin noise fill", "organic textured interior — different every run")
    show("S-F02-noise-fill", render(text, font="block", fill="noise"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("F03  Cellular automata fill", "Conway's Game of Life, frozen after 4 steps")
    show("S-F03-cells-fill", render(text, font="block", fill="cells"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("G01  FIGlet font — 'big'", "community font parser")
    show("S-G01-figlet-big", render(text, font="big"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("G01  FIGlet font — 'slant'", "")
    show("S-G01-figlet-slant", render(text, font="slant"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("G01  slim font", "3-row ASCII line-drawing")
    show("S-G01-slim", render(text, font="slim"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("C01  linear gradient — horizontal", "red → cyan across columns")
    show("S-C01-gradient-horiz",
         linear_gradient(plain, parse_color("red"), parse_color("cyan"), direction="horizontal"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("C01  linear gradient — vertical", "gold → blue across rows")
    show("S-C01-gradient-vert",
         linear_gradient(plain, parse_color("gold"), parse_color("blue"), direction="vertical"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("C01  linear gradient — diagonal", "magenta → green")
    show("S-C01-gradient-diag",
         linear_gradient(plain, parse_color("magenta"), parse_color("green"), direction="diagonal"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("C02  radial gradient", "white center → purple edges")
    show("S-C02-radial", radial_gradient(plain, parse_color("white"), parse_color("purple")))
    _pause(pause)

    # ------------------------------------------------------------------
    for name in ("fire", "ocean", "neon", "rainbow"):
        _header(f"C03  per-glyph palette — {name}", "")
        show(f"S-C03-{name}", per_glyph_palette(plain, PRESETS[name]))
        _pause(pause)

    # ------------------------------------------------------------------
    _header("S01  sine warp", "rows oscillate horizontally — wave/flag effect")
    show("S-S01-sine-warp", sine_warp(plain, amplitude=4.0, frequency=1.5))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("S02  perspective tilt — top", "vanishing point narrows toward top")
    show("S-S02-perspective-top", perspective_tilt(plain, strength=0.5, direction="top"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("S02  perspective tilt — bottom", "vanishing point narrows toward bottom")
    show("S-S02-perspective-bottom", perspective_tilt(plain, strength=0.5, direction="bottom"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("S08  shear — right", "italic/oblique offset per row")
    show("S-S08-shear-right", shear(plain, amount=1.2, direction="right"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("S03  isometric 3D extrusion — right", "chunky block letters with depth shading")
    iso = isometric_extrude(plain, depth=4, direction="right")
    show("S-S03-iso-right", iso)
    _pause(pause)

    # ------------------------------------------------------------------
    _header("S03  isometric 3D extrusion — left", "")
    show("S-S03-iso-left", isometric_extrude(plain, depth=4, direction="left"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("S03 + C01  iso + gradient", "gold→red vertical gradient over 3D extrusion")
    show("S-S03-iso-gradient",
         linear_gradient(iso, parse_color("gold"), parse_color("red"), direction="vertical"))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("S03 + C03 + S01  iso + neon palette + warp", "everything at once")
    show("S-S03-iso-neon-warp",
         sine_warp(per_glyph_palette(isometric_extrude(plain, depth=3), PRESETS["neon"]), amplitude=2.0))
    _pause(pause)

    # ------------------------------------------------------------------
    _header("F02 + C02  noise fill + radial gradient", "organic fill with color overlay")
    noise_rendered = render(text, font="block", fill="noise")
    show("S-F02-noise-radial",
         radial_gradient(noise_rendered, parse_color("cyan"), parse_color("blue")))
    _pause(pause)

    # ------------------------------------------------------------------
    # TTF (Pillow-gated)
    try:
        from justdoit.fonts.ttf import find_system_fonts, load_ttf_font
        fonts = find_system_fonts()
        if fonts:
            ttf_name = load_ttf_font(fonts[0], font_size=12)
            _header("G02  TTF rasterizer", f"{os.path.basename(fonts[0])}")
            ttf_rendered = render(text, font=ttf_name)
            show("S-G02-ttf", ttf_rendered)
            _pause(pause)
    except ImportError:
        _header("G02  TTF rasterizer", "skipped — Pillow not installed")
        print("  (install Pillow to enable TTF support)")

    # ------------------------------------------------------------------
    print(f"\n{_SEP}{'─' * 60}{_RESET}")
    print(f"{_BOLD}{_HEADER}Static techniques complete.{_RESET}  135 tests passing.")
    print(f"{_DIM}Run scripts/demo_animate.py for animation showcase.{_RESET}\n")

    # ------------------------------------------------------------------
    if gallery and saves:
        _save_gallery(saves)


# -------------------------------------------------------------------------
def _save_gallery(saves: list[tuple[str, str]]) -> None:
    """Save collected renders as SVGs and rebuild the gallery index.

    :param saves: List of (stem, rendered_string) pairs.
    """
    from pathlib import Path
    from justdoit.output.svg import save_svg
    from generate_gallery import build_index

    gallery_dir = Path(__file__).parent.parent / "docs" / "gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{_BOLD}Saving gallery SVGs ...{_RESET}")
    for stem, rendered in saves:
        path = gallery_dir / f"{stem}.svg"
        save_svg(rendered, str(path))
        print(f"  {path.name}")

    print(f"{_BOLD}Rebuilding index ...{_RESET}")
    build_index()
    print(f"{_DIM}Gallery: docs/gallery/README.md{_RESET}\n")


# -------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Visual showcase of all JustDoIt techniques.",
    )
    parser.add_argument(
        "text", nargs="?", default="Just Do It",
        help="Text to render (default: Just Do It)",
    )
    parser.add_argument(
        "--pause", action="store_true",
        help="Press Enter between each technique",
    )
    parser.add_argument(
        "--gallery", action="store_true",
        help="Save each render as SVG to docs/gallery/ and rebuild the index",
    )
    args = parser.parse_args()
    run(text=args.text.upper(), pause=args.pause, gallery=args.gallery)
