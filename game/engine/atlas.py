"""
Package: game.engine.atlas
Loads a pre-built font texture atlas PNG and exposes per-glyph UV regions.

Build-time counterpart: justdoit/output/arcade_atlas.py
Runtime use: instantiate once, pass to TileRenderer and AsciiParticleSystem.
"""

import logging as _logging
from pathlib import Path
from typing  import NamedTuple

import arcade

# -------------------------------------------------------------------------
_MODULE_NAME = "game.engine.atlas"
__updated__  = "2026-04-30"
__version__  = "0.1.0"
__author__   = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
class GlyphRegion(NamedTuple):
    """UV coordinates (in pixels) for one glyph inside the atlas texture."""
    x:      int
    y:      int
    width:  int
    height: int


# -------------------------------------------------------------------------
class AsciiAtlas:
    """
    Manages a packed font texture atlas for Arcade-based ASCII rendering.

    :param atlas_path: Path to the PNG atlas image.
    :param uv_path:    Path to the companion JSON glyph-UV map.
    """

    def __init__(self, atlas_path: Path, uv_path: Path) -> None:
        self._atlas_path = atlas_path
        self._uv_path    = uv_path
        self._texture: arcade.Texture | None = None
        self._glyphs:  dict[str, GlyphRegion] = {}

    # -------------------------------------------------------------------------
    def load(self) -> None:
        """Load atlas texture and UV map from disk."""
        raise NotImplementedError

    # -------------------------------------------------------------------------
    def glyph(self, char: str) -> GlyphRegion:
        """
        Return the UV region for *char*.

        :param char: Single ASCII character.
        :returns:    GlyphRegion pixel coordinates inside the atlas.
        :raises KeyError: If *char* is not present in the atlas.
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    @property
    def texture(self) -> arcade.Texture:
        """The loaded Arcade texture object."""
        if self._texture is None:
            raise RuntimeError("AsciiAtlas.load() must be called before accessing texture")
        return self._texture
