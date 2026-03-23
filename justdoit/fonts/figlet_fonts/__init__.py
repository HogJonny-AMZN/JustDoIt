"""
Package: justdoit.fonts.figlet_fonts
Auto-loader for bundled FIGlet .flf fonts.

All .flf files in this directory are loaded into the FONTS registry at import time.
The bundled 'block' FIGlet font is registered as 'figlet-block' to avoid colliding
with the builtin 'block' font.
"""

import logging as _logging
import os

from justdoit.fonts.figlet import load_flf_font

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.fonts.figlet_fonts"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_FONTS_DIR = os.path.dirname(__file__)

for _filename in sorted(os.listdir(_FONTS_DIR)):
    if _filename.endswith(".flf"):
        _path = os.path.join(_FONTS_DIR, _filename)
        _stem = os.path.splitext(_filename)[0]
        # Avoid colliding with the builtin 'block' font
        _name = f"figlet-{_stem}" if _stem == "block" else _stem
        load_flf_font(_path, _name)
        _LOGGER.debug(f"Auto-loaded FIGlet font '{_name}'")
