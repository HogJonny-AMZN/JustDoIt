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
  N06 — lsystem_fill:  Lindenmayer system (L-system) branching grown inside
                       the glyph mask. A turtle-graphics renderer traces the
                       L-system string, depositing density onto a grid. The
                       accumulated branch density drives character selection —
                       branch intersections and trunk regions → dense chars,
                       leaf tips → light chars. Named presets cover classic
                       botanical L-systems: plant, fern, sierpinski, dragon,
                       bush, algae (fractal branching). The fractal self-similarity
                       produces letterforms that look like they grew there.
                       one of two tile orientations (diagonal ╱╲, arc ╰╮, or
                       wave-biased diagonals), creating labyrinth / flow patterns.
                       Inspired by Sébastien Truchet (1704) and the "10 PRINT" demoscene.
  N08 — strange_attractor_fill: Chaotic strange attractor projected into glyph mask.
                       Integrates a continuous ODE (Lorenz, Rössler) or iterates a
                       discrete map (De Jong, Clifford) for many steps, then builds
                       a 2D density histogram of the trajectory. Each glyph ink cell
                       samples the density at its proportional position in the
                       attractor's bounding box — dense trajectory regions → heavy
                       chars, sparse regions → light chars. The result is a
                       calligraphically beautiful fill that encodes chaotic geometry
                       inside each letterform.
  N09 — turing_fill:   Turing activator-inhibitor reaction-diffusion model (1952).
                       Uses a FitzHugh-Nagumo-style activator/inhibitor system
                       distinct from Gray-Scott — short-range activation, long-range
                       inhibition. A single `epsilon` parameter transitions patterns
                       from isolated spots (biological leopard spots) through zebra
                       stripes to labyrinthine mazes. Named presets: spots, stripes,
                       maze, labyrinth. Based on Turing (1952) "The Chemical Basis
                       of Morphogenesis", Philos. Trans. R. Soc. Lond. B 237:37–72.
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


# -------------------------------------------------------------------------
# Wave Interference fill — F09
#
# Two plane waves at different angles and frequencies interfere inside the
# glyph mask. The superposition I(x,y) is normalized to [0,1] and mapped
# to density chars.
#

_WAVE_PRESETS: dict = {
    "default": {"freq1": 3.0,  "angle1":   0.0, "freq2": 5.0, "angle2":  45.0},
    "moire":   {"freq1": 8.0,  "angle1":   0.0, "freq2": 8.0, "angle2":   5.0},
    "radial":  {"freq1": 4.0,  "angle1":  30.0, "freq2": 4.0, "angle2": -30.0},
    "fine":    {"freq1": 10.0, "angle1":  22.5, "freq2": 7.0, "angle2":  67.5},
}


# -------------------------------------------------------------------------
def wave_fill(
    mask: list,
    freq1: float = 3.0,
    angle1: float = 0.0,
    freq2: float = 5.0,
    angle2: float = 45.0,
    phase1: float = 0.0,
    phase2: float = 0.0,
    preset: str = "default",
    density_chars: Optional[str] = None,
) -> list:
    """Fill glyph mask with two-wave interference pattern (F09).

    Two plane waves at different angles and frequencies interfere inside the
    glyph ink cells. The interference intensity:

      I(x,y) = cos(2π*(fx1*x + fy1*y) + phase1) + cos(2π*(fx2*x + fy2*y) + phase2)

    where fx = freq*cos(angle_rad), fy = freq*sin(angle_rad), and x,y are
    normalised to [0, 1] within the bounding box of ink cells.  I ranges
    from -2 to +2; it is normalised to [0, 1] before char mapping.

    Named presets (override individual params when specified):
      "default" — freq1=3,  angle1=0,    freq2=5,  angle2=45   (gentle diagonal cross)
      "moire"   — freq1=8,  angle1=0,    freq2=8,  angle2=5    (near-parallel moiré bands)
      "radial"  — freq1=4,  angle1=30,   freq2=4,  angle2=-30  (symmetric bowtie)
      "fine"    — freq1=10, angle1=22.5, freq2=7,  angle2=67.5 (fine diagonal interference)

    :param mask: 2D list of floats from glyph_to_mask() — values 0.0–1.0.
    :param freq1: Spatial frequency of wave 1 (cycles across the glyph, default: 3.0).
    :param angle1: Propagation angle of wave 1 in degrees (default: 0.0).
    :param freq2: Spatial frequency of wave 2 (default: 5.0).
    :param angle2: Propagation angle of wave 2 in degrees (default: 45.0).
    :param phase1: Phase offset of wave 1 in radians (default: 0.0).
    :param phase2: Phase offset of wave 2 in radians (default: 0.0).
    :param preset: Named parameter preset; overrides all wave params when set (default: 'default').
    :param density_chars: Darkest-to-lightest character sequence (default: _DENSE).
    :returns: List of strings — one per row, same shape as input mask.
    :raises ValueError: If preset name is unknown.
    """
    if preset not in _WAVE_PRESETS:
        raise ValueError(
            f"Unknown wave preset '{preset}'. "
            f"Available: {', '.join(_WAVE_PRESETS.keys())}"
        )

    rows = len(mask)
    if rows == 0:
        return []
    cols = max(len(row) for row in mask)
    if cols == 0:
        return []

    # Apply preset — overrides individual params
    p = _WAVE_PRESETS[preset]
    freq1  = p["freq1"]
    angle1 = p["angle1"]
    freq2  = p["freq2"]
    angle2 = p["angle2"]

    chars = density_chars if density_chars is not None else _DENSE
    n_chars = len(chars)

    # -------------------------------------------------------------------------
    # Identify ink cells and build bounding box for normalised coordinates
    ink_cells = [
        (r, c)
        for r in range(rows)
        for c in range(len(mask[r]))
        if mask[r][c] >= 0.5
    ]
    if not ink_cells:
        return [" " * cols for _ in range(rows)]

    min_r = min(r for r, _ in ink_cells)
    max_r = max(r for r, _ in ink_cells)
    min_c = min(c for _, c in ink_cells)
    max_c = max(c for _, c in ink_cells)

    row_span = max(max_r - min_r, 1)
    col_span = max(max_c - min_c, 1)

    # -------------------------------------------------------------------------
    # Pre-compute wave direction components
    TWO_PI = 2.0 * math.pi
    a1_rad = math.radians(angle1)
    a2_rad = math.radians(angle2)
    fx1 = freq1 * math.cos(a1_rad)
    fy1 = freq1 * math.sin(a1_rad)
    fx2 = freq2 * math.cos(a2_rad)
    fy2 = freq2 * math.sin(a2_rad)

    # -------------------------------------------------------------------------
    # Evaluate interference value for every ink cell, track min/max for normalisation
    wave_grid = [[0.0] * cols for _ in range(rows)]
    ink_mask  = [
        [mask[r][c] >= 0.5 if c < len(mask[r]) else False for c in range(cols)]
        for r in range(rows)
    ]

    ink_vals: list = []
    for r, c in ink_cells:
        x = (c - min_c) / col_span   # 0.0–1.0
        y = (r - min_r) / row_span   # 0.0–1.0
        val = (
            math.cos(TWO_PI * (fx1 * x + fy1 * y) + phase1)
            + math.cos(TWO_PI * (fx2 * x + fy2 * y) + phase2)
        )
        wave_grid[r][c] = val
        ink_vals.append(val)

    # -------------------------------------------------------------------------
    # Normalise from [-2, +2] → [0, 1] and map to chars
    w_min = min(ink_vals)
    w_max = max(ink_vals)
    w_span = w_max - w_min
    if w_span < 1e-9:
        w_span = 1.0

    result = []
    for r in range(rows):
        line = ""
        for c in range(cols):
            if not ink_mask[r][c]:
                line += " "
                continue
            norm = (wave_grid[r][c] - w_min) / w_span   # 0.0–1.0
            norm = max(0.0, min(1.0, norm))
            idx = int(norm * (n_chars - 1) + 0.5)
            idx = max(0, min(n_chars - 1, idx))
            line += chars[n_chars - 1 - idx]   # high intensity → chars[0] (dense)
        result.append(line)

    return result


# -------------------------------------------------------------------------
# Fractal Fill — F05
#
# Mandelbrot or Julia set escape-time algorithm.  Each ink cell is mapped to
# a complex coordinate; the escape iteration count (with smooth colouring)
# drives character density.
#

_FRACTAL_PRESETS: dict = {
    "default":      {"mode": "mandelbrot", "cx": -0.5,   "cy": 0.0,  "zoom": 1.5,
                     "julia_cx": -0.7,   "julia_cy": 0.27},
    "seahorse":     {"mode": "mandelbrot", "cx": -0.75,  "cy": 0.1,  "zoom": 0.1,
                     "julia_cx": -0.7,   "julia_cy": 0.27},
    "lightning":    {"mode": "mandelbrot", "cx": 0.0,    "cy": 0.65, "zoom": 0.3,
                     "julia_cx": -0.7,   "julia_cy": 0.27},
    "julia_swirl":  {"mode": "julia",      "cx": -0.5,   "cy": 0.0,  "zoom": 1.5,
                     "julia_cx": -0.4,   "julia_cy": 0.6},
    "julia_rabbit": {"mode": "julia",      "cx": -0.5,   "cy": 0.0,  "zoom": 1.5,
                     "julia_cx": -0.123, "julia_cy": 0.745},
}


# -------------------------------------------------------------------------
def fractal_fill(
    mask: list,
    cx: float = -0.5,
    cy: float = 0.0,
    zoom: float = 1.5,
    max_iter: int = 64,
    mode: str = "mandelbrot",
    julia_cx: float = -0.7,
    julia_cy: float = 0.27,
    preset: str = "default",
    density_chars: Optional[str] = None,
) -> list:
    """Fill glyph mask with Mandelbrot or Julia set escape time (F05).

    Each ink cell is mapped to a complex coordinate based on its normalised
    position in the glyph bounding box.  An aspect-ratio correction of 2.0 is
    applied to the y-axis (character cells are taller than wide).

    Escape-time algorithm:

      Mandelbrot: z₀=0+0j, c=mapped_coord; iterate z = z² + c
      Julia:      z₀=mapped_coord, c=julia_cx+julia_cy·j; iterate z = z² + c

    Smooth colouring (removes integer banding):
      When |z|²>4: smooth_val = n + 1 - log2(log2(|z|²))

    Interior cells (never escape) → 0.0 → densest character.
    Exterior cells → smooth_val normalised to [0, 1] → lighter characters.

    Named presets:
      "default"      — full Mandelbrot, cx=-0.5, cy=0, zoom=1.5
      "seahorse"     — seahorse valley, cx=-0.75, cy=0.1, zoom=0.1
      "lightning"    — lightning bolt region, cx=0, cy=0.65, zoom=0.3
      "julia_swirl"  — Julia set, c=-0.4+0.6j, swirling spirals
      "julia_rabbit" — Julia set, c=-0.123+0.745j, Douady rabbit

    :param mask: 2D list of floats from glyph_to_mask() — values 0.0–1.0.
    :param cx: Real-axis centre of the view window (default: -0.5).
    :param cy: Imaginary-axis centre of the view window (default: 0.0).
    :param zoom: View half-width in the complex plane (default: 1.5).
    :param max_iter: Maximum iteration count before declaring interior (default: 64).
    :param mode: 'mandelbrot' or 'julia' (default: 'mandelbrot').
    :param julia_cx: Real part of the Julia constant c (default: -0.7).
    :param julia_cy: Imaginary part of the Julia constant c (default: 0.27).
    :param preset: Named parameter preset; overrides all params when set (default: 'default').
    :param density_chars: Darkest-to-lightest character sequence (default: _DENSE).
    :returns: List of strings — one per row, same shape as input mask.
    :raises ValueError: If preset or mode name is unknown.
    """
    if preset not in _FRACTAL_PRESETS:
        raise ValueError(
            f"Unknown fractal preset '{preset}'. "
            f"Available: {', '.join(_FRACTAL_PRESETS.keys())}"
        )

    rows = len(mask)
    if rows == 0:
        return []
    cols = max(len(row) for row in mask)
    if cols == 0:
        return []

    # Apply preset — overrides individual params
    p = _FRACTAL_PRESETS[preset]
    mode     = p["mode"]
    cx       = p["cx"]
    cy       = p["cy"]
    zoom     = p["zoom"]
    julia_cx = p["julia_cx"]
    julia_cy = p["julia_cy"]

    if mode not in ("mandelbrot", "julia"):
        raise ValueError(f"Unknown fractal mode '{mode}'. Use 'mandelbrot' or 'julia'.")

    chars   = density_chars if density_chars is not None else _DENSE
    n_chars = len(chars)

    # -------------------------------------------------------------------------
    # Identify ink cells and build bounding box for normalised coordinates
    ink_cells = [
        (r, c)
        for r in range(rows)
        for c in range(len(mask[r]))
        if mask[r][c] >= 0.5
    ]
    if not ink_cells:
        return [" " * cols for _ in range(rows)]

    min_r = min(r for r, _ in ink_cells)
    max_r = max(r for r, _ in ink_cells)
    min_c = min(c for _, c in ink_cells)
    max_c = max(c for _, c in ink_cells)

    row_span = max(max_r - min_r, 1)
    col_span = max(max_c - min_c, 1)

    # Aspect-ratio correction: character cells are ~2× taller than wide, so
    # the y extent in the complex plane must be stretched accordingly.
    aspect_ratio = 2.0

    # Julia constant (only used in julia mode)
    julia_c = complex(julia_cx, julia_cy)

    ink_mask = [
        [mask[r][c] >= 0.5 if c < len(mask[r]) else False for c in range(cols)]
        for r in range(rows)
    ]

    # -------------------------------------------------------------------------
    # Compute escape values for all ink cells
    escape_grid: list = [[0.0] * cols for _ in range(rows)]
    exterior_vals: list = []   # smooth escape values for exterior cells

    for r, c in ink_cells:
        # Normalise to [-1, +1] within bounding box
        nx = (c - min_c) / col_span * 2.0 - 1.0   # -1.0 to +1.0
        ny = (r - min_r) / row_span * 2.0 - 1.0   # -1.0 to +1.0

        # Map to complex plane centred at (cx, cy) with half-width zoom
        re = cx + nx * zoom
        im = cy + ny * zoom * aspect_ratio

        if mode == "mandelbrot":
            z = complex(0.0, 0.0)
            c_val = complex(re, im)
        else:
            z = complex(re, im)
            c_val = julia_c

        escaped = False
        smooth_val = 0.0
        for n in range(max_iter):
            z = z * z + c_val
            absq = z.real * z.real + z.imag * z.imag
            if absq > 4.0:
                # Smooth colouring: fractional iteration count
                smooth_val = n + 1.0 - math.log2(math.log2(absq))
                escaped = True
                break

        if escaped:
            escape_grid[r][c] = smooth_val
            exterior_vals.append(smooth_val)
        else:
            escape_grid[r][c] = -1.0   # sentinel for interior

    # -------------------------------------------------------------------------
    # Normalise exterior smooth values to [0, 1]
    if exterior_vals:
        e_min = min(exterior_vals)
        e_max = max(exterior_vals)
        e_span = e_max - e_min
        if e_span < 1e-9:
            e_span = 1.0
    else:
        e_min, e_span = 0.0, 1.0

    # -------------------------------------------------------------------------
    # Build output rows
    result = []
    for r in range(rows):
        line = ""
        for c in range(cols):
            if not ink_mask[r][c]:
                line += " "
                continue
            val = escape_grid[r][c]
            if val < 0.0:
                # Interior — never escaped → densest character
                line += chars[0]
            else:
                norm = (val - e_min) / e_span
                norm = max(0.0, min(1.0, norm))
                idx = int(norm * (n_chars - 1) + 0.5)
                idx = max(0, min(n_chars - 1, idx))
                # Low norm (barely escaped) → dense; high norm → light
                line += chars[n_chars - 1 - idx]
        result.append(line)

    return result


# -------------------------------------------------------------------------
# Strange Attractor fill — N08
#
# Chaotic attractor trajectory projected into a 2D density histogram,
# then mapped to character density inside the glyph ink mask.
#
# Supported attractors:
#   "lorenz"   — Lorenz (1963) continuous ODE; parameters σ=10, ρ=28, β=8/3.
#                Classic butterfly attractor. Projected to (x, y) plane.
#                dt = 0.005 (RK4 integration).
#
#   "rossler"  — Rössler (1976) continuous ODE; parameters a=0.1, b=0.1, c=14.
#                Thin band spiral in (x, y) plane. dt = 0.05 (RK4 integration).
#
#   "dejong"   — Peter de Jong discrete map:
#                  x' = sin(a·y) - cos(b·x)
#                  y' = sin(c·x) - cos(d·y)
#                Default parameters: a=−2.0, b=−2.0, c=−1.2, d=2.0.
#                Produces intricate lattice-like patterns.
#
#   "clifford" — Clifford Pickover attractor:
#                  x' = sin(a·y) + c·cos(a·x)
#                  y' = sin(b·x) + d·cos(b·y)
#                Default parameters: a=−1.4, b=1.6, c=1.0, d=0.7.
#                Produces layered petals and woven filaments.
#
# Algorithm:
#   1. Warm up: discard first WARMUP steps so the trajectory is on the attractor.
#   2. Collect STEPS (x, y) samples.
#   3. Build a density histogram on a grid sized (BIN_ROWS × BIN_COLS).
#   4. Apply log1p compression to reduce the dynamic range (sparse/dense cells).
#   5. For each glyph ink cell (r, c), map to a histogram bin by proportional
#      position and sample the density.
#   6. Normalise and map to character density — high density → dense chars.
#
# The density histogram grid can be larger than the glyph mask — it acts as
# a virtual "canvas" that gets sampled at glyph-mask resolution.

_ATTRACTOR_DENSE: str = "@#S%?*+;:,. "

# Warmup steps to discard before collecting trajectory
_ATTRACTOR_WARMUP: int = 1000
# Default histogram bin dimensions — more bins = finer detail
_ATTRACTOR_BIN_ROWS: int = 120
_ATTRACTOR_BIN_COLS: int = 120

# Named preset parameter bundles for De Jong and Clifford
_DEJONG_PRESETS: dict = {
    "default": {"a": -2.0,  "b": -2.0,  "c": -1.2,  "d":  2.0},
    "classic": {"a": -1.4,  "b":  1.6,  "c":  1.0,  "d":  0.7},
    "thorn":   {"a":  2.01, "b": -2.53, "c":  1.61, "d": -0.33},
    "crystal": {"a": -0.8,  "b": -0.9,  "c": -0.5,  "d":  0.7},
}

_CLIFFORD_PRESETS: dict = {
    "default":  {"a": -1.4,  "b":  1.6,  "c":  1.0,  "d":  0.7},
    "spider":   {"a": -1.7,  "b":  1.3,  "c": -0.1,  "d": -1.2},
    "woven":    {"a": -1.3,  "b": -1.3,  "c": -1.8,  "d": -1.9},
    "spiral":   {"a":  1.7,  "b":  1.7,  "c":  0.6,  "d":  1.2},
}


# -------------------------------------------------------------------------
def _lorenz_trajectory(steps: int, dt: float = 0.005) -> list:
    """Integrate the Lorenz system using 4th-order Runge-Kutta.

    Parameters: σ=10, ρ=28, β=8/3 (classic chaos regime).
    Warmup: _ATTRACTOR_WARMUP steps discarded before collection.

    :param steps: Number of (x, y, z) points to collect.
    :param dt: Integration time step (default 0.005).
    :returns: List of (x, y) tuples (z discarded; x–y plane shows butterfly wings).
    """
    sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0
    x, y, z = 1.0, 0.5, 0.5

    def _deriv(x_: float, y_: float, z_: float):
        return (sigma * (y_ - x_), x_ * (rho - z_) - y_, x_ * y_ - beta * z_)

    def _rk4(x_: float, y_: float, z_: float):
        dx1, dy1, dz1 = _deriv(x_, y_, z_)
        dx2, dy2, dz2 = _deriv(x_ + 0.5*dt*dx1, y_ + 0.5*dt*dy1, z_ + 0.5*dt*dz1)
        dx3, dy3, dz3 = _deriv(x_ + 0.5*dt*dx2, y_ + 0.5*dt*dy2, z_ + 0.5*dt*dz2)
        dx4, dy4, dz4 = _deriv(x_ + dt*dx3, y_ + dt*dy3, z_ + dt*dz3)
        return (
            x_ + dt * (dx1 + 2*dx2 + 2*dx3 + dx4) / 6.0,
            y_ + dt * (dy1 + 2*dy2 + 2*dy3 + dy4) / 6.0,
            z_ + dt * (dz1 + 2*dz2 + 2*dz3 + dz4) / 6.0,
        )

    # Warm up — get onto the attractor
    for _ in range(_ATTRACTOR_WARMUP):
        x, y, z = _rk4(x, y, z)

    pts = []
    for _ in range(steps):
        x, y, z = _rk4(x, y, z)
        pts.append((x, y))   # project to x–y plane
    return pts


# -------------------------------------------------------------------------
def _rossler_trajectory(steps: int, dt: float = 0.05) -> list:
    """Integrate the Rössler system using 4th-order Runge-Kutta.

    Parameters: a=0.1, b=0.1, c=14.0 (funnel/band chaos regime).
    Projected to (x, y) plane — shows the spiraling band structure.

    :param steps: Number of (x, y) points to collect.
    :param dt: Integration time step (default 0.05).
    :returns: List of (x, y) tuples.
    """
    a, b, c = 0.1, 0.1, 14.0
    x, y, z = 1.0, 0.0, 0.0

    def _deriv(x_: float, y_: float, z_: float):
        return (-y_ - z_, x_ + a * y_, b + z_ * (x_ - c))

    def _rk4(x_: float, y_: float, z_: float):
        dx1, dy1, dz1 = _deriv(x_, y_, z_)
        dx2, dy2, dz2 = _deriv(x_ + 0.5*dt*dx1, y_ + 0.5*dt*dy1, z_ + 0.5*dt*dz1)
        dx3, dy3, dz3 = _deriv(x_ + 0.5*dt*dx2, y_ + 0.5*dt*dy2, z_ + 0.5*dt*dz2)
        dx4, dy4, dz4 = _deriv(x_ + dt*dx3, y_ + dt*dy3, z_ + dt*dz3)
        return (
            x_ + dt * (dx1 + 2*dx2 + 2*dx3 + dx4) / 6.0,
            y_ + dt * (dy1 + 2*dy2 + 2*dy3 + dy4) / 6.0,
            z_ + dt * (dz1 + 2*dz2 + 2*dz3 + dz4) / 6.0,
        )

    for _ in range(_ATTRACTOR_WARMUP):
        x, y, z = _rk4(x, y, z)

    pts = []
    for _ in range(steps):
        x, y, z = _rk4(x, y, z)
        pts.append((x, y))
    return pts


# -------------------------------------------------------------------------
def _dejong_trajectory(steps: int, params: dict) -> list:
    """Iterate the Peter de Jong attractor map.

    Map equations:
      x' = sin(a·y) - cos(b·x)
      y' = sin(c·x) - cos(d·y)

    :param steps: Number of (x, y) iterations to collect.
    :param params: Dict with keys 'a', 'b', 'c', 'd'.
    :returns: List of (x, y) tuples.
    """
    a, b, c, d = params["a"], params["b"], params["c"], params["d"]
    x, y = 0.1, 0.1

    # Warm up
    for _ in range(_ATTRACTOR_WARMUP):
        x, y = math.sin(a * y) - math.cos(b * x), math.sin(c * x) - math.cos(d * y)

    pts = []
    for _ in range(steps):
        x, y = math.sin(a * y) - math.cos(b * x), math.sin(c * x) - math.cos(d * y)
        pts.append((x, y))
    return pts


# -------------------------------------------------------------------------
def _clifford_trajectory(steps: int, params: dict) -> list:
    """Iterate the Clifford attractor map.

    Map equations:
      x' = sin(a·y) + c·cos(a·x)
      y' = sin(b·x) + d·cos(b·y)

    :param steps: Number of (x, y) iterations to collect.
    :param params: Dict with keys 'a', 'b', 'c', 'd'.
    :returns: List of (x, y) tuples.
    """
    a, b, c, d = params["a"], params["b"], params["c"], params["d"]
    x, y = 0.1, 0.1

    for _ in range(_ATTRACTOR_WARMUP):
        x, y = (math.sin(a * y) + c * math.cos(a * x),
                math.sin(b * x) + d * math.cos(b * y))

    pts = []
    for _ in range(steps):
        x, y = (math.sin(a * y) + c * math.cos(a * x),
                math.sin(b * x) + d * math.cos(b * y))
        pts.append((x, y))
    return pts


# -------------------------------------------------------------------------
def _build_density_grid(pts: list, bin_rows: int, bin_cols: int) -> list:
    """Build a 2D density histogram from trajectory points.

    Each point is mapped to its histogram bin by normalising the bounding box
    of the trajectory to [0, bin_rows) × [0, bin_cols). Log1p compression
    is applied to reduce dynamic range (very dense core vs sparse edges).

    :param pts: List of (x, y) tuples from a trajectory generator.
    :param bin_rows: Number of histogram rows.
    :param bin_cols: Number of histogram columns.
    :returns: 2D list[list[float]] of normalised density values (0.0–1.0),
              shape bin_rows × bin_cols.
    """
    if not pts:
        return [[0.0] * bin_cols for _ in range(bin_rows)]

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    range_x = max_x - min_x or 1.0
    range_y = max_y - min_y or 1.0

    # Build count grid
    grid = [[0] * bin_cols for _ in range(bin_rows)]
    for x, y in pts:
        col = int((x - min_x) / range_x * (bin_cols - 1) + 0.5)
        row = int((y - min_y) / range_y * (bin_rows - 1) + 0.5)
        col = max(0, min(bin_cols - 1, col))
        row = max(0, min(bin_rows - 1, row))
        grid[row][col] += 1

    # Log1p compression — reduces the extreme density contrast
    float_grid = [[math.log1p(grid[r][c]) for c in range(bin_cols)]
                  for r in range(bin_rows)]

    # Normalise to 0.0–1.0
    all_vals = [float_grid[r][c] for r in range(bin_rows) for c in range(bin_cols)]
    max_v = max(all_vals) if all_vals else 1.0
    if max_v < 1e-12:
        return [[0.0] * bin_cols for _ in range(bin_rows)]

    return [[float_grid[r][c] / max_v for c in range(bin_cols)]
            for r in range(bin_rows)]


# -------------------------------------------------------------------------
def strange_attractor_fill(
    mask: list,
    attractor: str = "lorenz",
    steps: int = 80000,
    density_chars: Optional[str] = None,
    preset: Optional[str] = None,
    bin_rows: int = _ATTRACTOR_BIN_ROWS,
    bin_cols: int = _ATTRACTOR_BIN_COLS,
) -> list:
    """Fill glyph mask using a chaotic strange attractor density projection (N08).

    Integrates or iterates the selected attractor for *steps* steps, building a
    2D density histogram of the trajectory. Each glyph ink cell is mapped to its
    proportional position in the attractor's bounding box and samples the density
    there. Dense trajectory regions (where the orbit spends most time) → heavy
    chars; sparse regions (rare excursions) → light chars.

    The histogram is log1p-compressed before mapping to reduce the extreme
    contrast between the dense core and the sparse outer filaments of the attractor.

    Available attractors:
      "lorenz"   — Lorenz butterfly (σ=10, ρ=28, β=8/3), projected to x–y plane.
                   Produces asymmetric wing-like density with dense orbital bands.
      "rossler"  — Rössler funnel (a=0.1, b=0.1, c=14.0), projected to x–y plane.
                   Produces a dense spiral disk with a lighter outer band.
      "dejong"   — Peter de Jong discrete map. Rich lattice / petal patterns.
                   Named presets: 'default', 'classic', 'thorn', 'crystal'.
      "clifford" — Clifford Pickover attractor. Layered filaments and woven loops.
                   Named presets: 'default', 'spider', 'woven', 'spiral'.

    :param mask: 2D list of floats from glyph_to_mask() — values 0.0–1.0.
    :param attractor: Attractor name (default: 'lorenz').
    :param steps: Trajectory length in iterations/steps (default: 80000).
    :param density_chars: Darkest-to-lightest char sequence (default: _ATTRACTOR_DENSE).
    :param preset: Named parameter preset for 'dejong' or 'clifford' attractors.
                   Ignored for 'lorenz' and 'rossler'.
    :param bin_rows: Density histogram height in bins (default: 120).
    :param bin_cols: Density histogram width in bins (default: 120).
    :returns: List of strings — one per row, same shape as input mask.
    :raises ValueError: If attractor name is unknown or preset name is invalid.
    """
    rows = len(mask)
    if rows == 0:
        return []
    cols = max(len(row) for row in mask)
    if cols == 0:
        return []

    # Strip trailing space from char set for ink cells — ink cells should never
    # be empty regardless of density. The space at the end of the default set is
    # for "outside the mask" only. We keep it in the user-supplied set only if
    # all characters happen to be spaces (unusual edge case).
    raw_chars = density_chars if density_chars is not None else _ATTRACTOR_DENSE
    ink_chars = raw_chars.rstrip(" ") or raw_chars[0]  # at least one char
    n_chars = len(ink_chars)

    # -------------------------------------------------------------------------
    # Build ink mask
    ink = [
        [mask[r][c] >= 0.5 if c < len(mask[r]) else False for c in range(cols)]
        for r in range(rows)
    ]

    # -------------------------------------------------------------------------
    # Generate trajectory
    attractor = attractor.lower()
    if attractor == "lorenz":
        pts = _lorenz_trajectory(steps)
    elif attractor == "rossler":
        pts = _rossler_trajectory(steps)
    elif attractor == "dejong":
        params = _DEJONG_PRESETS.get(preset or "default")
        if params is None:
            raise ValueError(
                f"Unknown De Jong preset '{preset}'. "
                f"Available: {', '.join(_DEJONG_PRESETS.keys())}"
            )
        pts = _dejong_trajectory(steps, params)
    elif attractor == "clifford":
        params = _CLIFFORD_PRESETS.get(preset or "default")
        if params is None:
            raise ValueError(
                f"Unknown Clifford preset '{preset}'. "
                f"Available: {', '.join(_CLIFFORD_PRESETS.keys())}"
            )
        pts = _clifford_trajectory(steps, params)
    else:
        raise ValueError(
            f"Unknown attractor '{attractor}'. "
            f"Available: lorenz, rossler, dejong, clifford"
        )

    # -------------------------------------------------------------------------
    # Build density histogram
    density = _build_density_grid(pts, bin_rows, bin_cols)

    # -------------------------------------------------------------------------
    # Map each ink cell to a density bin and select a character
    result = []
    for r in range(rows):
        line = ""
        for c in range(cols):
            if not ink[r][c]:
                line += " "
                continue
            # Map (r, c) proportionally to density grid coordinates
            # r ranges 0..rows-1 → bin_row 0..bin_rows-1
            # c ranges 0..cols-1 → bin_col 0..bin_cols-1
            br = int(r / max(rows - 1, 1) * (bin_rows - 1) + 0.5)
            bc = int(c / max(cols - 1, 1) * (bin_cols - 1) + 0.5)
            br = max(0, min(bin_rows - 1, br))
            bc = max(0, min(bin_cols - 1, bc))
            d = density[br][bc]   # 0.0–1.0, log-compressed
            idx = int(d * (n_chars - 1) + 0.5)
            idx = max(0, min(n_chars - 1, idx))
            line += ink_chars[n_chars - 1 - idx]    # high density → ink_chars[0] (dense)
        result.append(line)

    return result


# -------------------------------------------------------------------------
# L-System (Lindenmayer System) Growth fill — N06
#
# A Lindenmayer system is a parallel string-rewriting system originally
# developed by biologist Aristid Lindenmayer (1968) to model plant growth.
# An axiom string is repeatedly rewritten by production rules, then
# interpreted as turtle-graphics instructions to draw branching structures.
#
# Algorithm:
#   1. Expand the axiom string by applying productions N times (iterations).
#   2. Interpret the resulting string with a turtle:
#        F  — move forward, draw a segment (deposit density along the line)
#        f  — move forward, no draw (move only)
#        +  — turn left by angle
#        -  — turn right by angle
#        [  — push state (pos, heading, step_length)
#        ]  — pop state
#        |  — reverse direction (U-turn)
#        <  — multiply step length by contraction factor
#        >  — multiply step length by 1 / contraction_factor
#        X, Y, Z, A–W  — variables (no action, only rewritten)
#   3. Collect all drawn segments; for each segment rasterise it onto a
#      density grid using Bresenham's line algorithm with integer coordinates.
#   4. Map the density grid to the glyph mask:
#      - Scale the bounding box of all drawn points to fit the glyph.
#      - For each ink cell, sample the density at its mapped position.
#   5. Apply log1p compression to handle the density dynamic range.
#   6. Normalise to 0..1 and map to character density.
#
# Named presets from classic L-system literature:
#   "plant"      — Prusinkiewicz & Lindenmayer "Algorithmic Beauty of Plants" Fig 1.24
#   "fern"       — barnsley-fern like branching (Fractal Fern variant)
#   "sierpinski" — Sierpinski triangle / arrowhead curve
#   "dragon"     — Heighway Dragon curve
#   "bush"       — dense multi-branch bush
#   "algae"      — Lindenmayer's original two-symbol algae string (purely linear)
#   "tree32"     — binary tree at 32° branch angle
#   "crystal"    — Koch snowflake variant (hexagonal symmetry)

_LSYSTEM_DENSE: str = "@#S%?*+;:,. "

_LSYSTEM_PRESETS: dict = {
    # axiom, rules, angle_deg, iterations, contraction
    "plant": {
        "axiom":       "X",
        "rules":       {"X": "F+[[X]-X]-F[-FX]+X", "F": "FF"},
        "angle_deg":   25.0,
        "iterations":  4,
        "contraction": 1.0,
    },
    "fern": {
        "axiom":       "X",
        "rules":       {"X": "F+[[X]-X]-F[-FX]+X", "F": "FF"},
        "angle_deg":   22.5,
        "iterations":  4,
        "contraction": 1.0,
    },
    "sierpinski": {
        "axiom":       "F-G-G",
        "rules":       {"F": "F-G+F+G-F", "G": "GG"},
        "angle_deg":   120.0,
        "iterations":  4,
        "contraction": 1.0,
    },
    "dragon": {
        "axiom":       "FX",
        "rules":       {"X": "X+YF+", "Y": "-FX-Y"},
        "angle_deg":   90.0,
        "iterations":  8,
        "contraction": 1.0,
    },
    "bush": {
        "axiom":       "F",
        "rules":       {"F": "FF+[+F-F-F]-[-F+F+F]"},
        "angle_deg":   22.5,
        "iterations":  3,
        "contraction": 1.0,
    },
    "algae": {
        # Lindenmayer's original (1968) — A → AB, B → A
        # Purely linear; grows into a Fibonacci-sequence-length string.
        "axiom":       "A",
        "rules":       {"A": "AB", "B": "A"},
        "angle_deg":   45.0,
        "iterations":  6,
        "contraction": 1.0,
    },
    "tree32": {
        "axiom":       "F",
        "rules":       {"F": "F[+F]F[-F]F"},
        "angle_deg":   32.0,
        "iterations":  4,
        "contraction": 1.0,
    },
    "crystal": {
        "axiom":       "F++F++F",
        "rules":       {"F": "F-F++F-F"},
        "angle_deg":   60.0,
        "iterations":  4,
        "contraction": 1.0,
    },
}


# -------------------------------------------------------------------------
def _lsystem_expand(axiom: str, rules: dict, iterations: int) -> str:
    """Expand an L-system axiom by applying production rules N times.

    Each character not in `rules` is preserved unchanged.

    :param axiom: Starting string (the axiom / seed).
    :param rules: Dict mapping each symbol to its replacement string.
    :param iterations: Number of rewriting steps to perform.
    :returns: Expanded string after `iterations` applications of the rules.
    """
    s = axiom
    for _ in range(iterations):
        s = "".join(rules.get(ch, ch) for ch in s)
    return s


# -------------------------------------------------------------------------
def _lsystem_segments(
    s: str,
    angle_deg: float,
    step: float = 1.0,
    contraction: float = 1.0,
    start_angle_deg: float = 90.0,
) -> list:
    """Interpret an L-system string as turtle-graphics and collect segments.

    Turtle state: (x, y, heading_deg, step_length).
    Stack supports branching via [ and ].

    Only 'F' draws; 'f' moves without drawing. All other valid symbols
    are processed but produce no segments.

    :param s: Expanded L-system string.
    :param angle_deg: Turn angle per + or - command (degrees).
    :param step: Initial forward step length (default: 1.0).
    :param contraction: Step-length multiplier for '<' (>1 contracts, default 1.0).
    :param start_angle_deg: Initial heading in degrees (default: 90 = upward).
    :returns: List of (x0, y0, x1, y1) tuples representing drawn segments.
    """
    segments = []
    stack = []
    x, y, heading = 0.0, 0.0, start_angle_deg
    step_len = step

    for ch in s:
        if ch == "F":
            rad = math.radians(heading)
            nx = x + step_len * math.cos(rad)
            ny = y + step_len * math.sin(rad)
            segments.append((x, y, nx, ny))
            x, y = nx, ny
        elif ch == "f":
            rad = math.radians(heading)
            x += step_len * math.cos(rad)
            y += step_len * math.sin(rad)
        elif ch == "+":
            heading += angle_deg
        elif ch == "-":
            heading -= angle_deg
        elif ch == "[":
            stack.append((x, y, heading, step_len))
        elif ch == "]":
            if stack:
                x, y, heading, step_len = stack.pop()
        elif ch == "|":
            heading = (heading + 180.0) % 360.0
        elif ch == "<":
            step_len *= contraction
        elif ch == ">":
            step_len /= contraction if contraction != 0.0 else 1.0
        # Variable symbols (X, Y, Z, G, A, B, W, etc.) — no action

    return segments


# -------------------------------------------------------------------------
def _bresenham_density(
    x0: int, y0: int, x1: int, y1: int,
    grid: list, rows: int, cols: int,
) -> None:
    """Rasterise a line segment into a density grid using Bresenham's algorithm.

    Increments each grid cell the segment passes through by 1.
    Out-of-bounds cells are silently skipped.

    :param x0: Start column (integer).
    :param y0: Start row (integer).
    :param x1: End column (integer).
    :param y1: End row (integer).
    :param grid: 2D list of ints — density accumulator (rows × cols).
    :param rows: Grid height.
    :param cols: Grid width.
    """
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        if 0 <= y0 < rows and 0 <= x0 < cols:
            grid[y0][x0] += 1
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy


# -------------------------------------------------------------------------
def _lsystem_density_grid(
    segments: list,
    bin_rows: int,
    bin_cols: int,
) -> list:
    """Build a density grid from L-system turtle segments.

    Scales all segments so they fit within the bin_rows × bin_cols canvas,
    then rasterises each segment with Bresenham's algorithm. Applies log1p
    compression and normalises to 0.0–1.0.

    :param segments: List of (x0, y0, x1, y1) float tuples.
    :param bin_rows: Grid height in cells.
    :param bin_cols: Grid width in cells.
    :returns: 2D list[list[float]] of normalised density values (0.0–1.0),
              shape bin_rows × bin_cols. All-zero if no segments provided.
    """
    if not segments:
        return [[0.0] * bin_cols for _ in range(bin_rows)]

    # Gather all endpoints to find bounding box
    all_x = [pt for seg in segments for pt in (seg[0], seg[2])]
    all_y = [pt for seg in segments for pt in (seg[1], seg[3])]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)

    range_x = max_x - min_x or 1.0
    range_y = max_y - min_y or 1.0

    # Add a 5% margin on each side so branches don't sit exactly on edges
    margin_c = max(1, int(bin_cols * 0.05))
    margin_r = max(1, int(bin_rows * 0.05))
    inner_cols = bin_cols - 2 * margin_c
    inner_rows = bin_rows - 2 * margin_r
    if inner_cols < 1:
        inner_cols = 1
    if inner_rows < 1:
        inner_rows = 1

    def _to_grid(sx: float, sy: float):
        gc = int((sx - min_x) / range_x * inner_cols + margin_c)
        gr = int((max_y - sy) / range_y * inner_rows + margin_r)  # flip Y (screen coords)
        return (
            max(0, min(bin_cols - 1, gc)),
            max(0, min(bin_rows - 1, gr)),
        )

    grid = [[0] * bin_cols for _ in range(bin_rows)]
    for x0, y0, x1, y1 in segments:
        gc0, gr0 = _to_grid(x0, y0)
        gc1, gr1 = _to_grid(x1, y1)
        _bresenham_density(gc0, gr0, gc1, gr1, grid, bin_rows, bin_cols)

    # Log1p compression
    float_grid = [[math.log1p(grid[r][c]) for c in range(bin_cols)]
                  for r in range(bin_rows)]

    # Normalise to 0.0–1.0
    all_vals = [float_grid[r][c] for r in range(bin_rows) for c in range(bin_cols)]
    max_v = max(all_vals) if all_vals else 1.0
    if max_v < 1e-12:
        return [[0.0] * bin_cols for _ in range(bin_rows)]

    return [[float_grid[r][c] / max_v for c in range(bin_cols)]
            for r in range(bin_rows)]


# -------------------------------------------------------------------------
def lsystem_fill(
    mask: list,
    preset: str = "plant",
    axiom: Optional[str] = None,
    rules: Optional[dict] = None,
    angle_deg: Optional[float] = None,
    iterations: Optional[int] = None,
    start_angle_deg: float = 90.0,
    density_chars: Optional[str] = None,
    bin_rows: int = 120,
    bin_cols: int = 120,
) -> list:
    """Fill glyph mask using an L-system branching structure (N06).

    A Lindenmayer system string-rewriting system generates fractal branching
    geometry, which is then rendered via turtle graphics onto a density grid.
    The density at each glyph cell drives character selection — dense trunk and
    intersection regions → heavy chars, fine branch tips → light chars.

    The fractal geometry is scaled to fit the glyph bounding box, so the
    branching pattern fills the letterform completely regardless of letter size.

    Named presets (all pure Python, no external deps):
      "plant"      — Classic Prusinkiewicz plant (Fig 1.24, ABP 1990)
      "fern"       — Fern frond variant (22.5° angle)
      "sierpinski" — Sierpinski triangle / arrowhead curve (120° turns)
      "dragon"     — Heighway Dragon curve (90° turns)
      "bush"       — Multi-branch dense bush (22.5°, 3 iterations)
      "algae"      — Lindenmayer's original algae (linear Fibonacci sequence)
      "tree32"     — Binary tree at 32° branch angle
      "crystal"    — Koch snowflake variant (60°, hexagonal)

    You can also override any preset parameter or supply fully custom rules:
      axiom       — starting string (overrides preset axiom)
      rules       — production rules dict (overrides preset rules)
      angle_deg   — turn angle in degrees (overrides preset angle)
      iterations  — rewriting depth (overrides preset iterations)

    :param mask: 2D list of floats from glyph_to_mask() — values 0.0–1.0.
    :param preset: Named preset (default: 'plant').
    :param axiom: Optional axiom override.
    :param rules: Optional rules dict override.
    :param angle_deg: Optional angle override (degrees).
    :param iterations: Optional iteration count override.
    :param start_angle_deg: Initial turtle heading (default: 90 = upward).
    :param density_chars: Darkest-to-lightest char sequence (default: _LSYSTEM_DENSE).
    :param bin_rows: Density grid height (default: 120).
    :param bin_cols: Density grid width (default: 120).
    :returns: List of strings — one per row, same shape as input mask.
    :raises ValueError: If preset name is unknown.
    """
    rows = len(mask)
    if rows == 0:
        return []
    cols = max(len(row) for row in mask)
    if cols == 0:
        return []

    if preset not in _LSYSTEM_PRESETS:
        raise ValueError(
            f"Unknown L-system preset '{preset}'. "
            f"Available: {', '.join(_LSYSTEM_PRESETS.keys())}"
        )

    cfg = _LSYSTEM_PRESETS[preset]
    _axiom = axiom if axiom is not None else cfg["axiom"]
    _rules = rules if rules is not None else cfg["rules"]
    _angle = angle_deg if angle_deg is not None else cfg["angle_deg"]
    _iters = iterations if iterations is not None else cfg["iterations"]
    _contraction = cfg.get("contraction", 1.0)

    raw_chars = density_chars if density_chars is not None else _LSYSTEM_DENSE
    ink_chars = raw_chars.rstrip(" ") or raw_chars[0]
    n_chars = len(ink_chars)

    # Build ink mask
    ink = [
        [mask[r][c] >= 0.5 if c < len(mask[r]) else False for c in range(cols)]
        for r in range(rows)
    ]

    # Generate L-system string
    lstr = _lsystem_expand(_axiom, _rules, _iters)

    # Generate turtle segments
    segments = _lsystem_segments(
        lstr,
        angle_deg=_angle,
        step=1.0,
        contraction=_contraction,
        start_angle_deg=start_angle_deg,
    )

    # Build density grid
    density = _lsystem_density_grid(segments, bin_rows, bin_cols)

    # Map each ink cell to a density bin and select a character
    result = []
    for r in range(rows):
        line = ""
        for c in range(cols):
            if not ink[r][c]:
                line += " "
                continue
            br = int(r / max(rows - 1, 1) * (bin_rows - 1) + 0.5)
            bc = int(c / max(cols - 1, 1) * (bin_cols - 1) + 0.5)
            br = max(0, min(bin_rows - 1, br))
            bc = max(0, min(bin_cols - 1, bc))
            d = density[br][bc]   # 0.0–1.0, log-compressed
            idx = int(d * (n_chars - 1) + 0.5)
            idx = max(0, min(n_chars - 1, idx))
            line += ink_chars[n_chars - 1 - idx]   # high density → ink_chars[0] (dense)
        result.append(line)

    return result


# =============================================================================
# Turing Pattern fill (N09)
# =============================================================================
#
# Based on Alan Turing's "The Chemical Basis of Morphogenesis" (1952),
# Philos. Trans. R. Soc. Lond. B 237:37–72.
#
# This implementation uses a FitzHugh-Nagumo-style activator-inhibitor system,
# which is categorically distinct from the Gray-Scott model (F04):
#
#   Gray-Scott (F04):
#     dU/dt = Du·∇²U - U·V² + f·(1-U)
#     dV/dt = Dv·∇²V + U·V² - (f+k)·V
#     → autocatalytic cubic kinetics; requires careful (f,k) tuning
#
#   Turing / FitzHugh-Nagumo (N09):
#     dU/dt = Du·∇²U + alpha·U - U³ - V + beta
#     dV/dt = Dv·∇²V + epsilon·(U - gamma·V)
#     → bistable cubic activator, linear inhibitor; epsilon controls scale
#
# The `epsilon` parameter governs spatial frequency of patterns:
#   - low epsilon  → large isolated spots (leopard / cheetah spots)
#   - mid epsilon  → elongated stripes (zebra / tiger stripes)
#   - high epsilon → labyrinthine maze (brain coral / fingerprint)
#
# Named presets encode canonical values from the literature / empirical tuning:
#   "spots"     — isolated circular domains, epsilon=0.01
#   "stripes"   — alternating stripe bands,  epsilon=0.025
#   "maze"      — labyrinthine maze,         epsilon=0.05
#   "labyrinth" — dense fingerprint pattern, epsilon=0.08

_TURING_DENSE = "@#S%?*+;:,. "

_TURING_PRESETS: dict = {
    # (alpha, beta, gamma, Da, Db, epsilon, steps)
    # alpha: activator self-activation rate
    # beta:  activator bias (spatial asymmetry control)
    # gamma: inhibitor decay ratio (normally 1.0)
    # Da, Db: diffusion rates (Db >> Da for Turing instability)
    #   Stability constraint for explicit Euler: dt ≤ 1 / (4 · Db)
    #   With dt=0.1: Db_max = 2.5.  We use Da=0.1, Db=2.0 for a safe 20× ratio.
    # epsilon: activator-inhibitor coupling — controls pattern spatial scale
    # steps: simulation iterations at scale-upsampled resolution
    "spots":     {"alpha": 0.9, "beta": -0.05, "gamma": 1.0, "Da": 0.10, "Db": 2.0, "epsilon": 0.010, "steps": 3000},  # noqa: E501
    "stripes":   {"alpha": 0.9, "beta": -0.05, "gamma": 1.0, "Da": 0.10, "Db": 2.0, "epsilon": 0.025, "steps": 3000},  # noqa: E501
    "maze":      {"alpha": 0.9, "beta": -0.05, "gamma": 1.0, "Da": 0.10, "Db": 2.0, "epsilon": 0.050, "steps": 3000},  # noqa: E501
    "labyrinth": {"alpha": 0.9, "beta": -0.05, "gamma": 1.0, "Da": 0.10, "Db": 2.0, "epsilon": 0.080, "steps": 3500},  # noqa: E501
}

_TURING_dt: float = 0.1   # dt=0.1 stable for Db=2.0 (4·Db·dt = 0.8 < 1)
_TURING_CLAMP: float = 10.0   # hard clamp for U/V to catch any residual instability


# -------------------------------------------------------------------------
def _turing_laplacian(grid: list, r: int, c: int, rows: int, cols: int, ink: list) -> float:
    """5-point Laplacian with Neumann boundary condition at mask boundary.

    Cells outside the ink mask are treated as equal to the queried cell
    (zero-flux Neumann BC), so diffusion cannot escape the glyph.

    :param grid: 2D float list (rows × cols).
    :param r: Row index.
    :param c: Column index.
    :param rows: Total grid rows.
    :param cols: Total grid columns.
    :param ink: 2D bool list — True where simulation is active.
    :returns: Discrete Laplacian value at (r, c).
    """
    def _get(rr: int, cc: int) -> float:
        """Return grid value or replicate edge for Neumann BC."""
        if 0 <= rr < rows and 0 <= cc < cols and ink[rr][cc]:
            return grid[rr][cc]
        return grid[r][c]   # Neumann: replicate self at boundary

    val = grid[r][c]
    return _get(r - 1, c) + _get(r + 1, c) + _get(r, c - 1) + _get(r, c + 1) - 4.0 * val


# -------------------------------------------------------------------------
def turing_fill(
    mask: list,
    preset: str = "stripes",
    steps: Optional[int] = None,
    seed: Optional[int] = None,
    density_chars: Optional[str] = None,
    scale: int = 4,
) -> list:
    """Fill glyph mask with Turing activator-inhibitor reaction-diffusion (N09).

    Implements the FitzHugh-Nagumo activator-inhibitor model, categorically
    distinct from Gray-Scott (F04). The equations are:

      dU/dt = Da·∇²U + alpha·U - U³ - V + beta
      dV/dt = Db·∇²V + epsilon·(U - gamma·V)

    where U is the activator and V is the inhibitor. The Turing instability
    condition requires Db >> Da (inhibitor diffuses much faster than activator),
    which generates spatially periodic patterns whose wavelength is controlled
    by the `epsilon` coupling parameter.

    Pattern morphologies (via `preset`):
      "spots"     — isolated circular spots (leopard / cheetah pattern)
      "stripes"   — alternating stripe bands (zebra / tiger pattern)
      "maze"      — labyrinthine maze (brain coral / fingerprint)
      "labyrinth" — dense fingerprint pattern (high spatial frequency)

    The glyph mask is upscaled by `scale` (default 4×) before simulation
    so that at least one full pattern wavelength fits inside even small glyphs,
    then downsampled back. The activator U concentration drives char density:
    high U → dense chars; low/negative U → light chars.

    :param mask: 2D list of floats from glyph_to_mask() — values 0.0–1.0.
    :param preset: Named parameter preset (default: 'stripes').
    :param steps: Simulation steps override (default: preset-dependent, 3000–3500).
    :param seed: Integer seed for reproducible initialisation (default: None = random).
    :param density_chars: Darkest-to-lightest character sequence (default: _TURING_DENSE).
    :param scale: Upscale factor for simulation resolution (default: 4).
    :returns: List of strings — one per row, same shape as input mask.
    :raises ValueError: If preset name is unknown.
    """
    if preset not in _TURING_PRESETS:
        raise ValueError(
            f"Unknown Turing preset '{preset}'. "
            f"Available: {', '.join(_TURING_PRESETS.keys())}"
        )

    orig_rows = len(mask)
    if orig_rows == 0:
        return []
    orig_cols = max(len(row) for row in mask)
    if orig_cols == 0:
        return []

    p = _TURING_PRESETS[preset]
    alpha = p["alpha"]
    beta = p["beta"]
    gamma = p["gamma"]
    Da = p["Da"]
    Db = p["Db"]
    epsilon = p["epsilon"]
    n_steps = steps if steps is not None else p["steps"]
    chars = (density_chars or _TURING_DENSE).rstrip(" ") or "."
    n_chars = len(chars)

    # -------------------------------------------------------------------------
    # Build original ink mask
    orig_ink = [
        [mask[r][c] >= 0.5 if c < len(mask[r]) else False for c in range(orig_cols)]
        for r in range(orig_rows)
    ]

    # -------------------------------------------------------------------------
    # Upscale by nearest-neighbour
    sim_rows = orig_rows * scale
    sim_cols = orig_cols * scale
    ink = [
        [orig_ink[r // scale][c // scale] for c in range(sim_cols)]
        for r in range(sim_rows)
    ]

    # -------------------------------------------------------------------------
    # Initialise U and V with small random perturbation around (0, 0).
    # The FHN system is symmetric about (U=0, V=0); small noise breaks symmetry
    # and seeds the Turing instability. Exterior cells stay at 0.0.
    rng = random.Random(seed)
    noise_amplitude = 0.02
    U = [
        [rng.gauss(0.0, noise_amplitude) if ink[r][c] else 0.0 for c in range(sim_cols)]
        for r in range(sim_rows)
    ]
    V = [
        [rng.gauss(0.0, noise_amplitude) if ink[r][c] else 0.0 for c in range(sim_cols)]
        for r in range(sim_rows)
    ]

    # Pre-flatten ink for iteration speed
    active_cells = [(r, c) for r in range(sim_rows) for c in range(sim_cols) if ink[r][c]]

    # -------------------------------------------------------------------------
    # Run Euler integration of the FHN activator-inhibitor system
    dt = _TURING_dt
    for _step in range(n_steps):
        dU = [[0.0] * sim_cols for _ in range(sim_rows)]
        dV = [[0.0] * sim_cols for _ in range(sim_rows)]

        for r, c in active_cells:
            u = U[r][c]
            v = V[r][c]
            lap_u = _turing_laplacian(U, r, c, sim_rows, sim_cols, ink)
            lap_v = _turing_laplacian(V, r, c, sim_rows, sim_cols, ink)
            # FitzHugh-Nagumo kinetics:
            #   activator: Da·∇²U + alpha·U - U³ - V + beta
            #   inhibitor: Db·∇²V + epsilon·(U - gamma·V)
            dU[r][c] = Da * lap_u + alpha * u - u * u * u - v + beta
            dV[r][c] = Db * lap_v + epsilon * (u - gamma * v)

        for r, c in active_cells:
            U[r][c] += dt * dU[r][c]
            V[r][c] += dt * dV[r][c]
            # Hard clamp — prevents NaN propagation if any residual instability
            if U[r][c] > _TURING_CLAMP:
                U[r][c] = _TURING_CLAMP
            elif U[r][c] < -_TURING_CLAMP:
                U[r][c] = -_TURING_CLAMP
            if V[r][c] > _TURING_CLAMP:
                V[r][c] = _TURING_CLAMP
            elif V[r][c] < -_TURING_CLAMP:
                V[r][c] = -_TURING_CLAMP

    # -------------------------------------------------------------------------
    # Downsample U to original resolution by averaging the scale×scale blocks
    U_down = []
    for r in range(orig_rows):
        row_vals = []
        for c in range(orig_cols):
            total = 0.0
            count = 0
            for dr in range(scale):
                for dc in range(scale):
                    sr = r * scale + dr
                    sc = c * scale + dc
                    if sr < sim_rows and sc < sim_cols and ink[sr][sc]:
                        total += U[sr][sc]
                        count += 1
            row_vals.append(total / count if count > 0 else 0.0)
        U_down.append(row_vals)

    # -------------------------------------------------------------------------
    # Normalise U_down to [0, 1] across ink cells for char mapping.
    # U lives in roughly [-1, +1] for FHN steady states; we want +1 → dense chars.
    ink_vals = [
        U_down[r][c]
        for r in range(orig_rows)
        for c in range(orig_cols)
        if orig_ink[r][c]
    ]
    if not ink_vals:
        return [" " * orig_cols for _ in range(orig_rows)]

    u_min = min(ink_vals)
    u_max = max(ink_vals)
    u_range = u_max - u_min
    if u_range < 1e-9:
        u_range = 1.0

    # -------------------------------------------------------------------------
    # Map normalised U to density chars and assemble output rows
    result = []
    for r in range(orig_rows):
        line = ""
        for c in range(orig_cols):
            if c >= len(mask[r]) or mask[r][c] < 0.5:
                line += " "
                continue
            raw = U_down[r][c]
            if raw != raw:   # NaN guard (should not occur with clamping, but be safe)
                raw = 0.0
            u_norm = (raw - u_min) / u_range   # 0.0–1.0, high = activator peak
            idx = int(u_norm * (n_chars - 1) + 0.5)
            idx = max(0, min(n_chars - 1, idx))
            line += chars[n_chars - 1 - idx]   # high activator → chars[0] (dense)
        result.append(line)

    return result
