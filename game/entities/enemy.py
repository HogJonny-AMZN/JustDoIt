"""
Package: game.entities.enemy
Enemy entity — base class and concrete types.
"""

import logging as _logging
from dataclasses import dataclass

# -------------------------------------------------------------------------
_MODULE_NAME = "game.entities.enemy"
__updated__  = "2026-04-30"
__version__  = "0.1.0"
__author__   = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
@dataclass
class EnemyState:
    """Mutable runtime state shared by all enemy types."""
    x:       float = 0.0
    y:       float = 0.0
    vx:      float = 0.0
    vy:      float = 0.0
    health:  int   = 10
    variant: str   = "basic"
