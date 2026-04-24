"""
Package: scripts.generate_gallery
Generate SVG gallery from curated showcase renders + daily agent outputs.

Run with:
    python scripts/generate_gallery.py
    python scripts/generate_gallery.py --text "HELLO"
    python scripts/generate_gallery.py --index-only   # rebuild README without re-rendering
    python scripts/generate_gallery.py --profile wide
    python scripts/generate_gallery.py --profile all

Saves SVGs to docs/gallery/ (or profile-specific dir) and regenerates README.md.
Each SVG is self-contained and renders inline on GitHub.
"""

import argparse
import colorsys
import logging as _logging
import math
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from justdoit.layout import measure

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "scripts.generate_gallery"
__updated__ = "2026-04-04 00:00:00"
__version__ = "0.2.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

GALLERY_DIR = Path(__file__).parent.parent / "docs" / "gallery"
_GRID_COLS = 2   # columns in the README grid


# -------------------------------------------------------------------------
@dataclass
class GalleryProfile:
    """Gallery render tier — controls SVG font size and README thumbnail width.

    :param name: Profile name (standard/wide/4k).
    :param svg_font_size: Font size in pixels for SVG output.
    :param readme_img_width: img width in README table cells.
    :param output_dir: Path to output directory for this profile.
    :param text: Default render text (default: 'JUST DO IT').
    :param use_hd: Enable HD TTF rendering for higher character density (default: False).
    :param hd_target_cols: Target column count for HD TTF auto-sizing (default: 160).
    :param canvas_width: Fixed SVG canvas width in pixels (canvas-first sizing).
    :param canvas_height: Fixed SVG canvas height in pixels (canvas-first sizing).
    """
    name: str
    svg_font_size: int
    readme_img_width: int
    output_dir: Path
    text: str = "JUST DO IT"
    use_hd: bool = False
    hd_target_cols: int = 160
    canvas_width: int = 0
    canvas_height: int = 0


# -------------------------------------------------------------------------
def optimal_ttf_for_canvas(
    text: str,
    canvas_w: int,
    canvas_h: int,
    font_path: str,
    char_w_ratio: float = 0.6,
    min_rows: int = 8,
) -> "tuple[int, float, tuple[int, int, int] | None]":
    """Find TTF font_size that maximizes effective cell size for a canvas.

    For each candidate font_size, measures actual cols/rows, then computes:
      effective_cell_px = min(canvas_h / rows, canvas_w / (cols * char_w_ratio))
    Returns the font_size that maximizes effective_cell_px.

    :param text: Text to render.
    :param canvas_w: Canvas width in pixels.
    :param canvas_h: Canvas height in pixels.
    :param font_path: Path to the TTF font file.
    :param char_w_ratio: Monospace char width / font-size ratio (default: 0.6).
    :param min_rows: Minimum row count for quality (default: 8).
    :returns: (best_ttf_fs, best_cell_px, (cols, rows, svg_fs)) or
              (best_ttf_fs, best_cell_px, None) if no valid size found.
    """
    from justdoit.fonts.ttf import load_ttf_font

    best_fs = 4
    best_cell_px: float = 0
    best_info: "tuple[int, int, int] | None" = None

    for fs in range(4, 80, 2):
        try:
            font = load_ttf_font(font_path, font_size=fs)
            cols, rows = measure(text, font=font)
            if cols <= 0 or rows < min_rows:
                continue
            cell_px = min(canvas_h / rows, canvas_w / (cols * char_w_ratio))
            if cell_px > best_cell_px:
                best_cell_px = cell_px
                best_fs = fs
                best_info = (cols, rows, round(cell_px))
        except Exception:
            continue

    return best_fs, best_cell_px, best_info


PROFILES: dict[str, "GalleryProfile"] = {
    "standard": GalleryProfile(
        name="standard",
        svg_font_size=14,
        readme_img_width=480,
        output_dir=Path(__file__).parent.parent / "docs" / "gallery",
    ),
    "wide": GalleryProfile(
        name="wide",
        svg_font_size=28,
        readme_img_width=780,
        output_dir=Path(__file__).parent.parent / "docs" / "gallery-wide",
        use_hd=True,
        hd_target_cols=160,
    ),
    "4k": GalleryProfile(
        name="4k",
        svg_font_size=72,
        readme_img_width=780,
        output_dir=Path(__file__).parent.parent / "docs" / "gallery-4k",
        use_hd=True,
        hd_target_cols=240,
        canvas_width=3840,
        canvas_height=1080,
    ),
}

# Cell dimensions for 4K image pipeline rendering
_4K_CELL_W = 8
_4K_CELL_H = 16

# Custom palettes for G09 gallery color fills (not in main palette registry)
_NOISE_PALETTE: list = [(20, 40, 140), (60, 120, 200), (160, 210, 255), (240, 250, 255)]
_WAVE_PALETTE: list = [(0, 20, 160), (0, 160, 240), (120, 220, 255), (230, 250, 255)]

# Universal density char scale for reverse-mapping fill chars to floats
_REVERSE_DENSITY: str = "@#S%?*+;:,. "


# -------------------------------------------------------------------------
def _lerp_palette_rgb(palette: list, t: float) -> tuple:
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
    a, b = palette[lo], palette[hi]
    return (int(a[0] + (b[0] - a[0]) * frac), int(a[1] + (b[1] - a[1]) * frac), int(a[2] + (b[2] - a[2]) * frac))


# -------------------------------------------------------------------------
def _g09_grid_to_mask(base_grid: list) -> list:
    """Convert G09 (char, rgb) grid to GlyphMask (0.0/1.0 float grid).

    :param base_grid: list[list[(char, rgb|None)]].
    :returns: list[list[float]] — 1.0 for ink cells, 0.0 for space.
    """
    return [[0.0 if ch == " " else 1.0 for ch, _ in row] for row in base_grid]


# -------------------------------------------------------------------------
def _wave_float_inline(mask: list) -> list:
    """Compute wave interference float grid inline (no existing float_grid fn).

    :param mask: 2D list of floats — glyph mask.
    :returns: 2D list of floats in [0.0, 1.0] for ink cells, 0.0 for exterior.
    """
    freq1, angle1, freq2, angle2 = 3.0, 0.0, 5.0, 45.0
    fx1 = freq1 * math.cos(math.radians(angle1))
    fy1 = freq1 * math.sin(math.radians(angle1))
    fx2 = freq2 * math.cos(math.radians(angle2))
    fy2 = freq2 * math.sin(math.radians(angle2))

    rows = len(mask)
    cols = max(len(row) for row in mask) if rows > 0 else 0
    result = []
    for r in range(rows):
        row_out = []
        for c in range(cols):
            val = mask[r][c] if c < len(mask[r]) else 0.0
            if val < 0.5:
                row_out.append(0.0)
            else:
                nx = c / max(cols - 1, 1)
                ny = r / max(rows - 1, 1)
                v1 = math.cos(2 * math.pi * (fx1 * nx + fy1 * ny))
                v2 = math.cos(2 * math.pi * (fx2 * nx + fy2 * ny))
                row_out.append((v1 + v2 + 2.0) / 4.0)
        result.append(row_out)
    return result


# -------------------------------------------------------------------------
def _fill_to_float_grid(mask: list, fill_name: str) -> list:
    """Run a fill function and reverse-map chars to floats for fills without float_grid.

    :param mask: 2D list of floats — glyph mask.
    :param fill_name: Fill name (currently only 'voronoi' supported).
    :returns: 2D list of floats in [0.0, 1.0].
    """
    if fill_name == "voronoi":
        from justdoit.effects.generative import voronoi_fill
        char_rows = voronoi_fill(mask, seed=42)
    else:
        return [[0.0] * len(row) for row in mask]

    n = len(_REVERSE_DENSITY)
    result = []
    for row_str in char_rows:
        row_out = []
        for ch in row_str:
            if ch == " ":
                row_out.append(0.0)
            else:
                idx = _REVERSE_DENSITY.find(ch)
                row_out.append(1.0 - idx / max(n - 1, 1) if idx >= 0 else 0.5)
        result.append(row_out)
    return result


# -------------------------------------------------------------------------
def _apply_fill_color_to_grid(
    base_grid: list,
    fill_name: str,
    grid_cols: int,
    grid_rows: int,
    t: float = 0.0,
    fill_kwargs: "dict | None" = None,
) -> list:
    """Apply field effect color to G09 base grid cells.

    For each ink cell in base_grid, compute fill color at (col/grid_cols,
    row/grid_rows). Space cells stay space. Returns list[list[(char, rgb|None)]].

    :param base_grid: list[list[(char, None)]] — monochrome base from G09.
    :param fill_name: Fill name (flame, plasma, noise, wave, fractal, turing, voronoi).
    :param grid_cols: Grid column count.
    :param grid_rows: Grid row count.
    :param t: Time phase for animated fills (default 0.0).
    :param fill_kwargs: Extra kwargs for the fill function.
    :returns: list[list[(char, (r,g,b)|None)]].
    """
    mask = _g09_grid_to_mask(base_grid)
    kw = fill_kwargs or {}
    float_grid = None
    palette = None

    if fill_name == "flame":
        from justdoit.effects.color import FIRE_PALETTE
        from justdoit.effects.generative import flame_float_grid
        raw = flame_float_grid(mask, seed=42, **kw)
        # Remap: lift floor so edge cells (low values) stay visible; fire reads
        # brightest at high values — remap [0,1] → [0.25,1.0] so min is dim red
        float_grid = [[max(0.25, v) for v in row] for row in raw]
        palette = FIRE_PALETTE
    elif fill_name == "plasma":
        from justdoit.effects.color import SPECTRAL_PALETTE
        from justdoit.effects.generative import plasma_float_grid
        float_grid = plasma_float_grid(mask, t=t, **kw)
        palette = SPECTRAL_PALETTE
    elif fill_name == "noise":
        from justdoit.effects.generative import noise_float_grid
        float_grid = noise_float_grid(mask, seed=42, **kw)
        palette = _NOISE_PALETTE
    elif fill_name == "fractal":
        from justdoit.effects.color import ESCAPE_PALETTE
        from justdoit.effects.generative import fractal_float_grid
        float_grid = fractal_float_grid(mask, **kw)
        palette = ESCAPE_PALETTE
    elif fill_name == "turing":
        from justdoit.effects.color import BIO_PALETTE
        from justdoit.effects.generative import turing_float_grid
        raw = turing_float_grid(mask, seed=42, scale=1, steps=500, **kw)
        # Lift floor so dark turing cells stay visible (min dim green, not black)
        float_grid = [[max(0.2, v) for v in row] for row in raw]
        palette = BIO_PALETTE
    elif fill_name == "wave":
        float_grid = _wave_float_inline(mask)
        palette = _WAVE_PALETTE
    elif fill_name == "voronoi":
        from justdoit.effects.color import SPECTRAL_PALETTE
        float_grid = _fill_to_float_grid(mask, "voronoi")
        palette = SPECTRAL_PALETTE

    if float_grid is None or palette is None:
        return base_grid

    result = []
    for r, row in enumerate(base_grid):
        new_row = []
        for c, (ch, _) in enumerate(row):
            if ch == " ":
                new_row.append((" ", None))
            else:
                fval = float_grid[r][c] if r < len(float_grid) and c < len(float_grid[r]) else 0.0
                rgb = _lerp_palette_rgb(palette, fval)
                new_row.append((ch, rgb))
        result.append(new_row)
    return result


# -------------------------------------------------------------------------
def _apply_char_fill_to_grid(
    base_grid: list,
    fill_name: str,
    color: "tuple | None" = None,
) -> list:
    """Apply char-replacement fill (density/sdf/shape) to G09 mask.

    Extracts a binary mask from base_grid, runs the fill function, and
    returns a new (char, rgb) grid using the fill's chars.

    :param base_grid: list[list[(char, rgb|None)]].
    :param fill_name: Fill name (density, sdf, shape).
    :param color: Foreground color for filled chars (default white).
    :returns: list[list[(char, (r,g,b)|None)]].
    """
    mask = _g09_grid_to_mask(base_grid)

    if fill_name == "density":
        from justdoit.effects.fill import density_fill
        char_rows = density_fill(mask)
    elif fill_name == "sdf":
        from justdoit.effects.fill import sdf_fill
        char_rows = sdf_fill(mask)
    elif fill_name == "shape":
        from justdoit.effects.shape_fill import shape_fill
        char_rows = shape_fill(mask)
    else:
        return base_grid

    fg = color if color is not None else (255, 255, 255)
    result = []
    for row_str in char_rows:
        new_row = []
        for ch in row_str:
            if ch == " ":
                new_row.append((" ", None))
            else:
                new_row.append((ch, fg))
        result.append(new_row)
    return result


# -------------------------------------------------------------------------
def _grid_rainbow_color(base_grid: list) -> list:
    """Color each ink cell by column position — full hue cycle left-to-right.

    :param base_grid: list[list[(char, rgb|None)]].
    :returns: list[list[(char, (r,g,b)|None)]].
    """
    n_cols = max(len(row) for row in base_grid) if base_grid else 1
    result = []
    for row in base_grid:
        new_row = []
        for c, (ch, _) in enumerate(row):
            if ch == " ":
                new_row.append((" ", None))
            else:
                hue = c / max(n_cols - 1, 1)
                r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                new_row.append((ch, (int(r * 255), int(g * 255), int(b * 255))))
        result.append(new_row)
    return result


# -------------------------------------------------------------------------
def _curated_entries_g09(
    text: str,
    font_path: str,
    canvas_w: int,
    canvas_h: int,
    cell_w: int,
    cell_h: int,
    svg_font_size: int,
) -> "list[tuple[str, str, str]]":
    """Build all 4K G09 gallery entries via image pipeline.

    Renders text at full resolution via PIL, converts to ASCII grid via
    6D zone-match, then applies fill/color strategies to produce SVG strings.

    :param text: Text to render.
    :param font_path: Path to TTF font file.
    :param canvas_w: Canvas width in pixels.
    :param canvas_h: Canvas height in pixels.
    :param cell_w: Cell width in pixels.
    :param cell_h: Cell height in pixels.
    :param svg_font_size: Base SVG font size.
    :returns: List of (stem, label, svg_string).
    """
    from justdoit.core.image_pipeline import grid_to_svg, render_text_as_image

    grid_cols = canvas_w // cell_w
    grid_rows = canvas_h // cell_h

    print(f"    G09 base grid: {grid_cols}x{grid_rows} chars ({canvas_w}x{canvas_h}px canvas)")

    base_grid = render_text_as_image(
        text, font_path,
        output_cols=grid_cols, output_rows=grid_rows,
        cell_w=cell_w, cell_h=cell_h,
        color=False,
        fg_color=(255, 255, 255),
        bg_color=(0, 0, 0),
    )

    entries: list[tuple[str, str, str]] = []

    def _to_svg(grid: list) -> str:
        return grid_to_svg(
            grid, font_size=svg_font_size,
            canvas_width=canvas_w, canvas_height=canvas_h,
        )

    def add(stem: str, label: str, grid: list) -> None:
        entries.append((stem, label, _to_svg(grid)))

    # Strategy A — clean text, color variants
    print("    G09 Strategy A: clean text variants ...")
    white_grid = [[(ch, (255, 255, 255) if ch != " " else None) for ch, _ in row] for row in base_grid]
    add("S-G09-clean-white", "G09 — Clean text (white)", white_grid)

    cyan_grid = [[(ch, (0, 255, 200) if ch != " " else None) for ch, _ in row] for row in base_grid]
    add("S-G09-clean-cyan", "G09 — Clean text (cyan)", cyan_grid)

    add("S-G09-clean-rainbow", "G09 — Clean text (rainbow)", _grid_rainbow_color(base_grid))

    # Strategy B — field fills as color overlay
    _strategy_b = [
        ("S-G09-flame",   "G09+A08 — Flame",   "flame"),
        ("S-G09-plasma",  "G09+A10 — Plasma",  "plasma"),
        ("S-G09-voronoi", "G09+F07 — Voronoi", "voronoi"),
        ("S-G09-noise",   "G09+F02 — Noise",   "noise"),
        ("S-G09-wave",    "G09+F09 — Wave",    "wave"),
        ("S-G09-fractal", "G09+F05 — Fractal", "fractal"),
        ("S-G09-turing",  "G09+N09 — Turing",  "turing"),
    ]
    for stem, label, fill_name in _strategy_b:
        print(f"    G09 Strategy B: {fill_name} ...")
        colored = _apply_fill_color_to_grid(base_grid, fill_name, grid_cols, grid_rows)
        add(stem, label, colored)

    # Strategy C — char fills on G09 mask (full resolution)
    _strategy_c = [
        ("S-G09-density", "G09+F01 — Density (hi-res)", "density"),
        ("S-G09-sdf",     "G09+F06 — SDF (hi-res)",     "sdf"),
        ("S-G09-shape",   "G09+F07 — Shape (hi-res)",   "shape"),
    ]
    for stem, label, fill_name in _strategy_c:
        print(f"    G09 Strategy C: {fill_name} ...")
        filled = _apply_char_fill_to_grid(base_grid, fill_name)
        add(stem, label, filled)

    return entries


# -------------------------------------------------------------------------
def _validate_text(text: str, font: str = "block", gap: int = 1) -> None:
    """Warn if text renders unusually wide; raise if empty output.

    :param text: Text to validate.
    :param font: Font name (default: 'block').
    :param gap: Character gap (default: 1).
    :raises ValueError: If text produces empty output.
    """
    cols, _ = measure(text, font=font, gap=gap)
    if cols == 0:
        raise ValueError(f"Text {text!r} produces empty output with font {font!r}")
    if cols > 400:
        print(
            f"Warning: {text!r} renders to {cols} columns — SVGs will be very wide.",
            file=sys.stderr,
        )


# -------------------------------------------------------------------------
def _curated_entries(text: str, font: str = "block") -> list[tuple[str, str, str]]:
    """Render all curated showcase techniques.

    :param text: Text to render.
    :param font: Base font for block-style renders (default: 'block'). Pass an HD
        TTF font name here to get higher-density renders for wide/4k galleries.
    :returns: List of (filename_stem, label, rendered_string).
    """
    from justdoit.core.rasterizer import render
    from justdoit.effects.gradient import (
        PRESETS, linear_gradient, parse_color, per_glyph_palette, radial_gradient,
    )
    from justdoit.effects.isometric import isometric_extrude
    from justdoit.effects.spatial import perspective_tilt, shear, sine_warp

    plain = render(text, font=font)
    entries: list[tuple[str, str, str]] = []

    def add(stem: str, label: str, rendered: str) -> None:
        entries.append((stem, label, rendered))

    # Fonts
    add("S-F00-block-baseline",   "F00 — Block (baseline)",           plain)
    add("S-G01-figlet-big",       "G01 — FIGlet 'big'",               render(text, font="big"))
    add("S-G01-figlet-slant",     "G01 — FIGlet 'slant'",             render(text, font="slant"))
    add("S-G01-slim",             "G01 — Slim font",                  render(text, font="slim"))

    # Fill effects
    add("S-F01-density-fill",     "F01 — Density fill",               render(text, font=font, fill="density"))
    add("S-F06-sdf-fill",         "F06 — SDF fill",                   render(text, font=font, fill="sdf"))
    add("S-F07-shape-fill",       "F07 — Shape fill",                 render(text, font=font, fill="shape"))
    add("S-F02-noise-fill",       "F02 — Perlin noise fill",          render(text, font=font, fill="noise"))
    add("S-F03-cells-fill",       "F03 — Cellular automata fill",     render(text, font=font, fill="cells"))
    add("S-F09-wave-default",     "F09 — Wave interference (default)", render(text, font=font, fill="wave"))
    add("S-F09-wave-moire",       "F09 — Wave interference (moire)",   render(text, font=font, fill="wave"))
    add("S-F05-fractal-default",  "F05 — Fractal/Mandelbrot (default)", render(text, font=font, fill="fractal"))
    add("S-F05-fractal-julia",    "F05 — Fractal/Julia (julia_swirl)", render(text, font=font, fill="fractal"))

    # Color effects
    add("S-C01-gradient-horiz",   "C01 — Gradient (horizontal)",
        linear_gradient(plain, parse_color("red"), parse_color("cyan"), direction="horizontal"))
    add("S-C01-gradient-diag",    "C01 — Gradient (diagonal)",
        linear_gradient(plain, parse_color("magenta"), parse_color("green"), direction="diagonal"))
    add("S-C02-radial",           "C02 — Radial gradient",
        radial_gradient(plain, parse_color("white"), parse_color("purple")))
    add("S-C03-fire",             "C03 — Fire palette",               per_glyph_palette(plain, PRESETS["fire"]))
    add("S-C03-neon",             "C03 — Neon palette",               per_glyph_palette(plain, PRESETS["neon"]))
    add("S-C03-ocean",            "C03 — Ocean palette",              per_glyph_palette(plain, PRESETS["ocean"]))

    # Spatial effects
    add("S-S01-sine-warp",        "S01 — Sine warp",                  sine_warp(plain, amplitude=4.0, frequency=1.5))
    add("S-S02-perspective-top",  "S02 — Perspective tilt (top)",     perspective_tilt(plain, strength=0.5, direction="top"))
    add("S-S08-shear-right",      "S08 — Shear (right)",              shear(plain, amount=1.2, direction="right"))

    # Isometric
    iso = isometric_extrude(plain, depth=4, direction="right")
    add("S-S03-iso-right",        "S03 — Isometric extrude",          iso)
    add("S-S03-iso-gradient",     "S03+C01 — Iso + gradient",
        linear_gradient(iso, parse_color("gold"), parse_color("red"), direction="vertical"))
    add("S-S03-iso-neon-warp",    "S03+C03+S01 — Iso + neon + warp",
        sine_warp(per_glyph_palette(isometric_extrude(plain, depth=3), PRESETS["neon"]), amplitude=2.0))

    # Generative simulation fills
    add("S-N09-turing-stripes",   "N09 — Turing stripes (FHN activator-inhibitor)",
        render(text, font=font, fill="turing"))
    add("S-N09-turing-spots",     "N09 — Turing spots",
        render(text, font=font, fill="turing"))
    add("S-N09-turing-maze",      "N09 — Turing maze (labyrinthine)",
        render(text, font=font, fill="turing"))
    add("S-F07-voronoi-default",  "F07 — Voronoi fill (default)",
        render(text, font=font, fill="voronoi"))
    add("S-F07-voronoi-cracked",  "F07 — Voronoi cracked (stained-glass)",
        render(text, font=font, fill="voronoi_cracked"))
    add("S-F07-voronoi-fine",     "F07 — Voronoi fine (dense cells)",
        render(text, font=font, fill="voronoi_fine"))
    add("S-F07-voronoi-coarse",   "F07 — Voronoi coarse (large cells)",
        render(text, font=font, fill="voronoi_coarse"))

    # A10 — Plasma Wave fill
    add("S-A10-plasma-default",   "A10 — Plasma Wave (default)",
        render(text, font=font, fill="plasma"))
    add("S-A10-plasma-tight",     "A10 — Plasma tight (high freq)",
        render(text, font=font, fill="plasma_tight"))
    add("S-A10-plasma-slow",      "A10 — Plasma slow (large blobs)",
        render(text, font=font, fill="plasma_slow"))
    add("S-A10-plasma-diagonal",  "A10 — Plasma diagonal (stripe bias)",
        render(text, font=font, fill="plasma_diagonal"))

    # A08 — Flame Simulation fill
    add("S-A08-flame-default",  "A08 — Flame Simulation (balanced fire)",
        render(text, font=font, fill="flame"))
    add("S-A08-flame-hot",      "A08 — Flame hot (tall, intense flame)",
        render(text, font=font, fill="flame_hot"))
    add("S-A08-flame-embers",   "A08 — Flame embers (dying embers)",
        render(text, font=font, fill="flame_embers"))

    # Composition
    add("S-F02-noise-radial",     "F02+C02 — Noise fill + radial gradient",
        radial_gradient(render(text, font=font, fill="noise"), parse_color("cyan"), parse_color("blue")))

    return entries


# Category metadata: code prefix → (heading, anchor, description)
_CATEGORIES: dict = {
    "G": ("Fonts",          "fonts",        "Builtin, FIGlet, and TTF rasterized fonts"),
    "F": ("Fill Effects",   "fill-effects", "Character fill modes applied inside glyph masks"),
    "C": ("Color Effects",  "color-effects","Gradients, palettes, and ANSI colorization"),
    "S": ("Spatial & 3D",   "spatial--3d",  "Warps, perspective, shear, and isometric extrusion"),
}


# -------------------------------------------------------------------------
def _showcase_label(stem: str) -> str:
    """Convert a showcase SVG stem to a human-readable label.

    :param stem: SVG filename stem, e.g. 'S-F07-shape-fill'.
    :returns: Label string, e.g. 'F07 — Shape Fill'.
    """
    rest = stem[2:]  # strip "S-"
    parts = rest.split("-", 1)
    code = parts[0].upper()
    slug = parts[1].replace("-", " ").title() if len(parts) > 1 else ""
    return f"{code} — {slug}"


# -------------------------------------------------------------------------
def _daily_label(stem: str) -> str:
    """Convert a daily agent SVG stem to a human-readable label.

    :param stem: SVG filename stem, e.g. '2026-03-26-N10-slime-mold'.
    :returns: Label string, e.g. '2026-03-26 · N10 Slime Mold'.
    """
    parts = stem.split("-", 3)
    if len(parts) >= 4:
        date = "-".join(parts[:3])
        rest = parts[3].replace("-", " ").title()
        return f"{date} · {rest}"
    return stem.replace("-", " ").title()


# -------------------------------------------------------------------------
def _table(pairs: list, img_width: int = 480) -> list:
    """Render a list of (filename, label) pairs as an HTML grid table.

    When img_width <= 0, the width= attribute is omitted and the SVG
    renders at its natural intrinsic size (correct for 4K/wide galleries
    where the SVG itself is already the target resolution).

    :param pairs: List of (svg_filename, label) tuples.
    :param img_width: Width in pixels for thumbnail images. Pass 0 to
        render at natural SVG size (no width constraint).
    :returns: List of HTML lines.
    """
    lines = ['<table>']
    for i in range(0, len(pairs), _GRID_COLS):
        lines.append("<tr>")
        for fname, label in pairs[i:i + _GRID_COLS]:
            width_attr = f' width="{img_width}"' if img_width > 0 else ""
            lines.append(
                f'<td align="center">'
                f'<img src="{fname}"{width_attr}><br>'
                f'<sub><b>{label}</b></sub>'
                f'</td>'
            )
        lines.append("</tr>")
    lines.append("</table>")
    return lines


# -------------------------------------------------------------------------
def _write_readme(profile: GalleryProfile, entries: list[tuple[str, str, str]]) -> None:
    """Scan profile output_dir for all SVGs and write README.md.

    Showcase SVGs (S- prefix) are grouped by technique category with
    section headers and a table of contents. Daily agent outputs
    (YYYY-MM-DD- prefix) appear in a separate section, newest first.

    :param profile: Gallery profile controlling output path and img width.
    :param entries: List of (stem, label, rendered) tuples (used for ordering).
    """
    gallery_dir = profile.output_dir
    svgs = sorted(gallery_dir.glob("*.svg"))
    if not svgs:
        print(f"  no SVGs found in {gallery_dir} — nothing to index")
        return

    # Split into showcase (S- prefix) and daily (date prefix)
    showcase = [p for p in svgs if p.stem.startswith("S-")]
    daily    = sorted([p for p in svgs if not p.stem.startswith("S-")], reverse=True)

    # Group showcase by category letter (second char of code after "S-")
    groups: dict = {k: [] for k in _CATEGORIES}
    for p in showcase:
        code = p.stem[2:].split("-")[0].upper()   # e.g. "F07"
        cat = code[0] if code else "S"
        groups.setdefault(cat, []).append((p.name, _showcase_label(p.stem)))

    total = len(showcase) + len(daily)

    # --- Table of contents ---
    lines = [
        "# JustDoIt Gallery",
        "",
        "Auto-generated visual showcase of rendering techniques.",
        "Run `python scripts/demo.py --gallery` to regenerate.",
        "",
    ]
    if profile.name == "wide":
        lines.append("> **Wide gallery** — SVGs rendered at 1103×263px (28px font). Displayed at 780px width; open any SVG directly for full-width viewing.")
        lines.append("")
    elif profile.name == "4k":
        lines.append("> **4K gallery** — SVGs rendered via G09 image pipeline (PIL TTF raster → 6D zone-match ASCII → SVG). Full 480×67 character grid at 3840×1080px. Open any SVG directly for native 4K density.")
        lines.append("")
    lines += [
        "## Contents",
        "",
    ]
    for cat, (heading, anchor, _) in _CATEGORIES.items():
        if groups.get(cat):
            n = len(groups[cat])
            lines.append(f"- [{heading} ({n})](#{anchor})")
    if daily:
        lines.append(f"- [Daily Techniques ({len(daily)})](#daily-techniques)")
    lines.append("")

    # --- Showcase sections ---
    for cat, (heading, anchor, desc) in _CATEGORIES.items():
        pairs = groups.get(cat, [])
        if not pairs:
            continue
        lines += [
            f"## {heading}",
            "",
            f"*{desc}*",
            "",
        ]
        lines += _table(pairs, img_width=profile.readme_img_width)
        lines.append("")

    # --- Daily section ---
    if daily:
        lines += [
            "## Daily Techniques",
            "",
            "*New technique added each day by the daily agent — newest first.*",
            "",
        ]
        daily_pairs = [(_p.name, _daily_label(_p.stem)) for _p in daily]
        lines += _table(daily_pairs, img_width=profile.readme_img_width)
        lines.append("")

    lines.append(
        f"*Last updated: {datetime.now().strftime('%Y-%m-%d')} — "
        f"{total} technique{'s' if total != 1 else ''}*"
    )
    lines.append("")

    readme = gallery_dir / "README.md"
    readme.write_text("\n".join(lines), encoding="utf-8")
    print(f"  index  {readme}  ({total} entries)")


# -------------------------------------------------------------------------
def _generate_for_profile(profile: GalleryProfile, text: str) -> None:
    """Generate all gallery SVGs and README for a given profile.

    :param profile: Gallery profile controlling font size and output paths.
    :param text: Text to render for all gallery entries.
    """
    from justdoit.output.svg import save_svg

    profile.output_dir.mkdir(parents=True, exist_ok=True)

    # --- HD setup: attempt TTF rasterization for higher character density ---
    render_font = "block"
    svg_font_size = profile.svg_font_size
    svg_canvas_w = profile.canvas_width if profile.canvas_width > 0 else 0
    svg_canvas_h = profile.canvas_height if profile.canvas_height > 0 else 0

    if profile.use_hd:
        use_hd_runtime = False
        try:
            from PIL import Image  # noqa: F401
            use_hd_runtime = True
        except ImportError:
            print(f"  HD rendering skipped: Pillow not available", file=sys.stderr)

        if use_hd_runtime:
            from justdoit.layout import find_default_ttf, fit_ttf_size
            font_path = find_default_ttf()
            if font_path is None:
                print(f"  HD: no system TTF found — falling back to block font", file=sys.stderr)
            elif svg_canvas_h > 0 and svg_canvas_w > 0:
                # Canvas-first sizing: find TTF font_size that maximizes
                # effective cell size so fill effects render large.
                try:
                    from justdoit.fonts.ttf import load_ttf_font
                    best_fs, cell_px, info = optimal_ttf_for_canvas(
                        text, svg_canvas_w, svg_canvas_h, font_path,
                    )
                    pt_size = best_fs
                    render_font = load_ttf_font(font_path, font_size=pt_size)
                    # to_svg() will derive font_size from char_w in canvas mode,
                    # so svg_font_size here is informational only
                    svg_font_size = max(1, round(cell_px))

                    cols, rows = info[:2] if info else (0, 0)
                    print(
                        f"  Canvas-first optimal: ttf_pt={pt_size}, "
                        f"cell_px={cell_px:.1f}, text={cols}×{rows} chars, "
                        f"svg_font_size~{svg_font_size}px"
                    )
                except Exception as exc:
                    print(f"  Canvas-first setup failed: {exc} — falling back to block font", file=sys.stderr)
            else:
                try:
                    pt_size = fit_ttf_size(text, profile.hd_target_cols, font_path)
                    from justdoit.fonts.ttf import load_ttf_font
                    render_font = load_ttf_font(font_path, font_size=pt_size)
                    svg_font_size = int(pt_size * 96 / 72)
                    print(
                        f"  HD: {pt_size}pt TTF → {profile.hd_target_cols} cols target"
                        f" (font: {os.path.basename(font_path)}, svg_px={svg_font_size})"
                    )
                except Exception as exc:
                    print(f"  HD setup failed: {exc} — falling back to block font", file=sys.stderr)

    # --- G09 primary path for 4K ---
    if profile.name == "4k" and svg_canvas_w > 0 and svg_canvas_h > 0:
        try:
            from justdoit.layout import find_default_ttf
            font_path = find_default_ttf()
            if font_path is not None:
                entries = _curated_entries_g09(
                    text, font_path,
                    canvas_w=svg_canvas_w, canvas_h=svg_canvas_h,
                    cell_w=_4K_CELL_W, cell_h=_4K_CELL_H,
                    svg_font_size=svg_font_size,
                )
                for stem, label, svg_str in entries:
                    path = profile.output_dir / f"{stem}.svg"
                    path.write_text(svg_str, encoding="utf-8")
                    print(f"  saved  {path.name}  ({label})")
                _write_readme(profile, entries)
                return
            print("  G09: no system TTF found — falling back to old path", file=sys.stderr)
        except Exception as exc:
            print(f"  G09 pipeline failed: {exc} — falling back to old path", file=sys.stderr)

    entries = _curated_entries(text, font=render_font)

    for stem, label, rendered in entries:
        path = profile.output_dir / f"{stem}.svg"
        save_svg(
            rendered, str(path), font_size=svg_font_size,
            canvas_width=svg_canvas_w if svg_canvas_w > 0 else None,
            canvas_height=svg_canvas_h if svg_canvas_h > 0 else None,
        )
        print(f"  saved  {path.name}  ({label})")

    _write_readme(profile, entries)


# -------------------------------------------------------------------------
def build_index() -> None:
    """Scan docs/gallery/ for all SVGs and regenerate README.md.

    Showcase SVGs (S- prefix) are grouped by technique category with
    section headers and a table of contents. Daily agent outputs
    (YYYY-MM-DD- prefix) appear in a separate section, newest first.
    """
    standard_profile = PROFILES["standard"]
    _write_readme(standard_profile, [])


# -------------------------------------------------------------------------
def run(text: str = "Just Do It") -> None:
    """Render curated showcase SVGs and rebuild the gallery index.

    :param text: Text to render (default: 'JDI').
    """
    print(f"Rendering showcase for '{text}' ...")
    profile = PROFILES["standard"]
    profile.output_dir.mkdir(parents=True, exist_ok=True)
    _generate_for_profile(profile, text)
    print("Done.")


# -------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate JustDoIt SVG gallery and README index.",
    )
    parser.add_argument(
        "--text", default="Just Do It",
        help="Text to render (default: Just Do It)",
    )
    parser.add_argument(
        "--index-only", action="store_true",
        help="Only rebuild the README index, do not re-render SVGs",
    )
    parser.add_argument(
        "--profile", default="standard",
        choices=list(PROFILES.keys()) + ["all"],
        help="Gallery render profile: standard (14px/480px), wide (28px/800px), "
             "4k (72px/1600px), all. Default: standard",
    )
    args = parser.parse_args()

    if args.index_only:
        print("Rebuilding index only ...")
        build_index()
        print("Done.")
    else:
        text = args.text.upper()

        # Determine which profiles to run
        if args.profile == "all":
            profiles_to_run = list(PROFILES.values())
        else:
            profiles_to_run = [PROFILES[args.profile]]

        _validate_text(text)

        for profile in profiles_to_run:
            profile.output_dir.mkdir(parents=True, exist_ok=True)
            print(f"Rendering [{profile.name}] profile for '{text}' ...")
            _generate_for_profile(profile, text)
            print(f"[{profile.name}] Done → {profile.output_dir}")
