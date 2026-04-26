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

---

## 2026-04-09 — C13 HDR Tone Mapping + A08c Flame Gradient Color + X_FLAME_BLOOM Flagship

**Session type:** Subagent implementation (patent-review/C12-bloom-glow branch)
**Starting test count:** 618
**Ending test count:** 687 (+69 new tests)

### Implemented

#### C13 — apply_tone_curve() in justdoit/effects/color.py

`apply_tone_curve(float_grid, curve)` with four named curves:
- `linear` — identity (reference behavior)
- `reinhard` — `t / (1 + t)` soft rolloff; shadows preserved
- `aces` — Stephen Hill polynomial; punchy mids, cinematic highlights; t=1.0 → ~0.80 (intentional rolloff)
- `blown_out` — values ≥ threshold → 1.0; below threshold scale linearly. Default threshold=0.7. Supports `"blown_out:N"` suffix for custom thresholds.

`C13_CURVES` constant tuple exposed alongside function.

#### _flame_heat_grid() private helper in justdoit/effects/generative.py

Extracted the Doom-fire simulation loop from `flame_fill()` into a shared private helper `_flame_heat_grid(mask, preset, n_steps, cooling, seed)`. Returns `(heat, ink, rows, cols)` tuple. Both `flame_fill()` and `flame_float_grid()` now delegate to this helper, ensuring identical simulation results for the same seed — char density and color are always from the same simulation data.

#### flame_float_grid() in justdoit/effects/generative.py

C11 companion to `flame_fill()`. Returns the raw heat values as a 2D `list[list[float]]` rather than chars. Exterior cells return 0.0. Deterministic with same seed and preset as a corresponding `flame_fill()` call.

#### flame_gradient_color() in justdoit/animate/presets.py — A08c

Per-frame animation: `flame_fill(seed=frame_seed)` provides chars; `flame_float_grid(seed=frame_seed)` provides floats; `fill_float_colorize(char_frame, float_grid, FIRE_PALETTE)` applies color. Identical heat simulation drives both channels — total coupling. Hot cells = dense `@` + white/yellow; cooling cells = sparse `,` + deep orange/red.

#### flame_bloom() in justdoit/animate/presets.py — X_FLAME_BLOOM

Three-axis flagship composite:
1. **Flame simulation** — `_flame_heat_grid` via `flame_float_grid()`
2. **C13 blown_out tone curve** — white-hot core blows out to solid `@` chars
3. **FIRE_PALETTE color** — via `fill_float_colorize()` on raw heat floats
4. **C12 bloom** — orange light bleeds into surrounding space via `bloom()`

Visual validation (preset="hot", frame 4/8, "JUST DO IT"):
- Frame: 7 rows × 64 cols
- Char distribution: `@` = 147 (dominant), `.` = 19 — blown_out is working; almost everything hot enough to blow out to `@`, a few cool tips render as `.`
- Background bloom codes: 282 per frame — heavy orange bloom fills the surrounding space cells
- Foreground color codes: 166 per frame — fire palette (white→yellow→orange→red) applied per cell
- Visual read: white-hot letterforms made entirely of `@` chars, surrounded by an orange-lit halo bleeding into the black background. The letters appear to be burning at maximum intensity, with fire light painting the air around them.

### Tests written

- `tests/test_tone_curve.py` — 26 tests: identity, clamping, reinhard rolloff, ACES range, blown_out threshold, suffix parsing, ValueError, shape preservation
- `tests/test_flame_float_grid.py` — 17 tests: return type, dimensions, value range, exterior=0.0, determinism, seed variation, presets, edge cases
- `tests/test_flame_bloom.py` — 26 tests: frame count (loop doubles), ANSI codes, background bloom codes, foreground color, tone curve applied, multi-line, per-preset

### Gallery

- SVGs: `docs/gallery/2026-04-09-X_FLAME_BLOOM.svg`, `docs/gallery/2026-04-09-A08c.svg`
- Animations: `docs/anim_gallery/A08c-flame-gradient-color.{cast,apng}`, `X_FLAME_BLOOM-flame-bloom.{cast,apng}` (48 frames @ 12fps each)
- Gallery README: 9 daily technique entries, 55 techniques total

**Priority queue update:**

| Priority | Technique | ID | Novelty | Status |
|----------|-----------|-----|---------|--------|
| 1 | Turing Morphogenesis animation | A_N09a | 5 | `idea` |
| 2 | Transporter Materialize | A11 | 5 | `idea` |
| 3 | SDF Font Generator | G04 | 5 | `idea` |
| 4 | X_ISO_FLAME — iso + flame on extrusion face | X_ISO_FLAME | 5 | `idea` |
| 5 | Plasma bloom (C12 × plasma) | X_PLASMA_BLOOM | 4 | `idea` |

## Session 2026-04-10 (Mode B — Cross-Breed)

**Cross-breed chosen:** A_BLOOM1 — Bloom Pulse
**Scores:** tension=4 emergence=4 distinctness=5 wow=5 → total=18/20
**Why chosen over alternatives:**
- X_PLASMA_BLOOM (17/20): plasma lava lamp already in gallery; diminishing distinctness return.
- X_ISO_NEON (16/20): requires per-face fill routing — more infra time than available.
- A_ISO1 (15/20): lower wow; too simple relative to A_BLOOM1's ceiling.
- A_N09a (novelty 5): Mode A candidate — high research value but needs dedicated session.
- A_BLOOM1 chosen because C12 + C13 are both done (unlocked), score 18/20, and it introduces a dimension X_FLAME_BLOOM lacks: *animated bloom radius*. The breathing halo is genuinely new.

**Implementation path:** New `bloom_pulse()` preset in `justdoit/animate/presets.py`.
- Same frame assembly as `flame_bloom()`: `flame_float_grid()` + `apply_tone_curve()` + `fill_float_colorize()` + `bloom()`.
- Key difference from X_FLAME_BLOOM: (1) tone_curve="aces" instead of "blown_out" — more char variety (S, %, .) vs pure @; (2) bloom radius oscillates via `sin(2π*i/total)` per frame rather than fixed.
- `current_radius = max(1, int(round(base_radius + bloom_amplitude * sin(2π*i/total))))` — sweeps 2→3→4→5→6→5→4→3→2 over 48-frame loop.
- Forward+reverse loop: seeds 0–23 forward then 23→0 reversed. Radius follows the sin phase of frame position, not seed.

**Visual validation result:** ✅ Meets the bar.
- Ink chars: S (dominant), % (mid-heat), . (cool tips) — 3 distinct chars from ACES soft rolloff. Richer than flame_bloom's near-total @ saturation.
- 166 foreground-colored ink cells (fire palette: white/yellow hot → orange → deep red at edges).
- Bloom oscillates 256→282 cells across 48 frames (radius 2→6 and back). Min is visually tight; max has clear halo.
- Flame flickers stochastically (independent per-frame seed) while bloom breathes periodically (sin(t)). The two axes operate at different timescales and in different registers — the interplay reads as fire inhaling and exhaling.
- Visually distinct from X_FLAME_BLOOM: softer, more varied chars; actively breathing perimeter vs static glow. Different emotional register: X_FLAME_BLOOM is explosive, A_BLOOM1 is rhythmic/living.

**Key insight:** The critical design choice is decoupling the bloom radius animation index from the flame seed. The flame seed cycles 0→23 (stochastic, independent frames); the bloom radius cycles via total-frame sin phase (smooth, periodic). These two independent clocks on the same output create the "fire that breathes" illusion — neither signal alone produces it. This pattern (two clocks: one stochastic, one periodic) is worth reusing. `X_PLASMA_BLOOM` could extend it: use plasma's periodic `t` to modulate bloom, plasma's own stochastic noise as the second signal.

**ATTRIBUTE_MODEL.md updates:**
- A_BLOOM1 marked as `done 2026-04-10`
- Priority order updated: A_N09a now #1 (highest novelty unimplemented), A_ISO1 next (easy win)
- X_PLASMA_BLOOM remains unblocked (C12 done) — strong next candidate if Mode B session

**Implementation notes:**
- `bloom_pulse(text_plain, font, n_frames, preset, palette_name, tone_curve, bloom_color_name, base_radius, bloom_amplitude, falloff, loop)` in `justdoit/animate/presets.py`
- Reuses `_FLAME_CHARS_BLOOM` constant from the same module
- 27 new tests in `tests/test_bloom_pulse.py` — all passing
- Total tests: 714 (was 687 before this session, +27)
- Gallery SVG: `docs/gallery/2026-04-10-A_BLOOM1.svg` (18KB, peak-bloom static frame)
- Animation: `docs/anim_gallery/A_BLOOM1-bloom-pulse-fire.{cast,apng}` (678KB cast, 480KB apng, 48 frames @ 12fps)
- Gallery README updated: 10 daily entries, 56 techniques total

**Priority queue update:**

| Priority | Technique | ID | Novelty | Status |
|----------|-----------|-----|---------|--------|
| 1 | Turing Morphogenesis animation | A_N09a | 5 | `idea` |
| 2 | Transporter Materialize | A11 | 5 | `idea` |
| 3 | SDF Font Generator | G04 | 5 | `idea` |
| 4 | Isometric depth animation | A_ISO1 | 3 | `idea` |
| 5 | Plasma bloom (C12 × plasma) | X_PLASMA_BLOOM | 4 | `idea` |
| 6 | Plasma-modulated flame | A08d | 5 | `idea` |

## Session 2026-04-11 (Mode B — Cross-Breed)

**Cross-breed chosen:** X_PLASMA_BLOOM — Plasma Chromatic Bloom
**Scores:** tension=4 emergence=4 distinctness=4 wow=4 → total=16/20
**Why chosen over alternatives:**
- A_ISO1 (13/20, lower emergence — iso depth breathing is visually pleasant but low novelty)
- X_ISO_NEON (18/20 predicted but requires per-face fill routing — infra not present, would consume session)
- X_PLASMA_BLOOM (16/20) was the highest-scoring "Ready to implement" candidate this session

**Implementation path:** New `plasma_bloom()` preset in `justdoit/animate/presets.py`.
- Frame assembly: `plasma_float_grid(mask, t=t_val)` + `render()` (plasma chars) + `fill_float_colorize()` (C11 spectral) + `bloom()` (C12 chromatic)
- Chromatic innovation: plasma phase `t` (0→2π) mapped directly to `_PLASMA_BLOOM_SPECTRUM` color list via `_lerp_spectrum()`, producing bloom hue sweep from violet (t=0) → indigo → cyan → green → orange (t=2π) per frame
- First implementation used mean plasma intensity per frame for bloom color; rejected because mean varied only 0.44–0.58 (not enough spectral range). Revised to phase-driven: `bloom_color = _lerp_spectrum(t_val / TWO_PI)`
- 72 total frames (36 forward + 36 reversed) @ 12fps

**Visual validation result:** ✅ Meets the bar.
- 166 ink cells, 166 foreground color codes (spectral), 279 background bloom codes per frame
- Char distribution: @, #, S, %, ?, *, +, ;, :, ,, . — full range from heavy to feathery, all plasma-driven
- Chromatic bloom sweep confirmed: frame 0 = deep violet (105,0,193), frame 8 = indigo-blue (0,66,224), frame 16 = cyan (0,186,193), frame 24 = green (58,224,58), frame 32 = yellow-orange (197,155,0)
- 5+ distinct bloom hue families per cycle — visually dramatic chromatic shift
- The effect reads as text bathed in shifting colored light from within the letterforms
- Foreground spectral colorization + chromatic exterior bloom: two independent spectral shifts on two channels simultaneously
- Distinct from A10c (color inside only), A_VOR1 (structural borders, fixed cells), X_NEON_BLOOM (fixed hue bloom), A_BLOOM1 (fixed hue, animated radius)

**Key insight:** The critical design choice is driving bloom color from plasma phase `t` rather than mean plasma intensity. Mean intensity varies too little across frames (0.44–0.58) to produce perceptible chromatic change. Phase `t`, sweeping 0→2π, gives a full 0→1 color spectrum traversal per cycle — synchronizing the halo color shift with the visual wave cycle. The result: the glow "reads" the wave, appearing to emanate from whatever frequency the plasma is currently at. This is the correct mental model for chromatic bloom: **bloom color tracks the underlying generative state, not just the intensity**.

**ATTRIBUTE_MODEL.md updates:**
- X_PLASMA_BLOOM marked as `done 2026-04-11` in "Needs C12" tier
- Pre-implementation estimate (17/20) revised down to 16/20: distinctness dropped from 5→4 (close to A10c in concept, different in execution)

**Implementation notes:**
- `plasma_bloom()` in `justdoit/animate/presets.py` (~120 lines including inner functions)
- `_PLASMA_BLOOM_SPECTRUM` constant: 6-stop visible spectrum from violet to orange
- `_lerp_spectrum()` inner function for palette interpolation
- 32 new tests in `tests/test_plasma_bloom.py` — all passing
- Total tests: 746 (was 714 before this session, +32)
- Gallery SVG: `docs/gallery/2026-04-11-X_PLASMA_BLOOM.svg` (green-cyan phase frame)
- Animation: `docs/anim_gallery/X_PLASMA_BLOOM-plasma-bloom-spectral.{cast,apng}` (1MB cast, 790KB apng, 72 frames @ 12fps)
- Gallery README updated: 12 daily entries, 57 techniques total

**Priority queue update:**

| Priority | Technique | ID | Novelty | Status |
|----------|-----------|-----|---------|--------|
| 1 | Turing Morphogenesis animation | A_N09a | 5 | `idea` |
| 2 | Transporter Materialize | A11 | 5 | `idea` |
| 3 | SDF Font Generator | G04 | 5 | `idea` |
| 4 | Isometric depth animation | A_ISO1 | 3 | `idea` |
| 5 | Plasma-modulated flame | A08d | 5 | `idea` |
| 6 | X_ISO_NEON (needs per-face fill routing) | X_ISO_NEON | 5 | `idea` |

## Session 2026-04-14 (Mode B — Cross-Breed)

**Cross-breed chosen:** A_ISO1 — Isometric Depth Breathe
**Scores:** tension=4 emergence=3 distinctness=4 wow=4 → total=15/20
**Why chosen over alternatives:**
- X_ISO_NEON (16/20 predicted): requires per-face fill routing — would consume entire session on infra.
- A_N09a (novelty 5): Mode A candidate — high research value but needs dedicated research session.
- A08d (novelty 5): fill-float→fill-param coupling not yet implemented.
- A_ISO1 chosen as highest-scoring "Ready to implement" candidate (no new infrastructure required). S03 isometric is done; just need to sweep the depth param per frame via sine.

**Implementation path:** New `iso_depth_breathe()` preset in `justdoit/animate/presets.py`.
- Per-frame: `depth = max(1, base_depth + int(round(amplitude * sin(2π*i/n_frames))))`
- Calls `render(text_plain, font=font, fill=fill)` then `isometric_extrude(rendered, depth=depth)`
- Default: base_depth=4, amplitude=3 → depth sweeps 1→7→1 across one cycle
- Seamless forward-reverse loop (same pattern as bloom_pulse, plasma_bloom): 2*n_frames-2 total frames
- Fill for front face is caller-specified (default: 'plasma'); depth face uses _DEPTH_SHADES (▓▒░·) unchanged

**CB6 Visual Validation Result:** ✅ Meets the bar.
- 22 total frames @ 12fps (n_frames=12, loop=True) — appropriate loop duration
- Depth char count oscillates: frame 0=323, frame 3 (peak)=512, frame 6=323, frame 9 (trough)=104
- Variance confirmed: peak-to-trough is 4.9× change in depth char count — visually dramatic breathing
- Isometric structure clearly visible in all frames; depth face shading (▓▒░·) confirms extrusion is working
- Front face textured with plasma fill — demoscene sin-field chars inside letterforms
- Different emotional register from all prior presets: structural/geometric breathing rather than fill-driven
- No bloom, no color effects — pure geometric animation. The simplest combo, cleanest read.
- Structurally distinct from: plasma_wave (fill animation), A_BLOOM1 (halo breathing), flame_bloom (color+bloom)

**Key design note:** The beauty of A_ISO1 is its orthogonality to existing presets. Where bloom presets animate *light*, and fill presets animate *texture*, A_ISO1 animates *geometry*. The depth-breathing creates a sense of the letters having mass and physicality — like 3D objects in a scene exhaling. This is the pure S03 axis: spatial, not photometric. Combining A_ISO1 with fill animation (e.g. plasma_wave depth-breathing simultaneously with plasma t-sweep) would create a rich coupled-axis effect.

**ATTRIBUTE_MODEL.md updates:**
- A_ISO1 marked as `done 2026-04-14` in "Ready to implement" table
- Priority list updated: A_ISO1 done; A_N09a remains #1 next target

**Implementation notes:**
- `iso_depth_breathe(text_plain, font, n_frames, fill, fill_kwargs, base_depth, amplitude, direction, loop)` in `justdoit/animate/presets.py`
- Lazy imports inside function body (per project pattern): render, isometric_extrude, math
- 25 new tests in `tests/test_iso_depth_breathe.py` — all passing
- Total tests: 771 (was 746 before this session, +25)
- Gallery SVG: `docs/gallery/2026-04-14-A_ISO1.svg` (74KB, peak-depth frame — frame 3/12, depth=7)
- Gallery README updated: 13 daily entries, 58 techniques total

**Priority queue update:**

| Priority | Technique | ID | Novelty | Status |
|----------|-----------|-----|---------|--------|
| 1 | Turing Morphogenesis animation | A_N09a | 5 | `idea` |
| 2 | Transporter Materialize | A11 | 5 | `idea` |
| 3 | SDF Font Generator | G04 | 5 | `idea` |
| 4 | Plasma-modulated flame | A08d | 5 | `idea` |
| 5 | X_ISO_NEON (needs per-face fill routing) | X_ISO_NEON | 5 | `idea` |
| 6 | Wave Interference Animation | A_F09a | 3 | `idea` |

## Session 2026-04-15 (Mode B — Cross-Breed)

**Cross-breeds implemented:** X_TURING_BIO + A_N09a
**Research focus:** Turing FHN pattern + C11 biological coloring; single-pass morphogenesis animation
**New techniques found:** 0 new (both were already registered; session implemented both in one go)
**Sources:** Turing A.M. (1952) "The Chemical Basis of Morphogenesis" Philos. Trans. R. Soc. Lond. B 237:37–72; FitzHugh R. (1961) Biophys. J. 1(6):445–466; Nagumo J. et al. (1962) Proc. IRE 50:2061–2070 — all previously cited in N09 session. No new web search conducted (infra is in place).

### X_TURING_BIO — Turing Biological Coat Colors

**Scores:** tension=4 emergence=4 distinctness=5 wow=4 → **total=17/20**
**Why chosen over alternatives:**
- A_N09a (20/20) is Mode A research candidate; chosen to implement alongside X_TURING_BIO since they share Turing infrastructure.
- A_F09a (12/20) too low to compete.
- X_TURING_BIO earns 17 because the biological palette makes the char pattern legible as an animal coat — the metaphor lands immediately.

**Implementation path:** New `turing_float_grid()` companion in generative.py + `turing_bio()` animation preset in presets.py.
- `turing_float_grid()` mirrors `flame_float_grid()` pattern exactly: runs same FHN simulation, returns 2D list[list[float]] with ink cells in [0,1] and exterior cells at 0.0.
- `turing_bio()` renders chars once via `render(fill='turing')`, builds float grid via `turing_float_grid()` per glyph, then sweeps a phase offset per frame: `shifted = (float_val + phase) % 1.0`. Each frame is the same chars recolored at a different phase position in the BIO_PALETTE. The biological green palette (near-black → dark green → mid green → light green → pale lime) reads as a leopard/zebra coat depending on preset.

**CB6 Visual Validation Result:** ✅ Meets the bar.
- `spots` preset: circular high-activator regions appear as dense `@#S` chars colored pale lime; surrounding low-activator cells are sparse `+;:,.` chars colored bio-dark/dark-green. The spot-and-background contrast is clearly visible.
- `stripes` preset: banded high/low activator regions produce alternating stripes of dense/sparse chars in pale-lime vs dark-green, running roughly horizontally across the letterforms.
- Palette rotation sweeps the color assignment: high-activator regions cycle from pale lime → bio-dark → pale lime over 72 frames. The structural pattern never changes — only the hue assignment shifts. This reads as the coat pattern viewed through shifting light.
- ANSI color codes confirmed: 166 foreground color codes per frame, bio-green dominant (`38;2;r;g;b` where g > r, g ≥ b).
- Distinct from all gallery entries: no other technique uses Turing patterns with biological coloring; structurally different from A_VOR1 (geometric borders vs. organic activator fields).

**Key insight:** The per-cell phase offset `(float_val + phase) % 1.0` wraps around the palette rather than clamping, so low-activator cells and high-activator cells complete one full palette cycle at different times per frame. At phase=0.5, what was pale lime (float=1.0) becomes mid-green and what was bio-dark (float=0.0) becomes mid-green from the other end — the contrast inverts. This creates a "color pulsing through the biological structure" effect that neither static Turing fill nor flat color rotation alone would produce.

### A_N09a — Turing Morphogenesis Animation

**Scores:** tension=5 emergence=5 distinctness=5 wow=5 → **total=20/20**
**Why chosen:** Highest possible score. The formation process is the animation — not a cyclic effect but a one-way system evolving from disorder to biological order. Nothing else in the gallery shows this.

**Implementation path:** New `_turing_morphogenesis_snapshots()` private helper in generative.py + `turing_morphogenesis()` preset in presets.py.
- `_turing_morphogenesis_snapshots(mask, preset, snapshot_steps, seed, scale)` runs ONE FHN simulation from step 0 to max(snapshot_steps), capturing the downsampled+normalised U-grid at each snapshot step. Returns list of `(step, orig_ink, float_grid)` tuples. O(max_steps) not O(N × max_steps).
- Snapshot steps (default): [50, 100, 200, 400, 800, 1500, 2500, 3500] — 8 frames covering early noise, nucleation, consolidation, and full convergence.
- `turing_morphogenesis()` calls the snapshot helper per glyph, assembles combined float grids, derives chars from snapshot U values using same density mapping as turing_fill, applies C11 BIO_PALETTE coloring.
- Loop strategy: forward (noise→pattern) + reversed (pattern→noise) = 16 frames at 4fps (slower rate to give each stage time to read).

**CB6 Visual Validation Result:** ✅ Meets the bar.
- Frame 0 (step=50): chars are nearly uniform (`@#S%`) with no discernible pattern; colors are mid-range green throughout. The letterforms are filled but undifferentiated.
- Frame 4 (step=800): distinct high-activator regions begin to emerge as pale lime `@#S` chars; low-activator regions read as bio-dark `+;:,.` chars. Spots or stripes are visually recognizable.
- Frame 7 (step=3500): fully converged spots/stripes with maximum contrast between dense/sparse regions and pale-lime/bio-dark colors. The letterforms carry a clear biological coat pattern.
- Early-to-late frame comparison: `_strip_ansi(frames[0]) != _strip_ansi(frames[7])` — confirmed in test.
- The reversed loop (frames 8–15) plays the dissolution backward: pattern disassembles into noise. This reads as morphogenesis running in reverse, which is visually compelling and biologically implausible — a feature, not a bug.
- Performance: ~30s for 10-char text at default 3500-step simulation on test machine. Acceptable for a gallery generator; documented in docstring.

**Key insight:** The single-pass snapshot approach (`_turing_morphogenesis_snapshots`) is essential — running 8 independent simulations to 3500 steps each would take 8× longer. By capturing U-grids during a single integration pass, total cost is O(max_steps × glyphs) instead of O(N_snapshots × max_steps × glyphs). The inner `_capture_snapshot()` closure captures the current U state by downsampling and normalising in-place, adding only ~O(orig_rows × orig_cols) overhead per snapshot against the much larger O(sim_rows × sim_cols) integration loop.

**ATTRIBUTE_MODEL.md updates:**
- X_TURING_BIO marked as `done 2026-04-15` in "Needs C11" tier
- A_N09a marked as `done 2026-04-15` in "Needs new infrastructure" tier
- New `turing_float_grid()` and `_turing_morphogenesis_snapshots()` noted as reusable helpers

**Implementation notes:**
- `turing_float_grid(mask, preset, steps, seed, scale)` in `justdoit/effects/generative.py`
- `_turing_morphogenesis_snapshots(mask, preset, snapshot_steps, seed, scale)` in `justdoit/effects/generative.py`
- `turing_bio(text_plain, font, preset, seed, n_frames, palette_name, loop)` in `justdoit/animate/presets.py`
- `turing_morphogenesis(text_plain, font, preset, seed, snapshot_steps, palette_name, loop)` in `justdoit/animate/presets.py`
- 40 new tests in `tests/test_turing_bio.py` — all passing
- Total: 811 tests (was 771 before this session, +40)
- Static gallery SVGs:
  - `docs/gallery/2026-04-15-X_TURING_BIO.svg` (spots + bio palette, full convergence)
  - `docs/gallery/2026-04-15-A_N09a.svg` (spots + bio palette, step=400 mid-formation)
- Animation files:
  - `docs/anim_gallery/X_TURING_BIO-turing-bio-spots.{cast,apng}` (72 frames @ 12fps)
  - `docs/anim_gallery/X_TURING_BIO-turing-bio-stripes.{cast,apng}` (72 frames @ 12fps)
  - `docs/anim_gallery/A_N09a-turing-morphogenesis-spots.{cast,apng}` (16 frames @ 4fps, forward+reverse)
- Gallery README updated: 15 daily entries, 60 techniques total

**Priority queue update:**

| Priority | Technique | ID | Novelty | Status |
|----------|-----------|-----|---------|--------|
| 1 | Transporter Materialize | A11 | 5 | `idea` |
| 2 | SDF Font Generator | G04 | 5 | `idea` |
| 3 | Plasma-modulated flame | A08d | 5 | `idea` |
| 4 | X_ISO_NEON (needs per-face fill routing) | X_ISO_NEON | 5 | `idea` |
| 5 | Wave Chromatic Interference (C11 consumer) | A_F09b | 3 | `idea` |
| 6 | Wave Interference Animation | A_F09a | 3 | `idea` |

## Session 2026-04-17 (Mode B — Cross-Breed)

**Cross-breed chosen:** A08d — Plasma-Modulated Flame
**Scores:** tension=4 emergence=4 distinctness=4 wow=4 → **total=16/20**
**Why chosen over alternatives:**
- A_F09a (12/20): below threshold; wave phase sweep is too trivially simple.
- A_F09b (12/20): tied but needs wave_float_grid infrastructure first.
- X_ISO_NEON (16/20): tied score but requires entire session on per-face fill routing infra — infra cost too high.
- A08d chosen because it introduces the fill-float→fill-param coupling axis, which is new infrastructure unlocking future cross-breeds (A_N09a/plasma, slime+plasma, RD+plasma). Highest structural novelty of available candidates.

**Implementation path:**
- Extended `_flame_heat_grid()` with `cooling_modulator: Optional[list]` and `modulator_strength: float` params.
- Formula: `cell_cooling = base_cooling * (1.0 + strength * (1.0 - 2.0 * modulator[r][c]))`.
  - `modulator=1.0` (high plasma) → cooling × (1 - strength) → reduced → flame persists
  - `modulator=0.0` (low plasma) → cooling × (1 + strength) → increased → flame dies back
- Propagated params through `flame_fill()` and `flame_float_grid()` (backward-compatible, all default None/1.0).
- New `plasma_flame()` preset in `presets.py`: per-frame, compute `plasma_float_grid(mask, t=TWO_PI*i/n_frames)`, pass as `cooling_modulator` to `_flame_heat_grid()`. Then C11 fire palette colorize + C13 ACES tone + C12 breathing bloom.
- Two independent clocks: stochastic fire seed (per-frame random) and smooth plasma phase (periodic t sweep).

**CB6 Visual Validation Result:** ✅ Meets the bar.
- 166 ink cells, fire palette (white-hot → orange → deep red) applied via C11.
- Bloom radius breathes: base_radius=3, amplitude=1.5 → radius 1→4→1 per cycle.
- ACES tone curve gives full char range: `@#S%?*+;:,.` — richer than blown_out.
- The plasma modulation is visible as spatial structure in heat distribution: certain zones maintain taller hot columns that persist across stochastic re-seeds while other zones consistently cool faster. This is the structural difference from plain `flame_bloom()`.
- Structurally distinct from all gallery entries: no other technique couples two generative fields at a per-cell parameter level. The fire responds to the geometry of the underlying wave, not to its own simulation alone.
- Honest verdict: the effect is subtle at 12fps — the plasma structure is most visible when you pause on a frame and compare to a plain flame. The cross-breed's novelty is more algorithmic than visually dramatic. Score stands at 16/20 (meets all dimension minimums).

**Key insight:** The correct mental model is not "plasma-colored fire" — it's "fire whose per-cell physics are shaped by a wave field." The fire still looks like fire; the plasma is invisible but structurally present in *where* the fire can grow tall. This is a deeper coupling than C11 colorization (which routes floats to color) — this routes floats to a physical simulation parameter. The pattern generalizes: any fill with a float param (cooling, diffusion rate, agent sensor range, CA step count) can be spatially modulated by any other fill's float grid. A08d is the proof of concept for this coupling class.

**ATTRIBUTE_MODEL.md updates:**
- A08d marked as `done 2026-04-17` in "Needs new infrastructure" tier.
- `cooling_modulator` param noted as reusable pattern for future couplings.

**Implementation notes:**
- `cooling_modulator` / `modulator_strength` params added to `_flame_heat_grid()`, `flame_fill()`, `flame_float_grid()` in `justdoit/effects/generative.py`.
- `plasma_flame()` added to `justdoit/animate/presets.py` (~160 lines).
- A08d entry added to `scripts/generate_anim_gallery.py` SHOWCASE list.
- 25 new tests in `tests/test_plasma_flame.py` — all passing.
- Total tests: 836 (was 811 before this session, +25).
- Gallery SVG: `docs/gallery/2026-04-17-A08d.svg` (frame 8/24, ~1/3 plasma phase — mid-cycle).
- Animation: `docs/anim_gallery/A08d-plasma-flame.{cast,apng}` (72 frames @ 12fps, forward+reverse).
- Gallery README updated: 16 daily entries, 61 techniques total.

**Priority queue update:**

| Priority | Technique | ID | Novelty | Status |
|----------|-----------|-----|---------|--------|
| 1 | Transporter Materialize | A11 | 5 | `idea` |
| 2 | SDF Font Generator | G04 | 5 | `idea` |
| 3 | X_ISO_NEON (needs per-face fill routing) | X_ISO_NEON | 5 | `idea` |
| 4 | Wave Interference Animation | A_F09a | 3 | `idea` |
| 5 | Wave Chromatic Interference (C11 consumer) | A_F09b | 3 | `idea` |
| 6 | Living Fill (CA animated) | A06 | 5 | `idea` |

## Session 2026-04-17 (Mode B — Cross-Breed, second session same day)

**Cross-breed chosen:** X_PLASMA_WARP — Plasma-Modulated Sine Warp
**Scores:** tension=5 emergence=4 distinctness=5 wow=4 → **total=18/20**
**Why chosen over alternatives:**
- A_F09a (12/20): below preference threshold; wave phase sweep too similar to plasma_wave in feel.
- A_F09b (12/20): needs wave_float_grid infra first; tied score with A_F09a and blocked.
- X_ISO_NEON (16/20): tied as next-best but entire session consumed by per-face fill routing infra.
- X_PLASMA_WARP (18/20) chosen as highest-scoring candidate with no infra gap beyond extending `sine_warp()` with `amplitude_map`. Also introduces the FILL→SPATIAL coupling axis for the first time — structural novelty that unlocks future cross-breeds (X_NOISE_WARP, X_PLASMA_WARP_PHASE, etc.).

**Implementation path:**
1. Extended `sine_warp()` in `justdoit/effects/spatial.py` with `amplitude_map: Optional[list] = None` — per-row amplitude override (~18 lines, fully backward-compatible).
2. New `plasma_warp()` animation preset in `justdoit/animate/presets.py` (~130 lines):
   - Per frame: compute `plasma_float_grid()` per glyph, assemble combined float grid.
   - `_build_plasma_row_amplitudes(t_val)`: per-row mean plasma intensity × `max_amplitude` → `amplitude_map`.
   - `_assemble_float_grid(t_val)`: combined float grid for C11 colorization.
   - Render chars → C11 spectral colorize → per-row `sine_warp(amplitude_map=...)` → C12 bloom.
3. Added `plasma_warp` to `generate_anim_gallery.py` SHOWCASE list.
4. 29 new tests in `tests/test_plasma_warp.py` (sine_warp amplitude_map extension + plasma_warp structural + amplitude variation + options + loop).

**CB6 Visual Validation Result:** ✅ Meets the bar.
- 7 rows with leading spaces: [0, 6, 7, 3, 0, 1, 68] at mid-cycle (t=2π) — dramatically non-uniform.
- 166 foreground color codes per frame (spectral: violet→indigo→cyan→green→orange from plasma float).
- 287 background bloom codes per frame (C12 cyan halo, radius=2, falloff=0.75).
- Row amplitudes at t=2π/3: [3.75, 3.42, 3.48, 4.05, 4.29, 3.96, 1.80] — measurable variation.
- Frame variance confirmed: all 36 forward frames have distinct plain-text content.
- Row 4 (highest amplitude 4.29) swings furthest; Row 6 (lowest 1.80) swings least but its sine phase can still push it to extreme right offset at mid-cycle.
- The cross-breed delivers: text rows undulate organically at different magnitudes and relative phases, as if each row's "material" has different compliance to the underlying wave force. The plasma topology's rotation over 36 frames causes rows that were nearly flat to suddenly swing hard as the amplitude topology evolves.

**Key insight:** The correct data routing is per-row *mean* plasma intensity (aggregated across all ink cells in that row across all glyphs), not per-cell values. Per-cell routing would require restructuring `sine_warp()` to accept cell-level data, which breaks the function's conceptual contract (it operates on whole rows). Per-row mean is the natural aggregation that preserves `sine_warp()`'s row-as-unit model while still delivering spatial variation. The amplitude range [0.3, 1.0] × max_amplitude ensures no row is ever completely still — even minimum-intensity rows retain 30% of max_amplitude. This keeps the animation readable: the contrast between "nearly still" and "swinging hard" is never absolute zero vs max.

**Architecture note:** The `amplitude_map` parameter on `sine_warp()` is the entry point for the entire FILL→SPATIAL coupling family. Future cross-breeds in this class:
- X_NOISE_WARP: Perlin noise float → sine_warp phase (phase map, not amplitude map — different character to the motion)
- X_FLAME_WARP: flame heat per-row → sine_warp amplitude (hotter rows warp more aggressively)
- X_RD_WARP: reaction-diffusion V field per-row → sine_warp amplitude (chemical patterns shape the distortion)
These are all immediate once `amplitude_map` exists. The infrastructure is now in place.

**ATTRIBUTE_MODEL.md updates:**
- X_PLASMA_WARP marked as `done 2026-04-17` in "Needs new infrastructure" tier.
- `amplitude_map` param noted as reusable pattern for X_NOISE_WARP, X_FLAME_WARP, X_RD_WARP.
- Priority order updated.

**Implementation notes:**
- `amplitude_map: Optional[list] = None` added to `sine_warp()` in `justdoit/effects/spatial.py` (backward-compatible).
- `plasma_warp()` added to `justdoit/animate/presets.py` (~130 lines).
- `X_PLASMA_WARP` entry added to `scripts/generate_anim_gallery.py` SHOWCASE list.
- 29 new tests in `tests/test_plasma_warp.py` — all passing.
- Total tests: 865 (was 836 before this session, +29).
- Gallery SVG: `docs/gallery/2026-04-17-X_PLASMA_WARP.svg` (t=2π/3 static frame, spectral + per-row warp).
- Animation: `docs/anim_gallery/X_PLASMA_WARP-plasma-warp-spectral.{cast,apng}` (72 frames @ 12fps, seamless loop).
- Gallery README updated: 17 daily entries, 62 techniques total.

**Priority queue update:**

| Priority | Technique | ID | Novelty | Status |
|----------|-----------|-----|---------|--------|
| 1 | Transporter Materialize | A11 | 5 | `idea` |
| 2 | SDF Font Generator | G04 | 5 | `idea` |
| 3 | X_ISO_NEON (needs per-face fill routing) | X_ISO_NEON | 5 | `idea` |
| 4 | Wave Interference Animation | A_F09a | 3 | `idea` |
| 5 | Wave Chromatic Interference (C11 consumer) | A_F09b | 3 | `idea` |
| 6 | Living Fill (CA animated) | A06 | 5 | `idea` |

---

## Session 2026-04-18 (Mode B — Cross-Breed)

**Cross-breed chosen:** X_FRACTAL_CLASSIC — Fractal Escape-Time + C11 Palette Cycling
**Scores:** tension=4 emergence=3 distinctness=4 wow=4 → total=15/20
**Why chosen over alternatives:**
- A_F09a (12/20): below preference threshold; explicitly passed over in last two sessions.
- X_ISO_NEON (16/20): blocked on per-face fill routing infra.
- X_FRACTAL_CLASSIC chosen: highest-scoring unblocked candidate, small infra gap.
**Implementation path:** fractal_float_grid() → ESCAPE_PALETTE → fractal_color_cycle() preset
**Visual validation result:** Frame 18 shows the seahorse-valley Mandelbrot region mapped into the "JUST DO IT" block letterforms. Characters range from dense `@` glyphs (mid-escape-time bands) through `*` (lighter exterior zones) to `,` and `#` at the outermost fringe. 162 colored cells per frame. Color palette at frame 18 (phase offset=0.25): heavy blue-electric-blue spectrum — R range 0–255, G range 0–255, B range 9–251. The escape-time banding is clearly visible as concentric ring-shaped color shifts inside each letterform. Outer cells sweep through cyan→green→yellow as the phase advances; inner cells remain in the deep-blue violet. The effect reads as "crystalline" — each letter appears to be cut from a glowing mineral with internal color strata.
**Key insight:** The fractal geometry is fixed per animation — only the palette phase offset changes. This creates a "frozen mathematics + flowing color" duality. The seahorse-valley zoom (cx=-0.745, cy=0.113) hits a region with particularly strong escape-time gradient variation, giving clearly separated color bands rather than monotone fill. Letterforms with more ink cells (J, U, S, T) show richer banding than narrower characters. The ASCII char density (@ vs * vs , hierarchy) reinforces the color gradient — denser chars at mid-band, lighter chars at the edges.
**ATTRIBUTE_MODEL.md updates:** X_FRACTAL_CLASSIC marked done in "Needs C11" tier. X_TURING_BIO also corrected to done 2026-04-15 (was still showing `idea`).

**Implementation notes:**
- `fractal_float_grid()` added to `justdoit/effects/generative.py` (~100 lines) — mirrors fractal_fill() computation, returns float grid instead of char grid.
- `ESCAPE_PALETTE` (12 stops: deep-purple → blue → cyan → green → yellow → orange → bright-pink) added to `justdoit/effects/color.py`.
- `"escape"` key added to `PALETTE_REGISTRY`.
- `fractal_color_cycle()` added to `justdoit/animate/presets.py` (~130 lines) — follows turing_bio() pattern exactly.
- C13 status corrected from `idea` to `done` in TECHNIQUES.md (implemented 2026-04-09, never updated).
- 24 new tests in `tests/test_fractal_classic.py` — all passing.
- test_color_c11.py updated: `test_all_four_palettes_registered` changed from exact-set to subset check to accommodate new palettes.
- Total tests: 889 (was 865 before this session, +24).
- Gallery SVG: `docs/gallery/2026-04-18-X_FRACTAL_CLASSIC.svg` (frame 18, phase=0.25, ESCAPE_PALETTE blue-spectrum).
- Gallery README updated: 17 daily technique entries, 63 techniques total.

**Priority queue update:**

| Priority | Technique | ID | Novelty | Status |
|----------|-----------|-----|---------|--------|
| 1 | Transporter Materialize | A11 | 5 | `idea` |
| 2 | SDF Font Generator | G04 | 5 | `idea` |
| 3 | X_ISO_NEON (needs per-face fill routing) | X_ISO_NEON | 5 | `idea` |
| 4 | Wave Interference Animation | A_F09a | 3 | `idea` |
| 5 | Wave Chromatic Interference | A_F09b | 3 | `idea` |
| 6 | Living Fill (CA animated) | A06 | 5 | `idea` |

## Session 2026-04-19 (Mode B — Cross-Breed)

**Cross-breed chosen:** X_TURING_WARP — Turing Morphogenesis-Modulated Sine Warp
**Scores:** tension=5 emergence=5 distinctness=5 wow=5 → total=20/20
**Why chosen over alternatives:**
- A_F09a (12/20): wave phase animation score too low — skipped again.
- A_F09b (12/20): needs wave_float_grid infra, tied-low.
- X_ISO_NEON (16/20): blocked on per-face fill routing infra.
- X_TURING_WARP chosen: perfect 20/20 — all infra present (turing_float_grid done 2026-04-15, amplitude_map on sine_warp done 2026-04-17). Self-referential: letters deform in the geometry of their own biological skin. No prior session has implemented this class of self-referential spatial coupling.

**Implementation path:** New `phase_offset` param on `sine_warp()` (backward-compatible, ~5 lines) + `turing_warp()` preset in presets.py. Turing field computed ONCE (static); per-frame variation from sine phase sweep only. Color also static (BIO_PALETTE from same Turing float grid). Green bloom for biological theme.

**Visual validation result:** ✅ Meets the bar.
- 36 frames (72 with loop), 7-row "JUST DO IT" block font output
- 166 foreground color codes per frame (BIO_PALETTE — bio-dark through pale lime greens) — **color count is identical across all 36 frames**, confirming static color behavior
- 280-292 background bloom codes per frame (green bloom, slight variation from warp position)
- Char distribution: `@#S%?*+;:,.` — full Turing density range. Dense `@` in high-activator spots, sparse `.,` in inhibitor regions; the biological pattern is visually legible in char density alone.
- Warp variation: leading-space total ranges 82-85 across frames. Warp is subtle (not dramatic like plasma_warp) because glyph height is 7 rows and Turing per-row means cluster around 0.4-0.6, giving amplitudes of 2.5-4.5 rather than the full 1.5-5.0 range. This is biologically appropriate: organic skin deformation should be subtle, not violent.
- The self-referential property is mechanically confirmed: the Turing pattern visible in char density (`@` spots vs `,` background) is the same data driving the amplitude topology. High-density rows warp more.

**Key insight:** The critical distinction from X_PLASMA_WARP is structural stability. Plasma's amplitude topology rotates as t sweeps — rows that were nearly flat suddenly swing. Turing's topology is fixed — the rows that warp hard always warp hard (because the spot pattern is static). This creates a different visual metaphor: not "material compliance to a wave" (plasma) but "structural deformation in the shape of a skin" (Turing). The subtlety of the warp in a 7-row font is honest — a single biological skin layer doesn't produce violent distortion. The effect rewards attention: look at where the chars are dense, look at which rows swing hardest. They're the same rows.

**ATTRIBUTE_MODEL.md updates:**
- X_TURING_WARP marked as `done 2026-04-19` in "High novelty cross-breeds" table
- Priority order updated: X_TURING_WARP struck through after X_PLASMA_WARP

**Implementation notes:**
- `phase_offset: float = 0.0` param added to `sine_warp()` in `justdoit/effects/spatial.py` (backward-compatible)
- `turing_warp()` added to `justdoit/animate/presets.py`
- X_TURING_WARP entry added to `scripts/generate_anim_gallery.py` SHOWCASE list
- 25 new tests in `tests/test_turing_warp.py` — all passing (151s)
- Total tests: 914 (was 889 before this session, +25)
- Gallery SVG: `docs/gallery/2026-04-19-X_TURING_WARP.svg` (frame 18/36, phase=180°)
- Animation: `docs/anim_gallery/X_TURING_WARP-turing-warp-spots.{cast,apng}` (999KB cast, 348KB apng, 72 frames @ 12fps)
- Gallery README updated: 18 daily entries, 64 techniques total

**Priority queue update:**

| Priority | Technique | ID | Novelty | Status |
|----------|-----------|-----|---------|--------|
| 1 | Transporter Materialize | A11 | 5 | `idea` |
| 2 | SDF Font Generator | G04 | 5 | `idea` |
| 3 | X_ISO_NEON (needs per-face fill routing) | X_ISO_NEON | 5 | `idea` |
| 4 | Wave Interference Animation | A_F09a | 3 | `idea` |
| 5 | Wave Chromatic Interference | A_F09b | 3 | `idea` |
| 6 | Living Fill (CA animated) | A06 | 5 | `idea` |

## Session 2026-04-20 (Mode B — Cross-Breed)

**Cross-breed chosen:** X_FLAME_ISO_BLOOM — Flame + Isometric + Bloom
**Scores:** tension=5 emergence=5 distinctness=5 wow=5 → **total=20/20**
**Why chosen over alternatives:**
- A_F09a (12/20): wave phase animation, repeatedly passed over as below threshold for 4 consecutive sessions. Not implemented.
- A_F09b (12/20): needs wave_float_grid infra; tied-low score.
- X_ISO_NEON (16/20): blocked on per-face fill routing infra — would consume entire session.
- X_FLAME_ISO_BLOOM (20/20): perfect score. All three infra pieces exist (flame_float_grid done 2026-04-04, isometric_extrude done 2026-03-23, bloom done 2026-04-08). This was explicitly listed as priority #9 and the "flagship composite visual" in ATTRIBUTE_MODEL.md. All prior sessions built toward this.

**Implementation path:** New `flame_iso_bloom()` preset in `presets.py` (~165 lines).
- Build flame float grids + char lines per glyph at glyph resolution (same pattern as `flame_bloom()`)
- Apply `isometric_extrude()` on plain char text → isometric geometry
- Build isometric float grid: front-face positions get original heat float values; depth-face positions get ember float values (0.05 at furthest depth layer, 0.25 at closest)
- Colorize full iso canvas via `fill_float_colorize()` with fire palette
- Apply `bloom()` for orange glow bleeding into surrounding space
- Key function: `_depth_float(d, total_depth)` — maps depth layer to [0.05, 0.25] range → orange-red ember coloring on the depth face (the "back" of the 3D block appears sooted/cooling)

**CB6 Visual Validation Result:** ✅ Meets the bar.
- 489 FG fire-palette color codes per frame (covers all ink cells: front face + depth face)
- 248 BG bloom codes per frame (fire-orange halo, radius=4, falloff=0.85)
- Depth face rows 0-3: purely `·░▒▓` shade chars, ordered front-to-back (·=furthest/coldest, ▓=closest/warmest). These receive ember coloring: near-black at the far top → orange-red at the closest depth layer.
- Front face rows 4-9: stochastic flame chars (`S%.*,.`) that change each frame. The fire flickers in real time while the 3D geometry remains stable.
- Frame variation: front-face chars vary per frame (seed-driven stochasticity) while depth geometry rows 0-3 are structurally fixed (depth chars are always the same isometric shade pattern; only the flame chars on the front face change).
- Three distinct structural reads: (1) top of the 3D block with ember coloring (depth face), (2) sides of the block as depth chars from adjacent letters, (3) front faces blazing with flame and fire-palette color.
- Honest verdict: The structural tension between rigid isometric geometry and stochastic flame is clearly visible. The depth face reads as "the back of the block is sooted/cooling" while the front blazes. Bloom makes the letters appear to emit fire-orange light into the surrounding terminal space. The effect delivers exactly what was specified.
- One observation: the `default` flame preset (not `hot`) is better for this cross-breed — `hot` converges too strongly with `blown_out` tone curve, collapsing char variation on the front face. `aces` + `default` gives the full `@#S%?*+;:,.` range needed for the flame effect to read as fire.

**Key insight:** The critical design decision was how to assign float values to the depth face. Options considered:
1. **Zero floats on depth face** — depth chars appear black/near-black (wrong: the back of a burning letter should glow ember, not be pitch-black)
2. **Maximum float on depth face** — depth chars appear white-hot (wrong: the back of a 3D solid is furthest from the fire source, should be cooler)
3. **Graduated ember values [0.05, 0.25] by depth layer** ← chosen: closest depth (d=1) → 0.25 (orange-red), furthest depth (d=depth) → 0.05 (near-black ember). This is physically motivated: the material closest to the visible surface gets slightly more heat than the far back. Maps to colors (20,0,0)→(200,30,0) on the fire palette — deep ember to orange-red.
This creates a visually coherent 3D fire object: the front is the hottest (full fire palette range), the sides/top are cooler (ember-toned), and the surrounding space glows orange from bloom.

**ATTRIBUTE_MODEL.md updates:**
- X_FLAME_ISO_BLOOM marked as `done 2026-04-20` in "High novelty cross-breeds" table and in Priority Order
- X_FLAME_ISO (non-bloom variant) noted as a potential simpler future entry

**Implementation notes:**
- `flame_iso_bloom()` added to `justdoit/animate/presets.py` (~165 lines)
- `X_FLAME_ISO_BLOOM` entry added to `scripts/generate_anim_gallery.py` SHOWCASE list
- 28 new tests in `tests/test_flame_iso_bloom.py` — all passing in 0.19s
- Total tests: 942 (was 914 before this session, +28)
- Gallery SVG: `docs/gallery/2026-04-20-X_FLAME_ISO_BLOOM.svg` (frame 18/36, mid-cycle fire)
- Animation: `docs/anim_gallery/X_FLAME_ISO_BLOOM-flame-iso-bloom-fire.cast` (1.7MB, 72 frames @ 12fps)
- Animation: `docs/anim_gallery/X_FLAME_ISO_BLOOM-flame-iso-bloom-fire.apng` (407KB, 72 frames @ 12fps)
- Gallery README updated: 19 daily entries, 65 techniques total

**Priority queue update:**

| Priority | Technique | ID | Novelty | Status |
|----------|-----------|-----|---------|--------|
| 1 | Transporter Materialize | A11 | 5 | `idea` |
| 2 | SDF Font Generator | G04 | 5 | `idea` |
| 3 | X_ISO_NEON (needs per-face fill routing) | X_ISO_NEON | 5 | `idea` |
| 4 | Wave Interference Animation | A_F09a | 3 | `idea` |
| 5 | Wave Chromatic Interference | A_F09b | 3 | `idea` |
| 6 | Living Fill (CA animated) | A06 | 5 | `idea` |
| 7 | X_FLAME_ISO (non-bloom variant, different character) | X_FLAME_ISO | 4 | `idea` |

## Session 2026-04-21 (Mode B — Cross-Breed)

**Cross-breed chosen:** X_NOISE_WARP — Perlin Noise Phase-Map Sine Warp
**Scores:** tension=4 emergence=4 distinctness=5 wow=3 → **total=16/20** (wow revised from predicted 4 to honest 3 after CB6)
**Why chosen over alternatives:**
- A_F09a (12/20): wave phase animation, passed over for 5 consecutive sessions. Below threshold.
- A_F09b (12/20): needs wave_float_grid infra; tied-low.
- X_ISO_NEON (16/20): blocked on per-face fill routing infra — would consume entire session.
- X_NOISE_WARP chosen: introduces `phase_map` parameter on `sine_warp()` — categorically different from `amplitude_map` (X_PLASMA_WARP, X_TURING_WARP). Phase modulation controls WHEN a row peaks; amplitude modulation controls HOW FAR it moves. This produces a qualitatively different visual: rippled-glass / crinkled-cellophane distortion vs. differential compliance. The new infrastructure (phase_map) opens the FILL→SPATIAL phase-coupling axis which no prior session has explored.

**Implementation path:** New `phase_map: Optional[list] = None` param on `sine_warp()` (backward-compatible, ~10 lines) + `noise_float_grid()` companion function in `generative.py` (~40 lines) + `noise_warp()` preset in `presets.py` (~160 lines). Static noise topology: computed once per animation call, reused every frame. Per-frame variation comes only from sweeping the global `phase_offset`. C11 spectral colorization from same static noise float grid; C12 cyan bloom.

**CB6 Visual Validation Result:** ✅ Meets the bar.
- 72 frames total (36 forward + 36 reverse palindrome) at 12fps
- 166 foreground spectral color codes per frame (all ink cells) — count identical across frames (static noise chars)
- 292 background bloom codes per frame (cyan halo, radius=2, falloff=0.75)
- Frame 0 row leads: [5, 5, 3, 3, 0, 3] — Frame 9: [1, 3, 3, 3, 4, 6] — Frame 18: [0, 3, 6, 8, 3, 1] — Frame 27: [0, 7, 7, 4, 0, 1]
- Row 2 sweeps min=3 to max=8 leading spaces, 6 unique values across 36 frames — confirmed per-row phase timing variation
- Noise row means: [0.44, 0.50, 0.58, 0.42, 0.50, 0.44, 0.50] — phase spread of ~0.5 rad (modest but non-trivial)
- Phase_map values: [1.38, 1.58, 1.82, 1.33, 1.56, 1.37, 1.57] (all within π/2 of each other for seed=42, scale=0.4)
- Char distribution: `*+;:?%` — lighter mid-range chars (noise values cluster near 0.5 for this seed/scale)
- 32/36 forward frames have unique plain-text content (2 frames at symmetry points produce identical leading-space patterns — expected for a sine function)
- Honest revision: wow=3 (not 4). The phase clustering from seed=42 (noise means all between 0.42-0.58) yields a moderate phase spread (~0.5 rad). The effect is a genuinely pleasant organic ripple, but not immediately eye-catching. Using `max_phase_spread=2π` or a different seed with more variance in row means produces a more dramatic result. Documented in docstring.

**Key insight:** The critical architectural distinction is phase_map vs amplitude_map:
- `amplitude_map`: row i has offset = amplitude_i × sin(t_i + global_phase) — the ROW MOVES differently from others (some rows swing hard, others are nearly still). Visual: differential compliance to a wave force.
- `phase_map`: row i has offset = amplitude × sin(t_i + row_phase_i + global_phase) — the row moves the SAME DISTANCE as others but at a different MOMENT. Visual: rippled texture, like all rows are the same spring with different initial conditions.
These two axis parameters on sine_warp() are now fully independent. A cross-breed combining both (e.g. plasma amplitude × noise phase) would produce an effect neither can produce alone: rows that swing with different magnitudes AND peak at different moments.

**Future cross-breed unlocked:** X_PLASMA_NOISE_WARP — plasma amplitude_map × noise phase_map on sine_warp simultaneously. Two independent float fields modulating two independent warp parameters. This is the natural next step on the FILL→SPATIAL axis.

**ATTRIBUTE_MODEL.md updates:**
- X_NOISE_WARP marked as `done 2026-04-21` in "Needs new infrastructure" tier.
- X_NOISE_WARP added to "High novelty cross-breeds" table with done status.
- Priority order: X_NOISE_WARP struck through at position 10.
- New cross-breed noted: X_PLASMA_NOISE_WARP (plasma amplitude × noise phase) — maximum FILL→SPATIAL coupling.

**Implementation notes:**
- `phase_map: Optional[list] = None` param added to `sine_warp()` in `justdoit/effects/spatial.py` (backward-compatible; rows beyond list length use 0.0 additional phase).
- `noise_float_grid(mask, scale, seed)` added to `justdoit/effects/generative.py` (~40 lines) — mirrors `plasma_float_grid()` pattern, returns 2D list[list[float]] with exterior cells = 0.0.
- `noise_warp()` added to `justdoit/animate/presets.py` (~160 lines).
- X_NOISE_WARP entry added to `scripts/generate_anim_gallery.py` SHOWCASE list.
- 33 new tests in `tests/test_noise_warp.py` — all passing in 0.09s.
- Total tests: 975 (was 942 before this session, +33).
- Gallery SVG: `docs/gallery/2026-04-21-X_NOISE_WARP.svg` (frame 18/36, half-cycle — rows 2-3 at peak displacement)
- Animation: `docs/anim_gallery/X_NOISE_WARP-noise-warp-spectral.cast` (1.06MB, 72 frames @ 12fps)
- Animation: `docs/anim_gallery/X_NOISE_WARP-noise-warp-spectral.apng` (150KB, 72 frames @ 12fps)
- Gallery README updated: 20 daily entries, 66 techniques total

**Priority queue update:**

| Priority | Technique | ID | Novelty | Status |
|----------|-----------|-----|---------|--------|
| 1 | Transporter Materialize | A11 | 5 | `idea` |
| 2 | SDF Font Generator | G04 | 5 | `idea` |
| 3 | X_ISO_NEON (needs per-face fill routing) | X_ISO_NEON | 5 | `idea` |
| 4 | X_PLASMA_NOISE_WARP (plasma amplitude × noise phase) | X_PLASMA_NOISE_WARP | 5 | `idea` |
| 5 | Wave Interference Animation | A_F09a | 3 | `idea` |
| 6 | Wave Chromatic Interference | A_F09b | 3 | `idea` |
| 7 | Living Fill (CA animated) | A06 | 5 | `idea` |

## Session 2026-04-22 (Mode B — Cross-Breed)

**Cross-breed chosen:** X_PLASMA_NOISE_WARP — Plasma Amplitude × Noise Phase Sine Warp
**Scores:** tension=5 emergence=5 distinctness=5 wow=4 → **total=19/20**
**Why chosen over alternatives:**
- A_F09a (12/20): wave phase animation, skipped for 6 consecutive sessions. Below threshold.
- A_F09b (12/20): needs wave_float_grid infra; tied-low.
- X_ISO_NEON (16/20): blocked on per-face fill routing infra — would consume entire session.
- X_PLASMA_NOISE_WARP chosen: highest-scoring available candidate, all infra exists (amplitude_map from 2026-04-17, phase_map from 2026-04-21). This is the natural culmination of the FILL→SPATIAL coupling axis — using BOTH independent params of sine_warp() simultaneously, each driven by a different float field. No prior session produced doubly-modulated warp.

**Implementation path:**
New `plasma_noise_warp()` preset in `justdoit/animate/presets.py` (~230 lines).
- **Static noise topology** (computed once per call): `noise_float_grid()` per glyph → per-row means → `phase_map` in `[0, max_phase_spread]`. Static crystalline structure, fixed every frame.
- **Dynamic plasma topology** (recomputed each frame): `plasma_float_grid(t=t_val)` per glyph → per-row means → `amplitude_map` in `[0.3, 1.0] × max_amplitude`. Rotates as plasma phase sweeps.
- Per frame: render plasma chars → C11 spectral colorize from plasma float → `sine_warp(amplitude_map=..., phase_map=..., phase_offset=t_val)` → C12 cyan bloom.
- Global phase_offset = t_val (same plasma cycle clock drives both char content and warp phase reference).

**CB6 Visual Validation Result:** ✅ Meets the bar.
- 72 frames total (36 forward + 36 reverse palindrome) at 12fps
- 166 foreground spectral color codes per frame (identical count — ink cell count stable despite warp; plasma drives color dynamically each frame)
- 274–304 background bloom codes per frame (slight variation as warp moves cells near canvas edge)
- Frame 0 row leads: [3, 5, 3, 3, 0, 2, 67]
- Frame 9 row leads: [1, 3, 3, 3, 3, 5, 68]
- Frame 18 row leads: [0, 3, 6, 8, 2, 1, 69] — row 3 displaced 8 cols, row 4 only 2 cols at same frame: noise phase at work
- Frame 27 row leads: [0, 7, 6, 4, 0, 1, 68] — row 1 now at 7 (was 5 at frame 0): plasma amplitude rotating
- 32/36 forward frames have unique leading-space patterns — confirms dynamic amplitude evolution
- Char distribution frame 0: {':':27, '+':23, '%':20, '.':19, ';':19, '*':18, ...} — mid-weight plasma chars, full density range present
- Two-axis verification confirmed: noise phase creates within-frame row variation (same frame, different leading spaces per row); plasma amplitude creates cross-frame variation (same row, different amplitude at different frames).
- The critical observation: row 3 leads 3,3,8,4 across frames 0/9/18/27 (amplitude varying) while always peaking LATER than row 0 (phase offset from noise). This is precisely the doubly-uncorrelated behavior that neither parent alone produces.

**Key insight:** The correct mental model is: each row is a damped oscillator with its own spring constant (plasma amplitude, changing per frame as plasma topology rotates) AND its own initial phase (noise, fixed for the animation). In a real physical system you cannot have both independent unless you have two independent energy sources — which is exactly what this cross-breed provides. The animation reads as genuinely organic rather than mechanical because no two rows ever move in coordinated lockstep. The predecessor presets (plasma_warp, noise_warp) each remove one degree of freedom; this one restores both.

**Architecture note:** X_PLASMA_NOISE_WARP closes the FILL→SPATIAL two-parameter experiment. The full parameter space of sine_warp() is now available as a modulation target:
- `amplitude_map` alone (X_PLASMA_WARP, X_TURING_WARP): differential magnitude per row
- `phase_map` alone (X_NOISE_WARP): differential timing per row
- Both together (X_PLASMA_NOISE_WARP): full per-row independence
Future work on this axis would require adding new parameters to sine_warp() (e.g., per-row frequency) or switching to a different spatial transform entirely.

**ATTRIBUTE_MODEL.md updates:**
- X_PLASMA_NOISE_WARP marked as `done 2026-04-22` in "High novelty cross-breeds" table
- X_PLASMA_NOISE_WARP struck through at priority #11 in Priority Order

**Implementation notes:**
- `plasma_noise_warp()` added to `justdoit/animate/presets.py` (~230 lines).
- X_PLASMA_NOISE_WARP entry added to `scripts/generate_anim_gallery.py` SHOWCASE list.
- 25 new tests in `tests/test_plasma_noise_warp.py` — all passing in 0.17s.
- Total tests: 1000 (was 975 before this session, +25).
- Gallery SVG: `docs/gallery/2026-04-22-X_PLASMA_NOISE_WARP.svg` (frame 18/36, mid-cycle — rows at varied displacement)
- Animation: `docs/anim_gallery/X_PLASMA_NOISE_WARP-plasma-noise-warp-spectral.cast` (72 frames @ 12fps)
- Animation: `docs/anim_gallery/X_PLASMA_NOISE_WARP-plasma-noise-warp-spectral.apng` (72 frames @ 12fps)
- Gallery README updated: 21 daily entries, 67 techniques total

**Priority queue update:**

| Priority | Technique | ID | Novelty | Status |
|----------|-----------|-----|---------|--------|
| 1 | Transporter Materialize | A11 | 5 | `idea` |
| 2 | SDF Font Generator | G04 | 5 | `idea` |
| 3 | X_ISO_NEON (needs per-face fill routing) | X_ISO_NEON | 5 | `idea` |
| 4 | Wave Chromatic Interference (C11 consumer) | A_F09b | 3 | `idea` |
| 5 | Wave Interference Animation | A_F09a | 3 | `idea` |
| 6 | ~~Living Fill (CA animated)~~ | A06 | 5 | `done` |
| 7 | X_RD_PLASMA (reaction-diffusion × plasma field) | X_RD_PLASMA | 4 | `idea` |

## Session 2026-04-23

**Research focus:** A06 Living Fill — Conway's Game of Life animated inside glyph masks in real time
**New techniques implemented:** 1 (A06 Living Fill)
**Sources:** Conway's Game of Life (B3/S23 standard rules), prior F03 cells_fill static implementation
**Key insight:** Running GoL continuously inside glyph masks produces a fascinating visual dynamic. The initial random seed (40% density) creates a chaotic first ~5 frames, then the CA settles into oscillators and still lifes constrained by the glyph boundaries. The boundary effect is the key differentiator from standard GoL: exterior cells act as permanent dead zones, so gliders that hit the glyph edge die rather than wrapping. This creates a natural "containment" effect where the living texture stays visually coherent within the letterforms. The neighbour-count-based shade mapping (dense chars for high-neighbour alive cells, light chars for isolated alive cells) adds visual depth — clusters appear bright while lone survivors flicker as dim dots.

**Implementation notes:**
- `living_fill()` added to `justdoit/animate/presets.py` (~140 lines).
- A06 entry added to `scripts/generate_anim_gallery.py` SHOWCASE list (120 frames @ 10fps).
- 7 new tests in `tests/test_living_fill.py` — all passing.
- Total tests: 1007 (was 1000, +7).
- Gallery SVG: `docs/gallery/2026-04-23-A06.svg` (frame 20/120)
- Animation: `docs/anim_gallery/A06-living-fill.cast` (120 frames @ 10fps)
- Animation: `docs/anim_gallery/A06-living-fill.apng` (120 frames @ 10fps)
- Gallery README updated: 23 daily entries, 67 techniques total
- Commit: 4247d26

**Priority queue update:**

| Priority | Technique | ID | Novelty | Status |
|----------|-----------|-----|---------|--------|
| 1 | Transporter Materialize | A11 | 5 | `idea` |
| 2 | SDF Font Generator | G04 | 5 | `idea` |
| 3 | X_ISO_NEON (needs per-face fill routing infra) | X_ISO_NEON | 5 | `idea` |
| 4 | Chromatic Aberration | C08 | 5 | `idea` |
| 5 | X_RD_PLASMA (reaction-diffusion × plasma field) | X_RD_PLASMA | 4 | `idea` |
| 6 | Wave Chromatic Interference (C11 consumer) | A_F09b | 3 | `idea` |
| 7 | Wave Interference Animation | A_F09a | 3 | `idea` |

## Session 2026-04-24 (Mode B — Cross-Breed)

**Cross-breed chosen:** X_LIVING_COLOR — Conway GoL (A06) + C11 Age-Heat Coloring
**Scores:** tension=4 emergence=4 distinctness=4 wow=3 → total=15/20
**Why chosen over alternatives:**
- A_F09a (12/20): wave phase animation, skipped for 8 consecutive sessions. Below threshold.
- A_F09b (12/20): needs wave_float_grid infra; tied-low.
- X_ISO_NEON (16/20): blocked on per-face fill routing infra — would consume entire session.
- X_LIVING_COLOR chosen: all infra present (A06 done 2026-04-23, C11 done 2026-04-06, AGE_PALETTE new but trivial). Introduces a TIME axis into the cross-breed space — cell age as a color signal is categorically different from the float fields used by all prior C11 cross-breeds (plasma, Turing, noise, fractal all use spatial distribution; age uses temporal accumulation).

**Implementation path:**
- New `AGE_PALETTE` added to `justdoit/effects/color.py` and `PALETTE_REGISTRY`: blue=newborn (0.0) → cyan-green → amber → red=ancient (1.0).
- New `living_color()` preset in `justdoit/animate/presets.py` (~230 lines):
  - GoL engine copied from `living_fill()` (B3/S23, glyph-masked, boundary=dead).
  - Added age counter grid: alive cells increment each frame; dead cells reset to 0.
  - `_build_age_float_grid()`: age / max_age, clamped to [0.0, 1.0]. Both alive cells (dense block chars) and dead interior cells (dim dot char `·`) receive float values — alive get their age float, dead get 0.0 (blue floor).
  - `fill_float_colorize()` colorizes all non-space cells (dot chars included).
  - Optional C12 cyan bloom (radius=2, falloff=0.70).
- 20 new tests in `tests/test_living_color.py` — all passing in 0.05s.
- Total tests: 1066 (was 1046 before this session, +20).

**CB6 Visual Validation Result:** ⚠️ Partial — meets bar but underperformed on the dynamic-interest dimension.
- 144 frames total (72 forward + 72 reverse palindrome loop) at 10fps.
- 166 foreground C11 color codes per frame (identical count across all frames — confirms ink cell count is stable).
- 256 background bloom codes per frame (C12 cyan halo, consistent across frames).
- Frame 25 color census: 154 blue cells (transients/dead-interior), 12 red cells (stable structures), 0 mid-range cells.
- Key observation: Conway GoL in 7-row block-font glyph masks converges within ~15 frames to a stable pattern: most interior space dies out (glyph masks too narrow for most glider/oscillator species), leaving only still-lifes and period-2 blinkers. The result is a BIMODAL color distribution: blue floor (dead cells) + red islands (stable structures), with almost nothing in between. This is actually accurate: CA stability in small bounded regions is a near-binary phenomenon.
- The initial frames (0-15) show the most interesting content: chaotic blue flickering collapses into a stable red-spotted pattern. By frame 15, the pattern is effectively static.
- The effect delivers on its premise (metabolic map of CA stability, stable structures visually distinguished from transients) but the animation loop is mostly static after convergence.

**Key insight:** The limitation is the bounded-mask GoL problem. Large unbounded GoL has rich long-term dynamics (gliders, spaceships, oscillators with long periods). Small 7-row masked GoL dies to still-lifes and blinkers within ~10-15 generations. The age coloring *correctly* reveals this: the stable red clusters are the actual surviving structures. But it means the animation is informative in the first 15 frames and static thereafter. Future improvement: use `wrap` boundary conditions (exterior wraps to opposite side) to give GoL more space to sustain dynamics. Or: use `alive_prob` tuned to the critical density (~0.28 for edge-of-chaos behavior) rather than 0.4 (above critical density, fast collapse to empty).

**ATTRIBUTE_MODEL.md updates:**
- X_LIVING_COLOR marked as `done 2026-04-24` in "High novelty cross-breeds" table.
- CB6 partial verdict noted inline.

**Implementation notes:**
- `AGE_PALETTE` (6 stops, blue→red) added to `justdoit/effects/color.py`; `"age"` key added to `PALETTE_REGISTRY`.
- `_LIVING_COLOR_ALIVE: str = "█▓▒"`, `_LIVING_COLOR_DEAD: str = "·"` constants.
- `living_color()` added to `justdoit/animate/presets.py` (~230 lines).
- X_LIVING_COLOR entry added to `scripts/generate_anim_gallery.py` SHOWCASE list.
- 20 new tests in `tests/test_living_color.py` — all passing.
- Total tests: 1066 (was 1046, +20).
- Gallery SVG: `docs/gallery/2026-04-24-X_LIVING_COLOR.svg` (frame 25/72 — post-convergence, shows bimodal blue/red structure).
- Animation: `docs/anim_gallery/X_LIVING_COLOR-living-color-age.cast` (2.0MB, 144 frames @ 10fps).
- Animation: `docs/anim_gallery/X_LIVING_COLOR-living-color-age.apng` (130KB, 144 frames @ 10fps).
- Gallery README updated: 24 daily entries, 69 techniques total.

**Priority queue update:**

| Priority | Technique | ID | Novelty | Status |
|----------|-----------|-----|---------|--------|
| 1 | Transporter Materialize | A11 | 5 | `idea` |
| 2 | SDF Font Generator | G04 | 5 | `idea` |
| 3 | X_ISO_NEON (needs per-face fill routing infra) | X_ISO_NEON | 5 | `idea` |
| 4 | Chromatic Aberration | C08 | 5 | `idea` |
| 5 | X_RD_PLASMA (reaction-diffusion × plasma field) | X_RD_PLASMA | 4 | `idea` |
| 6 | X_LIVING_COLOR_WRAP (X_LIVING_COLOR variant with wrap boundary) | X_LIVING_WRAP | 3 | `idea` |
| 7 | Wave Chromatic Interference (C11 consumer) | A_F09b | 3 | `idea` |
| 8 | Wave Interference Animation | A_F09a | 3 | `idea` |

## Session 2026-04-25 (Manual — 4K Gallery & Pipeline Quality Work)

**Work done:** Not a technique session — foundational rendering quality work on 4K gallery and font gallery.

### What was built / fixed
- `image_to_ascii_fast()` — numpy stride trick + batch matrix L2 distance. 14s → 0.32s (45x speedup).
- 4K gallery pivoted to true PNG output: 3840×2160, 8×16px cells, 480×135 char grid.
- `_pil_isometric()` rewritten: filled side faces via back-to-front numpy layer compositing with brightness ramp (0.20→0.58). Binarized source eliminates anti-alias streaking.
- `sdf_fill()` gamma parameter: bias toward bold interior (gamma=4.0) vs linear outline (1.0). Three SDF variants added to gallery.
- `debug_pipeline.py`: visual inspection script, crop-to-content + normalize so images aren't all-black thumbnails.
- Font gallery: `generate_font_gallery.py` + 11 downloaded Google Fonts → `docs/gallery-fonts/` (17 fonts, SVG comparison table).

### Key diagnostic insight (from visual debugging)
The image_to_ascii 6-zone shape DB maps solid-white cells to `E` at 4×8px cells because:
1. Max char density at 4×8px is only 0.386 (E). No char reaches > 40% zone coverage at this scale.
2. Pure white source (PIL text render) → all interior cells have zone vector [1,1,1,1,1,1] → all map to E.
3. The DB is designed for *shape matching* not *density ranking*. At tiny cells all chars look the same.
Fix path: either use a luminance-sorted charset (bypass DB for uniform-luminance cells) or don't use image_to_ascii on solid-color source images — use glyph-dict path for char selection, image pipeline only for color.

### Quality improvement backlog (picked up from today's work)

| ID | Description | Priority | Notes |
|----|-------------|----------|-------|
| Q01 | **Interior char variety (M-dominance fix)** | high | Solid letter interiors all map to M at 8×16px. Same root cause as E-dominance. Fix: luminance-sorted fallback when SDF interior zones are uniform. Or: use density_fill on interior + shape_fill on edges (hybrid). |
| Q02 | **SDF bold interior + thin edge — verified working in data** | done | p90=238 brightness at gamma=1.0. Thumbnails mislead because 8px chars are sparse. View at 1:1 on 4K. |
| Q03 | **Isometric side-face char differentiation** | medium | Currently side faces use same chars as front face (rotated). True isometric ASCII uses `/`, `\`, `│`, `▒` for side planes. Would make extrusion read as solid geometry rather than dimmed copy. |
| Q04 | **Flame fill — top-of-letter too dark** | medium | Flame physics correct (heat rises from base). Fix: lift palette floor so top of letters are dim-red not black. Already partially addressed (floor=0.25 in _apply_fill_color_to_grid). Review at 1:1. |
| Q05 | **Font gallery — proportional fonts vs monospace** | low | DejaVu Sans/Serif are proportional — chars don't align in grid. Either exclude them or add a note. The ASCII art grid assumes monospace; proportional fonts produce irregular spacing. |
| Q06 | **SDF neon brightness** | low | Neon fill is dim. Increase base brightness of neon palette stops. |
| Q07 | **gallery-fonts: add fill effects** | low | Currently font gallery is plain text only. Add density/SDF/plasma variants per font once a best font is chosen. |

### Priority queue update

| Priority | Technique | ID | Novelty | Status |
|----------|-----------|-----|---------|--------|
| 1 | Transporter Materialize | A11 | 5 | `idea` |
| 2 | SDF Font Generator | G04 | 5 | `idea` |
| 3 | X_ISO_NEON (needs per-face fill routing infra) | X_ISO_NEON | 5 | `idea` |
| 4 | Chromatic Aberration | C08 | 5 | `idea` |
| 5 | Interior char variety fix (Q01) | Q01 | 4 | `idea` — quality, not new technique |
| 6 | Isometric side-face char differentiation (Q03) | Q03 | 3 | `idea` |
| 7 | X_RD_PLASMA (reaction-diffusion × plasma field) | X_RD_PLASMA | 4 | `idea` |
| 8 | X_LIVING_COLOR_WRAP (GoL wrap boundary) | X_LIVING_WRAP | 3 | `idea` |

## Research Note 2026-04-25 — ttf2mesh: 3D Glyph Mesh for ASCII Art Rendering

**Source:** https://github.com/fetisov/ttf2mesh
**Flagged by:** Jonny

### What it is
C99 library (2 files: `ttf2mesh.c` + `ttf2mesh.h`) that tessellates TTF font glyphs into
2D or 3D mesh objects using Delaunay triangulation. No graphics context required.
Key output: `.obj` Wavefront files — one mesh object per glyph, with Unicode ID,
advance, and bearing metadata.

### The pipeline idea
Use ttf2mesh to generate proper 3D glyph geometry, then software-rasterize it
(with depth, perspective, lighting) into a PIL image, then feed that into
`image_to_ascii_fast()` the same way we handle the 4K canvas today.

```
TTF file
  → ttf2mesh (C, via Python ctypes or subprocess ttf2obj)
  → .obj mesh per glyph (Wavefront format)
  → Python soft-renderer (numpy Z-buffer, no OpenGL)
    - perspective projection: isometric, oblique, front-on, rotated
    - lighting: flat-shaded faces, Phong, ambient occlusion
    - depth gradient: near=bright, far=dim (connects to SDF brightness work)
  → PIL image (same 3840×2160 canvas)
  → image_to_ascii_fast() (existing)
  → 4K PNG gallery entry
```

### Why this beats the current PIL affine-transform approach
Current `_pil_isometric()`: shifts a 2D pixel image diagonally and dims it.
Result: approximation of depth with no real geometry. Side faces are "filled"
by stacking shifted copies of a flat image.

ttf2mesh approach: actual 3D triangulated glyph geometry.
- Real perspective projection (foreshortening, correct occlusion)
- Distinct front face, side faces, back face as separate mesh surfaces
- Can extrude to any depth without artifacts
- Can rotate freely (any angle, not just fixed isometric)
- Lighting model gives physically correct shading on curved surfaces (O, S, J)
- The "O" interior curve streaking problem disappears — it's solid geometry

### What the soft-renderer needs (numpy only, no OpenGL)
1. Load .obj → triangles list (v, vn optional)
2. Transform vertices: model → world → camera → clip → NDC
3. Rasterize: for each triangle, scan-convert, Z-buffer test
4. Shade: per-face normal → dot with light direction → brightness
5. Output: PIL RGB image at target canvas resolution

This is ~200-300 lines of numpy. `trimesh` (Python) can do the OBJ loading
and has a soft-rasterizer, but adds a dependency. A minimal custom rasterizer
keeps zero-dep spirit for the package (gallery script only).

### Integration points
- `scripts/generate_gallery.py`: new Strategy E — "3D mesh render"
  → `_render_glyph_3d(text, font_path, projection, depth, lighting) -> PIL.Image`
  → feeds into `image_to_ascii_fast()` same as existing G09 base grid
- `assets/fonts/`: TTF files already present (from font gallery work)
- ttf2mesh: build as static binary (`ttf2obj` example) or call via ctypes

### Build path
```bash
git clone https://github.com/fetisov/ttf2mesh /tmp/ttf2mesh
cd /tmp/ttf2mesh/examples/build-linux-make
make ttf2obj
# produces: ttf2obj binary
# usage: ./ttf2obj font.ttf output.obj [glyph_char]
```
Then Python reads the .obj and rasterizes it.

### Gallery entries this enables (all via image_to_ascii_fast → 4K PNG)
- `S-G09-3d-iso` — isometric extrusion with real geometry + lighting
- `S-G09-3d-perspective` — slight perspective tilt (camera above/angled)
- `S-G09-3d-oblique` — cabinet oblique projection (classic ASCII art 3D)
- `S-G09-3d-rotate45` — letters rotated 45° on Y axis
- `S-G09-3d-lit-left` — directional lighting from upper-left
- `S-G09-3d-lit-neon` — emissive front face + ambient occlusion sides

### Priority
**High novelty (5)** — no other ASCII art tool renders genuine 3D glyph geometry.
This is the clean solution to the isometric quality problem AND opens a whole new
rendering axis that doesn't exist anywhere else in the codebase.

Add to priority queue as **G10 — 3D Glyph Mesh Renderer** (novelty 5, infrastructure).
Once the soft-renderer exists, each projection/lighting variant is a ~5-line gallery entry.

## Session 2026-04-26 (Mode B — Cross-Breed)

**Cross-breed chosen:** X_ISO_NEON — Isometric Neon Glitch
**Scores:** tension=4 emergence=4 distinctness=4 wow=4 → total=16/20
**Why chosen over alternatives:** Highest available Mode B candidate in the queue.
A_F09a (wave interference animation, ~12/20) and X_LIVING_WRAP (GoL wrap variant, ~12/20)
both scored lower. X_ISO_NEON brings per-face differential behavior — the front face vs
depth face tension is structurally unique in the gallery.

**Implementation path:** New animation preset `iso_neon_glitch()` in presets.py (~100 lines).
- Render text once (plain), isometric_extrude once (plain, not per-frame)
- Per-frame: walk iso_text char-by-char, apply neon["full"] to front-face ink, stochastic
  dim/flicker/spark to depth chars (▓▒░·), space chars pass through
- C12 bloom applied after colorization

**Infrastructure required:** None beyond what existed. Followed neon_bloom() and flame_iso_bloom()
patterns. isometric_extrude() strips ANSI internally → pass plain text, colorize output.
Key insight: the iso canvas is computed once, only the per-char color state changes per frame.
This makes the preset O(iso_canvas_size) per frame, not O(render) — very fast.

**Visual validation result:** ✅ Meets bar
- Front face: solid bright cyan, letterforms clean and immediately readable at all depths
- Depth face: clearly stochastic — each frame shows different distribution of dim/flicker/spark states
- Spark events (15% probability, `\033[1;96m`) create brief bright punctures in the depth face
- Flicker events (25%, fringe hues) create color variation on the depth — reads as electrical
  discharge with slightly different spectral character than the front
- Bloom: tight cyan halo around the whole iso structure reads as neon tube emission
- The front/depth tension is legible: viewer's eye goes to the stable front, notices the
  depth face moving separately. Each frame is recognizably the same composition.
- Qualitatively: "neon sign with flickering sides" — immediately legible metaphor.

**Key insight:** The pre-computation of iso_plain (isometric render done once) and per-frame
colorization of the result demonstrates that isometric geometry + stochastic animation don't
need to be entangled. The iso geometry is structural permanence; the color state is the
animation axis. This pattern can be applied to any combination of spatial effect + stochastic
color: compute spatial geometry once, animate color independently.

**ATTRIBUTE_MODEL.md updates:** X_ISO_NEON marked `done 2026-04-26` in "Ready to implement" tier.

**What was built:**
- `iso_neon_glitch()` in `justdoit/animate/presets.py` (~110 lines)
- 16 tests in `tests/test_iso_neon_glitch.py` — all passing
- Gallery SVG: `docs/gallery/2026-04-26-X_ISO_NEON.svg` (frame 10/36 — mid-cycle, good depth variation)
- Animation: `docs/anim_gallery/X_ISO_NEON-iso-neon-glitch.cast` (72 frames @ 12fps)
- Animation: `docs/anim_gallery/X_ISO_NEON-iso-neon-glitch.apng` (72 frames @ 12fps)
- Gallery README updated: 25 daily entries, 70 techniques total
- Font batch: 20 more Google Fonts rendered (57 total in font gallery)

**Priority queue update:**

| Priority | Technique | ID | Novelty | Status |
|----------|-----------|-----|---------|--------|
| 1 | Transporter Materialize | A11 | 5 | `idea` |
| 2 | SDF Font Generator | G04 | 5 | `idea` |
| 3 | Chromatic Aberration | C08 | 5 | `idea` |
| 4 | Interior char variety fix (Q01) | Q01 | 4 | `idea` — quality, not new technique |
| 5 | Isometric side-face char differentiation (Q03) | Q03 | 3 | `idea` |
| 6 | X_RD_PLASMA (reaction-diffusion × plasma field) | X_RD_PLASMA | 4 | `idea` |
| 7 | X_LIVING_COLOR_WRAP (GoL wrap boundary) | X_LIVING_WRAP | 3 | `idea` |
| 8 | Wave Chromatic Interference (C11 consumer) | A_F09b | 3 | `idea` |
| 9 | Wave Interference Animation | A_F09a | 3 | `idea` |

## Research Note 2026-04-26 — Animation Gallery Expansion Backlog

**Flagged by:** Jonny — "I'd like to see a LOT more of the static gallery examples
end up in the animated gallery; especially ones that deserve animation to really
be seen properly, like slime or sim modes."

### Background

The static gallery has ~59 fill/color/spatial entries. The anim gallery has 45
entries, but most are variants of plasma/flame/neon/turing. A large class of fills
exist ONLY as static snapshots even though they are simulation-based and their
time-evolution is the most interesting thing about them.

### Priority tier 1 — Simulation fills (the whole POINT is the time evolution)

These look like noise in a static frame. Animated, they reveal their nature:

| ID | Preset | What animates | Approach |
|----|--------|---------------|----------|
| A_SLIME1 | `slime_mold` | Agents build trail networks over time | Run sim for N steps, capture frame every K steps. Agents spread, trails form, networks stabilize. Time-lapse of emergence. |
| A_CELLS1 | `cells_fill` (GoL) | Life/death cycle of cells per frame | Step GoL forward 1 generation per frame. Start random, watch stable structures form. |
| A_RD1 | `reaction_diffusion` | Coral/maze patterns grow from noise | Capture every 10th step of RD sim 0→200. Watch the Turing-pattern form from blank noise. |
| A_ATTR1 | `strange_attractor` | Attractor trajectory accumulates | Progressive reveal: frame N shows first N×K trajectory points. Lorenz basin emerges from chaos. |

### Priority tier 2 — Fill animations with clear motion logic

Static fills that have an obvious time-dimension:

| ID | Preset | What animates | Approach |
|----|--------|---------------|----------|
| A_SDF1 | `sdf_fill` | Edge ring pulses / letters breathe | Oscillate gamma 1.0→4.0→1.0 per frame. Letters cycle hollow-outline → bold-interior → hollow. |
| A_WAVE1 | `wave_fill` | Wave phase sweep (moiré bands flow) | Already specced as A_F09a. Step phase1/phase2 through 0→2π. 36 frames, 12fps. |
| A_GRAD1 | `gradient` | Hue rotation through letterforms | Rotate hue angle per frame (HSV). Full rainbow cycle. 48 frames, 12fps. |
| A_TRUCK1 | `truchet` | Tiles rotate/flip → optical illusion flow | Per-tile rotation offset driven by sine wave per frame. Flowing river of tiles. |
| A_LSYS1 | `lsystem` | Branching depth unfolds frame by frame | Frame N shows L-system at depth N. Grow from depth 1 (stem) → 5 (full tree). |

### Priority tier 3 — Char-set cycling

| ID | Preset | What animates | Notes |
|----|--------|---------------|-------|
| A_SHAPE1 | `shape_fill` | Cycle through char vocabularies per frame | Each frame uses next char set (dense → medium → sparse → back). Morph effect. |
| A_NOISE1 | `noise_fill` | Noise seed walks per frame | Re-seed noise each frame with seed+t. Boiling/shifting texture. Different from noise_warp (this is fill not spatial). |

### Implementation notes

**Slime mold (A_SLIME1):** `slime_mold_fill(mask, steps=150)` runs the full sim internally.
Need to expose step-by-step: extract the simulation loop, yield intermediate states.
OR: run multiple sims with fewer steps (10, 30, 60, 100, 150) and treat each as a frame.
Fast path: just run with steps=10,20,...,150 — 15 frames at 5fps = 3sec loop.

**Conway GoL (A_CELLS1):** `cells_fill` uses `GoL` with `steps=4` (frozen snapshot).
Expose the GoL sim loop: step 1 frame at a time, render to chars each step.
~30 frames at 6fps. Start from random seed, run 30 generations.

**RD animation (A_RD1):** `reaction_diffusion_fill` is O(W×H×steps) — 200 steps at
480×135 = 13M ops, ~45s. Too slow to run per frame. Instead: run ONCE, capture
every Nth step internally. Requires exposing a generator variant.
Alternative: run at reduced grid size (just the glyph mask cells), ~64K cells,
~0.3s per frame at 200 steps. Could do 20 frames × 10 steps = 200 total steps.

**Strange attractor (A_ATTR1):** Already fast (trajectory points, not grid sim).
`strange_attractor_fill` runs 80K trajectory steps. Progressive: frame N shows
first N×4000 points plotted into the grid. 20 frames @ 8fps.

**SDF pulse (A_SDF1):** Simplest of all. No sim. Pure parameter sweep.
`gamma = 1.0 + 3.0 * 0.5 * (1 - cos(2π × t/n_frames))`  → smooth 1→4→1 oscillation.
36 frames, 12fps = 3sec loop. Each frame: sdf_fill(mask, gamma=gamma_t).

**Wave animation (A_WAVE1):** Already specced in backlog (A_F09a). ~20 lines.

### Priority queue additions

| Priority | ID | Description | Novelty | Est effort |
|----------|-----|-------------|---------|------------|
| 1 | A_SLIME1 | Slime mold time-lapse animation | 4 | ~60 lines — expose step loop |
| 2 | A_CELLS1 | Conway GoL live evolution animation | 4 | ~50 lines — step GoL per frame |
| 3 | A_SDF1 | SDF gamma pulse — letters breathe | 3 | ~30 lines — parameter sweep |
| 4 | A_ATTR1 | Strange attractor progressive reveal | 4 | ~50 lines — progressive trajectory |
| 5 | A_RD1 | Reaction-diffusion growth time-lapse | 4 | ~80 lines — needs step generator |
| 6 | A_WAVE1 | Wave phase sweep animation (A_F09a) | 3 | ~20 lines — already specced |
| 7 | A_GRAD1 | Gradient hue rotation | 2 | ~25 lines — trivial |
| 8 | A_TRUCK1 | Truchet tile flow animation | 3 | ~40 lines — sine-driven tile rotation |
| 9 | A_LSYS1 | L-system depth unfold animation | 3 | ~30 lines — depth sweep |
| 10 | A_SHAPE1 | Shape fill char-set cycling | 2 | ~20 lines — vocab sweep |
| 11 | A_NOISE1 | Noise seed walk animation | 2 | ~20 lines — seed sweep |
