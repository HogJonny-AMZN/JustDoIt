"""
Package: justdoit.animate
Terminal animation engine for ASCII art.

Provides a frame-loop player and preset animation generators.
The player drives any generator that yields strings (frames).
"""

import logging as _logging

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.animate"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)
