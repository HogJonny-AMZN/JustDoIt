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

# Dev environment (uv)
uv sync --dev     # Create .venv, install pytest + Pillow
uv run pytest     # Run all tests
uv run pytest -v  # Verbose
uv run pytest -q  # Quiet
uv run pytest tests/test_figlet.py -v  # Single test module

# Optional: install globally (legacy single-file)
chmod +x justdoit.py && cp justdoit.py /usr/local/bin/justdoit
```

---

## Architecture

### Package Structure

```text
justdoit/
├── __init__.py            # Public API
├── cli.py                 # argparse entry point → main()
├── core/
│   ├── glyph.py           # Glyph data structures
│   ├── rasterizer.py      # Glyph → ASCII raster pipeline
│   └── pipeline.py        # render() orchestration
├── fonts/
│   ├── __init__.py        # Font registry
│   ├── builtin/
│   │   ├── block.py       # 7-row Unicode block font (A–Z, 0–9, punctuation)
│   │   └── slim.py        # 3-row ASCII line-drawing font
│   ├── figlet.py          # FIGlet (.flf) parser and renderer
│   ├── figlet_fonts/      # Bundled .flf files: banner, big, block, bubble, digital, slant
│   └── ttf.py             # TTF/OTF rasterizer (requires Pillow)
├── effects/
│   ├── color.py           # ANSI colorization, rainbow mode
│   └── fill.py            # Density fill, SDF outline effects
└── output/
    └── terminal.py        # Terminal output helpers
```

There is also a legacy `justdoit.py` at the repo root for backwards compatibility.

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

### Adding New Fonts

**Builtin font:** Create `justdoit/fonts/builtin/myfont.py` with `MYFONT: dict[str, list[str]]`, ensure all glyphs have identical row counts, then register in `justdoit/fonts/__init__.py`.

**FIGlet font:** Drop `.flf` into `justdoit/fonts/figlet_fonts/` and register in `justdoit/fonts/__init__.py`. No parser changes needed.

### Dependencies

- **Core:** zero — pure Python 3 stdlib
- **TTF/OTF fonts:** requires `Pillow` (included in dev venv via `uv sync --dev`)
- **Tests:** `pytest` + `Pillow` (installed via `uv sync --dev`)

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
