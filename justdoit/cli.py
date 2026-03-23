import argparse
import sys

from justdoit.fonts import FONTS
from justdoit.effects.color import COLORS, colorize
from justdoit.core.rasterizer import render
from justdoit.output.terminal import print_art


def main():
    parser = argparse.ArgumentParser(
        prog='justdoit',
        description='JustDoIt — ASCII art generator. Turns text into bold ASCII art.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
fonts:   {', '.join(FONTS.keys())}
colors:  {', '.join(c for c in COLORS if c != 'reset')}

examples:
  %(prog)s "Hello World"
  %(prog)s "Just Do It" --font slim --color cyan
  %(prog)s "FIRE" --color rainbow
  %(prog)s "CO3DEX" --font block --color yellow
        """,
    )
    parser.add_argument('text', nargs='?', help='Text to render as ASCII art')
    parser.add_argument('--font', '-f', default='block', choices=list(FONTS.keys()),
                        help='Font style (default: block)')
    parser.add_argument('--color', '-c', default=None, choices=[k for k in COLORS if k != 'reset'],
                        help='Color/effect (default: none)')
    parser.add_argument('--gap', '-g', type=int, default=1,
                        help='Gap between characters in spaces (default: 1)')
    parser.add_argument('--list-fonts', action='store_true',
                        help='List available fonts and exit')
    parser.add_argument('--list-colors', action='store_true',
                        help='List available colors and exit')

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
            if name != 'reset':
                sample = colorize('██', name)
                print(f"  {name:<10} {sample}")
        sys.exit(0)

    try:
        output = render(args.text, font=args.font, color=args.color, gap=args.gap)
        print_art(output)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
