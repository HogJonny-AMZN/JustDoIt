from justdoit.fonts.builtin.block import BLOCK
from justdoit.fonts.builtin.slim import SLIM

FONTS = {
    'block': BLOCK,
    'slim': SLIM,
}

import justdoit.fonts.figlet_fonts  # noqa: E402 — registers bundled FIGlet fonts into FONTS
