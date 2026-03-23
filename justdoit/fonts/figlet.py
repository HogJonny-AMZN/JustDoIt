"""FIGlet .flf font parser.

FIGlet font format spec:
  Header: flf2a<hardblank> <height> <baseline> <max_width> <old_layout>
          <comment_lines> [<print_direction> [<full_layout> [<codetag_count>]]]
  Then <comment_lines> lines of comments.
  Then glyph definitions for ASCII chars 32-126 (and optional tagged Unicode).
  Each glyph is <height> lines, each ending with @ (continuation) or @@ (end of glyph).
"""

import os
from justdoit.fonts import FONTS


def parse_flf(path: str) -> dict:
    """Parse a .flf FIGlet font file.

    Returns a font dict compatible with FONTS registry format:
      {char: [row0, row1, ...]}

    All glyphs have the same height (padded with spaces if needed).
    Hardblank chars are replaced with regular spaces.
    """
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    if not lines:
        raise ValueError(f"Empty FIGlet font file: {path}")

    header = lines[0].rstrip('\r\n')
    if not header.startswith('flf2a'):
        raise ValueError(f"Not a valid FIGlet font (bad header): {path}")

    # Header: flf2a<hardblank> <height> <baseline> <max_width> <old_layout> <comment_lines> ...
    hardblank = header[5]
    parts = header[6:].split()
    if len(parts) < 6:
        raise ValueError(f"Malformed FIGlet header in: {path}")

    height = int(parts[0])
    comment_lines = int(parts[4])

    # Skip comment lines
    data_start = 1 + comment_lines
    data_lines = [l.rstrip('\r\n') for l in lines[data_start:]]

    font = {}

    def _read_glyph(line_iter, height):
        rows = []
        for _ in range(height):
            try:
                line = next(line_iter)
            except StopIteration:
                line = ''
            # Strip trailing @ markers (@ or @@)
            if line.endswith('@@'):
                line = line[:-2]
            elif line.endswith('@'):
                line = line[:-1]
            # Replace hardblank with space
            line = line.replace(hardblank, ' ')
            rows.append(line)
        return rows

    line_iter = iter(data_lines)

    # Parse glyphs for ASCII 32-126
    for code in range(32, 127):
        char = chr(code)
        glyph = _read_glyph(line_iter, height)
        # Pad all rows to same width
        width = max((len(r) for r in glyph), default=0)
        glyph = [r.ljust(width) for r in glyph]
        font[char] = glyph

    return font


def load_flf_font(path: str, name: str = None) -> str:
    """Parse a .flf font and register it in FONTS.

    Returns the registered font name.
    If name is None, derives it from the filename (without extension).
    """
    if name is None:
        name = os.path.splitext(os.path.basename(path))[0]
    font = parse_flf(path)
    FONTS[name] = font
    return name
