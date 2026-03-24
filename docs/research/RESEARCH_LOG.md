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
| 1 | Slime Mold Simulation | N10 | 5 | `idea` |
| 2 | Strange Attractor | N08 | 5 | `idea` |
| 3 | L-System Growth | N06 | 5 | `idea` |
| 4 | Typographic Recursion | N01 | 5 | `idea` |
| 5 | SDF Font Generator | G04 | 5 | `idea` |
| 6 | Wave Interference Fill | F09 | 4 | `idea` |
| 7 | Voronoi Fill | F07 | 4 | `idea` |
| 8 | Plasma Wave Animation | A10 | 4 | `idea` |
| 9 | Flame Simulation | A08 | 4 | `idea` |
| 10 | Fractal Fill (Mandelbrot) | F05 | 4 | `idea` |

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
