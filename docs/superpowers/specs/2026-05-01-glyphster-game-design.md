# GLYPHSTER — Game Design Document
*v0.2 · 2026-05-01 · JustDoIt repo*

---

## Elevator Pitch

You are **Glyphster** — a rogue process crawling through a dying distributed system.
The world is rendered in ASCII glyphs. So are you. The walls breathe. The rooms remember
what they used to be. Every ability you gain rewrites your own body.

A 2D side-scrolling metroidvania where the medium is the message: ASCII art is not the
aesthetic coating — it IS the world, the character, the physics, the storytelling.

---

## Three Design Pillars

**1. The World Is Alive**
Walls are not static. Glyph-growth algorithms (Turing patterns, slime mold, reaction-diffusion)
run on every surface. Rooms breathe. The deeper you go, the more corrupted the growth becomes.
The system is dying and you are moving through its decay.

**2. You Are What You Unlock**
Glyphster's body is the skill tree. Every ability adds new glyphs to your form — new leg
segments, orbital sigils, body core changes. A veteran player's Glyphster looks nothing like
a fresh one. Reading the character IS reading the loadout.

**3. Gravity Is a Perspective**
The game is side-on — until it isn't. Wall-rooms rotate gravity 90°. What was a decorated
wall becomes a floor of conduits and junction paths. The player's spatial understanding of
the world inverts. This is the core metroidvania "ability unlock" reimagined: you don't get
a double-jump, you get a new relationship with a surface.

---

## The World — THE MESH

A vast distributed system — cloud infrastructure, dark-web nodes, legacy mainframes, encrypted
vaults — rendered as traversable physical space. Glyphster moves through it as a hunter-program:
purpose unclear, instincts sharp.

The zones are not levels. They are system regions with distinct physical laws, aesthetics, and histories.

### Zone Registry (Demo Scope: Zones 1–3)

| # | Zone | System metaphor | Shader profile | Glyph-growth |
|---|---|---|---|---|
| 1 | **The Terminal** | Legacy mainframe, entry point | Amber CRT, heavy scanlines | Slow Conway's GoL — data age |
| 2 | **The Conduit** | Network backbone, data in motion | Subtle bloom + chromatic aberration | Physarum slime — live routing |
| 3 | **The Rot** | Corrupted sector, active decay | Heavy CA + screen tear + desaturation | Turing FHN spots — spreading corruption |
| 4 | **The Vault** | Encrypted cold storage | Overdriven bloom, deep dark | Reaction-diffusion stripes — crystalline |
| 5 | **The Core** | Root process, boss region | Full modern HD — jarring clean | Strange attractor — chaotic but structured |

Zone 5's "no post-process" is the most unsettling room in the game: everything else has been
filtered through decay and aesthetics. The Core looks raw and real. That's the horror.

### Room Types

**Standard room** — gravity points down, floor / platform / ceiling topology. Classic
metroidvania traversal.

**Wall-room** — gravity points laterally. What looked like a decorated wall becomes the
floor. Conduit pipes are paths. Junction boxes are platforms. The player's spatial model
inverts. This is not a gimmick — it is the second language of the game's movement.

**Zero-G node** — no gravity attractor. All surfaces are floors. Used sparingly for puzzle
and exploration beats, and for the sense of being truly inside a network — floating between
nodes.

**Terminal room** — fully CRT-shaded, phosphor-green or amber only. Puzzle-oriented.
Contains lore: system logs, error messages, fragments of what the Mesh used to be. These
rooms are quiet.

**Boss chamber** — large open space, unique shader profile, no glyph-growth (the boss IS
the growth, expanded to room scale).

---

## Player Character — GLYPHSTER

### Form

Glyphster is a spider-form entity. Not humanoid — no limbs in the biological sense.
A compact core of sigil-glyphs surrounded by eight articulated legs, each composed of
2–3 glyph sprites that render at pixel resolution with angle-based character switching.

**Starting footprint: ~7×5 glyphs at full extension. Core: 3×3 glyphs.**

```
Starting form         Mid-game              Full progression
  ╲  │  ╱             ◇╲  │  ╱◇            ╔═◇╲  │  ╱◇═╗
   ╲─┼─╱                ╲─┼─╱                  ◈╲─╬─╱◈
    (◆)                (◈◆◈)                  (◉◆◉)
   ╱─┼─╲                ╱─┼─╲                  ◈╱─╬─╲◈
  ╱  │  ╲             ◇╱  │  ╲◇            ╚═◇╱  │  ╲◇═╝
```

### Per-Pixel Animation

Glyphster does not snap to glyph cell boundaries. The sprites composing it are positioned
at floating-point pixel coordinates. Glyph *characters* switch at angle thresholds (~30°
intervals: `─ ╱ │ ╲`), but *positions* interpolate continuously.

Leg tips follow smooth arcs via inverse kinematics — tip anchors to contact point, upper
segments solve backward. The body core bobs on a sine curve (2–3px amplitude). At speed,
legs stretch; at rest, they tap and shift. Motion reads as fluid at a glance despite being
composed of discrete characters.

**Animation state set (starting):**

| State | What changes |
|---|---|
| Idle | Core glyph pulses (`◆→◈→◆`), legs tap alternately |
| Walk | 2-frame leg gait, body bobs ±2px |
| Run | Stretched leg arcs, body lowers 3px, glyph trail |
| Jump (ascend) | Legs tuck in, core compresses |
| Jump (apex) | Legs splay wide, momentary hold |
| Fall | Legs trail upward, core elongates |
| Land | Squash: body drops 4px, legs spread flat, snaps back |
| Wall-grip | Legs rotate 90°, body flattens to surface |
| Wall-crawl | Same gait as walk, rotated to gravity direction |
| Pounce | Compressed then explosive extension, glyph afterimage |
| Damaged | Random leg-glyph replaced with `·` or `╌`, core flickers |

### Progression — Visual Skill Tree

Every ability unlock rewrites Glyphster's body. The character sheet is the skill tree.

| Ability | Visual change | Gameplay |
|---|---|---|
| **Silk-thread** | Glyph-strand emitter appears at body front | Grappling hook — fire a stream of characters, swing |
| **Phase-shift** | Body core becomes hollow `○` briefly | Brief invincibility, pass through thin barriers |
| **Wall-route** | Leg tips gain grip-glyphs `⌐¬` | Wall-crawl without grip-drain in wall-rooms |
| **Overload** | Orbital glyph ring appears around core | Area burst — particles detonate outward |
| **Depth-scan** | Eyes appear in core (`◉`) | Reveals hidden paths — glyph-growth decodes into passages |
| **Carapace** | Outer shell glyphs wrap body `╔═╗╚═╝` | Absorb one hit, shell cracks, regenerates over time |

---

## Core Mechanics

### Movement

- Horizontal: physics-based with configurable friction per surface type
- Jump: variable height (hold = higher), legs tuck/extend as animation
- Wall-attach: press into any surface, legs grip, gravity perspective smoothly rotates
- Pounce: from wall-grip, launch in any direction — primary traversal in wall-rooms
- Grip-drain: wall-grip costs grip meter (shown as leg-glyph degradation `╲→╱→─→·`),
  empty = fall. Wall-route ability removes this cost in designated zones.

### Gravity Rotation

When Glyphster crosses a gravity-threshold trigger:
1. Gravity vector rotates toward new direction over 0.3s
2. Camera follows, rotating the world
3. Parallax layers rotate with gravity — depth still reads correctly
4. The room's tile data doesn't change — only the orientation of play

The player experiences the same room as both a standard room (entering from the floor)
and a wall-room (entering from the side passage) depending on which path they took.
The 47-blob tileset auto-resolves to the correct tile variants in both orientations.

### Combat System

#### Aim — 360° Glyph Cursor

Aim is fully 360° via mouse (PC) or right stick (controller). The aim direction is
communicated entirely by the **glyph cursor** — a single character orbiting Glyphster
at a fixed radius on an invisible circle.

Glyphster's body does **not** rotate to face the aim direction. The spider form is
radially symmetric; there is no meaningful "front." Instead:

- The cursor glyph orbits the body at ~3× the body radius
- A faint dotted aim-line traces from the body core to the cursor: `· · · ◎`
- When a charged shot is ready the line solidifies: `────◎` and cursor grows one glyph
- When the cursor overlaps an enemy, brackets appear: `[◎]`
- The cursor glyph is zone-specific:

| Zone | Cursor | Charged |
|---|---|---|
| The Terminal | `⌖` amber | `◉` amber |
| The Conduit | `◎` cyan | `⊕` cyan |
| The Rot | `×` desaturated | `✕` red-tint |
| The Vault | `◈` blue | `◉` white |
| The Core | `+` clean white | `✛` white |

The projectile visually emerges from the body core in the aimed direction — this
creates the directional read without requiring body orientation. Glyphster can walk
left and fire right simultaneously; the cursor is always the source of truth.

#### Glyph Charge — Resource System

Glyphster has a **Charge meter** with 4 pips. It is shown in the body core glyph,
not in a HUD bar:

```
0 pips   ○   empty, only Leg-strike available
1 pip    ◌   faint pulse
2 pips   ◎   steady glow
3 pips   ◉   bright
4 pips   ⊛   full, core overbrightens slightly
```

**Charge fills by:**
- Moving through active glyph-growth tiles (passive absorption, slow)
- Collecting glyph-fragments dropped by defeated enemies (instant, 1 pip each)
- Standing still near a glyph-growth tile (faster passive rate — risk/reward: standing still in combat)

**Charge depletes by:**
- Firing Glyph-pulse (1 pip per tap, 2 pips per charged shot)
- Silk-thread (2 pips)
- Overload (all remaining pips, minimum 2)

This creates the thematic loop: **engage with the living world to fuel your attacks**.
Avoiding glyph-growth keeps you safe but starves your combat resources.

#### Attack Arsenal

**Leg-strike** *(always available, no charge cost)*
Close-range melee. The two front legs extend in a 120° arc, dealing contact damage.
Reach: ~1.5× body width. No charge cost but 0.4s cooldown prevents spam.
Use case: close-quarters, finisher, or when charge is empty.
Animation: front legs shoot forward and snap back, glyph-scatter sparks on hit.

**Glyph-pulse** *(1 pip tap · 2 pips charged)*
Primary ranged attack. 360° aimed via cursor. Fires a projectile glyph in the
aimed direction; the character used is pulled from the zone's glyph vocabulary:

| Zone | Tap projectile | Charged projectile |
|---|---|---|
| Terminal | `█` amber | `▓▓▓` spread (3-shot) |
| Conduit | `◆` cyan | `◆◆◆` burst |
| Rot | `▒` desaturated | `▓` + corruption trail |
| Vault | `◉` blue | `●` heavy, slow |

Tap: single projectile, fast, travels full room width.
Charged (hold ≥0.5s): releases on button-up. Larger glyph, more damage, slight
screen-push on the cursor `[◉]` grows while charging.

**Silk-thread** *(unlockable · 2 pips)*
Fires a strand of connected glyph characters `─────◎` in aimed direction.
Range: ~80% of room width. Two uses:
- Hits enemy: stuns for 1.5s, moderate damage, tether glyphs visibly persist briefly
- Hits surface: grapple anchor, Glyphster is pulled toward impact point at speed

The strand is always visible from body to impact point until resolved — creates a
readable visual line of action in busy rooms.

**Overload** *(unlockable · all pips, min 2)*
Full charge dump. Glyphster's core flares, then detonates: ASCII particle burst in all
directions. Damage and radius scale with pips spent (2 pips = moderate, 4 pips = full room).
Clears glyph-growth in blast radius temporarily (growth resumes ~10s later).
Post-fire: brief 0.6s vulnerability window — core dims, legs splay flat. Committal.

#### Hit Feedback and Death

**Enemy hit:**
- Target's glyph characters scatter outward as particles (same chars that compose the enemy)
- Brief invert-flash on the hit glyph (single frame, white)
- Knockback proportional to damage

**Enemy death:**
- All constituent glyphs burst outward as ASCII particles, then fade over 0.8s
- The zone character vocabulary bleeds back in: a Daemon (Conduit zone) dies releasing `[>>]` and `╔╗` fragments
- Glyph-fragments (charge pickups) spawn at death point — 1–2 pips worth

**Player hit:**
- One leg-glyph degrades: `╲ → ╱ → ─ → ·` (visual health, no numeric display)
- Core glyph dims one step: `⊛ → ◉ → ◎ → ◌ → ○`
- Screen vignette pulses once (red-orange, 2 frames, then fades over 0.3s)
- Brief i-frame window (0.4s)

**Player death:**
- Body core implodes then explodes: all Glyphster's own glyphs scatter outward as particles
- Camera holds on the burst for 1s before fade-to-black
- Respawn at last anchor point (Terminal room in zone acts as checkpoint)

---

## Visual Architecture

### Layered Room Rendering

Every room renders 9 layers from back to front:

```
0  Far parallax      Network star-field, distant nodes           slowest scroll
1  Mid parallax      Circuit traces, pipe silhouettes            medium scroll
2  Room BG texture   Zone material (░▒▓) — semi-opaque base      static
3  Glyph-growth      Live generative simulation overlay          animated
4  Room structure    47-blob tileset — walls, floors, ceilings   static
5  Room overlay      Zone detail: graffiti, rust, glitch         static / sparse animation
6  Entities          Glyphster, enemies, items, projectiles      full physics
7  FG parallax       Close debris, rain, sparks                  fastest scroll
8  Post-process      Room shader profile applied to full scene   full-screen pass
```

### 47-Blob Tilesets

Each zone has one tileset. Each tileset has 47 variants per tile type, selected by
8-neighbor bitmask. Tile characters are chosen from the zone's glyph vocabulary:

- The Terminal: `█▓▒░ │─┼┤├┬┴` (solid block and line-drawing)
- The Conduit: `╔╗╚╝╠╣╦╩╬═║` (box-drawing, structural)
- The Rot: `▓▒░·:,.` (degrading density, corruption)

### Glyph-Growth Sub-Layer

Driven by JustDoIt's generative algorithms, running as a live simulation per zone.
Each room's growth simulation is seeded with room ID — same room always grows the same way.
Growth advances one step per N frames (configurable per zone: slow in The Terminal, fast in The Rot).

The growth layer renders at 50% alpha over the Room BG texture. At full corruption (late game),
alpha increases to 80% and the growth begins overwriting structural tiles — rooms visually decay
as the story progresses.

### Shader Profiles per Room

Each room carries a `ShaderProfile` — a named set of shader pass parameters. Entering a room
crossfades from the current profile to the room's profile over 0.5s.

```python
PROFILES = {
    "standard":   ShaderProfile(bloom=0.2, ca=0.003, scanlines=0.0, palette=None),
    "terminal":   ShaderProfile(bloom=0.4, ca=0.000, scanlines=0.8, palette="phosphor_green"),
    "amber":      ShaderProfile(bloom=0.5, ca=0.000, scanlines=0.9, palette="amber"),
    "corrupted":  ShaderProfile(bloom=0.1, ca=0.020, scanlines=0.2, palette="desaturate"),
    "vault":      ShaderProfile(bloom=0.9, ca=0.005, scanlines=0.0, palette=None),
    "clean":      ShaderProfile(bloom=0.0, ca=0.000, scanlines=0.0, palette=None),
}
```

---

## Enemies (Demo Scope)

| Name | Zone | Behaviour | Visual |
|---|---|---|---|
| **Daemon** | Conduit | Patrols path, damages on contact | 3×2 glyph walker, `[>>]` form |
| **Sentry** | Terminal | Stationary, periodic scan beam | 2×3 tower `╔▓╗` with sweep line |
| **Tracer** | Rot | Pursues once line-of-sight broken | Fast 5×3, `<◉>` core, erratic legs |
| **Node** | All | Environmental, spreads glyph-rot on contact | Pulsing 2×2 `▓█` blob |
| **BOSS: The Archivist** | Terminal (Zone 1) | Summons Daemons, fires amber beams, second phase wall-room gravity | Large 12×8, old terminal aesthetic |

---

## Audio

JustDoIt's sound synth (`justdoit.sound`) provides procedural audio — no audio files needed for the demo.

| Event | Sound character |
|---|---|
| Walk | Soft tick per step, pitch varies with surface material |
| Jump | Rising sine sweep, short |
| Land | Low thud + glyph-scatter burst |
| Wall-attach | Click + resonant hum |
| Glyph-pulse (attack) | Sawtooth burst, pitch = power level |
| Room transition | Chord shift, crossfades with shader profile |
| Glyph-growth tick | Near-silent background crackle in affected rooms |
| Boss presence | Low drone, zone-specific timbre |
| Damage | Discordant burst + leg-glyph scatter sound |

---

## Demo Scope

The technical demo ships with:

- **2 zones**: The Terminal (amber, tutorial) + The Conduit (standard cyberpunk)
- **1 gravity-rotation moment**: a wall-room in The Conduit, introduced after the player learns wall-attach
- **3 abilities**: Silk-thread, Phase-shift, Wall-route
- **1 boss**: The Archivist (Zone 1 exit)
- **All shader profiles** implemented, profiled in-game via room transitions
- **Live glyph-growth** on all room backgrounds
- **Full per-pixel animation** for Glyphster: idle, walk, run, jump, land, wall-grip, crawl, pounce, damaged

What is explicitly **not** in the demo: story dialogue, map screen, save system, zones 3–5,
enemies beyond the four listed, inventory/item system.

---

## Open Design Questions

~~1. **Glyph-pulse targeting**~~ — *Resolved: 360° free aim, glyph cursor, no body rotation.*

~~2. **Grip-drain meter UI**~~ — *Resolved: leg-glyph degradation is the meter. No HUD bar.*

~~3. **Zone 1 → Zone 2 transition room**~~ — *Resolved: environmental only, no tutorial. The passage forces the rotation; the player figures it out. Tutorial is a future iteration.*

~~4. **Glyph-growth and gameplay**~~ — *Resolved: purely aesthetic in the demo. Growth never blocks the player. Gameplay interaction (Overload clearing growth, growth damaging on contact) is a future iteration.*

~~5. **Enemy glyph vocabulary**~~ — *Resolved: distinct glyph set for enemies in the demo. Readability over zone consistency for now. Blended approach (zone chars for fill, unique core) is a future iteration.*

~~6. **Aim-line visibility**~~ — *Resolved: always-on at 30% true alpha, brightens to 100% when charging.*

   **Alpha rendering principle (applies game-wide):**
   Two transparency techniques coexist and serve different purposes:
   - **Glyph density** (`░▒▓█`) — an *aesthetic/content* choice. Used where the
     density graduation IS the thing: background textures, tile base layers,
     glyph-growth overlays. Looks like ASCII art because it is.
   - **True GPU alpha** — a *compositing/effect* choice. Used where smooth
     transparency serves readability or feel: aim line, particle trail fades,
     room transition overlays, UI elements, shader crossfades. Glyph density
     simulation would look messy here; true alpha is the right tool.

   Both can appear in the same frame. A glyph-growth tile using `░` characters
   sits on a layer rendered at 50% true alpha over the base texture — glyph
   density defines the *pattern*, true alpha defines the *layer weight*.

~~7. **Charge pip count**~~ — *Resolved: 4 pips. Tune fill/drop rates in playtesting.*

~~8. **Overload recovery window**~~ — *Resolved: 0.6s vulnerability window. Tune in playtesting, particularly against The Archivist.*

---

*GDD v0.1 — extrapolated from design conversation 2026-04-30/2026-05-01.*
*Next step: implementation plan for demo scope (Zones 1–2, The Archivist boss, core mechanics).*
