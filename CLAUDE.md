# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Reference Docs

- **System overview, architecture, patterns:** [`.github/copilot-instructions.md`](.github/copilot-instructions.md)
- **Python coding standards, module structure, conventions:** [`.github/python-instructions.md`](.github/python-instructions.md)

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

# Optional: install globally (legacy single-file)
chmod +x justdoit.py && cp justdoit.py /usr/local/bin/justdoit
```

---

## Architecture

### Package Structure

```
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

### Dependencies

- **Core:** zero — pure Python 3 stdlib
- **TTF/OTF fonts:** requires `Pillow` (included in dev venv via `uv sync --dev`)
- **Tests:** `pytest` + `Pillow` (installed via `uv sync --dev`)

### Python Environment — IMPORTANT

This project uses `uv` + a managed `.venv`. **Do not use `pip` or `python3` directly.**

```bash
# Run tests:
.venv/bin/pytest tests/ -q

# Run scripts:
.venv/bin/python scripts/demo.py

# Run CLI:
.venv/bin/python justdoit.py "Hello"

# Add a dependency:
uv add --dev <package>
```

The `.venv` has `pytest`, `Pillow`, and `justdoit` (editable install) already.
System `python3` does NOT have these — always use `.venv/bin/python` or `uv run`.

Optional Pillow features degrade gracefully — all PIL-gated code checks availability at call time and raises `ImportError` with a helpful install hint.

---

## Skills Directory

`skills/ascii_art_generator/` is an OpenClaw skill wrapper. Its `main.py` calls `render()` and writes the result to a file. It adds the repo root to `sys.path` so the import works regardless of working directory.

The skill uses `--key=value` argument syntax (not `--key value`):

```bash
openclaw run skills/ascii_art_generator main.py --text='Hello World' --output=/path/to/output.txt
```
