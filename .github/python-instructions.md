---
applyTo: python
---

# Python Coding Standards for JustDoIt

## Project Overview

**JustDoIt** is a zero-dependency Python 3 ASCII art CLI. It renders text using built-in bitmap fonts (block, slim), bundled FIGlet fonts, and optional TTF/OTF font rasterization via Pillow. Output is colorized ANSI terminal text.

**Current Status**: Core pipeline complete. Fonts: `block`, `slim`, 6 bundled FIGlet fonts, TTF rasterization (Pillow-gated). Effects: ANSI color, rainbow, density fill, SDF outline.

## Core Principles

- **PEP 8 Compliance**: Follow PEP 8 with line length extended to 120 characters
- **Type Safety**: Use type hints for all function arguments and return values
- **Readability First**: Prioritize clear, maintainable code over clever solutions
- **Minimal Changes**: Write the least code necessary to solve the problem
- **Zero Required Dependencies**: Core must stay pure Python 3 stdlib — no mandatory third-party imports
- **Graceful Degradation**: Optional features (Pillow, figlet) must skip cleanly if unavailable

## Project Architecture

### Package Structure

```
justdoit/
├── __init__.py            # Public API
├── cli.py                 # argparse entry point
├── core/
│   ├── __init__.py        # Core exports
│   ├── glyph.py           # Glyph data structures
│   ├── rasterizer.py      # Glyph → ASCII raster pipeline
│   └── pipeline.py        # render() orchestration
├── fonts/
│   ├── __init__.py        # Font registry
│   ├── builtin/
│   │   ├── block.py       # 7-row Unicode block font
│   │   └── slim.py        # 3-row ASCII line-drawing font
│   ├── figlet.py          # FIGlet (.flf) parser and renderer
│   ├── figlet_fonts/      # Bundled .flf files
│   └── ttf.py             # TTF/OTF rasterizer (requires Pillow)
├── effects/
│   ├── __init__.py        # Effect exports
│   ├── color.py           # ANSI colorization, rainbow mode
│   └── fill.py            # Density fill, SDF effects
└── output/
    └── terminal.py        # Terminal output helpers
```

### Rendering Pipeline

1. `cli.py` → parses args, selects font/color/effect
2. `pipeline.render()` → uppercases input, maps chars to glyphs, concatenates rows with gap spacer
3. `effects/color.py` → wraps rows in ANSI escape codes; rainbow cycles per-char
4. `output/terminal.py` → prints to stdout

**Hard constraint:** All glyphs in a font must have the same height (row count). The pipeline zips rows across characters — mismatched heights corrupt output.

### Optional Dependency Pattern

Features gated on Pillow must check availability at call time and raise `ImportError` with a helpful message:

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

Tests for PIL-gated features must skip gracefully when Pillow is absent — never hard-fail.

### Module Structure Standards

**Every Python module must include this header:**

```python
"""
Package: justdoit.subpackage.module
Brief one-line description.

Detailed description of module purpose and functionality.
"""

# Standard library imports
import logging as _logging
from pathlib import Path
from typing import Any

# External imports (optional — guard with try/except if optional)
# from PIL import Image

# Project imports (absolute paths only)
from justdoit.core.glyph import Glyph

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.subpackage.module"  # Must match Package docstring
__updated__ = "YYYY-MM-DD HH:MM:SS"
__version__ = "X.Y.Z"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)  # Use _MODULE_NAME, NOT __name__
```

### Logging

- Import logging with alias: `import logging as _logging`
- Define module logger: `_LOGGER = _logging.getLogger(_MODULE_NAME)`
- Two-part error messages: human-readable context first, then technical details
- Configure logging in entry points (`cli.py`), not in library modules
- Use debug level for execution flow tracking

## Import Organization

Follow strict import hierarchy:

```python
# 1. Standard library (alphabetical)
import logging as _logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 2. Third-party packages (alphabetical, guarded if optional)
try:
    from PIL import Image, ImageDraw, ImageFont
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

# 3. Local imports (alphabetical, grouped by subpackage)
from justdoit.core.glyph import Glyph
from justdoit.effects.color import colorize
```

**Import Rules:**

- Never use wildcard imports (`from x import *`)
- One import per line for readability
- Use absolute imports: `from justdoit.core.glyph import Glyph`
- Guard optional third-party imports with `try/except ImportError`

## Type Hints

All functions must have complete type hints:

```python
# Simple types
def render(text: str, font: str = "block", color: str = "white", gap: int = 1) -> str:
    ...

# Optional parameters
def colorize(text: str, color: str, rainbow_index: int = 0) -> str:
    ...

# Complex return types
def parse_flf(path: Path) -> Dict[str, List[str]]:
    ...

# No return value
def print_output(text: str) -> None:
    ...

# Optional values
def find_font(name: str) -> Optional[Path]:
    ...
```

## Font Conventions

### Builtin Fonts (block, slim)

- Each font is a `dict[str, list[str]]` mapping character → list of row strings
- All glyphs must have identical row counts (height) — enforced at render time
- Supported charset: A–Z, 0–9, common punctuation, space
- Unknown characters fall back to the space glyph silently

### FIGlet Fonts

- Parsed from `.flf` files in `justdoit/fonts/figlet_fonts/`
- Parser produces same `dict[str, list[str]]` structure as builtin fonts
- Bundled fonts: `banner`, `big`, `block`, `bubble`, `digital`, `slant`
- Adding a font: drop the `.flf` into `figlet_fonts/` and register in `fonts/__init__.py`

### TTF/OTF Fonts (Pillow-gated)

- Rasterizes system fonts via Pillow at a configurable target height (default: 7 rows)
- Maps pixel brightness → density characters (`█`, `▓`, `▒`, `░`, ` `)
- Must call `_require_pil()` before any PIL import
- System font discovery via `fc-list` (Linux) or `find` fallback

## Error Handling

- Catch specific exceptions, not generic `except:`
- Provide context in error messages
- Validate inputs early in functions

```python
# Good: specific + context
def load_figlet_font(name: str) -> Dict[str, List[str]]:
    font_path = FIGLET_FONTS_DIR / f"{name}.flf"
    if not font_path.exists():
        raise FileNotFoundError(f"FIGlet font not found: {name!r} (looked in {FIGLET_FONTS_DIR})")
    ...

# Good: early validation
def render(text: str, font: str = "block", gap: int = 1) -> str:
    if gap < 0:
        raise ValueError(f"gap must be >= 0, got {gap}")
    if not text:
        return ""
    ...
```

## Path Handling

- Use `pathlib.Path` for all path manipulation, not string operations
- Use `Path(__file__).parent` for paths relative to the module

```python
from pathlib import Path

FIGLET_FONTS_DIR = Path(__file__).parent / "figlet_fonts"

def load_font_file(name: str) -> Path:
    path = FIGLET_FONTS_DIR / f"{name}.flf"
    if not path.exists():
        raise FileNotFoundError(f"Font file not found: {path}")
    return path
```

## Testing

### Test Structure

- All tests in `/tests/` with `test_*.py` naming
- Use `pytest` (installed via `uv sync --dev`)
- Run: `uv run pytest` or `.venv/bin/pytest`
- PIL-gated tests: use `pytest.importorskip("PIL")` — never hard-fail

```python
# PIL-gated test — skip gracefully
def test_rasterize_ttf_with_real_font():
    PIL = pytest.importorskip("PIL")
    from justdoit.fonts.ttf import rasterize_ttf
    # ... test body

# Always-run test
def test_figlet_font_renders():
    from justdoit.fonts.figlet import render_figlet
    result = render_figlet("HI", font="big")
    assert isinstance(result, str)
    assert len(result) > 0
```

### Test Modules

- `tests/test_figlet.py` — FIGlet parser, rendering, all bundled fonts
- `tests/test_fill.py` — glyph mask, SDF, density fill
- `tests/test_ttf.py` — TTF discovery, rasterization (PIL-gated)

### Dev Environment

```bash
# Setup
uv sync --dev             # Creates .venv, installs pytest + Pillow

# Run tests
uv run pytest             # All tests
uv run pytest tests/test_figlet.py -v  # Single module
uv run pytest -q          # Quiet mode
```

## Docstrings and Documentation

Use compact reStructuredText (ReST) format:

```python
def render(text: str, font: str = "block", color: str = "white", gap: int = 1) -> str:
    """Render text as ASCII art.

    :param text: Input string (case-insensitive; uppercased internally)
    :param font: Font name — "block", "slim", or any bundled FIGlet font
    :param color: ANSI color name or "rainbow"
    :param gap: Column gap between characters (default: 1)
    :returns: Multi-line ANSI-colorized ASCII art string
    :raises ValueError: If gap is negative or font is unknown
    """
```

## Module Structure

**CRITICAL:** All functions, classes, and executable code must come AFTER the module metadata section.

**Function/Class Separation:** Every top-level function and class definition must be preceded by a separator line:

```python
# -------------------------------------------------------------------------
```

Full module template:

```python
"""
Package: justdoit.fonts.builtin.block
7-row Unicode block character font.

Provides the BLOCK_FONT glyph dictionary for use with the core render pipeline.
"""

import logging as _logging
from typing import Dict, List

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.fonts.builtin.block"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

BLOCK_FONT: Dict[str, List[str]] = {
    "A": [
        " ██ ",
        "█  █",
        "████",
        "█  █",
        "█  █",
        "    ",
        "    ",
    ],
    # ...
}


# -------------------------------------------------------------------------
def get_font() -> Dict[str, List[str]]:
    """Return the BLOCK font glyph dictionary.

    :returns: Mapping of character to list of row strings
    """
    return BLOCK_FONT
```

## Code Review Checklist

Before committing code, verify:

- [ ] All functions have type hints
- [ ] All public functions have docstrings (ReST format)
- [ ] Logging uses appropriate levels (debug/info/warning/error)
- [ ] Exceptions are specific, not bare `except:`
- [ ] Paths use `pathlib.Path`, not string operations
- [ ] Optional Pillow imports are guarded with `try/except ImportError`
- [ ] PIL-gated tests use `pytest.importorskip("PIL")`
- [ ] All glyphs in a new font have consistent row counts
- [ ] No mutable default arguments
- [ ] Imports are organized (stdlib → third-party → local)
- [ ] Tests pass (`uv run pytest`)

## Anti-Patterns to Avoid

```python
# WRONG: Mutable default argument
def render(text: str, rows: List[str] = []):  # BUG!
    rows.append(text)

# CORRECT: Use None
def render(text: str, rows: Optional[List[str]] = None) -> List[str]:
    if rows is None:
        rows = []
    rows.append(text)
    return rows

# WRONG: Hard import of optional dependency at module level
from PIL import Image  # Crashes if Pillow not installed

# CORRECT: Guard it
try:
    from PIL import Image
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

# WRONG: Bare except
try:
    result = render(text)
except:
    pass

# CORRECT: Specific exception
try:
    result = render(text)
except ValueError as e:
    _LOGGER.error(f"Render failed for {text!r}: {e}")
    raise

# WRONG: String path operations
font_path = "justdoit/fonts/figlet_fonts/" + name + ".flf"

# CORRECT: pathlib
font_path = Path(__file__).parent / "figlet_fonts" / f"{name}.flf"
```

## Goals Summary

When writing code for JustDoIt:

1. **Zero required deps** — core stays pure stdlib; optional features degrade gracefully
2. **Follow project conventions** — match existing module header and separator patterns
3. **Write idiomatic Python** — clean, Pythonic solutions
4. **Prioritize readability** — code is read more than written
5. **Minimize changes** — don't refactor unnecessarily
6. **Write tests** — all new features need tests; PIL-gated tests skip cleanly
7. **Document thoroughly** — type hints, ReST docstrings, examples
8. **Handle errors gracefully** — specific exceptions with context
9. **Log appropriately** — debug for flow, error for failures
10. **Keep fonts consistent** — glyph row counts must match within a font
