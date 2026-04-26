# 4K Animation Gallery

> True 3840×2160 animated PNG renders — 480×135 char grid, 8×16px cells @ 12fps.
> Download and view at 100% on a 4K display for full fidelity.
> Generate new effects: `uv run python scripts/generate_4k_anim.py --list`

| Effect | Frames | Size | Description |
|--------|--------|------|-------------|
| [fractal-julia.apng](fractal-julia.apng) | 72 | 4.5MB | Julia set — c parameter rotates around complex plane, fractal morphs each frame |
| [plasma.apng](plasma.apng) | 60 | 11MB | Plasma wave — phase sweeps continuously, spectral color cycling |
| [turing.apng](turing.apng) | 48 | 9MB | Turing FHN pattern — palette phase rotates over fixed reaction-diffusion field |

## Adding New Effects

Edit `scripts/generate_4k_anim.py` and add a new entry to `EFFECTS`:

```python
def effect_myname(n_frames: int = 60) -> list:
    base_grid = _build_base_grid()       # 480x135 G09 grid
    mask = [[1.0 if ch != " " else 0.0  # binary ink mask
             for ch, _ in row] for row in base_grid]
    # ... compute float_grid per frame ...
    return [_grid_to_png_bytes(colored_grid) for colored_grid in all_frames]

EFFECTS["myname"] = (effect_myname, "Description", 60)
```

Then: `uv run python scripts/generate_4k_anim.py --effect myname`
