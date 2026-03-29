"""
Package: justdoit.effects.recursive
Typographic recursion — fill rendered text cells with chars from the source text itself.

The visual effect: each "pixel" of the large letter is a character drawn
from the word being rendered, cycling: HELLO HELLO HELLO...

This is N01 in the TECHNIQUES.md registry.
"""

import logging as _logging

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.effects.recursive"
__updated__ = "2026-03-29 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
def typographic_recursion(
    rows: list,
    source_text: str,
    separator: str = " ",
    include_spaces: bool = False,
) -> list:
    """Replace each filled cell in the raster with successive chars from source_text.

    Creates the typographic recursion effect: text made from smaller instances
    of itself. Each non-space character in the rendered output is replaced by
    the next character in the cycling source_text sequence.

    :param rows: Rendered ASCII rows (list of strings, equal width)
    :param source_text: Text whose characters become the fill sequence
    :param separator: Separator inserted between word cycles (default: " ")
    :param include_spaces: If True, spaces in source_text are included in cycle
    :return: New rows with non-space cells replaced by source_text chars
    """
    if include_spaces:
        base_chars = list(source_text.upper())
    else:
        base_chars = [c for c in source_text.upper() if c.strip()]

    if not base_chars:
        _LOGGER.warning("typographic_recursion: source_text yielded no fill chars, returning unchanged")
        return rows

    # Build fill sequence: word chars + optional separator
    if separator:
        fill_chars = base_chars + list(separator)
    else:
        fill_chars = base_chars

    n = len(fill_chars)
    result = []
    char_idx = 0

    for row in rows:
        new_row = list(row)
        for col, cell in enumerate(row):
            if cell != " ":
                new_row[col] = fill_chars[char_idx % n]
                char_idx += 1
        result.append("".join(new_row))

    return result


# -------------------------------------------------------------------------
def typographic_recursion_multi(
    rows: list,
    source_text: str,
    levels: int = 2,
) -> list:
    """Apply typographic recursion with a multi-level offset for visual rhythm.

    Each row band cycles through source_text starting at a different offset,
    creating horizontal bands of repeating text that give a visual rhythm
    across the letter shape — denser at the top, sparser at the bottom
    (or vice versa depending on attractor structure).

    :param rows: Rendered ASCII rows
    :param source_text: Source text for fill chars
    :param levels: Number of row bands to divide the glyph into (default: 2)
    :return: Rows with multi-level typographic recursion applied
    """
    fill_chars = [c for c in source_text.upper() if c.strip()]
    if not fill_chars:
        return rows

    n = len(fill_chars)
    total_rows = len(rows)
    band_height = max(1, total_rows // max(1, levels))

    result = []
    char_idx = 0

    for row_idx, row in enumerate(rows):
        new_row = list(row)
        # Each band starts at a different offset in fill_chars
        band = row_idx // band_height
        band_offset = (band * (n // max(1, levels))) % n

        for col, cell in enumerate(row):
            if cell != " ":
                new_row[col] = fill_chars[(char_idx + band_offset) % n]
                char_idx += 1
        result.append("".join(new_row))

    return result
