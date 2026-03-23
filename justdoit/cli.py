"""
Package: justdoit.cli
Command-line interface entry point for JustDoIt.

Parses arguments, resolves the font (builtin, FIGlet, or TTF), invokes render(),
and prints to stdout. All user-facing error messages go to stderr.
"""

import argparse
import logging as _logging
import sys
from typing import Optional

from justdoit.fonts import FONTS
from justdoit.effects.color import COLORS, colorize
from justdoit.core.rasterizer import render, _FILL_FNS
from justdoit.effects.spatial import sine_warp, perspective_tilt, shear
from justdoit.effects.gradient import (
    linear_gradient, radial_gradient, per_glyph_palette,
    parse_color, PRESETS,
)
from justdoit.effects.isometric import isometric_extrude
from justdoit.animate.presets import typewriter, scanline, glitch, pulse, dissolve
from justdoit.animate.player import play
from justdoit.output.html import save_html
from justdoit.output.svg import save_svg
from justdoit.output.terminal import print_art

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.cli"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
def main() -> None:
    """Entry point for the JustDoIt CLI.

    Parses command-line arguments, resolves font (including optional TTF),
    renders the text, and prints to stdout.

    :raises SystemExit: On argument errors or missing dependencies.
    """
    parser = argparse.ArgumentParser(
        prog="justdoit",
        description="JustDoIt — ASCII art generator. Turns text into bold ASCII art.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
fonts:   {', '.join(FONTS.keys())}
colors:  {', '.join(c for c in COLORS if c != 'reset')}
fill:    {', '.join(_FILL_FNS.keys())}

examples:
  %(prog)s "Hello World"
  %(prog)s "Just Do It" --font slim --color cyan
  %(prog)s "FIRE" --color rainbow
  %(prog)s "CO3DEX" --fill density
  %(prog)s "JUST" --fill sdf --color cyan
  %(prog)s "Hi" --ttf /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
        """,
    )
    parser.add_argument("text", nargs="?", help="Text to render as ASCII art")
    parser.add_argument(
        "--font", "-f", default="block", choices=list(FONTS.keys()),
        help="Font style (default: block)",
    )
    parser.add_argument(
        "--color", "-c", default=None, choices=[k for k in COLORS if k != "reset"],
        help="Color/effect (default: none)",
    )
    parser.add_argument(
        "--gap", "-g", type=int, default=1,
        help="Gap between characters in spaces (default: 1)",
    )
    parser.add_argument(
        "--fill", default=None, choices=list(_FILL_FNS.keys()),
        help="Fill style for glyph rendering (default: none)",
    )
    parser.add_argument(
        "--ttf", metavar="PATH",
        help="Path to a TTF/OTF font file to use (requires Pillow)",
    )
    parser.add_argument(
        "--ttf-size", type=int, default=12, metavar="N",
        help="Font size for TTF rasterization (default: 12)",
    )
    parser.add_argument(
        "--save-html", metavar="PATH",
        help="Save output as an HTML file (e.g. out.html)",
    )
    parser.add_argument(
        "--save-svg", metavar="PATH",
        help="Save output as an SVG file (e.g. out.svg)",
    )
    parser.add_argument(
        "--save-png", metavar="PATH",
        help="Save output as a PNG image (requires Pillow, e.g. out.png)",
    )
    parser.add_argument(
        "--animate", default=None,
        choices=["typewriter", "scanline", "glitch", "pulse", "dissolve"],
        help="Animation preset to play in the terminal",
    )
    parser.add_argument(
        "--fps", type=float, default=12.0,
        help="Animation frames per second (default: 12)",
    )
    parser.add_argument(
        "--loop", action="store_true",
        help="Loop animation until Ctrl+C",
    )
    parser.add_argument(
        "--iso", type=int, default=None, metavar="DEPTH",
        help="Isometric 3D extrusion — depth in layers (e.g. 4)",
    )
    parser.add_argument(
        "--iso-dir", default="right", choices=["right", "left"],
        help="Isometric extrusion direction (default: right)",
    )
    parser.add_argument(
        "--gradient", nargs=2, metavar=("FROM", "TO"),
        help="Linear gradient between two colors (e.g. --gradient red cyan)",
    )
    parser.add_argument(
        "--gradient-dir", default="horizontal",
        choices=["horizontal", "vertical", "diagonal"],
        help="Gradient direction (default: horizontal)",
    )
    parser.add_argument(
        "--radial", nargs=2, metavar=("INNER", "OUTER"),
        help="Radial gradient from center outward (e.g. --radial white blue)",
    )
    parser.add_argument(
        "--palette", default=None,
        metavar="NAME",
        help=f"Per-column palette preset: {', '.join(PRESETS.keys())}",
    )
    parser.add_argument(
        "--warp", type=float, default=None, metavar="AMPLITUDE",
        help="Sine wave warp — horizontal row oscillation (e.g. 3.0)",
    )
    parser.add_argument(
        "--warp-freq", type=float, default=1.0, metavar="FREQ",
        help="Sine warp frequency — cycles across full height (default: 1.0)",
    )
    parser.add_argument(
        "--perspective", type=float, default=None, metavar="STRENGTH",
        help="Perspective tilt strength 0.0–1.0 — narrows toward top (e.g. 0.4)",
    )
    parser.add_argument(
        "--perspective-dir", default="top", choices=["top", "bottom"],
        help="Perspective tilt direction (default: top)",
    )
    parser.add_argument(
        "--shear", type=float, default=None, metavar="AMOUNT",
        help="Shear — italic/oblique offset per row (e.g. 0.5)",
    )
    parser.add_argument(
        "--shear-dir", default="right", choices=["right", "left"],
        help="Shear direction (default: right)",
    )
    parser.add_argument(
        "--list-fonts", action="store_true",
        help="List available fonts and exit",
    )
    parser.add_argument(
        "--list-colors", action="store_true",
        help="List available colors and exit",
    )

    args = parser.parse_args()

    if not args.text and not args.list_fonts and not args.list_colors:
        parser.print_help()
        sys.exit(1)

    if args.list_fonts:
        print("Available fonts:")
        for name in FONTS:
            print(f"  {name}")
        sys.exit(0)

    if args.list_colors:
        print("Available colors:")
        for name in COLORS:
            if name != "reset":
                sample = colorize("██", name)
                print(f"  {name:<10} {sample}")
        sys.exit(0)

    font_name: str = args.font

    if args.ttf:
        try:
            from justdoit.fonts.ttf import load_ttf_font
        except ImportError:
            print(
                "Error: TTF support requires Pillow. Install with: pip install Pillow",
                file=sys.stderr,
            )
            sys.exit(1)
        try:
            font_name = load_ttf_font(args.ttf, font_size=args.ttf_size)
        except ImportError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        except ValueError as exc:
            print(f"Error loading TTF font: {exc}", file=sys.stderr)
            sys.exit(1)

    try:
        output = render(args.text, font=font_name, color=args.color, gap=args.gap, fill=args.fill)

        # Apply isometric extrusion before color effects (color applies on top)
        if args.iso is not None:
            output = isometric_extrude(output, depth=args.iso, direction=args.iso_dir)

        # Apply gradient/palette color effects (override --color if set)
        if args.gradient:
            try:
                from_col = parse_color(args.gradient[0])
                to_col = parse_color(args.gradient[1])
            except ValueError as exc:
                print(f"Error: {exc}", file=sys.stderr)
                sys.exit(1)
            output = linear_gradient(output, from_col, to_col, direction=args.gradient_dir)
        elif args.radial:
            try:
                inner_col = parse_color(args.radial[0])
                outer_col = parse_color(args.radial[1])
            except ValueError as exc:
                print(f"Error: {exc}", file=sys.stderr)
                sys.exit(1)
            output = radial_gradient(output, inner_col, outer_col)
        elif args.palette:
            if args.palette not in PRESETS:
                print(
                    f"Error: Unknown palette '{args.palette}'. "
                    f"Available: {', '.join(PRESETS.keys())}",
                    file=sys.stderr,
                )
                sys.exit(1)
            output = per_glyph_palette(output, PRESETS[args.palette])

        # Apply spatial effects in order: warp → perspective → shear
        if args.warp is not None:
            output = sine_warp(output, amplitude=args.warp, frequency=args.warp_freq)
        if args.perspective is not None:
            output = perspective_tilt(output, strength=args.perspective, direction=args.perspective_dir)
        if args.shear is not None:
            output = shear(output, amount=args.shear, direction=args.shear_dir)

        # Save to file targets (can combine with terminal output)
        if args.save_html:
            save_html(output, args.save_html)
        if args.save_svg:
            save_svg(output, args.save_svg)
        if args.save_png:
            try:
                from justdoit.output.image import save_png
            except ImportError:
                print("Error: PNG output requires Pillow. Install with: pip install Pillow",
                      file=sys.stderr)
                sys.exit(1)
            save_png(output, args.save_png)

        if args.animate:
            _PRESETS = {
                "typewriter": lambda t: typewriter(t),
                "scanline":   lambda t: scanline(t),
                "glitch":     lambda t: glitch(t),
                "pulse":      lambda t: pulse(t),
                "dissolve":   lambda t: dissolve(t),
            }
            play(_PRESETS[args.animate](output), fps=args.fps, loop=args.loop)
        else:
            print_art(output)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
