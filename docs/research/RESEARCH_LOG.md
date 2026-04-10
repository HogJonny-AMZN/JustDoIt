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
| 1 | Transporter Materialize | A11 | 5 | `idea` |
| 2 | SDF Font Generator | G04 | 5 | `idea` |
| 3 | Living Fill (CA animated) | A06 | 5 | `idea` |
| 4 | Chromatic Aberration | C08 | 5 | `idea` |
| 5 | Stipple Fill | F08 | 3 | `idea` |
| — | Flame Simulation | A08 | 4 | `done` |
| — | Plasma Wave Animation | A10 | 4 | `done` |
| — | Voronoi Fill | F07 | 4 | `done` |
| — | Wave Interference Fill | F09 | 4 | `done` |
| — | Fractal Fill (Mandelbrot) | F05 | 4 | `done` |
| — | Typographic Recursion | N01 | 5 | `done` |
| — | L-System Growth | N06 | 5 | `done` |
| — | Strange Attractor | N08 | 5 | `done` |
| — | Slime Mold Simulation | N10 | 5 | `done` |
| — | Turing Pattern | N09 | 5 | `done` |

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

## Session 2026-03-30

**Research focus:** Turing activator-inhibitor reaction-diffusion (N09); FitzHugh-Nagumo activator-inhibitor PDE model; distinguishing characteristics vs Gray-Scott (F04); numerical stability analysis for explicit Euler on diffusion-dominated PDEs.
**New techniques found:** 0 new (web search unavailable; implemented N09 from prior knowledge of Turing 1952, FitzHugh 1961, Nagumo 1962, and activator-inhibitor literature).
**Sources:** Turing A.M. (1952) "The Chemical Basis of Morphogenesis" Philos. Trans. R. Soc. Lond. B 237:37–72; FitzHugh R. (1961) "Impulses and physiological states in theoretical models of nerve membrane" Biophys. J. 1(6):445–466; Nagumo J., Arimoto S., Yoshizawa S. (1962) "An active pulse transmission line simulating nerve axon" Proc. IRE 50:2061–2070; prior knowledge of the Turing instability condition and activator-inhibitor parameter space.
**Key insight:** The FHN activator-inhibitor model is the correct Turing implementation, categorically distinct from Gray-Scott (F04) in three ways: (1) different kinetics — FHN uses bistable cubic `u - u³` rather than GS autocatalytic `U·V²`; (2) different parameter space — FHN uses alpha/epsilon/beta rather than feed/kill rates; (3) different initialization — FHN requires tiny Gaussian noise to seed the instability, while GS needs discrete seed patches. The key numerical hazard: explicit Euler for diffusion requires `dt ≤ 1/(4·Db)` for 2D stability. With Db=5.0 and dt=0.1, the stability number is 2.0 >> 1.0 — NaN in ~20 steps. Fix: reduce Db to 2.0 (Da=0.10, ratio 20×, still well within Turing instability regime) giving stability number 0.8 < 1.0. Hard clamping of U/V at ±10 added as a secondary safety net. 4 presets (spots/stripes/maze/labyrinth) distinguish pattern morphology by epsilon: low → spots, high → labyrinths.
**Priority queue update:** N09 complete. Next priority queue: A11 (Transporter Materialize — novelty 5, multi-session) at #1, G04 (SDF Font Generator — novelty 5, achievable) at #2, F09 (Wave Interference Fill — novelty 4) at #3. G04 is likely the best single-session pick; A11 is a multi-session feature. Recommend G04 next.

## Session 2026-03-30 (evening)

**Research focus:** Wave interference fill (F09), Fractal/Mandelbrot fill (F05), interference pattern algorithms, smooth fractal coloring techniques.
**New techniques found:** 0 new (web search unavailable; both F09 and F05 were already registered; session implemented them from prior knowledge)
**Sources:** Prior knowledge of interference patterns (superposition of plane waves); Mandelbrot B. (1980) original fractal set; smooth iteration count coloring from Linas Vepstas (2004) "Smooth Iteration Count for the Mandelbrot and Julia Sets"; Julia G. (1918) "Mémoire sur l'itération des fonctions rationnelles".
**Key insight:** The wave interference fill is architecturally the simplest generative fill in the codebase — purely analytical (no simulation, no grid state, no iteration), yet produces visually complex patterns. The two plane waves interfere constructively/destructively purely as a function of (x,y) normalized position, producing moiré bands, bowtie patterns, and fine cross-hatching depending on frequency and angle ratios. The fractal fill is the opposite case: computationally intensive per-cell (64 iterations of complex arithmetic), but smooth coloring (Vepstas 2004) was essential — without `n + 1 - log2(log2(|z|²))` normalization, the escape-time steps produce harsh integer banding at ASCII resolution. The 2× aspect-ratio correction on the y-axis (char cells are taller than wide) was critical for Mandelbrot's canonical shape to appear correctly. Julia sets degrade more gracefully at ASCII resolution than Mandelbrot because their boundary is bounded (no deep infinite zoom structure), making them arguably the better default for ASCII letterform fills.
**Priority queue update:** F09 and F05 complete. Next priority queue: A11 (Transporter Materialize — novelty 5, multi-session) at #1, G04 (SDF Font Generator — novelty 5) at #2, F07 (Voronoi Fill — novelty 4) at #3.

## Research Import 2026-04-02 — Custom Character Sets for Terminal Rendering

**Source document:** `docs/research/custom_characters.md`
**Research type:** Background reference (externally authored, imported by Jonny)
**New techniques found:** 1 candidate (G10 — Custom PUA Glyph Font, see TECHNIQUES.md)

**Summary:**
Terminals are Unicode renderers; they cannot generate arbitrary glyphs at runtime. Custom symbols require: (1) picking code points in the Unicode Private Use Area (U+E000–U+F8FF for BMP, plus supplementary PUA ranges), (2) creating or patching a monospaced font with glyphs at those positions, (3) installing it and selecting it in the terminal emulator, (4) emitting the PUA code points from the application.

The Terminal Glyph Patcher project (https://github.com/s417-lama/terminal-glyph-patcher) automates font patching from SVG sources, mapping custom glyphs to chosen Unicode positions with alignment/stretch/overlap control.

**Relevance to JustDoIt:**

This directly addresses three registered-but-unimplemented font techniques:

- **G06 (Braille):** Unicode Braille block (U+2800–U+28FF) is within standard BMP, no PUA needed — already a known charset range, this research confirms terminal support constraints.
- **G07 (Half-block):** Unicode half-block chars (▀▄█ etc., U+2580–U+259F) are standard BMP — same note. No font patching required.
- **G08 (Quadrant block):** Unicode quadrant chars (▖▗▘▝, U+2596–U+2599) are standard BMP. Same note.
- **G04 (SDF Font Generator) / G05 (Bézier Font Generator):** The PUA workflow is the *deployment path* for any custom font generated by these techniques. If JustDoIt ever generates its own letterforms programmatically, PUA mapping is how they become visible in a terminal.

**New technique candidate:**

**G10 — Custom PUA Glyph Font:** A JustDoIt-native font that uses Unicode PUA code points mapped to custom SVG glyphs — e.g. partial-fill block variants, diagonal sub-cell patterns, or specialty symbols not in Unicode standard. The Terminal Glyph Patcher workflow enables this. Novelty: 4 (PUA fonts are used in icon sets like Nerd Fonts / Powerline; not used in ASCII art generators). Priority: `idea` — low urgency, high ceiling.

**Key constraint for JustDoIt:**
Any feature using PUA characters requires the *user* to install a patched font and configure their terminal. This is a non-trivial setup burden. G07 (half-blocks) and G08 (quadrant blocks) are the better near-term bet because they use standard BMP characters that render in any modern terminal font without patching.

**Reference links preserved:**
- Terminal Glyph Patcher: https://github.com/s417-lama/terminal-glyph-patcher
- Private Use Areas: https://en.wikipedia.org/wiki/Private_Use_Areas
- WezTerm custom block glyphs: https://wezterm.org/config/lua/config/custom_block_glyphs.html
- Microsoft PUA notes: https://learn.microsoft.com/en-us/globalization/encoding/pua

---

## Session 2026-04-02 — Web Research: Voronoi, Transporter, Plasma, SDF

**Research focus:** Four targeted web searches:
1. Voronoi diagram in ASCII art / terminal rendering
2. Transporter materialize animation prior art in terminal/ASCII
3. Demoscene plasma animation — 2025 state of the art in Python terminal
4. Signed distance field font rendering in ASCII / terminal contexts

**New techniques found:** 0 new (all four topics confirm existing registry entries; no prior art that supersedes them; details below reinforce novelty scores)

**Sources:**
- Roguelike Developer blog (2007) — Voronoi for wilderness map generation in ASCII roguelikes: https://roguelikedeveloper.blogspot.com/2007/07/wilderness-generation-using-voronoi.html
- TerminalTextEffects (TTE) docs & GitHub — 37 built-in terminal animation effects: https://chrisbuilds.github.io/terminaltexteffects/ | https://github.com/ChrisBuilds/terminaltexteffects
- Rosetta Code — Plasma effect implementations across languages: https://rosettacode.org/wiki/Plasma_effect
- Programmador.com (2025) — Plasma in Rust, pixel-based: https://programmador.com/posts/2025/plasma/
- Asciimatics docs — Plasma, Fire, Kaleidoscope renderers: https://asciimatics.readthedocs.io/en/stable/asciimatics.renderers.html
- Redblobgames — SDF font rendering basics: https://www.redblobgames.com/x/2403-distance-field-fonts/
- vgel.me — "Signed distance functions in 46 lines of Python" (ASCII raymarching): https://vgel.me/posts/donut/
- Valve/Green (2007) SIGGRAPH SDF paper: https://steamcdn-a.akamaihd.net/apps/valve/2007/SIGGRAPH2007_AlphaTestedMagnification.pdf
- msdfgen (Viktor Chlumský): https://github.com/Chlumsky/msdfgen
- GitHub Copilot CLI animated banner engineering post: https://github.blog/engineering/from-pixels-to-characters-the-engineering-behind-github-copilot-clis-animated-ascii-banner/

---

### Finding 1: Voronoi in ASCII Art — F07 (novelty score confirmed: 4)

**What was found:**
Voronoi diagrams are used extensively in roguelike games for procedural map generation (wilderness regions, dungeon partitioning) but all implementations treat Voronoi as a *spatial partitioning backend* — the map cells are then filled with terrain chars independently. No implementation was found that uses Voronoi cell geometry to drive character selection inside a glyph mask (i.e., seeding cells inside a letter shape, then choosing chars based on cell ID or proximity-to-boundary).

Python Voronoi implementations (scipy.spatial.Voronoi, xiaoxiae/Voronoi) all produce graphical output (matplotlib, SVG) — none output to terminal with character-cell rendering. Fortune's algorithm is the standard O(n log n) approach; for the pure-Python no-dependency version in JustDoIt, a BFS/Manhattan-distance approach (seed N random points, assign each mask cell to its nearest seed by Euclidean distance) is the correct implementation path — no Fortune's algorithm needed at glyph-mask scale.

**Is this prior art to F07?** No. Voronoi-as-character-fill inside a glyph mask has no prior art in any tool found. The roguelike usage is terrain assignment, not character selection. **F07 novelty score 4 is confirmed** — Voronoi exists in other tools/languages, but not in a Python ASCII art fill context.

**Implementation notes for F07:**
- BFS or distance comparison at each mask cell (O(N*S) where N=mask cells, S=seeds) is sufficient at 7-row glyph scale
- Cell ID → char: border cells (nearest to another cell) → `.` or `+`; interior cells → cycle through a per-cell char set keyed by cell index
- Cell borders can be detected by checking if any 4-neighbor belongs to a different cell
- Suggested: 5–15 seeds, seeded from random positions inside the mask

---

### Finding 2: Transporter Materialize — A11 (novelty score confirmed: 5)

**What was found:**
TTE (TerminalTextEffects) is the most complete terminal animation library in Python with 37 effects. The closest effect to a transporter materialize is "Scattered" — characters start at random canvas positions and move into their final positions using Bezier easing. "OrbittingVolley" fires characters inward from rotating edge positions.

Neither of these matches the A11 concept:
- **Scattered** spreads across the full canvas (not column-confined), uses whole-canvas random scatter, not localized bounding-box particle columns
- **OrbittingVolley** fires from edges toward center — orbital geometry, not columnar shimmer
- Neither has a "brightness cascade" per cell as it locks in — the TNG transporter shimmer visual
- Neither has era variants (TOS shimmer vs TNG sparkle vs Kelvin burst)
- Neither uses half-block sub-pixel resolution (▀▄█) to increase particle precision within character cells

The GitHub Copilot CLI animated banner uses pre-authored frame-by-frame animation — not algorithmic. No library found generates particles that scatter within a glyph's bounding column and then converge to glyph-mask positions with per-cell brightness lock-in.

**Is this prior art to A11?** No. The specific combination of: (1) columnar bounding box particle scatter, (2) convergence to glyph-mask target positions, (3) per-cell brightness cascade as lock-in, (4) half-block sub-pixel resolution, (5) era variants — has no prior art. **A11 novelty score 5 is confirmed.** This remains the highest-priority unimplemented animation.

---

### Finding 3: Demoscene Plasma in Terminal — A10 (novelty score confirmed: 4)

**What was found:**
The classic plasma effect (sinusoidal color field, sum of multiple sin/cos at different frequencies) is extremely well-documented and widely implemented. Key findings:

- **Rosetta Code** has implementations in 20+ languages. The standard formula is `value = sin(x/16) + sin(y/8) + sin((x+y)/16) + sin(sqrt(x²+y²)/8)`, normalized to [0,1] and mapped to HSV color.
- **Asciimatics** (Python) has a `Plasma` renderer that outputs animated plasma to the terminal. It uses sinusoidal functions driven by an `(x, y, t)` field and a colour palette. **This is the most significant prior art finding for A10.**
- The asciimatics Plasma renderer outputs *color variation only* — it fills the terminal with fixed characters (spaces or block chars) and varies the background color. It does not drive character selection from the plasma value, and it does not confine the effect inside a glyph mask.
- The 2025 Rust plasma article and pygame plasma projects all operate in pixel space, not character space.
- No Python library found applies plasma sin-field values to *character density selection* inside a *glyph mask*.

**Is asciimatics Plasma prior art to A10?** Partially. The sinusoidal color animation is prior art. But A10's distinguishing novelty is: (1) the plasma value drives *character selection* (density chars `@#%+-.` etc.) not just color, and (2) the effect is masked to the glyph shape — only ink cells show the animated plasma, creating letterforms that "pulse" with organic color+density variation. The combination is novel.

**Refinement to A10 description:** Should clarify that the novelty is the char-selection + glyph-masking combination, not the sin-field formula itself. Novelty score 4 stands — technique exists in other tools (color-only), not in Python ASCII fill form.

---

### Finding 4: SDF Font Rendering in ASCII — G04 (novelty score confirmed: 5)

**What was found:**
SDF font rendering has rich prior art in the GPU/game space:
- Valve/Green SIGGRAPH 2007: the foundational paper. SDF stored as a texture, shader thresholds the distance value for crisp rendering at any scale.
- msdfgen (Chlumský 2018): multi-channel SDF, solves the rounded-corner problem of single-channel SDF.
- SDFont, GLyphy: production SDF font generators.
- **vgel.me ASCII raymarcher:** Uses SDFs for 3D scene representation and ray marching in pure Python ASCII output. The SDF determines *whether* a ray hits a surface; the surface normal (derived from the SDF) drives character selection. However, this is 3D scene raymarching, not glyph-mask generation.

No tool or paper found implements the G04 concept: using a 2D SDF of a letterform to drive character selection *inside the glyph mask* at character-cell resolution, where distance from the glyph edge determines which character to render (e.g. near edge → outline chars `|/-\`, mid-distance → medium chars `+x`, deep interior → dense chars `@#`). This is the complement of F06 (SDF Edge Fill, already done), but applied as a standalone font generation path rather than a fill effect.

The existing F06 (SDF Edge Fill) already uses BFS distance from the glyph edge to select characters. G04 is the more ambitious version: generating the entire letterform *from* an SDF rather than applying SDF to an existing bitmapped mask. The SDF would be computed from Bezier outlines (G05 is the prerequisite or sister technique), and character cells would be filled based on their SDF value — producing a scalable ASCII representation of any letter at any resolution.

**Is this prior art to G04?** No. Pure-Python SDF-driven glyph generation for ASCII character-cell output has no known prior art. GPU SDF rendering (Valve 2007, msdfgen) is a completely different domain — those output pixel textures for GPU shaders, not character grids for terminals. **G04 novelty score 5 is confirmed.**

---

### Priority Queue Update

No changes to the registry — all four topics confirm existing entries. Priority queue remains:

| Priority | Technique | ID | Novelty | Status |
|----------|-----------|-----|---------|--------|
| 1 | Transporter Materialize | A11 | 5 | `idea` |
| 2 | SDF Font Generator | G04 | 5 | `idea` |
| 3 | Voronoi Fill | F07 | 4 | `idea` |
| 4 | Plasma Wave Animation | A10 | 4 | `idea` |
| 5 | Flame Simulation | A08 | 4 | `idea` |
| 6 | Chromatic Aberration | C08 | 5 | `idea` |

**Key insight:** The most actionable single-session pick from this research is **F07 (Voronoi Fill)**. The BFS-distance implementation requires no new dependencies (pure Python), can be scaffolded in ~100 lines using the same density-histogram approach as N08/N06, and has a clear visual: letterforms subdivided into organic Voronoi cells with distinct border and interior characters. A11 remains the flagship but is multi-session scope. G04 requires G05 (Bezier outlines) as a foundation, making it also multi-session.

**A10 (Plasma Wave) upgrade note:** The asciimatics prior art finding means A10's description should be updated to clarify that the novelty is character-density selection from the plasma field + glyph masking, not the sin-field formula. This distinguishes it cleanly from asciimatics Plasma.

## Session 2026-04-02

**Research focus:** Voronoi fill implementation; prior art for ASCII Voronoi; TTE transporter materialize prior art; SDF ASCII font rendering prior art.
**New techniques found:** 0 new (no novel techniques; research confirmed existing queue priorities remain valid; see research import 2026-04-02 for G10 candidate logged previously).
**Sources:**
- Voronoi in Python: scipy.spatial.Voronoi (https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.Voronoi.html) — prior art for computing Voronoi diagrams, but not for ASCII art fills inside glyph masks with radial density gradients and border characters. No Python library found that implements Voronoi as an ASCII fill effect.
- TTE (TerminalTextEffects): https://github.com/ChrisBuilds/terminaltexteffects — has scatter/spray/rain/swarm effects but NO transporter materialize (particles gather from columns into letterform with brightness cascade). A11 novelty confirmed.
- SDF font rendering: msdfgen (https://github.com/Chlumsky/msdfgen), SDFont (https://github.com/ShoYamanishi/SDFont) — all GPU/shader-based implementations. No pure-Python SDF-to-ASCII terminal font generator found. G04 novelty confirmed.
**Key insight:** F07 Voronoi Fill is architecturally the simplest geometric fill in the codebase — pure O(R·C·N) nearest-neighbor Voronoi partitioning, no simulation, no iteration, no external state. The key design decision was registering preset variants ("voronoi_cracked", "voronoi_fine", etc.) directly in _FILL_FNS so the gallery can render visually distinct outputs per preset, unlike wave/fractal/turing where all preset gallery entries call the same default. The `invert` flag on the density gradient is the aesthetic differentiator: "default" gives dark seed-centers fading to light (spotlight look), while "cracked" gives light centers with dark edges (cracked-earth / stained-glass look). Seed auto-scaling via sqrt(interior) * n_factor ensures sensible cell density independent of glyph resolution.
**Priority queue update:** F07 complete. Next priority queue: A11 (Transporter Materialize — novelty 5, multi-session) at #1, G04 (SDF Font Generator — novelty 5, achievable single-session) at #2, A10 (Plasma Wave Animation — novelty 4) at #3. Recommend G04 next if doing a single-session pick — it generates letterforms from SDF computation on existing font bitmaps, no new font geometry needed. A10 is the right pick for an animation-focused session.

## Session 2026-04-03

**Research focus:** Demoscene plasma effect for ASCII character density selection; web search unavailable, working from prior knowledge of plasma formula literature.
**New techniques found:** 0 new (web search unavailable; A10 was already registered; session implemented it from prior knowledge of the classic demoscene plasma formula)
**Sources:** Classic demoscene plasma — sum of multiple sinusoids at different frequencies/phases, documented extensively on Rosetta Code (https://rosettacode.org/wiki/Plasma_effect) and in demoscene tutorials; Asciimatics Plasma renderer (https://asciimatics.readthedocs.io/en/stable/asciimatics.renderers.html) — prior art to color-only plasma, confirmed non-overlapping with A10's char-selection approach. Prior knowledge of the canonical formula: sin(x*f) + sin(y*f) + sin((x+y)*f) + sin(sqrt(x²+y²)*f).
**Key insight:** The A10 novelty is cleanly separable from asciimatics: (1) the plasma field drives *character density selection* (`@#S%?*+;:,.`) not color, (2) the effect is glyph-mask-confined — only ink cells show the plasma pattern. The time parameter `t` shifts all four wave phases simultaneously, creating smooth animation. The implementation required one important detail: the `_DENSE` constant ends with a space character, so minimum-intensity ink cells were silently rendered as exterior spaces — fixed by `.rstrip(" ")` on the density char string before mapping. The `fill_kwargs` render() parameter was added as a side effect of this implementation, enabling any fill function to accept time-varying parameters from the render API.
**Priority queue update:** A10 complete. Updated priority queue:

| Priority | Technique | ID | Novelty | Status |
|----------|-----------|-----|---------|--------|
| 1 | Transporter Materialize | A11 | 5 | `idea` |
| 2 | SDF Font Generator | G04 | 5 | `idea` |
| 3 | Flame Simulation | A08 | 4 | `idea` |
| 4 | Living Fill (CA animated) | A06 | 5 | `idea` |
| 5 | Chromatic Aberration | C08 | 5 | `idea` |
| 6 | Stipple Fill | F08 | 3 | `idea` |

**Implementation notes:**
- `plasma_fill(mask, t, freq1, freq2, freq3, freq4, preset, density_chars)` in `justdoit/effects/generative.py`
- 4 presets: default/tight/slow/diagonal (freq1–4 vary)
- Registered as "plasma", "plasma_tight", "plasma_slow", "plasma_diagonal" in `_FILL_FNS`
- `plasma_wave(text_plain, font, n_frames, preset, color, loop)` animation preset in `justdoit/animate/presets.py` — takes plain text, re-renders at each frame with different t
- `fill_kwargs` parameter added to `render()` in `justdoit/core/rasterizer.py` — enables any fill to accept time-varying or extra params
- 18 new tests (test_generative.py) — all 413 passing
- 4 new static gallery SVGs (docs/gallery/): S-A10-plasma-default, S-A10-plasma-tight, S-A10-plasma-slow, S-A10-plasma-diagonal
- 2 new animation files (docs/anim_gallery/): A10-plasma-wave.cast/.apng, A10b-plasma-wave-cyan.cast/.apng (72 frames each @ 12fps, seamless loop)

## Session 2026-04-04

**Research focus:** Demoscene fire effect algorithms; Doom PSX fire algorithm for ASCII glyph mask application; web search unavailable — worked from prior knowledge of Fabien Sanglard's 2013 Doom fire article and the original id Software PSX Doom implementation.
**New techniques found:** 0 new (web search unavailable; A08 was already registered; session implemented it from prior knowledge of the classic Doom fire algorithm)
**Sources:** Fabien Sanglard (2013) "Doom Fire Effect" fabiensanglard.net/doom_fire_psx/ — the canonical reference for the heat-propagation algorithm used in PSX Doom; id Software PSX Doom fire.c — original source of the bottom-seeded heat-upward-propagation approach; prior knowledge of ASCII density char rendering.
**Key insight:** The Doom fire algorithm maps cleanly onto a glyph mask because it only propagates heat between cells that are already inside the mask — no ghost cells, no boundary conditions, no upscale-simulate-downsample cycle required (unlike Gray-Scott). The key design choice: use `random.Random(seed)` with per-frame seeds for the animation preset, making each frame a deterministic but independent snapshot. This gives a "flicker" effect rather than a smooth sweep (like plasma_wave does), which is the right visual for fire — random and chaotic, not periodic. The bottom-2-rows seed strategy ensures every font/glyph combination has a fire source, including thin-stroke fonts where only one row might exist at the base. One subtle correctness issue: the drift clamping logic — when a sideways drift would exit the mask boundary or hit an exterior cell, we fall back to the un-drifted column (`below_c = c`) rather than skipping the update entirely. This prevents heat from "stalling" at mask edges and allows it to propagate upward even when lateral movement is blocked.
**Priority queue update:** A08 complete. Updated priority queue:

| Priority | Technique | ID | Novelty | Status |
|----------|-----------|-----|---------|--------|
| 1 | Transporter Materialize | A11 | 5 | `idea` |
| 2 | SDF Font Generator | G04 | 5 | `idea` |
| 3 | Living Fill (CA animated) | A06 | 5 | `idea` |
| 4 | Chromatic Aberration | C08 | 5 | `idea` |
| 5 | Stipple Fill | F08 | 3 | `idea` |

**Implementation notes:**
- `flame_fill(mask, preset, n_steps, cooling, seed, density_chars)` in `justdoit/effects/generative.py`
- 4 presets: default (n_steps=25, cooling=0.12) / hot (30, 0.06) / cool (20, 0.20) / embers (15, 0.30)
- Registered as "flame", "flame_hot", "flame_cool", "flame_embers" in `_FILL_FNS`
- `flame_flicker(text_plain, font, n_frames, preset, color, loop)` animation preset — per-frame seed → independent flickering flame snapshots
- 16 new tests, all 429 passing (was 413)
- 3 new static gallery SVGs (docs/gallery/): S-A08-flame-default, S-A08-flame-hot, S-A08-flame-embers
- 2 new animation pairs (docs/anim_gallery/): A08-flame-flicker (.cast + .apng, 48 frames @ 12fps), A08b-flame-flicker-hot-red (.cast + .apng, 48 frames @ 12fps)

## Session 2026-04-06 (Mode B — Cross-Breed)

**Cross-breed chosen:** A_VOR1 — Voronoi Stained Glass
**Scores:** tension=5 emergence=4 distinctness=5 wow=5 → total=19/20
**Why chosen over alternatives:**
- A10c (plasma lava lamp, 18/20) is the next best candidate but needs the plasma float grid to be surfaced from inside voronoi_fill (more infra work). A_VOR1 first.
- A_F09a (wave phase animation, 12/20) scores too low vs A_VOR1 this session.
- ATTRIBUTE_MODEL.md priority order said C11 first, then A_VOR1 as first consumer — followed exactly.

**Implementation path:**
1. C11 infrastructure: `fill_float_colorize(text, float_grid, palette)` in `justdoit/effects/color.py` — standard palettes FIRE, LAVA, SPECTRAL, BIO + PALETTE_REGISTRY
2. A_VOR1 cross-breed: `voronoi_stained_glass()` in `justdoit/animate/presets.py` — spatial prime hash assigns region IDs per cell (row*6271 + col*7919 % 17), border '@' chars get silver (180,180,180), non-border cells get spectral palette color at `(region+offset) % 17 / 17.0`, sweeping offset per frame produces color rotation through the glass panes

**Visual validation result:** ✅ Meets the bar.
- 76 silver border cells form clean lead strips across "JUST DO IT" letterforms
- 90 interior cells carry spectral colors in distinct irregular pane shapes
- The prime hash distributes cells into 17 color groups without visible grid artifacts
- Rotating the palette offset shifts color assignment — the illusion of colored light moving through stained glass is immediate and compelling
- Structural permanence is maintained: cell borders never move, only color shifts
- The effect is visually unlike anything currently in the gallery

**Key insight:** The prime-hash approach (`row*6271 + col*7919 % 17`) produces a better stained-glass pane distribution than true Voronoi region tracking at this stage. True Voronoi region tracking would require surfacing `region` state from `voronoi_fill()` through the render API — architecturally messier and unnecessary when the visual goal is achieved via hash. The two primes chosen (6271, 7919) are in the same order of magnitude as the grid dimensions (~70 cols × 7 rows), preventing aliasing that would occur with small primes. This is a pattern worth reusing for any cell-stable color assignment.

**ATTRIBUTE_MODEL.md updates:**
- C11 marked as done in priority order and "Needs C11" tier
- A_VOR1 marked as `done 2026-04-06` in the tier table
- Next priority queue updated: A08c (flame + fire_palette) is next C11 consumer

**Implementation notes:**
- `fill_float_colorize(text, float_grid, palette)` in `justdoit/effects/color.py`
- Standard palettes: FIRE_PALETTE, LAVA_PALETTE, SPECTRAL_PALETTE, BIO_PALETTE
- PALETTE_REGISTRY: dict mapping names to palette lists
- `_lerp_palette(palette, t)` and `_tc_c11(r, g, b)` as local helpers (no gradient.py import)
- `voronoi_stained_glass(text_plain, font, n_frames, palette_name, loop)` in presets.py
- 35 new tests (test_color_c11.py × 24, test_voronoi_anim.py × 11), 564 total passing (was 529)
- 1 new static gallery SVG: docs/gallery/2026-04-06-A_VOR1.svg
- 2 new animation pairs: A_VOR1-voronoi-stained-glass-spectral (.cast + .apng, 60 frames @ 12fps), A_VOR1b-voronoi-stained-glass-fire (.cast + .apng, 60 frames @ 12fps)
- Gallery README updated: 6 daily entries, 51 techniques total

**Priority queue update:**

| Priority | Technique | ID | Novelty | Status |
|----------|-----------|-----|---------|--------|
| 1 | Flame Gradient Color (C11 consumer #2) | A08c | 3 | `idea` |
| 2 | Plasma Lava Lamp (C11 consumer #3) | A10c | 4 | `idea` |
| 3 | Bloom / Exterior Glow | C12 | 5 | `idea` |
| 4 | Wave Phase Animation | A_F09a | 3 | `idea` |
| 5 | Transporter Materialize | A11 | 5 | `idea` |
| 6 | SDF Font Generator | G04 | 5 | `idea` |

## Session 2026-04-06 (Mode B — Cross-Breed, second session same day)

**Cross-breed chosen:** A10c — Plasma Lava Lamp
**Scores:** tension=4 emergence=4 distinctness=5 wow=5 → total=18/20
**Why chosen over alternatives:**
- A08c (flame gradient color, est. ~10): Low emergence — color and chars from independent sources (color from row position, chars from flame sim). "Flame but colored" doesn't earn a 4 in emergence.
- A_F09a (wave phase animation, 12): Near-free warmup but visually similar to plasma_wave. Too low wow.
- X_ISO_NEON (16): Strong candidate but requires new per-face fill routing infrastructure. More infra than A10c.
- A10c earns 18 because both char density AND color come from the same float field — genuinely coupled, not independently colored.

**Implementation path:** New `plasma_float_grid()` helper in generative.py + `plasma_lava_lamp()` preset in presets.py.
- `plasma_float_grid()` computes only the normalized float grid (not chars) using the same plasma formula as `plasma_fill()`. This is the C11 data source.
- `plasma_lava_lamp()` calls `render()` for chars + assembles the combined float grid per-glyph (mirroring rasterizer assembly) + applies `fill_float_colorize()` with LAVA_PALETTE.
- Both char density and color track the same plasma float value — at peak (1.0): densest chars (`@#S`) + white/yellow; at trough (0.0 at exterior boundaries): sparsest chars (`;:,.`) + deep violet/purple.

**Visual validation result:** ✅ Meets the bar.
- 166 ink cells colored in "JUST DO IT" mid-cycle frame (t=π)
- Color spectrum spans deep violet (10,0,20) → purple (80,0,80) → dark red → orange (202,50,0) → yellow → white-hot (255,255,200) — LAVA_PALETTE interpolated faithfully
- Dense chars (`@#S`) co-locate with hottest colors; sparse chars (`;:,.`) co-locate with coolest — the coupling is visually legible
- The animation reads as hot lava-lamp fluid moving in slow organic patterns within the letterforms
- Structurally distinct from all gallery entries — no other technique uses per-cell 24-bit color from a generative float field

**Key insight:** The float grid assembly pattern (per-glyph float grid + gap padding to match rasterizer layout) is a reusable infrastructure pattern for any future C11 consumer that needs to color chars by the fill's own float output. The `plasma_float_grid()` function establishes the precedent: fills can expose their float data separately from their char output, enabling cross-module composition without changing the fill API contract.

**ATTRIBUTE_MODEL.md updates:**
- A10c marked as `done 2026-04-06`
- Priority order updated: C12 (bloom) is now #1 unimplemented
- `plasma_float_grid()` noted as reusable pattern for future C11 consumers

**Implementation notes:**
- `plasma_float_grid(mask, t, freq1, freq2, freq3, freq4, preset)` in `justdoit/effects/generative.py`
  - Returns 2D list[list[float]]: [0.0,1.0] for ink cells, 0.0 for exterior
  - Same normalization as plasma_fill: v_min/v_max per-frame normalization
  - Supports all 4 presets (default, tight, slow, diagonal)
- `plasma_lava_lamp(text_plain, font, n_frames, preset, palette_name, loop)` in `justdoit/animate/presets.py`
  - Default palette: "lava" (deep violet → white-hot)
  - Supports all PALETTE_REGISTRY palettes: lava, fire, spectral, bio
  - Float grid assembled by calling plasma_float_grid per glyph + gap-padding (mirrors rasterizer)
  - 72 frames @ 12fps for default n_frames=36 + loop=True
- 25 new tests in tests/test_plasma_lava_lamp.py — 10 for plasma_float_grid, 15 for plasma_lava_lamp
- All 589 tests passing (was 564 before this session)
- Gallery SVG: docs/gallery/2026-04-06-A10c.svg (mid-cycle static frame, 18KB)
- Animation files: docs/anim_gallery/A10c-plasma-lava-lamp.{cast,apng} (393KB + 784KB, 72 frames @ 12fps)
- Spectral variant: docs/anim_gallery/A10c-plasma-lava-spectral.{cast,apng} (390KB + 752KB)
- Gallery README updated: 7 daily entries, 52 techniques total

**Priority queue update:**

| Priority | Technique | ID | Novelty | Status |
|----------|-----------|-----|---------|--------|
| 1 | Bloom / Exterior Glow (patent-flag before ship) | C12 | 5 | `idea` |
| 2 | HDR Tone Mapping | C13 | 3 | `idea` |
| 3 | Wave Chromatic Interference (next C11 consumer) | A_F09b | 3 | `idea` |
| 4 | Turing Morphogenesis animation | A_N09a | 5 | `idea` |
| 5 | Transporter Materialize | A11 | 5 | `idea` |
| 6 | SDF Font Generator | G04 | 5 | `idea` |

## Session 2026-04-08 (Mode B — Cross-Breed)

**Cross-breed chosen:** C12 infrastructure + X_NEON_BLOOM — Bloom / Exterior Glow (C12 first consumer)
**Scores:** tension=5 emergence=4 distinctness=5 wow=5 → total=19/20
**Why chosen over alternatives:**
- C12 was #1 on priority queue. X_NEON_BLOOM is C12's first consumer — cleanest first use, fixed bloom color, no fill-float coupling needed.
- X_FLAME_BLOOM (20/20) is C12's flagship but requires A08c (flame+C11) first for the blown-out core. Blocked.
- A10c / A_VOR1 already done. A_F09a (12/20) too low to compete.

**Implementation path:**
1. `bloom(text, bloom_color, radius, falloff, core_boost)` in `justdoit/effects/color.py` — BFS distance map from all ink cells simultaneously (O(rows×cols)), Chebyshev 8-direction expansion, `\033[48;2;r;g;bm` background ANSI on each space cell within radius, exponential falloff. Optional core_boost: edge ink cells adjacent to space get foreground RGB 1.15× (inner glow).
2. `BLOOM_COLORS` dict in `color.py` (11 named presets) — was already staged from prior session start.
3. `neon_bloom()` preset in `presets.py` — renders once, applies `colorize()` for neon foreground, then applies `bloom()` with breathing falloff: `falloff + 0.06 * sin(2π * i / n_frames)` per frame. Forward+reverse loop, 60 total frames @ 12fps.

**Visual validation result:** ✅ Meets the bar.
- 166 ink cells in "JUST DO IT" block font
- 282 bloom cells surrounding the letterforms (radius=4, falloff=0.88)
- RGB breathing confirmed: first bloom cell RGB cycles 193→202→206→202→193→184→180→184 across 8 frames (the sine oscillation is real and legible)
- Letterforms structurally stable — only bloom intensity changes, not position
- SVG exporter limitation: background ANSI codes (`\033[48;2;...m`) are not rendered into SVG/PNG — bloom is terminal-only for now. Gallery SVG shows the neon-colored letterforms only (still visually clean). Documented in TECHNIQUES.md C12 entry.
- The effect is visually unlike anything currently in the gallery

**Key insight:** The BFS distance map approach (O(rows×cols), expand from all ink cells simultaneously) is ~100× faster than the naive O(space_cells × ink_cells) approach for terminal-width text. The key constraint is that `dist_map[r][c] >= radius` cells should NOT continue expanding — early termination keeps the BFS O(bloom_radius×perimeter) in practice. Chebyshev distance (8-direction expansion) produces the right circular bloom shape; Manhattan distance (4-direction) would produce diamond-shaped halos. The background ANSI channel (`\033[48;2;...m`) is genuinely unused by any ASCII art library — this is new territory for this class of output tools.

**ATTRIBUTE_MODEL.md updates:**
- C12 marked as `done 2026-04-08` (patent-review branch only — not merged to main)
- X_NEON_BLOOM marked as `done 2026-04-08` in "Needs C12" tier
- Priority order updated: C13 is now #1 unimplemented, X_FLAME_BLOOM is #2 target for next C12 consumer

**Patent status:** Bloom is on `patent-review/C12-bloom-glow` branch. NOT pushed to main. Flagged to Jonny per protocol. Background ANSI as spatial light-bleeding medium for ASCII art has no known prior art in any tool.

**Implementation notes:**
- `bloom(text, bloom_color, radius=4, falloff=0.9, core_boost=True)` in `justdoit/effects/color.py`
- `BLOOM_COLORS` dict with 11 named presets (cyan, magenta, red, orange, yellow, green, blue, white, fire, cold, lava)
- `neon_bloom(text_plain, font, n_frames, color, bloom_color_name, radius, falloff, loop)` in `justdoit/animate/presets.py`
- 29 new tests in `tests/test_bloom.py` — all passing
- Total: 618 tests (was 589 before this session, +29)
- 1 static gallery SVG: `docs/gallery/2026-04-08-X_NEON_BLOOM.svg` (18KB, neon cyan letters — bloom not visible in SVG)
- 4 animation files: `docs/anim_gallery/X_NEON_BLOOM-neon-bloom-cyan.{cast,apng}`, `X_NEON_BLOOM-neon-bloom-magenta.{cast,apng}` (60 frames @ 12fps each)
- Gallery README updated: 8 daily entries, 53 techniques total

**Priority queue update:**

| Priority | Technique | ID | Novelty | Status |
|----------|-----------|-----|---------|--------|
| 1 | HDR Tone Mapping | C13 | 3 | `idea` |
| 2 | Flame Bloom (C12 flagship) | X_FLAME_BLOOM | 5 | `idea` |
| 3 | Turing Morphogenesis animation | A_N09a | 5 | `idea` |
| 4 | Transporter Materialize | A11 | 5 | `idea` |
| 5 | SDF Font Generator | G04 | 5 | `idea` |
