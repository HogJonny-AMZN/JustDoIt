# Skill: add-fill-effect

You are adding a new fill effect to JustDoIt. Follow every step exactly.

## Step 1 — Understand the technique

Before writing code, state:
- What the fill does visually
- What algorithm drives it
- Which existing fill is most similar (use it as a code reference)
- Which module it belongs in (`fill.py` for simple fills, `generative.py` for simulation-based)

## Step 2 — Implement the fill function

Read `justdoit/effects/CLAUDE.md` first. The fill contract is non-negotiable:

```python
def my_fill(mask: list[list[float]], **kwargs) -> list[str]:
    """One-line description.

    :param mask: 2D list of floats from glyph_to_mask(). 1.0=ink, 0.0=empty.
    :param ...: any additional params with defaults
    :returns: List of strings — one per row, same shape as input mask.
    """
```

Rules:
- Pure Python only — no numpy, no Pillow
- `' '` for all exterior cells (mask < 0.5)
- Use `log1p` compression for simulation output → density mapping
- Standard density chars: `@#S%?*+;:,. ` (darkest → lightest)
- Module header with `_MODULE_NAME`, `__updated__`, `__version__`, `__author__`
- Separator lines `# -----...` before every top-level function

## Step 3 — Register the fill

In `justdoit/core/rasterizer.py`, add to `_FILL_FNS`:

```python
from justdoit.effects.<module> import my_fill

_FILL_FNS: dict = {
    ...
    "mykey": my_fill,
}
```

Pick a short, memorable key (e.g. `"fractal"`, `"wave"`, `"stipple"`).

## Step 4 — Write tests

Add to the appropriate test file (`tests/test_fill.py` or `tests/test_generative.py`):

```python
def test_my_fill_basic():
    mask = [[1.0, 0.5, 0.0], [0.8, 1.0, 0.0]]
    result = my_fill(mask)
    assert len(result) == 2
    assert len(result[0]) == 3
    assert result[0][2] == ' '  # exterior = space

def test_my_fill_via_render():
    from justdoit import render
    out = render("HI", fill="mykey")
    assert len(out) > 0
```

Run: `uv run pytest tests/ -q` — must pass before proceeding.

## Step 5 — Add to gallery

In `scripts/generate_gallery.py`, add an entry to the showcase list following the existing pattern. Use the same ID prefix as TECHNIQUES.md (e.g. `S-F05` for Fill technique 5).

## Step 6 — Update TECHNIQUES.md

In `docs/research/TECHNIQUES.md`, change the technique's status from `idea` → `done`.

## Step 7 — Update CLI help

In `justdoit/cli.py`, add the new fill key to the `--fill` choices help text.

## Step 8 — Commit

```
feat: add <TechniqueID> <Name> fill (<key> fill key)
```

Example: `feat: add F05 Fractal fill (fractal fill key)`
