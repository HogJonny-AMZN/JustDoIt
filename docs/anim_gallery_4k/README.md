# 4K Animation Gallery

> True 3840×2160 animated PNG renders — 480×135 char grid, 8×16px cells @ 12fps.
> Animations play inline. Download for full 4K fidelity.
> Generate: `uv run python scripts/generate_4k_anim.py --effect <name>`

---

## Julia Set (rotating c)

![fractal-julia](fractal-julia.apng)

*72 frames · 4.5MB · Julia set c parameter orbits the complex plane — fractal morphs each frame*

---

## Plasma Wave

![plasma](plasma.apng)

*60 frames · 11MB · Phase sweeps continuously through the spectral palette*

---

## Turing Pattern

![turing](turing.apng)

*48 frames · 9MB · FHN reaction-diffusion field with rotating palette phase*

---

## Flame Simulation

![flame](flame.apng)

*60 frames · 5.7MB · Seed + preset cycles through hot / default / cool / embers*

---

## Voronoi Stained Glass

![voronoi](voronoi.apng)

*48 frames · 17.8MB · Stained glass cells with palette phase shift and seed switching*

---

## Strange Attractor

![attractor](attractor.apng)

*60 frames · 7MB · Lorenz → Rössler trajectory with escape-time coloring*

---

## Adding New Effects

Edit `scripts/generate_4k_anim.py` — add an `effect_*` function and register it in `EFFECTS`, then run:

```bash
uv run python scripts/generate_4k_anim.py --effect myname
```
