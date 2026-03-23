"""
Package: justdoit
JustDoIt — zero-dependency Python 3 ASCII art generator.

Public API: render() and colorize() are the primary entry points.
"""

import logging as _logging

from justdoit.core.rasterizer import render
from justdoit.effects.color import colorize

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

__all__ = ["render", "colorize"]
