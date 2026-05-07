# Contributing to JustDoIt

Thank you for considering contributing to JustDoIt! This document outlines the process and guidelines for contributing.

---

## Quick Start

```bash
# Clone the repo
git clone https://github.com/HogJonny-AMZN/JustDoIt.git
cd JustDoIt

# Set up dev environment (uv required)
uv sync --dev

# Run tests
uv run pytest tests/

# Run specific test module
uv run pytest tests/test_fill.py -v

# Run tests excluding slow tests
uv run pytest -m "not slow"
```

---

## Development Environment

### Required Tools
- **Python 3.11+**
- **uv** — fast Python package installer ([install](https://github.com/astral-sh/uv))

### Optional Dependencies
- **Pillow** — TTF/OTF font support, image export (PNG, APNG)
- **numpy** — fast image processing (optional fallback), sound synthesis
- **sounddevice** — audio playback

All optional dependencies are installed automatically with `uv sync --dev`.

---

## Code Standards

### Python Style
Follow patterns from [`.github/python-instructions.md`](.github/python-instructions.md):

- **Line length**: 120 characters (PEP 8 extended)
- **Type hints**: Required for all public functions
- **Docstrings**: ReST format for all public functions and classes
- **Imports**: stdlib → third-party (guarded) → local absolute
- **Logging**: Use `_LOGGER` with appropriate level (debug/info/warning/error)
- **Module header**: Required format with `_MODULE_NAME`, `__updated__`, `__version__`

### Module Structure
```python
"""
Package: justdoit.subpackage.module
Brief one-line description.
"""

import logging as _logging

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.subpackage.module"
__updated__ = "YYYY-MM-DD HH:MM:SS"
__version__ = "X.Y.Z"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

# -------------------------------------------------------------------------
def my_function() -> None:
    """Function docstring in ReST format."""
```

### Linting and Formatting
We use **Ruff** for linting and formatting:

```bash
# Check code quality
uv run ruff check justdoit/

# Auto-fix issues
uv run ruff check justdoit/ --fix

# Check specific issues
uv run ruff check justdoit/ --select I  # import sorting
```

Configuration in [`pyproject.toml`](pyproject.toml):
- Line length: 120
- Ignored rules: E221 (aligned assignments), F821 (forward string annotations)
- Import sorting enabled (isort rules)

---

## Dependency Management

### Core Principle: Zero Required Dependencies
The core rendering pipeline (`justdoit/core/`, `justdoit/fonts/builtin/`, `justdoit/effects/fill.py`) must remain **pure Python 3 stdlib** with no external dependencies.

### Optional Dependency Pattern
Gate optional features behind try/except imports:

```python
def _require_pil() -> None:
    """Raise ImportError with install hint if Pillow is unavailable."""
    try:
        import PIL  # noqa: F401
    except ImportError:
        raise ImportError(
            "TTF font support requires Pillow. Install with: pip install Pillow"
        )

def render_ttf(font_path: str) -> list:
    """Render using TTF font (requires Pillow)."""
    _require_pil()
    from PIL import Image, ImageDraw, ImageFont
    # ... implementation
```

### Adding Dependencies
- **Required dependencies**: Need strong justification; discuss in issue first
- **Optional dependencies**: Add to `[project.optional-dependencies]` in `pyproject.toml`
- **Dev dependencies**: Add to `[dependency-groups] dev`

---

## Testing

### Running Tests
```bash
# All tests
uv run pytest tests/ -v

# Single test file
uv run pytest tests/test_fill.py -v

# Exclude slow tests (useful for quick validation)
uv run pytest -m "not slow"

# Run tests with coverage
uv run pytest tests/ --cov=justdoit --cov-report=html
```

### Test Requirements
- **All new features must have tests**
- **Bug fixes should include regression tests**
- PIL-gated tests: Use `pytest.importorskip("PIL")` — never hard-fail
- Mark slow tests (>1s) with `@pytest.mark.slow`

### Test Patterns
```python
def test_basic_feature():
    """Test basic functionality."""
    result = my_function("input")
    assert result == expected

@pytest.mark.slow
def test_performance_heavy():
    """Test that takes >1 second."""
    # ... expensive operation

def test_pil_feature():
    """Test requiring Pillow (skips cleanly if unavailable)."""
    pytest.importorskip("PIL")
    from justdoit.fonts.ttf import rasterize_ttf
    # ... test body
```

---

## Adding New Features

### New Fill Effect
See [`.claude/skills/add-fill-effect/SKILL.md`](.claude/skills/add-fill-effect/SKILL.md) for the complete workflow.

Quick checklist:
1. Implement in `justdoit/effects/` with proper module header
2. Register in `justdoit/effects/__init__.py`
3. Add CLI flag in `justdoit/cli.py`
4. Write tests in `tests/test_<effect>.py`
5. Document in `docs/research/TECHNIQUES.md`
6. Add gallery examples if visual

### New Font
See [`.claude/skills/add-font/SKILL.md`](.claude/skills/add-font/SKILL.md) for the complete workflow.

**Critical constraint**: All glyphs in a font must have identical row counts (height). Mismatched heights corrupt output silently.

Quick checklist:
1. Create font in `justdoit/fonts/builtin/<name>.py` or add `.flf` to `justdoit/fonts/figlet_fonts/`
2. Register in `justdoit/fonts/__init__.py`
3. Validate all glyphs have same height
4. Add tests confirming height consistency
5. Add to font gallery

### New Animation
1. Implement in `justdoit/animate/` following existing patterns
2. Register in `justdoit/animate/presets.py`
3. Add CLI support in `justdoit/cli.py`
4. Write tests in `tests/test_<animation>.py`
5. Generate `.cast` and `.apng` examples for gallery

---

## Commit Conventions

Use conventional commit prefixes:

- `feat:` — new feature (font, effect, CLI flag)
- `fix:` — bug fix
- `refactor:` — code restructuring without behavior change
- `test:` — test additions or fixes
- `docs:` — documentation updates
- `chore:` — build, tooling, dependencies

Examples:
```
feat: add plasma flame fill effect
fix: correct isometric depth calculation for hollow glyphs
refactor: extract SDF remapping to shared utility
test: add integration tests for CLI validation
docs: update TECHNIQUES.md with fractal fills
chore: add ruff to dev dependencies
```

---

## Documentation

### Required Documentation
- **Docstrings**: All public functions/classes (ReST format)
- **TECHNIQUES.md**: New fill effects, generative algorithms
- **CHANGELOG.md**: User-facing changes
- **Architecture decisions**: For significant structural changes, add to `docs/decisions/`

### Documentation Style
- Clear, concise explanations
- Code examples where helpful
- Link to related techniques or docs
- Use proper markdown formatting (linkify file references)

---

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feat/plasma-fill
   ```

2. **Make your changes**
   - Follow code standards
   - Add tests
   - Update documentation

3. **Validate your changes**
   ```bash
   uv run ruff check justdoit/ --fix    # lint
   uv run pytest tests/ -v               # all tests pass
   uv run pytest -m "not slow" -q        # quick validation
   ```

4. **Commit with conventional prefix**
   ```bash
   git commit -m "feat: add plasma fill effect"
   ```

5. **Push and create PR**
   ```bash
   git push origin feat/plasma-fill
   ```

6. **PR Description**
   - What: Brief summary of changes
   - Why: Motivation or problem solved
   - Testing: How you validated it works
   - Screenshots/examples: For visual features

---

## Questions or Issues?

- **Bug reports**: Open an issue with minimal reproduction case
- **Feature requests**: Open an issue with use case and rationale
- **Questions**: Check existing docs first, then open a discussion

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License (same as the project).

---

*"Make it so."*
