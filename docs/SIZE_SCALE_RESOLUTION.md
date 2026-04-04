# Size, Scale & Resolution — Feature Design Document

**Created:** 2026-04-04  
**Authors:** NumberOne + Jonny Galloway  
**Status:** Design / Pre-implementation  
**Relates to:** `justdoit/core/rasterizer.py`, `justdoit/output/svg.py`,
`scripts/generate_gallery.py`, `justdoit/cli.py`, `justdoit/layout.py` (new)

---

## Problem Statement

JustDoIt has no concept of where its output will be displayed. Every render
is produced at a fixed, implicit scale determined by glyph dimensions and
font choice. The output pipeline has no awareness of:

- Terminal width or height
- Display resolution or DPI
- Target pixel dimensions for SVG/PNG output
- How many characters of text will actually fit on screen
- What font size to use for a given display target

This creates several concrete problems:

1. **Text silently overflows** — no warning if "JUST DO IT" is wider than the
   terminal. The output is just clipped or wrapped by the terminal emulator.

2. **Gallery SVGs are all 14px** — every SVG in `docs/gallery/` was rendered
   at `font_size=14`, producing ~600×130px images. On a 4K display these look
   tiny. A 4K gallery would need `font_size=72` for pixel-perfect output.

3. **No "fill the screen" mode** — there is no way to say "I have a 3840×2160
   terminal at 63pt, make the text as large as possible." The math has to be
   done externally and manually.

4. **Animation cast headers are static** — `cast.py` does have `_detect_dims()`
   which auto-sizes from frame content (good), but the gallery script overrides
   this with fixed margins rather than display-aware sizing.

5. **Gallery README thumbnails are all 480px wide** — regardless of content
   complexity or intended display resolution.

---

## Scope

This document covers:

- **Layout primitives** — `measure()`, `RenderTarget`, `fit_text()`
- **SVG output scaling** — `font_size` as a first-class parameter
- **Gallery profiles** — standard / wide / 4K render tiers
- **CLI surface** — `--measure`, `--fit`, `--target`, `--svg-font-size`
- **Animation** — ensuring cast dimensions match render dimensions (already partially done)
- **Out of scope for this document:** bloom radius sizing, wallpaper export
  (these depend on this infrastructure but are separate features)

---

## Core Concepts

### Coordinate systems

There are three distinct coordinate systems in play. Keeping them separate
is the key to a clean design:

```
[GLYPH SPACE]          [TERMINAL SPACE]        [PIXEL SPACE]
  rows × cols            cols × rows              width × height
  (character grid)       (terminal dimensions)    (physical pixels)

  render() lives here    measure() lives here      svg.py lives here
  font defines scale     terminal reports this     font_size controls this
```

The conversions between them:

```
glyph_cols  ──(font glyph widths + gap)──→  terminal_cols
terminal_cols × cell_width_px ──────────→  pixel_width
cell_width_px = font_pt × (dpi/72) × char_w_ratio
```

### The three callers

Different callers need different things from size/scale:

| Caller | Question | Needs |
|--------|----------|-------|
| Terminal user | "Will this fit on screen?" | `measure()` + terminal size detection |
| Gallery generator | "What font_size for 4K output?" | `RenderTarget` → `svg_font_size()` |
| Interactive CLI | "Fill the screen with this text" | `fit_text()` + `--fit` / `--target` |

These are separate code paths. Don't conflate them.

---

## Part 1 — Layout Primitives

New file: `justdoit/layout.py`

### 1.1 `measure()`

```python
def measure(
    text: str,
    font: str = "block",
    gap: int = 1,
    iso_depth: int = 0,
    bloom_radius: int = 0,
    warp_amplitude: float = 0.0,
) -> tuple[int, int]:
    """Return (cols, rows) of the rendered output without rendering.

    Pure measurement — no ANSI output, no file I/O. Used to check fit
    before committing to a render.

    :param text: Input text string (same as render()).
    :param font: Font name (default: 'block').
    :param gap: Gap between characters in spaces (default: 1).
    :param iso_depth: If > 0, add isometric extrusion footprint (default: 0).
    :param bloom_radius: If > 0, add bloom halo margin on all sides (default: 0).
    :param warp_amplitude: If > 0, add sine warp horizontal overflow (default: 0.0).
    :returns: (cols, rows) as integers.
    """
```

**Implementation:**

```python
def measure(text, font="block", gap=1, iso_depth=0, bloom_radius=0, warp_amplitude=0.0):
    from justdoit.fonts import FONTS
    font_data = FONTS[font]
    text_upper = text.upper()
    height = len(next(iter(font_data.values())))
    
    cols = 0
    for i, char in enumerate(text_upper):
        glyph = font_data.get(char, font_data.get(" "))
        glyph_w = max(len(row) for row in glyph)
        cols += glyph_w + (gap if i < len(text_upper) - 1 else 0)
    
    rows = height
    
    # Spatial effect footprints
    if iso_depth > 0:
        cols += iso_depth
        rows += iso_depth
    if bloom_radius > 0:
        cols += bloom_radius * 2
        rows += bloom_radius * 2
    if warp_amplitude > 0:
        cols += int(warp_amplitude) + 1
    
    return cols, rows
```

**Key properties:**
- No side effects. No ANSI codes. No font rendering.
- Fast enough to call in a tight loop (e.g. binary search for max text length).
- Accounts for spatial effects that expand the footprint.
- Does NOT account for TTF fonts — those require Pillow to measure. TTF
  `measure()` is a separate code path (see §1.1a).

**1.1a — TTF measurement**

TTF glyph widths vary per character. Measurement requires Pillow:

```python
def measure_ttf(text: str, font_name: str, font_size: int) -> tuple[int, int]:
    """Measure rendered dimensions for a TTF font. Requires Pillow."""
    from PIL import ImageFont
    font = ImageFont.truetype(font_name, font_size)
    # Use getbbox or getlength per character
    ...
```

Gate behind `try: from PIL import ImageFont` as with other Pillow usage.

---

### 1.2 `RenderTarget`

```python
@dataclass
class RenderTarget:
    """Describes a physical display target for size/scale calculations.

    Used to compute font sizes, maximum column counts, and SVG dimensions
    for a given display configuration.

    :param display_w: Display width in pixels.
    :param display_h: Display height in pixels.
    :param dpi: Display DPI (default: 96 — standard Windows/Linux).
    :param scaling: OS DPI scaling factor, e.g. 1.5 for 150% (default: 1.0).
    :param char_w_ratio: Monospace cell width as fraction of cell height (default: 0.6).
    """
    display_w: int
    display_h: int
    dpi: float = 96.0
    scaling: float = 1.0
    char_w_ratio: float = 0.6

    @property
    def effective_dpi(self) -> float:
        """DPI after OS scaling is applied."""
        return self.dpi * self.scaling

    def cell_size_px(self, font_pt: float) -> tuple[float, float]:
        """Return (cell_width_px, cell_height_px) for a given font size in points."""
        cell_h = font_pt * (self.effective_dpi / 72.0)
        cell_w = cell_h * self.char_w_ratio
        return cell_w, cell_h

    def max_columns(self, font_pt: float) -> int:
        """Maximum terminal columns available at this font size."""
        cell_w, _ = self.cell_size_px(font_pt)
        return int(self.display_w / cell_w)

    def max_rows(self, font_pt: float) -> int:
        """Maximum terminal rows available at this font size."""
        _, cell_h = self.cell_size_px(font_pt)
        return int(self.display_h / cell_h)

    def max_font_pt(self, cols_needed: int, rows_needed: int) -> int:
        """Largest integer font pt size where cols_needed and rows_needed both fit."""
        for pt in range(1, 500):
            if self.max_columns(pt) < cols_needed or self.max_rows(pt) < rows_needed:
                return pt - 1
        return 499

    def svg_font_size_px(self, font_pt: float) -> int:
        """SVG font-size in pixels for this font_pt at this target's effective DPI."""
        return int(font_pt * (self.effective_dpi / 72.0))

    def fit_font_pt(
        self,
        text: str,
        font: str = "block",
        gap: int = 1,
        iso_depth: int = 0,
        bloom_radius: int = 0,
    ) -> int:
        """Return the largest font_pt where `text` fits on this display.

        Uses measure() to determine the render's column/row footprint, then
        finds the largest pt size where that footprint fits within display bounds.

        :returns: Font pt size as integer.
        """
        cols, rows = measure(text, font=font, gap=gap,
                             iso_depth=iso_depth, bloom_radius=bloom_radius)
        return self.max_font_pt(cols, rows)

    @classmethod
    def from_string(cls, spec: str, **kwargs) -> "RenderTarget":
        """Parse a display spec string like '3840x2160' or '3840x2160@1.5x'.

        Format: WxH  or  WxH@SCALINGx  (e.g. '3840x2160@2.0x')

        :param spec: Display spec string.
        :param kwargs: Additional kwargs passed to RenderTarget.__init__.
        :returns: RenderTarget instance.
        :raises ValueError: If spec format is invalid.
        """
        import re
        m = re.fullmatch(r"(\d+)x(\d+)(?:@([\d.]+)x)?", spec)
        if not m:
            raise ValueError(
                f"Invalid display spec {spec!r}. "
                "Expected format: WxH or WxH@SCALINGx (e.g. 3840x2160@2.0x)"
            )
        w, h = int(m.group(1)), int(m.group(2))
        scaling = float(m.group(3)) if m.group(3) else 1.0
        return cls(display_w=w, display_h=h, scaling=scaling, **kwargs)
```

**Named display presets** (convenience constants):

```python
# Common display configurations
DISPLAYS = {
    "fhd":        RenderTarget(1920, 1080),
    "qhd":        RenderTarget(2560, 1440),
    "4k":         RenderTarget(3840, 2160),
    "5k":         RenderTarget(5120, 2880),
    "ultrawide":  RenderTarget(5120, 1440),
    "4k-hiDPI":   RenderTarget(3840, 2160, scaling=2.0),
    "fhd-hiDPI":  RenderTarget(1920, 1080, scaling=2.0),
}
```

---

### 1.3 `fit_text()`

Given a target column count or RenderTarget, find the longest text that
fits, or the largest gap/font that works.

```python
def fit_text(
    text: str,
    target_cols: int,
    font: str = "block",
    gap: int = 1,
    iso_depth: int = 0,
    bloom_radius: int = 0,
    truncate: bool = True,
    truncation_suffix: str = "…",
) -> tuple[str, int]:
    """Find the longest prefix of text that fits within target_cols.

    :param text: Input text string.
    :param target_cols: Maximum column width to fit within.
    :param font: Font name (default: 'block').
    :param gap: Gap between chars (default: 1).
    :param iso_depth: Isometric depth footprint to account for (default: 0).
    :param bloom_radius: Bloom halo margin to account for (default: 0).
    :param truncate: If True, truncate text to fit. If False, raise ValueError
        when text is too wide (default: True).
    :param truncation_suffix: Suffix to add when truncating (default: '…').
    :returns: (fitted_text, actual_cols) tuple.
    :raises ValueError: If truncate=False and text doesn't fit.
    """
```

**Behaviour notes:**

- Works character by character, not word by word. The caller decides wrapping strategy.
- For `truncation_suffix="…"`, it accounts for the suffix's own width in the
  measurement — the result always fits within `target_cols` including the suffix.
- Returns the actual cols so the caller can compute centering/padding.

---

### 1.4 Terminal size detection

```python
def terminal_size() -> tuple[int, int]:
    """Return (cols, rows) of the current terminal.

    Uses os.get_terminal_size() with a fallback to (80, 24) if stdout
    is not a TTY (e.g. piped output, CI environment).

    :returns: (cols, rows) tuple.
    """
    import os
    try:
        ts = os.get_terminal_size()
        return ts.columns, ts.lines
    except OSError:
        return 80, 24
```

This exists implicitly scattered across the codebase. Make it canonical.

---

## Part 2 — SVG Output Scaling

### 2.1 Current state

`to_svg()` has a `font_size: int = 14` parameter that is never passed by any
caller. Every SVG in the gallery is 14px. The SVG canvas size is derived from:

```python
width = int(max_cols * char_w) + font_size     # ~640px for JUST DO IT at 14px
height = int(n_rows * line_h) + font_size      # ~128px for block font at 14px
```

### 2.2 What changes

`to_svg()` signature stays the same — `font_size` is already a parameter.
The changes are in the callers:

**`save_svg()` gains an optional `font_size` parameter:**

```python
def save_svg(text: str, path: str, font_size: int = 14, **kwargs) -> None:
```

No change to `to_svg()` internals.

**`generate_gallery.py` passes `font_size` per gallery profile.**

**CLI `--svg-font-size` flag:**

```bash
justdoit "JUST DO IT" --save-svg out.svg --svg-font-size 72
```

### 2.3 Font metric accuracy at large sizes

At 14px, a 10% error in `_CHAR_W_RATIO` is ~1.4px — invisible. At 72px,
the same error is ~7px per character. Over 64 columns: ~450px of drift.
This is visible as characters overlapping or gaps between them.

The fix: measure actual Courier New metrics at key font sizes and tune
`_CHAR_W_RATIO` or provide size-specific values. Courier New at most sizes
is very close to 0.600 — but at large sizes the rendering engine may apply
different hinting. Validate empirically with a test SVG at 72px and measure
the actual character positions.

Alternatively, switch the SVG renderer to use `textLength` attribute to force
exact spacing — this is an SVG feature that compresses/expands text to fill
a declared width, regardless of font metrics. It's the correct solution for
a fixed-width ASCII art renderer.

```xml
<text x="0" y="16" textLength="38.4" lengthAdjust="spacing">@</text>
```

Where `textLength = char_w` (precomputed from font_size × ratio). This
guarantees column alignment regardless of browser font rendering.

---

## Part 3 — Gallery Profiles

### 3.1 The three tiers

| Profile | Font size | SVG canvas | README img | Use case |
|---------|-----------|------------|------------|----------|
| `standard` | 14px | ~640×130px | 480px wide | Current behavior, GitHub README |
| `wide` | 28px | ~1280×260px | 800px wide | Higher fidelity GitHub, retina |
| `4k` | 72px | ~3200×650px | 1600px wide | 4K displays, direct viewing |

The `4k` profile SVG at 72px is ~3200px wide — a real 4K render. Displayed
at 1600px in the README it looks sharp on retina/4K screens (exactly 2× downscale).
The standard profile continues to work as-is for legacy viewers.

### 3.2 Directory structure

```
docs/
  gallery/          — standard (14px) — current
  gallery-wide/     — wide (28px) — new
  gallery-4k/       — 4K (72px) — new
```

Each directory has its own `README.md` with appropriate `img width` values.
The root `docs/gallery/README.md` (current) links to the wide and 4K galleries.

### 3.3 Gallery script changes

```python
# New profile definition at top of generate_gallery.py
@dataclass
class GalleryProfile:
    name: str
    svg_font_size: int
    readme_img_width: int
    output_dir: Path
    text: str = "JUST DO IT"

PROFILES = {
    "standard": GalleryProfile("standard", 14,  480,  GALLERY_DIR / "../gallery"),
    "wide":     GalleryProfile("wide",     28,  800,  GALLERY_DIR / "../gallery-wide"),
    "4k":       GalleryProfile("4k",       72,  1600, GALLERY_DIR / "../gallery-4k"),
}
```

CLI usage:

```bash
python scripts/generate_gallery.py                    # standard only (current behavior)
python scripts/generate_gallery.py --profile wide     # wide only
python scripts/generate_gallery.py --profile 4k       # 4K only
python scripts/generate_gallery.py --profile all      # all three
python scripts/generate_gallery.py --text "CO3DEX" --profile 4k
```

### 3.4 Validation before render

Before generating any gallery profile, validate that the text fits the
implicit terminal width for that profile:

```python
def _validate_fits(text: str, font: str, gap: int, profile: GalleryProfile) -> None:
    cols, rows = measure(text, font=font, gap=gap)
    # For SVG output there's no hard column limit — but sanity-check anyway
    if cols > 300:
        _LOGGER.warning(
            f"Text renders to {cols} columns — SVG will be very wide. "
            f"Consider shorter text or a narrower font."
        )
```

For terminal output, the check is a hard error if `cols > terminal_cols`.

---

## Part 4 — CLI Surface

### 4.1 New flags

**`--measure`** — print dimensions without rendering:

```bash
$ justdoit "JUST DO IT" --measure
cols: 64  rows: 7

$ justdoit "JUST DO IT" --measure --iso 4 --bloom 4
cols: 76  rows: 19
```

**`--fit N`** — truncate/scale text to fit N columns:

```bash
$ justdoit "JUST DO IT BUT LONGER" --fit 80
# Renders the longest prefix that fits within 80 columns
# Prints: "JUST DO IT BUT" (or whatever fits)
```

Primarily useful for dynamic text (user input, script output). Not useful
for fixed strings where you know the length in advance.

**`--target WxH[@SCALINGx]`** — compute and report max font size:

```bash
$ justdoit "JUST DO IT" --target 3840x2160
Max font size: 63pt (cell: 50.4×84.0px, letter height: 6.12")
Terminal grid at 63pt: 76×25

$ justdoit "JUST DO IT" --target 3840x2160@2.0x
Max font size: 31pt (cell: 49.6×82.7px, letter height: 3.01")
Terminal grid at 31pt: 77×26
```

**`--target` + `--save-svg`** — automatically size SVG for the target display:

```bash
$ justdoit "JUST DO IT" --target 3840x2160 --save-svg output.svg
# SVG font_size = 84px (63pt × 96/72 = 84px)
# Canvas: ~3226 × 589px — pixel-perfect for 3840×2160 native
```

**`--svg-font-size N`** — manual SVG font size override:

```bash
$ justdoit "JUST DO IT" --save-svg output.svg --svg-font-size 72
```

Takes precedence over `--target` when both are specified.

### 4.2 `--measure` output format

```
Text:         "JUST DO IT"
Font:         block
Gap:          1
Render size:  64 cols × 7 rows
With iso(4):  68 cols × 11 rows
With bloom(4): 76 cols × 19 rows

Display fits:
  1920×1080 @ 100%: up to 40pt  (letter height: 0.74")
  2560×1440 @ 100%: up to 47pt  (letter height: 0.88")
  3840×2160 @ 100%: up to 63pt  (letter height: 1.17")  ← pixel-perfect
  3840×2160 @ 200%: up to 31pt  (letter height: 0.58")
  5120×1440 @ 100%: up to 56pt  (letter height: 1.04")
```

This is the most useful output — gives Jonny the exact numbers for any
target display without running the Python calculation manually.

---

## Part 5 — Animation Dimensions

### 5.1 Current state

`cast.py` already has `_detect_dims()` which measures actual frame content.
The `to_cast()` function uses this automatically unless `width`/`height`
are explicitly overridden. This is already correct behavior.

### 5.2 What to fix

The gallery script's `generate_anim_gallery.py` should pass the `RenderTarget`
font size to the animation preset so that animated renders can be sized
consistently with the gallery profile:

```python
# In generate_anim_gallery.py SHOWCASE list:
{
    "id": "A08-flame",
    "preset_fn": lambda: flame_flicker("JUST DO IT"),
    "target": DISPLAYS["4k"],   # optional — for profile-aware gallery
}
```

When `target` is set, the gallery script generates a note in the README
about intended display size.

### 5.3 The 80×24 fallback

The default `cast.py` behavior writes `width=auto_detected, height=auto_detected`
from frame content. The hard-coded `80×24` that used to exist is gone — confirm
it's fully replaced. Current `to_cast()` signature should auto-detect when
no explicit width/height is given, which it does via `_detect_dims()`. Good.

---

## Part 6 — Text Layout for Multi-Line / Word-Wrap

Not in scope for v1 but needs a design note here because it will be asked for.

Currently `render()` takes a single string and renders it as one line of
characters. If the text is wider than the terminal, it overflows — there is
no wrapping, no line breaks, no layout engine.

Word-wrap is a fundamentally different feature from fit/scale:

- **Fit/scale** asks "how large can we make the text to fill the screen?"
- **Word-wrap** asks "how do we break text across multiple rows of ASCII art?"

Word-wrap for ASCII art is non-trivial because each glyph is 7 rows tall.
A "paragraph" of ASCII art is multiple bands of 7 rows stacked vertically.
Breaking words across bands requires measuring word widths and inserting
newlines at the glyph level.

This is `render_wrapped(text, max_cols)` — a future feature. Log it in
TECHNIQUES.md as a layout primitive when this document is implemented.

---

## Part 7 — Implementation Plan

### Phase 1 — Primitives (one session, ~100 lines)

1. Create `justdoit/layout.py` with `measure()`, `RenderTarget`, `DISPLAYS`, `fit_text()`, `terminal_size()`
2. Add tests in `tests/test_layout.py`:
   - `measure()` correctness against known render outputs
   - `RenderTarget` arithmetic (cell sizes, max columns)
   - `fit_text()` truncation behavior
   - `terminal_size()` fallback behavior
3. No changes to any other file yet — just the new module

### Phase 2 — SVG scaling (one session, ~30 lines)

1. Add `font_size` param to `save_svg()` call sites
2. Add `--svg-font-size` CLI flag
3. Validate `_CHAR_W_RATIO` accuracy at 28px, 48px, 72px (empirically)
4. Consider `textLength` SVG attribute if drift is visible at large sizes

### Phase 3 — CLI flags (one session, ~80 lines)

1. Add `--measure` flag
2. Add `--target WxH[@Sx]` flag with formatted output
3. Add `--fit N` flag with `fit_text()` integration
4. Wire `--target` → `--save-svg` auto font-size

### Phase 4 — Gallery profiles (one session, ~120 lines)

1. Add `GalleryProfile` dataclass and `PROFILES` dict
2. Add `--profile` flag to `generate_gallery.py`
3. Generate `docs/gallery-wide/` and `docs/gallery-4k/` directories
4. Link from main `docs/gallery/README.md`
5. Validate wide and 4K renders look correct in browser

### Phase 5 — Integration & polish

1. Wire `layout.py` into animation gallery (`generate_anim_gallery.py`)
2. Add `--target` to animation player `play()` for terminal-size-aware rendering
3. Document `RenderTarget` usage in CLAUDE.md

---

## Part 8 — Module Placement & Naming

```
justdoit/
  layout.py           NEW — measure(), RenderTarget, DISPLAYS, fit_text(), terminal_size()
  core/
    rasterizer.py     unchanged (measure() is a separate concern, not in the render path)
  output/
    svg.py            minor: font_size param to save_svg()
    terminal.py       minor: terminal_size() can delegate to layout.py
  cli.py              new flags: --measure, --target, --fit, --svg-font-size

tests/
  test_layout.py      NEW — layout primitive tests

scripts/
  generate_gallery.py  GalleryProfile + --profile flag
```

`layout.py` is at the top level of `justdoit/` (not `core/` or `output/`)
because it sits between those layers — it informs render decisions but doesn't
perform rendering, and it informs output decisions but isn't an output target.

---

## Part 9 — Open Questions

1. **TTF font measurement** — TTF glyphs have variable widths. `measure()` only
   handles the builtin fonts (fixed glyph widths). TTF measurement needs Pillow
   and is a separate implementation. For v1, document this limitation; for v2,
   add `measure_ttf()` with graceful fallback.

2. **FIGlet font measurement** — FIGlet fonts have variable glyph widths and
   kerning. The current FIGlet implementation in `justdoit/fonts/figlet.py`
   would need to expose glyph width without rendering. Defer to Phase 5.

3. **Bloom in `measure()`** — bloom radius parameter in `measure()` adds a
   symmetric margin. But bloom isn't implemented yet (C12). The `measure()`
   parameter should exist in the API (forward-compatible) but its effect can
   return 0 until C12 is implemented. Add `# TODO: update when C12 is built`
   comment.

4. **Windows DPI detection** — `RenderTarget` assumes DPI is provided externally.
   On Windows, the actual DPI depends on which monitor a window is on and the
   per-monitor DPI setting. `ctypes.windll.user32.GetDpiForWindow()` can return
   this. For now: document that `scaling=` must be set manually; add auto-detect
   as a future enhancement.

5. **The `textLength` SVG fix** — this is the right long-term solution for SVG
   column alignment at large font sizes. But it changes the SVG structure and
   could break downstream consumers. Implement behind a flag: `to_svg(..., fixed_width=True)`.

---

## Summary

The core of this feature is small: `measure()` (15 lines) and `RenderTarget`
(~60 lines). Everything else builds on those two primitives. The pipeline
transformation is:

**Before:**
```
render("JUST DO IT") → unknown size → output somewhere
```

**After:**
```
target = RenderTarget.from_string("3840x2160")
cols, rows = measure("JUST DO IT", font="block")
pt = target.max_font_pt(cols, rows)
# → "use 63pt — letter height is 6.12 inches"
output = render("JUST DO IT", ...)
save_svg(output, "out.svg", font_size=target.svg_font_size_px(pt))
# → pixel-perfect SVG for the specified display
```

That's the entire feature. Two primitives, well-placed, and the rest of the
system wires to them incrementally.

---

*This document is the implementation spec. When Phase 1 is complete, update
status to "Phase 1 done" and link to the commit. When all phases are done,
move to `docs/decisions/` as an ADR.*
