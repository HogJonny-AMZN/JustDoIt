# JustDoIt — Rendering Architecture & Roadmap

> *"The best terminal rendering codebase on the planet."*
> 
> Not a goal. A standard.

---

## The Premise

ASCII/ANSI is the hardest rendering medium that exists. Fixed-width monospace grid. 95 printable characters. No subpixel positioning. No blend modes. No transparency. Color only where the terminal cooperates.

If you can make text *alive* in that medium — truly alive, with sharp edges, real physics, generative fills, and 24fps animation — you can make it alive anywhere. The terminal is where ideas get proven. Everything else is just a richer substrate.

This document describes how JustDoIt becomes the definitive implementation of that proof.

---

## The Architecture Stack

```
┌─────────────────────────────────────────────────────────────────────┐
│                          INPUT LAYER                                 │
│  plain text  │  PIL image  │  AI-generated image  │  live capture   │
└──────────────┴─────────────┴──────────────────────┴─────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         RENDER PIPELINE                              │
│                                                                      │
│   PATH A: Glyph-Dict (fast, fill-composable)                        │
│     text → font lookup → glyph mask → fill_fn(mask, t) → rows       │
│                                                                      │
│   PATH B: Image-Sample (quality, color, any source)                 │
│     image → [composite effects] → image_to_ascii() → (char, rgb)    │
│                                                                      │
│   PATH C: Hybrid (best of both)                                     │
│     text → PIL render → effect image → composite → sample           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       SPATIAL EFFECTS LAYER                          │
│  warp  │  distort  │  perspective  │  rotate  │  fisheye  │  zoom   │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        ANIMATION LAYER                               │
│  frame loop  │  time parameter t  │  simulation state  │  easing    │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         OUTPUT LAYER                                 │
│  terminal/ANSI  │  SVG  │  PNG  │  APNG  │  asciinema  │  WebGL    │
└─────────────────────────────────────────────────────────────────────┘
```

Every layer is independently swappable. Every transition between layers is a well-defined data contract. Nothing is hardwired.

---

## Data Contracts

These are the types that flow between layers. Get these right and the whole system is composable.

### Glyph (Path A output)
```python
Glyph = list[str]          # list of rows, same width per font
GlyphMask = list[list[float]]  # 0.0=empty, 1.0=ink, float for anti-alias
```

### Cell (Path B output, universal intermediate)
```python
@dataclass
class Cell:
    char: str                          # single ASCII character
    fg: tuple[int, int, int] | None    # RGB foreground, None = default
    bg: tuple[int, int, int] | None    # RGB background, None = transparent
    bold: bool = False
    dim: bool = False
```

### Grid (universal intermediate — what everything converges to)
```python
Grid = list[list[Cell]]   # Grid[row][col]
```

**This is the key type.** Everything upstream produces a Grid. Everything downstream consumes one. Both paths converge here. The Grid is the universal handoff point.

### Frame (animation unit)
```python
@dataclass
class Frame:
    grid: Grid
    t: float          # normalized time [0.0, 1.0]
    index: int        # absolute frame number
    duration_ms: int  # how long to display this frame
```

### AnimationSpec
```python
@dataclass
class AnimationSpec:
    fps: float = 24.0
    frame_count: int = 48
    loop: bool = True
    bounce: bool = False   # forward + reverse = natural loop
    easing: str = "linear" # linear | ease-in | ease-out | ease-in-out
```

---

## Resolution Model

Resolution is a first-class parameter, not an afterthought.

### Display Targets
```python
# Named presets (extend freely)
DISPLAYS = {
    "terminal":  DisplayTarget(cols=80,   rows=24,  note="classic terminal"),
    "wide":      DisplayTarget(cols=220,  rows=50,  note="modern widescreen terminal"),
    "fhd":       DisplayTarget(px_w=1920, px_h=1080, cell_w=8, cell_h=16),
    "qhd":       DisplayTarget(px_w=2560, px_h=1440, cell_w=8, cell_h=16),
    "4k":        DisplayTarget(px_w=3840, px_h=2160, cell_w=8, cell_h=16),
    "4k-hidpi":  DisplayTarget(px_w=3840, px_h=2160, cell_w=16, cell_h=32),  # 2× cell, same grid as FHD
    "5k":        DisplayTarget(px_w=5120, px_h=2880, cell_w=8, cell_h=16),
}
```

### Resolution-Derived Values
Given a DisplayTarget, everything else is computable:
```
cols     = px_w // cell_w          # ASCII grid width
rows     = px_h // cell_h          # ASCII grid height
canvas   = (px_w, px_h)            # PIL image size for Path B
font_pt  = fit_to_fill(text, cols) # largest font that fills the width
cell_ar  = cell_w / cell_h         # aspect ratio (~0.5 for monospace)
```

### The cell_w / cell_h problem
Monospace cells are not square (~0.5 aspect ratio). This matters for:
- Image sampling (a "square" region in pixel space is not square in cell space)
- Effect generation (noise, plasma, etc. must compensate or circles become ovals)
- SDF computation (Euclidean distance in cell space ≠ pixel space)

**Rule:** All effects that care about geometry receive `(cell_w, cell_h)` and compensate internally. Callers never need to think about this.

---

## The Three Render Paths

### Path A — Glyph-Dict (current, extend don't replace)

**When to use:** Animated fills (flame, plasma, turing, RD, slime). Per-letter effects. Low-latency animation. Terminal output.

**Pipeline:**
```
text → font.lookup(char) → GlyphMask → fill_fn(mask, t, **params) → Glyph → Grid
```

**Strengths:**
- O(letters × fill_cells) per frame — scales with text length, not display resolution
- Fill effects have per-letter masks — can treat each letter independently
- Zero PIL dependency for pure fills
- Works in actual terminals (not just SVG/PNG)

**Limitations:**
- Letter shape quality bounded by `font_size` in the rasterizer
- No color sourced from the fill (fills produce char choices, color is separate)
- No arbitrary image input

**Extension points:**
- `fill_fn` signature: `(mask: GlyphMask, t: float, **params) -> Glyph` — add `t` everywhere
- Anti-aliased masks: `float` values in GlyphMask (currently binary 0/1) enable sub-cell effects
- Per-fill color: fill_fn can return `list[list[Cell]]` instead of `list[str]` for color-aware fills

---

### Path B — Image-Sampler (new, G09)

**When to use:** 4K gallery stills. AI image → ASCII. Photo → ASCII. Maximum quality text. Color-accurate output.

**Pipeline:**
```
PIL.Image → image_to_ascii(cell_w, cell_h) → Grid
```

Internally:
```
for each cell (row, col):
    pixel_block = image[row*cell_h:(row+1)*cell_h, col*cell_w:(col+1)*cell_w]
    zone_vec    = compute_6zone_coverage(pixel_block.to_grayscale())
    char        = nearest_char(zone_vec, char_db)
    fg_rgb      = mean_rgb(pixel_block)
    grid[row][col] = Cell(char, fg=fg_rgb)
```

**Strengths:**
- Harri-quality edge following (chars follow contours, not just brightness)
- True RGB color per cell
- Source-agnostic: text, AI image, photo, video frame — same code
- PIL kerning, anti-aliasing, subpixel rendering included for free (text source)

**Limitations:**
- DB build cost (one-time, cached)
- Animation: DB lookup × cells × frames (needs numpy at 4K)
- No per-letter fill effects (no mask isolation)

**Performance envelope:**
| Display | Cells | numpy time/frame | pure-python time/frame |
|---------|-------|-----------------|------------------------|
| fhd     | ~16k  | ~8ms            | ~200ms                 |
| 4k      | ~65k  | ~30ms           | ~800ms                 |
| 4k anim | 65k×24fps | ~720ms/s  | not viable             |

4K animation: pre-render to Grid list, write APNG. Don't attempt real-time.

---

### Path C — Hybrid (planned, unlocks everything)

**When to use:** Best quality + generative effects at any resolution. The future default.

**Pipeline:**
```
text
  → PIL render at canvas resolution (Path B quality)
  → composite effect image (flame/plasma/turing as PIL layer, aligned to mask)
  → image_to_ascii()
  → Grid (char from luminance, color from effect layer)
```

**Why this is better than either A or B alone:**
- Letter shapes are PIL-quality (not density-mapped glyph dict)
- Effect fills are visible as color in the output (flame = red/orange cells inside sharp letter edges)
- Same effect code can run at any resolution — just generate the effect at canvas size
- Effect simulation runs at a *lower* grid resolution for performance, upsampled to canvas before composite

**The compositing model:**
```python
def composite_effect(
    text_image: PIL.Image,    # white text on black
    effect_image: PIL.Image,  # colorful effect at same size
    mode: str = "mask",       # "mask" | "multiply" | "screen" | "overlay"
) -> PIL.Image:
    """
    mode="mask":     effect visible only where text_image is ink (sharp edges)
    mode="multiply": effect dims with text coverage (glow bleeds slightly)
    mode="screen":   effect brightens on ink (neon glow look)
    mode="overlay":  photoshop-style — high contrast version of multiply
    """
```

---

## Effect Taxonomy

Effects fall into two families. Both should work on both paths.

### Family 1: Field Effects (value at every point in space and time)

These generate a value `f(x, y, t)` for every position. Works naturally as an image layer.

| Effect | Generator | Notes |
|--------|-----------|-------|
| Noise | Perlin/Simplex | scale, octaves, seed |
| Plasma | Sum of sine waves | frequency, phase, palette |
| Flame | Upward noise convection | turbulence, cooling |
| Voronoi | Nearest-cell distance | n_cells, metric, preset |
| Wave | Directional sine | frequency, amplitude, direction |
| Fractal | Mandelbrot/Julia escape | center, zoom, max_iter |
| Gradient | Linear/radial/conic | stops, angle |

**Interface:**
```python
class FieldEffect:
    def sample(self, x: float, y: float, t: float) -> float:
        """Return value in [0.0, 1.0] at normalized position and time."""

    def to_image(self, w: int, h: int, t: float, palette: Palette) -> PIL.Image:
        """Rasterize to PIL image for compositing."""

    def to_mask_fill(self, mask: GlyphMask, t: float) -> Glyph:
        """Fast path for Path A — sample at cell centers."""
```

Same effect, three consumers: image composite (Path C), direct fill (Path A), future GPU shader.

### Family 2: Simulation Effects (stateful, evolve over time)

These maintain state between frames. Can't be computed independently per-frame.

| Effect | State | Notes |
|--------|-------|-------|
| Reaction-Diffusion | U, V grids | Gray-Scott equations |
| Turing | Activator/inhibitor grids | FHN model |
| Slime Mold | Agent positions | Physarum simulation |
| Strange Attractor | (x, y, z) trajectories | Lorenz, Rössler |
| L-System | Grammar state | rules, axiom, generations |
| Conway/CA | Cell grid | rule variants |

**Interface:**
```python
class SimulationEffect:
    def __init__(self, w: int, h: int, **params): ...
    def step(self, dt: float = 1.0) -> None:
        """Advance simulation by dt. Called once per frame."""
    def to_image(self, palette: Palette) -> PIL.Image:
        """Render current state to PIL image."""
    def to_mask_fill(self, mask: GlyphMask) -> Glyph:
        """Fast path for Path A."""
    def reset(self) -> None: ...
```

**Critical:** simulation effects run at a *logical* grid that is independent of output resolution. A Turing simulation might run on a 120×34 grid regardless of whether the output is FHD or 4K. The `to_image()` method upsamples to whatever canvas size is needed.

---

## Animation Model

### The time parameter `t`

Every effect and every fill function receives `t: float` — normalized time in [0.0, 1.0] for a looping animation, or absolute seconds for non-looping. This is the single threading parameter that makes everything animatable.

```python
# Frame loop (simplified)
for frame_idx in range(spec.frame_count):
    t = frame_idx / spec.frame_count  # [0.0, 1.0)
    
    # Path A
    grid = render_glyph(text, font, fill_fn=flame_fill, t=t)
    
    # Path B / C
    effect_img = flame_effect.to_image(canvas_w, canvas_h, t, palette)
    composited = composite_effect(text_img, effect_img, mode="mask")
    grid = image_to_ascii(composited, cell_w, cell_h)
    
    frames.append(Frame(grid, t=t, index=frame_idx, duration_ms=1000//fps))
```

### Bounce / pingpong
```python
# Bounce: t goes 0→1→0, giving a seamless loop with no jump cut
if spec.bounce:
    cycle = frame_idx / (spec.frame_count / 2)
    t = cycle if cycle <= 1.0 else 2.0 - cycle
```

### Simulation effects and frame count
Simulation effects must run for `frame_count` steps. They don't use normalized `t` — they use step count. The animation system calls `effect.step()` once per frame, then captures `effect.to_image()`.

---

## CLI Design — Resolution-Aware and Maximally Flexible

### Core flags (stable, don't break)
```
python justdoit.py TEXT [options]

--font NAME          font name (block|slim|figlet/*|ttf:path)
--color NAME         ANSI color or rainbow
--fill NAME          fill effect name
--gap N              char gap between letters
```

### Resolution flags (new)
```
--display NAME|WxH   named preset or explicit e.g. 3840x2160
--cell-w N           cell width in px (default: auto from display)
--cell-h N           cell height in px (default: auto from display)
--cols N             explicit grid width override
--rows N             explicit grid height override
```

### Pipeline flags (new)
```
--pipeline glyph|image|hybrid|auto
    glyph:  Path A — fast, fill effects, terminal-safe
    image:  Path B — quality, color, any image source
    hybrid: Path C — best quality + generative effects
    auto:   pick based on other flags (default)

--source text|file:PATH|ai:PROMPT
    text:   render --text as ASCII art (default)
    file:   convert image file to ASCII
    ai:     generate image via AI then convert (future)
```

### Effect flags (new — generalize existing)
```
--fill NAME           fill effect (existing, extended)
--fill-param K=V      arbitrary effect parameter (repeatable)
    e.g. --fill plasma --fill-param preset=tight --fill-param t_offset=0.5

--composite-mode mask|multiply|screen|overlay
    how effect layer composites with text in hybrid mode

--palette NAME|HEX,HEX,...
    color palette for effects that use one
```

### Animation flags (new)
```
--animate             enable animation output
--fps N               frames per second (default: 24)
--frames N            total frame count (default: 48)
--duration MS         total duration in ms (overrides --frames if set)
--loop                loop the animation (default: true)
--bounce              pingpong loop (forward + reverse)
--easing linear|ease-in|ease-out|ease-in-out

--sim-steps N         simulation steps per frame for sim effects (default: 1)
--sim-warmup N        warmup steps before first frame (default: 0)
```

### Output flags (extend existing)
```
--output FILE         output file (.svg|.png|.apng|.cast|.txt)
--format auto|svg|png|apng|ansi|cast
    auto: infer from --output extension
--profile standard|wide|4k   gallery profile (existing)
--bg-color HEX        background color for image output
--font-size N         override computed font size for SVG/PNG output
```

### Auto-resolution logic
```
--display 4k --pipeline auto --animate
  → pipeline = hybrid (animate + display > fhd → hybrid preferred)
  → canvas = 3840×2160
  → cell_w=8, cell_h=16 → grid = 480×135
  → font_pt = fit_to_fill(text, 480 cols)
  → output format: .apng (animate implies apng unless --format specified)

--display terminal --fill flame
  → pipeline = glyph (terminal + fill → fast path)
  → cols = terminal_size().cols
  → no PIL dependency, runs in actual terminal
```

### `--pipeline auto` decision table
| Conditions | Chosen path |
|---|---|
| `--source file` or `--source ai` | image |
| `--display` > fhd AND no `--fill` | image |
| `--fill` specified AND `--animate` | glyph (simulation fills) or hybrid (field fills) |
| `--display` terminal (no px) | glyph |
| `--display` 4k AND `--fill` | hybrid |
| everything else | glyph |

---

## Output Formats

| Format | Description | Color | Animation | Terminal-safe |
|--------|-------------|-------|-----------|---------------|
| ansi | ANSI escape codes to stdout | 24-bit | no | yes |
| txt | plain text, no color | no | no | yes |
| svg | vector, per-char `<text>` elements | full RGB | no (multi-file) | no |
| png | rasterized via PIL | full RGB | no | no |
| apng | animated PNG, frame sequence | full RGB | yes | no |
| cast | asciinema v2 format | ANSI | yes | no |
| html | `<pre>` with `<span style="">` | full RGB | CSS animation | no |

All output formats consume `list[Frame]` (or `Frame` for stills). The output layer is a pure function: `frames → bytes`.

---

## Performance Strategy

### Do not over-engineer early. Profile first.

The bottleneck hierarchy (measured, not assumed):

1. **Simulation step** — RD/Turing at large grids. Solution: run at 1/4 res, upsample.
2. **DB nearest-neighbor search** — 65k cells × 95 chars × 6D L2. Solution: numpy vectorized matmul, or precompute a quantized lookup table.
3. **PIL render** — text drawing. Solution: cache the text image; only re-render when text changes.
4. **File I/O** — APNG write. Solution: stream frames, don't hold all in RAM.

### Numpy is optional but practically required above FHD animation
Make it optional with a pure-Python fallback. Raise a warning (not an error) when numpy is missing and the user requests 4K animation. The pure-Python path exists for correctness testing and small renders.

### Caching layer
```python
# Cache keys:
# - char_db: (charset, cell_w, cell_h)
# - text_image: (text, font_path, font_pt, canvas_size, fg, bg)
# - effect_image: for field effects — (effect_name, w, h, t, params_hash)

# Cache policy: LRU, max_size configurable, default 64 entries
```

---

## Extension Points (not optional — design for these from day one)

### Custom fills
```python
from justdoit.effects import register_fill

@register_fill("myeffect")
def my_effect(mask: GlyphMask, t: float, **params) -> Glyph:
    ...
```

### Custom fonts
```python
from justdoit.fonts import register_font

register_font("myfont", my_glyph_dict)
# or
register_font_from_ttf("myfont", "/path/to/font.ttf", size=16)
# or
register_font_from_image("myfont", "/path/to/sprite.png", char_w=8, char_h=16)
```

### Custom output targets
```python
from justdoit.output import register_output

@register_output("myformat", extensions=[".xyz"])
def write_myformat(frames: list[Frame], path: str, **kwargs) -> None:
    ...
```

### Custom compositors
```python
from justdoit.composite import register_compositor

@register_compositor("dissolve")
def dissolve(base: PIL.Image, effect: PIL.Image, t: float) -> PIL.Image:
    ...
```

---

## The Path to "Best on the Planet"

### What "best" actually means here

Not most features. Not most effects. **Best** means:

1. **Correctness** — characters follow glyph contours. Edges are sharp. Colors are accurate.
2. **Composability** — any fill, any font, any source, any output. No hidden incompatibilities.
3. **Performance** — fast enough to be used. Documented limits. Graceful degradation.
4. **Extensibility** — adding a new fill, font, or output is one file and one registration call.
5. **Portability** — zero hard dependencies for core functionality. PIL optional. numpy optional. GPU optional. If you have them, use them. If you don't, still works.

### Near-term (what Claude is building now)
- ✅ `core/char_db.py` — 6D zone shape DB
- ✅ `core/image_sampler.py` — image → ASCII grid
- ✅ `core/image_pipeline.py` — text/image → Grid entry points
- 4K gallery using image pipeline

### Medium-term
- `Cell` dataclass as universal intermediate type
- `t: float` parameter threaded through all fill functions
- `FieldEffect` base class + `to_image()` method on all field effects
- `--display` / `--pipeline` / `--animate` CLI flags
- Hybrid path (Path C) — text image + effect composite

### Long-term
- `SimulationEffect` base class — stateful, resolution-independent
- `Frame` + `AnimationSpec` types
- HTML output format
- WebGL shader export (the pipeline is the product; the substrate is a parameter)
- AI image source (`--source ai:PROMPT`)

---

## Invariants — Never Break These

1. **`uv run pytest` is always green.** Every PR. No exceptions.
2. **Core is zero-dependency.** `from justdoit import render` must work with only stdlib.
3. **Both paths co-exist.** Never remove the glyph-dict path. It has real advantages.
4. **All glyphs in a font have the same height.** The rasterizer zips rows.
5. **`t: float` is normalized [0.0, 1.0] for looping effects.** Never assume absolute time.
6. **The Grid is the handoff type.** Everything produces Grids. Everything consumes Grids.
7. **CLI flags are additive.** New flags never change the behavior of old flags.
8. **Patent flag protocol.** Anything with no known prior art: stop, flag, don't push. (See CLAUDE.md)

---

*Last updated: 2026-04-24*  
*Authors: Jonny Galloway, NumberOne*
