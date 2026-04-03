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
from justdoit.effects.generative import noise_fill, cells_fill, truchet_fill, reaction_diffusion_fill, slime_mold_fill, strange_attractor_fill, lsystem_fill, turing_fill, wave_fill, fractal_fill, voronoi_fill, plasma_fill
from justdoit.effects.shape_fill import shape_fill
from justdoit.effects.recursive import typographic_recursion

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.core.rasterizer"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_FILL_FNS: dict = {
    "density":   density_fill,
    "sdf":       sdf_fill,
    "noise":     noise_fill,
    "cells":     cells_fill,
    "truchet":   truchet_fill,
    "rd":        reaction_diffusion_fill,
    "slime":     slime_mold_fill,
    "attractor": strange_attractor_fill,
    "lsystem":   lsystem_fill,
    "shape":     shape_fill,
    "turing":    turing_fill,
    "wave":           wave_fill,
    "fractal":        fractal_fill,
    "voronoi":        voronoi_fill,
    "voronoi_cracked": lambda m: voronoi_fill(m, preset="cracked"),
    "voronoi_fine":    lambda m: voronoi_fill(m, preset="fine"),
    "voronoi_coarse":  lambda m: voronoi_fill(m, preset="coarse"),
    "voronoi_cells":   lambda m: voronoi_fill(m, preset="cells"),
    "plasma":          plasma_fill,
    "plasma_tight":    lambda m, **kw: plasma_fill(m, preset="tight", **kw),
    "plasma_slow":     lambda m, **kw: plasma_fill(m, preset="slow", **kw),
    "plasma_diagonal": lambda m, **kw: plasma_fill(m, preset="diagonal", **kw),
}


# -------------------------------------------------------------------------
def render(
    text: str,
    font: str = "block",
    color: Optional[str] = None,
    gap: int = 1,
    fill: Optional[str] = None,
    recursion: bool = False,
    recursion_separator: str = " ",
    fill_kwargs: Optional[dict] = None,
) -> str:
    """Render text as multi-line ASCII art with optional color and fill effects.

    :param text: Input string (case-insensitive; uppercased internally).
    :param font: Font name — 'block', 'slim', or any registered FIGlet/TTF font.
    :param color: ANSI color name or 'rainbow' (default: no color).
    :param gap: Column gap between characters in spaces (default: 1).
    :param fill: Fill style — None (default block chars), 'density', or 'sdf'.
    :param recursion: If True, apply typographic recursion (N01): fill cells with
        source text chars cycling. Each "pixel" of the large letter is a char
        from the word itself.
    :param recursion_separator: Separator between word cycles in recursion mode
        (default: single space).
    :param fill_kwargs: Optional dict of extra keyword arguments forwarded to the
        fill function (e.g. ``{"t": 1.2, "preset": "tight"}`` for plasma_fill).
        Ignored when fill is None. Default: None.
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

    text_upper = text.upper()
    height = len(next(iter(font_data.values())))
    rows = [""] * height
    spacer = " " * gap
    fill_fn = _FILL_FNS.get(fill)

    # When recursion is active, defer colorization until after recursion so that
    # ANSI escape codes don't interfere with the character-replacement pass.
    defer_color = recursion and bool(color)

    for i, char in enumerate(text_upper):
        glyph = font_data.get(char, font_data.get(" "))

        if fill_fn is not None:
            # Collect ink chars present in this glyph (works for block and slim fonts).
            ink = "".join({ch for row in glyph for ch in row if ch != " "}) or "█"
            mask = glyph_to_mask(glyph, ink_chars=ink)
            extra = fill_kwargs or {}
            glyph = fill_fn(mask, **extra)

        for row_idx, row in enumerate(glyph):
            if color and not defer_color:
                row = colorize(row, color, rainbow_index=i)
            rows[row_idx] += row + spacer

    # Apply typographic recursion post-process (N01) on clean (uncolored) rows
    if recursion:
        rows = typographic_recursion(rows, text, separator=recursion_separator)

    # Apply deferred colorization after recursion (per-row, column-based index)
    if defer_color:
        rows = [colorize(row, color, rainbow_index=idx) for idx, row in enumerate(rows)]

    return "\n".join(rows)
