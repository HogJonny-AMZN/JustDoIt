"""
Package: game.main
Entry point for the JustDoIt ASCII side-scroller.
"""

import logging as _logging

import arcade

from game.scenes.title_scene import TitleScene

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "game.main"
__updated__ = "2026-04-30"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

# Logical resolution — 32:9 aspect ratio at a manageable scale.
# The Arcade window is created at this size; post-process pass scales to physical.
LOGICAL_WIDTH  = 3840
LOGICAL_HEIGHT = 1080
WINDOW_TITLE   = "JustDoIt: ASCII Side-Scroller"
TARGET_FPS     = 60


# -------------------------------------------------------------------------
def main() -> None:
    """Create the Arcade window and run the game loop."""
    window = arcade.Window(LOGICAL_WIDTH, LOGICAL_HEIGHT, WINDOW_TITLE, resizable=True)
    title  = TitleScene()
    window.show_view(title)
    arcade.run()


# -------------------------------------------------------------------------
if __name__ == "__main__":
    main()
