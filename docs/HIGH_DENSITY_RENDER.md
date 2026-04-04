# High-Density Render — Feature Design

**Created:** 2026-04-04  
**Authors:** NumberOne + Jonny Galloway  
**Status:** Ready to implement  

---

## The Idea

The existing size/scale work made the *pixels bigger* — the same 64-column
character grid rendered at a larger font size. That is not the goal.

The goal is **more characters per letter** — so fill effects (Voronoi, Turing,
plasma, fractal, flame) have many more cells to work with inside each glyph.
A block-font "J" has ~42 cells. A TTF-rasterized "J" at 72pt has ~4,176 cells.
The difference is not cosmetic — it's the difference between 4 Voronoi seed
points and 60, between a Turing pattern that barely starts and one that forms
a full biological coat pattern.

The mechanism: the **TTF rasterizer** already scales with `font_size`. Larger
`font_size` → larger glyphs in character-cell space → more cells per letter
→ richer fills.

**The user workflow:**
```
# Terminal at 8pt font, 800 columns wide:
justdoit "JUST DO IT" --hd 800 --fill voronoi --color rainbow
```
`--hd 800` means: "I have 800 terminal columns — rasterize the font at
whatever size fills that width". JustDoIt computes the TTF size, loads the
font, renders with the fill, and outputs to stdout.

---

## The Math

From measured data (DejaVuSans):
```
TTF size=12pt → 110 cols for "JUST DO IT"   (9.17 cols/pt)
TTF size=24pt → 200 cols                     (8.33 cols/pt)
TTF size=48pt → 390 cols                     (8.13 cols/pt)
TTF size=72pt → 590 cols                     (8.19 cols/pt)
```

Ratio is ~8.2 cols per pt — stable enough to invert:
```
ttf_size = target_cols / cols_per_pt_ratio
```

But the correct approach is a binary search using actual `measure()` calls,
since the ratio varies by font and by text content.

**Target scenarios on Jonny's setup:**

| Terminal config | Cols | TTF size | Cells per glyph |
|----------------|------|----------|----------------|
| 5120×1440 @ 6pt | 1066 | ~116pt | ~10,000+ |
| 5120×1440 @ 10pt | 640 | ~70pt | ~3,900 |
| 3840×2160 @ 8pt | 800 | ~87pt | ~6,000 |
| 3840×2160 @ 12pt | 400 | ~43pt | ~1,400 |

At 87pt per glyph, every fill effect operates at a resolution where:
- Voronoi: 40–60 seed points, visible cell structure
- Turing: 2–3 full pattern wavelengths, clear stripes/spots  
- Fractal: fine escape-time detail, smooth banding
- Plasma: multiple full sin cycles, smooth morphing
- Flame: tall heat column with visible cooling gradient

---

## What changes

### New CLI flag: `--hd [COLS]`

```bash
# Auto-detect terminal width:
justdoit "JUST DO IT" --hd --fill voronoi

# Explicit column target:
justdoit "JUST DO IT" --hd 800 --fill voronoi

# With a specific TTF font:
justdoit "JUST DO IT" --hd 800 --ttf /path/to/font.ttf --fill flame
```

`--hd` without a value: read terminal width via `terminal_size()`, use 90%
of it as the target (leave margin for bloom/iso headroom).

`--hd N`: use N as the target column count.

### New `layout.py` function: `fit_ttf_size()`

```python
def fit_ttf_size(
    text: str,
    target_cols: int,
    font_path: str,
    gap: int = 1,
    iso_depth: int = 0,
    bloom_radius: int = 0,
    size_min: int = 8,
    size_max: int = 200,
) -> int:
    """Find the largest TTF rasterization size where text fits within target_cols.

    Binary searches over font_size values, loading the font at each candidate
    size and calling measure() to check the rendered width.

    :param text: Text to render.
    :param target_cols: Maximum terminal columns to fit within.
    :param font_path: Path to TTF/OTF font file.
    :param gap: Character gap (default: 1).
    :param iso_depth: Isometric depth footprint (default: 0).
    :param bloom_radius: Bloom halo margin (default: 0).
    :param size_min: Minimum font size to try (default: 8).
    :param size_max: Maximum font size to try (default: 200).
    :returns: Optimal font_size as integer.
    :raises ValueError: If even size_min doesn't fit, or font cannot be loaded.
    """
```

Binary search: load font at candidate size, measure, adjust. Converges in
~7 iterations for a range of 8–200.

**Caching:** `rasterize_ttf()` is expensive — 100+ glyphs rendered via Pillow
each call. The binary search must cache: if we already measured size=48, don't
re-rasterize at size=48.

```python
_ttf_size_cache: dict[tuple[str, int], tuple[int, int]] = {}
# key: (font_path, font_size), value: (cols, rows) for the standard text
```

Or simpler: do a linear scan with coarse steps first (every 8pt), then narrow:
```
Pass 1: sizes = [8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 96, 112, 128]
         → find last size where cols <= target
Pass 2: binary search between that size and next step
```
Total: ~15 rasterizations max. Each takes ~0.1s → ~1.5s startup. Acceptable.

### Default font

`--hd` without `--ttf` should have a default. Options:
1. Fall back to block font and warn (wrong — defeats the purpose)
2. Require `--ttf` explicitly (annoying)
3. Use the first available system TTF (fragile)
4. Bundle a single permissively-licensed monospace font (best)

**Recommendation:** Bundle one font. DejaVu Sans Mono is MIT-compatible, widely
used, renders cleanly at all sizes. Add it to `justdoit/fonts/bundled/`.
Or: check for common system paths and use the first found, with a clear error
if none exist. Document the paths checked.

For v1: require `--ttf` with `--hd`, provide `--list-fonts` output showing
system fonts found. Add bundled font in a follow-up.

### Gallery high-density profile

New gallery profile `hd`:
```python
"hd": GalleryProfile(
    name="hd",
    svg_font_size=14,      # SVG rendering: standard pixel size
    ttf_size=72,           # TTF rasterization: 72pt per glyph
    readme_img_width=0,    # natural SVG size
    output_dir=...,
    text="JUST DO IT",
    ttf_path=None,         # use bundled/system font
),
```

The `hd` profile renders with TTF at 72pt (590 cols, ~4000 cells/glyph) and
saves SVGs at standard pixel size. The SVGs will be wider (590 cols × 14px ≈
3395px) but that's fine — they're viewed at natural size.

---

## Implementation Plan

### Phase 1: `fit_ttf_size()` in layout.py (~50 lines)

```python
def fit_ttf_size(text, target_cols, font_path, gap=1, iso_depth=0, 
                 bloom_radius=0, size_min=8, size_max=200) -> int:
```

Algorithm:
1. Coarse scan: try sizes [8, 16, 24, ..., size_max] in steps of 8
2. Find last size where measure(text, font=loaded_font, gap=gap, ...) <= target_cols
3. Fine binary search between that size and the next step
4. Cache results: `(font_path, size)` → `(cols, rows)` so each size only
   loads once per call

Needs Pillow — gate with `try: from justdoit.fonts.ttf import load_ttf_font`.
Raise `ImportError` with install hint if missing.

Add tests to `tests/test_layout.py`:
- `test_fit_ttf_size_returns_int`
- `test_fit_ttf_size_output_fits_target`
- `test_fit_ttf_size_larger_than_min`
- `test_fit_ttf_size_requires_pillow_or_skips`

### Phase 2: `--hd` CLI flag (~30 lines)

```bash
justdoit "JUST DO IT" --hd [COLS] [--ttf PATH] --fill voronoi
```

Handler:
```python
if args.hd is not None:
    from justdoit.layout import fit_ttf_size, terminal_size
    ttf_path = args.ttf or _find_default_ttf()
    target = args.hd if args.hd > 0 else int(terminal_size()[0] * 0.9)
    ttf_size = fit_ttf_size(args.text, target, ttf_path, gap=args.gap,
                            iso_depth=args.iso or 0)
    font_name = load_ttf_font(ttf_path, font_size=ttf_size)
    # font_name is now used for render() instead of args.font
```

`--hd` takes an optional integer (`nargs='?'`, `const=0` meaning "auto-detect"):
```python
parser.add_argument(
    "--hd", type=int, nargs="?", const=0, default=None, metavar="COLS",
    help="High-density render: rasterize font to fill COLS terminal columns "
         "(default: auto-detect terminal width). Requires --ttf or a system font.",
)
```

### Phase 3: HD gallery profile (~20 lines)

Add `hd` profile to `PROFILES` dict. Requires TTF. Generate on-demand:
```bash
python scripts/generate_gallery.py --profile hd --ttf /path/to/font.ttf
```

---

## What the output looks like

At TTF size=72pt, "JUST DO IT" renders as 590×72 character grid. The fill
effects operating at that resolution:

**Voronoi cracked at 72pt:** The "JUST" glyph has ~3000 interior cells.
The cracked preset generates `sqrt(3000) × 1.2 ≈ 66 seed points`. Each
Voronoi cell is ~45 chars across — visible, distinct regions with sharp
border chars. At 14pt block font you get 4–5 seeds and can barely see cells.

**Turing stripes at 72pt:** The simulation runs on a 72×58 upscaled mask
(scale factor 4 = 288×232 grid). At 4× scale that's enough for 3–5 full
stripe wavelengths across the glyph. At block font you get half a wavelength.

**Fractal at 72pt:** Each escape-time sample covers ~1/3000 of the view
window instead of ~1/42. Fine detail in the Mandelbrot boundary becomes
visible — actual filaments rather than aliased blobs.

**Flame at 72pt:** The heat propagation grid is 72 rows tall instead of 7.
The cooling gradient is gradual and visible — you can see the flame dying
back from a hot base to cooler tips across tens of rows.

---

## The render pipeline at HD

```
terminal_size() → 800 cols
fit_ttf_size("JUST DO IT", 800, font.ttf) → 87pt
load_ttf_font(font.ttf, font_size=87) → "font_87"  (87×N char glyphs)
render("JUST DO IT", font="font_87", fill="voronoi") → 800×87 char grid
print_art(output)  → prints to terminal
```

The terminal at 8pt font with 800 columns has 87 lines visible vertically.
The render is exactly 87 rows tall. It fills the screen.

---

*Implement Phase 1 first — `fit_ttf_size()` is the enabler. Once that exists,
Phases 2 and 3 are straightforward wires.*
