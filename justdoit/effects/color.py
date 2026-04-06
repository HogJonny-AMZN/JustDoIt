"""
Package: justdoit.effects.color
ANSI terminal colorization for ASCII art output.

Provides flat color, bold color, and rainbow (per-character cycling) modes.
All ANSI codes target 256-color-compatible terminals.

Also provides C11 — fill-float → per-cell 24-bit color mapping:
  fill_float_colorize(text, float_grid, palette) → str
  Standard palettes: FIRE_PALETTE, LAVA_PALETTE, SPECTRAL_PALETTE, BIO_PALETTE
  PALETTE_REGISTRY: dict mapping palette names to palette lists
"""

import logging as _logging
import re as _re

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.effects.color"
__updated__ = "2026-04-06 00:00:00"
__version__ = "0.2.0"
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
# C11 — Standard palettes (float 0.0 → 1.0 maps to first → last entry)
# Each entry is an (r, g, b) tuple; linear interpolation between entries.

FIRE_PALETTE: list = [
    (20, 0, 0),       # 0.0 — near-black ember
    (120, 0, 0),      # 0.2 — dark red
    (200, 30, 0),     # 0.4 — orange-red
    (240, 120, 0),    # 0.6 — orange
    (255, 220, 40),   # 0.8 — yellow
    (255, 255, 200),  # 1.0 — white-hot
]

LAVA_PALETTE: list = [
    (10, 0, 20),      # 0.0 — deep violet
    (80, 0, 80),      # 0.2 — purple
    (180, 20, 0),     # 0.5 — deep orange
    (240, 100, 0),    # 0.7 — bright orange
    (255, 220, 80),   # 0.9 — yellow
    (255, 255, 200),  # 1.0 — white center
]

SPECTRAL_PALETTE: list = [
    (200, 0, 200),    # 0.0 — violet
    (0, 0, 255),      # 0.2 — blue
    (0, 200, 200),    # 0.4 — cyan
    (0, 200, 0),      # 0.6 — green
    (200, 200, 0),    # 0.8 — yellow
    (255, 50, 0),     # 1.0 — red
]

BIO_PALETTE: list = [
    (5, 30, 5),       # 0.0 — near-black bio-dark
    (20, 80, 20),     # 0.25 — dark green
    (60, 140, 60),    # 0.5 — mid green
    (120, 200, 80),   # 0.75 — light green
    (200, 240, 160),  # 1.0 — pale lime
]

PALETTE_REGISTRY: dict = {
    "fire":     FIRE_PALETTE,
    "lava":     LAVA_PALETTE,
    "spectral": SPECTRAL_PALETTE,
    "bio":      BIO_PALETTE,
}

# -------------------------------------------------------------------------
# Internal helpers for C11
_ANSI_RE_COLOR = _re.compile(r"\033\[[0-9;]*m")
_RESET_C11 = "\033[0m"


def _tc_c11(r: int, g: int, b: int) -> str:
    """Return a 24-bit true-color ANSI foreground code.

    :param r: Red channel 0–255.
    :param g: Green channel 0–255.
    :param b: Blue channel 0–255.
    :returns: ANSI escape string.
    """
    return f"\033[38;2;{r};{g};{b}m"


def _lerp_palette(palette: list, t: float) -> tuple:
    """Linearly interpolate through a palette of (r, g, b) stops.

    :param palette: List of (r, g, b) tuples from float=0.0 to float=1.0.
    :param t: Float in [0.0, 1.0].
    :returns: Interpolated (r, g, b) tuple.
    """
    n = len(palette)
    if n == 0:
        return (255, 255, 255)
    if n == 1:
        return palette[0]
    t = max(0.0, min(1.0, t))
    scaled = t * (n - 1)
    lo = int(scaled)
    hi = min(lo + 1, n - 1)
    frac = scaled - lo
    a, b_ = palette[lo], palette[hi]
    return (
        int(a[0] + (b_[0] - a[0]) * frac),
        int(a[1] + (b_[1] - a[1]) * frac),
        int(a[2] + (b_[2] - a[2]) * frac),
    )


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


# -------------------------------------------------------------------------
def fill_float_colorize(
    text: str,
    float_grid: list,
    palette: list,
) -> str:
    """Apply per-cell 24-bit color to a rendered ASCII art string (C11).

    Each visible (non-space) character cell is colored by looking up its
    float value in ``float_grid`` and interpolating through ``palette``.
    Space cells (exterior) are left uncolored. Existing ANSI sequences in
    ``text`` are stripped and replaced.

    :param text: Multi-line rendered string from render() — with or without
        existing ANSI codes. Rows separated by newlines.
    :param float_grid: 2D list of floats indexed as float_grid[row][col].
        Values should be in [0.0, 1.0]. Cells not present in the grid default
        to float value 0.0.
    :param palette: List of (r, g, b) tuples defining the color gradient from
        float=0.0 (index 0) to float=1.0 (last index). Use FIRE_PALETTE,
        LAVA_PALETTE, SPECTRAL_PALETTE, BIO_PALETTE, or a custom list.
    :returns: Multi-line string with 24-bit ANSI true-color applied per cell.
    """
    lines = text.split("\n")
    n_rows = len(lines)
    result = []

    for row_idx, line in enumerate(lines):
        # Strip existing ANSI codes to get clean character sequence
        clean = _ANSI_RE_COLOR.sub("", line)
        out = ""
        float_row = float_grid[row_idx] if row_idx < len(float_grid) else []
        for col_idx, ch in enumerate(clean):
            if ch == " ":
                out += ch
            else:
                # Look up float value; default to 0.0 if out of bounds
                fval = float_row[col_idx] if col_idx < len(float_row) else 0.0
                rgb = _lerp_palette(palette, fval)
                out += _tc_c11(*rgb) + ch + _RESET_C11
        result.append(out)

    return "\n".join(result)
