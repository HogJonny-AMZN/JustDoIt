"""
Package: game.engine.tile_renderer
Renders a justdoit TileGrid to an Arcade render target using sprite batching.

Each TileCell (char + fg + bg) becomes two quads: background color fill and
foreground glyph sprite tinted to fg color. Batched via arcade.SpriteList for
a single GPU draw call per layer.
"""

import logging as _logging

import arcade

from game.engine.atlas       import AsciiAtlas
from justdoit.core.tile_grid import TileGrid

# -------------------------------------------------------------------------
_MODULE_NAME = "game.engine.tile_renderer"
__updated__  = "2026-04-30"
__version__  = "0.1.0"
__author__   = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
class TileRenderer:
    """
    Converts a TileGrid into an efficiently drawn Arcade sprite batch.

    :param atlas:       AsciiAtlas providing glyph UV regions.
    :param cell_width:  Pixel width of each tile cell on screen.
    :param cell_height: Pixel height of each tile cell on screen.
    """

    def __init__(self, atlas: AsciiAtlas, cell_width: int, cell_height: int) -> None:
        self._atlas       = atlas
        self._cell_width  = cell_width
        self._cell_height = cell_height
        self._bg_list:  arcade.SpriteList | None = None
        self._fg_list:  arcade.SpriteList | None = None

    # -------------------------------------------------------------------------
    def update(self, grid: TileGrid) -> None:
        """
        Rebuild sprite lists from *grid*.  Call when grid content changes.

        :param grid: TileGrid to render.
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    def draw(self) -> None:
        """Draw the current sprite lists.  Must be called inside a draw pass."""
        raise NotImplementedError
