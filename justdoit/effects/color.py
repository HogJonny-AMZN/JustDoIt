"""
Package: justdoit.effects.color
ANSI terminal colorization for ASCII art output.

Provides flat color, bold color, and rainbow (per-character cycling) modes.
All ANSI codes target 256-color-compatible terminals.

Also provides C11 — fill-float → per-cell 24-bit color mapping:
  fill_float_colorize(text, float_grid, palette) → str
  Standard palettes: FIRE_PALETTE, LAVA_PALETTE, SPECTRAL_PALETTE, BIO_PALETTE
  PALETTE_REGISTRY: dict mapping palette names to palette lists

Also provides C12 — bloom / exterior glow via background color channel:
  bloom(text, bloom_color, radius, falloff, core_boost) → str
  BLOOM_COLORS: dict mapping preset names to (r, g, b) tuples
  Uses \033[48;2;r;g;bm (background ANSI) on surrounding space cells.
  BFS distance map from all ink cells; exponential falloff per cell.
"""

import logging as _logging
import re as _re

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.effects.color"
__updated__ = "2026-04-06 00:00:00"
__version__ = "0.2.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

COLORS: dict = {
    "red":     "\033[91m",
    "green":   "\033[92m",
    "yellow":  "\033[93m",
    "blue":    "\033[94m",
    "magenta": "\033[95m",
    "cyan":    "\033[96m",
    "white":   "\033[97m",
    "reset":   "\033[0m",
    "bold":    "\033[1m",
    "rainbow": None,  # special case — handled in colorize()
}

RAINBOW_CYCLE: list = [
    "\033[91m",  # red
    "\033[93m",  # yellow
    "\033[92m",  # green
    "\033[96m",  # cyan
    "\033[94m",  # blue
    "\033[95m",  # magenta
]

# -------------------------------------------------------------------------
# C11 — Standard palettes (float 0.0 → 1.0 maps to first → last entry)
# Each entry is an (r, g, b) tuple; linear interpolation between entries.

FIRE_PALETTE: list = [
    (20, 0, 0),       # 0.0 — near-black ember
    (120, 0, 0),      # 0.2 — dark red
    (200, 30, 0),     # 0.4 — orange-red
    (240, 120, 0),    # 0.6 — orange
    (255, 220, 40),   # 0.8 — yellow
    (255, 255, 200),  # 1.0 — white-hot
]

LAVA_PALETTE: list = [
    (10, 0, 20),      # 0.0 — deep violet
    (80, 0, 80),      # 0.2 — purple
    (180, 20, 0),     # 0.5 — deep orange
    (240, 100, 0),    # 0.7 — bright orange
    (255, 220, 80),   # 0.9 — yellow
    (255, 255, 200),  # 1.0 — white center
]

SPECTRAL_PALETTE: list = [
    (200, 0, 200),    # 0.0 — violet
    (0, 0, 255),      # 0.2 — blue
    (0, 200, 200),    # 0.4 — cyan
    (0, 200, 0),      # 0.6 — green
    (200, 200, 0),    # 0.8 — yellow
    (255, 50, 0),     # 1.0 — red
]

BIO_PALETTE: list = [
    (5, 30, 5),       # 0.0 — near-black bio-dark
    (20, 80, 20),     # 0.25 — dark green
    (60, 140, 60),    # 0.5 — mid green
    (120, 200, 80),   # 0.75 — light green
    (200, 240, 160),  # 1.0 — pale lime
]

ESCAPE_PALETTE: list = [
    (10, 0, 30),      # 0.0  — deep violet-black
    (30, 0, 100),     # 0.09 — deep purple
    (0, 20, 180),     # 0.18 — deep blue
    (0, 80, 240),     # 0.27 — bright blue
    (0, 160, 255),    # 0.36 — electric blue
    (0, 230, 220),    # 0.45 — cyan
    (60, 255, 120),   # 0.54 — bright green
    (200, 255, 50),   # 0.63 — yellow-green
    (255, 200, 0),    # 0.72 — golden yellow
    (255, 100, 0),    # 0.81 — orange
    (255, 30, 30),    # 0.90 — red
    (255, 220, 230),  # 1.0  — near-white pink
]

# C11 — AGE_PALETTE for X_LIVING_COLOR: temporal heat map.
# float=0.0 (just born/new alive) → cool blue; float=1.0 (long-lived/stable) → hot red.
# Reveals cellular age structure: transients glow blue, stable oscillators burn red.
AGE_PALETTE: list = [
    (0, 80, 220),     # 0.0  — newborn: deep blue
    (0, 180, 255),    # 0.2  — young: bright cyan-blue
    (0, 220, 160),    # 0.4  — adolescent: cyan-green
    (80, 220, 0),     # 0.6  — maturing: bright green
    (240, 180, 0),    # 0.8  — old: amber-orange
    (255, 40, 0),     # 1.0  — ancient/stable: hot red
]

PALETTE_REGISTRY: dict = {
    "fire":     FIRE_PALETTE,
    "lava":     LAVA_PALETTE,
    "spectral": SPECTRAL_PALETTE,
    "bio":      BIO_PALETTE,
    "escape":   ESCAPE_PALETTE,
    "age":      AGE_PALETTE,
}

# C12 — Named bloom colors for presets
# These are (r, g, b) tuples representing the bloom hue at distance=1.
# Attenuated exponentially per cell distance: intensity = falloff**distance.
BLOOM_COLORS: dict = {
    "cyan":    (0, 220, 255),
    "magenta": (255, 0, 200),
    "red":     (255, 60, 0),
    "orange":  (255, 100, 0),
    "yellow":  (255, 200, 0),
    "green":   (0, 220, 80),
    "blue":    (80, 120, 255),
    "white":   (255, 255, 255),
    "fire":    (255, 80, 0),
    "cold":    (100, 150, 255),
    "lava":    (255, 60, 0),
}

# -------------------------------------------------------------------------
# Internal helpers for C11 and C12
_ANSI_RE_COLOR = _re.compile(r"\033\[[0-9;]*m")
_RESET_C11 = "\033[0m"
_RESET_C12 = "\033[0m"


def _tc_c11(r: int, g: int, b: int) -> str:
    """Return a 24-bit true-color ANSI foreground code.

    :param r: Red channel 0–255.
    :param g: Green channel 0–255.
    :param b: Blue channel 0–255.
    :returns: ANSI escape string.
    """
    return f"\033[38;2;{r};{g};{b}m"


def _lerp_palette(palette: list, t: float) -> tuple:
    """Linearly interpolate through a palette of (r, g, b) stops.

    :param palette: List of (r, g, b) tuples from float=0.0 to float=1.0.
    :param t: Float in [0.0, 1.0].
    :returns: Interpolated (r, g, b) tuple.
    """
    n = len(palette)
    if n == 0:
        return (255, 255, 255)
    if n == 1:
        return palette[0]
    t = max(0.0, min(1.0, t))
    scaled = t * (n - 1)
    lo = int(scaled)
    hi = min(lo + 1, n - 1)
    frac = scaled - lo
    a, b_ = palette[lo], palette[hi]
    return (
        int(a[0] + (b_[0] - a[0]) * frac),
        int(a[1] + (b_[1] - a[1]) * frac),
        int(a[2] + (b_[2] - a[2]) * frac),
    )


# -------------------------------------------------------------------------
def colorize(text: str, color: str, rainbow_index: int = 0) -> str:
    """Wrap text in ANSI escape codes for the given color.

    For 'rainbow', cycles through RAINBOW_CYCLE using rainbow_index.
    For all other colors, applies bold + the named color code.
    Returns text unchanged if color is unrecognized.

    :param text: The string to colorize.
    :param color: Color name from COLORS, or 'rainbow'.
    :param rainbow_index: Character index used to select rainbow cycle position.
    :returns: ANSI-wrapped string.
    """
    if color == "rainbow":
        c = RAINBOW_CYCLE[rainbow_index % len(RAINBOW_CYCLE)]
        return f"{c}{text}{COLORS['reset']}"
    if color in COLORS and COLORS[color]:
        return f"{COLORS['bold']}{COLORS[color]}{text}{COLORS['reset']}"
    return text


# -------------------------------------------------------------------------
def fill_float_colorize(
    text: str,
    float_grid: list,
    palette: list,
) -> str:
    """Apply per-cell 24-bit color to a rendered ASCII art string (C11).

    Each visible (non-space) character cell is colored by looking up its
    float value in ``float_grid`` and interpolating through ``palette``.
    Space cells (exterior) are left uncolored. Existing ANSI sequences in
    ``text`` are stripped and replaced.

    :param text: Multi-line rendered string from render() — with or without
        existing ANSI codes. Rows separated by newlines.
    :param float_grid: 2D list of floats indexed as float_grid[row][col].
        Values should be in [0.0, 1.0]. Cells not present in the grid default
        to float value 0.0.
    :param palette: List of (r, g, b) tuples defining the color gradient from
        float=0.0 (index 0) to float=1.0 (last index). Use FIRE_PALETTE,
        LAVA_PALETTE, SPECTRAL_PALETTE, BIO_PALETTE, or a custom list.
    :returns: Multi-line string with 24-bit ANSI true-color applied per cell.
    """
    lines = text.split("\n")
    n_rows = len(lines)
    result = []

    for row_idx, line in enumerate(lines):
        # Strip existing ANSI codes to get clean character sequence
        clean = _ANSI_RE_COLOR.sub("", line)
        out = ""
        float_row = float_grid[row_idx] if row_idx < len(float_grid) else []
        for col_idx, ch in enumerate(clean):
            if ch == " ":
                out += ch
            else:
                # Look up float value; default to 0.0 if out of bounds
                fval = float_row[col_idx] if col_idx < len(float_row) else 0.0
                rgb = _lerp_palette(palette, fval)
                out += _tc_c11(*rgb) + ch + _RESET_C11
        result.append(out)

    return "\n".join(result)


# -------------------------------------------------------------------------
def bloom(
    text: str,
    bloom_color: tuple,
    radius: int = 4,
    falloff: float = 0.9,
    core_boost: bool = True,
) -> str:
    """Apply bloom glow to space cells surrounding ink cells (C12).

    For each space cell within ``radius`` chebyshev-distance steps of any
    ink cell, sets the terminal BACKGROUND color via ANSI
    ``\033[48;2;r;g;bm`` with intensity attenuated exponentially per cell
    distance::

        intensity = falloff ** distance   (distance 1-indexed)

    Space cells beyond radius, or with all-zero attenuated color, are left
    unchanged (plain ``" "``).  A ``\033[0m`` reset follows each bloom cell
    to prevent background bleed to the next character.

    Ink characters are preserved with their original foreground colors.
    If ``core_boost`` is True, ink cells adjacent to ≥1 space cell have
    their foreground RGB brightened by 1.15× (clamped to 255) for an
    inner-glow highlight. Only cells with a known 24-bit foreground color
    are boosted.

    This function uses the terminal BACKGROUND color channel
    (``\033[48;2;...m``), which is completely unused by all other JustDoIt
    effects. Space characters with a bright background appear as
    pure-color rectangles — the bloom medium.

    :param text: Multi-line rendered string (may contain existing ANSI
        foreground codes).
    :param bloom_color: ``(r, g, b)`` tuple for the bloom hue at distance=1.
        Use BLOOM_COLORS dict for named presets.
    :param radius: Max cells outward from ink to apply bloom (default 4).
    :param falloff: Per-cell intensity factor 0.0–1.0 (default 0.9;
        falloff**4 ≈ 0.66 at radius=4).
    :param core_boost: If True, edge ink cells adjacent to ≥1 space get
        foreground RGB brightened 1.15× (inner glow). Only 24-bit fg
        colors are boosted (default True).
    :returns: Multi-line string with background ANSI codes on bloom cells.
    """
    from collections import deque as _deque
    from justdoit.output.ansi_parser import (
        parse as _ansi_parse,
    )

    if not text:
        return text

    # --- Parse into 2D grid of (char, Optional[fg_color]) ---
    tokens = _ansi_parse(text)
    rows_2d: list = [[]]
    for ch, color in tokens:
        if ch == "\n":
            rows_2d.append([])
        else:
            rows_2d[-1].append((ch, color))

    n_rows = len(rows_2d)
    if n_rows == 0:
        return text
    n_cols = max((len(row) for row in rows_2d), default=0)
    if n_cols == 0:
        return text

    # Normalize all rows to the same width
    for row in rows_2d:
        while len(row) < n_cols:
            row.append((" ", None))

    # --- Build ink mask ---
    ink_mask = [
        [rows_2d[ri][ci][0] != " " for ci in range(n_cols)]
        for ri in range(n_rows)
    ]

    # Check if there are any ink cells at all
    has_ink = any(ink_mask[ri][ci] for ri in range(n_rows) for ci in range(n_cols))
    if not has_ink or radius <= 0:
        # No bloom possible — return original text (re-assembled clean)
        result_lines = []
        for ri in range(n_rows):
            line_out = ""
            for ci in range(n_cols):
                ch, fg_color = rows_2d[ri][ci]
                if ch != " " and fg_color is not None:
                    fr, fg, fb = fg_color
                    line_out += f"\033[38;2;{fr};{fg};{fb}m{ch}\033[0m"
                else:
                    line_out += ch
            result_lines.append(line_out.rstrip())
        return "\n".join(result_lines)

    # --- BFS distance map (Chebyshev 8-direction from all ink simultaneously) ---
    INF = radius + 1
    dist_map = [[INF] * n_cols for _ in range(n_rows)]
    q: _deque = _deque()
    for ri in range(n_rows):
        for ci in range(n_cols):
            if ink_mask[ri][ci]:
                dist_map[ri][ci] = 0
                q.append((ri, ci))

    while q:
        ri, ci = q.popleft()
        cur_d = dist_map[ri][ci]
        if cur_d >= radius:
            continue  # do not expand beyond bloom radius
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = ri + dr, ci + dc
                if 0 <= nr < n_rows and 0 <= nc < n_cols:
                    nd = cur_d + 1
                    if nd < dist_map[nr][nc]:
                        dist_map[nr][nc] = nd
                        q.append((nr, nc))

    bloom_r, bloom_g, bloom_b = bloom_color

    # --- Identify edge ink cells (adjacent to ≥1 space, 4-cardinal) ---
    edge_ink: set = set()
    if core_boost:
        for ri in range(n_rows):
            for ci in range(n_cols):
                if ink_mask[ri][ci]:
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = ri + dr, ci + dc
                        if 0 <= nr < n_rows and 0 <= nc < n_cols:
                            if not ink_mask[nr][nc]:
                                edge_ink.add((ri, ci))
                                break

    # --- Reconstruct output ---
    result_lines = []
    for ri in range(n_rows):
        line_out = ""
        for ci in range(n_cols):
            ch, fg_color = rows_2d[ri][ci]
            if ch == " ":
                d = dist_map[ri][ci]
                if d <= radius:
                    intensity = falloff ** d
                    cr = int(bloom_r * intensity)
                    cg = int(bloom_g * intensity)
                    cb = int(bloom_b * intensity)
                    if cr > 0 or cg > 0 or cb > 0:
                        line_out += f"\033[48;2;{cr};{cg};{cb}m \033[0m"
                    else:
                        line_out += " "
                else:
                    line_out += " "
            else:
                # Ink cell — preserve fg color, optionally boost edge cells
                if core_boost and (ri, ci) in edge_ink and fg_color is not None:
                    fr, fg, fb = fg_color
                    fr = min(255, int(fr * 1.15))
                    fg = min(255, int(fg * 1.15))
                    fb = min(255, int(fb * 1.15))
                    line_out += f"\033[38;2;{fr};{fg};{fb}m{ch}\033[0m"
                elif fg_color is not None:
                    fr, fg, fb = fg_color
                    line_out += f"\033[38;2;{fr};{fg};{fb}m{ch}\033[0m"
                else:
                    line_out += ch
        result_lines.append(line_out)

    return "\n".join(result_lines)


# -------------------------------------------------------------------------
C13_CURVES = ("linear", "reinhard", "aces", "blown_out")


def apply_tone_curve(float_grid: list, curve: str = "linear") -> list:
    """Apply a named tone curve to a fill float grid (C13).

    Transforms a 2D float grid through a named tone mapping curve before char
    density selection. Most visually impactful on high-DR fills (flame, plasma).

    Curves:

    - ``linear``:     identity; current default behavior
    - ``reinhard``:   ``t / (1 + t)`` — soft rolloff, shadow detail preserved
    - ``aces``:       Stephen Hill polynomial approximation — punchy mids,
                      cinematic highlights (industry standard filmic curve)
    - ``blown_out``:  values >= threshold → 1.0; below threshold scale linearly
                      to 0–1. Default threshold 0.7. Pass "blown_out:0.5" to
                      override threshold.

    :param float_grid: 2D list[list[float]] from any fill function.
    :param curve: Tone curve name (default "linear"). "blown_out" accepts optional
        threshold suffix: "blown_out:0.7" (default threshold=0.7).
    :returns: New 2D float grid with same shape, values remapped to [0.0, 1.0].
    :raises ValueError: If curve name is unrecognized.
    """
    threshold = 0.7
    curve_name = curve
    if ":" in curve:
        parts = curve.split(":", 1)
        curve_name = parts[0]
        try:
            threshold = float(parts[1])
            threshold = max(0.001, min(1.0, threshold))
        except ValueError:
            threshold = 0.7

    known = ("linear", "reinhard", "aces", "blown_out")
    if curve_name not in known:
        raise ValueError(
            f"Unknown tone curve '{curve_name}'. Available: {', '.join(known)}"
        )

    def _apply(t: float) -> float:
        t = max(0.0, min(1.0, t))
        if curve_name == "linear":
            return t
        elif curve_name == "reinhard":
            return t / (1.0 + t)
        elif curve_name == "aces":
            a, b_, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
            out = (t * (a * t + b_)) / (t * (c * t + d) + e)
            return max(0.0, min(1.0, out))
        else:  # blown_out
            if t >= threshold:
                return 1.0
            return t / threshold

    return [[_apply(v) for v in row] for row in float_grid]
