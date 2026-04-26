"""
Package: justdoit.effects.fill
Glyph fill effects for ASCII art rendering.

Provides density-mapped ASCII fill (F01) and SDF-based shading (F06).
Both operate on GlyphMask (2D float arrays) produced by glyph_to_mask().
"""

import logging as _logging
from typing import Optional

from justdoit.core.glyph import mask_to_sdf

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.effects.fill"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

# Darkest to lightest — 12 density levels.
# Density ramp: densest (full coverage) → lightest → space
# Block elements prepended so solid-interior cells map to █ (100% coverage)
# rather than @ (~34% coverage). Makes fills appear bright and solid.
DENSITY_CHARS: str = "\u2588\u2593\u2592\u2591@#S%?*+;:,. "


# -------------------------------------------------------------------------
def density_fill(mask: list, density_chars: Optional[str] = None) -> list:
    """Map mask float values to characters based on a density scale.

    1.0 (full ink) maps to the darkest character; 0.0 (empty) maps to space.
    Returns a list of strings in the same format as a font glyph.

    :param mask: 2D list of floats from glyph_to_mask() — values 0.0–1.0.
    :param density_chars: Darkest-to-lightest char sequence (default: DENSITY_CHARS).
    :returns: List of strings — one per row, same shape as input mask.
    """
    chars = density_chars if density_chars is not None else DENSITY_CHARS
    n = len(chars)
    result = []
    for row in mask:
        line = ""
        for val in row:
            # val=1.0 → index 0 (darkest), val=0.0 → index n-1 (lightest/space)
            idx = int(val * (n - 1) + 0.5)
            idx = max(0, min(n - 1, idx))
            line += chars[n - 1 - idx]
        result.append(line)
    return result


# -------------------------------------------------------------------------
def sdf_fill(
    mask: list,
    density_chars: Optional[str] = None,
    gamma: float = 1.0,
    threshold: float = 0.0,
) -> list:
    """Fill using signed distance field — natural outline and shading effect.

    Computes the SDF of the mask (edge ≈ 0.5, interior → 1.0, exterior → 0.0),
    optionally applies a threshold and/or gamma curve, then applies density_fill.

    threshold > 0: cells with SDF >= threshold use the densest char (█);
    cells below threshold use the normal density ramp. Produces a bold solid
    interior with a crisp edge ring of lighter chars.
    e.g. threshold=0.5 fills everything > halfway from edge with █.

    gamma > 1.0 (without threshold): biases the ramp toward the interior.
    gamma=1.0 is linear (default, original behaviour).

    :param mask: 2D list of floats from glyph_to_mask() — values 0.0–1.0.
    :param density_chars: Darkest-to-lightest char sequence (default: DENSITY_CHARS).
    :param gamma: Curve exponent applied to SDF values before density mapping.
    :param threshold: SDF threshold above which the densest char is used (0=off).
    :returns: List of strings — one per row, same shape as input mask.
    """
    sdf = mask_to_sdf(mask)
    if threshold > 0.0:
        # Threshold mode: solid interior + narrow edge ramp
        chars = density_chars if density_chars is not None else DENSITY_CHARS
        densest = chars[0]  # █ when block chars are in the ramp
        # Build modified SDF: above threshold → 1.0 (maps to densest char)
        # below threshold → rescale [0, threshold] → [0, 0.9] for edge ramp
        scale = 0.9 / threshold if threshold > 0 else 1.0
        sdf = [[
            1.0 if v >= threshold else v * scale
            for v in row
        ] for row in sdf]
        return density_fill(sdf, density_chars)
    if gamma != 1.0:
        sdf = [[v ** gamma for v in row] for row in sdf]
    return density_fill(sdf, density_chars)
