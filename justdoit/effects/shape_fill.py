"""
Package: justdoit.effects.shape_fill
Shape-vector / contour-following fill (F07).

Uses 4-cardinal-neighbor connectivity to classify each ink cell:

  - Exterior  (mask == 0): space
  - Interior  (all 4 cardinal neighbors have ink): density char scaled by
      8-neighbor fill count — fully surrounded → densest, near-edge → lighter
  - Edge      (≥1 cardinal neighbor is empty): directional char that draws the
      glyph boundary passing through that cell:
        top+left empty  →  /   top+right empty  →  \\
        bottom+left     →  \\  bottom+right      →  /
        top/bottom only →  -   left/right only   →  |
        complex junction → +

This approach works correctly at character resolution (1 mask cell = 1 output
cell) because it reads the *connectivity pattern* of the binary mask rather
than trying to differentiate continuous SDF gradient levels that do not exist
at this resolution.

Pure Python at render time — no external dependencies.
The Pillow-based character DB is in justdoit.core.char_db and is used by
the image-to-ASCII pipeline (G09) and tests.
"""

import logging as _logging
from typing import Optional

from justdoit.core.char_db import (
    PRINTABLE_ASCII as SHAPE_CHARS,
    get_char_db as _get_char_db,
    nearest_char as _nearest_char,
)

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.effects.shape_fill"
__updated__ = "2026-04-24 00:00:00"
__version__ = "0.4.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

# Interior density ramp — densest (8 filled neighbors) to lightest (4 filled)
_INTERIOR_CHARS: str = "@#S%*+;:,. "


# -------------------------------------------------------------------------
def _cell_char(mask: list, r: int, c: int, rows: int, cols: int) -> str:
    """Select a character for an ink cell using 4-cardinal neighbor analysis.

    Classifies the cell by examining which cardinal directions (top, bottom,
    left, right) have empty (non-ink) cells, then maps that connectivity
    pattern to a directional character that visually draws the boundary:

      - All 4 filled  → interior density char (8-neighbor count)
      - Top+left      → /    Top+right  → \\
      - Bottom+left   → \\   Bottom+right → /
      - Top/bottom    → -    Left/right → |
      - Complex       → +

    :param mask: 2D list of floats (0.0=empty, 1.0=ink).
    :param r: Row index.
    :param c: Column index.
    :param rows: Grid row count.
    :param cols: Grid column count.
    :returns: Single character.
    """
    def empty(dr: int, dc: int) -> bool:
        nr, nc = r + dr, c + dc
        if not (0 <= nr < rows and 0 <= nc < cols):
            return True  # treat out-of-bounds as empty
        return mask[nr][nc] <= 0.5

    t  = empty(-1,  0)
    b  = empty(+1,  0)
    le = empty( 0, -1)
    ri = empty( 0, +1)

    # Interior: all 4 cardinal neighbors have ink
    if not (t or b or le or ri):
        filled = sum(
            1
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if (dr, dc) != (0, 0)
            and 0 <= r + dr < rows
            and 0 <= c + dc < cols
            and mask[r + dr][c + dc] > 0.5
        )
        # filled = 0–8; 8 = deep interior → densest char
        n = len(_INTERIOR_CHARS)
        idx = int((8 - filled) * (n - 1) / 8)
        return _INTERIOR_CHARS[max(0, min(n - 1, idx))]

    # Corner: exactly one vertical + one horizontal cardinal empty
    if t and le and not b and not ri:  return "/"
    if t and ri and not b and not le:  return "\\"
    if b and le and not t and not ri:  return "\\"
    if b and ri and not t and not le:  return "/"

    # Edge: count empties per axis to determine dominant boundary direction
    v_count = int(t) + int(b)    # empties on vertical axis → horizontal boundary
    h_count = int(le) + int(ri)  # empties on horizontal axis → vertical boundary

    if v_count > h_count:  return "-"
    if h_count > v_count:  return "|"

    # Equal (e.g. all 4 empty = isolated cell, or T-junction)
    return "+"


# -------------------------------------------------------------------------
def shape_fill(mask: list, charset: Optional[str] = None) -> list:
    """Fill using 4-neighbor connectivity character selection (F07).

    Each ink cell is assigned a character that visually draws the glyph
    boundary passing through it, based on which of its four cardinal
    neighbors (top / bottom / left / right) are empty:

      - Exterior cells (mask == 0): space
      - Interior cells (all 4 cardinal neighbors have ink): density char
          chosen by 8-neighbor fill count (@→lightest; deep interior→dense)
      - Edge cells: directional char matching the boundary orientation
          /  \\  -  |  +

    Pure Python — no external dependencies at render time.

    :param mask: 2D list of floats from glyph_to_mask() — values 0.0–1.0.
    :param charset: Unused in default mode; reserved for future photo-to-ASCII
        rendering where a Pillow-based character DB will be used.
    :returns: List of strings — one per row, same shape as input mask.
    """
    rows = len(mask)
    cols = len(mask[0]) if mask else 0

    if not any(mask[r][c] > 0.5 for r in range(rows) for c in range(cols)):
        return [" " * cols for _ in range(rows)]

    result = []
    for r in range(rows):
        line = ""
        for c in range(cols):
            if mask[r][c] <= 0.5:
                line += " "
            else:
                line += _cell_char(mask, r, c, rows, cols)
        result.append(line)
    return result
