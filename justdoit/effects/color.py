"""
Package: justdoit.effects.color
ANSI terminal colorization for ASCII art output.

Provides flat color, bold color, and rainbow (per-character cycling) modes.
All ANSI codes target 256-color-compatible terminals.
"""

import logging as _logging

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.effects.color"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

COLORS: dict = {
    "red":     "\033[91m",
    "green":   "\033[92m",
    "yellow":  "\033[93m",
    "blue":    "\033[94m",
    "magenta": "\033[95m",
    "cyan":    "\033[96m",
    "white":   "\033[97m",
    "reset":   "\033[0m",
    "bold":    "\033[1m",
    "rainbow": None,  # special case — handled in colorize()
}

RAINBOW_CYCLE: list = [
    "\033[91m",  # red
    "\033[93m",  # yellow
    "\033[92m",  # green
    "\033[96m",  # cyan
    "\033[94m",  # blue
    "\033[95m",  # magenta
]


# -------------------------------------------------------------------------
def colorize(text: str, color: str, rainbow_index: int = 0) -> str:
    """Wrap text in ANSI escape codes for the given color.

    For 'rainbow', cycles through RAINBOW_CYCLE using rainbow_index.
    For all other colors, applies bold + the named color code.
    Returns text unchanged if color is unrecognized.

    :param text: The string to colorize.
    :param color: Color name from COLORS, or 'rainbow'.
    :param rainbow_index: Character index used to select rainbow cycle position.
    :returns: ANSI-wrapped string.
    """
    if color == "rainbow":
        c = RAINBOW_CYCLE[rainbow_index % len(RAINBOW_CYCLE)]
        return f"{c}{text}{COLORS['reset']}"
    if color in COLORS and COLORS[color]:
        return f"{COLORS['bold']}{COLORS[color]}{text}{COLORS['reset']}"
    return text
