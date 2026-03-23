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
        print_art(output)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
