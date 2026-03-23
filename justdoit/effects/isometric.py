"""
Package: justdoit.effects.isometric
Isometric 3D extrusion effect for ASCII art rendering (S03).

Takes a fully-rendered multi-line string and extrudes it in isometric space,
producing chunky 3D block letters with distinct top and side faces.

Algorithm:
  Each ink cell (r, c) in the original is placed as the "front face" at
  canvas position (r + depth, c).  For each depth step d in 1..depth, a
  shade character is drawn at (r + depth - d, c + d), going one row up and
  one column right per step.  Depth layers are drawn back-to-front so
  closer cells override farther ones; the front face is drawn last and
  overrides everything.

  This produces:
    - Top face visibility: shade chars peeking above the top edge of the front face
    - Right face visibility: shade chars peeking to the right of the right edge
    - Hidden faces: automatically covered by the front face (correct for this viewpoint)

Direction "right" (default): depth goes up-right (-1 row, +1 col per step)
Direction "left": depth goes up-left (-1 row, -1 col per step); canvas
  shifts right by `depth` columns to make room on the left side.

Output is plain Unicode (no ANSI) so gradient/color effects can be
applied afterward via effects.gradient.
"""

import logging as _logging
import re
from typing import Optional

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.effects.isometric"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")

# Depth shade sequence: index 0 = closest (d=1), last = furthest (d=depth).
# Rendered back-to-front so closest overrides furthest.
_DEPTH_SHADES: list = ["▓", "▒", "░", "·"]


# -------------------------------------------------------------------------
def isometric_extrude(
    text: str,
    depth: int = 4,
    direction: str = "right",
    front_char: Optional[str] = None,
) -> str:
    """Extrude rendered ASCII art into isometric 3D block letters (S03).

    Each ink character in the source is projected onto a larger canvas:
      - Front face: at the original position (shifted down by depth rows).
      - Depth face: shade characters at diagonal positions above/beside the front face.

    The result resembles chunky 3D block letters viewed from a 45° isometric angle,
    with visible top and side faces.

    :param text: Multi-line rendered string from render().
    :param depth: Number of depth layers — controls how thick the 3D extrusion is (default: 4).
    :param direction: Extrusion direction — "right" (up-right, default) or "left" (up-left).
    :param front_char: Override character for the front face (default: preserve original chars).
    :returns: Multi-line Unicode string with isometric extrusion applied.
    :raises ValueError: If direction is not "right" or "left", or depth < 1.
    """
    if direction not in ("right", "left"):
        raise ValueError(f"direction must be 'right' or 'left', got {direction!r}")
    if depth < 1:
        raise ValueError(f"depth must be >= 1, got {depth}")
    if not text:
        return text

    lines = text.split("\n")

    # Strip ANSI to get plain visible content
    visible = [_ANSI_RE.sub("", line) for line in lines]
    n_rows = len(visible)
    n_cols = max(len(r) for r in visible) if visible else 0
    if n_cols == 0:
        return text

    # Pad all rows to uniform width
    visible = [r.ljust(n_cols) for r in visible]

    # Build character grid and ink mask
    chars: list = [[visible[r][c] for c in range(n_cols)] for r in range(n_rows)]
    ink: list = [[chars[r][c] != " " for c in range(n_cols)] for r in range(n_rows)]

    # -------------------------------------------------------------------------
    # Canvas sizing
    # direction "right": depth goes (-d_row, +d_col) = (-1, +1) per step
    #   front face at canvas (r + depth, c)
    #   depth d at canvas (r + depth - d, c + d)
    #   canvas: (n_rows + depth) × (n_cols + depth)
    #
    # direction "left": depth goes (-1, -1) per step
    #   front face at canvas (r + depth, c + depth)   [shifted right to make room]
    #   depth d at canvas (r + depth - d, c + depth - d)
    #   canvas: (n_rows + depth) × (n_cols + depth)

    c_rows = n_rows + depth
    c_cols = n_cols + depth
    canvas: list = [[" "] * c_cols for _ in range(c_rows)]

    # -------------------------------------------------------------------------
    def _shade_for_depth(d: int) -> str:
        """Map depth step d (1=closest, depth=furthest) to a shade character.

        :param d: Depth step — 1 is closest to front, depth is furthest back.
        :returns: Shade character from _DEPTH_SHADES.
        """
        if depth == 1:
            return _DEPTH_SHADES[0]
        # t = 0.0 at d=1 (closest/darkest), 1.0 at d=depth (furthest/lightest)
        t = (d - 1) / (depth - 1)
        idx = min(len(_DEPTH_SHADES) - 1, int(t * (len(_DEPTH_SHADES) - 1) + 0.5))
        return _DEPTH_SHADES[idx]

    # -------------------------------------------------------------------------
    # Draw depth layers back-to-front (d=depth first, d=1 last)
    for d in range(depth, 0, -1):
        shade = _shade_for_depth(d)
        for r in range(n_rows):
            for c in range(n_cols):
                if not ink[r][c]:
                    continue
                if direction == "right":
                    cr = r + depth - d
                    cc = c + d
                else:  # left
                    cr = r + depth - d
                    cc = c + depth - d
                if 0 <= cr < c_rows and 0 <= cc < c_cols:
                    canvas[cr][cc] = shade

    # -------------------------------------------------------------------------
    # Draw front face on top (overrides all depth layers)
    for r in range(n_rows):
        for c in range(n_cols):
            if not ink[r][c]:
                continue
            if direction == "right":
                cr = r + depth
                cc = c
            else:  # left
                cr = r + depth
                cc = c + depth
            if 0 <= cr < c_rows and 0 <= cc < c_cols:
                canvas[cr][cc] = front_char if front_char else chars[r][c]

    # -------------------------------------------------------------------------
    # Trim trailing whitespace from each row (cleaner output)
    result_lines = ["".join(row).rstrip() for row in canvas]
    return "\n".join(result_lines)


# -------------------------------------------------------------------------
def iso_render(
    text: str,
    font: str = "block",
    depth: int = 4,
    direction: str = "right",
    gap: int = 1,
) -> str:
    """Convenience wrapper: render text then immediately apply isometric extrusion.

    :param text: Input string to render.
    :param font: Font name for render() (default: 'block').
    :param depth: Isometric extrusion depth (default: 4).
    :param direction: Extrusion direction — 'right' or 'left' (default: 'right').
    :param gap: Character gap passed to render() (default: 1).
    :returns: Multi-line isometric ASCII art string.
    """
    from justdoit.core.rasterizer import render
    rendered = render(text, font=font, gap=gap)
    return isometric_extrude(rendered, depth=depth, direction=direction)
