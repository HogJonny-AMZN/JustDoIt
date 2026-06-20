# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Reference Docs

- **System overview, architecture, patterns:** [`.github/copilot-instructions.md`](.github/copilot-instructions.md)
- **Python coding standards, module structure, conventions:** [`.github/python-instructions.md`](.github/python-instructions.md)
- **Vision and roadmap:** [`docs/VISION.md`](docs/VISION.md)
- **Technique registry (all fills, fonts, effects — status + novelty):** [`docs/research/TECHNIQUES.md`](docs/research/TECHNIQUES.md)
- **Architecture decisions (why things are the way they are):** [`docs/decisions/`](docs/decisions/)
- **Effects danger zone (fill contract, module map):** [`justdoit/effects/CLAUDE.md`](justdoit/effects/CLAUDE.md)

## ⚠️ Patent Flag Protocol

If you implement or discover something with **no known prior art**, stop before pushing to GitHub.

Message Jonny (HogJonny) immediately:
> "⚠️ PATENT FLAG: [name] — [why it's novel]. No prior art found in [sources]. Recommend review before publishing."

Public disclosure destroys patent rights. When in doubt, flag it.

---

## Skills (Reusable Workflows)

Use these when asked to perform common tasks — load the SKILL.md, follow it exactly:

| Task | Skill |
|------|-------|
| Research session / daily build | [`.claude/skills/research-session/SKILL.md`](.claude/skills/research-session/SKILL.md) |
| Add a new fill effect | [`.claude/skills/add-fill-effect/SKILL.md`](.claude/skills/add-fill-effect/SKILL.md) |
| Add a new font | [`.claude/skills/add-font/SKILL.md`](.claude/skills/add-font/SKILL.md) |
| Regenerate gallery SVGs | [`.claude/skills/regenerate-gallery/SKILL.md`](.claude/skills/regenerate-gallery/SKILL.md) |
| Regenerate animation gallery | [`.claude/skills/regenerate-anim-gallery/SKILL.md`](.claude/skills/regenerate-anim-gallery/SKILL.md) |

---

## Commands

```bash
# Run the CLI
python justdoit.py "Your Text"
python justdoit.py "FIRE" --color rainbow
python justdoit.py "hello" --font slim --color cyan
python justdoit.py "hi" --gap 3
python justdoit.py "HEY" --font big          # FIGlet font
python justdoit.py "HEY" --ttf DejaVuSans   # TTF (requires Pillow)

# List available options
python justdoit.py --list-fonts
python justdoit.py --list-colors

# Newer effect / output flags (see "CLI Flags" below for the full set)
python justdoit.py "HI" --animate glitch --fps 20 --loop   # terminal animation
python justdoit.py "HI" --iso 4 --gradient red yellow      # 3D extrude + gradient
python justdoit.py "HI" --hd --save-png out.png            # high-density 4K PNG
python justdoit.py "HI" --measure                          # print size / display fit, exit

# Dev environment (uv)
uv sync --dev     # Create .venv, install all dev deps (pytest, Pillow, numpy, sounddevice, arcade, ruff)
uv run pytest     # Run all tests
uv run pytest -v  # Verbose
uv run pytest -q  # Quiet
uv run pytest tests/test_figlet.py -v          # Single test module
uv run pytest -m "not slow and not manual"     # Skip slow/manual-marked tests (CI default)
uv run ruff check .                             # Lint (line length 120; config in pyproject.toml)

# Run the Arcade game (requires the `game` extra: arcade>=3.0, Pillow)
uv run python -m game.main

# Optional: install globally (legacy single-file)
chmod +x justdoit.py && cp justdoit.py /usr/local/bin/justdoit
```

---

## Architecture

### Package Structure

```text
justdoit/
├── __init__.py            # Public API
├── cli.py                 # argparse entry point → main() (large flag surface, see CLI Flags)
├── layout.py              # Resolution/size helpers: measure(), RenderTarget, DISPLAYS, fit_text, --hd sizing (pure stdlib)
├── core/
│   ├── glyph.py           # Glyph data structures
│   ├── char_db.py         # Character metadata
│   ├── rasterizer.py      # Glyph → ASCII raster pipeline
│   ├── pipeline.py        # render() orchestration
│   ├── image_pipeline.py  # Image → ASCII pipeline
│   └── image_sampler.py   # Image sampling for ASCII conversion
├── fonts/
│   ├── __init__.py        # Font registry
│   ├── builtin/
│   │   ├── block.py       # 7-row Unicode block font (A–Z, 0–9, punctuation)
│   │   └── slim.py        # 3-row ASCII line-drawing font
│   ├── figlet.py          # FIGlet (.flf) parser and renderer
│   ├── figlet_fonts/      # Bundled .flf files: banner, big, block, bubble, digital, slant
│   └── ttf.py             # TTF/OTF rasterizer (requires Pillow)
├── effects/               # See justdoit/effects/CLAUDE.md for the fill contract
│   ├── color.py           # ANSI colorization, rainbow mode
│   ├── fill.py            # Density fill, SDF outline effects
│   ├── gradient.py        # Linear / radial gradients, palettes
│   ├── isometric.py       # 3D isometric extrusion
│   ├── spatial.py         # Warp, perspective, shear transforms
│   ├── shape_fill.py      # Shape-aware fills
│   ├── recursive.py       # Typographic recursion (text-in-text)
│   └── generative.py      # Generative/simulation fills
├── animate/               # Terminal animation engine (requires nothing; sound is optional)
│   ├── player.py          # Frame-loop player w/ ANSI cursor control; optional sound hook
│   └── presets.py         # Generators: typewriter, scanline, glitch, pulse, dissolve, ...
├── sound/                 # OPTIONAL procedural audio — import-gated via SOUND_AVAILABLE
│   ├── synth.py           # Waveform synthesis (sweeps, noise, decay) — needs numpy
│   └── player.py          # Frame-synced async playback — needs sounddevice
└── output/
    ├── terminal.py        # Terminal output helpers
    ├── ansi_parser.py     # Parse ANSI back into structured cells
    ├── svg.py             # SVG export (--save-svg)
    ├── html.py            # HTML export (--save-html)
    ├── image.py           # PNG export (--save-png)
    ├── apng.py            # Animated PNG export
    ├── cast.py            # asciinema .cast export
    ├── arcade_atlas.py    # Build font texture atlas (PNG + UV JSON) for the game
    └── sprite_sheet.py    # Sprite strip generator — STUB (raises NotImplementedError)
```

There is also a legacy `justdoit.py` at the repo root for backwards compatibility.

### `game/` Package (Arcade side-scroller)

`game/` is a separate top-level package — an Arcade (`arcade>=3.0`) ASCII side-scroller that uses JustDoIt as its asset pipeline. Logical resolution 3840×1080 (32:9), 60fps target. **Status: scaffold** — scenes, entities, physics, and collision exist but are incomplete. The player character is **GLYPHSTER** (a multi-stage evolving glyph; see design docs below).

```text
game/
├── main.py            # Entry point → Arcade window + game loop  (uv run python -m game.main)
├── build/             # Asset build: build_atlas.py, build_sprites.py (consume justdoit.output.*)
├── engine/            # atlas, camera, tile_renderer, particle_system, post_process
├── entities/          # player.py (PlayerState), enemy.py
├── levels/            # level_01.py
├── scenes/            # title / gameplay / game_over
├── systems/           # physics.py, collision.py
└── gallery/           # generate_game_gallery.py
```

Build flow: `justdoit.output.arcade_atlas.build_atlas()` packs a font into a texture atlas (PNG) + glyph UV map (JSON) → loaded at runtime by `game/engine/atlas.py`.

Design docs:
- [`docs/superpowers/specs/2026-04-30-ascii-arcade-game-design.md`](docs/superpowers/specs/2026-04-30-ascii-arcade-game-design.md)
- [`docs/superpowers/specs/2026-05-01-glyphster-game-design.md`](docs/superpowers/specs/2026-05-01-glyphster-game-design.md)
- [`docs/game_gallery/GLYPHSTER_PROGRESSION.md`](docs/game_gallery/GLYPHSTER_PROGRESSION.md)

### Rendering Pipeline

1. `cli.py` — parses args, selects font/color/effect
2. `pipeline.render()` — uppercases input, maps chars to glyphs, concatenates rows with gap spacer
3. `effects/color.colorize()` — wraps in ANSI escape codes; rainbow cycles per-char index
4. `output/terminal.py` — prints to stdout

**Hard constraint:** All glyphs in a font must have the same row count (height). The pipeline zips rows across characters — mismatched heights corrupt output.

### Font Types

| Font | Source | Height | Requires |
| ---- | ------ | ------ | -------- |
| `block` | `builtin/block.py` | 7 rows | nothing |
| `slim` | `builtin/slim.py` | 3 rows | nothing |
| `banner`, `big`, `bubble`, `digital`, `slant` (figlet) | bundled `.flf` | varies | nothing |
| TTF/OTF system fonts | Pillow rasterizer | configurable (default 7) | Pillow |

### CLI Flags

`cli.py` has grown well beyond `--font/--color/--gap/--ttf`. Grouped overview (run `python justdoit.py -h` for exact spelling/defaults):

| Group | Flags |
| ----- | ----- |
| Animation | `--animate {typewriter,scanline,glitch,pulse,dissolve}`, `--fps`, `--loop` |
| Spatial | `--iso DEPTH` `--iso-dir`, `--warp` `--warp-freq`, `--perspective` `--perspective-dir`, `--shear` `--shear-dir` |
| Color/gradient | `--gradient FROM TO` `--gradient-dir`, `--radial INNER OUTER`, `--palette NAME` |
| Fill | `--fill`, `--truchet-style`, `--recursion` `--recursion-sep` |
| Output files | `--save-svg`, `--save-html`, `--save-png` (+ `--svg-font-size`) |
| Sizing/display | `--target WxH[@Sx]`, `--hd [COLS]`, `--fit COLS`, `--measure`, `--ttf-size` |

`--measure` and `--hd` are powered by `justdoit/layout.py` (`measure()`, `RenderTarget`, `DISPLAYS`). The 4K strategy is **PNG, not SVG** (see [`docs/VISION.md`](docs/VISION.md)).

### Adding New Fonts

**Builtin font:** Create `justdoit/fonts/builtin/myfont.py` with `MYFONT: dict[str, list[str]]`, ensure all glyphs have identical row counts, then register in `justdoit/fonts/__init__.py`.

**FIGlet font:** Drop `.flf` into `justdoit/fonts/figlet_fonts/` and register in `justdoit/fonts/__init__.py`. No parser changes needed.

### Dependencies

Core install has **zero** dependencies. Optional features are `pyproject.toml` extras (all installed by `uv sync --dev`):

| Extra | Packages | Enables |
| ----- | -------- | ------- |
| `ttf` | `Pillow>=10.0` | TTF/OTF rasterization, PNG/image output |
| `sound` | `numpy>=1.24`, `sounddevice>=0.4` | Procedural audio synth + frame-synced playback |
| `game` | `arcade>=3.0`, `Pillow>=10.0` | The `game/` Arcade side-scroller |

Each optional path is **import-gated** and degrades gracefully — e.g. `justdoit.sound` exposes a `SOUND_AVAILABLE` flag; PIL-gated code raises `ImportError` with an install hint at call time. Never hard-fail or silently skip these paths in tests; gate with `pytest.importorskip(...)`.

> ⚠️ **Pillow note:** Pillow is confirmed available in this project's `.venv`. Always use `uv run` (not bare `python`) to ensure Pillow/numpy/sounddevice/arcade import correctly. Do NOT fall back to system fonts or skip PIL-gated paths — use `uv run` and the deps will be present.

### Python Environment — IMPORTANT

This project uses `uv`. **Do not use `pip`, `python3`, or `.venv/bin/` paths directly.**
The `.venv` shebangs are hardcoded to the machine that built them — they break in Docker/CI.
Always use `uv run` instead. It works everywhere.

```bash
# Run tests:
uv run pytest tests/ -q

# Run a single test file:
uv run pytest tests/test_fill.py -v

# Run scripts:
uv run python scripts/demo.py
uv run python scripts/generate_gallery.py

# Run CLI:
uv run python justdoit.py "Hello"

# Add a dependency:
uv add --dev <package>

# Sync environment (after clone or dependency change):
uv sync --dev
```

`uv run` automatically uses the project's `.venv` regardless of working directory or platform.

Optional Pillow features degrade gracefully — all PIL-gated code checks availability at call time and raises `ImportError` with a helpful install hint.

---

## Module Structure

Every Python module must follow this header pattern (from `.github/python-instructions.md`):

```python
"""
Package: justdoit.subpackage.module
Brief one-line description.
"""

import logging as _logging

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.subpackage.module"  # must match Package docstring
__updated__ = "YYYY-MM-DD HH:MM:SS"
__version__ = "X.Y.Z"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)  # use _MODULE_NAME, NOT __name__
```

Every top-level function/class must be preceded by a separator line:

```python
# -------------------------------------------------------------------------
def my_function() -> None:
```

**Key rules:**

- No `print()` in library code — use `_LOGGER` with appropriate level
- Line length: 120 characters (PEP 8 extended)
- All functions require type hints and ReST-format docstrings
- Use `pathlib.Path` for all paths, not string operations
- PIL-gated tests: `pytest.importorskip("PIL")` — never hard-fail
- Imports: stdlib → third-party (guarded) → local absolute

---

## Commit Conventions

- `feat:` new font, effect, or CLI flag
- `fix:` bug fix
- `refactor:` structural improvement
- `test:` test additions or fixes
- `docs:` documentation updates
- `chore:` build, tooling, deps

---

## Skills Directory

`skills/ascii_art_generator/` is an OpenClaw skill wrapper. Its `main.py` calls `render()` and writes the result to a file. It adds the repo root to `sys.path` so the import works regardless of working directory.

The skill uses `--key=value` argument syntax (not `--key value`):

```bash
openclaw run skills/ascii_art_generator main.py --text='Hello World' --output=/path/to/output.txt
```
