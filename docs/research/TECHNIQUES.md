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
| F05 | Fractal Fill | Mandelbrot/Julia escape time → char density | 4 | `done` |
| F06 | SDF Edge Fill | Distance from glyph edge → char selection (outline/glow) | 4 | `done` |
| F07 | Voronoi Fill | Voronoi cells inside glyph, cell borders as chars | 4 | `done` |
| F08 | Stipple Fill | Error-diffusion dithering (Floyd-Steinberg) inside mask | 3 | `idea` |
| F09 | Wave Interference | Two sine waves interfering inside mask | 4 | `done` |
| F10 | Truchet Tiles | Tiling patterns inside glyph using arc/diagonal chars | 5 | `done` |
| F11 | Shape-Vector Fill | 4-neighbor connectivity: `\|/-` at edges, density chars at interior — contour-following, pure Python | 4 | `done` |

> **Note:** F11 is labelled "F07" in the gallery/demo (numbering predates this registry entry). F07 Voronoi Fill remains unimplemented.

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
| G09 | GenAI Logo-to-Image → ASCII | AI image gen (DALL-E / SD) → hi-res image → 6D zone char matching via `_get_char_db()` | 5 | `idea` |
| G10 | Custom PUA Glyph Font | Unicode Private Use Area (U+E000–U+F8FF) + font patching (Terminal Glyph Patcher) to embed custom SVG glyphs — partial-fill blocks, diagonal sub-cell patterns, specialty symbols — usable in terminals running a patched font | 4 | `idea` |

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
| C11 | Fill-Float Color | Infrastructure: per-cell float→RGB color mapping. fill_float_colorize(text, float_grid, palette) → str. Receives the fill's raw float grid before char snapping; maps it through a named palette (FIRE, LAVA, SPECTRAL, BIO). Unlocks A08c, A10c, A_VOR1, A_F09b, X_TURING_BIO, X_FRACTAL_CLASSIC. | 2 | `done` |
| C12 | Bloom / Exterior Glow | Post-process: outward SDF from ink cells drives background-color (`\033[48;2;r;g;bm`) on surrounding space cells. BFS distance map from all ink cells; exponential falloff per cell. BLOOM_COLORS dict of named presets. Composable: pipe after any render output. Terminal-only: SVG/PNG exporters currently ignore background ANSI codes (bloom not visible in static exports). X_NEON_BLOOM is first consumer. | 5 | `done` |
| C13 | HDR Tone Mapping | Replace linear float→char mapping with named tone curves applied inside fill functions: `reinhard` (soft rolloff, shadow detail), `aces` (punchy mids, filmic highlights), `blown_out` (values above threshold → solid block chars, simulates overexposure). Parameter: `tone_curve="linear"|"reinhard"|"aces"|"blown_out"`. ~15 lines; most visually impactful on flame/plasma fills. | 3 | `done` |

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
| A08 | Flame Simulation | Heat-based upward particle drift inside glyphs | 4 | `done` |
| A08c | Flame Gradient + Sin-Wave Color | Variant of A08 — per-row fire palette (white→yellow→orange→red→dark red, hot at base) with a sin-wave phase offset per frame that makes the color boundary ripple vertically on a loop. No new deps: 256-color ANSI already in use. Post-processes `render()` output rows directly in the animation preset — same pattern as neon presets. One new `FIRE_PALETTE` list in color.py (~10 entries), one new `flame_gradient_flicker()` preset (~40 lines). | 3 | `idea` |
| A09 | Liquid Fill | Glyph fills up like liquid pouring in from bottom | 4 | `idea` |
| A10 | Plasma Wave | Animated plasma sin-field drives *character density selection* (not just color) inside glyph mask — classic demoscene formula applied to char choice; asciimatics has color-only plasma (no char selection, no glyph masking) — that is prior art to color component, not to this | 4 | `done` |
| A10c | Plasma Lava Lamp | A10 + C11: per-cell 24-bit color driven by same plasma float that drives char selection (high→white/yellow, mid→orange/red, low→deep violet). Both char and color shift simultaneously per frame on same field at different scales. Looks like a lava lamp. No new fill code — wire plasma float grid into C11. | 4 | `done` |
| A11 | Transporter Materialize | Star Trek transporter effect — particles scatter in bounding column then converge/coalesce into glyph shape; half-block subpixel resolution (▀▄█) for particle precision; brightness cascade per cell as it locks in; bidirectional (materialize + dematerialize); TOS/TNG/ENT/Kelvin era variants; fps configurable (24–60, effect decides) | 5 | `idea` |
| A08d | Plasma-Modulated Flame | Cross-breed: plasma sin-field spatially modulates the per-cell cooling rate inside flame_fill. High plasma → low cooling (tall hot flame persists). Low plasma → high cooling (flame dies back). Animate by sweeping plasma `t` while regenerating flame — fire's hot zones slowly rotate as plasma field evolves underneath it. Two independent physical processes coupled. Genuinely novel cross-breed. | 5 | `done 2026-04-17` |
| A_VOR1 | Voronoi Stained Glass | Voronoi cracked preset + C11: each cell region gets its own palette color (cell_id % palette_size). Animate by rotating palette offset each frame — color "light" shifts through the panes while cell borders stay structurally fixed. Structural permanence + color motion is the key tension. | 4 | `done` |
| A_F09a | Wave Interference Animation | F09 wave_fill already accepts phase1/phase2 but they're never swept. Animate by stepping both phases 0→2π per frame — moiré bands slide, interference fringes flow. The `moire` preset animated looks like a signal broadcast. ~20 lines, directly analogous to plasma_wave. | 3 | `idea` |
| A_F09b | Wave Chromatic Interference | F09 + C11: constructive peaks (intensity≈1.0) → one hue (e.g. cyan), destructive troughs (≈0.0) → complementary (red/orange), smooth interpolation between. Moire preset animated with color bands sliding = optical interference experiment. Simple once C11 exists. | 3 | `idea` |
| A_N09a | Turing Morphogenesis | Animate the *process* of Turing pattern formation: single-pass FHN sim captures U-grid at steps [50, 100, 200, 400, 800, 1500, 2500, 3500], play as frames with C11 BIO_PALETTE color. Letterforms grow a coat/skin pattern from noise. Turing 1952 morphogenesis visualized inside ASCII letterforms. | 5 | `done 2026-04-15` |
| X_TURING_BIO | Turing Biological Coat Colors | FHN activator-inhibitor pattern (N09) + C11 BIO_PALETTE coloring. Same float grid drives both char density and biological green color. Palette-rotation animation: structurally fixed Turing pattern, color sweeps through bio spectrum. Spots or stripes preset. Scores: tension=4 emerge=4 distinct=5 wow=4 → 17/20. | 4 | `done 2026-04-15` |
| X_NEON_BLOOM | Neon Bloom | C12 cross-breed: neon color (24-bit ANSI foreground) + C12 bloom (background ANSI). Bloom falloff breathes via sin(t) per frame — the halo glow expands and contracts. Axes: C07 (24-bit color) × C12 (bloom) × A (falloff animation). Terminal-only — SVG/PNG exporters ignore background ANSI. 60 frames @ 12fps, forward+reverse loop. Scores: tension=5 emerge=4 distinct=5 wow=5 → 19/20. | 5 | `done` |
| X_PLASMA_BLOOM | Plasma Chromatic Bloom | A10 plasma fill + C11 spectral colorization + C12 chromatic bloom. Key axis: plasma phase `t` drives the bloom halo color through the full visible spectrum (violet→indigo→cyan→green→orange) synchronized with the wave cycle. Interior chars colored spectrally from plasma float; exterior bloom hue shifts as `t` sweeps. Truly chromatic bloom — hue-shifting halos have no prior art in ASCII art tooling. Scores: tension=4 emerge=4 distinct=4 wow=4 → 16/20. 72 frames @ 12fps (36×2 loop). | 4 | `done` |
| A_ISO1 | Isometric Depth Breathe | S03 isometric + depth animation cross-breed. Sine-swept depth parameter: depth = max(1, base_depth + round(amplitude * sin(2π*i/n_frames))). Per-frame: render() then isometric_extrude(depth=computed_depth). Letters appear to breathe in 3D — extrusion grows and shrinks each cycle. Any fill for front face; depth face uses shade chars (▓▒░·). Seamless forward-reverse loop. Implemented as iso_depth_breathe() in presets.py. | 3 | `done` 2026-04-14 |
| A_BLOOM1 | Bloom Pulse | Animation: C12 bloom radius oscillates via sin(t) — the glow breathes in and out around letterforms. Combined with flame fill interior (tone-mapped ACES curve) and fire palette: a burning core with a pulsing light halo. The bloom radius, color saturation, and fill heat all independently driven. Implemented as `bloom_pulse()` in presets.py. | 5 | `done` |
| X_PLASMA_WARP | Plasma-Modulated Sine Warp | A10 plasma float grid → per-row sine_warp amplitude (S01). First FILL→SPATIAL param coupling in the project. Each row's mean plasma intensity modulates the row's warp amplitude — rows at plasma peaks swing hard, rows at troughs are nearly still. As plasma `t` sweeps, amplitude topology rotates: previously static rows suddenly swing. A10 (plasma float) × S01 (per-row amplitude) × C11 spectral × C12 bloom. Implemented as `plasma_warp()` in presets.py; `amplitude_map` param added to `sine_warp()`. Scores: tension=5 emerge=4 distinct=5 wow=4 → 18/20. 72 frames @ 12fps (36×2 loop). | 5 | `done 2026-04-17` |
| X_FRACTAL_CLASSIC | Fractal Escape-Time Color | Mandelbrot escape-time float grid exposed via `fractal_float_grid()` companion. ESCAPE_PALETTE (deep-purple → blue → cyan → green → yellow → orange → bright) colorizes letterforms via C11 fill_float_colorize(). Palette offset sweeps per frame — fractal geometry fixed, color bands cycle continuously through letterforms. Pattern: mathematical structural permanence + color flow. 72 frames @ 12fps. Scores: tension=4 emerge=3 distinct=4 wow=4 → 15/20. | 4 | `done 2026-04-18` |

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

### I. Sound
Synchronized audio output — optional, gracefully degraded if unavailable.

| ID | Name | Description | Novelty | Status |
|----|------|-------------|---------|--------|
| SO01 | Synthesized Sound Engine | Optional `sounddevice`+`numpy` audio layer; procedural tone generation synchronized to animation frames; gated import, silent fallback | 5 | `idea` |
| SO02 | Transporter Beam Audio | TNG/TOS transporter sound synthesized procedurally — frequency sweep + bandpass noise + reverb tail, synced to A11 materialize animation frames | 5 | `idea` |
| SO03 | Sound Asset Playback | WAV/OGG file playback via `pygame.mixer` for pre-recorded effects; asset pipeline for bundled sounds | 3 | `idea` |

### L. Layout & Scale Infrastructure

| ID | Name | Description | Novelty | Status |
|----|------|-------------|---------|--------|
| L01 | measure() | Pure measurement function: returns (cols, rows) for a given text+font+gap without rendering. Accounts for iso depth, bloom radius, warp amplitude footprints. Foundation for all size-aware features. ~15 lines. | 1 | `idea` |
| L02 | RenderTarget | Display geometry descriptor: display_w/h, dpi, scaling → cell_size_px(), max_columns(), max_font_pt(), svg_font_size_px(), fit_font_pt(). Named presets: fhd/qhd/4k/5k/ultrawide. ~60 lines. | 1 | `idea` |
| L03 | fit_text() | Given target_cols, returns longest text prefix that fits + actual width. Accounts for spatial effect footprints. | 1 | `idea` |
| L04 | Gallery Profiles | Three render tiers: standard (14px SVG, 480px README), wide (28px, 800px), 4k (72px, 1600px). GalleryProfile dataclass + --profile flag on generate_gallery.py. | 1 | `idea` |
| L05 | CLI Size Flags | --measure (print col/row dims), --target WxH[@Sx] (compute max font pt), --fit N (truncate to N cols), --svg-font-size N. | 1 | `idea` |
| L06 | render_wrapped() | Word-wrap for ASCII art: break text across multiple 7-row bands. Requires measure() per word. Future feature — do not implement before L01-L03. | 2 | `idea` |

### H. Pipeline & Composition
Architectural ideas — not a single technique but a way of combining them at a higher level.

| ID | Name | Description | Novelty | Status |
|----|------|-------------|---------|--------|
| P01 | Multi-layer Compositor | Stack renders with blend modes (multiply/screen/overlay) — Photoshop layers for ASCII | 5 | `idea` |
| P02 | ASCII Video Pipeline | Any video file → per-frame zone-matched ASCII → ANSI sequence / GIF / re-encoded video. ffmpeg for ASCII. | 5 | `idea` |
| P03 | Live Input → ASCII | Real-time webcam / capture card → streaming zone-matched ASCII. ASCII photobooth or music visualizer. | 5 | `idea` |
| P04 | AI Creative Director | Brand brief or mood prompt → LLM art direction → image AI → zone-matched ASCII → color effects → gallery. End-to-end AI-driven ASCII creation. | 5 | `idea` |
| P05 | Full 3D Scene Renderer | Arbitrary 3D scene (camera, lights, mesh, texture) → raytraced / rasterized → F11 normal-mapped char selection. ASCII as a first-class 3D output format. Extends N07 + N11. | 5 | `idea` |

---

### G. Novel / Experimental
Things that don't fit elsewhere. The truly weird stuff.

| ID | Name | Description | Novelty | Status |
|----|------|-------------|---------|--------|
| N01 | Typographic Recursion | Glyphs made of smaller instances of the same text | 5 | `done` |
| N02 | Semantic Fill | Fill chars chosen for thematic meaning (e.g. "FIRE" filled with fire chars) | 5 | `idea` |
| N03 | Terrain Generation | Glyph fills driven by procedural heightmap (looks like topographic map) | 5 | `idea` |
| N04 | Fluid Simulation | Shallow water equations inside glyph mask | 5 | `idea` |
| N05 | Music-Reactive | ASCII art driven by audio FFT data | 5 | `idea` |
| N06 | L-System Growth | Lindenmayer system branching inside glyph | 5 | `done` |
| N07 | ASCII Raytracer | Full raytracer: camera, lights, mesh, BVH, shadows, reflections → char selected by surface normal (F11) + density by luminance. Terminal Quake. | 5 | `idea` |
| N08 | Strange Attractor | Lorenz/Rössler attractor projected into glyph mask | 5 | `done` |
| N09 | Turing Pattern | Reaction-diffusion yielding biological spot/stripe patterns | 5 | `done` |
| N10 | Slime Mold Simulation | Physarum polycephalum agent sim inside glyph | 5 | `done` |
| N11 | 3D Font Renderer → Normal-Mapped Fill | Extrude glyph outline to 3D mesh, software-rasterize, use surface normals to drive F11 char selection | 5 | `idea` |
| N12 | 3D Particle Volume Fill | Extend N11: extruded glyph 3D volume becomes a particle field — particles animate into the letter shape from scatter, with physics (gravity, attractors, turbulence); ASCII char encodes particle density/velocity; the text-fill particle mode as a terminal-native effect; natural extension of A11 transporter into a general particle-to-glyph animation system | 5 | `idea` |
