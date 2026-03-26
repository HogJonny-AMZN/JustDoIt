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
  F04 — reaction_diffusion_fill: Gray-Scott reaction-diffusion model. Upscales the
                       glyph mask by `scale` (default 4) so that patterns have room
                       to develop, runs the simulation, then downsamples V back.
                       Named presets (coral, spots, maze, worms, zebra) from
                       Pearson 1993. Final V concentration drives char density.
  F10 — truchet_fill:  Truchet tile tiling inside glyph mask. Each ink cell gets
                       one of two tile orientations (diagonal ╱╲, arc ╰╮, or
                       wave-biased diagonals), creating labyrinth / flow patterns.
                       Inspired by Sébastien Truchet (1704) and the "10 PRINT" demoscene.
  N10 — slime_mold_fill: Physarum polycephalum (slime mold) agent-based simulation.
                       Agents move by chemotaxis — they deposit trail and sense
                       chemical concentration in front, rotating toward the strongest
                       gradient. The resulting trail map creates organic vein-like
                       networks inside the glyph mask.

All are pure Python stdlib — no external dependencies.
"""

import logging as _logging
import math
import random
from typing import Optional

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.effects.generative"
__updated__ = "2026-03-24 00:00:00"
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


# -------------------------------------------------------------------------
# Reaction-Diffusion (Gray-Scott) fill
#
# Named presets from Pearson (1993): "Complex Patterns in a Simple System"
# Science 261, 189–192.  Parameter values are (f, k) pairs.
#
# Equations (continuous form):
#   dU/dt = Du * lap(U) - U*V^2 + f*(1-U)
#   dV/dt = Dv * lap(V) + U*V^2 - (f+k)*V
#
# Discretised with dt=1.0 and 5-point Laplacian.
# Boundary condition: Neumann — cells outside mask treated as equal to
# the cell itself (zero-flux), so the reaction stays inside the glyph.

_RD_PRESETS: dict = {
    "coral":  {"f": 0.055, "k": 0.062},   # coral branching, medium-density patterns
    "spots":  {"f": 0.035, "k": 0.060},   # isolated spots / disconnected blobs
    "maze":   {"f": 0.060, "k": 0.062},   # stripe labyrinth patterns
    "worms":  {"f": 0.050, "k": 0.065},   # sparse filament-like structures
    "zebra":  {"f": 0.037, "k": 0.060},   # alternating stripe / zebra effect
}

_RD_Du: float = 0.16
_RD_Dv: float = 0.08
_RD_dt: float = 1.0


# -------------------------------------------------------------------------
def reaction_diffusion_fill(
    mask: list,
    preset: str = "coral",
    steps: int = 2000,
    seed: Optional[int] = None,
    density_chars: Optional[str] = None,
    scale: int = 4,
) -> list:
    """Fill glyph mask using Gray-Scott reaction-diffusion simulation (F04).

    Upscales the glyph ink mask by *scale* (default 4×) so the simulation has
    enough spatial resolution to develop patterns, then downsamples the final
    V concentration back to the original cell grid and maps to characters.

    Gray-Scott RD model equations:
      dU/dt = Du · ∇²U - U·V² + f·(1-U)
      dV/dt = Dv · ∇²V + U·V² - (f+k)·V

    The V (activator) concentration after *steps* iterations drives char density:
    high V → dense chars, low V → light/dot chars.
    Cells outside the mask remain spaces.

    Named presets (inspired by Pearson 1993) control the (f, k) parameters:
      "coral" — f=0.055, k=0.062  (coral branching, medium-density patterns)
      "spots" — f=0.035, k=0.060  (isolated spots / disconnected blobs)
      "maze"  — f=0.060, k=0.062  (stripe labyrinth patterns)
      "worms" — f=0.050, k=0.065  (sparse filament-like structures)
      "zebra" — f=0.037, k=0.060  (alternating stripe / zebra effect)

    :param mask: 2D list of floats from glyph_to_mask() — values 0.0–1.0.
    :param preset: Named parameter preset (default: 'coral').
    :param steps: Number of simulation steps (default: 2000).
    :param seed: Optional integer seed for V initialisation reproducibility.
    :param density_chars: Darkest-to-lightest char sequence (default: _DENSE).
    :param scale: Upscale factor before simulation (default: 4). Higher = finer patterns.
    :returns: List of strings — one per row, same shape as input mask.
    :raises ValueError: If preset name is unknown.
    """
    if preset not in _RD_PRESETS:
        raise ValueError(
            f"Unknown RD preset '{preset}'. "
            f"Available: {', '.join(_RD_PRESETS.keys())}"
        )

    orig_rows = len(mask)
    if orig_rows == 0:
        return []
    orig_cols = max(len(row) for row in mask)

    params = _RD_PRESETS[preset]
    f = params["f"]
    k = params["k"]
    chars = (density_chars or _DENSE).rstrip(" ") or "."
    n_chars = len(chars)

    # -------------------------------------------------------------------------
    # Build original ink mask (bool grid, orig_rows × orig_cols)
    orig_ink = [
        [mask[r][c] >= 0.5 if c < len(mask[r]) else False for c in range(orig_cols)]
        for r in range(orig_rows)
    ]

    # -------------------------------------------------------------------------
    # Upscale ink mask by nearest-neighbour — each orig cell → scale×scale block
    sim_rows = orig_rows * scale
    sim_cols = orig_cols * scale
    ink = [
        [orig_ink[r // scale][c // scale] for c in range(sim_cols)]
        for r in range(sim_rows)
    ]

    # -------------------------------------------------------------------------
    # Initialise U=1, V=0 for ink cells
    U = [[1.0 if ink[r][c] else 0.0 for c in range(sim_cols)] for r in range(sim_rows)]
    V = [[0.0] * sim_cols for _ in range(sim_rows)]

    # Seed small patches of V=1.0 / U=0.5 scattered inside the ink region.
    # Small-patch seeding (rather than random flooding) is essential for Gray-Scott —
    # a global flood of V kills the pattern before it can establish.
    rng = random.Random(seed)
    ink_cells = [(r, c) for r in range(sim_rows) for c in range(sim_cols) if ink[r][c]]
    n_seeds = max(3, len(ink_cells) // 20)   # ~5% of ink area, minimum 3 seeds
    seed_radius = max(1, scale // 2)
    for _ in range(n_seeds):
        if not ink_cells:
            break
        cr, cc = rng.choice(ink_cells)
        for dr in range(-seed_radius, seed_radius + 1):
            for dc in range(-seed_radius, seed_radius + 1):
                sr, sc = cr + dr, cc + dc
                if 0 <= sr < sim_rows and 0 <= sc < sim_cols and ink[sr][sc]:
                    V[sr][sc] = 1.0
                    U[sr][sc] = 0.5

    # -------------------------------------------------------------------------
    def _laplacian(grid: list, r: int, c: int) -> float:
        """5-point Laplacian with Neumann BC (zero-flux at mask boundary).

        :param grid: 2D float grid (sim_rows × sim_cols).
        :param r: Row index.
        :param c: Column index.
        :returns: Laplacian value at (r, c).
        """
        center = grid[r][c]
        total = 0.0
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < sim_rows and 0 <= nc < sim_cols and ink[nr][nc]:
                total += grid[nr][nc]
            else:
                # Neumann: ghost cell = self → zero flux
                total += center
        return total - 4.0 * center

    # -------------------------------------------------------------------------
    # Time integration on the upscaled grid
    for _ in range(steps):
        lapU = [[0.0] * sim_cols for _ in range(sim_rows)]
        lapV = [[0.0] * sim_cols for _ in range(sim_rows)]
        for r in range(sim_rows):
            for c in range(sim_cols):
                if ink[r][c]:
                    lapU[r][c] = _laplacian(U, r, c)
                    lapV[r][c] = _laplacian(V, r, c)

        newU = [row[:] for row in U]
        newV = [row[:] for row in V]
        for r in range(sim_rows):
            for c in range(sim_cols):
                if not ink[r][c]:
                    continue
                u = U[r][c]
                v = V[r][c]
                uvv = u * v * v
                newU[r][c] = max(0.0, min(1.0,
                    u + _RD_dt * (_RD_Du * lapU[r][c] - uvv + f * (1.0 - u))))
                newV[r][c] = max(0.0, min(1.0,
                    v + _RD_dt * (_RD_Dv * lapV[r][c] + uvv - (f + k) * v)))
        U = newU
        V = newV

    # -------------------------------------------------------------------------
    # Downsample: for each original ink cell, average V over its scale×scale block
    # Build downsampled V grid (orig_rows × orig_cols)
    down_V = []
    for r in range(orig_rows):
        row_v = []
        for c in range(orig_cols):
            if not orig_ink[r][c]:
                row_v.append(0.0)
                continue
            total_v = 0.0
            count = 0
            for dr in range(scale):
                for dc in range(scale):
                    sr, sc = r * scale + dr, c * scale + dc
                    if ink[sr][sc]:
                        total_v += V[sr][sc]
                        count += 1
            row_v.append(total_v / count if count > 0 else 0.0)
        down_V.append(row_v)

    # -------------------------------------------------------------------------
    # Downsample U as well — needed as fallback when V dies
    down_U = []
    for r in range(orig_rows):
        row_u = []
        for c in range(orig_cols):
            if not orig_ink[r][c]:
                row_u.append(1.0)
                continue
            total_u = 0.0
            count = 0
            for dr in range(scale):
                for dc in range(scale):
                    sr, sc = r * scale + dr, c * scale + dc
                    if ink[sr][sc]:
                        total_u += U[sr][sc]
                        count += 1
            row_u.append(total_u / count if count > 0 else 1.0)
        down_U.append(row_u)

    # -------------------------------------------------------------------------
    # Choose signal: prefer V when it has variation; fall back to inverted U
    v_vals = [down_V[r][c] for r in range(orig_rows) for c in range(orig_cols)
              if orig_ink[r][c]]
    if not v_vals:
        return ["" for _ in range(orig_rows)]

    v_span = max(v_vals) - min(v_vals)

    if v_span < 1e-4:
        # V is flat (patterns died) — use U-derived gradient instead.
        # U is depleted where V was active, so inverted U gives the same pattern.
        u_vals = [down_U[r][c] for r in range(orig_rows) for c in range(orig_cols)
                  if orig_ink[r][c]]
        min_u = min(u_vals)
        max_u = max(u_vals)
        u_span = max_u - min_u
        if u_span < 1e-4:
            # Both flat — use Perlin-based deterministic fallback
            perm = _build_perm(seed)
            result = []
            for r in range(orig_rows):
                line = ""
                for c in range(orig_cols):
                    if not orig_ink[r][c]:
                        line += " "
                    else:
                        raw = _perlin2d(c * 0.5, r * 0.5, perm)
                        t = max(0.0, min(1.0, (raw + 1.0) / 2.0))
                        idx = int(t * (n_chars - 1) + 0.5)
                        line += chars[n_chars - 1 - idx]
                result.append(line)
            return result

        # Map U: high U (uninhibited) → light; low U → dense
        result = []
        for r in range(orig_rows):
            line = ""
            for c in range(orig_cols):
                if not orig_ink[r][c]:
                    line += " "
                else:
                    t = (down_U[r][c] - min_u) / u_span
                    t = max(0.0, min(1.0, t))
                    # Low U means V was active → dense; high U → light
                    idx = int(t * (n_chars - 1) + 0.5)
                    line += chars[idx]   # high U → chars[-1] (light), low U → chars[0]
            result.append(line)
        return result

    # V has variation — normalise and map directly
    min_v = min(v_vals)
    result = []
    for r in range(orig_rows):
        line = ""
        for c in range(orig_cols):
            if not orig_ink[r][c]:
                line += " "
            else:
                t = (down_V[r][c] - min_v) / v_span   # 0.0..1.0
                t = max(0.0, min(1.0, t))
                idx = int(t * (n_chars - 1) + 0.5)
                idx = max(0, min(n_chars - 1, idx))
                line += chars[n_chars - 1 - idx]       # high V → chars[0] (dense)
        result.append(line)

    return result


# -------------------------------------------------------------------------
# Slime Mold Simulation (Physarum polycephalum) fill — N10
#
# Inspired by Jeff Jones (2010) "Characteristics of Pattern Formation and
# Evolution in Approximations of Physarum Transport Networks"
# Int. Journal of Unconventional Computing.
#
# Algorithm overview:
#   1. Spawn N agents scattered inside the glyph ink mask.
#   2. Each agent has a position (continuous float) and a heading angle.
#   3. Per step — sense phase: sample trail at three sensor points
#      (forward-left, forward, forward-right), rotate toward the strongest.
#   4. Motor phase: move forward one step. If the target cell is outside
#      the mask boundary, pick a new random heading and try again.
#   5. Deposit phase: add DEPOSIT amount to the trail grid at current pos.
#   6. Diffuse phase: 3×3 box-blur the trail grid (inside-mask cells only).
#   7. Decay phase: multiply all trail values by (1 - DECAY).
#
# After all steps the trail grid is normalised and mapped to chars.
# Dense trail (heavily-used vein) → dense chars; sparse trail → light chars.
#
# The mask boundary acts as a natural containment — agents bounce off
# the edge, so the network always stays inside the glyph shape.

_SLIME_DENSE: str = "@#S%?*+;:,. "


# -------------------------------------------------------------------------
def slime_mold_fill(
    mask: list,
    n_agents: int = 200,
    steps: int = 150,
    sensor_angle: float = 0.523599,   # 30° in radians
    sensor_dist: float = 2.5,
    turn_speed: float = 0.523599,     # 30° in radians
    deposit: float = 1.0,
    decay: float = 0.05,
    density_chars: Optional[str] = None,
    seed: Optional[int] = None,
) -> list:
    """Fill glyph mask with a Physarum polycephalum (slime mold) simulation (N10).

    Agents perform chemotaxis — they deposit a chemical trail and navigate
    toward the strongest gradient sensed ahead of them. After simulation,
    the accumulated trail map (normalised) is used to drive character density.
    Heavily-traversed veins appear as dense chars; sparse regions are lighter.

    The simulation is confined inside the glyph mask — agents that reach
    the mask boundary pick a new random heading, so the network never
    leaves the letter form.

    Parameters control:
      n_agents     — population size. More agents → denser/faster coverage.
      steps        — simulation iterations. More steps → more elaborate networks.
      sensor_angle — half-angle between forward and side sensors (radians, default 30°).
      sensor_dist  — distance ahead to sample trail (cells, default 2.5).
      turn_speed   — max rotation per step toward best sensor (radians, default 30°).
      deposit      — trail deposit per step per agent (default 1.0).
      decay        — trail decay rate per step, 0.0–1.0 (default 0.05).

    :param mask: 2D list of floats from glyph_to_mask() — values 0.0–1.0.
    :param n_agents: Number of Physarum agents (default: 200).
    :param steps: Simulation iterations (default: 150).
    :param sensor_angle: Half-angle between forward and side sensors in radians.
    :param sensor_dist: Look-ahead distance in cells.
    :param turn_speed: Max rotation toward strongest sensor per step (radians).
    :param deposit: Trail chemical deposited per agent per step.
    :param decay: Fractional trail evaporation per step (0 = no decay, 1 = instant).
    :param density_chars: Darkest-to-lightest char sequence.
    :param seed: Optional integer seed for reproducibility.
    :returns: List of strings — one per row, same shape as input mask.
    """
    rows = len(mask)
    if rows == 0:
        return []
    cols = max(len(row) for row in mask)
    if cols == 0:
        return []

    chars = density_chars if density_chars is not None else _SLIME_DENSE
    n_chars = len(chars)
    rng = random.Random(seed)
    TWO_PI = 2.0 * math.pi

    # -------------------------------------------------------------------------
    # Build ink mask (bool grid)
    ink = [
        [mask[r][c] >= 0.5 if c < len(mask[r]) else False for c in range(cols)]
        for r in range(rows)
    ]

    # Collect all ink cells as candidate spawn/sensor positions
    ink_cells = [(r, c) for r in range(rows) for c in range(cols) if ink[r][c]]
    if not ink_cells:
        return [" " * cols for _ in range(rows)]

    # -------------------------------------------------------------------------
    # Trail grid — float, same size as mask; only updated inside ink cells
    trail = [[0.0] * cols for _ in range(rows)]

    # -------------------------------------------------------------------------
    # Agent state: list of [py (float), px (float), angle (float)]
    # py/px are continuous floats; clamped to ink cells on each step.
    # Use all ink cells if n_agents > population, else sample.
    sample_size = min(n_agents, len(ink_cells))
    spawn_cells = rng.sample(ink_cells, sample_size)
    # Pad if n_agents > available cells by repeating random choices
    while len(spawn_cells) < n_agents:
        spawn_cells.append(rng.choice(ink_cells))

    agents = []
    for (ar, ac) in spawn_cells:
        angle = rng.uniform(0.0, TWO_PI)
        agents.append([float(ar) + rng.uniform(-0.4, 0.4),
                       float(ac) + rng.uniform(-0.4, 0.4),
                       angle])

    # -------------------------------------------------------------------------
    def _sense(py: float, px: float, angle: float) -> float:
        """Sample trail at a sensor point ahead of (py, px) at given angle.

        Returns 0.0 if the sensor point is outside the ink mask.

        :param py: Agent row (float).
        :param px: Agent column (float).
        :param angle: Sensor direction angle (radians).
        :returns: Trail value at sensor point, or 0.0 if outside mask.
        """
        sr = int(round(py + sensor_dist * math.sin(angle)))
        sc = int(round(px + sensor_dist * math.cos(angle)))
        if 0 <= sr < rows and 0 <= sc < cols and ink[sr][sc]:
            return trail[sr][sc]
        return 0.0

    # -------------------------------------------------------------------------
    def _diffuse() -> None:
        """In-place 3×3 box-blur of trail, restricted to ink cells.

        Each ink cell's new value is the average of itself and its ink neighbours
        (including diagonals). Outside cells contribute 0 to the average, so
        the blur never pulls trail past the mask boundary.
        """
        new_trail = [row[:] for row in trail]
        for r in range(rows):
            for c in range(cols):
                if not ink[r][c]:
                    continue
                total = 0.0
                count = 0
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < rows and 0 <= nc < cols and ink[nr][nc]:
                            total += trail[nr][nc]
                            count += 1
                new_trail[r][c] = total / count if count > 0 else 0.0
        for r in range(rows):
            for c in range(cols):
                trail[r][c] = new_trail[r][c]

    # -------------------------------------------------------------------------
    # Main simulation loop
    for _step in range(steps):
        # --- Sense & rotate ---
        for agent in agents:
            py, px, angle = agent
            f  = _sense(py, px, angle)                   # forward
            fl = _sense(py, px, angle - sensor_angle)    # forward-left
            fr = _sense(py, px, angle + sensor_angle)    # forward-right

            if f >= fl and f >= fr:
                # Forward is best — keep heading
                pass
            elif fl > fr:
                agent[2] = (angle - turn_speed) % TWO_PI
            elif fr > fl:
                agent[2] = (angle + turn_speed) % TWO_PI
            else:
                # Equal — random turn
                agent[2] = (angle + (turn_speed if rng.random() < 0.5
                                     else -turn_speed)) % TWO_PI

        # --- Move & deposit ---
        for agent in agents:
            py, px, angle = agent
            ny = py + math.sin(angle)
            nx = px + math.cos(angle)
            nr = int(round(ny))
            nc = int(round(nx))

            if 0 <= nr < rows and 0 <= nc < cols and ink[nr][nc]:
                agent[0] = ny
                agent[1] = nx
            else:
                # Hit boundary — pick a new random heading and stay put
                agent[2] = rng.uniform(0.0, TWO_PI)
                nr, nc = int(round(py)), int(round(px))

            # Deposit at clamped grid cell
            dr = max(0, min(rows - 1, nr))
            dc = max(0, min(cols - 1, nc))
            if ink[dr][dc]:
                trail[dr][dc] += deposit

        # --- Diffuse ---
        _diffuse()

        # --- Decay ---
        decay_factor = 1.0 - decay
        for r in range(rows):
            for c in range(cols):
                trail[r][c] *= decay_factor

    # -------------------------------------------------------------------------
    # Normalise trail and map to chars
    trail_vals = [trail[r][c] for r in range(rows) for c in range(cols)
                  if ink[r][c]]
    if not trail_vals:
        return [" " * cols for _ in range(rows)]

    min_t = min(trail_vals)
    max_t = max(trail_vals)
    span = max_t - min_t

    result = []
    for r in range(rows):
        line = ""
        for c in range(cols):
            if not ink[r][c]:
                line += " "
                continue
            if span < 1e-9:
                line += chars[n_chars // 2]
                continue
            t = (trail[r][c] - min_t) / span    # 0.0..1.0
            t = max(0.0, min(1.0, t))
            idx = int(t * (n_chars - 1) + 0.5)
            idx = max(0, min(n_chars - 1, idx))
            line += chars[n_chars - 1 - idx]    # high trail → chars[0] (dense)
        result.append(line)

    return result
