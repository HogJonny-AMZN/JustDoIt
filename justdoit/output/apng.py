"""
Package: justdoit.output.apng
APNG (Animated PNG) output target for animation frame sequences.

Converts a list of ANSI frame strings to a PIL Image sequence and saves
as an APNG file. Pillow is required — all public functions call
_require_pil() before any PIL import.

Requires Pillow: pip install Pillow
"""

import io
import logging as _logging
from pathlib import Path
from typing import Optional

from justdoit.output.ansi_parser import parse, effective_color

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.output.apng"
__updated__ = "2026-03-30 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_PIL_MISSING_MSG = (
    "Pillow is required for APNG output.\n"
    "Install it with:  pip install Pillow\n"
    "Then re-run your command."
)

_CHAR_W_RATIO = 0.6  # char_width ≈ font_size * 0.6


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
def _hex_to_rgb(color: str) -> tuple:
    """Convert a hex color string to an (r, g, b) tuple.

    :param color: Color string like '#111111' or '111111'.
    :returns: (r, g, b) tuple with values 0-255.
    """
    color = color.lstrip("#")
    return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))


# -------------------------------------------------------------------------
def frame_to_image(
    frame: str,
    font_size: int = 14,
    bg_color: str = "#111111",
    line_height: float = 1.2,
    font_path: Optional[str] = None,
):
    """Convert a single ANSI frame string to a PIL Image.

    Each visible character is drawn at its grid position using its ANSI color.
    The image uses the specified background color.

    :param frame: Multi-line rendered string (with or without ANSI).
    :param font_size: Font size in pixels (default: 14).
    :param bg_color: Background color as hex string (default: '#111111').
    :param line_height: Line spacing multiplier of font_size (default: 1.2).
    :param font_path: Optional path to a .ttf monospace font.
    :returns: PIL.Image.Image object.
    :raises ImportError: If Pillow is not installed.
    """
    _require_pil()

    from PIL import Image, ImageDraw, ImageFont

    tokens = parse(frame)

    rows: list = [[]]
    for ch, color in tokens:
        if ch == "\n":
            rows.append([])
        else:
            rows[-1].append((ch, color))

    pil_font = _load_font(font_path, font_size)

    # Measure character cell
    try:
        bbox = pil_font.getbbox("█")
        char_w = bbox[2] - bbox[0]
        char_h = bbox[3] - bbox[1]
    except AttributeError:
        char_w = font_size
        char_h = font_size

    char_w = max(char_w, font_size // 2)
    char_h = max(char_h, font_size)
    line_h = int(char_h * line_height)

    max_cols = max((len(row) for row in rows), default=1)
    n_rows = len(rows)

    padding = 6
    img_w = max_cols * char_w + padding * 2
    img_h = n_rows * line_h + padding * 2

    bg_rgb = _hex_to_rgb(bg_color)
    img = Image.new("RGB", (img_w, img_h), color=bg_rgb)
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
def to_apng(
    frames: list[str],
    fps: float = 24.0,
    bg_color: str = "#111111",
    loop: int = 0,
    font_size: int = 14,
) -> bytes:
    """Convert a list of ANSI frame strings to APNG bytes.

    :param frames: List of ANSI frame strings (one string per frame).
    :param fps: Playback speed in frames per second.
    :param bg_color: Background color as hex string (default: '#111111').
    :param loop: Number of times to loop (0 = infinite, 1 = play once).
    :param font_size: Font size in pixels (default: 14).
    :returns: APNG file contents as bytes.
    :raises ImportError: If Pillow is not installed.
    :raises ValueError: If frames is empty.
    """
    _require_pil()

    if not frames:
        raise ValueError("frames must not be empty")

    duration_ms = int(1000 / fps)

    images = [frame_to_image(f, font_size=font_size, bg_color=bg_color) for f in frames]

    # Normalize all frames to the same size (use the first frame's dimensions)
    target_w = max(img.width for img in images)
    target_h = max(img.height for img in images)

    bg_rgb = _hex_to_rgb(bg_color)
    from PIL import Image as PILImage
    normalized = []
    for img in images:
        if img.size == (target_w, target_h):
            normalized.append(img)
        else:
            canvas = PILImage.new("RGB", (target_w, target_h), color=bg_rgb)
            canvas.paste(img, (0, 0))
            normalized.append(canvas)

    buf = io.BytesIO()
    normalized[0].save(
        buf,
        format="PNG",
        save_all=True,
        append_images=normalized[1:],
        loop=loop,
        duration=duration_ms,
    )
    return buf.getvalue()


# -------------------------------------------------------------------------
def save_apng(
    frames: list[str],
    path: str | Path,
    fps: float = 24.0,
    bg_color: str = "#111111",
    loop: int = 0,
    font_size: int = 14,
) -> None:
    """Save an animation frame list as an APNG file.

    :param frames: List of ANSI frame strings (one string per frame).
    :param path: Output file path (e.g. 'output.apng').
    :param fps: Playback speed in frames per second.
    :param bg_color: Background color as hex string (default: '#111111').
    :param loop: Number of times to loop (0 = infinite, 1 = play once).
    :param font_size: Font size in pixels (default: 14).
    :raises ImportError: If Pillow is not installed.
    """
    data = to_apng(frames, fps=fps, bg_color=bg_color, loop=loop, font_size=font_size)
    Path(path).write_bytes(data)
    _LOGGER.info(f"Saved APNG to {path} ({len(frames)} frames @ {fps}fps)")


# -------------------------------------------------------------------------
def _load_font(font_path: Optional[str], font_size: int):
    """Load a PIL font, falling back gracefully if the path is invalid.

    :param font_path: Path to a .ttf font file, or None for default.
    :param font_size: Point size for TrueType fonts.
    :returns: PIL ImageFont instance.
    """
    import os
    from PIL import ImageFont

    if font_path:
        try:
            return ImageFont.truetype(font_path, font_size)
        except (OSError, IOError) as exc:
            _LOGGER.warning(f"Could not load font '{font_path}': {exc}. Falling back to default.")

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

    _LOGGER.warning("No TrueType font found — using PIL default bitmap font.")
    return ImageFont.load_default()
