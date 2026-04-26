# 4K Animation Gallery

> True 3840×2160 animated PNG renders — 480×135 char grid, 8×16px cells @ 12fps.
> Text fills the full canvas width (font_scale=4.0 — ~479×92 cells of ink).
> Download for full 4K fidelity; plays inline in browser.
> Generate: `uv run python scripts/generate_4k_anim.py --effect <name>`

---

## Julia Set (rotating c)

![fractal-julia](fractal-julia.apng)

*72 frames · 9.4MB · Julia set c parameter orbits the complex plane — fractal morphs each frame*

---

## Plasma Wave

![plasma](plasma.apng)

*60 frames · 14MB · Phase sweeps continuously through the spectral palette*

---

## Turing Pattern

![turing](turing.apng)

*48 frames · 13.9MB · FHN reaction-diffusion field with rotating palette phase*

---

## Flame (plasma-driven fire palette)

![flame](flame.apng)

*36 frames · 7.9MB · Plasma wave with fire palette — hot/cool band cycling*

---

## Voronoi Stained Glass

![voronoi](voronoi.apng)

*12 frames · 20MB · Fixed Voronoi cells, spectral palette phase sweeps across*

---

## Strange Attractor

![attractor](attractor.apng)

*36 frames · 19.8MB · Lorenz → Rössler trajectory with escape-time coloring*

---

## Adding New Effects

```python
def effect_myname(n_frames: int = 60) -> list:
    base_grid = _build_base_grid()      # 480x135, font_scale=4.0
    mask = [[1.0 if ch != " " else 0.0 for ch, _ in row] for row in base_grid]
    frames = []
    for i in range(n_frames):
        colored_grid = [...]            # compute per-frame
        frames.append(_grid_to_png_bytes(colored_grid))
    return frames

EFFECTS["myname"] = (effect_myname, "Description", 60)
```

`uv run python scripts/generate_4k_anim.py --effect myname`
