"""
Package: game.engine
Reusable Arcade primitives for ASCII-style rendering.

Public surface:
    AsciiAtlas          — font texture atlas loader and glyph UV index
    TileRenderer        — batched draw of TileGrid to an Arcade render target
    AsciiParticleSystem — particle emitter where each particle is a glyph sprite
    PostProcessPipeline — render-texture chain with GLSL shader passes
    ScrollingCamera     — smooth-follow camera with viewport management
"""

from game.engine.atlas           import AsciiAtlas
from game.engine.tile_renderer   import TileRenderer
from game.engine.particle_system import AsciiParticleSystem
from game.engine.post_process    import PostProcessPipeline
from game.engine.camera          import ScrollingCamera

__all__ = [
    "AsciiAtlas",
    "TileRenderer",
    "AsciiParticleSystem",
    "PostProcessPipeline",
    "ScrollingCamera",
]
