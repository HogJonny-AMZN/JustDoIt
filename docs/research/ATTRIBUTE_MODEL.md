# ATTRIBUTE_MODEL.md — Technique Decomposition & Cross-Breeding

**Created:** 2026-04-04  
**Authors:** NumberOne + Jonny Galloway  
**Purpose:** Classify every rendering attribute as an independent axis.
Cross-breeding two or more axes produces a combinatorial space of novel techniques.

---

## The Pipeline

Every JustDoIt output passes through some subset of these stages, in order:

```
[FONT] → [FILL] → [SPATIAL] → [COLOR/LIGHT] → [ANIMATION] → [OUTPUT]
```

Each stage is independently swappable. The goal of this doc is to enumerate
every knob at every stage, then ask: what happens if we wire two knobs together?

---

## Axis 1 — FONT (glyph shape)

The letterform itself. What goes into the mask before anything else.

| Key | Description | Done? |
|-----|-------------|-------|
| block | 7-row Unicode block chars | ✓ |
| slim | 3-row ASCII thin | ✓ |
| figlet | Any .flf FIGlet font (400+) | ✓ |
| ttf | System TTF rasterized via Pillow | ✓ |
| bitmap | Pixel spritesheet import | idea |
| sdf-gen | Letters as signed distance fields | idea |
| bezier | Bézier curve rasterizer | idea |
| braille | Unicode Braille (ultra hi-res) | idea |
| half-block | ▀▄ for 2x vertical resolution | idea |
| quadrant | ▖▗▘▝ for 2×2 subpixel | idea |
| pua | Custom glyphs via font patching | idea |

**Cross-breed opportunity:** Font affects mask shape, which affects every fill.
A SDF-generated font gives curved, smooth masks — fractal and voronoi fills
inside those would look completely different from block font masks.

---

## Axis 2 — FILL (what chars go inside the glyph)

The texture inside each letterform. Operates on the mask float grid.

### 2a — Static fills (single-frame, deterministic or seeded)

| Key | Algorithm | Output float source |
|-----|-----------|---------------------|
| density | brightness → char density | position |
| sdf | distance from edge | geometry |
| noise | Perlin field | spatial noise |
| cells | Conway GoL frozen | sim state |
| truchet | tiling arc/diagonal | tiling |
| rd | Gray-Scott reaction-diffusion | sim state |
| slime | Physarum agent sim | agent trail |
| attractor | Lorenz/Rössler projected | dynamics |
| lsystem | L-system branching | grammar |
| turing | FitzHugh-Nagumo activator | sim state |
| wave | Two-wave interference | frequency |
| fractal | Mandelbrot/Julia escape time | iteration |
| voronoi | Nearest-seed partitioning | geometry |
| plasma | Demoscene sin-field | sin composite |
| flame | Doom-fire heat propagation | thermal sim |
| shape | SDF contour-following | edge normals |

### 2b — Fill parameters as animation axes

Every fill has at least one float param that, when swept over frames, produces animation:

| Fill | Animatable param | Effect |
|------|-----------------|--------|
| plasma | `t` (phase) | blobs morph → A10 (done) |
| wave | `phase1`, `phase2` | fringes slide → A_F09a (idea) |
| flame | `seed` | fire flickers → A08 (done) |
| turing | `steps` | pattern grows → A_N09a (idea) |
| fractal | `zoom`, `cx`/`cy` | zoom into set |
| cells | `steps` | CA evolves |
| rd | `steps` | RD grows |
| slime | `steps` | trails extend |
| voronoi | `seed` | cells reform |
| noise | `z` (3D Perlin slice) | surface drifts |

**Key insight:** The fill float grid is the fundamental data. Right now it's
discarded after char selection. Preserving it and routing it to other axes
(color, spatial modulation) is the main unlocked value.

---

## Axis 3 — SPATIAL (geometry of the whole block)

Post-fill geometric transformations on the assembled text block.

| Key | Transform | Params |
|-----|-----------|--------|
| none | identity | — |
| sine_warp | row-wise horizontal oscillation | amplitude, frequency, phase |
| perspective_tilt | per-row width scaling | strength, direction (top/bottom) |
| shear | italic/oblique slant | amount, direction |
| isometric | 2.5D extrusion | depth, direction (left/right) |
| rotation | arbitrary angle | angle |
| mirror | symmetry fold | axis |
| radial_distort | fisheye / pinch | strength, center |
| barrel | curved surface projection | k1, k2 |
| vortex | rotational distortion from center | strength, direction |

**Animation axes:**
- `sine_warp.phase` → wave rolls left/right across text
- `sine_warp.amplitude` → breathes in/out
- `perspective_tilt.strength` → depth pulses
- `isometric.depth` → extrusion breathes (grows/shrinks)
- `rotation.angle` → slow spin
- `vortex.strength` → tightens/loosens

**S03 (isometric) cross-breed ideas:**
- `iso + flame_fill` → burning 3D letters (the side faces flame, front face dims)
- `iso + plasma + C11` → lava-lamp 3D block letters
- `iso_depth` swept per frame → extrusion breathes/pulses as animation (A_ISO1)
- `iso + sine_warp` on the *depth face only* → the extrusion shimmers like heat haze
- `iso + neon_glitch` → 3D neon sign that sparks on the extrusion face

---

## Axis 4 — COLOR / LIGHT

How ink cells are colored. Currently one of the weakest axes — big opportunity.

### 4a — Existing color modes

| Key | Scope | Source |
|-----|-------|--------|
| flat ANSI | per-glyph (all chars same) | fixed |
| rainbow | per-glyph cycle | char index |
| linear_gradient | per-cell | position (row or col) |
| radial_gradient | per-cell | distance from center |
| per_glyph_palette | per-glyph | glyph index in word |
| neon (presets) | per-row | frame state |

### 4b — C11: Fill-Float Color (the missing axis)

The biggest gap. No current mode maps the fill's own float output to color.
This is `C11` — a per-cell color function that receives `(fill_value: float, row, col) → (r, g, b)`.

Once C11 exists, every fill gets a free color dimension:

| Fill + C11 palette | Effect |
|-------------------|--------|
| flame + fire_palette | hot white base, red tips (A08c) |
| plasma + lava_palette | morphing lava lamp (A10c) |
| wave + spectral | interference fringes colored (A_F09b) |
| voronoi + cell_palette | stained glass, each cell its own hue (A_VOR1) |
| turing + bio_palette | spotted/striped coat coloring (N09 variant) |
| fractal + escape_palette | classic Mandelbrot color bands |
| noise + thermal_palette | heat map of a terrain |
| rd + chem_palette | chemical reaction visualization |

### 4c — Light model axes (future)

| Concept | Description | Depends on |
|---------|-------------|-----------|
| Z-depth color | color by extrusion depth layer | S03 isometric |
| Surface normal color | color by face orientation | N11 3D font renderer |
| Specular highlight | bright spot that moves per frame | any spatial output |
| Ambient occlusion | darkening at char density clusters | fill float |
| Chromatic aberration | RGB channels offset slightly | post-process |
| Phosphor glow | CRT green/amber bloom | post-process |
| Scanline shading | alternating dim/bright rows | post-process |

---

## Axis 5 — ANIMATION (time)

How any of the above changes between frames.

### 5a — Animation sources (what drives the change)

| Source | Description |
|--------|-------------|
| param sweep | single float stepped across frames (t, phase, seed, depth) |
| state evolution | sim state advanced N steps per frame (CA, RD, turing, slime) |
| stochastic | independent random per frame (flame, glitch, neon) |
| scripted | hand-authored keyframes / state machine (neon_startup) |
| physics | particles with velocity/gravity (A11, N12) |
| coupled | two fill outputs cross-modulated (A08d plasma→flame cooling) |
| reactive | driven by external signal (audio FFT, video frame) |

### 5b — Animation targets (what the change affects)

| Target | Examples |
|--------|---------|
| fill chars | plasma_wave, flame_flicker — chars change each frame |
| color only | neon_glitch, pulse — chars fixed, color changes |
| spatial | sine_warp phase, iso depth — geometry shifts |
| color + chars | A10c lava lamp — both driven by same field |
| structure | Turing morphogenesis — fill topology changes as sim runs |
| coupled layers | A08d — two fills modulate each other |

### 5c — Loop strategies

| Strategy | Description |
|----------|-------------|
| forward | play once, stop |
| forward-reverse | play forward then reverse for seamless loop (plasma_wave) |
| random-stable | each frame independent random, never loops identically (flame) |
| periodic | sin/cos drive, naturally periodic (wave phase, plasma t) |
| state-machine | scripted phases with transitions (neon_startup) |
| infinite | sim advances indefinitely, no defined end (CA, RD) |

---

## The Cross-Breed Matrix

Axes that can be wired together:

```
FILL float  ──→  COLOR (C11)          [plasma→color, flame→color, wave→color]
FILL float  ──→  SPATIAL modulation   [plasma modulates sine_warp amplitude]
FILL float  ──→  another FILL rate    [plasma modulates flame cooling → A08d]
SPATIAL     ──→  COLOR                [iso depth → Z-depth color]
ANIMATION t ──→  SPATIAL param        [depth breathes, warp rolls, tilt pulses]
ANIMATION t ──→  COLOR shift          [palette rotation → Voronoi stained glass]
FONT shape  ──→  FILL behavior        [SDF font → smoother masks → smoother fills]
```

---

## Cross-Breed Idea Catalog

### Ready to implement (no new infrastructure)

| ID | Combination | Notes |
|----|-------------|-------|
| A_F09a | F09 wave + phase animation | 20 lines |
| A_ISO1 | S03 iso + depth animation | iso depth swept per frame, letters breathe |
| X_ISO_NEON | S03 iso + A03 neon on extrusion face only | depth chars flicker, front face stable |
| X_WARP_PULSE | S01 sine_warp + A04 pulse | amplitude oscillates — text breathes AND waves |

### Needs C11 (fill-float → per-cell color)

| ID | Combination | Notes |
|----|-------------|-------|
| A08c | flame + fire_palette | hot base, cool tips, sin ripple |
| A10c | plasma + lava_palette | both chars and color from plasma float |
| A_F09b | wave + spectral | interference fringes colored |
| A_VOR1 | voronoi + cell_palette | stained glass |
| X_TURING_BIO | turing + bio_palette | leopard/zebra coat colors |
| X_FRACTAL_CLASSIC | fractal + escape_palette | classic Mandelbrot color bands |

### Needs new infrastructure

| ID | Combination | Infra needed |
|----|-------------|-------------|
| A08d | plasma modulates flame cooling rate | fill-float → fill-param coupling |
| A_N09a | Turing step animation | precompute snapshot series |
| X_ISO_FLAME | iso + flame on extrusion face | per-face fill routing |
| X_ISO_DEPTH_COLOR | iso + Z-depth color | depth layer → color map |
| X_NOISE_WARP | Perlin noise modulates sine_warp phase | fill-float → spatial param |
| X_PLASMA_WARP | plasma field modulates sine_warp amplitude per row | fill-float → spatial param |

### High novelty cross-breeds (multiple sessions)

| ID | Combination | Description |
|----|-------------|-------------|
| X_PLASMA_ISO | plasma fill + iso extrude + C11 | 3D block letters with lava-lamp interior AND Z-depth color on faces |
| X_FLAME_ISO | flame fill + iso extrude + A08c color | burning 3D letters, hot base white, tips red, depth face ember-shaded |
| X_TURING_WARP | turing spots/stripes modulate sine_warp phase per row | letters warp in the pattern of their own skin |
| X_RD_PLASMA | reaction-diffusion fill spatially modulated by plasma field | two generative systems layered, plasma shapes where RD can grow |
| X_FRACTAL_ZOOM_ANIM | fractal fill + zoom animation + C11 escape bands | zoom into Mandelbrot live inside letterforms, colored |
| X_LIVING_COLOR | CA fill animated (A06) + C11 step-count color | cells age, older cells shift hue toward red/orange |

---

## S03 Isometric — Specific Cross-Breed Ideas

S03 is particularly rich because it has a *structural* axis (front face vs depth face)
that no other technique has. Each face can be treated independently.

| Idea | Front face | Depth face | Animation |
|------|-----------|-----------|-----------|
| ISO_FLAME | flame fill | ember shading | flame flickers per frame |
| ISO_NEON | neon glitch | dim depth | depth chars spark independently |
| ISO_PLASMA | plasma fill | plasma offset t | depth runs slightly behind front |
| ISO_BREATHE (A_ISO1) | any fill | any fill | depth param sweeps 1→8→1 |
| ISO_HEAT | any fill | fire_palette on depth | depth face glows like the back is on fire |
| ISO_SCANLINE | any fill | CRT phosphor | front is clean, extrusion is retro CRT |
| ISO_STENCIL | voronoi cracked | solid block | front looks spray-painted, depth is solid |

---

## Priority Order

Based on implementation cost vs novelty payoff:

1. **C11** — fill-float → per-cell color infrastructure. Unlocks 6+ techniques.
2. **A_F09a** — wave phase animation. Nearly free. Do in same session as C11 warmup.
3. **A08c** — flame gradient color. First C11 consumer. Validates the infra.
4. **A_N09a** — Turing morphogenesis animation. Standalone, highest novelty.
5. **A_ISO1** — isometric depth animation. Short, makes S03 come alive.
6. **A08d** — plasma-modulated flame. Needs fill-float→fill-param coupling. Most novel cross-breed.
7. **X_ISO_FLAME** — burning 3D letters. Needs per-face fill routing + C11. Flagship visual.

---

## Notes on Architecture

The current rasterizer pipeline is:
```
font → mask → fill_fn(mask) → colorize(row, color) → string
```

To support the cross-breed matrix properly, it wants to be:
```
font → mask → fill_fn(mask) → (chars_grid, float_grid)
                                    ↓              ↓
                              spatial_fn       color_fn(float_grid)
                                    ↓              ↓
                              assembled_rows ← merge(chars, colors)
```

The float grid passthrough is the key architectural change. It doesn't have to be
done all at once — C11 can be implemented as a post-process function that accepts
the string output + a separately computed float grid, which is how A08c works today
(derive the palette from row index, not the actual heat values). The "proper" version
that routes actual fill floats comes later and is the unlock for A08d and the spatial
modulation family.

---

*Maintained by NumberOne. Update after each session that adds new cross-breed ideas.*
