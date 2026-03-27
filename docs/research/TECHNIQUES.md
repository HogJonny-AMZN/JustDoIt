# TECHNIQUES.md — Master Technique Registry

The canonical deduplicated list of all known/discovered techniques.
Research sessions append here. Duplicates get merged, not re-added.

---

## Categories

### A. Fill & Texture
Techniques that determine what characters fill a glyph mask.

| ID | Name | Description | Novelty | Status |
|----|------|-------------|---------|--------|
| F01 | Density ASCII | Map brightness → character density (`@#%+-.`) | 2 | `done` |
| F02 | Perlin Noise Fill | Noise field drives char selection inside mask | 4 | `done` |
| F03 | Cellular Automata Fill | Conway/GoL seeds inside glyph, freeze after N steps | 4 | `done` |
| F04 | Reaction-Diffusion | Gray-Scott inside glyph boundary | 5 | `done` |
| F05 | Fractal Fill | Mandelbrot/Julia escape time → char density | 4 | `idea` |
| F06 | SDF Edge Fill | Distance from glyph edge → char selection (outline/glow) | 4 | `done` |
| F07 | Voronoi Fill | Voronoi cells inside glyph, cell borders as chars | 4 | `idea` |
| F08 | Stipple Fill | Error-diffusion dithering (Floyd-Steinberg) inside mask | 3 | `idea` |
| F09 | Wave Interference | Two sine waves interfering inside mask | 4 | `idea` |
| F10 | Truchet Tiles | Tiling patterns inside glyph using arc/diagonal chars | 5 | `done` |

### B. Font Generation
Techniques for generating or importing new glyph sets.

| ID | Name | Description | Novelty | Status |
|----|------|-------------|---------|--------|
| G01 | FIGlet Parser | Parse `.flf` format, unlock 400+ community fonts | 2 | `done` |
| G02 | TTF/PIL Rasterizer | System fonts → low-res ASCII via Pillow | 3 | `done` |
| G03 | Bitmap Spritesheet Import | `.png` pixel font → glyph dict | 3 | `idea` |
| G04 | SDF Font Generator | Letterforms as signed distance fields, rasterize to grid | 5 | `idea` |
| G05 | Bézier Font Generator | Letters as Bézier curves, rasterize at any resolution | 5 | `idea` |
| G06 | Braille Font | Unicode Braille patterns for ultra-high-res ASCII | 3 | `idea` |
| G07 | Half-block Font | Unicode half-block chars (▀▄) for 2x vertical resolution | 2 | `idea` |
| G08 | Quadrant Block Font | Unicode quadrant chars (▖▗▘▝) for 2x2 subpixel grid | 3 | `idea` |

### C. Spatial Effects
Geometric transformations applied to the full rasterized grid.

| ID | Name | Description | Novelty | Status |
|----|------|-------------|---------|--------|
| S01 | Sine Wave Warp | Oscillate rows horizontally — flag/water effect | 2 | `done` |
| S02 | Perspective Tilt | Vanishing point projection — text receding to horizon | 3 | `done` |
| S03 | Isometric Extrusion | 3D isometric extrusion with face shading | 5 | `done` |
| S04 | Radial Distortion | Fisheye or pinch on whole text block | 3 | `idea` |
| S05 | Ripple/Moiré | Overlapping sine interference patterns | 3 | `idea` |
| S06 | Rotation | Arbitrary angle rotation of grid | 2 | `idea` |
| S07 | Mirror/Symmetry | Horizontal/vertical/radial symmetry modes | 1 | `idea` |
| S08 | Shear | Italic/oblique effect via grid shear | 2 | `done` |
| S09 | Barrel Distortion | Curved surface projection | 4 | `idea` |
| S10 | Vortex/Swirl | Rotational distortion increasing from center | 4 | `idea` |

### D. Color & Lighting
Color systems beyond flat ANSI.

| ID | Name | Description | Novelty | Status |
|----|------|-------------|---------|--------|
| C01 | Linear Gradient | Horizontal/vertical gradient across text block | 1 | `done` |
| C02 | Radial Gradient | Gradient radiating from center point | 2 | `done` |
| C03 | Per-Glyph Palette | Each letter gets its own color | 2 | `done` |
| C04 | Depth Color | Color driven by Z-depth (combine with 3D extrusion) | 3 | `idea` |
| C05 | Noise-Driven Color | Color field from Perlin noise, independent of shape | 4 | `idea` |
| C06 | Palette Import | Load palette from image or hex list | 2 | `idea` |
| C07 | True-Color ANSI | 24-bit RGB via `\033[38;2;r;g;bm` | 2 | `done` |
| C08 | Chromatic Aberration | RGB channels offset slightly | 5 | `idea` |
| C09 | Scanline Shading | Alternating bright/dim rows (CRT effect) | 3 | `idea` |
| C10 | Phosphor Glow | Green/amber CRT phosphor palette + bloom simulation | 4 | `idea` |

### E. Animation
Frame-based terminal animation techniques.

| ID | Name | Description | Novelty | Status |
|----|------|-------------|---------|--------|
| A01 | Typewriter | Characters appear sequentially | 1 | `done` |
| A02 | Scanline Reveal | Text builds top-to-bottom | 1 | `done` |
| A03 | Glitch | Random character corruption, snap back | 2 | `done` |
| A04 | Pulse | Brightness/color oscillation | 2 | `done` |
| A05 | Particle Dissolve | Characters drift/scatter on exit | 3 | `done` |
| A06 | Living Fill | Cellular automata animating inside glyph mask in real time | 5 | `idea` |
| A07 | Matrix Rain | Characters falling through the glyph shape | 3 | `idea` |
| A08 | Flame Simulation | Heat-based upward particle drift inside glyphs | 4 | `idea` |
| A09 | Liquid Fill | Glyph fills up like liquid pouring in from bottom | 4 | `idea` |
| A10 | Plasma Wave | Animated plasma color field (classic demoscene) | 4 | `idea` |

### F. Output Targets
Rendering to non-terminal targets.

| ID | Name | Description | Novelty | Status |
|----|------|-------------|---------|--------|
| O01 | HTML/CSS Export | `<pre>` with inline styles | 1 | `done` |
| O02 | SVG Export | Each char as positioned `<text>` element | 2 | `done` |
| O03 | PNG Export | PIL rasterization | 2 | `done` |
| O04 | GIF Export | Animated output | 3 | `idea` |
| O05 | ANSI File | `.ans` format for ANSI art viewers | 2 | `idea` |
| O06 | Markdown Export | Fenced code block output for docs/README embeds | 1 | `idea` |

### G. Novel / Experimental
Things that don't fit elsewhere. The truly weird stuff.

| ID | Name | Description | Novelty | Status |
|----|------|-------------|---------|--------|
| N01 | Typographic Recursion | Glyphs made of smaller instances of the same text | 5 | `idea` |
| N02 | Semantic Fill | Fill chars chosen for thematic meaning (e.g. "FIRE" filled with fire chars) | 5 | `idea` |
| N03 | Terrain Generation | Glyph fills driven by procedural heightmap (looks like topographic map) | 5 | `idea` |
| N04 | Fluid Simulation | Shallow water equations inside glyph mask | 5 | `idea` |
| N05 | Music-Reactive | ASCII art driven by audio FFT data | 5 | `idea` |
| N06 | L-System Growth | Lindenmayer system branching inside glyph | 5 | `idea` |
| N07 | ASCII Raytracer | Simple raytracer rendering 3D scene in ASCII | 5 | `idea` |
| N08 | Strange Attractor | Lorenz/Rössler attractor projected into glyph mask | 5 | `done` |
| N09 | Turing Pattern | Reaction-diffusion yielding biological spot/stripe patterns | 5 | `idea` |
| N10 | Slime Mold Simulation | Physarum polycephalum agent sim inside glyph | 5 | `done` |
