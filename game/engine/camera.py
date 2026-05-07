"""
Package: game.engine.camera
Smooth-follow scrolling camera with configurable deadzone and damping.
"""

import logging as _logging

import arcade

# -------------------------------------------------------------------------
_MODULE_NAME = "game.engine.camera"
__updated__  = "2026-04-30"
__version__  = "0.1.0"
__author__   = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
class ScrollingCamera:
    """
    2D scrolling camera that smoothly tracks a target position.

    :param viewport_width:  Logical viewport width in pixels.
    :param viewport_height: Logical viewport height in pixels.
    :param damping:         Lerp factor (0.0–1.0); lower = smoother/slower.
    """

    def __init__(
        self,
        viewport_width:  int,
        viewport_height: int,
        damping:         float = 0.1,
    ) -> None:
        self._vw      = viewport_width
        self._vh      = viewport_height
        self._damping = damping
        self._camera  = arcade.camera.Camera2D()
        self._target_x = 0.0
        self._target_y = 0.0

    # -------------------------------------------------------------------------
    def follow(self, x: float, y: float) -> None:
        """
        Set the world position the camera should track.

        :param x: Target world x coordinate.
        :param y: Target world y coordinate.
        """
        self._target_x = x
        self._target_y = y

    # -------------------------------------------------------------------------
    def update(self, delta_time: float) -> None:
        """
        Lerp camera position toward the tracked target.

        :param delta_time: Elapsed time since last frame in seconds.
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    def use(self) -> None:
        """Activate this camera for subsequent draw calls."""
        self._camera.use()
