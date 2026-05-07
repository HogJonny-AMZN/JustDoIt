"""
Package: justdoit.output.sprite_sheet
Generates a sprite sheet PNG from a sequence of JustDoIt-rendered frames.

Each frame is produced by the image pipeline (render_text_as_image) with an
optional effect preset applied.  Frames are packed horizontally into a single
PNG strip suitable for use as an Arcade texture atlas or sprite sheet.

Consumed at build time by game/build/build_sprites.py.
"""

import logging as _logging
from pathlib import Path

# -------------------------------------------------------------------------
_MODULE_NAME = "justdoit.output.sprite_sheet"
__updated__  = "2026-04-30"
__version__  = "0.1.0"
__author__   = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
def build_sprite_sheet(
    text:         str,
    font_name:    str,
    effect_names: list[str],
    out_png:      Path,
    frame_width:  int | None = None,
    frame_height: int | None = None,
) -> None:
    """
    Render *text* once per entry in *effect_names* and pack into a horizontal strip.

    :param text:          Text string to render (typically a single character or short word).
    :param font_name:     JustDoIt font identifier.
    :param effect_names:  List of effect preset names; one frame is rendered per entry.
    :param out_png:       Destination path for the sprite sheet PNG.
    :param frame_width:   Crop each frame to this width (pixels); None = natural width.
    :param frame_height:  Crop each frame to this height (pixels); None = natural height.
    """
    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError("Pillow is required for build_sprite_sheet — run: uv add Pillow") from exc

    raise NotImplementedError
