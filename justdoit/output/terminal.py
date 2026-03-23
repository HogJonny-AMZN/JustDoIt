"""
Package: justdoit.output.terminal
Terminal (stdout) output adapter for rendered ASCII art.

The simplest output target — prints the rendered string directly to stdout.
Future targets (HTML, SVG, PNG) will follow the same single-function interface.
"""

import logging as _logging

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.output.terminal"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
def print_art(rendered: str) -> None:
    """Print rendered ASCII art to stdout.

    :param rendered: Multi-line ANSI string from render().
    """
    print(rendered)
