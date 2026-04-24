"""
Package: justdoit.core.image_pipeline
High-level entry points for image-to-ASCII rendering.

Provides render_text_as_image() for rendering text via a TTF font at full
resolution and then converting to an ASCII grid via 6-zone shape matching,
and render_pil_image_as_ascii() for converting any PIL image.

Also provides grid_to_ansi() and grid_to_svg() for converting the
(char, rgb) grid into displayable/exportable formats.

Requires Pillow.
"""

import logging as _logging
from typing import Optional

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.core.image_pipeline"
__updated__ = "2026-04-24 12:00:00"
__version__ = "1.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_CHAR_W_RATIO = 0.6


# -------------------------------------------------------------------------
def render_text_to_pil(
    text: str,
    font_path: str,
    canvas_w: int,
    canvas_h: int,
    fg_color: tuple = (255, 255, 255),
    bg_color: tuple = (0, 0, 0),
    font_scale: float = 1.0,
) -> "PIL.Image.Image":
    """Render text to a PIL image at canvas resolution without ASCII sampling.

    Produces a white-on-black (or custom fg/bg) PIL image suitable for
    geometric transforms before passing to ``image_to_ascii()``.

    :param text: Text to render.
    :param font_path: Path to a TTF/OTF font file.
    :param canvas_w: Canvas width in pixels.
    :param canvas_h: Canvas height in pixels.
    :param fg_color: Foreground (text) color as (r, g, b) tuple.
    :param bg_color: Background color as (r, g, b) tuple.
    :param font_scale: Scale factor for auto-sized font (default: 1.0).
    :returns: PIL.Image.Image (RGB) at *canvas_w* x *canvas_h*.
    :raises ImportError: If Pillow is not installed.
    """
    from PIL import Image, ImageDraw, ImageFont

    best_pt = 10
    for pt in range(10, 500):
        try:
            font = ImageFont.truetype(font_path, pt)
        except (IOError, OSError):
            break
        bbox = font.getbbox(text)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        if tw > canvas_w * 0.95 or th > canvas_h * 0.95:
            break
        best_pt = pt

    best_pt = max(10, int(best_pt * font_scale))

    try:
        font = ImageFont.truetype(font_path, best_pt)
    except (IOError, OSError):
        font = ImageFont.load_default()

    img = Image.new("RGB", (canvas_w, canvas_h), bg_color)
    draw = ImageDraw.Draw(img)

    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (canvas_w - tw) // 2 - bbox[0]
    y = (canvas_h - th) // 2 - bbox[1]
    draw.text((x, y), text, fill=fg_color, font=font)

    return img


# -------------------------------------------------------------------------
def render_text_as_image(
    text: str,
    font_path: str,
    output_cols: int,
    output_rows: int,
    cell_w: int = 8,
    cell_h: int = 16,
    charset: str = "",
    color: bool = True,
    bg_color: tuple = (0, 0, 0),
    fg_color: tuple = (255, 255, 255),
    font_scale: float = 1.0,
) -> list:
    """Render text to a PIL image using a TTF font, then convert to ASCII grid.

    Steps:
      1. Compute PIL image size: output_cols * cell_w x output_rows * cell_h
      2. Find largest font_pt that fits text in that canvas
      3. Render text centered on canvas (PIL ImageDraw.text)
      4. Pass to image_to_ascii()
      5. Return (char, rgb) grid

    :param text: Text to render.
    :param font_path: Path to a TTF/OTF font file.
    :param output_cols: Number of ASCII columns in the output grid.
    :param output_rows: Number of ASCII rows in the output grid.
    :param cell_w: Cell width in pixels (default: 8).
    :param cell_h: Cell height in pixels (default: 16).
    :param charset: Characters to consider for matching.
    :param color: If True, return RGB per cell; if False, None.
    :param bg_color: Background color as (r, g, b) tuple.
    :param fg_color: Foreground (text) color as (r, g, b) tuple.
    :param font_scale: Scale factor for auto-sized font (default: 1.0).
    :returns: list[rows] of list[cols] of (char, (r,g,b) | None).
    :raises ImportError: If Pillow is not installed.
    """
    from PIL import Image, ImageDraw, ImageFont

    from justdoit.core.image_sampler import image_to_ascii

    canvas_w = output_cols * cell_w
    canvas_h = output_rows * cell_h

    # Find the largest font size that fits text in the canvas
    best_pt = 10
    for pt in range(10, 500):
        try:
            font = ImageFont.truetype(font_path, pt)
        except (IOError, OSError):
            break
        bbox = font.getbbox(text)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        if tw > canvas_w * 0.95 or th > canvas_h * 0.95:
            break
        best_pt = pt

    best_pt = max(10, int(best_pt * font_scale))

    try:
        font = ImageFont.truetype(font_path, best_pt)
    except (IOError, OSError):
        font = ImageFont.load_default()

    # Create canvas and render text centered
    img = Image.new("RGB", (canvas_w, canvas_h), bg_color)
    draw = ImageDraw.Draw(img)

    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (canvas_w - tw) // 2 - bbox[0]
    y = (canvas_h - th) // 2 - bbox[1]
    draw.text((x, y), text, fill=fg_color, font=font)

    return image_to_ascii(img, cell_w, cell_h, charset=charset, color=color)


# -------------------------------------------------------------------------
def render_pil_image_as_ascii(
    image: "PIL.Image.Image",
    cell_w: int = 8,
    cell_h: int = 16,
    charset: str = "",
    color: bool = True,
) -> list:
    """Convert any PIL image to ASCII grid. Thin wrapper over image_to_ascii().

    Entry point for AI image -> ASCII and photo -> ASCII use cases.

    :param image: PIL.Image in any mode.
    :param cell_w: Cell width in pixels (default: 8).
    :param cell_h: Cell height in pixels (default: 16).
    :param charset: Characters to consider for matching.
    :param color: If True, return RGB per cell; if False, None.
    :returns: list[rows] of list[cols] of (char, (r,g,b) | None).
    :raises ImportError: If Pillow is not installed.
    """
    from justdoit.core.image_sampler import image_to_ascii
    return image_to_ascii(image, cell_w, cell_h, charset=charset, color=color)


# -------------------------------------------------------------------------
def grid_to_ansi(grid: list) -> str:
    """Convert (char, rgb) grid to ANSI true-color string.

    :param grid: list[rows] of list[cols] of (char, (r,g,b) | None).
    :returns: Multi-line string with ANSI 24-bit color codes.
    """
    lines = []
    for row in grid:
        parts = []
        for ch, rgb in row:
            if rgb is not None:
                r, g, b = rgb
                parts.append(f"\033[38;2;{r};{g};{b}m{ch}\033[0m")
            else:
                parts.append(ch)
        lines.append("".join(parts))
    return "\n".join(lines)


# -------------------------------------------------------------------------
def grid_to_svg(
    grid: list,
    cell_w: float = 0.0,
    cell_h: float = 0.0,
    font_size: int = 14,
    font_family: str = "Courier New, Courier, monospace",
    bg_color: str = "#111111",
    canvas_width: int = 0,
    canvas_height: int = 0,
) -> str:
    """Convert (char, rgb) grid to SVG string.

    :param grid: list[rows] of list[cols] of (char, (r,g,b) | None).
    :param cell_w: Character cell width in SVG pixels (auto-derived if 0).
    :param cell_h: Character cell height / line height in SVG pixels (auto-derived if 0).
    :param font_size: Font size in SVG pixels (default: 14).
    :param font_family: CSS font-family string.
    :param bg_color: Background fill color.
    :param canvas_width: Fixed SVG width (0 = auto).
    :param canvas_height: Fixed SVG height (0 = auto).
    :returns: SVG document string.
    """
    if not grid:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="0" height="0"></svg>\n'

    n_rows = len(grid)
    n_cols = max(len(row) for row in grid)

    if canvas_width > 0 and canvas_height > 0:
        width = canvas_width
        height = canvas_height
        cw = width / n_cols if n_cols > 0 else font_size * _CHAR_W_RATIO
        ch = height / n_rows if n_rows > 0 else font_size * 1.2
        font_size = max(1, round(cw / _CHAR_W_RATIO))
    else:
        cw = cell_w if cell_w > 0 else font_size * _CHAR_W_RATIO
        ch = cell_h if cell_h > 0 else font_size * 1.2
        width = int(n_cols * cw) + font_size
        height = int(n_rows * ch) + font_size

    elements = [f'<rect width="{width}" height="{height}" fill="{_svg_escape(bg_color)}"/>']

    default_color = (255, 255, 255)

    for row_idx, row in enumerate(grid):
        y = int((row_idx + 1) * ch)
        for col_idx, (char, rgb) in enumerate(row):
            if char == " ":
                continue
            x = int(col_idx * cw)
            r, g, b = rgb if rgb is not None else default_color
            fill = f"#{r:02x}{g:02x}{b:02x}"
            safe_ch = _svg_escape(char)
            elements.append(
                f'<text x="{x}" y="{y}" fill="{fill}" '
                f'font-size="{font_size}" '
                f'font-family="{font_family}">'
                f'{safe_ch}</text>'
            )

    body = "\n  ".join(elements)
    return (
        f'<?xml version="1.0" encoding="utf-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}">\n'
        f'  {body}\n'
        f'</svg>\n'
    )


# -------------------------------------------------------------------------
def _svg_escape(s: str) -> str:
    """Escape XML special characters for use in SVG.

    :param s: Input string.
    :returns: Escaped string.
    """
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
         .replace("'", "&apos;")
    )
