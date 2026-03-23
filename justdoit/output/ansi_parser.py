"""
Package: justdoit.output.ansi_parser
ANSI escape sequence parser for output target rendering.

Walks a string containing ANSI color codes and produces a flat list of
(char, color) tokens where color is an (r, g, b) tuple or None (default).

Supports:
  - 24-bit true-color foreground: \033[38;2;r;g;bm  (from effects.gradient)
  - 8-color bright foreground:    \033[9Xm           (X = 1-7)
  - Bold:                         \033[1m            (recorded but not used for color)
  - Dim:                          \033[2m            (recorded)
  - Reset:                        \033[0m
"""

import logging as _logging
import re
from typing import Optional

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.output.ansi_parser"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_ANSI_RE = re.compile(r"\033\[([0-9;]*)m")

# Maps standard bright ANSI color codes (91–97) to (r, g, b)
_ANSI_BRIGHT: dict = {
    91: (255,  80,  80),   # red
    92: ( 80, 220,  80),   # green
    93: (255, 220,  50),   # yellow
    94: ( 80, 120, 255),   # blue
    95: (220,  80, 220),   # magenta
    96: ( 80, 220, 220),   # cyan
    97: (255, 255, 255),   # white
}

# Default text color (white on dark background)
DEFAULT_COLOR: tuple = (220, 220, 220)


# -------------------------------------------------------------------------
def parse(text: str) -> list:
    """Parse a string with ANSI codes into a list of (char, color) tokens.

    Each token is a 2-tuple:
      - char:  a single visible character (never an escape sequence)
      - color: (r, g, b) tuple, or None to use DEFAULT_COLOR

    Newlines are included as ("\\n", None) tokens.

    :param text: String containing ANSI escape codes and visible characters.
    :returns: List of (char, color) tuples.
    """
    tokens = []
    current_color: Optional[tuple] = None
    pos = 0

    for match in _ANSI_RE.finditer(text):
        start, end = match.span()
        # Emit visible chars before this escape
        for ch in text[pos:start]:
            tokens.append((ch, current_color))
        # Update current color state
        current_color = _parse_sgr(match.group(1), current_color)
        pos = end

    # Remaining visible chars after last escape
    for ch in text[pos:]:
        tokens.append((ch, current_color))

    return tokens


# -------------------------------------------------------------------------
def _parse_sgr(params_str: str, current: Optional[tuple]) -> Optional[tuple]:
    """Parse an SGR parameter string and return the new current color.

    :param params_str: Semicolon-separated parameter string from \033[...m.
    :param current: The current (r, g, b) color before this sequence.
    :returns: Updated (r, g, b) color, or None for reset/default.
    """
    if not params_str:
        return None

    parts = params_str.split(";")
    try:
        nums = [int(p) for p in parts if p]
    except ValueError:
        return current

    i = 0
    while i < len(nums):
        n = nums[i]
        if n == 0:
            # Reset
            return None
        elif n == 38 and i + 4 < len(nums) and nums[i + 1] == 2:
            # 24-bit true color: 38;2;r;g;b
            r, g, b = nums[i + 2], nums[i + 3], nums[i + 4]
            return (
                max(0, min(255, r)),
                max(0, min(255, g)),
                max(0, min(255, b)),
            )
        elif n in _ANSI_BRIGHT:
            return _ANSI_BRIGHT[n]
        # Bold (1), dim (2), etc — don't change color
        i += 1

    return current


# -------------------------------------------------------------------------
def effective_color(color: Optional[tuple]) -> tuple:
    """Return the effective (r, g, b) color, substituting DEFAULT_COLOR for None.

    :param color: Color tuple or None.
    :returns: (r, g, b) tuple.
    """
    return color if color is not None else DEFAULT_COLOR
