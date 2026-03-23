"""
Package: justdoit.output
Output target adapters for rendered ASCII art.

Currently provides terminal (stdout) output. Future targets: HTML, SVG, PNG.
"""

import logging as _logging

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.output"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)
