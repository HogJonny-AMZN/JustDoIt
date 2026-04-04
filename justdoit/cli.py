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
from justdoit.effects.generative import _TRUCHET_STYLES
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
  %(prog)s "JUST DO IT" --measure
  %(prog)s "JUST DO IT" --target 3840x2160
  %(prog)s "JUST DO IT" --target 3840x2160 --save-svg out.svg
  %(prog)s "JUST DO IT" --fit 80
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
        "--truchet-style", default="diagonal", choices=list(_TRUCHET_STYLES.keys()),
        help="Truchet tile style when --fill truchet is used (default: diagonal). "
             f"Options: {', '.join(_TRUCHET_STYLES.keys())}",
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
        "--recursion", action="store_true",
        help="Typographic recursion (N01): fill cells with cycling source text chars",
    )
    parser.add_argument(
        "--recursion-sep", default=" ", metavar="SEP",
        help="Separator between word cycles in recursion mode (default: space)",
    )
    parser.add_argument(
        "--list-fonts", action="store_true",
        help="List available fonts and exit",
    )
    parser.add_argument(
        "--list-colors", action="store_true",
        help="List available colors and exit",
    )
    parser.add_argument(
        "--measure", action="store_true",
        help="Print render dimensions (cols x rows) and display fit table, then exit.",
    )
    parser.add_argument(
        "--target", metavar="WxH[@Sx]", default=None,
        help="Display target spec (e.g. 3840x2160 or 3840x2160@2.0x). "
             "With --save-svg: auto-sizes font. Standalone: prints sizing info to stderr.",
    )
    parser.add_argument(
        "--svg-font-size", type=int, default=None, metavar="N",
        help="Font size in pixels for SVG output (default: 14). Overrides --target auto-sizing.",
    )
    parser.add_argument(
        "--fit", type=int, default=None, metavar="COLS",
        help="Truncate text to fit within COLS terminal columns before rendering.",
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

    # --- 1. Parse --target immediately after font resolution ---
    _target_rt = None
    if args.target:
        from justdoit.layout import RenderTarget
        try:
            _target_rt = RenderTarget.from_string(args.target)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

    # --- 2. Handle --measure (print + exit before render) ---
    if args.measure:
        from justdoit.layout import measure, DISPLAYS
        iso_d = args.iso if args.iso else 0
        cols, rows = measure(args.text, font=font_name, gap=args.gap, iso_depth=iso_d)
        print(f"Render size:  {cols} cols x {rows} rows")
        print()
        print("Display fits:")
        for label, rt in DISPLAYS.items():
            pt = rt.max_font_pt(cols, rows)
            cell_w, cell_h = rt.cell_size_px(pt)
            letter_h_in = (rows * cell_h) / 96.0
            print(
                f"  {label:<12} {rt.display_w}x{rt.display_h}  ->  {pt}pt  "
                f"letter height {letter_h_in:.2f}\"  "
                f"grid {rt.max_columns(pt)}x{rt.max_rows(pt)}"
            )
        sys.exit(0)

    # If truchet fill is selected, patch the registry to honour --truchet-style
    if args.fill == "truchet" and args.truchet_style != "diagonal":
        from justdoit.effects.generative import truchet_fill as _tf
        from justdoit.core.rasterizer import _FILL_FNS as _fns
        _chosen_style = args.truchet_style
        _fns["truchet"] = lambda mask: _tf(mask, style=_chosen_style)

    # --- 3. Handle --fit (set text_to_render before render call) ---
    text_to_render = args.text
    if args.fit is not None:
        from justdoit.layout import fit_text
        iso_d = args.iso if args.iso else 0
        text_to_render, actual_cols = fit_text(
            args.text,
            target_cols=args.fit,
            font=font_name,
            gap=args.gap,
            iso_depth=iso_d,
        )
        if text_to_render != args.text:
            print(
                f"Note: text truncated to fit {args.fit} cols "
                f"(rendered {actual_cols} cols)",
                file=sys.stderr,
            )

    try:
        # --- 4. Use text_to_render in render() call ---
        output = render(
            text_to_render,
            font=font_name,
            color=args.color,
            gap=args.gap,
            fill=args.fill,
            recursion=args.recursion,
            recursion_separator=args.recursion_sep,
        )

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

        # --- 5. Handle --target standalone info → stderr (after render, before save) ---
        if _target_rt is not None and not args.save_svg:
            from justdoit.layout import measure
            iso_d = args.iso if args.iso else 0
            cols, rows = measure(args.text, font=font_name, gap=args.gap, iso_depth=iso_d)
            pt = _target_rt.max_font_pt(cols, rows)
            cell_w, cell_h = _target_rt.cell_size_px(pt)
            letter_h = rows * cell_h / 96.0
            print(
                f"Target: {_target_rt.display_w}x{_target_rt.display_h} "
                f"@ {_target_rt.scaling:.1f}x scaling\n"
                f"Max font size: {pt}pt  (cell: {cell_w:.1f}x{cell_h:.1f}px)\n"
                f"Letter height: {letter_h:.2f}\"  ({letter_h*2.54:.2f} cm)\n"
                f"Terminal grid: {_target_rt.max_columns(pt)}x{_target_rt.max_rows(pt)}\n"
                f"SVG font-size: {_target_rt.svg_font_size_px(pt)}px",
                file=sys.stderr,
            )

        # Save to file targets (can combine with terminal output)
        if args.save_html:
            save_html(output, args.save_html)
        # --- 6. Handle --svg-font-size + --target auto-size inside save_svg block ---
        if args.save_svg:
            svg_font_size = args.svg_font_size  # explicit override, may be None
            if svg_font_size is None and _target_rt is not None:
                from justdoit.layout import measure
                iso_d = args.iso if args.iso else 0
                cols, rows = measure(args.text, font=font_name, gap=args.gap, iso_depth=iso_d)
                pt = _target_rt.max_font_pt(cols, rows)
                svg_font_size = _target_rt.svg_font_size_px(pt)
            save_svg(output, args.save_svg, font_size=svg_font_size or 14)
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
