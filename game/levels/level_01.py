"""
Package: game.levels.level_01
First level — tutorial area, introduces movement and basic enemies.

Level data is a 2D list of TileCell specs.  Entity spawn points are
declared as a list of (variant, x, y) tuples.
"""

import logging as _logging

# -------------------------------------------------------------------------
_MODULE_NAME = "game.levels.level_01"
__updated__  = "2026-04-30"
__version__  = "0.1.0"
__author__   = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

# Tile map — each entry is (char, fg_hex, bg_hex).
# '#' = solid wall, '.' = empty, '-' = platform
TILE_MAP: list[list[tuple[str, str, str]]] = []

# Entity spawns: (variant, tile_col, tile_row)
ENTITY_SPAWNS: list[tuple[str, int, int]] = []
