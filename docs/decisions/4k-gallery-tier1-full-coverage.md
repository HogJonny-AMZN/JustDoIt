# ADR: 4K Gallery Tier 1 — Full Sample Coverage

**Date:** 2026-04-24  
**Status:** Approved — implement  
**Goal:** Revive every old gallery sample at full G09 4K quality. Target: ~40 entries covering all fill presets, color variants, and palette combos.

---

## Current state

`_curated_entries_g09()` produces 13 entries across 3 strategies:
- Strategy A: clean-white, clean-cyan, clean-rainbow
- Strategy B (field color): flame, plasma, voronoi, noise, wave, fractal, turing
- Strategy C (char fill): density, sdf, shape

## What needs adding

All additions go inside `_curated_entries_g09()` in `scripts/generate_gallery.py`.
No other files need to change. No new infrastructure needed.

---

## Strategy B extensions — fill presets and palette variants

### How `_apply_fill_color_to_grid` works today

```python
_apply_fill_color_to_grid(base_grid, fill_name, grid_cols, grid_rows, t=0.0, fill_kwargs=None)
```

`fill_name` maps to a `float_grid` generator + `palette`. Add new entries by passing `fill_kwargs` with preset params, and/or a different `palette` override.

### Required: add `palette` override param to `_apply_fill_color_to_grid`

```python
def _apply_fill_color_to_grid(
    base_grid, fill_name, grid_cols, grid_rows,
    t=0.0, fill_kwargs=None,
    palette_override=None,   # NEW — list of (r,g,b) tuples
) -> list:
```

When `palette_override` is not None, use it instead of the fill's default palette. This lets us reuse the same float_grid with different color treatments.

---

## New entries to add

### Flame presets (Strategy B)
The `flame_float_grid` function accepts `preset` kwarg. Pass via `fill_kwargs`.

```python
# Already exists:
("S-G09-flame",        "G09+A08 — Flame (default)",   fill="flame")

# Add:
("S-G09-flame-hot",    "G09+A08 — Flame hot",         fill="flame",   fill_kwargs={"preset": "hot"})
("S-G09-flame-embers", "G09+A08 — Flame embers",      fill="flame",   fill_kwargs={"preset": "embers"})
("S-G09-flame-lava",   "G09+A08 — Flame lava",        fill="flame",   palette_override=LAVA_PALETTE)
```

Note: `flame_cool` preset exists in fill registry — add as:
```python
("S-G09-flame-cool",   "G09+A08 — Flame cool",        fill="flame",   fill_kwargs={"preset": "cool"})
```

### Plasma presets (Strategy B)
`plasma_float_grid` accepts `preset` kwarg.

```python
# Already exists:
("S-G09-plasma",          "G09+A10 — Plasma (default)")

# Add:
("S-G09-plasma-tight",    "G09+A10 — Plasma tight",     fill="plasma",  fill_kwargs={"preset": "tight"})
("S-G09-plasma-slow",     "G09+A10 — Plasma slow",      fill="plasma",  fill_kwargs={"preset": "slow"})
("S-G09-plasma-diagonal", "G09+A10 — Plasma diagonal",  fill="plasma",  fill_kwargs={"preset": "diagonal"})
```

### Voronoi presets (Strategy B)
`voronoi_fill` accepts `preset` kwarg. Use `_fill_to_float_grid` with preset passed through, OR: run the fill and extract float values from char density.

The cleanest approach: extend `_fill_to_float_grid(mask, fill_name, fill_kwargs=None)` to pass kwargs to the underlying voronoi call. Then:

```python
# Already exists:
("S-G09-voronoi",         "G09+F07 — Voronoi (default)")

# Add:
("S-G09-voronoi-cracked", "G09+F07 — Voronoi cracked",  fill="voronoi", fill_kwargs={"preset": "cracked"})
("S-G09-voronoi-fine",    "G09+F07 — Voronoi fine",     fill="voronoi", fill_kwargs={"preset": "fine"})
("S-G09-voronoi-coarse",  "G09+F07 — Voronoi coarse",   fill="voronoi", fill_kwargs={"preset": "coarse"})
("S-G09-voronoi-cells",   "G09+F07 — Voronoi cells",    fill="voronoi", fill_kwargs={"preset": "cells"})
```

### Turing presets (Strategy B)
`turing_float_grid` accepts `preset` kwarg ('stripes', 'spots', 'maze' — check generative.py).

```python
# Already exists (default = stripes):
("S-G09-turing",       "G09+N09 — Turing stripes")

# Add:
("S-G09-turing-spots", "G09+N09 — Turing spots",   fill="turing", fill_kwargs={"preset": "spots"})
("S-G09-turing-maze",  "G09+N09 — Turing maze",    fill="turing", fill_kwargs={"preset": "maze"})
```

### Wave preset (Strategy B)
`wave_fill` accepts `preset` kwarg. Need a `wave_float_grid` or use `_wave_float_inline`.
Add 'moire' preset:

```python
# Already exists:
("S-G09-wave",      "G09+F09 — Wave (default)")

# Add:
("S-G09-wave-moire","G09+F09 — Wave moiré",   fill="wave", fill_kwargs={"preset": "moire"})
```

Check that `_wave_float_inline` or `_apply_fill_color_to_grid` for "wave" passes `fill_kwargs` to the underlying wave call. If not, fix that path to accept kwargs.

### Fractal preset (Strategy B)
`fractal_float_grid` accepts `julia=True` and `julia_c` params.

```python
# Already exists:
("S-G09-fractal",       "G09+F05 — Fractal Mandelbrot")

# Add:
("S-G09-fractal-julia", "G09+F05 — Fractal Julia",   fill="fractal", fill_kwargs={"julia": True, "julia_c": complex(-0.7, 0.27)})
```

### Noise variant (Strategy B)
```python
# Already exists:
("S-G09-noise", "G09+F02 — Noise")

# Add (same float_grid, radial color mapping — brighter at center):
("S-G09-noise-radial", "G09+F02 — Noise + radial",  fill="noise", palette_override=_RADIAL_NOISE_PALETTE)
```

Where `_RADIAL_NOISE_PALETTE` is a cool blue→white palette (already defined as `_NOISE_PALETTE`). The "radial" variant uses a different color computation: distance from grid center drives the palette, not the noise value itself. Implement as a new helper `_apply_radial_color_to_grid(base_grid, float_grid)`.

---

## Strategy A extensions — color palette variants

These all use the same `base_grid` chars, just different color mappings. Pure color work, no fill needed.

### Named palette variants (C03 equivalents)
```python
# Palette-mapped: density of char → palette color
# Space = transparent, chars mapped by their ink density to a palette stop

("S-G09-palette-fire",   "G09+C03 — Fire palette",    palette=FIRE_PALETTE)
("S-G09-palette-lava",   "G09+C03 — Lava palette",    palette=LAVA_PALETTE)
("S-G09-palette-bio",    "G09+C03 — Bio palette",     palette=BIO_PALETTE)
("S-G09-palette-escape", "G09+C03 — Escape palette",  palette=ESCAPE_PALETTE)
```

Implement as `_apply_palette_by_density(base_grid, palette)`:
- For each ink cell, look up its char in a density order string (e.g. `DENSITY_CHARS`)
- Map position in that string → float → palette RGB
- Space cells stay space

### Gradient variants (C01/C02 equivalents)
```python
("S-G09-gradient-horiz",  "G09+C01 — Gradient horizontal",  direction="horizontal")
("S-G09-gradient-diag",   "G09+C01 — Gradient diagonal",    direction="diagonal")
("S-G09-gradient-radial", "G09+C02 — Gradient radial",      direction="radial")
("S-G09-gradient-vert",   "G09+C01 — Gradient vertical",    direction="vertical")
```

Implement as `_apply_gradient_color(base_grid, grid_cols, grid_rows, direction, palette)`:
- "horizontal": `t = col / grid_cols` → palette
- "vertical": `t = row / grid_rows` → palette
- "diagonal": `t = (col/grid_cols + row/grid_rows) / 2`
- "radial": `t = sqrt((col - cols/2)² + (row - rows/2)²) / (max_dim/2)`, clamped [0,1]

Default palette for gradients: `[(0,200,255), (100,50,255), (255,0,200)]` (cyan→purple→magenta).

---

## Strategy C extensions — char fills with color

Currently char fills (density, sdf, shape) use default white color. Add colored variants:

```python
# Already exists (white):
("S-G09-density",  "G09+F01 — Density (hi-res)")
("S-G09-sdf",      "G09+F06 — SDF (hi-res)")
("S-G09-shape",    "G09+F07 — Shape (hi-res)")

# Add colored variants — apply gradient on top of char fill result:
("S-G09-density-fire",  "G09+F01 — Density + fire",   char_fill="density", color="gradient-horiz", palette=FIRE_PALETTE)
("S-G09-sdf-neon",      "G09+F06 — SDF + neon",       char_fill="sdf",     color="gradient-diag",  palette=[(0,255,200),(255,0,255)])
("S-G09-shape-ocean",   "G09+F07 — Shape + ocean",    char_fill="shape",   color="gradient-vert",  palette=[(0,30,120),(0,180,255),(200,240,255)])
```

Implement as `_apply_char_fill_to_grid(base_grid, fill_name, color_fn=None)` extended to accept an optional color function applied after char fill.

---

## Also: previously undiscovered fills — add showcase entries

The fill registry has fills that never had 4K gallery entries. Add at least:

```python
("S-G09-cells",      "G09+F03 — Cellular automata",  fill="cells")
("S-G09-rd",         "G09+F04 — Reaction-diffusion",  fill="rd")
("S-G09-attractor",  "G09+F11 — Strange attractor",   fill="attractor")
("S-G09-slime",      "G09+F12 — Slime mold",          fill="slime")
("S-G09-truchet",    "G09+F13 — Truchet tiles",        fill="truchet")
("S-G09-lsystem",    "G09+F14 — L-system",             fill="lsystem")
```

These use char-replacement fills (no float_grid needed) — use Strategy C path. Each gets white color by default; pick a fitting palette if desired.

---

## Implementation notes for Claude

1. **Add `palette_override` param to `_apply_fill_color_to_grid`** — first thing to do.
2. **Add `fill_kwargs` passthrough to `_fill_to_float_grid`** for voronoi presets.
3. **Add `_apply_gradient_color()`** — simple per-cell position → palette.
4. **Add `_apply_palette_by_density()`** — char position in DENSITY_CHARS → palette.
5. **Check wave kwargs passthrough** — `_wave_float_inline` or equivalent must accept `fill_kwargs`.
6. **Use `uv run pytest -q` before committing** — must be 1046 passed.
7. **Run `uv run python scripts/generate_gallery.py --profile 4k --text "JUST DO IT"`** to verify all entries generate without error.
8. All new helpers go in `scripts/generate_gallery.py` — no changes to `justdoit/` package files.
9. Target: **~40 entries total** (13 existing + ~27 new).
10. Commit: `feat: 4K gallery tier 1 — full sample coverage, all presets and palette variants`

---

## Reference — existing helper functions available in generate_gallery.py

```python
_g09_grid_to_mask(base_grid)                          # → GlyphMask
_apply_fill_color_to_grid(base_grid, fill_name, ...)  # → colored grid (Strategy B)
_apply_char_fill_to_grid(base_grid, fill_name, ...)   # → char-filled grid (Strategy C)
_grid_rainbow_color(base_grid)                         # → rainbow colored grid
_lerp_palette_rgb(palette, t)                          # → (r,g,b)
```

## Reference — palette constants available

```python
from justdoit.effects.color import FIRE_PALETTE, LAVA_PALETTE, BIO_PALETTE, ESCAPE_PALETTE, SPECTRAL_PALETTE
```

## Reference — fill names in _FILL_FNS (Strategy C — char replacement)
```
density, sdf, shape, cells, rd, attractor, slime, truchet, lsystem, noise, wave, fractal, voronoi, voronoi_cracked, voronoi_fine, voronoi_coarse, voronoi_cells, plasma, plasma_tight, plasma_slow, plasma_diagonal, flame, flame_hot, flame_cool, flame_embers, turing
```
