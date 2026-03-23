"""Auto-load all .flf FIGlet fonts in this directory into the FONTS registry."""

import os
from justdoit.fonts.figlet import load_flf_font

_FONTS_DIR = os.path.dirname(__file__)

for _filename in sorted(os.listdir(_FONTS_DIR)):
    if _filename.endswith('.flf'):
        _path = os.path.join(_FONTS_DIR, _filename)
        _stem = os.path.splitext(_filename)[0]
        # Avoid colliding with built-in 'block' font
        _name = f'figlet-{_stem}' if _stem == 'block' else _stem
        load_flf_font(_path, _name)
