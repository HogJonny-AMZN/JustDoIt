"""
Package: justdoit.core.rasterizer
Core text-to-ASCII-art rendering engine.

Handles glyph lookup, optional fill pass, colorization, and row assembly.
The fill registry (_FILL_FNS) maps fill names to fill functions from effects.fill.
"""

import logging as _logging
from typing import Optional

from justdoit.fonts import FONTS
from justdoit.effects.color import colorize
from justdoit.core.glyph import glyph_to_mask
from justdoit.effects.fill import density_fill, sdf_fill

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.core.rasterizer"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_FILL_FNS: dict = {
    "density": density_fill,
    "sdf": sdf_fill,
}


# -------------------------------------------------------------------------
def render(
    text: str,
    font: str = "block",
    color: Optional[str] = None,
    gap: int = 1,
    fill: Optional[str] = None,
) -> str:
    """Render text as multi-line ASCII art with optional color and fill effects.

    :param text: Input string (case-insensitive; uppercased internally).
    :param font: Font name — 'block', 'slim', or any registered FIGlet/TTF font.
    :param color: ANSI color name or 'rainbow' (default: no color).
    :param gap: Column gap between characters in spaces (default: 1).
    :param fill: Fill style — None (default block chars), 'density', or 'sdf'.
    :returns: Multi-line string — rows joined by newlines.
    :raises ValueError: If font or fill name is unknown, or gap is negative.
    """
    if gap < 0:
        raise ValueError(f"gap must be >= 0, got {gap}")

    font_data = FONTS.get(font)
    if font_data is None:
        raise ValueError(f"Unknown font '{font}'. Available: {', '.join(FONTS.keys())}")

    if fill is not None and fill not in _FILL_FNS:
        raise ValueError(f"Unknown fill '{fill}'. Available: {', '.join(_FILL_FNS.keys())}")

    text = text.upper()
    height = len(next(iter(font_data.values())))
    rows = [""] * height
    spacer = " " * gap
    fill_fn = _FILL_FNS.get(fill)

    for i, char in enumerate(text):
        glyph = font_data.get(char, font_data.get(" "))

        if fill_fn is not None:
            # Collect ink chars present in this glyph (works for block and slim fonts).
            ink = "".join({ch for row in glyph for ch in row if ch != " "}) or "█"
            mask = glyph_to_mask(glyph, ink_chars=ink)
            glyph = fill_fn(mask)

        for row_idx, row in enumerate(glyph):
            if color:
                row = colorize(row, color, rainbow_index=i)
            rows[row_idx] += row + spacer

    return "\n".join(rows)
