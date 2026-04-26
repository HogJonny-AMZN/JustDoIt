# 4K Animation Gallery

> True 3840×2160 animated PNG renders — 480×135 char grid, 8×16px cells @ 12fps.
> Download and view at 100% on a 4K display for full fidelity.
> Generate: `uv run python scripts/generate_4k_anim.py --effect <name>`

| Effect | Frames | Size | Description |
|--------|--------|------|-------------|
| [fractal-julia.apng](fractal-julia.apng) | 72 | 4.5MB | Julia set — c rotates around complex plane, fractal morphs each frame |
| [plasma.apng](plasma.apng) | 60 | 11MB | Plasma wave — phase sweeps continuously, spectral palette |
| [turing.apng](turing.apng) | 48 | 9MB | Turing FHN pattern — palette phase rotates over fixed reaction-diffusion field |
| [flame.apng](flame.apng) | 60 | 5.7MB | Flame simulation — seed + preset cycles (hot/default/cool/embers) |
| [voronoi.apng](voronoi.apng) | 48 | 17.8MB | Voronoi stained glass — palette phase + seed switching |
| [attractor.apng](attractor.apng) | 60 | 7MB | Strange attractor — Lorenz→Rössler trajectory, escape-time coloring |

## Adding New Effects

```python
def effect_myname(n_frames: int = 60) -> list:
    base_grid = _build_base_grid()       # 480x135 G09 grid
    mask = [[1.0 if ch != " " else 0.0 for ch, _ in row] for row in base_grid]
    frames = []
    for i in range(n_frames):
        # compute float_grid per frame...
        colored_grid = [...]
        frames.append(_grid_to_png_bytes(colored_grid))
    return frames

EFFECTS["myname"] = (effect_myname, "Description", 60)
```

`uv run python scripts/generate_4k_anim.py --effect myname`
