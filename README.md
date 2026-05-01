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
| [**Static Gallery →**](https://hogjonny-amzn.github.io/JustDoIt/gallery/) | Fonts, fills, color effects, spatial & 3D — SVG snapshots (14px / standard) |
| [**Wide Gallery →**](https://hogjonny-amzn.github.io/JustDoIt/gallery-wide/) | Same techniques at 28px — sharper on retina/HiDPI screens |
| [**4K Gallery →**](https://hogjonny-amzn.github.io/JustDoIt/gallery-4k/) | Full 4K renders at 72px — pixel-perfect for 3840×2160 displays |
| [**Font Gallery →**](https://hogjonny-amzn.github.io/JustDoIt/gallery-fonts/) | TTF comparison — 37+ fonts rendered as ASCII art, 20 new fonts added daily |
| [**Animation Gallery →**](https://hogjonny-amzn.github.io/JustDoIt/anim_gallery/) | APNG + asciinema `.cast` — animated effects (typewriter, glitch, neon, flame, plasma) |
| [**4K Animation Gallery →**](https://hogjonny-amzn.github.io/JustDoIt/anim_gallery_4k/index.html) | True 3840×2160 APNG renders — Julia fractal, plasma, flame, Turing, Voronoi, attractor |

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
| `--fill` | | Fill mode: `density`, `noise`, `cells`, `sdf`, `shape`, `fractal`, `slime`, `attractor`, `turing`, `plasma`, `flame`, `voronoi`, `wave`, … |
| `--animate` | | Animation: `typewriter`, `scanline`, `glitch`, `pulse`, `dissolve` |
| `--gap` | `-g` | Gap between characters (default: 1) |
| `--fps` | | Animation framerate (default: 12) |
| `--iso` | | Isometric 3D extrusion depth (e.g. `--iso 4`) |
| `--gradient` | | Linear gradient between two colors (e.g. `--gradient red cyan`) |
| `--warp` | | Sine wave warp amplitude (e.g. `--warp 3.0`) |
| `--save-svg` | | Save output as SVG |
| `--save-png` | | Save output as PNG (requires Pillow) |
| `--measure` | | Print render dimensions + display fit table for all known displays, then exit |
| `--target` | | Display target spec (e.g. `3840x2160` or `3840x2160@2.0x`) — auto-sizes SVG with `--save-svg` |
| `--svg-font-size` | | SVG font size in pixels (default: 14; overrides `--target`) |
| `--fit` | | Truncate text to fit within N terminal columns |
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
- [ATTRIBUTE_MODEL.md](docs/research/ATTRIBUTE_MODEL.md) — axis decomposition + cross-breed catalog
- [SIZE_SCALE_RESOLUTION.md](docs/SIZE_SCALE_RESOLUTION.md) — size/scale feature design
- [animation_gallery.md](docs/animation_gallery.md) — animation pipeline design
- [sound_design.md](docs/sound_design.md) — audio engine design
- [decisions/](docs/decisions/) — architecture decision records

---

*"The line must be drawn here. This far, no further."*  
*— except for the renderer, which will go considerably further.*
