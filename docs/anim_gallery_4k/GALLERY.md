# 4K Animation Gallery

> True 3840×2160 animated PNG renders — 480×135 char grid, 8×16px cells.
> Text fills the full canvas width (font_scale=4.0).
> Generate: `uv run python scripts/generate_4k_anim.py --effect <name>`

---

## Julia Set (rotating c)

<img src="fractal-julia.apng" width="100%" style="max-width:100%;display:block">

*72 frames · 9.4MB · 12fps · Julia set c parameter orbits the complex plane — fractal morphs each frame*

---

## Plasma Wave

<img src="plasma.apng" width="100%" style="max-width:100%;display:block">

*60 frames · 14MB · 12fps · Phase sweeps continuously through the spectral palette*

---

## Turing Pattern

<img src="turing.apng" width="100%" style="max-width:100%;display:block">

*48 frames · 13.9MB · 12fps · FHN reaction-diffusion field with rotating palette phase*

---

## Flame

<img src="flame.apng" width="100%" style="max-width:100%;display:block">

*48 frames · 11.3MB · 8fps · Analytical heat gradient — hot white/yellow base, cool red top, per-column flicker*

---

## Voronoi Stained Glass

<img src="voronoi.apng" width="100%" style="max-width:100%;display:block">

*12 frames · 20MB · 12fps · Fixed Voronoi cells, spectral palette phase sweeps across*

---

## Strange Attractor

<img src="attractor.apng" width="100%" style="max-width:100%;display:block">

*36 frames · 19.8MB · 12fps · Lorenz → Rössler trajectory with escape-time coloring*

---

## Adding New Effects

```python
def effect_myname(n_frames: int = 60) -> list:
    base_grid = _build_base_grid()      # 480x135, font_scale=4.0
    mask = [[1.0 if ch != " " else 0.0 for ch, _ in row] for row in base_grid]
    frames = []
    for i in range(n_frames):
        colored_grid = [...]
        frames.append(_grid_to_png_bytes(colored_grid))
    return frames

EFFECTS["myname"] = (effect_myname, "Description", 60)
```

`uv run python scripts/generate_4k_anim.py --effect myname`
