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
The Pillow-based character DB (_get_char_db) is retained for tests and for
future use in photo-to-ASCII rendering where sub-cell resolution is available.
"""

import logging as _logging
import string
from typing import Optional

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.effects.shape_fill"
__updated__ = "2026-03-28 00:00:00"
__version__ = "0.3.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

# Default character vocabulary for the Pillow-based DB (tests / future use)
SHAPE_CHARS: str = string.printable[:95]

# Cell dimensions used when rendering chars for the Pillow-based DB
_CELL_H: int = 16
_CELL_W: int = 8

# Module-level DB cache: (charset, cell_h, cell_w) → {char: [6 floats]}
_DB_CACHE: dict = {}

# Interior density ramp — densest (8 filled neighbors) to lightest (4 filled)
_INTERIOR_CHARS: str = "@#S%*+;:,. "


# -------------------------------------------------------------------------
def _require_pil() -> None:
    """Raise ImportError with install hint if Pillow is unavailable.

    :raises ImportError: If Pillow is not installed.
    """
    try:
        import PIL  # noqa: F401
    except ImportError:
        raise ImportError(
            "Shape fill character DB requires Pillow. Install with: uv add --dev Pillow"
        )


# -------------------------------------------------------------------------
def _find_mono_font(size: int):
    """Return a PIL ImageFont for a monospace face at the given size.

    :param size: Font size in pixels.
    :returns: PIL ImageFont instance.
    """
    from PIL import ImageFont

    candidates = [
        "DejaVuSansMono.ttf",
        "DejaVuSansMono",
        "LiberationMono-Regular.ttf",
        "UbuntuMono-R.ttf",
        "Courier New",
        "CourierNew.ttf",
        "cour.ttf",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


# -------------------------------------------------------------------------
def _char_zone_densities(char: str, cell_h: int, cell_w: int) -> list:
    """Render a character and compute its 6-zone ink density vector.

    Zones (2-column × 3-row):  UL UR / ML MR / LL LR

    :param char: Single character to render.
    :param cell_h: Cell height in pixels.
    :param cell_w: Cell width in pixels.
    :returns: List of 6 floats in [0.0, 1.0].
    """
    from PIL import Image, ImageDraw

    img = Image.new("L", (cell_w, cell_h), 0)
    draw = ImageDraw.Draw(img)
    font = _find_mono_font(cell_h - 2)
    draw.text((0, 0), char, fill=255, font=font)
    pixels = list(img.tobytes())

    def zone(r0: int, r1: int, c0: int, c1: int) -> float:
        total = sum(pixels[r * cell_w + c] for r in range(r0, r1) for c in range(c0, c1))
        area = (r1 - r0) * (c1 - c0)
        return total / (area * 255.0) if area > 0 else 0.0

    h2, h3, w2 = cell_h // 2, cell_h // 3, cell_w // 2
    return [
        zone(0,  h2,      0,  w2),
        zone(0,  h2,      w2, cell_w),
        zone(h3, 2 * h3,  0,  w2),
        zone(h3, 2 * h3,  w2, cell_w),
        zone(h2, cell_h,  0,  w2),
        zone(h2, cell_h,  w2, cell_w),
    ]


# -------------------------------------------------------------------------
def _build_char_db(charset: str, cell_h: int, cell_w: int) -> dict:
    """Precompute 6D shape vectors for every character in charset.

    :param charset: Characters to include.
    :param cell_h: Render height in pixels.
    :param cell_w: Render width in pixels.
    :returns: Dict mapping char → list of 6 floats.
    """
    _require_pil()
    db = {ch: _char_zone_densities(ch, cell_h, cell_w) for ch in charset}
    _LOGGER.debug("Built shape DB: %d chars at %d×%dpx", len(db), cell_h, cell_w)
    return db


# -------------------------------------------------------------------------
def _get_char_db(charset: str = SHAPE_CHARS) -> dict:
    """Return the cached Pillow-based shape DB for charset.

    :param charset: Character vocabulary.
    :returns: Dict mapping char → list of 6 floats.
    """
    key = (charset, _CELL_H, _CELL_W)
    if key not in _DB_CACHE:
        _DB_CACHE[key] = _build_char_db(charset, _CELL_H, _CELL_W)
    return _DB_CACHE[key]


# -------------------------------------------------------------------------
def _nearest_char(vec: list, db: dict) -> str:
    """Find the character whose shape vector is nearest to vec.

    :param vec: 6D input vector.
    :param db: Shape DB from _get_char_db().
    :returns: Best-matching character string.
    """
    best_char = " "
    best_dist = float("inf")
    for ch, cv in db.items():
        dist = sum((a - b) ** 2 for a, b in zip(vec, cv))
        if dist < best_dist:
            best_dist = dist
            best_char = ch
    return best_char


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
