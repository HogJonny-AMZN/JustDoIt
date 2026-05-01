"""
debug_pipeline.py — Visual pipeline inspector for JustDoIt 4K rendering.

Saves PNG snapshots at each stage so you can see exactly what's happening.

Usage:
    uv run python scripts/debug_pipeline.py

Outputs to: debug/
  00_pil_canvas.png         — raw PIL render (white text on black, 3840x2160)
  01_ascii_grid_chars.png   — image_to_ascii result, chars rendered back to pixels
  02_ascii_grid_zoom.png    — zoomed 10x crop of letter interior (see actual chars)
  03_fill_flame.png         — flame colorize applied to grid, rendered to PNG
  04_fill_plasma.png        — plasma colorize applied to grid, rendered to PNG
  05_spatial_sine_warp.png  — PIL sine warp transform (pre-sampling)
  06_spatial_shear.png      — PIL shear transform (pre-sampling)
  07_spatial_iso.png        — PIL isometric (pre-sampling)
  08_sine_warp_sampled.png  — sine warp after image_to_ascii (chars rendered)
"""

import sys
import os
import time
from pathlib import Path

# ensure project root on path
sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("PYTHONPATH", str(Path(__file__).parent.parent))

from PIL import Image, ImageDraw, ImageFont

from justdoit.core.image_pipeline import render_text_to_pil, render_text_as_image
from justdoit.core.image_sampler import image_to_ascii_fast
from justdoit.layout import find_default_ttf

# ── config ────────────────────────────────────────────────────────────────────
TEXT       = "JUST DO IT"
CANVAS_W   = 3840
CANVAS_H   = 2160
CELL_W     = 8
CELL_H     = 16
GRID_COLS  = CANVAS_W // CELL_W   # 960
GRID_ROWS  = CANVAS_H // CELL_H   # 270
OUT_DIR    = Path(__file__).parent.parent / "debug"
OUT_DIR.mkdir(exist_ok=True)

FONT_PATH  = find_default_ttf()
if FONT_PATH is None:
    print("ERROR: no system TTF found")
    sys.exit(1)

print(f"Canvas: {CANVAS_W}x{CANVAS_H}")
print(f"Cell:   {CELL_W}x{CELL_H}px  →  grid {GRID_COLS}x{GRID_ROWS} = {GRID_COLS*GRID_ROWS:,} cells")
print(f"Font:   {FONT_PATH}")
print()


def save(img: Image.Image, name: str, label: str = "") -> None:
    path = OUT_DIR / name
    img.save(str(path))
    kb = path.stat().st_size // 1024
    print(f"  saved {name}  ({img.size[0]}x{img.size[1]}px, {kb}KB)  {label}")


def crop_to_content(img: Image.Image, pad: int = 40) -> Image.Image:
    """Crop image to non-black bounding box + padding."""
    import numpy as np
    arr = np.array(img.convert("L"))
    rows = np.any(arr > 10, axis=1)
    cols = np.any(arr > 10, axis=0)
    if not rows.any():
        return img
    r0, r1 = np.where(rows)[0][[0, -1]]
    c0, c1 = np.where(cols)[0][[0, -1]]
    r0 = max(0, r0 - pad)
    r1 = min(img.height, r1 + pad)
    c0 = max(0, c0 - pad)
    c1 = min(img.width, c1 + pad)
    return img.crop((c0, r0, c1, r1))


def normalize(img: Image.Image) -> Image.Image:
    """Auto-levels: stretch per-channel min/max to 0-255."""
    import numpy as np
    arr = np.array(img).astype(float)
    out = np.zeros_like(arr)
    for c in range(arr.shape[2]):
        ch = arr[:, :, c]
        lo, hi = ch.min(), ch.max()
        if hi > lo:
            out[:, :, c] = (ch - lo) / (hi - lo) * 255
        else:
            out[:, :, c] = ch
    return Image.fromarray(out.astype('uint8'))


def debug_save(img: Image.Image, name: str, label: str = "",
               scale_to: int = 1920, do_normalize: bool = False) -> None:
    """Crop to content, optionally normalize, scale to target width, save."""
    cropped = crop_to_content(img)
    if do_normalize:
        cropped = normalize(cropped)
    # Scale to target width preserving aspect ratio
    w, h = cropped.size
    if w > scale_to:
        nh = int(h * scale_to / w)
        cropped = cropped.resize((scale_to, nh), Image.LANCZOS)
    save(cropped, name, label)


def grid_to_png(
    grid: list,
    cell_w: int = CELL_W,
    cell_h: int = CELL_H,
    bg: tuple = (17, 17, 17),
) -> Image.Image:
    """Render an (char, rgb) grid back to a PIL image for visual inspection."""
    rows = len(grid)
    cols = max(len(r) for r in grid) if rows else 0
    img = Image.new("RGB", (cols * cell_w, rows * cell_h), bg)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSansMono.ttf", cell_h - 1)
    except Exception:
        font = ImageFont.load_default()
    for r, row in enumerate(grid):
        for c, (ch, rgb) in enumerate(row):
            if ch != " " and rgb:
                draw.text((c * cell_w, r * cell_h), ch, fill=rgb, font=font)
    return img


# ── Stage 0: PIL canvas ───────────────────────────────────────────────────────
print("Stage 0: PIL canvas render ...")
t0 = time.time()
pil_canvas = render_text_to_pil(TEXT, FONT_PATH, CANVAS_W, CANVAS_H)
print(f"  render_text_to_pil: {time.time()-t0:.2f}s")
debug_save(pil_canvas, "00_pil_canvas.png", "PIL canvas — cropped to text bbox")


# ── Stage 1: image_to_ascii sampling ─────────────────────────────────────────
print("\nStage 1: image_to_ascii_fast sampling ...")
t0 = time.time()
base_grid = image_to_ascii_fast(pil_canvas, CELL_W, CELL_H, color=False)
print(f"  image_to_ascii_fast: {time.time()-t0:.3f}s  →  {len(base_grid[0])}x{len(base_grid)} grid")

# Render chars as white on black
white_grid = [[(ch, (220, 220, 220) if ch != " " else None) for ch, _ in row] for row in base_grid]
grid_img = grid_to_png(white_grid)
# Crop to text content so it's not black
debug_save(grid_img, "01_ascii_grid.png", "ASCII grid — cropped to text")

# Zoom crop: find ink bbox, crop to letter region, scale up so individual chars are legible
ink_rows = [r for r, row in enumerate(base_grid) if any(ch != " " for ch, _ in row)]
ink_cols = [c for row in base_grid for c, (ch, _) in enumerate(row) if ch != " "]
if ink_rows and ink_cols:
    r0, r1 = min(ink_rows), max(ink_rows)
    c0, c1 = min(ink_cols), max(ink_cols)
    # Crop to a window covering ~1/3 of the text width at the centre
    cr0 = r0
    cr1 = r1
    width_third = (c1 - c0) // 3
    cc0 = c0 + width_third
    cc1 = cc0 + width_third
    crop_grid = [row[cc0:cc1] for row in base_grid[cr0:cr1]]
    crop_white = [[(ch, (220,220,220) if ch != " " else None) for ch,_ in row] for row in crop_grid]
    crop_img = grid_to_png(crop_white)
    # Scale up 6x NEAREST so individual chars are pixel-readable
    zoom = crop_img.resize((crop_img.width * 6, crop_img.height * 6), Image.NEAREST)
    save(zoom, "02_ascii_grid_zoom.png", f"Zoom 6x: centre third of text, cells [{cc0}:{cc1}, {cr0}:{cr1}]")


# ── Stage 2: fill color strategies ───────────────────────────────────────────
print("\nStage 2: fill color strategies ...")

# Import gallery helpers
sys.path.insert(0, str(Path(__file__).parent))
from generate_gallery import _apply_fill_color_to_grid, _g09_grid_to_mask

for fill_name in ["flame", "plasma", "voronoi", "turing"]:
    t0 = time.time()
    colored = _apply_fill_color_to_grid(base_grid, fill_name, GRID_COLS, GRID_ROWS)
    elapsed = time.time() - t0
    img = grid_to_png(colored)
    idx = {"flame": "03", "plasma": "04", "voronoi": "05", "turing": "06"}[fill_name]
    debug_save(img, f"{idx}_fill_{fill_name}.png", f"{fill_name} fill ({elapsed:.2f}s) — cropped")


# ── Stage 3: spatial transforms ──────────────────────────────────────────────
print("\nStage 3: spatial transforms (PIL image space) ...")
sys.path.insert(0, str(Path(__file__).parent))
from generate_gallery import _pil_sine_warp, _pil_shear, _pil_isometric

for name, fn in [
    ("sine_warp", lambda img: _pil_sine_warp(img)),
    ("shear",     lambda img: _pil_shear(img)),
    ("iso",       lambda img: _pil_isometric(img)),
]:
    idx = {"sine_warp": "07", "shear": "08", "iso": "09"}[name]

    # Stage 3a: transformed PIL image (before sampling) — crop to content
    t0 = time.time()
    transformed_pil = fn(pil_canvas)
    elapsed_transform = time.time() - t0
    debug_save(transformed_pil, f"{idx}_spatial_{name}_pil.png",
               f"PIL transform ({elapsed_transform:.2f}s) — cropped")

    # Stage 3b: transformed PIL → image_to_ascii → grid rendered as PNG — crop to content
    t0 = time.time()
    xgrid = image_to_ascii_fast(transformed_pil, CELL_W, CELL_H, color=False)
    elapsed_sample = time.time() - t0
    xwhite = [[(ch, (220,220,220) if ch != " " else None) for ch,_ in row] for row in xgrid]
    ximg = grid_to_png(xwhite)
    debug_save(ximg, f"{idx}_spatial_{name}_sampled.png",
               f"After sampling ({elapsed_sample:.3f}s) — cropped")


print(f"\nAll debug images saved to: {OUT_DIR}/")
print("Open the debug/ folder to inspect each stage.")
