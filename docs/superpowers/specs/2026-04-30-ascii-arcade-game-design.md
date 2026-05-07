# ASCII Arcade Side-Scroller — Architecture Design
*2026-04-30 · JustDoIt repo · Python Arcade 3.x*

---

## Overview

A 2D side-scrolling game that looks like ASCII art but is not a terminal application.
The visual aesthetic is entirely ASCII characters rendered as GPU sprites; the runtime
is Python Arcade (OpenGL) at 3840×1080 (32:9 native).

JustDoIt is the **asset authoring pipeline**, not the game runtime.  It generates
font texture atlases and sprite sheets at build time.  The game's engine layer
(`game/engine/`) is a thin, reusable Arcade abstraction that any ASCII-style game
could use.

The game lives at `game/` in the JustDoIt repo and fits the vision's roadmap:

```
Terminal → SVG/PNG → 4K PNG → Browser → WebGL/GPU ← we are here
```

---

## Folder Layout

```
game/
├── main.py                    # entry point; creates Window, shows TitleScene
├── engine/                    # reusable Arcade primitives (no game logic)
│   ├── atlas.py               # AsciiAtlas — load PNG atlas, expose GlyphRegion UVs
│   ├── tile_renderer.py       # TileRenderer — draw TileGrid as batched sprites
│   ├── particle_system.py     # AsciiParticleSystem — ASCII glyph particles
│   ├── post_process.py        # PostProcessPipeline — render-texture + GLSL chain
│   └── camera.py              # ScrollingCamera — smooth-follow viewport
├── scenes/                    # arcade.View subclasses (one per screen)
│   ├── title_scene.py
│   ├── gameplay_scene.py
│   └── game_over_scene.py
├── entities/                  # plain dataclass state objects (no Arcade coupling)
│   ├── player.py              # PlayerState
│   └── enemy.py               # EnemyState
├── systems/                   # stateless functions operating on entity data
│   ├── physics.py             # gravity, velocity integration
│   └── collision.py           # AABB tile and entity collision
├── levels/
│   └── level_01.py            # tile map + entity spawn data
├── shaders/                   # GLSL fragment shaders for post-process passes
│   ├── crt.glsl               # scanlines + barrel distortion + vignette
│   ├── bloom.glsl             # luminance-threshold blur + additive blend
│   └── chromatic_aberration.glsl
├── build/                     # run before game launch (depend on justdoit)
│   ├── build_atlas.py         # font → atlas PNG + UV JSON
│   └── build_sprites.py       # text+effects → sprite sheet PNGs
└── assets/                    # generated outputs (not committed, rebuild on clone)
    ├── atlas/
    └── sprites/
```

### JustDoIt API additions

New modules added to the JustDoIt library to support the game (and any future GPU substrate):

```
justdoit/core/tile_grid.py          # TileCell, TileGrid — substrate-agnostic cell grid
justdoit/output/arcade_atlas.py     # build_atlas() — font → PNG atlas + UV JSON
justdoit/output/sprite_sheet.py     # build_sprite_sheet() — text+effects → PNG strip
```

`TileGrid` is the canonical shared data format between JustDoIt's render pipeline
and all downstream consumers.  It replaces ad-hoc list-of-strings representations
that exist in several places today.

---

## Layer Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  ASSET PIPELINE  (build time, Python + JustDoIt)                 │
│  build_atlas.py → ascii_atlas.png + ascii_atlas.json             │
│  build_sprites.py → player.png, enemy_basic.png …                │
└──────────────────────────────────┬───────────────────────────────┘
                                   │ PNG files on disk
┌──────────────────────────────────▼───────────────────────────────┐
│  ENGINE LAYER  (game/engine/, reusable)                          │
│  AsciiAtlas · TileRenderer · AsciiParticleSystem                 │
│  PostProcessPipeline · ScrollingCamera                           │
└──────────────────────────────────┬───────────────────────────────┘
                                   │ draw calls, shader passes
┌──────────────────────────────────▼───────────────────────────────┐
│  GAME LAYER  (game/scenes/, entities/, systems/, levels/)        │
│  TitleScene · GameplayScene · GameOverScene                      │
│  PlayerState · EnemyState · physics · collision                  │
└──────────────────────────────────────────────────────────────────┘
```

**Rule:** Nothing in `game/engine/` knows about game rules.
Nothing in `game/entities/` or `game/systems/` imports Arcade.
Arcade lives only in `game/engine/` and `game/scenes/`.

---

## Rendering Pipeline (per frame)

```
GameplayScene.on_draw()
  │
  ├─ with PostProcessPipeline.capture():    ← redirect to offscreen RenderTexture
  │    ├─ camera.use()
  │    ├─ TileRenderer.draw()               ← batched BG quads + glyph sprites
  │    ├─ draw entities (sprite lists)
  │    └─ AsciiParticleSystem.draw()        ← glyph particles
  │
  └─ PostProcessPipeline.render()
       ├─ ShaderPass("bloom")               ← ping-pong between two RenderTextures
       ├─ ShaderPass("crt")
       ├─ ShaderPass("chromatic_aberration")
       └─ blit final texture to screen
```

Two ping-pong `RenderTexture2D` objects are allocated at startup.  Each pass reads
from one and writes to the other.  The final pass writes to the default framebuffer.

---

## Asset Pipeline (build time)

```
uv run python -m game.build.build_atlas
  └─ justdoit.output.arcade_atlas.build_atlas(font="block", cell=8×16)
       └─ renders each printable ASCII char via PIL ImageDraw
       └─ packs into N×M grid PNG
       └─ writes ascii_atlas.json: {"A": {"x": 0, "y": 0, "w": 8, "h": 16}, …}

uv run python -m game.build.build_sprites
  └─ justdoit.output.sprite_sheet.build_sprite_sheet(text="@", effects=[...])
       └─ calls justdoit image pipeline per frame
       └─ packs frames left-to-right into PNG strip
```

Assets are written to `game/assets/` which is git-ignored.  A `Makefile` or
`build.py` at the repo root will run both scripts before `game/main.py`.

**Open question:** should assets be committed for reproducibility, or always
regenerated?  Current decision: regenerate on clone (add to `.gitignore`).

---

## TileGrid as Shared Data Format

`justdoit.core.tile_grid.TileGrid` is the canonical representation of a rendered
ASCII scene across all substrates:

| Substrate | Consumer |
|---|---|
| Terminal | `justdoit/output/terminal.py` (future: adapt to use TileGrid) |
| PNG / 4K | `justdoit/core/image_pipeline.py` (future) |
| Arcade game | `game/engine/tile_renderer.py` |

A `TileGrid` is a 2D array of `TileCell(char, fg, bg)`.  It has no knowledge of
pixel sizes, fonts, or rendering backends.

---

## Dependency Model

```
justdoit (core)        ← zero runtime deps
justdoit.output.arcade_atlas  ← requires Pillow (build time only)
justdoit.output.sprite_sheet  ← requires Pillow (build time only)
justdoit.core.tile_grid       ← zero deps, part of core

game.engine            ← requires arcade>=3.0
game.scenes            ← requires arcade>=3.0
game.entities          ← zero deps (plain dataclasses)
game.systems           ← zero deps (pure Python)
game.build             ← requires justdoit + Pillow (build time only)
```

The game runtime (`game/engine/`, `game/scenes/`) has **no dependency on JustDoIt**.
JustDoIt is only imported at build time in `game/build/`.

---

## Technology Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Game framework | Python Arcade 3.x | OpenGL GPU pipeline, shader support, texture atlases, active maintenance |
| Logical resolution | 3840×1080 | Native 32:9; scales down cleanly for narrower displays |
| Target FPS | 60 | Standard; Arcade's default scheduler |
| Shader language | GLSL 330 | Arcade's OpenGL context is core profile 3.3 |
| Post-process approach | Ping-pong RenderTexture2D | Standard pattern; avoids allocating per-pass |
| Particle physics | CPU per-frame | Simple enough; GPU compute reserved for if particle count > 2000 |
| Level format | Python module (list literals) | Zero parsing overhead; easy to author and diff |
| Asset format | PNG + JSON | Pillow-compatible; no custom formats |
| Font atlas layout | Linear grid | Simple UV math; predictable for debugging |

---

## Open Questions

1. **Runtime JustDoIt usage** — Should the game ever call JustDoIt at runtime (e.g. dynamically generate a plasma texture for a boss fight)?  Current answer: no — build-time only.  Revisit when a use case arises.

2. **Level format** — Python module vs. JSON vs. Tiled `.tmx`.  Python module chosen for now; Tiled is a natural upgrade if levels grow complex.

3. **Entity model** — Plain dataclasses + stateless systems vs. Arcade's built-in `Sprite`/`SpriteList`.  Current: dataclasses for state, Arcade sprites only for rendering (held by `TileRenderer` and `AsciiParticleSystem`).  Revisit if collision detection becomes complex.

4. **Shader vertex pass** — Current stubs assume a full-screen quad vertex shader is provided by Arcade.  Need to confirm Arcade 3.x provides this or write it.

5. **Asset regeneration** — Whether assets live in git or are always rebuilt.  Decision pending.

---

*First draft 2026-04-30.*
