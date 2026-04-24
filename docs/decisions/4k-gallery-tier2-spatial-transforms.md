# ADR: 4K Gallery Tier 2 — Spatial Transforms in Image Space

**Date:** 2026-04-24  
**Status:** Approved — implement  
**Goal:** Revive S01 sine warp, S02 perspective tilt, S08 shear, and S03 isometric
extrude at full G09 4K quality by applying transforms in PIL image space before
G09 sampling — instead of operating on char grids.

---

## Why image-space transforms

The existing spatial effects (spatial.py, isometric.py) operate on rendered ANSI
strings — they shift/compress/duplicate rows of characters. At 4K with G09 the
rendered output is a `list[list[(char,rgb)]]` grid, not a string, so the old path
can't be reused directly.

The better approach: apply the geometric transform to the **PIL image** (white text
on black, `canvas_w × canvas_h` pixels) before calling `image_to_ascii()`. PIL has
native affine, perspective, and arbitrary pixel-mapping transforms. The result is:

- G09-quality edge sharpness on the transformed output
- Transforms operate at full pixel resolution (smooth subpixel interpolation)
- Single unified pipeline: transform → sample → grid → SVG

---

## New helper: `_pil_transform_text_image(img, transform, **kwargs) -> PIL.Image`

Add to `scripts/generate_gallery.py`. Takes a PIL Image (the rendered text canvas)
and returns a transformed PIL Image of the same size, ready for `image_to_ascii()`.

All transforms operate in-place on the canvas. Background fill is black `(0,0,0)`.

---

## Transforms to implement

### T1 — Sine warp (S01)

Per-row horizontal pixel shift driven by a sine function.

```python
def _pil_sine_warp(img, amplitude=0.08, frequency=1.5):
    """
    Shift each row of pixels horizontally by: offset = amplitude * canvas_w * sin(row/h * 2π * frequency)
    amplitude: fraction of canvas_w (default 0.08 = 8% of width)
    frequency: cycles across full height (default 1.5)
    Returns new PIL.Image same size, black background.
    """
```

Implementation: iterate rows, use `PIL.Image.transform` or numpy roll per row.
With numpy: `np_arr[row] = np.roll(np_arr[row], offset, axis=0)`.
Pure-Python fallback: crop each row as a 1px-tall strip and paste at offset.

### T2 — Perspective tilt (S02)

PIL perspective transform — vanishing point at top or bottom.

```python
def _pil_perspective_tilt(img, strength=0.25, direction="top"):
    """
    Apply a perspective (keystone) distortion.
    direction="top": top edge narrows (vanishes upward)
    direction="bottom": bottom edge narrows
    strength: 0.0 (none) → 1.0 (extreme), default 0.25

    Uses PIL.Image.transform(PERSPECTIVE, coefficients).
    Perspective coefficients map destination pixel (x,y) → source pixel.
    For "top" narrow: source x = x + (strength * (h-y)/h) * (x - w/2)
    """
```

PIL `PERSPECTIVE` transform takes 8 coefficients `(a,b,c,d,e,f,g,h)` mapping:
`src_x = (a*dst_x + b*dst_y + c) / (g*dst_x + h*dst_y + 1)`
`src_y = (d*dst_x + e*dst_y + f) / (g*dst_x + h*dst_y + 1)`

For "top" taper:
- top-left maps to `(w*strength/2, 0)`, top-right to `(w*(1-strength/2), 0)`
- bottom-left maps to `(0, h)`, bottom-right to `(w, h)`
Use `PIL.Image.transform(size, Image.PERSPECTIVE, coefficients, Image.BILINEAR)`.

### T3 — Shear (S08)

Horizontal shear — each row shifted right proportionally to its vertical position.

```python
def _pil_shear(img, amount=0.15, direction="right"):
    """
    Shear: each row r shifts by: offset = amount * canvas_w * (r / h)
    direction="right": bottom shifts right (italic lean)
    direction="left": bottom shifts left
    amount: fraction of canvas_w per full height (default 0.15)
    Returns PIL.Image, same canvas size, black background.
    """
```

Implementation: PIL affine transform.
Affine matrix for shear-x: `[[1, shear_x, 0], [0, 1, 0]]`
where `shear_x = amount * canvas_w / canvas_h` per pixel row.
Use `PIL.Image.transform(size, Image.AFFINE, (1, shear_x, -shear_x*h/2, 0, 1, 0))`.
The translation term `-shear_x*h/2` centers the shear so the middle row stays fixed.

### T4 — Isometric extrude (S03)

Most complex. Render TWO PIL images: the front face and an offset extrusion layer,
then composite them before sampling.

```python
def _pil_isometric(text_img, depth_fraction=0.04, direction="right"):
    """
    Create isometric extrusion effect in image space.

    depth_fraction: extrusion depth as fraction of canvas_w (default 0.04 = ~150px at 4K)
    direction: "right" (depth goes up-right) or "left" (up-left)

    Algorithm:
      depth_px = int(depth_fraction * canvas_w)
      canvas_out = canvas_w + depth_px, canvas_h + depth_px  (expand to fit)

      1. Place 'front face' (text_img) at offset (0, depth_px) — shifted down
      2. For each depth step d in 1..depth_px:
           offset_x = d if direction=="right" else -d
           offset_y = -d  (up)
           alpha = max(0.3, 1.0 - d/depth_px)  — fade depth layers
           paste text_img at (offset_x, depth_px + offset_y) with alpha
      3. Composite back-to-front (furthest first, front face last)
      4. Crop back to canvas_w x canvas_h

    Color: depth layers use a dim version of the text (multiply brightness).
    Returns PIL.Image ready for image_to_ascii().
    """
```

Simpler alternative (still good visual): just render two versions of the text —
one normal (front face) and one dim/shifted (depth face) — and composite:

```python
    # Shift the text image by (depth_px, -depth_px) to create depth layer
    depth_img = text_img.transform(text_img.size, Image.AFFINE,
                                   (1, 0, -depth_px, 0, 1, depth_px))
    # Darken depth layer
    depth_img = ImageEnhance.Brightness(depth_img).enhance(0.4)
    # Composite: depth behind, front on top
    out = Image.new("RGB", text_img.size, (0,0,0))
    out.paste(depth_img, (0,0))
    out.paste(text_img, (0,0), mask=text_img.convert("L"))
    return out
```

---

## New gallery entries to add in `_curated_entries_g09()`

### Strategy D — image-space transforms (new strategy)

```python
print("    G09 Strategy D: spatial transforms ...")

# Base text image — white text on black, full canvas resolution
# Already computed as part of render_text_as_image internals.
# Need to expose it — add a helper: _render_text_to_pil(text, font_path, canvas_w, canvas_h)
# that returns the PIL.Image before image_to_ascii() is called.

# Sine warp variants
("S-G09-sine-warp",         "G09+S01 — Sine warp",              transform="sine_warp")
("S-G09-sine-warp-deep",    "G09+S01 — Sine warp (deep)",       transform="sine_warp",    kwargs={"amplitude": 0.14})
("S-G09-sine-warp-fast",    "G09+S01 — Sine warp (fast)",       transform="sine_warp",    kwargs={"frequency": 3.0})

# Perspective variants
("S-G09-perspective-top",   "G09+S02 — Perspective (top)",      transform="perspective",  kwargs={"direction": "top"})
("S-G09-perspective-bottom","G09+S02 — Perspective (bottom)",   transform="perspective",  kwargs={"direction": "bottom"})

# Shear variants
("S-G09-shear-right",       "G09+S08 — Shear right",            transform="shear",        kwargs={"direction": "right"})
("S-G09-shear-left",        "G09+S08 — Shear left",             transform="shear",        kwargs={"direction": "left"})

# Isometric
("S-G09-iso-right",         "G09+S03 — Isometric (right)",      transform="iso",          kwargs={"direction": "right"})
("S-G09-iso-left",          "G09+S03 — Isometric (left)",       transform="iso",          kwargs={"direction": "left"})

# Combos — transform + color
("S-G09-sine-warp-rainbow", "G09+S01+C — Sine warp + rainbow",  transform="sine_warp",    post_color="rainbow")
("S-G09-iso-flame",         "G09+S03+A08 — Iso + flame",        transform="iso",          post_fill="flame")
("S-G09-shear-plasma",      "G09+S08+A10 — Shear + plasma",     transform="shear",        post_fill="plasma")
```

---

## New helpers needed in `scripts/generate_gallery.py`

### `_render_text_to_pil(text, font_path, canvas_w, canvas_h, fg, bg) -> PIL.Image`

Extracts the PIL image generation step from `render_text_as_image()` so transforms
can be applied before sampling.

```python
def _render_text_to_pil(
    text: str,
    font_path: str,
    canvas_w: int,
    canvas_h: int,
    fg_color: tuple = (255, 255, 255),
    bg_color: tuple = (0, 0, 0),
) -> "PIL.Image.Image":
    """Render text to a PIL image at canvas resolution. No sampling yet."""
```

This duplicates the first half of `render_text_as_image()`. Either extract it from
`image_pipeline.py` (preferred — add as a public function there) or reimplement
inline in generate_gallery.py.

**Preferred:** add `render_text_to_pil()` to `justdoit/core/image_pipeline.py` as a
new public function. This is a clean extension — not a behavior change.

### `_pil_to_g09_grid(pil_img, cell_w, cell_h, color=True) -> list`

Thin wrapper: `image_to_ascii(pil_img, cell_w, cell_h, color=color)`. Already exists
as `render_pil_image_as_ascii()` in image_pipeline.py — use that.

### `_pil_sine_warp(img, amplitude, frequency) -> PIL.Image`
### `_pil_perspective_tilt(img, strength, direction) -> PIL.Image`
### `_pil_shear(img, amount, direction) -> PIL.Image`
### `_pil_isometric(img, depth_fraction, direction) -> PIL.Image`

All in `scripts/generate_gallery.py` (pure gallery scripts — not part of the package).

### `_g09_transform_entry(text_pil, transform_fn, cell_w, cell_h, post_color=None, post_fill=None) -> list`

Orchestrator:
```python
def _g09_transform_entry(text_pil, transform_fn, cell_w, cell_h,
                          post_color=None, post_fill=None, fill_kwargs=None):
    transformed = transform_fn(text_pil)
    grid = render_pil_image_as_ascii(transformed, cell_w, cell_h, color=False)
    if post_fill:
        grid = _apply_fill_color_to_grid(grid, post_fill, len(grid[0]), len(grid), fill_kwargs=fill_kwargs)
    elif post_color == "rainbow":
        grid = _grid_rainbow_color(grid)
    else:
        grid = _apply_uniform_color(grid, (220, 220, 220))  # default near-white
    return grid
```

---

## Files to modify

```
MODIFY:
  justdoit/core/image_pipeline.py   — add render_text_to_pil() public function
  scripts/generate_gallery.py       — add Strategy D helpers + entries

NO CHANGES:
  justdoit/effects/spatial.py       — untouched (old string path kept for standard/wide)
  justdoit/effects/isometric.py     — untouched
  all test files                    — must stay green
```

---

## Implementation order for Claude

1. Add `render_text_to_pil()` to `justdoit/core/image_pipeline.py`
2. Add `_pil_sine_warp()`, `_pil_perspective_tilt()`, `_pil_shear()`, `_pil_isometric()` to `generate_gallery.py`
3. Add `_g09_transform_entry()` orchestrator
4. Wire Strategy D entries into `_curated_entries_g09()`
5. Run `uv run pytest -q` — must be 1046 passed (only image_pipeline.py changed in package)
6. Run `uv run python scripts/generate_gallery.py --profile 4k --text "JUST DO IT"` — verify ~58 entries generate without error
7. Commit: `feat: 4K gallery tier 2 — spatial transforms in image space (S01/S02/S03/S08)`

---

## Success criteria

1. `uv run pytest -q` — 1046 passed (plus any new tests for `render_text_to_pil`)
2. 4K gallery generates ~58 SVGs cleanly (46 existing + 12 new spatial entries)
3. Sine warp shows visible wave distortion of letters at 4K
4. Perspective shows visible keystone/taper
5. Shear shows visible italic lean
6. Isometric shows visible 3D extrusion face
7. Combos (iso+flame, shear+plasma) show both transform and color effect
8. No existing entries regress
