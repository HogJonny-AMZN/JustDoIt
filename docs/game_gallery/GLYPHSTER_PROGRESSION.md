# GLYPHSTER — Character Progression Design

Visual reference and design rationale for the three-stage character form progression.
Each upgrade physically rewrites the body — the skill tree **is** the character.

---

## Overview: The Three Forms

```
  STARTING               MID-GAME               FULL PROGRESSION
  ─────────              ────────               ────────────────

  ╲  │  ╱             ◇╲  │  ╱◇            ╔═◇╲  │  ╱◇═╗
   ╲─┼─╱                ╲─┼─╱                  ◈╲─╬─╱◈
    (◆)                (◈◆◈)                  (◉◆◉)
   ╱─┼─╲                ╱─┼─╲                  ◈╱─╬─╲◈
  ╱  │  ╲             ◇╱  │  ╲◇            ╚═◇╱  │  ╲◇═╝

  Rogue process          Orbital presence       Carapace complete
  awakens                established            Entity is whole
```

---

## Element-by-Element Progression

### 1 — The Core

The core is the identity glyph. It reads the current charge level and form stage simultaneously.

```
  STARTING               MID-GAME               FULL PROGRESSION
  ─────────              ────────               ────────────────

    (◆)                (◈◆◈)                   (◉◆◉)
```

| Glyph | Form | Meaning |
|-------|------|---------|
| `◆` | All stages | Primary core — the process itself. Always present. |
| `◈` | Mid-game + | Junction orbs: two unlocked abilities flanking the core. Each `◈` marks an active power node. |
| `◉` | Full only | Evolved consciousness. Core has expanded. The entity is fully self-aware. |
| `( )` | All stages | Body bracket — holds the core. Parentheses = containment. |

**Design intent:** The core tells you what stage you're at in a single glance. No HUD, no level number — just look at the body.

---

### 2 — Inner Arm / Junction

The inner arm connects the core to the outer legs. It changes structure as the form evolves.

```
  STARTING               MID-GAME               FULL PROGRESSION
  ─────────              ────────               ────────────────

   ╲─┼─╱                ╲─┼─╱                  ◈╲─╬─╱◈
   ╱─┼─╲                ╱─┼─╲                  ◈╱─╬─╲◈
```

| Element | Appears | Meaning |
|---------|---------|---------|
| `┼` | Starting, Mid | Basic crosshair junction — simple pivot point |
| `╬` | Full only | Reinforced double junction — thicker, structural, load-bearing |
| `◈` (on inner arm) | Full only | Fixed junction markers at the arm attachment point. Not the same `◈` as the core flankers — these are structural anchors. |
| `─` | All stages | Connector segments — bone of the arm |

**Design intent:** The `┼` → `╬` upgrade is subtle but load-bearing. The junction gets thicker as the form adds weight (carapace, orbs). The `◈` anchors on the inner arm in the full form are the visual pivot that the carapace frame attaches to.

---

### 3 — Outer Legs

The outer rows are the most expressive part of the form. They move through the walk cycle and telegraph the animation state.

```
  STARTING               MID-GAME               FULL PROGRESSION
  ─────────              ────────               ────────────────

  ╲  │  ╱             ◇╲  │  ╱◇            ╔═◇╲  │  ╱◇═╗
  ╱  │  ╲             ◇╱  │  ╲◇            ╚═◇╱  │  ╲◇═╝
```

| Element | Appears | Meaning |
|---------|---------|---------|
| `╲ │ ╱` | All stages | Outer leg segments — directional vectors that rotate through the walk cycle |
| `◇` | Mid + Full | Sigil tips riding the outermost leg ends. Mark unlocked ability slots. |
| `╔═ ═╗` / `╚═ ═╝` | Full only | Carapace shell — protective frame, locks around the form |

**Walk cycle animation:** The outer leg chars cycle through `╲ → / → | → \ → ╱` as stride progresses. The inner arm follows with a quarter-phase offset. The body reads as mechanical/organic — joints are visible.

---

### 4 — The Sigils (◇)

Orbital diamond markers that appear at the outer leg tips in Mid-Game form, then become fixed to the carapace in Full Progression.

```
  STARTING               MID-GAME               FULL PROGRESSION
  ─────────              ────────               ────────────────

  (no sigils)          ◇╲  │  ╱◇            ╔═◇╲  │  ╱◇═╗
                       ◇╱  │  ╲◇            ╚═◇╱  │  ╲◇═╝

                       Sigils ride the tips  Sigils pinned to carapace
                       — they move with the  — locked in place,
                       legs each frame       carapace absorbs motion
```

| Stage | Sigil behavior | Design meaning |
|-------|---------------|----------------|
| Starting | None | Form has no unlocked abilities beyond base |
| Mid-Game | Ride the outermost leg tip — flip and extend with each stride | Dynamic, orbital, responsive. Two ability slots. |
| Full | Pinned at carapace corners — static relative to body | Locked and integrated. Form is complete. Sigils are structural. |

**Design intent:** The sigil's change from dynamic-orbital to locked-structural is the key visual tell that the form is "done." Mid-game has an energetic, reaching quality. Full progression is solid — nothing is loose anymore.

---

### 5 — The Carapace

Protective outer shell that appears only in Full Progression. Blue double-line frame.

```
  STARTING               MID-GAME               FULL PROGRESSION
  ─────────              ────────               ────────────────

  (none)               (none)                 ╔═◇╲  │  ╱◇═╗
                                                  ◈╲─╬─╱◈
                                                   (◉◆◉)
                                                  ◈╱─╬─╲◈
                                              ╚═◇╱  │  ╲◇═╝
```

| Element | Meaning |
|---------|---------|
| `╔═ ═╗` | Top carapace — two corner anchors with horizontal bar |
| `╚═ ═╝` | Bottom carapace — mirror of top |
| `◇` at corners | Sigils now integrated as structural fasteners into the carapace corners |
| Blue coloring | Cold, structural. The carapace is not organic — it was built/grown. |

**Gameplay:** The carapace absorbs one hit. Shell shows visual cracks when damaged. Regenerates over time.

**Design intent:** The frame closes the form. Starting and mid-game forms are open — they reach outward. The carapace wraps everything in. The entity is complete and armored.

---

## Walk Cycle Comparison

All three forms run the same 5-frame stride at 8fps. The visual weight and reach increase with each stage.

### Frame 0 — Neutral / Rest

```
  W01 (Starting)         W02 (Mid-Game)         W03 (Full)
  ──────────────         ──────────────         ──────────

  ╲  │  ╱             ◇╲  │  ╱◇            ╔═◇╲  │  ╱◇═╗
   ╲─┼─╱               ╲─┼─╱                  ◈╲─╬─╱◈
    (◆)               (◈◆◈)                   (◉◆◉)
   ╱─┼─╲               ╱─┼─╲                  ◈╱─╬─╲◈
  ╱  │  ╲             ◇╱  │  ╲◇            ╚═◇╱  │  ╲◇═╝
```

### Frame 1 — Right Stride (Right legs extend)

```
  W01 (Starting)         W02 (Mid-Game)         W03 (Full)
  ──────────────         ──────────────         ──────────

  ╲   /  |             ◇╲   /  |◇           ╔═◇╲   /  |◇═╗
   ╲─┼──╱               ╲─┼──╱                 ◈╲─╬──╱◈
    (◆)               (◈◆◈)                   (◉◆◉)
   ╱─┼──╲               ╱─┼──╲                 ◈╱─╬──╲◈
  ╱   \  |             ◇╱   \  |◇           ╚═◇╱   \  |◇═╝
```

### Frame 2 — Peak Stride (All tips at max extension)

```
  W01 (Starting)         W02 (Mid-Game)         W03 (Full)
  ──────────────         ──────────────         ──────────

  |   |  \             ◇|   |  \◇           ╔═◇|   |  \◇═╗
   ╲──┼──|               ╲──┼──|               ◈╲──╬─|◈
     (◆)                (◈◆◈)                 (◉◆◉)
   ╱──┼──|               ╱──┼──|               ◈╱──╬─|◈
  |   |  /             ◇|   |  /◇           ╚═◇|   |  /◇═╝
```

*Rear inner arm ends straighten to `|` — most extended moment of the stride.*

### Frame 3 — Left Stride (Left legs extend)

```
  W01 (Starting)         W02 (Mid-Game)         W03 (Full)
  ──────────────         ──────────────         ──────────

  /  \  |              ◇/  \  |◇           ╔═◇/  \  |◇═╗
  |──┼─╱               |──┼─╱                ◈|──╬─╱◈
    (◆)               (◈◆◈)                   (◉◆◉)
  |──┼─╲               |──┼─╲                ◈|──╬─╲◈
  \  /  |              ◇\  /  |◇           ╚═◇\  /  |◇═╝
```

*Rear inner arm starts straighten to `|` — left side now extending.*

### Frame 4 — Settle (Returning to neutral)

```
  W01 (Starting)         W02 (Mid-Game)         W03 (Full)
  ──────────────         ──────────────         ──────────

  |  |  ╱              ◇|  |  ╱◇           ╔═◇|  |  ╱◇═╗
  ╲──┼─╱               ╲──┼─╱                ◈╲──╬─╱◈
    (◆)               (◈◆◈)                   (◉◆◉)
  ╱──┼─╲               ╱──┼─╲                ◈╱──╬─╲◈
  |  |  ╲              ◇|  |  ╲◇           ╚═◇|  |  ╲◇═╝
```

---

## Charge System

The charge display is the body. No HUD bar — read the core.

### Cells — Three States, Instant Read

Whether a cell **exists** is a boss-gated upgrade. How **charged** it is changes constantly.
Each unlocked cell moves through three states:

```
○  =  empty
◎  =  mid charge
◉  =  full charge
```

These three glyphs are visually unambiguous at a glance — open, ringed, filled.
Each cell holds 2 charge points (empty=0, mid=1, full=2). Six cells = **12 charge points max**.

### Cell Unlock — Boss-Gated Evolution

Defeating a boss permanently unlocks one cell pair — one cell on each side of the core. The core grows visibly wider. New cells appear dark, waiting to be filled.

```
Start:   (◆)          0 cells — 0 charge max   leg-strike only
Boss 1:  (○◆○)        2 cells — 2 charge max   glyph-pulse + silk-thread unlocked
Boss 2:  (○○◆○○)      4 cells — 4 charge max   phase-shift + wall-route unlocked
Boss 3:  (○○○◆○○○)    6 cells — 6 charge max   overload + depth-scan unlocked
```

The body reads its own progression. A wider core means more bosses defeated, more capacity, more power available.

### Filling Charge

| Source | Amount |
|--------|--------|
| Glyph-fragment pickup (enemy drop, environment) | +1 cell |
| Charge pad (fixed environmental point) | +3 cells (tunable) |
| Glyph-growth contact (passive background) | slow trickle — not a strategy, just ambient |

### Charge as Shield

**Charge depletes before health does.**

```
Hit at charge > 0  →  lose 1 charge point. Health untouched.
Hit at charge = 0  →  health takes damage.
```

High charge is both offensive capacity and defensive buffer. Firing aggressively burns through your shield. Conserving charge means you can absorb hits. The tradeoff is always live.

### Shot Power at Fire Time

Each shot costs 1 charge point. What you fire is determined by your total charge at the moment of pulling the trigger — not a pre-selected mode, not a held charge. Just: what do you have right now?

Cells drain inside-out: outermost cells empty first, preserving inner charge as long as possible.

```
12  (◉◉◉◆◉◉◉)  zone overload — slow, massive, area effect, clears glyph-growth
10  (◎◉◉◆◉◉◎)  heavy glyph, high damage, slow travel
 8  (○◉◉◆◉◉○)  strong, solid range
 6  (○◎◉◆◉◎○)  standard — reliable workhorse
 4  (○○◉◆◉○○)  fast dart, reduced damage, shorter range
 2  (○○◎◆◎○○)  weak poke — but it's something
 0  (○○○◆○○○)  leg-strike only
```

Firing burns charge — each shot weaker than the last. Combat is a managed burn. The opening shot from full charge is the best shot you will get until you refuel.

### Zone Projectile Vocabulary

The projectile glyph scales with charge, using each zone's own visual language:

| Charge | The Terminal | The Conduit | The Rot | The Vault |
|--------|-------------|-------------|---------|-----------|
| 6 | `█` | `⊕` | `✕` | `◉` |
| 4–5 | `▓` | `◆` | `▓` | `◈` |
| 2–3 | `▒` | `◎` | `▒` | `◦` |
| 1 | `·` | `─` | `,` | `·` |

What you fire reads as *of the world you're in.* The weapon is the zone.

---

## Ability Unlock Progression

Each boss defeat unlocks one cell pair and the abilities that come with it. The visual change and the ability unlock are the same event.

### Starting Form — Core Only `(◆)`

| Ability | Charge cost | Notes |
|---------|-------------|-------|
| **Leg-strike** | Free (0.4s cooldown) | Two front legs extend 120°, glyph sparks on hit. Always available. |

### Boss 1 — First Cell Pair `(○◆○)` → `(◉◆◉)`

| Ability | Charge cost | Notes |
|---------|-------------|-------|
| **Glyph-pulse** | 1 cell per shot | Power scales with current charge at fire time. Zone glyph vocabulary. |
| **Silk-thread** | 2 cells | Fires `─────◎` strand. Enemy hit: stuns 1.5s. Surface hit: grapple pull. |

### Boss 2 — Second Cell Pair `(○○◆○○)` → `(◉◉◆◉◉)`

| Ability | Charge cost | Notes |
|---------|-------------|-------|
| **Phase-shift** | — | Core briefly hollow `○` — short invincibility window, pass thin barriers. |
| **Wall-route** | — | Leg tips gain grip-glyphs. Wall-crawl in wall-rooms without drain. |

### Boss 3 — Third Cell Pair `(○○○◆○○○)` → `(◉◉◉◆◉◉◉)`

| Ability | Charge cost | Notes |
|---------|-------------|-------|
| **Overload** | Automatic at charge 6 | Firing at full charge triggers overload behavior — no separate mode. Core flares, detonates. |
| **Depth-scan** | — | Core eyes surface as `◉` — reveals hidden paths, glyph-growth decodes into passages. |

---

## Color Language

Each ANSI color carries a consistent meaning across all forms.

| Color | Glyph elements | Meaning |
|-------|---------------|---------|
| Red `\033[91m` | `◆` core | The process itself — primary identity |
| Cyan `\033[96m` | Legs, connectors, `┼ ╬ ─` | Mobility, structure, the physical body |
| Yellow `\033[93m` | `◈ ◉` on core and arms | Ability nodes, powered junctions |
| Magenta `\033[95m` | `◇` sigils | Orbital abilities — active power slots |
| Blue `\033[94m` | Carapace `╔═╗ ╚═╝` | Armor, cold structure, protection |
| White `\033[97m` | Body brackets `( )` | Containment — the shell holding the core |

---

## Progression Narrative

The three forms are not costume changes. Each is a different version of the same entity at different stages of self-assembly.

**Starting — The process awakens.** Compact, raw, no adornment. Eight legs, one core, nothing wasted. The rogue process has just escaped and doesn't yet know what it is.

**Mid-Game — The process recognizes itself.** The `◈` junction orbs emerge not as attachments but as expressions of accumulated self-knowledge. The `◇` sigils orbit the tips — loose, dynamic, still figuring out what they are. Two abilities unlocked. Two questions answered.

**Full Progression — The entity is whole.** The carapace closes. The sigils lock. The junction upgrades to `╬`. Nothing is exploratory anymore — the form is complete, intentional, sealed. The `◉` core is not brighter than `◆`; it has more structure. The entity knows what it is.

> *Reading the character reads the loadout. There is no separate status screen.*
