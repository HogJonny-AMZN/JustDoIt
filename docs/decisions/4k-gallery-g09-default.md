# ADR: G09 as Default 4K Render Path

**Date:** 2026-04-24  
**Status:** Approved — implement  

---

## Context

The 4K gallery currently has two parallel render systems:

1. **Old path (all entries):** `rasterize_ttf()` glyph dict → `render()` → ANSI string → `save_svg()`. Produces coarse glyph shapes — character selection is single-pixel brightness-mapped, not shape-aware. At canvas-first 4K sizing (`font_size=16`, `cell_px=133`), letters are only 8×8 chars tall — barely enough to read.

2. **G09 path (one bonus SVG only):** `render_text_as_image()` → `image_to_ascii()` → `grid_to_svg()`. PIL renders text at full canvas resolution, 6D zone DB samples every cell → real glyph contours. Currently only generates `S-G09-image-pipeline.svg` as an afterthought.

The goal: **make G09 the primary render path for every 4K showcase entry.** The old TTF glyph-dict path remains for standard/wide profiles and for animated fill effects that require a mask.

---

## What Needs to Change

### `scripts/generate_gallery.py`

#### 1. Compute G09 base grid once per profile run

At the top of `_generate_for_profile()`, when `profile.name == "4k"`, compute:

```python
g09_font_path = find_default_ttf()
g09_grid_cols = canvas_w // _4K_CELL_W    # e.g. 3840 // 8 = 480
g09_grid_rows = canvas_h // _4K_CELL_H    # e.g. 1080 // 16 = 67

# Base grid: white text on black, no color (monochrome — fills add color)
g09_base_grid = render_text_as_image(
    text, g09_font_path,
    output_cols=g09_grid_cols,
    output_rows=g09_grid_rows,
    cell_w=_4K_CELL_W,
    cell_h=_4K_CELL_H,
    color=False,           # monochrome — fills color independently
    fg_color=(255, 255, 255),
    bg_color=(0, 0, 0),
)
```

Cache this once. All 4K entries use the same base grid.

#### 2. Replace `_curated_entries()` with a new `_curated_entries_g09()` for 4K

The current `_curated_entries()` returns `(stem, label, rendered_string)` — it bakes renders into ANSI strings. This won't work for G09 which produces a grid. 

**Approach:** Add a new render path alongside the existing one. Keep `_curated_entries()` untouched (used by standard/wide). Add a new `_curated_entries_g09(text, base_grid, grid_cols, grid_rows, canvas_w, canvas_h, svg_font_size)` that returns `(stem, label, svg_string)` directly.

#### 3. Implement `_curated_entries_g09()`

Each entry in this function produces an SVG string using one of these strategies:

**Strategy A — Clean text (no fill):**
Use `g09_base_grid` directly → `grid_to_svg()`. For: baseline block, figlet, slim variants.
- These are currently rendered at the wrong font with glyph dict. G09 renders the text using PIL's actual TTF, so figlet/slim become moot at 4K (PIL renders the real font). Keep them as separate entries but all use PIL → same source, different color treatments.

**Strategy B — Field fill as color overlay:**
Take `g09_base_grid`, for each cell that has a non-space char, replace its color with the fill function's output at that cell position.

```python
def _apply_fill_color_to_grid(
    base_grid: list,          # list[list[(char, None)]] — monochrome base
    fill_name: str,           # e.g. "flame", "plasma"
    grid_cols: int,
    grid_rows: int,
    t: float = 0.0,
    fill_kwargs: dict = None,
) -> list:
    """
    For each ink cell in base_grid, compute fill color at (col/grid_cols, row/grid_rows).
    Space cells stay space. Returns list[list[(char, rgb | None)]].
    
    Uses the fill function's palette/color system to map normalized (x, y) → RGB.
    Field fills (flame, plasma, voronoi, wave, fractal, noise) all produce a
    float value per cell; map that through a palette to get RGB.
    """
```

This is **not** the full hybrid compositing path (that's Move 2). This is simpler: sample the field effect at each cell's normalized position to get a color value, apply it as the cell's fg color. The char comes from the G09 base grid (real glyph shape). The color comes from the fill.

**Strategy C — Density/SDF/Shape as char override:**
For fills that change *which char* is used (density, sdf, shape), re-apply the fill logic on top of the G09 mask. 

Extract a binary mask from `g09_base_grid` (ink cells = 1.0, space = 0.0) → run `fill_fn(mask)` → get char grid → combine with G09 positions.

```python
def _g09_grid_to_mask(base_grid: list) -> list:
    """Convert G09 (char, rgb) grid to GlyphMask (0.0/1.0 float grid)."""
    return [
        [0.0 if ch == " " else 1.0 for ch, _ in row]
        for row in base_grid
    ]
```

Then run `density_fill(mask)`, `sdf_fill(mask)`, `shape_fill(mask)` on the full-resolution G09 mask. This is a huge upgrade — these fills now operate on a 480×67 cell mask (real glyph resolution) instead of an 8×8 glyph-dict mask.

#### 4. Entry map for `_curated_entries_g09()`

```python
# Strategy A — clean text, color variants
("S-G09-clean-white",     "G09 — Clean text (white)",    strategy_a, color=(255,255,255))
("S-G09-clean-cyan",      "G09 — Clean text (cyan)",     strategy_a, color=(0,255,200))
("S-G09-clean-rainbow",   "G09 — Clean text (rainbow)",  strategy_a, color="rainbow")  # per-col hue

# Strategy B — field fills as color
("S-G09-flame",           "G09+A08 — Flame",             strategy_b, fill="flame")
("S-G09-plasma",          "G09+A10 — Plasma",            strategy_b, fill="plasma")
("S-G09-voronoi",         "G09+F07 — Voronoi",           strategy_b, fill="voronoi")
("S-G09-noise",           "G09+F02 — Noise",             strategy_b, fill="noise")
("S-G09-wave",            "G09+F09 — Wave",              strategy_b, fill="wave")
("S-G09-fractal",         "G09+F05 — Fractal",           strategy_b, fill="fractal")
("S-G09-turing",          "G09+N09 — Turing",            strategy_b, fill="turing")

# Strategy C — char fills on G09 mask (full resolution)
("S-G09-density",         "G09+F01 — Density (hi-res)",  strategy_c, fill="density")
("S-G09-sdf",             "G09+F06 — SDF (hi-res)",      strategy_c, fill="sdf")
("S-G09-shape",           "G09+F07 — Shape (hi-res)",    strategy_c, fill="shape")
```

#### 5. Wire into `_generate_for_profile()`

When `profile.name == "4k"`:
- Run `_curated_entries_g09()` instead of (or in addition to) the old `_curated_entries()`
- Old entries (glyph-dict path) can still run for comparison, prefixed `S-OLD-`
- Or: replace entirely and remove the G09 bonus file (it becomes redundant)

**Recommended: replace entirely.** The G09 path is strictly better for 4K. Keep old path only for standard/wide.

#### 6. Update `_write_readme()` for 4K

Update the 4K gallery README blurb to describe G09 rendering. Update category groupings if new stems don't match existing patterns.

---

## What NOT to change

- `_curated_entries()` — leave completely alone, used by standard/wide
- `standard` and `wide` profile render paths — untouched
- All existing tests — must still pass
- `justdoit/core/image_pipeline.py`, `image_sampler.py`, `char_db.py` — no changes needed

---

## New helper functions needed

All in `scripts/generate_gallery.py` (or a new `scripts/_g09_gallery.py` if preferred):

```python
def _g09_grid_to_mask(base_grid: list) -> list:
    """GlyphMask from G09 grid — ink=1.0, space=0.0."""

def _apply_fill_color_to_grid(
    base_grid: list,
    fill_name: str,
    grid_cols: int,
    grid_rows: int,
    t: float = 0.0,
    fill_kwargs: dict | None = None,
) -> list:
    """Apply field effect color to G09 base grid cells."""

def _apply_char_fill_to_grid(
    base_grid: list,
    fill_name: str,
    color: tuple | None = None,
) -> list:
    """Apply char-replacement fill (density/sdf/shape) to G09 mask."""

def _grid_rainbow_color(base_grid: list) -> list:
    """Color each ink cell by column position — full hue cycle left→right."""

def _curated_entries_g09(
    text: str,
    font_path: str,
    canvas_w: int,
    canvas_h: int,
    cell_w: int,
    cell_h: int,
    svg_font_size: int,
) -> list[tuple[str, str, str]]:
    """Build all 4K G09 gallery entries. Returns (stem, label, svg_string)."""
```

---

## Field fill → color mapping

The field fill functions (`flame_fill`, `plasma_fill`, etc.) currently take a `GlyphMask` and return a `Glyph` (list of strings with chars). For Strategy B we need the *color value* at each grid position, not the char.

**Approach:** Each field effect has a float field `f(x, y)` in [0,1] at each cell. Sample that field at `(col / grid_cols, row / grid_rows)` normalized coords, then map through a palette to get RGB.

For fills that already expose their underlying field (plasma, wave, fractal — they compute a float per cell and map it to a char), we can access the field directly or re-implement a thin color sampler.

For fills that don't expose their field cleanly (turing, cells), generate the full fill output, extract the char, look up the char's density in `DENSITY_CHARS` to get a float, map to palette RGB.

**Palette for each fill:**

| Fill | Palette |
|------|---------|
| flame | black → red → orange → yellow → white |
| plasma | cyan → magenta → yellow → cyan (cycle) |
| voronoi | randomized per-cell hue, fixed seed |
| noise | cool blue → white |
| wave | blue → cyan → white |
| fractal | classic Mandelbrot escape-time palette |
| turing | green → pale lime (BIO_PALETTE from existing code) |

These palettes already exist in the codebase (check `effects/color.py`, `effects/generative.py`, existing preset code). Reuse them.

---

## Success criteria

1. `uv run pytest` — all existing tests still pass
2. `uv run python scripts/generate_gallery.py --profile 4k` produces:
   - At minimum 10 G09 SVGs with recognizable letter shapes at full 4K density
   - Each fill variant has distinctly different color treatment
   - Density/SDF/shape variants show visible char-level detail across the full grid
3. No G09 SVG has the "noise cluster" problem from the old path
4. Old standard/wide gallery generates identically to before
5. Commit: `feat: G09 as primary 4K render path — all showcase entries via image pipeline`

---

## Implementation notes for Claude

- Use `uv run` for all Python execution
- Do not modify any existing test files
- Run `uv run pytest -q` before committing to confirm zero regressions
- The `_apply_fill_color_to_grid` helper is the core new piece — get it right first, then wire everything else around it
- Print progress during gallery generation so failures are visible
- Check `justdoit/effects/generative.py` for existing palette/color constants before inventing new ones
- The `grid_to_svg()` function in `image_pipeline.py` is the output — pass the colored G09 grid directly to it
