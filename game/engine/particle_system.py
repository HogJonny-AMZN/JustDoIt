"""
Package: game.engine.particle_system
Particle emitter where each particle is rendered as an ASCII glyph sprite.

Particles are plain data (position, velocity, lifetime, char, color).
Physics update runs on CPU each frame; drawing uses a pooled SpriteList.
"""

import logging as _logging
from dataclasses import dataclass, field
from typing      import Sequence

import arcade

from game.engine.atlas import AsciiAtlas

# -------------------------------------------------------------------------
_MODULE_NAME = "game.engine.particle_system"
__updated__  = "2026-04-30"
__version__  = "0.1.0"
__author__   = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
@dataclass
class Particle:
    """Single particle state."""
    x:        float
    y:        float
    vx:       float
    vy:       float
    char:     str
    color:    arcade.Color
    lifetime: float          # seconds remaining
    age:      float = 0.0


# -------------------------------------------------------------------------
@dataclass
class EmitterConfig:
    """Parameters controlling how a burst or stream of particles is spawned."""
    chars:          Sequence[str]           # glyph pool to pick from
    colors:         Sequence[arcade.Color]  # color pool
    count:          int   = 20
    speed_min:      float = 50.0
    speed_max:      float = 200.0
    lifetime_min:   float = 0.3
    lifetime_max:   float = 1.2
    gravity:        float = -300.0
    spread_angle:   float = 360.0           # degrees


# -------------------------------------------------------------------------
class AsciiParticleSystem:
    """
    Manages a pool of ASCII glyph particles.

    :param atlas: AsciiAtlas providing glyph textures.
    :param max_particles: Upper bound on live particles before oldest are culled.
    """

    def __init__(self, atlas: AsciiAtlas, max_particles: int = 512) -> None:
        self._atlas        = atlas
        self._max          = max_particles
        self._particles:   list[Particle] = []
        self._sprite_list: arcade.SpriteList | None = None

    # -------------------------------------------------------------------------
    def emit(self, x: float, y: float, config: EmitterConfig) -> None:
        """
        Spawn a burst of particles at *(x, y)*.

        :param x:      World x coordinate.
        :param y:      World y coordinate.
        :param config: EmitterConfig controlling spawn behaviour.
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    def update(self, delta_time: float) -> None:
        """
        Advance all particles by *delta_time* seconds and cull dead ones.

        :param delta_time: Elapsed time since last frame in seconds.
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    def draw(self) -> None:
        """Draw all live particles.  Must be called inside a draw pass."""
        raise NotImplementedError
