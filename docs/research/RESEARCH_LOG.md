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
| 1 | L-System Growth | N06 | 5 | `idea` |
| 2 | Typographic Recursion | N01 | 5 | `idea` |
| 3 | SDF Font Generator | G04 | 5 | `idea` |
| 4 | Wave Interference Fill | F09 | 4 | `idea` |
| 5 | Voronoi Fill | F07 | 4 | `idea` |
| 6 | Plasma Wave Animation | A10 | 4 | `idea` |
| 7 | Flame Simulation | A08 | 4 | `idea` |
| 8 | Fractal Fill (Mandelbrot) | F05 | 4 | `idea` |
| 9 | Chromatic Aberration | C08 | 5 | `idea` |
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
