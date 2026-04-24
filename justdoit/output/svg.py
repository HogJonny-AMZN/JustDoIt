"""
Package: justdoit.output.svg
SVG output target for rendered ASCII art (O02).

Renders each character as a positioned <text> element with fill color.
Output is a valid SVG file. Characters are monospaced using a fixed
character-width estimate — no external font metrics required.

Pure Python stdlib — no external dependencies.
"""

import logging as _logging

from justdoit.output.ansi_parser import parse, effective_color

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.output.svg"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

# Monospace character size estimates in pixels at a given font-size
_CHAR_W_RATIO = 0.6   # char_width ≈ font_size * 0.6


# -------------------------------------------------------------------------
def to_svg(
    text: str,
    font_size: int = 14,
    bg_color: str = "#111111",
    line_height: float = 1.2,
    canvas_width: "int | None" = None,
    canvas_height: "int | None" = None,
) -> str:
    """Convert a rendered ANSI string to an SVG document.

    Each visible character becomes a <text> element positioned at its
    (x, y) coordinate based on row/column index and font metrics.

    :param text: Multi-line rendered string from render() (with or without ANSI).
    :param font_size: Font size in pixels (controls overall scale, default: 14).
    :param bg_color: Background rectangle fill color (default: '#111111').
    :param line_height: Line spacing as a multiplier of font_size (default: 1.2).
    :param canvas_width: Override SVG width in pixels (default: derived from content).
    :param canvas_height: Override SVG height in pixels (default: derived from content).
    :returns: SVG document string.
    """
    tokens = parse(text)

    # Lay out characters into rows
    rows: list = [[]]
    for ch, color in tokens:
        if ch == "\n":
            rows.append([])
        else:
            rows[-1].append((ch, color))

    max_cols = max((len(row) for row in rows), default=0)
    n_rows = len(rows)

    # Canvas size — use overrides when provided, else derive from content
    if canvas_width is not None and canvas_height is not None:
        width = canvas_width
        height = canvas_height
        # Derive char metrics from canvas to fill it
        char_w = width / max_cols if max_cols > 0 else font_size * _CHAR_W_RATIO
        line_h = height / n_rows if n_rows > 0 else font_size * line_height
        # In canvas mode, font-size must match char spacing — derive from char_w
        font_size = max(1, round(char_w / _CHAR_W_RATIO))
    else:
        char_w = font_size * _CHAR_W_RATIO
        line_h = font_size * line_height
        width = int(max_cols * char_w) + font_size
        height = int(n_rows * line_h) + font_size

    elements = []
    elements.append(
        f'<rect width="{width}" height="{height}" fill="{_svg_escape(bg_color)}"/>'
    )

    for row_idx, row in enumerate(rows):
        y = int((row_idx + 1) * line_h)
        for col_idx, (ch, color) in enumerate(row):
            if ch == " ":
                continue
            x = int(col_idx * char_w)
            r, g, b = effective_color(color)
            fill = f"#{r:02x}{g:02x}{b:02x}"
            safe_ch = _svg_escape(ch)
            elements.append(
                f'<text x="{x}" y="{y}" fill="{fill}" '
                f'font-size="{font_size}" '
                f'font-family="Courier New, Courier, monospace">'
                f'{safe_ch}</text>'
            )

    body = "\n  ".join(elements)
    return (
        f'<?xml version="1.0" encoding="utf-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}">\n'
        f'  {body}\n'
        f'</svg>\n'
    )


# -------------------------------------------------------------------------
def save_svg(text: str, path: str, font_size: int = 14, **kwargs) -> None:
    """Save rendered ASCII art as an SVG file.

    :param text: Multi-line rendered string from render().
    :param path: Output file path (e.g. 'output.svg').
    :param font_size: Font size in pixels (controls overall scale, default: 14).
    :param kwargs: Additional keyword arguments passed to to_svg().
    """
    svg = to_svg(text, font_size=font_size, **kwargs)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    _LOGGER.info(f"Saved SVG to {path}")


# -------------------------------------------------------------------------
def _svg_escape(s: str) -> str:
    """Escape XML special characters for use in SVG attribute values and text.

    :param s: Input string.
    :returns: String with &, <, >, ", ' escaped.
    """
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
         .replace("'", "&apos;")
    )
