"""
Package: game.engine.post_process
Render-texture chain with GLSL shader passes (CRT, bloom, chromatic aberration).

Usage pattern:
    pipeline = PostProcessPipeline(width, height)
    pipeline.add_pass("crt",   Path("game/shaders/crt.glsl"))
    pipeline.add_pass("bloom", Path("game/shaders/bloom.glsl"))

    # In draw():
    with pipeline.capture():
        draw_scene()          # draws to offscreen render texture
    pipeline.render()         # applies passes and blits to screen
"""

import logging as _logging
from pathlib import Path

import arcade

# -------------------------------------------------------------------------
_MODULE_NAME = "game.engine.post_process"
__updated__  = "2026-04-30"
__version__  = "0.1.0"
__author__   = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
class ShaderPass:
    """One GLSL post-process pass applied to an offscreen render texture."""

    def __init__(self, name: str, shader_path: Path) -> None:
        self.name        = name
        self.shader_path = shader_path
        self._program: arcade.gl.Program | None = None

    # -------------------------------------------------------------------------
    def load(self, ctx: arcade.ArcadeContext) -> None:
        """
        Compile the shader from *shader_path*.

        :param ctx: Active Arcade OpenGL context.
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    def apply(self, source: arcade.gl.Texture2D, target: arcade.gl.Framebuffer) -> None:
        """
        Read from *source*, write post-processed result to *target*.

        :param source: Input render texture from previous pass (or scene capture).
        :param target: Output framebuffer.
        """
        raise NotImplementedError


# -------------------------------------------------------------------------
class PostProcessPipeline:
    """
    Ordered chain of ShaderPass objects applied after scene rendering.

    :param width:  Logical render width in pixels.
    :param height: Logical render height in pixels.
    """

    def __init__(self, width: int, height: int) -> None:
        self._width   = width
        self._height  = height
        self._passes: list[ShaderPass] = []

    # -------------------------------------------------------------------------
    def add_pass(self, name: str, shader_path: Path) -> None:
        """
        Append a shader pass to the pipeline.

        :param name:        Identifier for the pass (used in logging).
        :param shader_path: Path to the GLSL fragment shader source.
        """
        self._passes.append(ShaderPass(name, shader_path))

    # -------------------------------------------------------------------------
    def capture(self):
        """Context manager: redirect draw calls to the offscreen render texture."""
        raise NotImplementedError

    # -------------------------------------------------------------------------
    def render(self) -> None:
        """Apply all passes in order and blit final result to the screen."""
        raise NotImplementedError
