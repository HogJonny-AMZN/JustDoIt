# REFACTOR.md — Bite 1: Package Layout

Restructured the single-file `justdoit.py` into a proper Python package with no behavior changes.

## What moved where

| Old location (`justdoit.py`) | New location |
|---|---|
| `BLOCK` dict | `justdoit/fonts/builtin/block.py` |
| `SLIM` dict | `justdoit/fonts/builtin/slim.py` |
| `FONTS` registry | `justdoit/fonts/__init__.py` |
| `COLORS`, `RAINBOW_CYCLE`, `colorize()` | `justdoit/effects/color.py` |
| `render()` | `justdoit/core/rasterizer.py` |
| `main()` | `justdoit/cli.py` |

## New files (stubs / scaffolding)

| File | Purpose |
|---|---|
| `justdoit/core/glyph.py` | Documents the glyph data structure; placeholder for Bite 2 mask abstraction |
| `justdoit/core/pipeline.py` | Stub documenting the planned stage-chaining architecture |
| `justdoit/output/terminal.py` | `print_art()` wrapper; first output target in a future multi-target system |

## Entry points

- **`justdoit.py`** (root) — thin shim: `from justdoit.cli import main; main()`. Preserves all existing CLI usage.
- **`justdoit/__init__.py`** — exports `render()` and `colorize()` for programmatic use (`from justdoit import render`).
- **`skills/ascii_art_generator/main.py`** — unchanged; `from justdoit import render` now resolves through the package `__init__`.
