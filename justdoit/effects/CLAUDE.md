# CLAUDE.md — justdoit/effects/

This is a **danger zone**. Read this before touching anything here.

## The Fill Contract

All fill functions share an identical signature and must return identical shapes:

```python
def my_fill(mask: list[list[float]], **kwargs) -> list[str]:
```

- **Input:** `mask` — 2D list of floats, shape `[rows][cols]`, values `0.0–1.0`
  - `1.0` = full ink (glyph interior)
  - `0.0` = empty (outside glyph)
  - Values between = antialiased edge pixels
- **Output:** list of strings, one per row, same `len(row)` as input
- **Pure function** — no side effects, no global state mutations
- **No imports** from `core/` allowed — effects must not depend upward

Breaking this contract corrupts every downstream renderer (SVG, PNG, terminal, HTML).

## Fill Registry

Fills are registered in `core/rasterizer.py` in `_FILL_FNS: dict`.

**To add a new fill:**
1. Implement in the appropriate module (`fill.py`, `generative.py`, `shape_fill.py`, or a new file)
2. Add to `_FILL_FNS` in `rasterizer.py`
3. Add a test in `tests/test_fill.py` or `tests/test_generative.py`
4. Add a gallery entry in `scripts/generate_gallery.py`
5. Update `TECHNIQUES.md` status from `idea` → `done`

## Module Map

| File | Fills | Notes |
|------|-------|-------|
| `fill.py` | `density`, `sdf` | Core fills, stable |
| `generative.py` | `noise`, `cells`, `truchet`, `rd`, `slime`, `attractor`, `lsystem` | Simulation/generative fills |
| `shape_fill.py` | `shape` | 4-neighbor connectivity contour fill (F11) |
| `recursive.py` | `recursion` | Typographic recursion (N01) — not a fill, applied differently |
| `color.py` | — | ANSI colorization; operates on rendered strings, not masks |
| `spatial.py` | — | Grid-level transforms (sine warp, perspective, isometric, shear) |
| `gradient.py` | — | Gradient color computation helpers |
| `isometric.py` | — | Isometric extrusion logic (S03) |

## Density Chars Convention

Standard density scale (darkest → lightest): `@#S%?*+;:,. `

The `density_fill()` function maps `1.0 → '@'`, `0.0 → ' '`. This scale is the baseline all other fills should feel consistent with.

## Generative Fills Pattern

All generative fills in `generative.py` follow this internal pattern:
1. Identify interior cells (`mask[r][c] > 0.5`)
2. Build a bounding box or grid over interior
3. Run the simulation/algorithm
4. Map simulation output → density chars using `log1p` compression for visual balance
5. Return strings, placing `' '` for exterior cells

The `log1p` compression step is intentional — raw linear maps look flat. Do not remove it.

## Known Constraints

- **No Pillow in core fills** — PIL is optional, gated behind `pytest.importorskip` in tests
- **No numpy** — pure Python only; keep it zero-dependency
- **Line length:** 120 chars max
- **All functions need type hints + ReST docstrings**
- Pillow-dependent fills should check availability at call time and raise `ImportError` with a helpful message
