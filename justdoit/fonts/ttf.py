"""
Package: justdoit.fonts.ttf
TTF/OTF font rasterizer — technique G02.

Renders any system font at low resolution via Pillow and converts each character
to an ASCII glyph using density character mapping.

Pillow is an optional dependency; all public functions call _require_pil() before
any PIL import to provide a clear, actionable ImportError if it is absent.
"""

import logging as _logging
import os
from typing import Optional

from justdoit.fonts import FONTS

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.fonts.ttf"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

# Light-to-dark density chars (0 = dark pixel → dense char, 255 = light → space).
DENSITY_CHARS: str = " .,:;+*?%S#@"

_PIL_MISSING_MSG = (
    "Pillow is required for TTF font support.\n"
    "Install it with:  pip install Pillow\n"
    "Then re-run your command."
)


# -------------------------------------------------------------------------
def _require_pil() -> None:
    """Raise ImportError with a helpful install hint if Pillow is not available.

    :raises ImportError: If PIL cannot be imported.
    """
    try:
        import PIL  # noqa: F401
    except ImportError:
        raise ImportError(_PIL_MISSING_MSG)


# -------------------------------------------------------------------------
def rasterize_ttf(
    font_path: str,
    font_size: int = 12,
    chars: Optional[str] = None,
    density_chars: Optional[str] = None,
    threshold: float = 0.3,
) -> dict:
    """Rasterize a TTF/OTF font to an ASCII glyph dict compatible with FONTS.

    Each character is rendered via Pillow at font_size, cropped, scaled to
    font_size rows, then mapped through density_chars by pixel brightness.

    :param font_path: Path to a .ttf or .otf file.
    :param font_size: Point size used for rendering (controls row height and detail).
    :param chars: Characters to rasterize (default: printable ASCII 32–126).
    :param density_chars: Light-to-dark char sequence (default: DENSITY_CHARS).
    :param threshold: Reserved for future use (ink threshold).
    :returns: Dict mapping char to list[str] — one string per row, all same width.
    :raises ValueError: If the font file cannot be loaded.
    :raises ImportError: If Pillow is not installed.
    """
    _require_pil()

    from PIL import Image, ImageDraw, ImageFont

    if chars is None:
        chars = "".join(chr(c) for c in range(32, 127))
    if density_chars is None:
        density_chars = DENSITY_CHARS

    target_height = font_size
    img_w = font_size * 2
    img_h = int(font_size * 2.5)

    try:
        pil_font = ImageFont.truetype(font_path, font_size)
    except (OSError, IOError) as exc:
        raise ValueError(f"Cannot load font '{font_path}': {exc}") from exc

    raw_glyphs: dict = {}
    for ch in chars:
        img = Image.new("L", (img_w, img_h), color=255)
        draw = ImageDraw.Draw(img)
        draw.text((0, 0), ch, font=pil_font, fill=0)

        bbox = img.getbbox()
        if bbox is None:
            raw_glyphs[ch] = None
            continue

        cropped = img.crop(bbox)
        orig_w, orig_h = cropped.size
        scale = target_height / orig_h
        new_w = max(1, round(orig_w * scale))
        resized = cropped.resize((new_w, target_height), Image.LANCZOS)

        # Map pixel brightness → density char index
        if hasattr(resized, "get_flattened_data"):
            pixels = list(resized.get_flattened_data())
        else:
            pixels = list(resized.getdata())

        rows = []
        for row_idx in range(target_height):
            row_pixels = pixels[row_idx * new_w:(row_idx + 1) * new_w]
            row_str = ""
            for px in row_pixels:
                # px: 0 = black (ink), 255 = white (empty)
                # map to density_chars: 0 → last char (dense), 255 → first (space)
                idx = int((1.0 - px / 255.0) * (len(density_chars) - 1))
                idx = max(0, min(len(density_chars) - 1, idx))
                row_str += density_chars[idx]
            rows.append(row_str)

        raw_glyphs[ch] = rows

    # Per-glyph width: each glyph keeps its natural proportional width.
    # Space gets the average ink-glyph width (no bbox → no natural width).
    ink_glyphs = [rows for rows in raw_glyphs.values() if rows is not None]
    if ink_glyphs:
        space_w = max(1, int(
            sum(max(len(r) for r in rows) for rows in ink_glyphs)
            / len(ink_glyphs)
        ))
    else:
        space_w = target_height  # fallback
    space_rows = [" " * space_w] * target_height

    result: dict = {}
    for ch, rows in raw_glyphs.items():
        if rows is None:
            result[ch] = space_rows
        else:
            glyph_w = max(len(row) for row in rows)
            result[ch] = [row.ljust(glyph_w) for row in rows]

    if " " not in result:
        result[" "] = space_rows

    # --- Trim blank leading/trailing columns per glyph ---
    for ch in list(result.keys()):
        rows = result[ch]
        if not rows or ch == " ":
            continue
        glyph_w = max(len(row) for row in rows)
        # find first/last col with ink across all rows
        ink_cols: set[int] = set()
        for row in rows:
            for col_i, c in enumerate(row):
                if c != " ":
                    ink_cols.add(col_i)
        if not ink_cols:
            continue
        left_col = min(ink_cols)
        right_col = max(ink_cols)
        trimmed = [row[left_col:right_col + 1] for row in rows]
        glyph_w_trimmed = right_col - left_col + 1
        result[ch] = [r.ljust(glyph_w_trimmed) for r in trimmed]

    # Recompute space width from post-trim ink glyph widths
    post_trim_ink = [
        max(len(r) for r in rows)
        for ch, rows in result.items()
        if ch != " " and rows
    ]
    if post_trim_ink:
        space_w = max(1, int(sum(post_trim_ink) / len(post_trim_ink)))
    result[" "] = [" " * space_w] * target_height

    # --- Trim uniform blank leading/trailing rows (cross-glyph) ---
    ink_row_indices: set[int] = set()
    for ch, rows in result.items():
        if ch == " ":
            continue
        for i, row in enumerate(rows):
            if any(c != " " for c in row):
                ink_row_indices.add(i)

    if ink_row_indices:
        top = min(ink_row_indices)
        bot = max(ink_row_indices)
        for ch in result:
            result[ch] = result[ch][top : bot + 1]
        new_h = bot - top + 1
        result[" "] = [" " * space_w] * new_h

    return result


# -------------------------------------------------------------------------
def find_system_fonts() -> list:
    """Return a sorted list of TTF/OTF font paths found on the system.

    Checks common font directories on Linux, macOS, and Windows (via WSL).

    :returns: Sorted list of absolute font file paths.
    """
    search_dirs = [
        "/usr/share/fonts",
        "/usr/local/share/fonts",
        os.path.expanduser("~/.fonts"),
        "/System/Library/Fonts",   # macOS
        "/Library/Fonts",          # macOS
        "C:/Windows/Fonts",        # Windows native
        "/mnt/c/Windows/Fonts",    # WSL
    ]

    found = []
    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        for root, _dirs, files in os.walk(d):
            for fname in files:
                if fname.lower().endswith((".ttf", ".otf")):
                    found.append(os.path.join(root, fname))

    return sorted(found)


# -------------------------------------------------------------------------
def load_ttf_font(font_path: str, name: Optional[str] = None, font_size: int = 12) -> str:
    """Rasterize a TTF/OTF font and register it in the global FONTS dict.

    :param font_path: Path to the .ttf or .otf font file.
    :param name: Registry key (default: lowercased filename stem, e.g. 'dejavusans').
    :param font_size: Rasterization point size (controls row height and detail).
    :returns: The registered font name.
    :raises ValueError: If the font file cannot be loaded.
    :raises ImportError: If Pillow is not installed.
    """
    if name is None:
        stem = os.path.basename(font_path)
        if "." in stem:
            stem = stem.rsplit(".", 1)[0]
        name = stem.lower()

    glyph_dict = rasterize_ttf(font_path, font_size=font_size)
    FONTS[name] = glyph_dict
    _LOGGER.debug(f"Loaded TTF font '{name}' from {font_path} at size {font_size}")
    return name
