# Star Trek Effects — Design Document

**Status:** Design / Pre-implementation  
**Author:** NumberOne (AI) + Jonny Galloway (creative director)  
**Created:** 2026-03-29  
**Technique IDs:** A11, SO01, SO02 (see TECHNIQUES.md)

> Jonny Galloway was Game Lead & Director on Star Trek Elite Force 2.  
> He has production-level canon knowledge. When in doubt, ask him.  
> Action items marked **[JONNY]** require his input before implementation locks.

---

## Vision

A suite of Star Trek–inspired ASCII art animation effects that are immediately
recognizable to Trek fans — not just "sparkly text" but effects that feel
*canon-accurate* to specific series and eras.

The transporter is the first and flagship effect. Done right, it becomes a
reference implementation for all subsequent Trek effects: visual + audio
synchronized, series-selectable, terminally renderable in pure Python.

The bar: a Trek nerd watches it and says "that's TNG" or "that's TOS" — not
"that kind of looks like it."

---

## Series / Era Variants

Each series has a distinct visual and audio signature. The effect system must
be parameterized by era, not just generic "Star Trek."

### TOS (1966–1969) — The Original Series

**Visual:**
- Sharp, high-contrast column shimmer — almost strobing
- Particles are bright, small, high-frequency
- Monochromatic or blue-white
- Feels *electrical* — like matter being ionized
- The shimmer column is very visible as a distinct region before particles appear
- Fast materialize — not lingering, businesslike

**Audio:**
- The iconic rising "bweeeee" — a frequency sweep from ~200Hz to ~2kHz
- Sharp attack, moderate decay
- Less reverb than later series — drier, more raw
- Almost sounds like a theremin mixed with static
- Distinct from TNG — faster, more angular waveform

**Palette:** `white`, `bright_blue`, `cyan` ANSI colors

---

### TNG (1987–1994) — The Next Generation

**Visual:**
- Warmer golden/amber shimmer column — softer than TOS
- Particles are more numerous and smaller — feels like a denser cloud
- The column glows before particles appear — ambient luminance first
- Materialize feels *organic* — particles drift and coalesce, not snap
- Longer duration than TOS — more cinematic, less functional
- The letter shape is visible as a ghost/outline before it solidifies

**Audio:**
- The classic "shimmering" sound — layered harmonics, not a single sweep
- Warmer tone — more reverb, more room
- Almost musical — you could hum it
- Has a distinct "sparkle" quality layered on top of the base sweep
- Longer tail on dematerialize

**Palette:** `yellow`, `gold` (256-color amber), `white` shimmer

---

### DS9 (1993–1999) — Deep Space Nine

**Visual:**
- Cardassian transporter (different from Starfleet) — more orange/red
- Bajoran transporter — golden, similar to TNG but warmer
- Starfleet (runabout) — close to TNG but slightly faster
- The effect sometimes feels more violent — less gentle coalescing, more *arrival*

**Audio:**
- Varies by transporter type
- Cardassian: harsher, more industrial tone
- Bajoran/Starfleet: close to TNG with slight variations

**Palette:** `red`, `orange`, `amber` for Cardassian; TNG palette for Starfleet

> **[JONNY]** DS9 had multiple transporter types/cultures. What's the most  
> iconic DS9 transporter moment you'd want to nail?

---

### VOY (1995–2001) — Voyager

**Visual:**
- Very similar to TNG — same Starfleet tech
- Emergency Transport Unit has a slightly different signature
- Borg transporter is green-tinged

**Audio:**
- Near-identical to TNG baseline
- Borg beam: lower frequency, more ominous

**Palette:** TNG palette; Borg variant: `green`, `dark_green`

---

### ENT (2001–2005) — Enterprise (Prequel)

**Visual:**
- Prototype transporter — the effect should feel *uncertain*, less refined
- More scatter, less precision — particles don't converge as cleanly
- Longer duration — early tech, takes more time
- Characters visibly nervous using it — the effect communicates risk
- Blue-tinted

**Audio:**
- More noise, less musical — prototype feel
- Longer ramp, less confident sweep
- Should feel like it *might not work*

**Palette:** `blue`, `cyan`, slight static/noise chars mixed in

> **[JONNY]** The ENT transporter reluctance is a great character beat.  
> Did the EF2 team reference ENT-era tech design? Any production notes on  
> how they distinguished early vs. late-era Starfleet tech visually?

---

### Kelvin Timeline (2009–2016) — JJ Abrams films

**Visual:**
- Much faster — almost instant materialize vs. the slower TV series
- More *explosive* scatter → coalesce
- High contrast, almost white-out flash at completion
- Lens flare energy (we can simulate this with bloom chars)

**Audio:**
- More cinematic — orchestral design mixed with classic sweep
- Faster attack

**Palette:** `white`, `bright_white`, flash effect

---

### SNW / PIC / DSC (2017–present) — Modern era

**Visual:**
- Highest fidelity — particles are most numerous, finest
- Very fast materialize
- Some series show the transporter stream as a continuous ribbon, not scattered particles

> **[JONNY]** Less familiar with modern era production design.  
> Any canon notes you'd add here?

---

## A11 — Transporter Materialize Animation

### Core Algorithm

**Phase 1: Shimmer Column** (frames 0 → N×0.2)
- Render the full bounding box of the text as a faint shimmer field
- Random sparse sparkle characters scattered across the column
- Brightness ~10–20% — presence not content
- Characters: ` `, `·`, `.` cycling randomly

**Phase 2: Particle Scatter → Converge** (frames N×0.2 → N×0.6)
- Particles appear at random positions within bounding box
- Each particle has a target: a cell in the glyph mask
- Per frame: particle moves toward target by `velocity * convergence_factor(t)`
- Early: slow drift. Late: fast snap
- Particle brightness increases as it approaches target:
  `·` → `.` → `+` → `*` → `#` → glyph char

**Phase 3: Lock-In Cascade** (frames N×0.6 → N×0.85)
- Interior cells of glyph mask lock to solid first (mass/density = stable)
- Edge cells shimmer slightly longer — they're the boundary between matter states
- A few stray particles on exterior linger and fade

**Phase 4: Resolve + Trail** (frames N×0.85 → N)
- Letter is fully solid
- A few trailing sparkles outside the glyph fade to nothing
- Shimmer column dims to black

**Reverse (Dematerialize):** Run phases 4→1 in reverse.

### Half-Block Subpixel Resolution

Standard terminals: 1 character = 1 cell. Particles can only exist at integer positions.

With Unicode half-blocks, vertical resolution doubles:
- `▀` — top half lit
- `▄` — bottom half lit  
- `█` — full cell lit
- ` ` — empty

A particle at row 3.7 renders as `▄` in row 3 (bottom half). At row 3.3 it renders as `▀`. This makes particle drift look smooth instead of quantized.

**Implementation:** Double the internal grid height, map to half-blocks on output.

### Brightness Cascade Characters

Darkest → brightest progression for converging particles:

```
TOS:  ·  .  '  +  *  #  @  █
TNG:  ·  .  :  +  *  ░  ▒  ▓  █
ENT:  ,  .  ?  +  *  #  @  █   (with random noise chars mixed in)
```

> **[JONNY]** Does this cascade feel right visually? TNG's use of block  
> chars (`░▒▓`) for the intermediate states — does that read as more  
> organic/warm vs. TOS ASCII punctuation? Your eye will know.

### Particle Physics Parameters (per era)

| Parameter | TOS | TNG | ENT | Kelvin |
|-----------|-----|-----|-----|--------|
| Duration (frames) | 24 | 36 | 48 | 16 |
| Particle count | medium | high | low | very high |
| Convergence curve | linear | ease-in | erratic | snap |
| Column glow | sharp | soft | faint | flash |
| Trailing sparkles | few | many | scattered | minimal |
| Lock-in order | top-down | inside-out | random | simultaneous |

> **[JONNY]** These are educated guesses. What parameter feels most wrong?  
> Especially the lock-in order — TNG "inside-out" is my read but I'm not  
> certain. You've watched this in production context more carefully than anyone.

---

## SO01 / SO02 — Sound Engine + Transporter Audio

### Architecture

```
justdoit/sound/
  __init__.py
  synth.py      # procedural tone generation (numpy + sounddevice)
  player.py     # frame-synchronized playback
  presets.py    # named sound presets (transporter_tos, transporter_tng, etc.)
  assets/       # optional: bundled WAV files for non-synthesizable sounds
```

Optional import — silent fallback if `sounddevice`/`numpy` not installed:

```python
try:
    from justdoit.sound import player
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False
```

### TNG Transporter — Synthesized

The TNG transporter beam is approximately:

```
Base:     Sine sweep 300Hz → 1800Hz over 1.2s (materialize)
Shimmer:  Bandpass-filtered white noise, -20dB below base
Sparkle:  Random short sine bursts (50–100ms), 800Hz–3kHz, very low amplitude
Tail:     Reverb simulation — exponential decay of base frequency
```

> **[JONNY]** This is my best guess from listening to the effect dozens of  
> times. You shipped a Trek game — did your audio team have the actual  
> Paramount sound design notes or did you reconstruct from reference?  
> Any specific frequency or envelope details you remember?

### TOS Transporter — Synthesized

```
Base:     Sharper sweep, 150Hz → 2500Hz over 0.8s
Waveform: Slightly sawtooth (not pure sine) — that's the "electrical" quality
Noise:    Higher ratio of white noise to tone vs. TNG
Reverb:   Minimal — dry room
```

### ENT Transporter — Synthesized  

```
Base:     Slower, uncertain sweep — 200Hz → 1200Hz over 2.0s
Variation: Pitch wavers slightly — prototype instability
Noise:    Higher noise floor throughout
Resolution: Incomplete — add a brief descending tone at end (prototype hiccup)
```

### Frame Sync

The animation player calls `sound.player.update(frame, total_frames)` each frame. The player advances the audio envelope to match. If sound is unavailable, the animation runs silently at the same timing.

---

## Action Items

### NumberOne (me — implement these)

- [ ] Implement A11 materialize animation core (TNG first, as reference)
- [ ] Implement half-block subpixel renderer (`justdoit/output/halfblock.py`)
- [ ] Implement SO01 sound engine skeleton with silent fallback
- [ ] Implement SO02 TNG transporter beam synthesis
- [ ] Add `--animate transporter` CLI flag with `--trek-era` option
- [ ] Write tests (visual regression via SVG snapshot, audio via waveform shape)
- [ ] Implement TOS variant once TNG is validated
- [ ] Implement ENT variant (simplest, most forgiving)

### Jonny — I need your expertise on these

- [ ] **[JONNY-1]** Validate the brightness cascade character sequences — do they read right for each era? Especially TNG block chars vs TOS punctuation.
- [ ] **[JONNY-2]** Lock-in order per era — TNG inside-out vs top-down vs random. What does your memory say?
- [ ] **[JONNY-3]** DS9 — which transporter is most iconic? Cardassian, Bajoran, or runabout?
- [ ] **[JONNY-4]** Audio — did the EF2 audio team have Paramount reference material or reconstruct from scratch? Any frequency/envelope notes you recall?
- [ ] **[JONNY-5]** Frame reference — can you screenshot 4-6 frames from a TNG or TOS transporter sequence? One per phase: column glow, early scatter, mid-converge, lock-in, resolved. These become the visual spec.
- [ ] **[JONNY-6]** ENT transporter "reluctance" feel — is there a specific episode/scene that best captures the prototype anxiety? Best scene to use as reference.
- [ ] **[JONNY-7]** Modern era (SNW/PIC/DSC) — any production notes you'd add?
- [ ] **[JONNY-8]** The Kelvin timeline "flash" at materialize completion — does the white-out interpretation feel right or is there a more specific visual you'd describe?

---

## Related Techniques

Once A11 is solid, natural extensions:

- **A12 — Holodeck Initialization** — grid lines resolving into scene, text appearing from holographic framework
- **A13 — Borg Assimilation** — text corrupting and being rebuilt in green geometric patterns  
- **A14 — Warp Jump** — text stretching into streaks then snapping to normal (warp field effect)
- **A15 — Red Alert** — pulsing red color cycle + text corruption effect

> **[JONNY]** Any of these feel more iconic than A12–A15? What's the Trek  
> effect you most wanted to see done well and never have?

---

## Implementation Notes for Next Session

Start with TNG — it's the most recognizable and most forgiving (warmer, slower,
easier to get "close enough"). TOS is sharper and less forgiving of imprecision.

Implement visuals first, sound second. A great silent transporter is better
than a mediocre one with audio.

The half-block renderer is the key technical unlock — get that right and
everything else follows.

Test phrase: `"ENERGIZE"` — obviously.
