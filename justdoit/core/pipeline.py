"""
Package: justdoit.core.pipeline
Stage-chaining pipeline — stub for future composable render architecture.

Planned pipeline stages:
  text
    → glyph lookup / generation
    → rasterize to pixel grid
    → spatial effects  (warp, distort, rotate, perspective)
    → fill pass        (noise, gradient, pattern, cellular, fractal)
    → composite layers (background, shadow, outline, glow)
    → colorize         (flat, gradient, per-char, rainbow, palette)
    → output target    (terminal, file, HTML, SVG, PNG)
"""

import logging as _logging

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.core.pipeline"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)
