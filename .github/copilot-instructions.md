# GitHub Copilot Instructions

**Last Updated:** 2026-03-23
**Status:** Active development — core pipeline complete, font/effects system expanding

---

## Quick Reference

**Repository:** HogJonny-AMZN/JustDoIt (Git/GitHub)
**Python Version:** 3.11+
**Required Dependencies:** None (pure Python 3 stdlib)
**Optional Dependencies:** Pillow (TTF/OTF font support)
**Dev Environment:** `uv sync --dev` → `.venv` with pytest + Pillow

**Key Entry Points:**
- CLI: `python justdoit.py "Your Text"`
- Package entry: `justdoit/cli.py` → `main()`
- Core render: `justdoit/core/pipeline.py` → `render()`

**Coding standards and module patterns:** See `.github/python-instructions.md`

---

## Project Overview

**JustDoIt** is a zero-dependency Python 3 ASCII art CLI. It renders text as multi-line ANSI-colorized terminal output using bitmap fonts.

**Design goals:**
- Zero required external dependencies — core stays pure Python 3 stdlib
- Graceful degradation — optional features (Pillow, figlet) skip cleanly if unavailable
- Fast, readable, composable — small focused modules with a clean pipeline

---

## Architecture

### Package Structure

```
justdoit/
├── __init__.py            # Public API
├── cli.py                 # argparse entry point → main()
├── core/
│   ├── __init__.py
│   ├── glyph.py           # Glyph data structures
│   ├── rasterizer.py      # Glyph → ASCII raster pipeline
│   └── pipeline.py        # render() orchestration
├── fonts/
│   ├── __init__.py        # Font registry
│   ├── builtin/
│   │   ├── block.py       # 7-row Unicode block font (A–Z, 0–9, punctuation)
│   │   └── slim.py        # 3-row ASCII line-drawing font
│   ├── figlet.py          # FIGlet (.flf) parser and renderer
│   ├── figlet_fonts/      # Bundled .flf files (banner, big, block, bubble, digital, slant)
│   └── ttf.py             # TTF/OTF rasterizer (requires Pillow)
├── effects/
│   ├── __init__.py
│   ├── color.py           # ANSI colorization, rainbow mode
│   └── fill.py            # Density fill, SDF outline effects
└── output/
    └── terminal.py        # Terminal output helpers
```

There is also a legacy single-file `justdoit.py` at the repo root for backwards compatibility.

### Rendering Pipeline

```
cli.py (argparse)
    ↓
pipeline.render(text, font, color, gap)
    ↓ uppercase input
    ↓ map chars → glyphs (unknown → space fallback)
    ↓ zip rows across characters + gap spacer
    ↓
effects/color.colorize()
    ↓ ANSI escape codes; rainbow cycles per-char index
    ↓
output/terminal.py → stdout
```

**Hard constraint:** All glyphs in a font must have the same row count (height). The pipeline zips rows across characters — mismatched heights corrupt output silently.

### Font Types

| Font | Source | Height | Requires |
|------|--------|--------|----------|
| `block` | builtin/block.py | 7 rows | nothing |
| `slim` | builtin/slim.py | 3 rows | nothing |
| `banner`, `big`, `bubble`, `digital`, `slant`, `block` (figlet) | bundled .flf | varies | nothing |
| TTF/OTF system fonts | Pillow rasterizer | configurable (default 7) | Pillow |

### Optional Dependency Pattern

Any feature gated on Pillow must guard the import and raise a helpful error:

```python
def _require_pil() -> None:
    """Raise ImportError with install hint if Pillow is unavailable."""
    try:
        import PIL  # noqa: F401
    except ImportError:
        raise ImportError(
            "TTF font support requires Pillow. Install with: pip install Pillow"
        )
```

Tests for PIL-gated features must use `pytest.importorskip("PIL")` — never hard-fail.

---

## Essential Commands

```bash
# Run the CLI
python justdoit.py "Your Text"
python justdoit.py "FIRE" --color rainbow
python justdoit.py "hello" --font slim --color cyan
python justdoit.py "hi" --gap 3
python justdoit.py "HEY" --font big           # FIGlet font
python justdoit.py "HEY" --ttf DejaVuSans     # TTF (requires Pillow)

# List options
python justdoit.py --list-fonts
python justdoit.py --list-colors

# Dev environment
uv sync --dev          # Install .venv with pytest + Pillow
uv run pytest          # Run all tests
uv run pytest -v       # Verbose
uv run pytest -q       # Quiet

# Optional: install globally (single-file legacy mode)
chmod +x justdoit.py && cp justdoit.py /usr/local/bin/justdoit
```

---

## Critical Code Patterns

### Font Data Structure

All fonts (builtin and FIGlet) produce the same structure:

```python
# dict[str, list[str]] — char → list of row strings
BLOCK_FONT: dict[str, list[str]] = {
    "A": [
        " ██ ",
        "█  █",
        "████",
        "█  █",
        "█  █",
        "    ",
        "    ",
    ],
    " ": [
        "  ",
        "  ",
        "  ",
        "  ",
        "  ",
        "  ",
        "  ",
    ],
    # ... all glyphs must have exactly 7 rows
}
```

### Render Pipeline

```python
def render(text: str, font: str = "block", color: str = "white", gap: int = 1) -> str:
    """Render text as multi-line ASCII art with ANSI color."""
    font_data = get_font(font)           # dict[str, list[str]]
    text = text.upper()
    height = get_font_height(font_data)  # all glyphs must match
    rows = [""] * height

    for char in text:
        glyph = font_data.get(char, font_data[" "])  # unknown → space
        for i, row in enumerate(glyph):
            rows[i] += row
        # Add gap column(s)
        for i in range(height):
            rows[i] += " " * gap

    output = "\n".join(rows)
    return colorize(output, color)
```

### ANSI Colorization

```python
RAINBOW_CYCLE = ["red", "yellow", "green", "cyan", "blue", "magenta"]

def colorize(text: str, color: str, rainbow_index: int = 0) -> str:
    """Wrap text in ANSI escape codes."""
    if color == "rainbow":
        # Cycle per character — index tracks position across calls
        ...
    else:
        return f"\033[1m{ANSI_CODES[color]}{text}\033[0m"
```

### FIGlet Parser

```python
def parse_flf(path: Path) -> dict[str, list[str]]:
    """Parse a FIGlet .flf file into glyph dict."""
    # Read header → hardblank char, height, end-marker
    # For each ASCII char 32–126: read height lines, strip end-marker
    # Return dict[char → list[str]]
```

### TTF Rasterizer (Pillow-gated)

```python
def rasterize_ttf(font_path: Path, text: str, target_height: int = 7) -> list[str]:
    """Rasterize a character using Pillow at target_height rows."""
    _require_pil()
    from PIL import Image, ImageDraw, ImageFont
    # Render char to bitmap → crop → resize to target_height rows
    # Map pixel brightness → density chars: █ ▓ ▒ ░ (space)
    # Return list[str] — one string per row
```

---

## Testing

### Test Modules

| File | What it covers |
|------|---------------|
| `tests/test_figlet.py` | FIGlet parser, rendering, all 6 bundled fonts |
| `tests/test_fill.py` | Glyph mask, SDF distance field, density fill |
| `tests/test_ttf.py` | TTF discovery, rasterization, height consistency (PIL-gated) |

### Key Patterns

```python
# PIL-gated test — skip cleanly if Pillow not installed
def test_rasterize_ttf_with_real_font():
    pytest.importorskip("PIL")
    from justdoit.fonts.ttf import rasterize_ttf
    # ... test body

# Always-run test
def test_figlet_font_renders():
    from justdoit.fonts.figlet import render_figlet
    result = render_figlet("HI", font="big")
    assert isinstance(result, str)
    assert len(result.strip()) > 0

# Consistent height check — critical font constraint
def test_parse_flf_consistent_height():
    glyphs = parse_flf(FIGLET_FONTS_DIR / "big.flf")
    heights = {char: len(rows) for char, rows in glyphs.items()}
    assert len(set(heights.values())) == 1, f"Height mismatch: {heights}"
```

---

## Project Structure

```
JustDoIt/
├── .github/
│   ├── copilot-instructions.md    # This file — system overview and patterns
│   └── python-instructions.md    # Python coding standards, module structure, conventions
├── docs/
│   ├── VISION.md                  # Project direction and goals
│   ├── REFACTOR.md                # Refactor notes
│   └── research/
│       ├── TECHNIQUES.md          # Font/effect technique research log
│       ├── RESEARCH_LOG.md        # Session-by-session research notes
│       ├── DAILY_AGENT_PROMPT.md  # Claude Code daily prompt
│       └── output/                # Research output artifacts (.txt renders)
├── justdoit/                      # Main package
│   ├── cli.py
│   ├── core/
│   ├── fonts/
│   ├── effects/
│   └── output/
├── tests/
│   ├── test_figlet.py
│   ├── test_fill.py
│   └── test_ttf.py
├── skills/
│   └── ascii_art_generator/       # OpenClaw skill wrapper
│       ├── SKILL.md
│       ├── README.md
│       └── main.py
├── justdoit.py                    # Legacy single-file entry (backwards compat)
├── pyproject.toml                 # uv/hatchling build config
├── uv.lock                        # Locked dependencies
├── CLAUDE.md                      # Claude Code guidance
└── README.md
```

---

## Adding New Fonts

### New Builtin Font

1. Create `justdoit/fonts/builtin/myfont.py` with `MYFONT: dict[str, list[str]]`
2. All glyphs must have identical row counts — validate before committing
3. Register in `justdoit/fonts/__init__.py`
4. Add tests confirming consistent glyph height

### New FIGlet Font

1. Drop `.flf` file into `justdoit/fonts/figlet_fonts/`
2. Register name in `justdoit/fonts/__init__.py` font registry
3. No parser changes needed — `figlet.py` handles it generically

---

## Non-ASCII Characters & Encoding

- Use UTF-8 throughout
- Unicode block characters (`█`, `▓`, `▒`, `░`) are intentional in font data — they're the output, not decoration
- ANSI escape codes are the colorization mechanism — do not strip them from output strings
- All source files: UTF-8, no BOM required

---

## Copilot Behavior Guidelines

When writing code for this project:

- **Never introduce required dependencies.** Core must stay pure stdlib.
- **Always guard Pillow imports** with `try/except ImportError` or `_require_pil()`.
- **Never break glyph height consistency** when adding or modifying fonts.
- **Follow module structure standards** from `python-instructions.md` — headers, `_MODULE_NAME`, separator lines, ReST docstrings.
- **PIL-gated tests use `pytest.importorskip("PIL")`** — never `import PIL` at module level in tests.
- **Use `uv run pytest`** for test commands, not bare `pytest`.
- **No `print()` in library code** — use `_LOGGER` with appropriate level.
- **Prefer direct object manipulation** over selection-based patterns (no DCC context here, but the principle carries: prefer explicit over implicit).

---

## Commit Message Conventions

- `feat:` new font, effect, or CLI flag
- `fix:` bug fix
- `refactor:` structural improvement
- `test:` test additions or fixes
- `docs:` documentation updates
- `chore:` build, tooling, deps

---

## Current Status

**Complete:**
- Core pipeline: `render()`, `colorize()`, gap support
- Builtin fonts: `block` (7-row), `slim` (3-row)
- FIGlet support: parser + 6 bundled fonts
- TTF rasterization via Pillow (density chars, configurable height)
- Effects: ANSI color, rainbow, density fill, SDF outline
- Tests: 20 passing (figlet × 6, fill × 7, ttf × 7)
- `pyproject.toml` + `uv.lock` — dev env via `uv sync --dev`

**In Research / Upcoming:**
- See `docs/research/TECHNIQUES.md` for technique backlog
- Additional effects and font rendering improvements
- Potential packaging for PyPI
