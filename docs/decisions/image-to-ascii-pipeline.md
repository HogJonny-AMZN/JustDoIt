# ADR: Image-to-ASCII Pipeline (G09 / G02 upgrade)

**Date:** 2026-04-24  
**Status:** Approved — implement  
**Techniques:** G09 (new), G02 upgrade  

---

## Context

The current TTF rasterizer (`justdoit/fonts/ttf.py` — G02) builds a glyph dict by rendering each character individually at `font_size` pixels and mapping single-pixel brightness → density char. At 4K gallery scale this produces noise clusters instead of recognizable letter shapes, because:

1. Single-pixel nearest-neighbor sampling has no awareness of partial cell coverage (aliasing)
2. The glyph dict approach caps detail at `font_size` rows — no matter how large the output SVG, the letter shape is determined by a ~12–80px render
3. No color information is captured

The harri-style approach (https://alexharri.com/blog/ascii-rendering) solves this by:
- Rendering at full resolution
- For each ASCII output cell, computing a **coverage vector** (fraction of ink in each zone of the cell)
- Matching that vector to the nearest character in a prebuilt shape DB
- Result: characters follow glyph contours, edges are sharp, partial coverage is handled correctly

`shape_fill.py` already contains the shape vector infrastructure (`_char_zone_densities`, `_build_char_db`, `_get_char_db`, `_nearest_char`) explicitly marked for future photo-to-ASCII use. This work promotes and completes that infrastructure.

---

## Decision

Implement **two changes** as a single cohesive feature:

### 1. Promote char DB to `justdoit/core/char_db.py`
Move the 6-zone shape vector system out of `shape_fill.py` into a shared core module. `shape_fill.py` will import from there.

### 2. New module `justdoit/core/image_sampler.py`
General-purpose `image_to_ascii()` function: any `PIL.Image` → `list[list[tuple[str, tuple[int,int,int]]]]` (grid of `(char, rgb)` per cell).

### 3. New entry point `render_image()` in `justdoit/core/pipeline.py` (or a new `justdoit/core/image_pipeline.py`)
Wire `image_to_ascii()` into the existing output pipeline.

### 4. Wire into 4K gallery
Update `generate_gallery.py` and the `4k` gallery profile to use the new image pipeline for text rendering instead of the glyph-dict TTF path.

---

## Architecture

```
TEXT + FILL EFFECTS           CLEAN TEXT (4K)         AI / PHOTO
─────────────────────         ──────────────────       ─────────────
glyph dict (unchanged)        PIL render high-res      any PIL.Image
     ↓                              ↓                       ↓
 mask → fill_fn()            ╔══════════════════╗          │
     ↓                       ║  image_to_ascii() ║◄─────────┘
 list[str]                   ║  core/image_sampler║
     ↓                       ║  6D zone DB       ║
 existing output             ║  + RGB per cell   ║
                             ╚══════════════════╝
                                      ↓
                             list[list[(char, rgb)]]
                                      ↓
                             existing output pipeline
```

**Key invariant:** The glyph-dict / mask / fill pipeline is **not modified**. Both paths co-exist. Fill effects (flame, plasma, turing, etc.) stay on the mask path. Clean text renders and image sources use the new path.

---

## Detailed Spec

### `justdoit/core/char_db.py` (NEW)

Promote from `shape_fill.py`. Public API:

```python
def build_char_db(
    charset: str = PRINTABLE_ASCII,
    cell_h: int = 16,
    cell_w: int = 8,
) -> dict[str, list[float]]:
    """Build 6-zone shape vector DB for charset. Cached by (charset, cell_h, cell_w)."""

def get_char_db(
    charset: str = PRINTABLE_ASCII,
    cell_h: int = 16,
    cell_w: int = 8,
) -> dict[str, list[float]]:
    """Return cached DB, building if needed."""

def nearest_char(vec: list[float], db: dict[str, list[float]]) -> str:
    """Find char whose 6D shape vector is nearest to vec (L2 distance)."""
```

**6 zones** (2 columns × 3 rows):
```
┌──────┬──────┐
│  UL  │  UR  │  row 0 .. cell_h//3
├──────┼──────┤
│  ML  │  MR  │  row cell_h//3 .. 2*cell_h//3
├──────┼──────┤
│  LL  │  LR  │  row 2*cell_h//3 .. cell_h
└──────┴──────┘
```

Each zone value = fraction of pixels in that zone that are "ink" (0.0–1.0).

Performance: use numpy if available, pure-Python fallback.  
Cache: module-level dict `_DB_CACHE: dict[tuple, dict]`, keyed by `(charset, cell_h, cell_w)`.

---

### `justdoit/core/image_sampler.py` (NEW)

```python
def image_to_ascii(
    image: "PIL.Image.Image",
    cell_w: int,
    cell_h: int,
    charset: str = PRINTABLE_ASCII,
    color: bool = True,
    db: Optional[dict] = None,
) -> list[list[tuple[str, Optional[tuple[int, int, int]]]]]:
    """
    Convert a PIL image to a 2D grid of (char, rgb_or_None) cells.

    For each cell in the grid:
      - Compute 6-zone coverage vector from the cell's pixels
      - Match to nearest char in the shape DB
      - Average the RGB of all pixels in the cell (for color=True)

    Cell grid dimensions:
      cols = image.width // cell_w
      rows = image.height // cell_h
      (rightmost/bottom partial cells are discarded)

    Args:
        image:    PIL.Image in any mode; converted to RGB internally
        cell_w:   Cell width in pixels (monospace char width)
        cell_h:   Cell height in pixels (monospace char height)
        charset:  Characters to consider for matching
        color:    If True, return RGB per cell; if False, return None for color
        db:       Optional pre-built char DB; built/cached if not provided

    Returns:
        list[rows] of list[cols] of (char: str, color: tuple[int,int,int] | None)

    Raises:
        ImportError: if Pillow is not installed
    """
```

**Luminance vs color:**
- Convert image to RGB
- For each cell: extract pixel block `image[row*cell_h:(row+1)*cell_h, col*cell_w:(col+1)*cell_w]`
- Convert to grayscale for zone vector computation (luminance)
- Average raw RGB for color output
- These are independent operations on the same pixel block

**Cell aspect ratio:**
- `cell_w` and `cell_h` must be passed by caller — sampler is aspect-ratio-agnostic
- Callers responsible for correct terminal cell proportions (~0.5 for standard monospace)

**Performance:**
- Use numpy for pixel block operations if available
- Pure-Python fallback (significantly slower at 4K but correct)
- For 4K at 8×16 cells: ~65k cells, numpy makes this fast enough for stills

---

### `justdoit/core/image_pipeline.py` (NEW) or extend `pipeline.py`

```python
def render_text_as_image(
    text: str,
    font_path: str,
    output_cols: int,
    output_rows: int,
    cell_w: int = 8,
    cell_h: int = 16,
    charset: str = PRINTABLE_ASCII,
    color: bool = True,
    bg_color: tuple = (0, 0, 0),
    fg_color: tuple = (255, 255, 255),
    font_scale: float = 1.0,
) -> list[list[tuple[str, Optional[tuple[int,int,int]]]]]:
    """
    Render text to a PIL image using a TTF font, then convert to ASCII grid.

    Steps:
      1. Compute PIL image size: output_cols * cell_w × output_rows * cell_h
      2. Find largest font_pt that fits text in that canvas
      3. Render text centered on canvas (PIL ImageDraw.text with kerning)
      4. Pass to image_to_ascii()
      5. Return (char, rgb) grid

    This replaces the glyph-dict TTF path for 4K gallery text renders.
    """

def render_pil_image_as_ascii(
    image: "PIL.Image.Image",
    cell_w: int = 8,
    cell_h: int = 16,
    charset: str = PRINTABLE_ASCII,
    color: bool = True,
) -> list[list[tuple[str, Optional[tuple[int,int,int]]]]]:
    """
    Convert any PIL image to ASCII grid. Thin wrapper over image_to_ascii().
    Entry point for AI image → ASCII and photo → ASCII use cases.
    """
```

**Output format conversion** — helper to go from the grid to existing output targets:

```python
def grid_to_ansi(grid: list[list[tuple[str, Optional[tuple]]]]) -> str:
    """Convert (char, rgb) grid to ANSI true-color string."""

def grid_to_svg(grid, cell_w, cell_h, font_size, font_family) -> str:
    """Convert (char, rgb) grid to SVG string."""
```

---

### Gallery integration

In `scripts/generate_gallery.py`, the `4k` profile should use `render_text_as_image()` instead of the current TTF glyph-dict path. The output is an SVG with per-character color from the grid.

Cell dimensions for 4K SVG gallery:
- SVG canvas: 3840×2160 (or scaled)  
- Monospace cell: 8px wide × 16px tall (adjust per font)
- Grid: 480 cols × 135 rows

---

## What NOT to change

- `justdoit/fonts/ttf.py` — leave as-is; still used by fill-effect renders
- `justdoit/core/rasterizer.py` — leave as-is; glyph-dict path unchanged  
- `justdoit/effects/shape_fill.py` — update to import from `core/char_db.py` instead of defining locally; pure refactor, no behavior change
- All existing tests — must continue passing

---

## New tests required

- `tests/test_char_db.py` — DB build, cache hit, nearest_char correctness
- `tests/test_image_sampler.py` — synthetic PIL images (solid, gradient, half-filled), verify char and color output
- `tests/test_image_pipeline.py` — render_text_as_image smoke tests, grid dimensions correct

---

## Technique registry updates

Update `docs/research/TECHNIQUES.md`:
- G02: status `done` → note "superseded by image pipeline for 4K; glyph-dict path retained for fill effects"
- G09: status `idea` → `done`, implementation notes

---

## File checklist

```
NEW:
  justdoit/core/char_db.py
  justdoit/core/image_sampler.py
  justdoit/core/image_pipeline.py
  tests/test_char_db.py
  tests/test_image_sampler.py
  tests/test_image_pipeline.py

MODIFIED:
  justdoit/effects/shape_fill.py   (import from core/char_db, remove local defs)
  scripts/generate_gallery.py      (4k profile → image pipeline)
  docs/research/TECHNIQUES.md      (G02 note, G09 done)

UNCHANGED:
  justdoit/fonts/ttf.py
  justdoit/core/rasterizer.py
  justdoit/core/glyph.py
  all existing tests
```

---

## Success criteria

1. `uv run pytest` — all existing tests pass, new tests pass
2. `uv run python scripts/generate_gallery.py --profile 4k` — produces SVG where letter shapes are recognizable at full 4K scale (not noise clusters)
3. `render_pil_image_as_ascii(some_image)` works end-to-end and produces colored ASCII output
4. No regressions on fill effects (flame, plasma, turing, etc.)
