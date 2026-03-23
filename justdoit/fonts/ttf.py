"""
TTF/OTF font rasterizer — technique G02.

Renders any system font at low resolution via Pillow and converts to ASCII glyphs.
Pillow is an optional dependency; this module degrades gracefully if PIL is missing.
"""

import os
import string

from justdoit.fonts import FONTS

# Light-to-dark density chars (0=dark pixel → dense char, 255=light → space)
DENSITY_CHARS = ' .,:;+*?%S#@'

_PIL_MISSING_MSG = (
    "Pillow is required for TTF font support.\n"
    "Install it with:  pip install Pillow\n"
    "Then re-run your command."
)


def _require_pil():
    """Raise ImportError with a helpful message if PIL is not installed."""
    try:
        import PIL  # noqa: F401
    except ImportError:
        raise ImportError(_PIL_MISSING_MSG)


def rasterize_ttf(
    font_path: str,
    font_size: int = 12,
    chars: str = None,
    density_chars: str = None,
    threshold: float = 0.3,
) -> dict:
    """
    Rasterize a TTF/OTF font file to an ASCII glyph dict compatible with FONTS.

    Parameters
    ----------
    font_path     : path to a .ttf or .otf file
    font_size     : point size used for rendering (controls detail level)
    chars         : characters to rasterize (default: printable ASCII 32-126)
    density_chars : light-to-dark char sequence (default: DENSITY_CHARS)
    threshold     : fraction of max brightness below which a pixel is considered 'ink'

    Returns
    -------
    dict mapping char → list[str]  (one string per row, all same width)
    """
    _require_pil()

    from PIL import Image, ImageDraw, ImageFont

    if chars is None:
        chars = ''.join(chr(c) for c in range(32, 127))
    if density_chars is None:
        density_chars = DENSITY_CHARS

    target_height = font_size
    img_w = font_size * 2
    img_h = int(font_size * 2.5)

    try:
        pil_font = ImageFont.truetype(font_path, font_size)
    except (OSError, IOError) as exc:
        raise ValueError(f"Cannot load font '{font_path}': {exc}") from exc

    raw_glyphs = {}
    for ch in chars:
        img = Image.new('L', (img_w, img_h), color=255)
        draw = ImageDraw.Draw(img)
        draw.text((0, 0), ch, font=pil_font, fill=0)

        # Crop to bounding box of ink pixels
        bbox = img.getbbox()
        if bbox is None:
            # Fully empty (whitespace / missing glyph) — skip for now
            raw_glyphs[ch] = None
            continue

        cropped = img.crop(bbox)

        # Resize to exactly target_height rows (keep aspect ratio for width)
        orig_w, orig_h = cropped.size
        scale = target_height / orig_h
        new_w = max(1, round(orig_w * scale))
        resized = cropped.resize((new_w, target_height), Image.LANCZOS)

        # Map pixel brightness → density char
        pixels = list(resized.getdata())
        rows = []
        for row_idx in range(target_height):
            row_pixels = pixels[row_idx * new_w:(row_idx + 1) * new_w]
            row_str = ''
            for px in row_pixels:
                # px: 0=black(ink), 255=white(empty)
                # map to index in density_chars: 0 → last char (dense), 255 → first (space)
                idx = int((1.0 - px / 255.0) * (len(density_chars) - 1))
                idx = max(0, min(len(density_chars) - 1, idx))
                row_str += density_chars[idx]
            rows.append(row_str)

        raw_glyphs[ch] = rows

    # Normalize all glyph widths to the same value (pad with spaces)
    max_w = 0
    for rows in raw_glyphs.values():
        if rows is not None:
            for row in rows:
                max_w = max(max_w, len(row))

    if max_w == 0:
        max_w = 1

    # Build space glyph (blank column, same height)
    space_rows = [' ' * max_w] * target_height

    result = {}
    for ch, rows in raw_glyphs.items():
        if rows is None:
            result[ch] = space_rows
        else:
            result[ch] = [row.ljust(max_w) for row in rows]

    # Ensure space is present
    if ' ' not in result:
        result[' '] = space_rows

    return result


def find_system_fonts() -> list:
    """
    Return a sorted list of TTF/OTF font paths found on the system.

    Checks common locations on Linux, macOS, and Windows (via WSL).
    """
    search_dirs = [
        '/usr/share/fonts',
        '/usr/local/share/fonts',
        os.path.expanduser('~/.fonts'),
        '/System/Library/Fonts',          # macOS
        '/Library/Fonts',                 # macOS
        'C:/Windows/Fonts',               # Windows native
        '/mnt/c/Windows/Fonts',           # WSL
    ]

    found = []
    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        for root, _dirs, files in os.walk(d):
            for fname in files:
                if fname.lower().endswith(('.ttf', '.otf')):
                    found.append(os.path.join(root, fname))

    return sorted(found)


def load_ttf_font(font_path: str, name: str = None, font_size: int = 12) -> str:
    """
    Rasterize a TTF/OTF font and register it in the global FONTS dict.

    Parameters
    ----------
    font_path : path to the font file
    name      : registry key (default: stem of font_path, e.g. 'arial')
    font_size : rasterization size

    Returns
    -------
    The registered font name.
    """
    if name is None:
        stem = os.path.basename(font_path)
        if '.' in stem:
            stem = stem.rsplit('.', 1)[0]
        name = stem.lower()

    glyph_dict = rasterize_ttf(font_path, font_size=font_size)
    FONTS[name] = glyph_dict
    return name
