"""
Package: justdoit.fonts.figlet
FIGlet .flf font parser and loader.

FIGlet font format spec:
  Header: flf2a<hardblank> <height> <baseline> <max_width> <old_layout>
          <comment_lines> [<print_direction> [<full_layout> [<codetag_count>]]]
  Then <comment_lines> lines of comments.
  Then glyph definitions for ASCII chars 32–126 (and optional tagged Unicode).
  Each glyph is <height> lines; each line ends with @ (continuation) or @@ (end of glyph).
"""

import logging as _logging
import os
from typing import Optional

from justdoit.fonts import FONTS

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.fonts.figlet"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
def parse_flf(path: str) -> dict:
    """Parse a .flf FIGlet font file into a FONTS-compatible glyph dict.

    Returns a font dict: {char: [row0, row1, ...]}
    All glyphs have the same height (padded with spaces if needed).
    Hardblank chars are replaced with regular spaces.

    :param path: Path to the .flf font file.
    :returns: Dict mapping character to list of row strings.
    :raises ValueError: If the file is empty, has a bad header, or malformed glyph data.
    """
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    if not lines:
        raise ValueError(f"Empty FIGlet font file: {path}")

    header = lines[0].rstrip("\r\n")
    if not header.startswith("flf2a"):
        raise ValueError(f"Not a valid FIGlet font (bad header): {path}")

    # Header: flf2a<hardblank> <height> <baseline> <max_width> <old_layout> <comment_lines> ...
    hardblank = header[5]
    parts = header[6:].split()
    if len(parts) < 6:
        raise ValueError(f"Malformed FIGlet header in: {path}")

    height = int(parts[0])
    comment_lines = int(parts[4])

    data_start = 1 + comment_lines
    data_lines = [ln.rstrip("\r\n") for ln in lines[data_start:]]

    font: dict = {}
    line_iter = iter(data_lines)

    # Parse glyphs for printable ASCII 32–126
    for code in range(32, 127):
        char = chr(code)
        glyph = _read_glyph(line_iter, height, hardblank)
        width = max((len(r) for r in glyph), default=0)
        font[char] = [r.ljust(width) for r in glyph]

    return font


# -------------------------------------------------------------------------
def _read_glyph(line_iter, height: int, hardblank: str) -> list:
    """Read one glyph of height rows from line_iter, stripping FIGlet end markers.

    :param line_iter: Iterator over the font data lines.
    :param height: Number of rows per glyph.
    :param hardblank: The hardblank character to replace with a real space.
    :returns: List of row strings for this glyph.
    """
    rows = []
    for _ in range(height):
        try:
            line = next(line_iter)
        except StopIteration:
            line = ""
        # Strip trailing @ end markers (@@ = end of glyph, @ = continuation line)
        if line.endswith("@@"):
            line = line[:-2]
        elif line.endswith("@"):
            line = line[:-1]
        line = line.replace(hardblank, " ")
        rows.append(line)
    return rows


# -------------------------------------------------------------------------
def load_flf_font(path: str, name: Optional[str] = None) -> str:
    """Parse a .flf font and register it in the global FONTS dict.

    :param path: Path to the .flf font file.
    :param name: Registry key (default: filename stem, e.g. 'big').
    :returns: The registered font name.
    """
    if name is None:
        name = os.path.splitext(os.path.basename(path))[0]
    font = parse_flf(path)
    FONTS[name] = font
    _LOGGER.debug(f"Loaded FIGlet font '{name}' from {path}")
    return name
