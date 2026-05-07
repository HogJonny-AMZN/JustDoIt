"""
Package: game.scenes.game_over_scene
Game over screen — score display, restart / quit options.
"""

import logging as _logging

import arcade

# -------------------------------------------------------------------------
_MODULE_NAME = "game.scenes.game_over_scene"
__updated__  = "2026-04-30"
__version__  = "0.1.0"
__author__   = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
class GameOverScene(arcade.View):
    """Game over view."""

    def on_show_view(self) -> None:
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self) -> None:
        self.clear()

    def on_key_press(self, key: int, modifiers: int) -> None:
        pass
