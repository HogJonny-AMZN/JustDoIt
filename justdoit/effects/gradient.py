"""
Package: justdoit.effects.gradient
True-color ANSI gradient and palette effects for ASCII art rendering.

Operates on fully-rendered multi-line strings (output of render()).
Uses 24-bit true-color ANSI codes (\033[38;2;r;g;bm) for foreground color.

Implemented techniques:
  C01 — linear_gradient:  horizontal, vertical, or diagonal gradient across text block
  C02 — radial_gradient:  gradient radiating from center of text block outward
  C03 — per_glyph_palette: each character column group cycles through a color palette
  C07 — true-color ANSI:  24-bit RGB via \033[38;2;r;g;bm (used by all effects here)

All functions:
  - Accept plain or ANSI-colored multi-line strings
  - Apply true-color codes per visible character (ANSI sequences preserved/replaced)
  - Are pure Python stdlib — no external dependencies
"""

import logging as _logging
import math
import re
from typing import Optional

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.effects.gradient"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

# Regex matching a single ANSI escape sequence
_ANSI_RE = re.compile(r"\033\[[0-9;]*m")

# Reset code
_RESET = "\033[0m"

# Named color shortcuts — (r, g, b)
NAMED_COLORS: dict = {
    "red":     (255, 50,  50),
    "green":   (50,  220, 80),
    "yellow":  (255, 220, 50),
    "blue":    (80,  120, 255),
    "magenta": (220, 80,  220),
    "cyan":    (80,  220, 220),
    "white":   (255, 255, 255),
    "black":   (0,   0,   0),
    "orange":  (255, 140, 0),
    "pink":    (255, 100, 180),
    "purple":  (140, 60,  200),
    "gold":    (255, 200, 0),
}


# -------------------------------------------------------------------------
def parse_color(spec: str) -> tuple:
    """Parse a color specification into an (r, g, b) tuple.

    Accepts:
      - Named color: "red", "cyan", etc. (see NAMED_COLORS)
      - Hex string: "ff0080" or "#ff0080"

    :param spec: Color specification string.
    :returns: (r, g, b) tuple with values 0–255.
    :raises ValueError: If the spec is unrecognized or invalid hex.
    """
    spec = spec.strip().lower().lstrip("#")
    if spec in NAMED_COLORS:
        return NAMED_COLORS[spec]
    if len(spec) == 6:
        try:
            r = int(spec[0:2], 16)
            g = int(spec[2:4], 16)
            b = int(spec[4:6], 16)
            return (r, g, b)
        except ValueError:
            pass
    raise ValueError(
        f"Unrecognized color {spec!r}. Use a named color ({', '.join(NAMED_COLORS)}) "
        "or a 6-digit hex string (e.g. ff8800)."
    )


# -------------------------------------------------------------------------
def tc(r: int, g: int, b: int) -> str:
    """Return a 24-bit true-color ANSI foreground escape code.

    :param r: Red channel 0–255.
    :param g: Green channel 0–255.
    :param b: Blue channel 0–255.
    :returns: ANSI escape string for the given RGB color.
    """
    return f"\033[38;2;{r};{g};{b}m"


# -------------------------------------------------------------------------
def _lerp_color(a: tuple, b: tuple, t: float) -> tuple:
    """Linearly interpolate between two RGB colors.

    :param a: Start color (r, g, b).
    :param b: End color (r, g, b).
    :param t: Interpolation factor 0.0 (a) to 1.0 (b).
    :returns: Interpolated (r, g, b) tuple.
    """
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


# -------------------------------------------------------------------------
def _tokenize(line: str) -> list:
    """Split a line into alternating ANSI-escape and visible-character tokens.

    :param line: String potentially containing ANSI escape codes.
    :returns: List of (kind, text) tuples where kind is 'ansi' or 'char'.
    """
    tokens = []
    pos = 0
    for match in _ANSI_RE.finditer(line):
        start, end = match.span()
        # Visible chars before this escape
        for ch in line[pos:start]:
            tokens.append(("char", ch))
        tokens.append(("ansi", match.group()))
        pos = end
    # Remaining visible chars
    for ch in line[pos:]:
        tokens.append(("char", ch))
    return tokens


# -------------------------------------------------------------------------
def _apply_color_map(lines: list, color_fn) -> str:
    """Apply a per-character color function to a list of text lines.

    color_fn receives (row_index, col_index, total_rows, total_cols) and
    returns an (r, g, b) tuple. Existing ANSI sequences are stripped and
    replaced with the new true-color codes.

    :param lines: List of strings — one per row.
    :param color_fn: Callable(row, col, n_rows, n_cols) -> (r, g, b).
    :returns: Multi-line string with true-color ANSI codes applied.
    """
    n_rows = len(lines)
    # Measure visible width as max visible chars across all lines
    n_cols = max(
        (sum(1 for t in _tokenize(ln) if t[0] == "char") for ln in lines),
        default=1,
    )

    result_lines = []
    for row_idx, line in enumerate(lines):
        tokens = _tokenize(line)
        out = ""
        col_idx = 0
        for kind, text in tokens:
            if kind == "ansi":
                # Drop existing color codes — we're replacing them
                continue
            # Apply our color to this visible character
            r, g, b = color_fn(row_idx, col_idx, n_rows, n_cols)
            out += tc(r, g, b) + text
            col_idx += 1
        out += _RESET
        result_lines.append(out)

    return "\n".join(result_lines)


# -------------------------------------------------------------------------
def linear_gradient(
    text: str,
    from_color: tuple,
    to_color: tuple,
    direction: str = "horizontal",
) -> str:
    """Apply a linear gradient across the text block (C01).

    :param text: Multi-line rendered string from render().
    :param from_color: Start (r, g, b) color tuple.
    :param to_color: End (r, g, b) color tuple.
    :param direction: "horizontal" (left→right), "vertical" (top→bottom),
                      or "diagonal" (top-left→bottom-right).
    :returns: Multi-line string with 24-bit ANSI true-color gradient applied.
    :raises ValueError: If direction is not recognized.
    """
    if direction not in ("horizontal", "vertical", "diagonal"):
        raise ValueError(
            f"direction must be 'horizontal', 'vertical', or 'diagonal', got {direction!r}"
        )
    if not text:
        return text

    lines = text.split("\n")

    def color_fn(row: int, col: int, n_rows: int, n_cols: int) -> tuple:
        if direction == "horizontal":
            t = col / max(n_cols - 1, 1)
        elif direction == "vertical":
            t = row / max(n_rows - 1, 1)
        else:  # diagonal
            t = (col / max(n_cols - 1, 1) + row / max(n_rows - 1, 1)) / 2.0
        return _lerp_color(from_color, to_color, t)

    return _apply_color_map(lines, color_fn)


# -------------------------------------------------------------------------
def radial_gradient(
    text: str,
    inner_color: tuple,
    outer_color: tuple,
) -> str:
    """Apply a radial gradient radiating outward from the text block center (C02).

    :param text: Multi-line rendered string from render().
    :param inner_color: Color at the center (r, g, b).
    :param outer_color: Color at the edges (r, g, b).
    :returns: Multi-line string with 24-bit ANSI radial gradient applied.
    """
    if not text:
        return text

    lines = text.split("\n")

    def color_fn(row: int, col: int, n_rows: int, n_cols: int) -> tuple:
        # Normalized distance from center (0.0 = center, 1.0 = corner)
        dr = (row - (n_rows - 1) / 2.0) / max((n_rows - 1) / 2.0, 1)
        dc = (col - (n_cols - 1) / 2.0) / max((n_cols - 1) / 2.0, 1)
        t = min(1.0, math.sqrt(dr * dr + dc * dc) / math.sqrt(2.0))
        return _lerp_color(inner_color, outer_color, t)

    return _apply_color_map(lines, color_fn)


# -------------------------------------------------------------------------
def per_glyph_palette(
    text: str,
    palette: list,
) -> str:
    """Color each character column group using a cycling palette (C03).

    The palette cycles per column position, so each glyph in the rendered
    text gets a distinct color from the sequence.

    :param text: Multi-line rendered string from render().
    :param palette: List of (r, g, b) color tuples — cycles if fewer than columns.
    :returns: Multi-line string with per-column palette colors applied.
    :raises ValueError: If palette is empty.
    """
    if not palette:
        raise ValueError("palette must contain at least one color")
    if not text:
        return text

    lines = text.split("\n")
    n = len(palette)

    def color_fn(row: int, col: int, n_rows: int, n_cols: int) -> tuple:
        return palette[col % n]

    return _apply_color_map(lines, color_fn)


# -------------------------------------------------------------------------
# Preset palettes — ready to use from the CLI or API

FIRE_PALETTE: list = [
    (255, 0,   0),
    (255, 60,  0),
    (255, 120, 0),
    (255, 180, 0),
    (255, 220, 0),
    (255, 255, 80),
]

OCEAN_PALETTE: list = [
    (0,   40,  120),
    (0,   80,  180),
    (0,   160, 220),
    (80,  220, 240),
    (160, 240, 255),
]

NEON_PALETTE: list = [
    (255, 0,   200),
    (0,   255, 200),
    (255, 200, 0),
    (0,   200, 255),
    (200, 0,   255),
]

RAINBOW_PALETTE: list = [
    (255, 0,   0),
    (255, 127, 0),
    (255, 255, 0),
    (0,   200, 0),
    (0,   0,   255),
    (75,  0,   130),
    (148, 0,   211),
]

PRESETS: dict = {
    "fire":    FIRE_PALETTE,
    "ocean":   OCEAN_PALETTE,
    "neon":    NEON_PALETTE,
    "rainbow": RAINBOW_PALETTE,
}
