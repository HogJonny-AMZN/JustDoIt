"""
Package: justdoit.fonts.builtin
Built-in hand-authored bitmap fonts.

Currently provides:
  BLOCK — 7-row Unicode block character font (A–Z, 0–9, punctuation)
  SLIM  — 3-row ASCII line-drawing font (A–Z, 0–9, punctuation)
"""

import logging as _logging

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.fonts.builtin"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)
