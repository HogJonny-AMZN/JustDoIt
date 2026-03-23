"""
Package: justdoit.output.image
PNG/image output target for rendered ASCII art (O03).

Rasterizes each character to a PIL Image using a monospace font,
then saves as PNG. Pillow is an optional dependency — all public
functions call _require_pil() before any PIL import.

Requires Pillow: pip install Pillow
"""

import logging as _logging
import os
from typing import Optional

from justdoit.output.ansi_parser import parse, effective_color

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.output.image"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_PIL_MISSING_MSG = (
    "Pillow is required for PNG image output.\n"
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
def to_image(
    text: str,
    font_size: int = 16,
    bg_color: tuple = (17, 17, 17),
    padding: int = 10,
    font_path: Optional[str] = None,
):
    """Rasterize a rendered ANSI string to a PIL Image.

    Each visible character is drawn at its grid position in its ANSI color.
    The image uses a dark background by default.

    :param text: Multi-line rendered string from render() (with or without ANSI).
    :param font_size: Font size in pixels (default: 16).
    :param bg_color: Background (r, g, b) color tuple (default: dark grey).
    :param padding: Pixel padding around the image edges (default: 10).
    :param font_path: Optional path to a .ttf monospace font.
                      Falls back to PIL's default bitmap font if not provided.
    :returns: PIL.Image.Image object.
    :raises ImportError: If Pillow is not installed.
    """
    _require_pil()

    from PIL import Image, ImageDraw, ImageFont

    tokens = parse(text)

    # Build row data
    rows: list = [[]]
    for ch, color in tokens:
        if ch == "\n":
            rows.append([])
        else:
            rows[-1].append((ch, color))

    # Load font
    pil_font = _load_font(font_path, font_size)

    # Measure character cell size using a sample character
    try:
        bbox = pil_font.getbbox("█")
        char_w = bbox[2] - bbox[0]
        char_h = bbox[3] - bbox[1]
    except AttributeError:
        # Fallback for older Pillow without getbbox on font
        char_w = font_size
        char_h = font_size

    # Ensure minimum cell size
    char_w = max(char_w, font_size // 2)
    char_h = max(char_h, font_size)
    line_h = int(char_h * 1.2)

    max_cols = max((len(row) for row in rows), default=1)
    n_rows = len(rows)

    img_w = max_cols * char_w + padding * 2
    img_h = n_rows * line_h + padding * 2

    img = Image.new("RGB", (img_w, img_h), color=bg_color)
    draw = ImageDraw.Draw(img)

    for row_idx, row in enumerate(rows):
        y = padding + row_idx * line_h
        for col_idx, (ch, color) in enumerate(row):
            if ch == " ":
                continue
            x = padding + col_idx * char_w
            r, g, b = effective_color(color)
            draw.text((x, y), ch, font=pil_font, fill=(r, g, b))

    return img


# -------------------------------------------------------------------------
def save_png(text: str, path: str, **kwargs) -> None:
    """Rasterize rendered ASCII art and save as a PNG file.

    :param text: Multi-line rendered string from render().
    :param path: Output file path (e.g. 'output.png').
    :param kwargs: Additional keyword arguments passed to to_image().
    :raises ImportError: If Pillow is not installed.
    """
    img = to_image(text, **kwargs)
    img.save(path, format="PNG")
    _LOGGER.info(f"Saved PNG to {path} ({img.width}×{img.height}px)")


# -------------------------------------------------------------------------
def _load_font(font_path: Optional[str], font_size: int):
    """Load a PIL font, falling back gracefully if the path is invalid.

    :param font_path: Path to a .ttf font file, or None for default.
    :param font_size: Point size for TrueType fonts.
    :returns: PIL ImageFont instance.
    """
    from PIL import ImageFont

    if font_path:
        try:
            return ImageFont.truetype(font_path, font_size)
        except (OSError, IOError) as exc:
            _LOGGER.warning(f"Could not load font '{font_path}': {exc}. Falling back to default.")

    # Try to find a monospace system font
    _candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
        "/System/Library/Fonts/Courier.ttc",
        "/mnt/c/Windows/Fonts/cour.ttf",
    ]
    for candidate in _candidates:
        if os.path.exists(candidate):
            try:
                return ImageFont.truetype(candidate, font_size)
            except (OSError, IOError):
                continue

    # Last resort: PIL default bitmap font (no size control)
    _LOGGER.warning("No TrueType font found — using PIL default bitmap font.")
    return ImageFont.load_default()
