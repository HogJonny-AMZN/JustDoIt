"""
Package: justdoit.output.arcade_atlas
Generates a packed font texture atlas PNG + glyph UV map JSON from a JustDoIt font.

The atlas is a grid of rendered glyph cells.  The companion JSON maps each
character to its pixel-space bounding box inside the atlas.

Consumed at build time by game/build/build_atlas.py.
Loaded at game runtime by game/engine/atlas.py (AsciiAtlas).
"""

import json
import logging as _logging
from pathlib import Path

# -------------------------------------------------------------------------
_MODULE_NAME = "justdoit.output.arcade_atlas"
__updated__  = "2026-04-30"
__version__  = "0.1.0"
__author__   = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

# Default printable ASCII range baked into every atlas
_DEFAULT_CHARS = [chr(c) for c in range(32, 127)]


# -------------------------------------------------------------------------
def build_atlas(
    font_name:   str,
    cell_width:  int,
    cell_height: int,
    out_png:     Path,
    out_json:    Path,
    chars:       list[str] | None = None,
) -> None:
    """
    Render each glyph in *chars* to a PIL canvas and save as a packed atlas.

    :param font_name:   JustDoIt font identifier (e.g. ``"block"``, ``"slim"``).
    :param cell_width:  Pixel width of each glyph cell in the atlas.
    :param cell_height: Pixel height of each glyph cell in the atlas.
    :param out_png:     Destination path for the atlas PNG.
    :param out_json:    Destination path for the glyph UV map JSON.
    :param chars:       Characters to include; defaults to printable ASCII (32–126).
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise ImportError("Pillow is required for build_atlas — run: uv add Pillow") from exc

    raise NotImplementedError
