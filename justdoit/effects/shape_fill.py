"""
Package: justdoit.effects.shape_fill
Shape-vector character matching fill (F07).

Implements a 6-dimensional shape-vector approach inspired by the character-
morphology matching technique described in ASCII art rendering research.
Each candidate character is described by ink density in 6 spatial zones
(2-column × 3-row). During fill, each mask cell's local ink distribution
is sampled using 2×2 corner averages across its neighborhood, then matched
to the nearest character in the precomputed shape DB.

Unlike density fill (1D brightness → fixed density char), shape fill captures
directional ink distribution: edge cells yield directional characters (/ \\ | -)
that follow contours; interior cells yield solid chars; exterior cells yield space.

Pillow-gated: DB precomputation requires Pillow (render chars to bitmaps).
Matching at render time is pure Python — no additional dependencies.
"""

import logging as _logging
import string
from typing import Optional

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.effects.shape_fill"
__updated__ = "2026-03-27 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

# Default character vocabulary — all 95 printable ASCII chars
SHAPE_CHARS: str = string.printable[:95]

# Cell dimensions (pixels) used when rendering chars for the shape DB.
# These represent typical monospace terminal proportions (2:1 height:width).
_CELL_H: int = 16
_CELL_W: int = 8

# Module-level cache: (charset, cell_h, cell_w) → {char: [6 floats]}
_DB_CACHE: dict = {}


# -------------------------------------------------------------------------
def _require_pil() -> None:
    """Raise ImportError with install hint if Pillow is unavailable.

    :raises ImportError: If Pillow is not installed.
    """
    try:
        import PIL  # noqa: F401
    except ImportError:
        raise ImportError(
            "Shape fill requires Pillow. Install with: uv add --dev Pillow"
        )


# -------------------------------------------------------------------------
def _find_mono_font(size: int):
    """Return a PIL ImageFont for a monospace face at the given size.

    Tries common system monospace fonts in order; falls back to PIL default.

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

    Zones (2-column × 3-row layout):
        UL  UR     rows 0   .. h/2,     cols 0..w/2 and w/2..w
        ML  MR     rows h/3 .. 2h/3,    cols 0..w/2 and w/2..w
        LL  LR     rows h/2 .. h,       cols 0..w/2 and w/2..w

    :param char: Single character to render.
    :param cell_h: Cell height in pixels.
    :param cell_w: Cell width in pixels.
    :returns: List of 6 floats in [0.0, 1.0] — [UL, UR, ML, MR, LL, LR].
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

    h2 = cell_h // 2
    h3 = cell_h // 3
    w2 = cell_w // 2

    return [
        zone(0,   h2,      0,  w2),        # UL
        zone(0,   h2,      w2, cell_w),    # UR
        zone(h3,  2 * h3,  0,  w2),        # ML (middle band, left)
        zone(h3,  2 * h3,  w2, cell_w),    # MR (middle band, right)
        zone(h2,  cell_h,  0,  w2),        # LL
        zone(h2,  cell_h,  w2, cell_w),    # LR
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
    """Return the cached shape DB for charset, building it if needed.

    :param charset: Character vocabulary.
    :returns: Dict mapping char → list of 6 floats.
    """
    key = (charset, _CELL_H, _CELL_W)
    if key not in _DB_CACHE:
        _DB_CACHE[key] = _build_char_db(charset, _CELL_H, _CELL_W)
    return _DB_CACHE[key]


# -------------------------------------------------------------------------
def _sample_cell(mask: list, r: int, c: int) -> list:
    """Sample the 6-zone neighborhood vector for cell (r, c).

    Uses 2×2 corner averages to capture directional ink distribution:

        UL = avg(mask[r-1][c-1], mask[r-1][c], mask[r][c-1], mask[r][c])
        UR = avg(mask[r-1][c],   mask[r-1][c+1], mask[r][c], mask[r][c+1])
        ML = avg(mask[r][c-1], mask[r][c])
        MR = avg(mask[r][c],   mask[r][c+1])
        LL = avg(mask[r][c-1], mask[r][c], mask[r+1][c-1], mask[r+1][c])
        LR = avg(mask[r][c],   mask[r][c+1], mask[r+1][c], mask[r+1][c+1])

    Out-of-bounds indices are clamped to the mask boundary.

    :param mask: 2D list of floats (GlyphMask).
    :param r: Row index.
    :param c: Column index.
    :returns: List of 6 floats in [0.0, 1.0] — [UL, UR, ML, MR, LL, LR].
    """
    rows = len(mask)
    cols = len(mask[0]) if mask else 0

    def m(row: int, col: int) -> float:
        return mask[max(0, min(rows - 1, row))][max(0, min(cols - 1, col))]

    return [
        (m(r-1, c-1) + m(r-1, c) + m(r, c-1) + m(r, c)) / 4.0,          # UL
        (m(r-1, c) + m(r-1, c+1) + m(r, c) + m(r, c+1)) / 4.0,          # UR
        (m(r, c-1) + m(r, c)) / 2.0,                                       # ML
        (m(r, c) + m(r, c+1)) / 2.0,                                       # MR
        (m(r, c-1) + m(r, c) + m(r+1, c-1) + m(r+1, c)) / 4.0,          # LL
        (m(r, c) + m(r, c+1) + m(r+1, c) + m(r+1, c+1)) / 4.0,          # LR
    ]


# -------------------------------------------------------------------------
def _nearest_char(vec: list, db: dict) -> str:
    """Find the character whose shape vector is nearest to vec.

    Uses squared Euclidean distance (no sqrt needed for argmin).

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
def shape_fill(mask: list, charset: Optional[str] = None) -> list:
    """Fill using 6D shape-vector character matching (F07).

    For each cell, samples ink density in 6 directional zones using
    neighborhood averages, then selects the character whose rendered shape
    most closely matches. Interior cells yield solid/dense characters;
    edge cells yield directional characters that follow contours;
    exterior cells yield space.

    Pillow-gated: raises ImportError if Pillow is not installed.
    First call precomputes and caches the character shape DB (~95 chars).

    :param mask: 2D list of floats from glyph_to_mask() — values 0.0–1.0.
    :param charset: Character vocabulary (default: all 95 printable ASCII).
    :returns: List of strings — one per row, same shape as input mask.
    :raises ImportError: If Pillow is not installed.
    """
    _require_pil()
    db = _get_char_db(charset if charset is not None else SHAPE_CHARS)

    result = []
    for r, row in enumerate(mask):
        line = ""
        for c in range(len(row)):
            vec = _sample_cell(mask, r, c)
            line += _nearest_char(vec, db)
        result.append(line)
    return result
