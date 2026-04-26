# VISION.md — JustDoIt: The Best Font Rendering Codebase on Earth

> *"How do you eat a whale? One bite at a time."*

## The Real North Star

Not "a cool ASCII art tool." Not "a fun terminal toy."

**The best font rendering codebase on earth.**

Not the best *terminal* font renderer. The best font renderer. Full stop. One that happens to start in the terminal — because the terminal is the hardest, most constrained medium. If you can make text *alive* in 80 columns of ASCII, you can make it alive anywhere.

That means:
- Every effect is configurable, composable, and production-quality
- Framerates are not assumed — 24fps is a default, 60fps is worth trying, the effect decides
- The rendering pipeline is substrate-agnostic: terminal today, SVG/PNG today, WebGL tomorrow
- When someone needs to render text with maximum expressiveness — in *any* medium — this is what they reach for
- The kind of thing that ends up as a dependency in other people's serious tools

The ASCII/ANSI aesthetic is the *foundation*, not the ceiling. The terminal is where we prove every idea. Then we port the proof.

---

## The Hierarchy

```
Terminal         ← prove it here first. hardest constraints. most honest feedback.
    ↓
SVG / PNG        ← vector and raster export, shareable artifacts (WORKING)
    ↓
4K PNG           ← true 3840×2160 pixel renders, image-pipeline path (WORKING)
    ↓
Browser / HTML   ← same pipeline, richer color, DOM output
    ↓
WebGL / GPU      ← particle volume fills, 3D extrusion, real-time at scale
    ↓
Anywhere         ← the pipeline is the product. the substrate is a parameter.
```

Terminal-first is a *discipline*, not a limitation. Every effect that works in 256 colors and monospace characters works everywhere. The reverse is not true. Start constrained, expand outward.

---

## What We've Learned Building It

### The Image Pipeline Is the Real Power Move

The biggest architectural insight to emerge in practice: **stop generating ANSI strings and start generating images**. The `image_to_ascii_fast()` path (PIL canvas → 6-zone char matching → grid → PNG/SVG) is where quality actually lives. It gives:

- Real glyph contours at any resolution, not block-font approximations
- The ability to use *any* PIL image as source — photos, generated textures, 3D renders
- Substrate-agnostic output: the same grid feeds SVG, PNG, terminal, or anything else
- True 4K output at 3840×2160 with 480×135 char grids that are pixel-perfect at native resolution

The 6-zone shape-matching DB (char_db.py) enables this. It's the bridge between pixels and characters — each cell of the image gets mapped to the ASCII character whose ink density best matches the source cell.

**Key caveat discovered:** The DB works for *photographic* sources where cell luminance varies continuously. It breaks for *solid-color* sources (white text on black) because all interior cells map to the same char. The fix: use the glyph-dict path for char selection, the image pipeline for color. This is the unsolved tension in the current 4K renders.

### The Terminal Constraint Is a Feature, Not a Bug

We set out to "prove ideas in the terminal first." What we discovered is more interesting: the terminal cell grid is a creative medium in its own right, with rules that produce effects impossible in normal graphics:

- Fill effects inside glyph masks produce **text that contains another texture** — fractal letterforms, Turing patterns growing inside the J, plasma fields mapped to character density. No conventional font renderer does this.
- The char-as-pixel abstraction forces you to think about **ink density**, not color — which leads to visual effects that read differently from normal graphics and are genuinely novel aesthetic territory.
- Animation inside glyph masks (living_fill, turing_bio, plasma_wave) produces effects where the **letter is alive** — the content of the letterform evolves independently of its shape. This is not a thing that exists outside ASCII art.

### Simulation Fills Need Animation to Be Seen

Slime mold, Conway's GoL, reaction-diffusion, strange attractors — these are *time-based phenomena*. A static snapshot is meaningless. The evolution IS the content. Every simulation fill should have a matching animated preset. This wasn't obvious at the start; it took building the static gallery and staring at boring snapshots to realize it. The animation backlog exists because of this lesson.

### 4K Is PNG, Not SVG

SVG is vector and scales infinitely, which sounds right for "4K gallery." But in practice, SVG renders characters as fonts — each char is a `<text>` element rendered by the browser at whatever size the SVG declares. When you try to fit 480 chars into 3840px, each char is 8px wide and the font rendering engine makes them look terrible at browser zoom levels.

The right model: **4K = a literal 3840×2160 PNG** where each pixel is a real pixel. Chars are rendered at 8×16px using PIL/ImageDraw at actual pixel resolution. Zoom into a letter at 1:1 and you see a detailed texture of ASCII characters. That's what 4K means for this project.

### Font Choice Matters More Than Expected

`DejaVuSansMono` was the default because it's the most commonly available monospace TTF on Linux. But `RobotoMono-Bold` renders dramatically better for ASCII art — the strokes are heavier, the letterforms are more distinct, and the bold weight means more ink coverage per cell which reads better in the char-density fills. The font gallery (3,861 Google Fonts, 20/day rendering) exists because we want to know empirically which fonts make the best ASCII art source material.

### 3D Without Geometry Is Always an Approximation

The current isometric extrusion (`_pil_isometric`) works by shifting a 2D PIL image and dimming it — a geometric approximation. The side faces look like a dimmed copy of the front face, not like actual side planes with correct per-face shading. The right path is `ttf2mesh` (G11) — tessellate glyph geometry into real 3D triangles, rasterize with a numpy Z-buffer. That's what gives correct occlusion, per-face lighting, and side faces that look like side faces. It's in the queue.

---

## Architecture: What's Real Now

```
justdoit/
  core/
    glyph.py          # mask representation, SDF computation
    char_db.py        # 6-zone shape-vector DB for image→ASCII
    image_sampler.py  # image_to_ascii_fast() — vectorized, numpy
    image_pipeline.py # render_text_as_image, grid_to_svg, grid_to_ansi
    rasterizer.py     # text → ANSI string (glyph-dict path)
  fonts/
    builtin/          # block, slim
    figlet.py         # .flf parser, 400+ community fonts ✓
    ttf.py            # PIL TTF rasterizer ✓
  effects/
    spatial.py        # warp, perspective, shear, isometric (string path)
    fill.py           # density, SDF (with gamma curve), shape
    color.py          # gradients, palettes, C11 fill_float_colorize
    generative.py     # flame, plasma, turing, voronoi, noise, wave,
                      # fractal, RD, slime, attractor, truchet, lsystem,
                      # living_fill, living_color
  animate/
    presets.py        # 45+ animation presets
  output/
    svg.py            # grid → SVG (with padding, auto-size)
    apng.py           # animated PNG output
    cast.py           # asciinema .cast output
  scripts/
    generate_gallery.py      # standard/wide/4K gallery generation
    generate_anim_gallery.py # APNG + .cast animation gallery
    generate_font_gallery.py # TTF font comparison gallery (20/day batch)
    download_google_fonts.py # 3,861 Google Fonts download + manifest
    debug_pipeline.py        # visual pipeline inspection (crop-to-content)
```

**What "done" means at each layer:**
- Terminal: ✅ Full ANSI, 256-color and true-color, animatable
- SVG: ✅ Per-char `<text>` elements, auto-sized with padding
- PNG (4K): ✅ 3840×2160 true-pixel, PIL ImageDraw, 8×16px cells
- APNG: ✅ Animated PNG export, all presets
- asciinema .cast: ✅ All presets

---

## The Technique Registry

As of 2026-04-26: **70 techniques** across 8 axes:

| Axis | Count | Examples |
|------|-------|---------|
| Fonts (G) | 11 done + 8 idea | block, slim, FIGlet (400+ fonts), TTF (3,861 Google), image pipeline |
| Fills (F) | 9 done + 1 idea | density, SDF (gamma curve), shape, noise, cells, wave, fractal, voronoi |
| Color (C) | 13 done + 6 idea | gradient, radial, palette, C11 float-colorize, C12 bloom, C13 HDR |
| Spatial (S) | 8 done + 7 idea | sine warp, perspective, shear, isometric, image-space transforms |
| Animation (A) | 13 done + 11 idea | typewriter, glitch, dissolve, plasma, flame, turing, neon, GoL |
| Generative (N) | 6 done + 0 idea | Turing FHN (spots/stripes/maze/morphogenesis), slime, attractor |
| Output (O) | 5 done + 3 idea | terminal, SVG, PNG, APNG, .cast |
| Cross-breeds (X) | 15 done | flame×iso×bloom, turing×warp, plasma×noise, GoL×age-color |

**Animation backlog:** 11 sim-based animations need to be built — slime, GoL, RD, attractor, SDF pulse, wave sweep, gradient hue rotation, truchet flow, L-system unfold, shape cycling, noise walk. Most are 20-80 lines each.

---

## The Specific Gaps (2026-04-26)

Things we now know are wrong or missing that weren't on the original vision:

1. **Interior char variety** — solid-white source images map all interior cells to the same char (M at 8×16px). The 6-zone DB is shape-matching, not density-ranking. Need a luminance-sorted fallback for uniform-luminance regions, or use glyph-dict path for chars and image pipeline only for color.

2. **Simulation animations** — slime, GoL, RD, attractor all look like noise as static SVGs. The animation IS the content. These should never have been added to the static gallery without a matching animated preset.

3. **3D is geometry, not transforms** — PIL affine transforms are approximations. ttf2mesh + numpy Z-buffer is the real path. G11 in queue.

4. **Font selection matters** — the font gallery (3,861 fonts, 20/day) exists to answer empirically which fonts make the best ASCII art source. RobotoMono-Bold is the current best; this will evolve.

5. **Gallery is a living thing** — the daily gallery should show APNGs, not static SVGs, for animated techniques. Fixed. The gallery README now auto-links to APNGs when they exist.

---

## The Remaining North Star

> A Python package where you hand it a string and a configuration, and it produces output ranging from "functional terminal banner" to "generative art piece" to "3D particle volume fill rendered in real-time" — from one tool, one pipeline, one mental model.

Terminal-first. Substrate-agnostic. The best font rendering codebase on earth.

The kind of thing that ends up on Hacker News, gets starred 10k times, and ships as a dependency in other people's creative tools — and occasionally makes someone say "wait, that was *Python*?"

---

*Vision drafted 2026-03-23 in conversation between Jonny Galloway and NumberOne.*
*Expanded 2026-03-30 — terminal is the proving ground, not the ceiling.*
*Major revision 2026-04-26 — updated to reflect what was actually learned building it:*
*image pipeline as the real power move; 4K = PNG not SVG; font choice matters;*
*3D needs geometry not transforms; simulation fills need animation.*
