#!/usr/bin/env python3
"""
JustDoIt - ASCII Art Generator CLI
Turns text into bold ASCII art. Just do it.
"""

import argparse
import sys

# ── Font definitions ──────────────────────────────────────────────────────────
# Each font maps characters to multi-line ASCII art (list of rows).
# All characters in a font must have the same height.

FONTS = {}

# ── BLOCK font (classic block letters, 7 rows tall) ──────────────────────────
BLOCK = {
    'A': [
      "  ██  ",
      " ████ ",
      "██  ██",
      "██████",
      "██  ██",
      "██  ██",
      "      ",
    ],
    'B': [
      "█████ ",
      "██  ██",
      "██  ██",
      "█████ ",
      "██  ██",
      "█████ ",
      "      ",
    ],
    'C': [
      " ████ ",
      "██    ",
      "██    ",
      "██    ",
      "██    ",
      " ████ ",
      "      ",
    ],
    'D': [
      "█████ ",
      "██  ██",
      "██  ██",
      "██  ██",
      "██  ██",
      "█████ ",
      "      ",
    ],
    'E': [
      "██████",
      "██    ",
      "██    ",
      "████  ",
      "██    ",
      "██████",
      "      ",
    ],
    'F': [
      "██████",
      "██    ",
      "██    ",
      "████  ",
      "██    ",
      "██    ",
      "      ",
    ],
    'G': [
      " ████ ",
      "██    ",
      "██    ",
      "██ ███",
      "██  ██",
      " █████",
      "      ",
    ],
    'H': [
      "██  ██",
      "██  ██",
      "██  ██",
      "██████",
      "██  ██",
      "██  ██",
      "      ",
    ],
    'I': [
      "██████",
      "  ██  ",
      "  ██  ",
      "  ██  ",
      "  ██  ",
      "██████",
      "      ",
    ],
    'J': [
      "██████",
      "   ██ ",
      "   ██ ",
      "   ██ ",
      "██ ██ ",
      " ████ ",
      "      ",
    ],
    'K': [
      "██  ██",
      "██ ██ ",
      "████  ",
      "████  ",
      "██ ██ ",
      "██  ██",
      "      ",
    ],
    'L': [
      "██    ",
      "██    ",
      "██    ",
      "██    ",
      "██    ",
      "██████",
      "      ",
    ],
    'M': [
      "██   ██",
      "███ ███",
      "███████",
      "██ █ ██",
      "██   ██",
      "██   ██",
      "       ",
    ],
    'N': [
      "██   ██",
      "███  ██",
      "████ ██",
      "██ ████",
      "██  ███",
      "██   ██",
      "       ",
    ],
    'O': [
      " ████ ",
      "██  ██",
      "██  ██",
      "██  ██",
      "██  ██",
      " ████ ",
      "      ",
    ],
    'P': [
      "█████ ",
      "██  ██",
      "██  ██",
      "█████ ",
      "██    ",
      "██    ",
      "      ",
    ],
    'Q': [
      " ████ ",
      "██  ██",
      "██  ██",
      "██  ██",
      "██ ███",
      " █████",
      "      ",
    ],
    'R': [
      "█████ ",
      "██  ██",
      "██  ██",
      "█████ ",
      "██ ██ ",
      "██  ██",
      "      ",
    ],
    'S': [
      " █████",
      "██    ",
      "██    ",
      " ████ ",
      "    ██",
      "█████ ",
      "      ",
    ],
    'T': [
      "██████",
      "  ██  ",
      "  ██  ",
      "  ██  ",
      "  ██  ",
      "  ██  ",
      "      ",
    ],
    'U': [
      "██  ██",
      "██  ██",
      "██  ██",
      "██  ██",
      "██  ██",
      " ████ ",
      "      ",
    ],
    'V': [
      "██  ██",
      "██  ██",
      "██  ██",
      "██  ██",
      " ████ ",
      "  ██  ",
      "      ",
    ],
    'W': [
      "██   ██",
      "██   ██",
      "██   ██",
      "██ █ ██",
      "███████",
      "██   ██",
      "       ",
    ],
    'X': [
      "██  ██",
      "██  ██",
      " ████ ",
      "  ██  ",
      " ████ ",
      "██  ██",
      "      ",
    ],
    'Y': [
      "██  ██",
      "██  ██",
      " ████ ",
      "  ██  ",
      "  ██  ",
      "  ██  ",
      "      ",
    ],
    'Z': [
      "██████",
      "   ██ ",
      "  ██  ",
      " ██   ",
      "██    ",
      "██████",
      "      ",
    ],
    '0': [
      " ████ ",
      "██  ██",
      "██ ███",
      "███ ██",
      "██  ██",
      " ████ ",
      "      ",
    ],
    '1': [
      " ███  ",
      "  ██  ",
      "  ██  ",
      "  ██  ",
      "  ██  ",
      "██████",
      "      ",
    ],
    '2': [
      " ████ ",
      "██  ██",
      "   ██ ",
      "  ██  ",
      " ██   ",
      "██████",
      "      ",
    ],
    '3': [
      "█████ ",
      "    ██",
      "    ██",
      " ████ ",
      "    ██",
      "█████ ",
      "      ",
    ],
    '4': [
      "██  ██",
      "██  ██",
      "██████",
      "    ██",
      "    ██",
      "    ██",
      "      ",
    ],
    '5': [
      "██████",
      "██    ",
      "█████ ",
      "    ██",
      "    ██",
      "█████ ",
      "      ",
    ],
    '6': [
      " ████ ",
      "██    ",
      "█████ ",
      "██  ██",
      "██  ██",
      " ████ ",
      "      ",
    ],
    '7': [
      "██████",
      "   ██ ",
      "  ██  ",
      " ██   ",
      " ██   ",
      " ██   ",
      "      ",
    ],
    '8': [
      " ████ ",
      "██  ██",
      "██  ██",
      " ████ ",
      "██  ██",
      " ████ ",
      "      ",
    ],
    '9': [
      " ████ ",
      "██  ██",
      "██  ██",
      " █████",
      "    ██",
      " ████ ",
      "      ",
    ],
    '!': [
      "  ██  ",
      "  ██  ",
      "  ██  ",
      "  ██  ",
      "      ",
      "  ██  ",
      "      ",
    ],
    '?': [
      " ████ ",
      "██  ██",
      "   ██ ",
      "  ██  ",
      "      ",
      "  ██  ",
      "      ",
    ],
    '.': [
      "      ",
      "      ",
      "      ",
      "      ",
      "  ██  ",
      "  ██  ",
      "      ",
    ],
    ',': [
      "      ",
      "      ",
      "      ",
      "      ",
      "  ██  ",
      "  ██  ",
      " ██   ",
    ],
    '-': [
      "      ",
      "      ",
      "      ",
      "██████",
      "      ",
      "      ",
      "      ",
    ],
    ' ': [
      "   ",
      "   ",
      "   ",
      "   ",
      "   ",
      "   ",
      "   ",
    ],
}

FONTS['block'] = BLOCK

# ── SLIM font (narrower, 5 rows tall) ─────────────────────────────────────────
SLIM = {
    'A': ["/\\  ", "/--\\", "/  \\"],
    'B': ["|_) ", "|_) ", "    "],
    'C': ["/-  ", "|   ", "\\_  "],
    'D': ["|\\  ", "| ) ", "|/  "],
    'E': ["|-- ", "|_  ", "|-- "],
    'F': ["|-- ", "|_  ", "|   "],
    'G': ["/-  ", "| _ ", "\\-/ "],
    'H': ["|_| ", "| | ", "    "],
    'I': ["--- ", " |  ", "--- "],
    'J': ["  | ", "  | ", "\\_/ "],
    'K': ["|\\ ", "|/ ", "    "],
    'L': ["|   ", "|   ", "|-- "],
    'M': ["|V| ", "| | ", "    "],
    'N': ["|\\  ", "| \\ ", "|  \\"],
    'O': ["/\\ ", "\\/ ", "   "],
    'P': ["|_) ", "|   ", "    "],
    'Q': ["/\\ ", "\\X ", "   "],
    'R': ["|_) ", "| \\ ", "    "],
    'S': ["/_ ", " _)", "/_  "],
    'T': ["--- ", " |  ", " |  "],
    'U': ["| | ", "| | ", "\\-/ "],
    'V': ["\\ / ", " V  ", "    "],
    'W': ["\\ / ", "V V ", "    "],
    'X': ["\\ / ", "_X_ ", "/ \\ "],
    'Y': ["\\ / ", " Y  ", " |  "],
    'Z': ["_/ ", "/  ", "/_ "],
    '0': ["O ", "O ", "  "],
    '1': ["| ", "| ", "  "],
    '2': ["_) ", "/  ", "/_ "],
    '3': ["_) ", "_) ", "   "],
    '4': ["|_|", "  |", "   "],
    '5': ["|_ ", " _)", "   "],
    '6': ["|_ ", "|_)", "   "],
    '7': ["-- ", " / ", "   "],
    '8': ["o ", "o ", "  "],
    '9': ["_) ", " ) ", "   "],
    '!': ["! ", "  ", "! "],
    '?': ["?) ", "  ", "? "],
    ' ': ["  ", "  ", "  "],
    '-': ["   ", "-- ", "   "],
    '.': ["  ", ". ", "  "],
}

FONTS['slim'] = SLIM


# ── ANSI color helpers ────────────────────────────────────────────────────────

COLORS = {
    'red':     '\033[91m',
    'green':   '\033[92m',
    'yellow':  '\033[93m',
    'blue':    '\033[94m',
    'magenta': '\033[95m',
    'cyan':    '\033[96m',
    'white':   '\033[97m',
    'reset':   '\033[0m',
    'bold':    '\033[1m',
    'rainbow': None,  # special case
}

RAINBOW_CYCLE = ['\033[91m', '\033[93m', '\033[92m', '\033[96m', '\033[94m', '\033[95m']


def colorize(text: str, color: str, rainbow_index: int = 0) -> str:
    if color == 'rainbow':
        c = RAINBOW_CYCLE[rainbow_index % len(RAINBOW_CYCLE)]
        return f"{c}{text}{COLORS['reset']}"
    if color in COLORS and COLORS[color]:
        return f"{COLORS['bold']}{COLORS[color]}{text}{COLORS['reset']}"
    return text


# ── Core rendering ────────────────────────────────────────────────────────────

def render(text: str, font: str = 'block', color: str = None, gap: int = 1) -> str:
    font_data = FONTS.get(font)
    if font_data is None:
        raise ValueError(f"Unknown font '{font}'. Available: {', '.join(FONTS.keys())}")

    text = text.upper()
    height = len(next(iter(font_data.values())))
    rows = [''] * height
    spacer = ' ' * gap

    for i, char in enumerate(text):
        glyph = font_data.get(char, font_data.get(' '))
        for row_idx, row in enumerate(glyph):
            if color:
                row = colorize(row, color, rainbow_index=i)
            rows[row_idx] += row + spacer

    return '\n'.join(rows)


# ── CLI ───────────────────────────────────────────────────────────────────────

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
    parser.add_argument('text', help='Text to render as ASCII art')
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
        print(output)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
