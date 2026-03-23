"""
Package: justdoit.fonts
Font registry and loader for JustDoIt.

Populates the global FONTS dict with all available fonts:
  - Builtin: 'block' (7-row), 'slim' (3-row)
  - FIGlet: bundled .flf fonts auto-loaded from figlet_fonts/
  - TTF/OTF: loaded on demand via load_ttf_font() (requires Pillow)
"""

import logging as _logging

from justdoit.fonts.builtin.block import BLOCK
from justdoit.fonts.builtin.slim import SLIM

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.fonts"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

FONTS: dict = {
    "block": BLOCK,
    "slim": SLIM,
}

# Auto-load bundled FIGlet fonts — registers them into FONTS.
import justdoit.fonts.figlet_fonts  # noqa: E402,F401

# Optional TTF support — import only if Pillow is available.
try:
    from justdoit.fonts.ttf import load_ttf_font, find_system_fonts, rasterize_ttf  # noqa: F401
except ImportError:
    pass
