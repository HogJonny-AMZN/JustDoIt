"""
Package: game.scenes.title_scene
Title screen — animated ASCII logo, menu options, transitions to gameplay.
"""

import logging as _logging

import arcade

# -------------------------------------------------------------------------
_MODULE_NAME = "game.scenes.title_scene"
__updated__  = "2026-04-30"
__version__  = "0.1.0"
__author__   = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
class TitleScene(arcade.View):
    """Title screen view."""

    def on_show_view(self) -> None:
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self) -> None:
        self.clear()

    def on_update(self, delta_time: float) -> None:
        pass

    def on_key_press(self, key: int, modifiers: int) -> None:
        pass
