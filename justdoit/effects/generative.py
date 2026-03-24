"""
Package: justdoit.effects.generative
Generative fill effects for ASCII art rendering.

Operates on GlyphMask (2D float arrays from glyph_to_mask()).
Returns list[str] in the same format as density_fill / sdf_fill,
so these slot directly into the fill pipeline in core/rasterizer.py.

Implemented techniques:
  F02 — noise_fill:    Perlin-style gradient noise drives character selection
                       inside the glyph mask. Every render is different unless seeded.
  F03 — cells_fill:    Conway's Game of Life seeded inside the glyph mask,
                       evolved N steps then frozen. The letter is legible but
                       the interior looks like a biological pattern.
  F10 — truchet_fill:  Truchet tile tiling inside glyph mask. Each ink cell gets
                       one of two tile orientations (diagonal ╱╲, arc ╰╮, or
                       wave-biased diagonals), creating labyrinth / flow patterns.
                       Inspired by Sébastien Truchet (1704) and the "10 PRINT" demoscene.

All are pure Python stdlib — no external dependencies.
"""

import logging as _logging
import math
import random
from typing import Optional

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.effects.generative"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

# Density char scales (darkest → lightest)
_DENSE: str = "@#S%?*+;:,. "
_CELLS_CHARS: str = "█▓▒░ "   # alive-inside → dead-inside → outside


# -------------------------------------------------------------------------
# Perlin noise implementation (pure Python, 2D)
# Based on Ken Perlin's improved noise algorithm (2002).

_PERM_BASE: list = list(range(256))

# -------------------------------------------------------------------------
def _build_perm(seed: Optional[int]) -> list:
    """Build a 512-element permutation table for Perlin noise.

    :param seed: Optional integer seed for reproducibility.
    :returns: List of 512 ints (doubled 0–255 permutation).
    """
    rng = random.Random(seed)
    perm = _PERM_BASE[:]
    rng.shuffle(perm)
    return perm + perm   # doubled for easy wrapping


# -------------------------------------------------------------------------
def _fade(t: float) -> float:
    """Perlin fade curve: 6t⁵ - 15t⁴ + 10t³.

    :param t: Input value 0.0–1.0.
    :returns: Smoothed value.
    """
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


# -------------------------------------------------------------------------
def _lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b.

    :param a: Start value.
    :param b: End value.
    :param t: Interpolation factor 0.0–1.0.
    :returns: Interpolated value.
    """
    return a + t * (b - a)


# -------------------------------------------------------------------------
def _grad(hash_val: int, x: float, y: float) -> float:
    """Compute gradient contribution from a hash value and offset.

    :param hash_val: Hash value from permutation table.
    :param x: X offset from grid corner.
    :param y: Y offset from grid corner.
    :returns: Dot product of gradient vector with offset vector.
    """
    h = hash_val & 3
    if h == 0:
        return  x + y
    elif h == 1:
        return -x + y
    elif h == 2:
        return  x - y
    else:
        return -x - y


# -------------------------------------------------------------------------
def _perlin2d(x: float, y: float, perm: list) -> float:
    """Evaluate 2D Perlin noise at (x, y).

    :param x: X coordinate.
    :param y: Y coordinate.
    :param perm: 512-element permutation table from _build_perm().
    :returns: Noise value in approximately -1.0 to 1.0.
    """
    xi = int(math.floor(x)) & 255
    yi = int(math.floor(y)) & 255
    xf = x - math.floor(x)
    yf = y - math.floor(y)
    u = _fade(xf)
    v = _fade(yf)

    aa = perm[perm[xi    ] + yi    ]
    ab = perm[perm[xi    ] + yi + 1]
    ba = perm[perm[xi + 1] + yi    ]
    bb = perm[perm[xi + 1] + yi + 1]

    return _lerp(
        _lerp(_grad(aa, xf,       yf      ), _grad(ba, xf - 1.0, yf      ), u),
        _lerp(_grad(ab, xf,       yf - 1.0), _grad(bb, xf - 1.0, yf - 1.0), u),
        v,
    )


# -------------------------------------------------------------------------
def noise_fill(
    mask: list,
    density_chars: Optional[str] = None,
    scale: float = 0.4,
    seed: Optional[int] = None,
) -> list:
    """Fill glyph mask using 2D Perlin gradient noise (F02).

    Each ink cell in the mask is assigned a character based on its Perlin
    noise value at that grid position. Empty cells become spaces.
    The result is an organic, textured fill — different every render
    unless a seed is provided.

    :param mask: 2D list of floats from glyph_to_mask() — values 0.0–1.0.
    :param density_chars: Darkest-to-lightest char sequence (default: _DENSE).
    :param scale: Noise frequency — higher = finer detail (default: 0.4).
    :param seed: Optional integer seed for reproducibility.
    :returns: List of strings — one per row, same shape as input mask.
    """
    chars = density_chars if density_chars is not None else _DENSE
    n = len(chars)
    perm = _build_perm(seed)
    result = []

    for r, row in enumerate(mask):
        line = ""
        for c, val in enumerate(row):
            if val < 0.5:
                line += " "
                continue
            # Sample noise at scaled grid coords; normalize to 0–1
            raw = _perlin2d(c * scale, r * scale, perm)
            t = (raw + 1.0) / 2.0   # -1..1 → 0..1
            t = max(0.0, min(1.0, t))
            idx = int(t * (n - 1) + 0.5)
            idx = max(0, min(n - 1, idx))
            line += chars[n - 1 - idx]   # darker = denser (index 0)
        result.append(line)

    return result


# -------------------------------------------------------------------------
def cells_fill(
    mask: list,
    steps: int = 4,
    seed: Optional[int] = None,
    alive_prob: float = 0.5,
) -> list:
    """Fill glyph mask using Conway's Game of Life frozen after N steps (F03).

    Seeds GoL randomly inside the ink mask, evolves steps generations,
    then freezes. Alive cells inside the mask → dense chars; dead cells
    inside the mask → light chars; outside → space.

    :param mask: 2D list of floats from glyph_to_mask() — values 0.0–1.0.
    :param steps: Number of GoL generations to simulate (default: 4).
    :param seed: Optional integer seed for reproducibility.
    :param alive_prob: Probability a mask cell starts alive (default: 0.5).
    :returns: List of strings — one per row, same shape as input mask.
    """
    rng = random.Random(seed)
    rows = len(mask)
    if rows == 0:
        return []
    cols = max(len(row) for row in mask)

    # Ink mask — only cells with val >= 0.5 are inside the glyph
    ink = [[mask[r][c] >= 0.5 if c < len(mask[r]) else False
            for c in range(cols)]
           for r in range(rows)]

    # Seed GoL state randomly inside ink cells
    state = [[ink[r][c] and rng.random() < alive_prob
              for c in range(cols)]
             for r in range(rows)]

    # -------------------------------------------------------------------------
    def _step(s: list) -> list:
        """Advance GoL one generation, constrained to ink mask.

        :param s: Current state grid.
        :returns: Next generation state grid.
        """
        ns = [[False] * cols for _ in range(rows)]
        for r in range(rows):
            for c in range(cols):
                if not ink[r][c]:
                    continue
                # Count alive neighbours (8-connected, wrap stays inside mask)
                alive_nb = 0
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < rows and 0 <= nc < cols and ink[nr][nc]:
                            if s[nr][nc]:
                                alive_nb += 1
                # Standard Conway rules
                if s[r][c]:
                    ns[r][c] = alive_nb in (2, 3)
                else:
                    ns[r][c] = alive_nb == 3
        return ns

    for _ in range(steps):
        state = _step(state)

    # Map to characters
    result = []
    for r in range(rows):
        line = ""
        for c in range(cols):
            if not ink[r][c]:
                line += " "
            elif state[r][c]:
                line += _CELLS_CHARS[0]   # alive → densest
            else:
                # Dead inside mask — use a lighter shade based on neighbour density
                alive_nb = sum(
                    1
                    for dr in (-1, 0, 1)
                    for dc in (-1, 0, 1)
                    if not (dr == 0 and dc == 0)
                    and 0 <= r + dr < rows
                    and 0 <= c + dc < cols
                    and ink[r + dr][c + dc]
                    and state[r + dr][c + dc]
                )
                shade_idx = min(3, max(1, 3 - alive_nb // 2))
                line += _CELLS_CHARS[shade_idx]
        result.append(line)

    return result


# -------------------------------------------------------------------------
# Truchet tile character sets
#
# Each style provides exactly 2 tile variants that get assigned randomly.
# Outside the glyph mask → space.
#
# Styles:
#   "diagonal"  — forward/back diagonals (╱╲), the "10 PRINT" effect
#   "arc"       — quarter-arc connectors (╰╮ / ╭╯), smooth flow
#   "cross"     — hash/pipe combo (╋ / ╬ ... or simple + / ×)
#   "block"     — filled/half-block tiles (▀▄ — emphasise mass)

_TRUCHET_STYLES: dict = {
    "diagonal": ("╱", "╲"),
    "arc":      ("╰", "╮"),    # tile A: corners connect BL→TR; tile B: TL→BR
    "arc2":     ("╭", "╯"),    # variant — opposite corners
    "cross":    ("+", "×"),
    "block":    ("▀", "▄"),
    "sparse":   ("·", "∙"),
}

_DEFAULT_TRUCHET_STYLE: str = "diagonal"


# -------------------------------------------------------------------------
def truchet_fill(
    mask: list,
    style: str = "diagonal",
    seed: Optional[int] = None,
    bias: float = 0.5,
) -> list:
    """Fill glyph mask with randomised Truchet tiling (F10).

    Each ink cell in the mask is assigned one of two tile characters
    independently at random (controlled by *bias*). This creates
    labyrinth-like flow patterns inside the letter form — inspired by
    Sébastien Truchet (1704) and the demoscene "10 PRINT" one-liner.

    Available styles and their character pairs:
      "diagonal"  — ╱ / ╲  (10-PRINT style — the classic)
      "arc"       — ╰ / ╮  (arc connectors — smooth, wave-like)
      "arc2"      — ╭ / ╯  (arc variant)
      "cross"     — + / ×  (clean grid cross)
      "block"     — ▀ / ▄  (half-block emphasis)
      "sparse"    — · / ∙  (light dot texture)

    :param mask: 2D list of floats from glyph_to_mask() — values 0.0–1.0.
    :param style: Tile style name (default: "diagonal").
    :param seed: Optional integer seed for reproducibility.
    :param bias: Probability of choosing tile A vs tile B (default: 0.5 = equal).
    :returns: List of strings — one per row, same shape as input mask.
    :raises ValueError: If style name is unknown.
    """
    if style not in _TRUCHET_STYLES:
        raise ValueError(
            f"Unknown truchet style '{style}'. "
            f"Available: {', '.join(_TRUCHET_STYLES.keys())}"
        )
    tile_a, tile_b = _TRUCHET_STYLES[style]
    rng = random.Random(seed)

    result = []
    for row in mask:
        line = ""
        for val in row:
            if val < 0.5:
                line += " "
            else:
                line += tile_a if rng.random() < bias else tile_b
        result.append(line)

    return result
