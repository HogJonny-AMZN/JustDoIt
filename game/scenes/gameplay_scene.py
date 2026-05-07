"""
Package: game.scenes.gameplay_scene
Main gameplay loop — tile world rendering, entities, particles, post-process.
"""

import logging as _logging

import arcade

from game.engine import (
    AsciiAtlas,
    TileRenderer,
    AsciiParticleSystem,
    PostProcessPipeline,
    ScrollingCamera,
)

# -------------------------------------------------------------------------
_MODULE_NAME = "game.scenes.gameplay_scene"
__updated__  = "2026-04-30"
__version__  = "0.1.0"
__author__   = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
class GameplayScene(arcade.View):
    """Main gameplay view."""

    def on_show_view(self) -> None:
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self) -> None:
        self.clear()

    def on_update(self, delta_time: float) -> None:
        pass

    def on_key_press(self, key: int, modifiers: int) -> None:
        pass
