# JustDoIt Research Log

Aggregated findings from daily research sessions.
Each entry: source, technique, novelty score (1-5), priority, status.

---

## Aggregation System

### Novelty Score
- **5** — No known Python implementation exists. Genuinely new.
- **4** — Exists in other languages/tools, not in Python ASCII art.
- **3** — Exists in Python, not in a modern/clean package.
- **2** — Common technique, worth having for completeness.
- **1** — Standard, already done to death.

### Status
- `idea` — Logged, not yet designed
- `planned` — Scoped for implementation
- `in-progress` — Currently being built
- `done` — Implemented and tested
- `deferred` — Valid but lower priority
- `superseded` — Better approach found

### Priority Queue
Reordered after each session. Top = next bite.

| Priority | Technique | ID | Novelty | Status |
|----------|-----------|-----|---------|--------|
| 1 | SDF Font Generator | G04 | 5 | `idea` |
| 2 | Turing Pattern | N09 | 5 | `idea` |
| 3 | Wave Interference Fill | F09 | 4 | `idea` |
| 4 | Voronoi Fill | F07 | 4 | `idea` |
| 5 | Plasma Wave Animation | A10 | 4 | `idea` |
| 6 | Flame Simulation | A08 | 4 | `idea` |
| 7 | Fractal Fill (Mandelbrot) | F05 | 4 | `idea` |
| 8 | Chromatic Aberration | C08 | 5 | `idea` |
| — | Typographic Recursion | N01 | 5 | `done` |
| — | L-System Growth | N06 | 5 | `done` |
| — | Strange Attractor | N08 | 5 | `done` |
| — | Slime Mold Simulation | N10 | 5 | `done` |

---

## Sessions

*(Daily entries appended below)*

## Session 2026-03-24

**Research focus:** Truchet tiles (ASCII/terminal tiling patterns), reaction-diffusion Gray-Scott model, signed distance field font generation, demoscene 10-PRINT
**New techniques found:** 0 new (F10 was already registered; research confirmed implementation approach and expanded style variants)
**Sources:** Wikipedia — Truchet tiles, Gray-Scott/Reaction-Diffusion; prior knowledge of the classic C64 "10 PRINT CHR$(205.5+RND(1)); : GOTO 10" demoscene one-liner
**Key insight:** Truchet tiles have a beautiful connection to the demoscene 10-PRINT C64 BASIC one-liner — just two diagonal chars (╱╲) assigned randomly. The Unicode box-drawing charset extends this to arc connectors (╰╮╭╯) that create smooth labyrinth patterns, and half-blocks (▀▄) that feel more like tile art. All are achieved with the same trivially simple algorithm: per-cell coin flip. Implemented 6 style variants (diagonal, arc, arc2, cross, block, sparse) with bias control.
**Priority queue update:** Placed F04 Reaction-Diffusion at #1 — it's the natural follow-on from the generative fill space, most visually dramatic, and well-understood algorithmically (Gray-Scott is a classic simulation). N10 Slime Mold is the other very-weird option queued next.

## Session 2026-03-24 (evening)

**Research focus:** Reaction-diffusion Gray-Scott model, Gray-Scott parameter sets (coral/spots/maze/worms/zebra), pure-Python numerical simulation on small glyph masks, upscaling strategy for spatial simulations
**New techniques found:** 0 new (web search unavailable; research from prior knowledge of Gray-Scott literature, Karl Sims 1994 tutorial, and Pearson 1993 parameter map)
**Sources:** Pearson (1993) "Complex Patterns in a Simple System" Science 261, 189–192; Karl Sims Gray-Scott parameter exploration; Xenomachina Gray-Scott interactive explorer reference values
**Key insight:** Gray-Scott RD on tiny ASCII glyph masks (7×6 cells) requires an upscale-simulate-downsample strategy — patterns need room (~30×30 cells minimum) to establish before the boundary kill effect dominates. Also discovered that "coral" f=0.060 k=0.058 converges to a trivial homogeneous fixed point; better parameter tuning comes from numerical exploration of the (f,k) phase space. For thin-stroke glyphs where V dies entirely (too much boundary), using inverted-U as the signal source recovers meaningful spatial variation. The full system now degrades gracefully through three fallback levels: V-based → U-based → Perlin-based.
**Priority queue update:** F04 complete. N10 (Slime Mold / Physarum polycephalum simulation) promoted to #1 — it uses agent-based simulation rather than PDE, which sidesteps the grid-size problem entirely. Each agent explores the mask with chemotaxis, naturally adapting to boundary shape.

## Session 2026-03-26

**Research focus:** Physarum polycephalum agent-based simulation (slime mold), Jones (2010) chemotaxis algorithm, sensor-motor-deposit model, boundary confinement strategies for glyph-constrained agent sims
**New techniques found:** 0 new (web search unavailable; session implemented N10 from prior knowledge of Jones 2010 and Physarum literature)
**Sources:** Jeff Jones (2010) "Characteristics of Pattern Formation and Evolution in Approximations of Physarum Transport Networks" Int. Journal of Unconventional Computing; prior knowledge of agent-based chemotaxis models
**Key insight:** The Physarum simulation adapts beautifully to the glyph-mask constraint because it's agent-based rather than PDE-based. Agents that hit the mask boundary simply pick a new random heading — no ghost cells or Neumann conditions required. The resulting trail maps form organic vein-like networks that trace the interior shape of each letter. Sensor angle is the most expressive parameter: narrow angles (~15°) yield fine parallel filaments; wide angles (~45°) yield dense branching networks. Decay rate controls whether ancient paths fade or accumulate indefinitely. Three output files generated showing range.
**Priority queue update:** N10 complete. Next: N08 (Strange Attractor — Lorenz/Rössler projected into glyph mask, novelty 5) is now #1. Agent-based and chaotic-system approaches are proving more robust than PDE on small grids, so N08's projection approach should work well. N06 (L-System Growth) is #2.

## Session 2026-03-27

**Research focus:** Strange attractors for ASCII fill — Lorenz system, Rössler system, De Jong discrete map, Clifford attractor. Trajectory-density projection approach for glyph mask fill. Histogram binning and log1p compression techniques.
**New techniques found:** 0 new (web search unavailable; implemented N08 from prior knowledge of Lorenz 1963, Rössler 1976, Peter de Jong map, and Clifford Pickover attractor literature)
**Sources:** Lorenz E.N. (1963) "Deterministic Nonperiodic Flow" J. Atmos. Sci. 20:130–141; Rössler O.E. (1976) "An equation for continuous chaos" Phys. Lett. A 57(5):397–398; Peter de Jong (iterated function system); Clifford Pickover "Chaos in Wonderland" (1994); prior knowledge of 2D density histogram visualization
**Key insight:** The density histogram approach generalises beautifully across attractor types. Lorenz and Rössler are continuous ODEs (RK4 integration) yielding orbits that densely cover a bounded region; De Jong and Clifford are discrete maps that iterate instantly. All four fill the glyph mask with a density field that reflects the chaotic geometry — the dense core of the Lorenz butterfly maps to heavy chars, the sparse orbital arms map to light chars. Log1p compression is essential: raw hit counts have 100:1 dynamic range, which collapses to ~1:1 without it. The 120×120 bin histogram acts as an intermediary "canvas" sampled at glyph-mask resolution, decoupling attractor scale from glyph scale entirely. 41 tests, all passing.
**Priority queue update:** N08 complete. Next: N06 (L-System Growth — Lindenmayer system branching inside glyph, novelty 5) is now #1. L-systems are string-rewriting systems that produce self-similar branching structures; constraining growth to the glyph mask boundary should produce elegant fractal letterforms.

## Session 2026-03-28

**Research focus:** Lindenmayer systems for ASCII art fill — classic L-system presets from "The Algorithmic Beauty of Plants" (Prusinkiewicz & Lindenmayer, 1990), Heighway Dragon curve, Koch snowflake variants, turtle-graphics rendering, Bresenham rasterisation of fractal geometry, density histogram approach (identical to N08 but with geometric instead of chaotic source).
**New techniques found:** 0 new (web search unavailable; implemented N06 from prior knowledge of L-system literature and Prusinkiewicz & Lindenmayer 1990)
**Sources:** Prusinkiewicz & Lindenmayer (1990) "The Algorithmic Beauty of Plants" Springer; Lindenmayer A. (1968) "Mathematical models for cellular interactions in development" J. Theor. Biology 18; Heighway J. (1966) Dragon curve (first described); Koch H. von (1904) "Sur une courbe continue sans tangente, obtenue par une construction géométrique élémentaire" Ark. Mat. Astron. Fys. 1(3); prior knowledge of turtle graphics (Logo, LOGO derivatives)
**Key insight:** The density histogram approach generalises perfectly from attractor trajectories to L-system segments — instead of ODE trajectory points we rasterise turtle-graphics segments via Bresenham's algorithm into the same 120×120 bin canvas. The fractal self-similarity of L-systems means the density field has a characteristic multi-scale structure: the trunk region gets painted many times (high density → dense chars), while terminal branches appear once (low density → light chars). This matches the visual metaphor perfectly — letters filled with botanic growth, reading from dense root to fine leaf tip. 8 named presets covering plant, fern, sierpinski, dragon, bush, algae, tree32, crystal. 50 tests, all passing.
**Priority queue update:** N06 complete. Next: N01 (Typographic Recursion — glyphs made of smaller instances of the same text, novelty 5) is now #1. N09 (Turing Pattern — reaction-diffusion yielding biological spot/stripe patterns, distinct from N10's Gray-Scott approach) is now #3.

## Session 2026-03-28 (evening) — F07 shape fill implementation

**Research focus:** Implementing F07 shape-vector / contour-following fill inspired by the alexharri.com/blog/ascii-rendering 6D zone density technique. Three full implementation attempts. Gallery pipeline fixes (text default, cache, section labels).

**New techniques found:** F07 shape fill (v3 — 4-neighbor connectivity), now `done`.

**Sources:** alexharri.com/blog/ascii-rendering (6D sub-zone density vectors); empirical SDF diagnostic on block font glyph masks.

**Key insight:** Three implementations were required before arriving at a working approach. The alexharri 6D zone technique needs many source pixels per output cell to produce stable zone density vectors. A binary glyph mask at 1:1 character resolution cannot satisfy this — all zone averages collapse to 0 or 1, making nearest-character matching meaningless (v1). SDF gradient angle as a proxy also fails: BFS on a small binary grid produces only 4 unique normalized SDF levels, so all edge cells share the same value and gradient computation yields pure quantization noise (v2). The correct approach at character resolution is direct 4-cardinal-neighbor connectivity analysis: which of the four neighbors (top/bottom/left/right) are empty determines which boundary is passing through the cell, which maps deterministically to `|`, `-`, `/`, `\`, `+`. This is v3 (current implementation). `O` now renders `/---\`…`\---/`, corners and strokes are clean and legible.

**Remaining limitation:** Block font strokes are 2 cells wide. At that width every ink cell has at least one empty cardinal neighbor, so the interior density ramp never activates — the result is a wireframe outline rather than a filled letter. See improvement ideas (G05, S04) logged below.

**Work completed tonight:**
- F07 v1 implemented and diagnosed (6D zone → random chars — broken)
- F07 v2 implemented and diagnosed (SDF gradient → noise — broken)
- F07 v3 implemented, 25 tests written, 305 total passing
- Gallery default text fixed (JDI → JUST DO IT) — JDI was 21 cols wide, magnified 2.5× at img width=480, making chars look huge
- Gallery F07 entry added to curated showcase in `generate_gallery.py`
- GitHub Pages cache bust required (Ctrl+Shift+R) after each push

**Priority queue update:** F11 shape-vector fill is `done` (labelled F07 in gallery). Future work: G09 (GenAI logo-to-image → shape fill) and N11 (3D font renderer → normal-mapped shape fill) logged as `idea`.

---

## Session 2026-03-28 (F07 shape fill — lessons learned & improvement ideas)

**Research focus:** Post-implementation analysis of F07 shape-vector / contour-following fill; why the alexharri.com 6D zone approach fails at character resolution; what would make the fill visually compelling.

**Sources:** alexharri.com/blog/ascii-rendering; empirical SDF diagnostic on block font glyph masks; visual comparison of v1 (6D zone), v2 (SDF gradient angle), v3 (4-neighbor connectivity).

**Key insight:** Three implementations were tried before landing on v3 (4-neighbor connectivity):
- **v1** (6D zone matching): fails because block font mask is binary 1:1 — the Pillow char DB measures sub-pixel zone density within a single cell, but mask zones are character-level averages across neighbors. Incompatible coordinate spaces → random character output.
- **v2** (SDF gradient angle): fails because BFS on a binary mask produces only 4 unique SDF values (0.0, 0.25, 0.75, 1.0). All edge cells land at the same SDF level with no meaningful gradient signal → quantization noise.
- **v3** (4-neighbor connectivity, current): correct for character resolution. Reads which of the 4 cardinal neighbors are empty and assigns `|`, `-`, `/`, `\`, `+` accordingly. `O` → `/---\`…`\---/`; corners, verticals, horizontals all deterministic.

**Remaining visual limitation:** Block font uses 2-cell-wide strokes (██). At that width, every ink cell has at least one empty cardinal neighbor, so ALL cells are edge cells — no interior density ramp activates. The result is a wireframe outline rather than a filled letter. The fill is technically correct but looks sparse compared to the solid █ block font.

**Three concrete improvement paths (not yet implemented):**

1. **Color overlay on F07** — thin directional chars (`|/-\`) look underwhelming in monochrome but become visually striking when colored. A horizontal or radial gradient over the shape fill would make it gallery-worthy with minimal effort. Add a `S-F07-shape-fill-gradient` showcase entry pairing `render(text, font="block", fill="shape")` with `linear_gradient(..., direction="horizontal")`.

2. **F07 with wider-stroke fonts** — FIGlet `big` and `slant` fonts have 4–8 cell strokes. At that width, interior cells (all 4 cardinal neighbors have ink) appear, and the 8-neighbor density ramp activates. The combination of edge directional chars at the boundary and density chars in the interior would produce the "filled sketch" effect that the article shows. Add showcase entries for `font="big", fill="shape"` and `font="slant", fill="shape"`.

3. **Heavier directional characters** — `|` and `-` are among the thinnest ASCII chars. Substituting Unicode box-drawing (`│ ─ ╱ ╲`) or block-adjacent chars (`▏▕ ▁▔`) would increase visual weight without changing the logic. These are not pure ASCII but are within standard terminal charset ranges.

**Numbering note:** The priority queue lists "Voronoi Fill" as F07. The shape-vector fill was assigned F07 during implementation. One of these needs renumbering — suggest Voronoi Fill → F08 and adjusting the queue accordingly.

---

### Idea — G09: GenAI Logo-to-Image → Shape Fill

**Concept:** Use a generative AI image model (DALL-E, Stable Diffusion, etc.) to produce a high-resolution logo or emblem image from a text prompt, then apply the alexharri.com 6D zone density approach to convert that image to ASCII art using the `_get_char_db()` / `_nearest_char()` pipeline already in `shape_fill.py`.

**Why this matters:** This is the scenario the alexharri approach was actually designed for — many source pixels per output character cell. A 512×512 image rendered into a 64×16 ASCII grid gives ~8×8 source pixels per cell, meaning the 6 sub-zone densities are stable and distinctive. The Pillow char DB is already implemented and cached; only the source sampling needs a new code path.

**Pipeline sketch:**
1. Call generative AI API with prompt (e.g. `"minimalist geometric lion logo, black on white"`)
2. Download resulting image
3. Resize to intermediate resolution matching desired ASCII output (e.g. 6× the output cols/rows for 6-zone sampling)
4. Sample 6 sub-zones per output cell from the greyscale image
5. `_nearest_char(vec, _get_char_db())` → character
6. Optionally apply color from the original image's dominant hue per cell

**Novelty score:** 5 — no existing Python ASCII art tool uses a generative image as the source for zone-matched character selection.
**Priority:** `idea`
**ID:** G09

---

### Idea — N11: 3D Font Renderer → Normal-Mapped Shape Fill

**Concept:** Extrude glyph outlines into a 3D mesh, render them with a software rasterizer or raytracer (depth buffer + surface normals), then use the surface normal direction at each character cell to select the directional ASCII character (`|`, `-`, `/`, `\`, plus shading chars for lit vs. shadowed faces). The 3D render provides far richer per-cell information than a binary mask — depth, normal angle, specular highlight, and shadow can all drive character selection.

**Why this matters:** The current isometric extrusion (S03) is a geometric transformation of 2D ASCII, not true 3D rendering. A real depth buffer would enable: correct perspective foreshortening, specular highlights on curved surfaces, cast shadows, and normal-mapped directional chars that actually follow the 3D surface orientation. The shape fill (F07) character logic maps directly onto surface normal direction (normal pointing up → `-`, pointing left/right → `|`, diagonal → `/\`).

**Pipeline sketch:**
1. Convert glyph mask → 2D polygon outline (marching squares or contour tracing)
2. Extrude outline to 3D mesh (add depth faces and cap faces)
3. Software rasterize with orthographic or perspective camera → depth buffer + normal buffer (pure Python or via `numpy`)
4. Per output cell: sample normal direction → `_cell_char_from_normal(nx, ny, nz)`
5. Shade by lighting angle: front-lit → dense char, shadowed → light char
6. Optionally apply color from lighting model

**Relationship to existing work:** Extends S03 (isometric extrude) and F07 (shape fill). The 3D normal map is a natural upgrade to the binary mask that F07 currently uses — same character selection logic, richer input signal.

**Novelty score:** 5 — software-rasterized 3D glyph meshes with normal-driven ASCII character selection has no known Python implementation.
**Priority:** `idea`
**ID:** N11

---

## Big Picture — ASCII as a Universal Rendering Target

The G09 and N11 ideas are two ends of the same larger concept: **ASCII characters as a rendering target for any visual input source**. The zone-density character DB (already built) and the F11 contour-following logic (already built) are the *output stage* of a rendering pipeline. What's missing is the *input stage* — anything that can produce a pixel buffer can drive them.

This reframes JustDoIt from a text-art CLI into a **universal visual-to-ASCII renderer**. Five pipeline-level ideas logged below (P01–P05 in TECHNIQUES.md):

---

### Idea — P01: Multi-layer Compositor

**Concept:** Stack multiple independent renders (different fonts, fills, color effects) as layers with configurable blend modes — multiply, screen, overlay, difference. A render pipeline that composes like Photoshop rather than applying effects sequentially. Each layer has its own mask, fill, color, and opacity. Enabling this unlocks compositional possibilities none of the individual effects can reach alone: e.g. an isometric extrusion as base, a noise fill multiplied over it, a gradient as a color layer, a slime-mold mask as a vignette.

**Why this matters:** Every current effect is a single-pass transform. Composition requires only a shared canvas abstraction — a 2D grid of `(char, r, g, b)` cells — and blend functions over that type. The hard creative work (all the fills and effects) is already done.

**Novelty score:** 5
**Priority:** `idea`
**ID:** P01

---

### Idea — P02: ASCII Video Pipeline

**Concept:** Accept any video file as input (MP4, GIF, webcam stream), process each frame with zone-matched character selection via the Pillow char DB, and output as: ANSI escape sequence file (plays in terminal), animated SVG, GIF, or re-encoded MP4 where each "pixel" is a monospaced character cell rendered at native resolution. Essentially ffmpeg with ASCII as its codec.

**Why this matters:** ASCII animation currently requires hand-crafting frame sequences. A video pipeline makes ASCII art a *derivative format* — any video content can be restyled as ASCII. The quality ceiling is determined by how well the zone-matching handles motion (temporal coherence is an interesting sub-problem: characters that flicker between frames are visually noisy, so some temporal smoothing is needed).

**Novelty score:** 5
**Priority:** `idea`
**ID:** P02

---

### Idea — P03: Live Input → ASCII

**Concept:** Real-time capture (webcam, screen capture, audio visualizer FFT) → streaming zone-matched ASCII rendered to terminal or window at interactive frame rates. A live ASCII mirror, a concert visualizer, or an ASCII photobooth. The character selection pipeline needs to run at 15–30fps on a ~80×24 output grid, which is easily achievable with the pure-Python zone DB at that resolution.

**Why this matters:** This is the demo that makes people say "wait, what?" — a terminal that shows your face in ASCII in real time is immediately shareable and memorable. It also stress-tests the full pipeline (capture → resize → zone sample → char select → render) in a way that reveals performance bottlenecks worth addressing.

**Novelty score:** 5
**Priority:** `idea`
**ID:** P03

---

### Idea — P04: AI Creative Director

**Concept:** End-to-end AI-driven ASCII creation. A brand brief or mood prompt → LLM generates art direction (color palette, style keywords, composition notes) → image AI (DALL-E / Stable Diffusion API) generates a hi-res visual matching that direction → zone-matched ASCII via G09 pipeline → JustDoIt color effects applied using LLM-suggested palette → SVG gallery output. The human provides intent; the system produces finished ASCII art.

**Why this matters:** This is the convergence of the entire JustDoIt toolchain with generative AI. ASCII becomes a first-class AI output format — not a fallback or novelty, but a deliberate aesthetic choice made by a creative pipeline. The LLM handles style decisions that currently require manual parameter tuning (which fill? which palette? which font?).

**Novelty score:** 5
**Priority:** `idea`
**ID:** P04

---

### Idea — P05: Full 3D Scene Renderer

**Concept:** Arbitrary 3D scene (camera position, point/directional lights, triangle mesh, material properties) → full software raytracer or rasterizer → per-cell surface normal + luminance → F11 char selection for normal direction + density ramp for luminance. Every character in the output is simultaneously a color sample AND a surface descriptor. Shadows, reflections, and specular highlights all encoded in character choice and color. Extends N07 (ASCII raytracer) and N11 (3D font renderer) to arbitrary geometry — not just glyphs but any 3D content.

**Why this matters:** This is the full realization of the shape-vector fill concept at scene scale. The F11 logic already maps surface normals to directional chars; the missing piece is a 3D input that generates those normals at character-cell resolution. Combined with P04, it enables: "render my brand's 3D logo in ASCII" as a complete automated pipeline.

**Novelty score:** 5
**Priority:** `idea`
**ID:** P05

## Session 2026-03-29

**Research focus:** Typographic recursion — text made of itself. Self-referential letterform rendering. Web search unavailable; worked from prior knowledge of typographic recursion as an art technique (Escher-style self-referential structures, "text as texture" approaches in computational typography, and the well-established concept in generative art of replacing pixels with meaningful symbols from the source content).
**New techniques found:** 0 new (N01 was already registered; session implemented it from first principles)
**Sources:** Prior knowledge of typographic recursion in generative art; computational typography literature; the fundamental concept that any symbol-replacement pass on a bitmapped text render yields self-similar letterforms.
**Key insight:** The implementation is deceptively simple: render the text to a grid of rows (each char is either space or an ink char), then walk every non-space cell in reading order and replace it with the next character from the source text cycling. The word "HELLO" rendered in block font has ~340 ink cells; cycling H→E→L→L→O→H→E→... replaces all 340 with meaningful characters. The effect: letterforms that "spell themselves out" at cell scale. One subtle engineering issue: the inline `colorize()` call in the render loop wraps each glyph row in ANSI escape codes — if recursion runs after colorization, it walks into the escape sequences. Fix: defer colorization until after the recursion pass completes (controlled by `defer_color` flag). This keeps the character-replacement pass on clean ASCII, then ANSI wraps the finished rows.
**Priority queue update:** N01 complete. Next: G04 (SDF Font Generator — signed distance field letterforms rasterized to any resolution, novelty 5) is now #1. Turing Pattern (N09) is #2.
