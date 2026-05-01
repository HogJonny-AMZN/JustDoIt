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
def _sdf_remap(
    v: float,
    floor: float = 0.0,
    mid: float = 0.5,
    high: float = 0.85,
    power: float = 1.0,
) -> float:
    """Piecewise SDF value remapper with configurable floor, mid, high and curve.

    Three zones:
      v < floor             → 0.0  (clipped — no character rendered)
      floor ≤ v < mid       → [0.0, 0.5]  outer glow ramp (power curve)
      mid   ≤ v < high      → [0.5, 1.0]  inner edge ring (power curve)
      v ≥ high              → 1.0  solid interior (█)

    power > 1: compress low values — sharper transition at floor/mid.
    power = 1: linear ramps (same as gamma=1.0 but with hard floor/high clip).
    power < 1: expand low values — softer wider glow.

    :param v: SDF value in [0.0, 1.0].
    :param floor: Below this → clipped to 0.  (default 0.0 = no clipping)
    :param mid: Boundary between outer glow and inner ring (default 0.5 = edge)
    :param high: Above this → solid █ (default 0.85)
    :param power: Curve exponent for both ramp segments (default 1.0 = linear)
    :returns: Remapped value in [0.0, 1.0].
    """
    if v < floor:
        return 0.0
    if v >= high:
        return 1.0
    if v < mid:
        # Outer glow: floor → mid maps to 0.0 → 0.5
        t = (v - floor) / max(mid - floor, 1e-6)
        return 0.5 * (t ** power)
    else:
        # Inner edge ring: mid → high maps to 0.5 → 1.0
        t = (v - mid) / max(high - mid, 1e-6)
        return 0.5 + 0.5 * (t ** power)


def sdf_fill(
    mask: list,
    density_chars: Optional[str] = None,
    gamma: float = 1.0,
    threshold: float = 0.0,
    floor: float = 0.0,
    mid: float = 0.5,
    high: float = 0.85,
    power: float = 1.0,
) -> list:
    """Fill using signed distance field — natural outline and shading effect.

    Computes the SDF of the mask (edge ≈ 0.5, interior → 1.0, exterior → 0.0),
    then applies one of two mapping modes:

    Piecewise curve mode (floor/mid/high/power):
      v < floor  → clipped to 0 (no char — hard exterior cutoff)
      floor→mid  → outer glow ramp [0.0 → 0.5] with power curve
      mid→high   → inner edge ring [0.5 → 1.0] with power curve
      v ≥ high   → solid █ interior
      power > 1 sharpens transitions; power < 1 softens/widens glow.

    Legacy gamma mode (when floor=mid=0, high=0.85 defaults not set):
      Apply v**gamma curve then density_fill.

    threshold > 0: cells ≥ threshold use densest char (█) — hard interior fill.

    :param mask: 2D list of floats from glyph_to_mask() — values 0.0–1.0.
    :param density_chars: Darkest-to-lightest char sequence (default: DENSITY_CHARS).
    :param gamma: Legacy gamma exponent (used when floor=0 and mid=0).
    :param threshold: Legacy hard threshold for densest char (0=off).
    :param floor: Piecewise floor — below this is clipped to 0 (default 0.0).
    :param mid: Piecewise midpoint — boundary between glow and ring (default 0.5).
    :param high: Piecewise high — above this is solid interior (default 0.85).
    :param power: Curve exponent for both ramp segments (default 1.0 = linear).
    :returns: List of strings — one per row, same shape as input mask.
    """
    sdf = mask_to_sdf(mask)

    # Piecewise mode: floor/mid/high/power all defined
    use_piecewise = (floor > 0.0 or mid != 0.5 or high != 0.85 or power != 1.0)
    if use_piecewise:
        sdf = [[
            _sdf_remap(v, floor=floor, mid=mid, high=high, power=power)
            for v in row
        ] for row in sdf]
        return density_fill(sdf, density_chars)

    # Legacy threshold mode
    if threshold > 0.0:
        scale = 0.9 / threshold
        sdf = [[
            1.0 if v >= threshold else v * scale
            for v in row
        ] for row in sdf]
        return density_fill(sdf, density_chars)

    # Legacy gamma mode
    if gamma != 1.0:
        sdf = [[v ** gamma for v in row] for row in sdf]
    return density_fill(sdf, density_chars)
