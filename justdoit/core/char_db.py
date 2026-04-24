"""
Package: justdoit.core.char_db
6-zone shape-vector character database for image-to-ASCII conversion.

Renders each character in a charset into a small bitmap and computes a
6-dimensional density vector (2 columns x 3 rows of zones).  The resulting
DB is used by the image sampler to find the best-matching character for
each cell of an input image.

Promoted from justdoit.effects.shape_fill (where it was originally built
for future photo-to-ASCII use).
"""

import logging as _logging
import string
from typing import Optional

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.core.char_db"
__updated__ = "2026-04-24 00:00:00"
__version__ = "1.0.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

# Default character vocabulary — printable ASCII (95 chars)
PRINTABLE_ASCII: str = string.printable[:95]

# Default cell dimensions for rendering chars
DEFAULT_CELL_H: int = 16
DEFAULT_CELL_W: int = 8

# Module-level DB cache: (charset, cell_h, cell_w) -> {char: [6 floats]}
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
            "Character DB requires Pillow. Install with: uv add --dev Pillow"
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
def char_zone_densities(char: str, cell_h: int, cell_w: int) -> list:
    """Render a character and compute its 6-zone ink density vector.

    Zones (2-column x 3-row):  UL UR / ML MR / LL LR

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
def build_char_db(
    charset: str = PRINTABLE_ASCII,
    cell_h: int = DEFAULT_CELL_H,
    cell_w: int = DEFAULT_CELL_W,
) -> dict:
    """Build 6-zone shape vector DB for charset. Cached by (charset, cell_h, cell_w).

    :param charset: Characters to include.
    :param cell_h: Render height in pixels.
    :param cell_w: Render width in pixels.
    :returns: Dict mapping char -> list of 6 floats.
    """
    _require_pil()
    db = {ch: char_zone_densities(ch, cell_h, cell_w) for ch in charset}
    _LOGGER.debug("Built shape DB: %d chars at %d x %dpx", len(db), cell_h, cell_w)
    return db


# -------------------------------------------------------------------------
def get_char_db(
    charset: str = PRINTABLE_ASCII,
    cell_h: int = DEFAULT_CELL_H,
    cell_w: int = DEFAULT_CELL_W,
) -> dict:
    """Return cached DB, building if needed.

    :param charset: Character vocabulary.
    :param cell_h: Render height in pixels.
    :param cell_w: Render width in pixels.
    :returns: Dict mapping char -> list of 6 floats.
    """
    key = (charset, cell_h, cell_w)
    if key not in _DB_CACHE:
        _DB_CACHE[key] = build_char_db(charset, cell_h, cell_w)
    return _DB_CACHE[key]


# -------------------------------------------------------------------------
def nearest_char(vec: list, db: dict) -> str:
    """Find char whose 6D shape vector is nearest to vec (L2 distance).

    :param vec: 6D input vector.
    :param db: Shape DB from get_char_db().
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
