"""
Package: justdoit.effects.spatial
Spatial transformation effects for ASCII art rendering.

Operates on fully-rendered multi-line strings (output of render()).
All effects are pure Python stdlib — no external dependencies.

Implemented techniques:
  S01 — sine_warp: horizontal row oscillation (flag/wave effect)
  S02 — perspective_tilt: per-row width scaling (vanishing-point fake 3D)
  S08 — shear: per-row horizontal offset (italic/oblique effect)
"""

import logging as _logging
import math
from typing import Optional

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.effects.spatial"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
def sine_warp(
    text: str,
    amplitude: float = 3.0,
    frequency: float = 1.0,
    amplitude_map: Optional[list] = None,
) -> str:
    """Shift each row horizontally by a sine offset (S01 — wave/flag effect).

    Each row is left-padded with spaces proportional to its sine offset.
    ANSI escape codes in the row content are preserved unchanged.

    When ``amplitude_map`` is provided it overrides ``amplitude`` on a per-row
    basis, enabling non-uniform warp driven by an external field (e.g. a plasma
    float grid).  The list should have one float per row; rows beyond the list
    length fall back to ``amplitude``.

    :param text: Multi-line rendered string from render().
    :param amplitude: Maximum horizontal shift in character columns (default: 3.0).
        Used for all rows when amplitude_map is None; used as fallback otherwise.
    :param frequency: Oscillation cycles across the full text height (default: 1.0).
    :param amplitude_map: Optional per-row amplitude overrides (list of floats,
        length must equal the number of rows in text).  Values outside [0, N] are
        clamped silently.  Default: None (uniform amplitude).
    :returns: Multi-line string with rows shifted by sine offsets.
    """
    if not text:
        return text

    lines = text.split("\n")
    n = len(lines)
    if n == 0:
        return text

    result = []
    for i, line in enumerate(lines):
        # Choose per-row amplitude: map entry if available, else global amplitude
        if amplitude_map is not None and i < len(amplitude_map):
            row_amp = float(amplitude_map[i])
        else:
            row_amp = amplitude
        # Normalise row index to 0.0–2π * frequency
        t = (i / max(n - 1, 1)) * 2.0 * math.pi * frequency
        offset = int(round(row_amp * math.sin(t)))
        # Positive offset → pad left; negative → pad right (keeps visual symmetry)
        if offset >= 0:
            result.append(" " * offset + line)
        else:
            result.append(line + " " * (-offset))

    return "\n".join(result)


# -------------------------------------------------------------------------
def perspective_tilt(text: str, strength: float = 0.3, direction: str = "top") -> str:
    """Scale row widths to simulate a vanishing-point perspective tilt (S02).

    Rows near the vanishing point are compressed; rows away from it are full width.
    Characters are sampled at evenly-spaced positions — not simply truncated —
    so the content remains readable at all compression levels.
    ANSI sequences are preserved: only visible characters are sampled.

    :param text: Multi-line rendered string from render().
    :param strength: Compression strength 0.0 (no effect) to 1.0 (max tilt, default: 0.3).
    :param direction: Which end narrows — "top" or "bottom" (default: "top").
    :returns: Multi-line string with per-row width scaling applied.
    :raises ValueError: If direction is not "top" or "bottom".
    """
    if direction not in ("top", "bottom"):
        raise ValueError(f"direction must be 'top' or 'bottom', got {direction!r}")

    if not text:
        return text

    lines = text.split("\n")
    n = len(lines)
    if n == 0:
        return text

    strength = max(0.0, min(1.0, strength))
    result = []

    for i, line in enumerate(lines):
        # t = 0.0 at the vanishing end, 1.0 at the full-width end
        t = i / max(n - 1, 1)
        if direction == "bottom":
            t = 1.0 - t

        # scale_factor: 1.0 at full end, (1 - strength) at vanishing end
        scale = (1.0 - strength) + strength * t

        visible = _strip_ansi(line)
        target_len = max(1, int(round(len(visible) * scale)))

        if target_len >= len(visible):
            result.append(line)
        else:
            # Sample characters at evenly-spaced positions
            sampled = _sample_chars(visible, target_len)
            # Re-pad to original width so columns stay aligned
            result.append(sampled.ljust(len(visible)))

    return "\n".join(result)


# -------------------------------------------------------------------------
def shear(text: str, amount: float = 0.5, direction: str = "right") -> str:
    """Apply a horizontal shear (italic/oblique) to each row (S08).

    Each row is offset by amount * row_index columns.
    Direction "right" shifts lower rows further right; "left" further left.

    :param text: Multi-line rendered string from render().
    :param amount: Horizontal shift per row in character columns (default: 0.5).
    :param direction: "right" (default) or "left".
    :returns: Multi-line string with per-row shear offsets applied.
    :raises ValueError: If direction is not "right" or "left".
    """
    if direction not in ("right", "left"):
        raise ValueError(f"direction must be 'right' or 'left', got {direction!r}")

    if not text:
        return text

    lines = text.split("\n")
    result = []

    for i, line in enumerate(lines):
        offset = int(round(amount * i))
        if direction == "right":
            result.append(" " * offset + line)
        else:
            # Left shear: later rows shift left → pad right instead
            result.append(line + " " * offset)

    return "\n".join(result)


# -------------------------------------------------------------------------
def _strip_ansi(text: str) -> str:
    """Return text with ANSI escape sequences removed.

    Used internally to measure visible character width.

    :param text: String potentially containing ANSI escape codes.
    :returns: String with all ANSI sequences stripped.
    """
    import re
    return re.sub(r"\033\[[0-9;]*m", "", text)


# -------------------------------------------------------------------------
def _sample_chars(text: str, target_len: int) -> str:
    """Sample target_len characters evenly from text.

    Picks characters at evenly-spaced indices so the sampled result
    represents the full span of the original rather than just a prefix.

    :param text: Source string (plain visible characters, no ANSI).
    :param target_len: Number of characters to sample.
    :returns: Sampled string of length target_len.
    """
    src_len = len(text)
    if target_len >= src_len:
        return text
    if target_len <= 0:
        return ""

    result = []
    for i in range(target_len):
        src_idx = int(round(i * (src_len - 1) / (target_len - 1))) if target_len > 1 else 0
        result.append(text[src_idx])
    return "".join(result)
