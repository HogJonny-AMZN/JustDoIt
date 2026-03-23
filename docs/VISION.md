# VISION.md — JustDoIt: The Most Robust Python ASCII Art Generator on Earth

> *"How do you eat a whale? One bite at a time."*

---

## What It Is Now

A **static renderer**: hardcoded glyph arrays → concatenate rows → ANSI color. Clean, zero-dependency, single file. It works. But the ceiling is low.

---

## The Mental Model Shift: Glyphs as Masks

The key insight that unlocks almost everything: stop thinking of glyphs as strings of characters and start thinking of them as **2D boolean masks** — a grid of "ink" vs "empty." Once you have that abstraction, you can *fill* the mask with anything.

Right now the fill is always `██`. It doesn't have to be.

---

## Fill Strategies

Once glyphs are masks, the fill becomes a creative dimension:

- **Density-mapped ASCII** — `@`, `#`, `%`, `+`, `-`, `.`, ` ` — lighter characters near glyph edges, heavier toward the center. Instant pseudo-shading.
- **Noise fill** — Perlin/Simplex noise drives which character gets placed. Every render is slightly different. Same text, never the same output twice.
- **Reaction-diffusion** — run a Gray-Scott simulation inside the glyph boundary. The fill *grows* like a living pattern.
- **Cellular automata** — seed Conway's Game of Life inside the mask, evolve N steps, freeze it, render. The letter is legible but *alive*.
- **Fractal fill** — Mandelbrot escape time mapped to character density inside glyph bounds.
- **SDF-based fill** — distance from glyph edge drives character selection. Natural outline/glow effects.

---

## Font Generation

Right now fonts are hand-authored arrays. That scales badly. Better:

### 1. Bitmap Font Import
Load any `.bmp` or `.png` sprite sheet (free pixel fonts are everywhere), threshold pixels → ASCII. Instant access to thousands of existing fonts.

### 2. TTF/OTF → ASCII
Use PIL/Pillow (or freetype-py) to render any system font at low resolution, then map pixel brightness → ASCII density character. **Infinite fonts for free** — anything installed on the system.

### 3. FIGlet Compatibility
FIGlet (`.flf` format) has a massive community font library — 400+ fonts. Write a parser and unlock all of them instantly.

### 4. Procedural / Mathematical Fonts
Describe letterforms as signed distance fields (SDFs) or Bézier curves. Rasterize to a grid at any resolution. Scale-independent, mathematically precise. **Genuinely novel territory** in pure-Python ASCII art.

---

## Effect Pipeline

Right now: `render → colorize → print`. Linear, no composition.

The target architecture is a **stage pipeline** where each step is swappable:

```
text
  → glyph lookup / generation
  → rasterize to pixel grid
  → spatial effects  (warp, distort, rotate, perspective)
  → fill pass        (noise, gradient, pattern, cellular, fractal)
  → composite layers (background, shadow, outline, glow)
  → colorize         (flat, gradient, per-char, rainbow, palette)
  → output target    (terminal, file, HTML, SVG, PNG)
```

---

## Spatial Effects

Once you have a pixel grid, you can do math on it:

- **Sine wave warp** — oscillate rows horizontally. Text that looks like it's on a flag or water.
- **Perspective / vanishing point** — fake 3D tilt. Text receding into the horizon.
- **Isometric extrusion** — take a 2D glyph, extrude it in isometric space. Chunky 3D block letters with shaded faces. 🏆 *Showstopper feature.*
- **Radial distortion** — fisheye or pinch effect on the whole text block.
- **Ripple / interference** — overlapping sine waves creating moiré-like patterns.

---

## Color as a Dimension

Current model: one flat color per render.

Target:
- **Gradient fills** — horizontal, vertical, radial, diagonal gradients using 256-color or true-color ANSI
- **Per-glyph palettes** — each letter gets its own color, smooth transitions between them
- **Depth-based color** — combine with 3D extrusion: top face bright, side face mid, shadow dark
- **Heat map** — color driven by a noise field, independent of text shape
- **Palette import** — load a color palette from an image or hex list

---

## Animation

Terminal ANSI supports cursor movement — you can redraw frames:

- **Typewriter** — characters appear one at a time
- **Scanline reveal** — text builds top to bottom
- **Glitch** — randomly corrupt characters, snap back
- **Pulse** — brightness oscillates with color cycling
- **Particle dissolve** — characters drift and scatter on exit
- **Living fill** — cellular automata or reaction-diffusion animating *inside* the glyph mask in real time

---

## Output Targets

Beyond the terminal:
- **HTML/CSS** — `<pre>` with inline styles. Shareable, embeddable.
- **SVG** — each character as a positioned `<text>` element. Vector, scalable.
- **PNG/image** — PIL rasterization. Game assets, thumbnails, social.
- **ANSI file** — `.ans` format, compatible with old-school ANSI art viewers.
- **GIF** — animated output for the web.

---

## Target Package Architecture

```
justdoit/
  core/
    glyph.py          # mask representation (2D boolean grid)
    rasterizer.py     # text → pixel grid
    pipeline.py       # stage chaining
  fonts/
    builtin/          # block, slim, + more hand-crafted
    figlet.py         # .flf parser (400+ community fonts)
    bitmap.py         # sprite sheet importer
    ttf.py            # freetype/PIL renderer (infinite fonts)
    sdf.py            # mathematical / procedural font gen
  effects/
    spatial.py        # warp, perspective, isometric extrusion
    fill.py           # noise, SDF, cellular, fractal fills
    color.py          # gradients, palettes, depth-based color
    composite.py      # shadow, outline, glow, layer blending
  animate/
    player.py         # frame loop, terminal ANSI control
    presets.py        # typewriter, glitch, dissolve, pulse
  output/
    terminal.py       # ANSI print
    html.py
    svg.py
    image.py          # PNG via PIL
    ansi_file.py
  cli.py              # argparse entry point (backwards-compatible)
```

---

## The Bites

1. **Refactor** — restructure `justdoit.py` into the package layout above. No new features. Clean foundation.
2. **Glyph mask abstraction** + density fill (`@#%+-.` shading). Immediately impressive output.
3. **FIGlet parser** — unlock 400+ community fonts instantly.
4. **TTF/PIL import** — infinite font support.
5. **Gradient color system** — true-color ANSI, per-glyph palettes.
6. **Spatial effects** — sine warp, perspective tilt.
7. **Isometric 3D extrusion** — the showstopper. *(genuinely novel in pure Python)*
8. **Animation engine** — frame loop, typewriter, glitch, pulse.
9. **HTML/SVG/PNG output** targets.
10. **Cellular / noise fills** — the truly weird, generative, never-same-twice stuff.

---

## North Star

> A Python package where you hand it a string and a configuration, and it can produce output ranging from "functional terminal banner" to "generative art piece" — all in ASCII/ANSI, all in pure Python, all from one tool.

The kind of thing that ends up on Hacker News, gets starred 10k times, and ships as a dependency in other people's creative tools.

---

*Vision drafted 2026-03-23 in conversation between Jonny Galloway and NumberOne.*
