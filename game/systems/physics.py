"""
Package: game.systems.physics
Applies gravity, velocity integration, and tile collision resolution.
"""

import logging as _logging

# -------------------------------------------------------------------------
_MODULE_NAME = "game.systems.physics"
__updated__  = "2026-04-30"
__version__  = "0.1.0"
__author__   = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

GRAVITY = -980.0  # pixels / s²
