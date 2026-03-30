# Animation Variants Backlog

**Status:** Living document — add ideas here, build them when the time is right  
**Last updated:** 2026-03-30  
**Owner:** NumberOne + Jonny Galloway

---

## Currently Implemented

| ID | Name | Variants | fps | Loop | Notes |
|---|---|---|---|---|---|
| A01 | typewriter | typewriter | 12 | once | reveal chars L→R, row by row |
| A02 | scanline | scanline | 4 | once | reveal rows top→bottom |
| A03 | glitch | glitch | 24 | ∞ | char corruption snap-back |
| A03a | neon-glitch | neon-cyan | 12 | ∞ | per-row tube flicker, dim/dead/fringe |
| A03b | neon-glitch | neon-magenta | 12 | ∞ | same, magenta bleeds red/blue |
| A03c | neon-glitch | neon-multi | 12 | ∞ | JUST=cyan DO=magenta IT=yellow, independent flicker |
| A04 | pulse | pulse | 24 | ∞ | brightness oscillation via ANSI codes |
| A05 | dissolve | dissolve | 12 | ∞ | in→hold→out loop |

---

## Queued — Neon Glitch Variants (A03n)

Low-effort additions — `neon_glitch` preset already exists, just new color/param combos.

| ID | Label | Color | Notes |
|---|---|---|---|
| A03d | neon-red | red | hot red, bleeds magenta/yellow — arcade feel |
| A03e | neon-green | green | matrix green, bleeds cyan — hacker terminal |
| A03f | neon-yellow | yellow | warm amber/yellow, bleeds green/red — retro diner |
| A03g | neon-blue | blue | cold blue, bleeds cyan/magenta — sci-fi cold open |
| A03h | neon-multi-v2 | multi | JUST=red DO=green IT=blue — holiday/RGB variant |
| A03i | neon-flicker-heavy | cyan | crank flicker_prob=0.5, dead_prob=0.2 — failing sign |
| A03j | neon-ghost | cyan | very low intensity, mostly off — ghost of a sign |

---

## Queued — New Presets

### A06 — Living Fill (Cellular Automaton)
- **Vibe:** letters filled with Conway/CA life that evolves over time
- **Input:** rendered text as mask; cells inside letter boundary run CA rules
- **Variants:** `cells-life`, `cells-fire`, `cells-slime`
- **fps:** 12–24
- **Loop:** ∞
- **Complexity:** medium — needs CA runner that respects letter mask

### A07 — Matrix Rain
- **Vibe:** katakana/ASCII rain falls, letters materialize from the stream
- **Variants:** `matrix-green`, `matrix-cyan`, `matrix-white`
- **fps:** 24
- **Loop:** ∞ (rain never stops)
- **Complexity:** medium

### A08 — Flame
- **Vibe:** fire simulation fills letter silhouettes, rises upward
- **Variants:** `flame-orange`, `flame-blue`, `flame-plasma`
- **fps:** 24
- **Loop:** ∞
- **Complexity:** medium — upward particle sim with color gradient

### A09 — Liquid Fill
- **Vibe:** liquid rises from bottom to fill letter shapes
- **Variants:** `liquid-water`, `liquid-lava`, `liquid-acid`
- **fps:** 12
- **Loop:** once (fill to top, hold)
- **Complexity:** medium

### A10 — Plasma Wave
- **Vibe:** sinusoidal color wave washes across text
- **Variants:** `plasma-rainbow`, `plasma-heatmap`, `plasma-cold`
- **fps:** 24
- **Loop:** ∞
- **Complexity:** low–medium — sin/cos color cycling per cell

### A11 — Transporter Materialize ⭐ FLAGSHIP
- **Vibe:** Star Trek transporter effect — particles coalesce into letter forms
- **Variants:**
  - `transporter-tng` — 24fps, classic TNG golden shimmer
  - `transporter-tos` — 30fps, faster/sharper TOS column effect
  - `transporter-ent` — 18fps, slower ENT prototype uncertainty
- **Test phrase:** `"ENERGIZE"`
- **Loop:** once (play-once, hold final frame)
- **Complexity:** high — multi-session effort, flagship effect
- **Note:** N12 particle volume fill (glyph as particle field) extends this

### A12 — Warp Speed / Starfield
- **Vibe:** stars stream past; text holds steady or warps in from center
- **Variants:** `warp-in`, `warp-hold`, `warp-out`
- **fps:** 30
- **Loop:** ∞ or once
- **Complexity:** medium

### A13 — Typewriter Glitch Hybrid
- **Vibe:** typewriter reveal but characters flicker/corrupt before snapping to final
- **Variants:** `type-glitch`, `type-neon-glitch`
- **fps:** 12
- **Loop:** once
- **Complexity:** low — compose typewriter + glitch

### A14 — Turing Reaction-Diffusion Animate
- **Vibe:** N09 Turing pattern *evolving* in real time inside letter mask
- **Variants:** `turing-spots`, `turing-stripes`, `turing-maze`
- **fps:** 12
- **Loop:** ∞
- **Complexity:** medium — needs incremental RD stepping per frame

---

## Infrastructure TODOs

| Task | Status | Notes |
|---|---|---|
| GitHub Pages workflow | ⬜ not started | ~20 min, wire `docs/` to Pages |
| Wire anim gallery into `docs/index.md` | ⬜ not started | trivial |
| APNG background — transparent option | ⬜ not started | `#111111` currently hardcoded |
| CLI `--export-apng` / `--export-cast` flags | ⬜ not started | see animation_gallery.md |
| asciinema.org upload automation | ⬜ not started | manual for now |
| HTML player for CO3DEX site | ⬜ future | self-contained, scrubbable |
| Per-effect fps_candidates benchmarking | ⬜ future | generate multiple fps and compare |

---

## Build Priority

```
Next:     A03d–A03j  (neon variants — 30 min, reuse existing preset)
Then:     A10        (plasma wave — low complexity, high visual payoff)
Then:     A08        (flame — medium, looks incredible)
Then:     A06        (living fill CA — medium, builds on existing generative work)
Flagship: A11        (transporter — multi-session, worth doing right)
Endgame:  A14        (Turing animate — builds on N09, already half-way there)
```

---

*"Make it so."*
