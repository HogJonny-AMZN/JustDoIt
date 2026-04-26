"""
generate_4k_anim.py — 4K animated PNG generator for JustDoIt G09 effects.

Renders frame sequences at 3840x2160 using the G09 image pipeline (PIL text
render -> image_to_ascii_fast -> PIL PNG render) and saves as APNG.

Usage:
    uv run python scripts/generate_4k_anim.py --effect fractal-julia
    uv run python scripts/generate_4k_anim.py --effect plasma --frames 60
    uv run python scripts/generate_4k_anim.py --list

Output: docs/anim_gallery_4k/<effect>.apng  (3840x2160, 8x16px cells)
"""

import argparse
import io
import math
import string
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Config ────────────────────────────────────────────────────────────────────
TEXT       = "JUST DO IT"
CANVAS_W   = 3840
CANVAS_H   = 2160
CELL_W     = 8
CELL_H     = 16
GRID_COLS  = CANVAS_W // CELL_W   # 480
GRID_ROWS  = CANVAS_H // CELL_H   # 135
CHARSET    = "█▓▒░" + string.printable[:95]
OUT_DIR    = Path(__file__).parent.parent / "docs" / "anim_gallery_4k"
FPS        = 12.0


def _build_base_grid(font_scale: float = 1.0):
    """Render TEXT to a 480x135 ASCII grid using G09 image pipeline.

    font_scale=1.0: largest font that fits the canvas with margins (95% rule).
    Text is centered in the 3840x2160 canvas with proper padding on all sides.
    Higher font_scale clips letters — stay at 1.0.
    """
    from justdoit.core.image_pipeline import render_text_as_image
    from justdoit.layout import find_default_ttf
    font = find_default_ttf()
    return render_text_as_image(
        TEXT, font,
        output_cols=GRID_COLS, output_rows=GRID_ROWS,
        cell_w=CELL_W, cell_h=CELL_H,
        charset=CHARSET, color=False,
        font_scale=font_scale,
    )


def _grid_to_png_bytes(grid: list, font=None) -> bytes:
    """Render (char, rgb) grid to 3840x2160 PNG bytes."""
    from PIL import Image, ImageDraw, ImageFont
    rows = len(grid)
    cols = max(len(r) for r in grid) if rows else 0
    img = Image.new("RGB", (cols * CELL_W, rows * CELL_H), (17, 17, 17))
    draw = ImageDraw.Draw(img)
    if font is None:
        try:
            font = ImageFont.truetype("DejaVuSansMono.ttf", CELL_H - 1)
        except Exception:
            font = ImageFont.load_default()
    for r, row in enumerate(grid):
        for c, (ch, rgb) in enumerate(row):
            if ch != " " and rgb:
                draw.text((c * CELL_W, r * CELL_H), ch, fill=rgb, font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False)
    return buf.getvalue()


def _lerp_palette(palette: list, t: float) -> tuple:
    """Interpolate between palette stops."""
    if not palette:
        return (255, 255, 255)
    t = max(0.0, min(1.0, t))
    if len(palette) == 1:
        return tuple(palette[0])
    seg = t * (len(palette) - 1)
    i = min(int(seg), len(palette) - 2)
    f = seg - i
    r0, g0, b0 = palette[i]
    r1, g1, b1 = palette[i + 1]
    return (int(r0 + (r1 - r0) * f), int(g0 + (g1 - g0) * f), int(b0 + (b1 - b0) * f))


# ── Effect definitions ────────────────────────────────────────────────────────
def effect_fractal_julia(n_frames: int = 72) -> list:
    """Julia set with rotating c parameter — letter geometry constant, fractal rotates."""
    from justdoit.core.glyph import mask_to_sdf
    from justdoit.effects.generative import fractal_float_grid
    from justdoit.effects.color import ESCAPE_PALETTE

    print(f"  Computing G09 base grid...")
    t0 = time.time()
    base_grid = _build_base_grid()
    print(f"  Base grid: {time.time()-t0:.2f}s")

    # Binary mask of ink cells
    mask = [[1.0 if ch != " " else 0.0 for ch, _ in row] for row in base_grid]

    # Precompute fractal float grids for each frame (julia_c rotates around a circle)
    print(f"  Precomputing {n_frames} fractal frames...")
    float_grids = []
    for i in range(n_frames):
        phase = 2 * math.pi * i / n_frames
        # Orbit around a classic julia set region
        angle = phase
        radius = 0.7885
        c = complex(radius * math.cos(angle), radius * math.sin(angle))
        t0 = time.time()
        fg = fractal_float_grid(mask, julia=True, julia_c=c, max_iter=80)
        float_grids.append(fg)
        if (i + 1) % 12 == 0:
            print(f"  Frame {i+1}/{n_frames} ({time.time()-t0:.2f}s each)")

    # Render each frame
    from PIL import ImageFont
    try:
        png_font = ImageFont.truetype("DejaVuSansMono.ttf", CELL_H - 1)
    except Exception:
        png_font = ImageFont.load_default()

    # Precompute per-frame value range for normalisation
    # Interior (non-escaping) cells have v=0.0; escape cells v>0.
    # Strategy: map escape cells to a color, give interior a BASE color
    # that shifts with the frame phase — so the full letter is always lit.
    frames = []
    for i, fg in enumerate(float_grids):
        frame_phase = i / n_frames
        colored_grid = []
        for r, row in enumerate(base_grid):
            new_row = []
            for c, (ch, _) in enumerate(row):
                if ch == " ":
                    new_row.append((" ", None))
                else:
                    v = fg[r][c] if r < len(fg) and c < len(fg[r]) else 0.0
                    if v < 0.01:
                        # Interior: slow-cycling deep blue/indigo so full letter is visible
                        t = (frame_phase * 2 + c / max(GRID_COLS - 1, 1) * 0.2) % 1.0
                        # Pulse between dark blue and mid-blue
                        brightness = 0.15 + 0.15 * math.sin(t * math.pi * 2)
                        rgb = (int(20 * brightness * 10), int(40 * brightness * 10), int(180 + 60 * math.sin(t * math.pi * 2)))
                    else:
                        # Escape boundary: bright full palette
                        rgb = _lerp_palette(ESCAPE_PALETTE, v)
                    new_row.append((ch, rgb))
            colored_grid.append(new_row)
        frames.append(_grid_to_png_bytes(colored_grid, font=png_font))
        if (i + 1) % 12 == 0:
            print(f"  Rendered frame {i+1}/{n_frames}")

    return frames


def effect_plasma(n_frames: int = 60) -> list:
    """Plasma wave cycling — phase sweeps continuously."""
    from justdoit.effects.generative import plasma_float_grid
    from justdoit.effects.color import SPECTRAL_PALETTE

    print(f"  Computing G09 base grid...")
    base_grid = _build_base_grid()
    mask = [[1.0 if ch != " " else 0.0 for ch, _ in row] for row in base_grid]

    from PIL import ImageFont
    try:
        png_font = ImageFont.truetype("DejaVuSansMono.ttf", CELL_H - 1)
    except Exception:
        png_font = ImageFont.load_default()

    frames = []
    for i in range(n_frames):
        t_phase = i / n_frames
        fg = plasma_float_grid(mask, t=t_phase)
        colored_grid = []
        for r, row in enumerate(base_grid):
            new_row = []
            for c, (ch, _) in enumerate(row):
                if ch == " ":
                    new_row.append((" ", None))
                else:
                    v = fg[r][c] if r < len(fg) and c < len(fg[r]) else 0.0
                    rgb = _lerp_palette(SPECTRAL_PALETTE, v)
                    new_row.append((ch, rgb))
            colored_grid.append(new_row)
        frames.append(_grid_to_png_bytes(colored_grid, font=png_font))
        if (i + 1) % 12 == 0:
            print(f"  Rendered frame {i+1}/{n_frames}")

    return frames


def effect_turing(n_frames: int = 48) -> list:
    """Turing pattern — palette phase rotates over fixed FHN field."""
    from justdoit.effects.generative import turing_float_grid
    from justdoit.effects.color import BIO_PALETTE, SPECTRAL_PALETTE

    print(f"  Computing G09 base grid + Turing field (one-time)...")
    t0 = time.time()
    base_grid = _build_base_grid()
    mask = [[1.0 if ch != " " else 0.0 for ch, _ in row] for row in base_grid]
    fg = turing_float_grid(mask, seed=42, scale=1, steps=200)
    print(f"  Turing field computed: {time.time()-t0:.2f}s")

    from PIL import ImageFont
    try:
        png_font = ImageFont.truetype("DejaVuSansMono.ttf", CELL_H - 1)
    except Exception:
        png_font = ImageFont.load_default()

    # Animate by rotating palette phase
    full_palette = SPECTRAL_PALETTE + list(reversed(SPECTRAL_PALETTE[1:-1]))

    frames = []
    for i in range(n_frames):
        phase = i / n_frames  # 0→1 rotation
        colored_grid = []
        for r, row in enumerate(base_grid):
            new_row = []
            for c, (ch, _) in enumerate(row):
                if ch == " ":
                    new_row.append((" ", None))
                else:
                    v = fg[r][c] if r < len(fg) and c < len(fg[r]) else 0.0
                    # Rotate phase
                    v_shifted = (v + phase) % 1.0
                    rgb = _lerp_palette(full_palette, v_shifted)
                    new_row.append((ch, rgb))
            colored_grid.append(new_row)
        frames.append(_grid_to_png_bytes(colored_grid, font=png_font))
        if (i + 1) % 12 == 0:
            print(f"  Rendered frame {i+1}/{n_frames}")

    return frames



def effect_flame(n_frames: int = 48) -> list:
    """Flame simulation — continuous heat simulation, smooth temporal evolution.

    Runs the flame heat grid as a persistent simulation, advancing ~8 steps
    per frame. Heat state carries over frame-to-frame = smooth, organic motion.
    FPS slowed to 8fps for a more natural fire tempo.
    """
    import random
    from justdoit.effects.color import FIRE_PALETTE, LAVA_PALETTE

    print(f"  Computing G09 base grid...")
    base_grid = _build_base_grid()
    mask = [[1.0 if ch != " " else 0.0 for ch, _ in row] for row in base_grid]

    from PIL import ImageFont
    try: png_font = ImageFont.truetype("DejaVuSansMono.ttf", CELL_H - 1)
    except: png_font = ImageFont.load_default()

    rows = len(mask)
    cols = max(len(r) for r in mask) if rows else 0
    ink = [[mask[r][c] >= 0.5 for c in range(cols)] for r in range(rows)]
    ink_cells = [(r, c) for r in range(rows) for c in range(cols) if ink[r][c]]

    # For each column, find the bottom-most ink row (heat source)
    col_bottom = {}
    for r, c in ink_cells:
        if c not in col_bottom or r > col_bottom[c]:
            col_bottom[c] = r
    seed_cells = set((col_bottom[c], c) for c in col_bottom)

    # Cooling per row above base: heat at row r = 1.0 - (distance_from_bottom / ink_height) * cooling_rate
    # We compute this analytically rather than simulating propagation —
    # much faster and reliably fills the full letter height.
    rng = random.Random(42)
    cooling_rate = 1.0  # full range from base (hot) to top (cold)

    # Precompute distance-from-bottom for each ink cell (per column)
    col_ink_rows = {}
    for r, c in ink_cells:
        col_ink_rows.setdefault(c, []).append(r)
    col_ink_range = {c: (min(rs), max(rs)) for c, rs in col_ink_rows.items()}

    def _heat_for_frame(time_offset: float):
        """Compute heat grid analytically with time-varying flicker at base."""
        h = [[0.0] * cols for _ in range(rows)]
        for r, c in ink_cells:
            if c not in col_ink_range:
                continue
            top_r, bot_r = col_ink_range[c]   # top=small r, bottom=large r
            span = max(bot_r - top_r, 1)
            # Distance from bottom (0 = at base, 1 = at top of letter)
            dist_from_bot = (bot_r - r) / span   # 0.0 at bottom, 1.0 at top
            # Base flicker: random per-column phase offset
            flicker = 0.08 * math.sin(time_offset * 6.28 + c * 0.3)
            # Heat: hot at base, cool at top
            base_heat = 1.0 - dist_from_bot * cooling_rate
            h[r][c] = max(0.0, min(1.0, base_heat + flicker))
        return h

    frames = []
    for i in range(n_frames):
        t = i / n_frames
        heat = _heat_for_frame(t)
        colored = []
        for r, row in enumerate(base_grid):
            new_row = []
            for c, (ch, _) in enumerate(row):
                if ch == " ": new_row.append((" ", None))
                else:
                    v = heat[r][c]
                    new_row.append((ch, _lerp_palette(FIRE_PALETTE, v)))
            colored.append(new_row)
        frames.append(_grid_to_png_bytes(colored, font=png_font))
        if (i + 1) % 12 == 0: print(f"  Frame {i+1}/{n_frames}")
    return frames


def effect_voronoi(n_frames: int = 48) -> list:
    """Voronoi stained glass — palette phase rotates over fixed cell pattern."""
    from justdoit.effects.generative import voronoi_fill
    from justdoit.effects.color import SPECTRAL_PALETTE

    print(f"  Computing G09 base grid...")
    base_grid = _build_base_grid()
    mask = [[1.0 if ch != " " else 0.0 for ch, _ in row] for row in base_grid]

    from PIL import ImageFont
    try: png_font = ImageFont.truetype("DejaVuSansMono.ttf", CELL_H - 1)
    except: png_font = ImageFont.load_default()

    # Pre-compute ONE voronoi fill — chars stay fixed, only palette phase animates.
    # Fixed chars = APNG delta-compression works well = small file size.
    print(f"  Computing voronoi fill...")
    char_rows = voronoi_fill(mask, seed=42, n_seeds=20)
    full_palette = SPECTRAL_PALETTE + list(reversed(SPECTRAL_PALETTE[1:-1]))

    frames = []
    for i in range(n_frames):
        phase = i / n_frames
        colored = []
        for r, row_str in enumerate(char_rows):
            new_row = []
            for c, ch in enumerate(row_str):
                if ch == " ": new_row.append((" ", None))
                else:
                    t = (c / max(GRID_COLS - 1, 1) * 0.6 + phase) % 1.0
                    new_row.append((ch, _lerp_palette(full_palette, t)))
            colored.append(new_row)
        frames.append(_grid_to_png_bytes(colored, font=png_font))
        if (i + 1) % 12 == 0: print(f"  Frame {i+1}/{n_frames}")
    return frames


def effect_attractor(n_frames: int = 60) -> list:
    """Strange attractor progressive reveal — trajectory accumulates."""
    from justdoit.effects.generative import strange_attractor_fill
    from justdoit.effects.color import ESCAPE_PALETTE

    print(f"  Computing G09 base grid...")
    base_grid = _build_base_grid()
    mask = [[1.0 if ch != " " else 0.0 for ch, _ in row] for row in base_grid]

    from PIL import ImageFont
    try: png_font = ImageFont.truetype("DejaVuSansMono.ttf", CELL_H - 1)
    except: png_font = ImageFont.load_default()

    # Pre-compute full attractor then reveal progressively
    # Use density_fill on mask with partial trajectory counts
    frames = []
    for i in range(n_frames):
        # Vary attractor type per cycle section
        attractor = "lorenz" if i < n_frames // 2 else "rossler"
        steps = 5000 + int(75000 * i / n_frames)
        from justdoit.effects.generative import strange_attractor_fill
        char_rows = strange_attractor_fill(mask, attractor=attractor, steps=steps)
        colored = []
        for r, row_str in enumerate(char_rows):
            new_row = []
            for c, ch in enumerate(row_str):
                if ch == " ": new_row.append((" ", None))
                else:
                    t = (c / max(GRID_COLS - 1, 1) + i / n_frames) % 1.0
                    new_row.append((ch, _lerp_palette(ESCAPE_PALETTE, t)))
            colored.append(new_row)
        frames.append(_grid_to_png_bytes(colored, font=png_font))
        if (i + 1) % 12 == 0: print(f"  Frame {i+1}/{n_frames}")
    return frames


EFFECTS = {
    "fractal-julia": (effect_fractal_julia, "Julia set rotating c — fractal morphs each frame", 72),
    "plasma":        (effect_plasma,        "Plasma wave phase cycling",                         60),
    "turing":        (effect_turing,        "Turing pattern palette rotation",                   48),
}


# ── Main ──────────────────────────────────────────────────────────────────────
EFFECTS.update({
    "flame":     (effect_flame,     "Flame simulation — continuous heat state, smooth",     48),
    "voronoi":   (effect_voronoi,   "Voronoi stained glass — palette phase",                 12),
    "attractor": (effect_attractor, "Strange attractor progressive reveal (Lorenz→Rössler)", 36),
})


def main():
    parser = argparse.ArgumentParser(description="4K animated PNG generator")
    parser.add_argument("--effect", default="fractal-julia",
                        choices=list(EFFECTS.keys()), help="Effect to render")
    parser.add_argument("--frames", type=int, default=0, help="Override frame count")
    parser.add_argument("--list",   action="store_true", help="List available effects")
    parser.add_argument("--fps",    type=float, default=FPS)
    args = parser.parse_args()

    if args.list:
        print("Available 4K effects:")
        for name, (_, desc, frames) in EFFECTS.items():
            print(f"  {name:20s} {frames} frames — {desc}")
        return

    fn, desc, default_frames = EFFECTS[args.effect]
    n_frames = args.frames if args.frames > 0 else default_frames

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{args.effect}.apng"

    print(f"\n4K Animation: {args.effect}")
    print(f"  Resolution: {CANVAS_W}x{CANVAS_H}, {GRID_COLS}x{GRID_ROWS} chars, {CELL_W}x{CELL_H}px cells")
    print(f"  Frames: {n_frames} @ {args.fps}fps")
    print(f"  Output: {out_path}")
    print()

    t_start = time.time()
    frames = fn(n_frames)
    print(f"\n  {len(frames)} frames rendered in {time.time()-t_start:.1f}s")

    # Save APNG from pre-rendered PNG bytes using PIL
    print(f"  Saving APNG ({len(frames)} frames)...")
    from PIL import Image
    duration_ms = int(1000 / args.fps)
    pil_frames = [Image.open(io.BytesIO(f)) for f in frames]
    pil_frames[0].save(
        out_path,
        format="PNG",
        save_all=True,
        append_images=pil_frames[1:],
        loop=0,
        duration=duration_ms,
        optimize=False,
    )
    size_mb = out_path.stat().st_size / 1_048_576
    print(f"  Saved: {out_path} ({size_mb:.1f}MB, {duration_ms}ms/frame)")


def main():
    parser = argparse.ArgumentParser(description="4K animated PNG generator")
    parser.add_argument("--effect", default="fractal-julia",
                        choices=list(EFFECTS.keys()), help="Effect to render")
    parser.add_argument("--frames", type=int, default=0, help="Override frame count")
    parser.add_argument("--list",   action="store_true", help="List available effects")
    parser.add_argument("--fps",    type=float, default=FPS)
    args = parser.parse_args()

    if args.list:
        print("Available 4K effects:")
        for name, (_, desc, frames) in EFFECTS.items():
            print(f"  {name:20s} {frames} frames — {desc}")
        return

    fn, desc, default_frames = EFFECTS[args.effect]
    n_frames = args.frames if args.frames > 0 else default_frames

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{args.effect}.apng"

    print(f"\n4K Animation: {args.effect}")
    print(f"  Resolution: {CANVAS_W}x{CANVAS_H}, {GRID_COLS}x{GRID_ROWS} chars, {CELL_W}x{CELL_H}px cells")
    print(f"  Frames: {n_frames} @ {args.fps}fps")
    print(f"  Output: {out_path}")
    print()

    t_start = time.time()
    frames = fn(n_frames)
    print(f"\n  {len(frames)} frames rendered in {time.time()-t_start:.1f}s")

    # Save APNG from pre-rendered PNG bytes using PIL
    print(f"  Saving APNG ({len(frames)} frames)...")
    from PIL import Image
    duration_ms = int(1000 / args.fps)
    pil_frames = [Image.open(io.BytesIO(f)) for f in frames]
    pil_frames[0].save(
        out_path,
        format="PNG",
        save_all=True,
        append_images=pil_frames[1:],
        loop=0,
        duration=duration_ms,
        optimize=False,
    )
    size_mb = out_path.stat().st_size / 1_048_576
    print(f"  Saved: {out_path} ({size_mb:.1f}MB, {duration_ms}ms/frame)")


if __name__ == "__main__":
    main()

