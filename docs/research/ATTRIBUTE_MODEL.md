# ATTRIBUTE_MODEL.md - Technique Decomposition & Cross-Breeding

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

## Axis 1 - FONT (glyph shape)

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
A SDF-generated font gives curved, smooth masks - fractal and voronoi fills
inside those would look completely different from block font masks.

---

## Axis 2 - FILL (what chars go inside the glyph)

The texture inside each letterform. Operates on the mask float grid.

### 2a - Static fills (single-frame, deterministic or seeded)

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

### 2b - Fill parameters as animation axes

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

## Axis 3 - SPATIAL (geometry of the whole block)

Post-fill geometric transformations on the assembled text block.

| Key | Transform | Params |
|-----|-----------|--------|
| none | identity | - |
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

## Axis 4 - COLOR / LIGHT

How ink cells are colored. Currently one of the weakest axes - big opportunity.

### 4a - Existing color modes

| Key | Scope | Source |
|-----|-------|--------|
| flat ANSI | per-glyph (all chars same) | fixed |
| rainbow | per-glyph cycle | char index |
| linear_gradient | per-cell | position (row or col) |
| radial_gradient | per-cell | distance from center |
| per_glyph_palette | per-glyph | glyph index in word |
| neon (presets) | per-row | frame state |

### 4b - C11: Fill-Float Color (the missing axis)

The biggest gap. No current mode maps the fill's own float output to color.
This is `C11` - a per-cell color function that receives `(fill_value: float, row, col) → (r, g, b)`.

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

### 4c - The dual-channel insight (foreground + background)

Each terminal cell has TWO independent color channels. JustDoIt currently
uses only one:

| Channel | ANSI code | Current use | Opportunity |
|---------|-----------|-------------|-------------|
| Foreground | `\033[38;2;r;g;bm` | fill color, gradients | already used |
| Background | `\033[48;2;r;g;bm` | **completely unused** | bloom, glow, halo |

A space character with a bright background color is a **pure light-emitting cell**
- no glyph, just emitted light. This is the bloom medium.

A character with a dim background and a bright foreground reads as a cell inside
a lit volume. This is ambient lighting / depth cueing.

### 4d - C12: Bloom / Exterior Glow (new territory)

Bloom = bright foreground pixels above a threshold bleed spatially into
surrounding space cells via their background color channel.

**Algorithm:**

```
1. Identify ink cells (mask >= 0.5)
2. Compute outward SDF: for each space cell, dist = min distance to nearest ink cell
3. For each space cell where dist <= bloom_radius:
     intensity = exp(-dist * falloff_rate)  # exponential decay
     bloom_color = lerp(glyph_color, black, 1 - intensity)
     write \033[48;2;r;g;bm + " " to that cell
4. For ink cells: optionally boost foreground brightness based on fill float
   (the "core" - simulates the bright center of a light source)
```

**Bloom color source options:**
- Fixed color (e.g. always orange for fire theme)
- Nearest ink cell's foreground color (spatially correct, more complex)
- Fill float value of nearest ink cell (physically motivated)
- Constant per-preset (simplest, most controllable)

**What it produces:**
- Neon text: glowing colored halo in surrounding space
- Flame fill: fire that lights the air around the letters
- Plasma fill: pulsing light that bleeds outward as the field peaks
- Any colored fill: letters appear to emit light into the terminal

**This is completely unexplored in ASCII art tooling.** No existing library
(asciimatics, aalib, jp2a, blessed, textual) uses background color for spatial
light bleeding. Patent-flag candidate.

### 4e - C13: HDR Tone Mapping **`done` 2026-04-09**

Replaces the linear float→char mapping inside fill functions with a named
tone curve. Applied as a post-step before char selection.
`apply_tone_curve(float_grid, curve)` in `justdoit/effects/color.py`. Supports `blown_out:N` threshold suffix.

| Curve | Formula | Visual character |
|-------|---------|-----------------|
| `linear` | `t_out = t_in` | current behavior, reference |
| `reinhard` | `t_out = t_in / (1 + t_in)` | soft rolloff, shadow detail preserved |
| `aces` | approx. polynomial | punchy mids, cinematic highlights, industry standard |
| `blown_out` | `t_out = 1.0 if t_in > threshold else t_in / threshold` | values above threshold → densest char (`@`/`█`), simulates overexposure |

Most impactful on fills with high dynamic range (flame, plasma, fractal).
With `blown_out`, the hot core of a flame becomes solid `@` while the
cooling outer cells retain density variation - distinctly different look from
the current soft gradient.

**Implementation:** ~15 lines. Add `tone_curve` param to fill functions or
apply as a pre-processing step on the fill float grid before char mapping.

### 4f - Light model axes (future)

| Concept | Description | Depends on |
|---------|-------------|-----------|
| Z-depth color | color by extrusion depth layer | S03 isometric |
| Surface normal color | color by face orientation | N11 3D font renderer |
| Specular highlight | bright spot that moves per frame | any spatial output |
| Ambient occlusion | darkening at char density clusters | fill float |
| Chromatic aberration | RGB channels offset slightly | post-process |
| Phosphor glow | CRT green/amber bloom | C12 + green palette |
| Scanline shading | alternating dim/bright rows | post-process |

---

## Axis 5 - ANIMATION (time)

How any of the above changes between frames.

### 5a - Animation sources (what drives the change)

| Source | Description |
|--------|-------------|
| param sweep | single float stepped across frames (t, phase, seed, depth) |
| state evolution | sim state advanced N steps per frame (CA, RD, turing, slime) |
| stochastic | independent random per frame (flame, glitch, neon) |
| scripted | hand-authored keyframes / state machine (neon_startup) |
| physics | particles with velocity/gravity (A11, N12) |
| coupled | two fill outputs cross-modulated (A08d plasma→flame cooling) |
| reactive | driven by external signal (audio FFT, video frame) |

### 5b - Animation targets (what the change affects)

| Target | Examples |
|--------|---------|
| fill chars | plasma_wave, flame_flicker - chars change each frame |
| color only | neon_glitch, pulse - chars fixed, color changes |
| spatial | sine_warp phase, iso depth - geometry shifts |
| color + chars | A10c lava lamp - both driven by same field |
| structure | Turing morphogenesis - fill topology changes as sim runs |
| coupled layers | A08d - two fills modulate each other |

### 5c - Loop strategies

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
| X_WARP_PULSE | S01 sine_warp + A04 pulse | amplitude oscillates - text breathes AND waves |

### C11 infrastructure - DONE (2026-04-06)

fill_float_colorize(text, float_grid, palette) → str implemented in justdoit/effects/color.py.
Standard palettes: FIRE_PALETTE, LAVA_PALETTE, SPECTRAL_PALETTE, BIO_PALETTE.
PALETTE_REGISTRY maps names to lists. Unlocks the full tier below.

### Needs C11 (fill-float → per-cell color)

**Note:** `plasma_float_grid()` in generative.py is the established pattern for exposing fill float data to C11 colorization. Future C11 consumers (A08c, A_F09b, X_TURING_BIO, X_FRACTAL_CLASSIC) should follow the same pattern: add a `*_float_grid()` companion function alongside the fill function.

| ID | Combination | Notes | Status |
|----|-------------|-------|--------|
| A08c | flame + fire_palette | hot base, cool tips, sin ripple | **`done` 2026-04-09** |
| A10c | plasma + lava_palette | both chars and color from plasma float | **`done` 2026-04-06** |
| A_F09b | wave + spectral | interference fringes colored | `idea` |
| A_VOR1 | voronoi + cell_palette | stained glass | **`done` 2026-04-06** |
| X_TURING_BIO | turing + bio_palette | leopard/zebra coat colors | `idea` |
| X_FRACTAL_CLASSIC | fractal + escape_palette | classic Mandelbrot color bands | `idea` |

### Needs C12 (bloom infrastructure)

| ID | Combination | Visual interest | Notes |
|----|-------------|----------------|-------|
| X_NEON_BLOOM | neon fill + C12 bloom | tension=5 emerge=4 distinct=5 wow=5 → 19 | Neon chars glow into surrounding space. Neon color defines bloom hue. Minimal exterior radius (2-3 cells). | **`done` 2026-04-08** (patent-review branch) |
| X_FLAME_BLOOM | flame fill + C12 bloom + C13 blown_out | tension=5 emerge=5 distinct=5 wow=5 → 20 | Hot core blows out to solid chars; bloom bleeds orange light into surrounding space. Fire that lights the air. Highest-score combo in catalog. | **`done` 2026-04-09** |
| X_PLASMA_BLOOM | plasma fill + C12 bloom | tension=4 emerge=4 distinct=5 wow=4 → 17 | Bloom radius oscillates with plasma field value — exterior glow breathes with the wave. |
| A_BLOOM1 | C12 bloom radius + sin animation | tension=4 emerge=4 distinct=5 wow=5 → 18 | Bloom breathes in/out around any fill. Combined with flame interior: pulsing fire halo. | **`done` 2026-04-10** |

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
| X_FLAME_ISO_BLOOM | flame fill + iso extrude + C12 bloom | **flagship**: burning 3D letters that light the surrounding space. Depth face is ember-shaded; exterior cells glow orange from bloom falloff. Three axes: fill, spatial, light. |
| X_TURING_WARP | turing spots/stripes modulate sine_warp phase per row | letters warp in the pattern of their own skin |
| X_RD_PLASMA | reaction-diffusion fill spatially modulated by plasma field | two generative systems layered, plasma shapes where RD can grow |
| X_FRACTAL_ZOOM_ANIM | fractal fill + zoom animation + C11 escape bands | zoom into Mandelbrot live inside letterforms, colored |
| X_LIVING_COLOR | CA fill animated (A06) + C11 step-count color | cells age, older cells shift hue toward red/orange |

---

## S03 Isometric - Specific Cross-Breed Ideas

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

~~1. **C11** - fill-float → per-cell color. Unlocks 6+ C11-gated combos.~~ **DONE 2026-04-06**
~~A_VOR1 - Voronoi Stained Glass. First C11 consumer. Score 19/20.~~ **DONE 2026-04-06**
~~A10c - Plasma Lava Lamp. Second C11 consumer. Score 18/20.~~ **DONE 2026-04-06**
~~1. **C12** - bloom / exterior glow via background color channel. Unlocks 4+ bloom combos. ~60 lines. **Patent-flag before shipping.**~~ **DONE 2026-04-08** (patent-review branch only)
~~X_NEON_BLOOM - neon + C12. First C12 consumer. Score 19/20.~~ **DONE 2026-04-08** (patent-review branch only)
1. ~~**C13** - HDR tone mapping curves inside fills.~~ **`done` 2026-04-09** - `apply_tone_curve()` with linear/reinhard/aces/blown_out.
2. ~~**A08c** - flame gradient + sin-wave color.~~ **`done` 2026-04-09** - `flame_gradient_color()` in presets.py.
3. ~~**X_FLAME_BLOOM** - flame + C12 + C13 blown_out. Score 20/20.~~ **`done` 2026-04-09** - `flame_bloom()` flagship 20/20 composite.
~~4. **A_BLOOM1** — bloom pulse. Breathing bloom radius around burning letterforms. Score 18/20.~~ **DONE 2026-04-10**
4. **A_N09a** — Turing morphogenesis animation. Standalone, highest scientific novelty.
5. **A_ISO1** — isometric depth animation. Short, makes S03 come alive.
6. **A08d** — plasma-modulated flame. Fill-float→fill-param coupling. Most novel generative cross-breed.
7. **X_FLAME_ISO_BLOOM** — flame + iso + bloom. Three axes. The project’s flagship composite visual.

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
done all at once - C11 can be implemented as a post-process function that accepts
the string output + a separately computed float grid, which is how A08c works today
(derive the palette from row index, not the actual heat values). The "proper" version
that routes actual fill floats comes later and is the unlock for A08d and the spatial
modulation family.

---

## C12 Architecture Sketch

This section is a pre-implementation design spec for the bloom effect so the
implementing session starts with a clear plan rather than designing on the fly.

### The dual-channel opportunity

Every terminal cell has two independent 24-bit color channels:
- **Foreground** `\033[38;2;r;g;bm` - the ink character color. Currently used.
- **Background** `\033[48;2;r;g;bm` - the cell background. **Currently unused.**

A space character (`" "`) with a bright background is a pure light-emitting cell.
No glyph, no density - just a colored rectangle of terminal real estate. This is
the bloom medium.

### Function signature

```python
def bloom(
    text: str,
    ink_mask: list[list[bool]],
    bloom_color: tuple[int, int, int],
    radius: int = 4,
    falloff: float = 0.9,
    core_boost: bool = True,
) -> str:
    """Apply bloom glow to space cells surrounding ink cells (C12).

    For each space cell within `radius` steps of an ink cell, sets the
    background color to `bloom_color` attenuated by exponential falloff:
        intensity = falloff ** distance   (distance in cells, 1-indexed)

    :param text: Multi-line rendered string (may contain existing ANSI).
    :param ink_mask: 2D bool grid - True where ink cells are (same shape as text grid).
    :param bloom_color: (r, g, b) tuple for the bloom hue.
    :param radius: Max cells outward from ink to apply bloom (default 4).
    :param falloff: Per-cell intensity falloff factor, 0-1 (default 0.9 → ~66% at dist=4).
    :param core_boost: If True, brighten foreground of ink edge cells slightly (inner glow).
    :returns: Multi-line string with background ANSI codes on bloom cells.
    """
```

### Algorithm (pure Python, no numpy)

```
1. Parse text grid into (char, fg_color) per cell
2. Identify ink cells from ink_mask
3. For each space cell (ink_mask == False):
     min_dist = min(chebyshev_distance(cell, ink) for ink in ink_cells in radius)
     if min_dist <= radius:
         intensity = falloff ** min_dist        # exponential decay
         r = int(bloom_color[0] * intensity)
         g = int(bloom_color[1] * intensity)
         b = int(bloom_color[2] * intensity)
         write \033[48;2;{r};{g};{b}m + " " + \033[0m
4. If core_boost: for ink cells adjacent to space cells, brighten fg slightly
5. Return assembled string
```

**Performance note:** naive O(space_cells × ink_cells) is acceptable for
terminal-width text (~80×24 = 1920 cells). If slow, precompute a distance
transform (BFS from all ink cells simultaneously) - O(cells) instead.

### Bloom color strategies

The simplest and most controllable: pass a fixed `bloom_color` per preset.

| Preset | bloom_color | Notes |
|--------|------------|-------|
| fire | (255, 80, 0) | deep orange |
| neon_cyan | (0, 220, 255) | cyan plasma |
| neon_magenta | (255, 0, 200) | magenta tube |
| cold | (100, 150, 255) | cool blue |
| plasma | derived from current plasma value | varies per frame |

Future extension: per-cell bloom color derived from nearest ink cell's actual
foreground RGB - spatially accurate but more complex. Implement fixed-color first.

### Output compatibility

The bloom function emits `\033[48;2;...m` background codes and `\033[0m` resets.
Downstream SVG/PNG exporters in `justdoit/output/` need to handle background
color tokens - check and extend the tokenizer in `color.py` if needed.

The SVG exporter in `svg.py` currently writes `<rect>` background fills per char
(check `_bg_color` param) - confirm it handles the background ANSI codes before
calling bloom a gallery-ready technique. If the SVG exporter can't render it,
bloom is terminal-only for now and should be flagged as such in TECHNIQUES.md.

### ⚠️ Patent flag

The use of terminal background color channel as a spatial light-bleeding medium
applied to ASCII art output does not appear in any prior art in:
- asciimatics, aalib, jp2a, blessed, textual, rich (all checked)
- Any ASCII art research paper known to us

**Do not commit the C12 implementation to the public repo without flagging
to Jonny first.** This is a candidate for IP review.

---

*Maintained by NumberOne. Update after each session that adds new cross-breed ideas.*
