# JustDoIt 🔡

**The best font rendering codebase on earth.**  
Terminal-first. Substrate-agnostic. Pure Python.

ASCII/ANSI text art with a serious rendering pipeline — fills, spatial effects, 3D extrusion, generative patterns, animation, and more. Starts in your terminal. Goes anywhere.

```
██████ ██  ██  █████ ██████     █████   ████      ██████ ██████
   ██  ██  ██ ██       ██       ██  ██ ██  ██       ██     ██
   ██  ██  ██ ██       ██       ██  ██ ██  ██       ██     ██
   ██  ██  ██  ████    ██       ██  ██ ██  ██       ██     ██
██ ██  ██  ██     ██   ██       ██  ██ ██  ██       ██     ██
 ████   ████  █████    ██       █████   ████      ██████   ██
```

---

## 📸 Galleries

| Gallery | Contents |
|---------|----------|
| [**Static Gallery →**](docs/gallery/README.md) | Fonts, fills, color effects, spatial & 3D — SVG snapshots of all rendering techniques |
| [**Animation Gallery →**](docs/anim_gallery/README.md) | APNG + asciinema `.cast` — animated effects (typewriter, glitch, transporter, particle fills) |

---

## Usage

```bash
uv run python justdoit.py "Your Text"
uv run python justdoit.py "FIRE" --color rainbow
uv run python justdoit.py "CO3DEX" --font block --color yellow
uv run python justdoit.py "ENERGIZE" --animate transporter --trek-era tng
```

## Options

| Flag | Short | Description |
|------|-------|-------------|
| `--font` | `-f` | Font: `block`, `slim`, FIGlet fonts, TTF |
| `--color` | `-c` | Color: `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`, `bold`, `rainbow`, gradients, palettes |
| `--fill` | | Fill mode: `density`, `noise`, `cells`, `sdf`, `shape`, `fractal`, `slime`, `attractor`, … |
| `--effect` | | Spatial effect: `sine-warp`, `perspective`, `isometric`, `shear`, … |
| `--animate` | | Animation: `typewriter`, `scanline`, `glitch`, `pulse`, `transporter`, … |
| `--trek-era` | | Trek era for transporter: `tos`, `tng`, `ds9`, `ent`, `kelvin` |
| `--gap` | `-g` | Gap between characters (default: 1) |
| `--fps` | | Animation framerate (default: per-effect; baseline 24) |
| `--export-apng` | | Export animation to APNG file |
| `--export-cast` | | Export animation to asciinema `.cast` file |
| `--list-fonts` | | List available fonts |
| `--list-colors` | | List available colors |

---

## What It Can Do

### Fonts
- **Builtin** — `block`, `slim` (hand-crafted, zero deps)
- **FIGlet** — `.flf` format, 400+ community fonts
- **TTF/OTF** — any system font via Pillow rasterization

### Fill Effects
Glyphs are 2D masks. Fill them with anything:
- Density-mapped ASCII (`@#%+-.`)
- Perlin/Simplex noise — never the same twice
- Cellular automata (Conway's Game of Life inside the letter)
- Reaction-diffusion (Gray-Scott — biological patterns)
- SDF-based (distance from edge → outline, glow)
- Slime mold, strange attractors, L-systems, Turing patterns
- Isometric extrusion — 3D block letters with shaded faces

### Color
- Flat, gradient (H/V/diagonal/radial), per-glyph palettes
- Named palettes: `fire`, `neon`, `ocean`, `rainbow`
- Full 256-color and true-color ANSI

### Spatial & 3D
- Sine warp, perspective tilt, shear
- Isometric extrusion with face shading
- Normal-mapped 3D font rendering *(in design)*

### Animation
- Typewriter, scanline reveal, glitch, pulse, dissolve
- **Star Trek transporter** — TOS/TNG/DS9/ENT/Kelvin era variants, half-block subpixel particles, optional synthesized audio
- 3D particle volume fill — particles converge into letter shape from a 3D scatter field *(in design)*

### Output
- Terminal (ANSI)
- SVG — vector, scalable
- PNG — via Pillow
- APNG — animated, GitHub-embeddable
- asciinema `.cast` — authentic terminal playback
- HTML *(planned)*

---

## Install

```bash
git clone <repo>
cd JustDoIt
uv sync          # installs optional deps (Pillow, numpy, sounddevice)
uv run python justdoit.py "hello"
```

Core is zero-dependency Python stdlib. Optional deps unlock fonts, export formats, and audio.

---

## Docs

- [VISION.md](docs/VISION.md) — where this is going
- [TECHNIQUES.md](docs/research/TECHNIQUES.md) — full technique registry
- [star_trek_effects.md](docs/star_trek_effects.md) — transporter design doc
- [animation_gallery.md](docs/animation_gallery.md) — animation pipeline design
- [sound_design.md](docs/sound_design.md) — audio engine design
- [decisions/](docs/decisions/) — architecture decision records

---

*"The line must be drawn here. This far, no further."*  
*— except for the renderer, which will go considerably further.*
