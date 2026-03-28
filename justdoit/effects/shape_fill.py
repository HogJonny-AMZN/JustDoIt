"""
Package: justdoit.effects.shape_fill
Shape-vector / gradient-edge fill (F07).

Uses the SDF of the glyph mask to identify three regions:
  - Exterior  (SDF < 0.20): space
  - Edge band (SDF 0.20-0.60): directional character chosen by SDF gradient angle
  - Interior  (SDF > 0.60): density character scaled by SDF depth

The gradient of the SDF at each edge cell encodes the local contour direction.
That angle is mapped to a directional ASCII character (| / \\ -) so strokes
follow the actual shape of the glyph rather than a uniform density fill.

Pure Python at render time — no external dependencies.
The Pillow-based character DB (_get_char_db) is retained for tests and for
future use in photo-to-ASCII rendering where sub-cell resolution is available.
"""

import logging as _logging
import math
import string
from typing import Optional

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.effects.shape_fill"
__updated__ = "2026-03-28 00:00:00"
__version__ = "0.2.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

# Default character vocabulary for the Pillow-based DB (tests / future use)
SHAPE_CHARS: str = string.printable[:95]

# Cell dimensions used when rendering chars for the Pillow-based DB
_CELL_H: int = 16
_CELL_W: int = 8

# Module-level DB cache: (charset, cell_h, cell_w) → {char: [6 floats]}
_DB_CACHE: dict = {}

# Interior density ramp — densest to lightest
_INTERIOR_CHARS: str = "@#S%*+;:,. "

# Edge-band characters indexed by contour angle (degrees, 0–180)
# Angle is measured from the SDF gradient; 0°=horizontal, 90°=vertical
_EDGE_ANGLE_MAP: list = [
    (0,   22,  "-"),    # horizontal stroke
    (22,  68,  "/"),    # rising diagonal
    (68,  112, "|"),    # vertical stroke
    (112, 158, "\\"),   # falling diagonal
    (158, 180, "-"),    # horizontal stroke (other side)
]

# SDF thresholds
_EXTERIOR_MAX: float  = 0.20
_INTERIOR_MIN: float  = 0.60


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
def _sdf_val(sdf: list, r: int, c: int, rows: int, cols: int) -> float:
    """Clamp-safe SDF lookup.

    :param sdf: 2D SDF grid.
    :param r: Row index (may be out of bounds).
    :param c: Column index (may be out of bounds).
    :param rows: Grid row count.
    :param cols: Grid column count.
    :returns: SDF float value, clamped to grid boundary.
    """
    return sdf[max(0, min(rows - 1, r))][max(0, min(cols - 1, c))]


# -------------------------------------------------------------------------
def _edge_char(sdf: list, r: int, c: int, rows: int, cols: int) -> str:
    """Choose a directional character for an edge cell using the SDF gradient.

    Computes the gradient of the SDF at (r, c) via central differences.
    The gradient angle (0°=horizontal, 90°=vertical) is mapped to a
    directional ASCII character that follows the local contour direction.

    :param sdf: 2D SDF grid.
    :param r: Row index.
    :param c: Column index.
    :param rows: Grid row count.
    :param cols: Grid column count.
    :returns: Single directional character.
    """
    dx = _sdf_val(sdf, r, c + 1, rows, cols) - _sdf_val(sdf, r, c - 1, rows, cols)
    dy = _sdf_val(sdf, r + 1, c, rows, cols) - _sdf_val(sdf, r - 1, c, rows, cols)
    mag = math.sqrt(dx * dx + dy * dy)

    if mag < 0.05:
        return "+"  # no clear gradient — ambiguous corner/junction

    angle = math.degrees(math.atan2(abs(dy), abs(dx)))  # 0°–90°
    # Mirror into 0°–180° using sign of dy*dx to distinguish / vs \
    if dx * dy < 0:
        angle = 180.0 - angle

    for a0, a1, ch in _EDGE_ANGLE_MAP:
        if a0 <= angle < a1:
            return ch
    return "-"


# -------------------------------------------------------------------------
def shape_fill(mask: list, charset: Optional[str] = None) -> list:
    """Fill using SDF gradient edge-character selection (F07).

    Three-region fill based on the signed distance field of the mask:

      - Exterior  (SDF < 0.20): space
      - Edge band (SDF 0.20–0.60): directional char from contour angle
          | for vertical strokes, - for horizontal, / and \\ for diagonals
      - Interior  (SDF > 0.60): density char scaled by depth (@→.)

    Pure Python — no external dependencies at render time.

    :param mask: 2D list of floats from glyph_to_mask() — values 0.0–1.0.
    :param charset: Unused in default mode; reserved for future photo-to-ASCII
        rendering where a Pillow-based character DB will be used.
    :returns: List of strings — one per row, same shape as input mask.
    """
    from justdoit.core.glyph import mask_to_sdf

    rows = len(mask)
    cols = len(mask[0]) if mask else 0

    # No ink — return all spaces immediately (mask_to_sdf returns 0.5 uniformly
    # for a blank mask, which would produce edge-band chars instead of spaces)
    if not any(mask[r][c] > 0.5 for r in range(rows) for c in range(cols)):
        return [" " * cols for _ in range(rows)]

    sdf = mask_to_sdf(mask)
    n_interior = len(_INTERIOR_CHARS)

    result = []
    for r in range(rows):
        line = ""
        for c in range(cols):
            sv = _sdf_val(sdf, r, c, rows, cols)

            if sv < _EXTERIOR_MAX:
                line += " "
            elif sv > _INTERIOR_MIN:
                # Interior: map SDF depth to density char (deep → dense)
                t = (sv - _INTERIOR_MIN) / (1.0 - _INTERIOR_MIN)
                idx = int((1.0 - t) * (n_interior - 1))
                line += _INTERIOR_CHARS[max(0, min(n_interior - 1, idx))]
            else:
                line += _edge_char(sdf, r, c, rows, cols)

        result.append(line)
    return result
