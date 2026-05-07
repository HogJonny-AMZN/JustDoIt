"""
Package: game.entities.player
Player entity — state, physics inputs, animation state machine.
"""

import logging as _logging
from dataclasses import dataclass, field

# -------------------------------------------------------------------------
_MODULE_NAME = "game.entities.player"
__updated__  = "2026-04-30"
__version__  = "0.1.0"
__author__   = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
@dataclass
class PlayerState:
    """Mutable runtime state for the player entity."""
    x:          float = 0.0
    y:          float = 0.0
    vx:         float = 0.0
    vy:         float = 0.0
    on_ground:  bool  = False
    health:     int   = 100
    facing_right: bool = True
