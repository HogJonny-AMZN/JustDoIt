"""
Package: scripts.generate_anim_gallery
Generate animation gallery from preset animations.

Run with:
    uv run python scripts/generate_anim_gallery.py

Saves .cast and .apng files to docs/anim_gallery/ and regenerates
docs/anim_gallery/README.md. Each APNG embeds inline on GitHub.
"""

import logging as _logging
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "scripts.generate_anim_gallery"
__updated__ = "2026-03-30 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

GALLERY_DIR = Path(__file__).parent.parent / "docs" / "anim_gallery"


# -------------------------------------------------------------------------
def _neon_multi_frames(text_plain: str) -> list[str]:
    """Build a multi-color neon glitch where each word gets its own tube color.

    Renders each word separately with its assigned color, then composites
    the rows side-by-side and applies per-row flicker independently.

    :param text_plain: Raw text (e.g. 'JUST DO IT').
    :returns: List of frame strings.
    """
    import re
    import random
    from justdoit.core.rasterizer import render
    from justdoit.animate.presets import neon_glitch, _NEON_COLORS, _ANSI_RE, _RESET  # noqa: F401

    words = text_plain.upper().split()
    colors = ["cyan", "magenta", "yellow"]
    word_colors = [colors[i % len(colors)] for i in range(len(words))]

    # Render each word separately
    word_renders = [render(w, font="block") for w in words]
    n_rows = max(len(r.split("\n")) for r in word_renders)

    # Pad all renders to same row count
    padded = []
    for r in word_renders:
        lines = r.split("\n")
        while len(lines) < n_rows:
            lines.append("")
        padded.append(lines)

    # Build composite plain lines (words joined with gap)
    gap = "  "
    composite_lines = []
    for row_idx in range(n_rows):
        composite_lines.append(gap.join(p[row_idx] for p in padded))

    # Per-word column ranges for selective colorization
    rng = random.Random(7)
    n_frames = 36

    neon_map = _NEON_COLORS

    frames = []
    for _ in range(n_frames):
        frame_lines = []
        for row_idx, line in enumerate(composite_lines):
            if not line.strip():
                frame_lines.append(line)
                continue
            # Re-colorize each word segment independently
            plain = _ANSI_RE.sub("", line)
            # Split back by gap to colorize per-segment
            segments = plain.split(gap)
            colored_segs = []
            for seg_idx, seg in enumerate(segments):
                color_name = word_colors[seg_idx % len(word_colors)]
                neon = neon_map[color_name]
                roll = rng.random()
                if roll < 0.08:
                    state = "off"
                elif roll < 0.30:
                    state = "dim"
                elif roll < 0.42:
                    state = "fringe"
                    neon_code = rng.choice(neon["fringe"])
                    colored_segs.append(f"{neon_code}{seg}{_RESET}")
                    continue
                else:
                    state = "full"
                colored_segs.append(f"{neon[state]}{seg}{_RESET}")
            frame_lines.append(gap.join(colored_segs))
        frames.append("\n".join(frame_lines))
    return frames

_TEXT = "JUST DO IT"


# -------------------------------------------------------------------------
def _dissolve_in_out(text: str) -> list[str]:
    """Build a looping dissolve-in + hold + dissolve-out frame sequence.

    :param text: Fully rendered multi-line string.
    :returns: Combined frame list suitable for looping APNG.
    """
    from justdoit.animate.presets import dissolve

    dissolve_out = list(dissolve(text, seed=42))   # full → blank
    dissolve_in = list(reversed(dissolve_out))[1:] # blank → full (drop dup)
    hold = [dissolve_out[0]] * 6                   # hold full frame ~0.5s @ 12fps
    # in → hold → out; skip duplicate boundary frames
    return dissolve_in + hold + dissolve_out[1:]


# -------------------------------------------------------------------------
def _build_showcase() -> list[dict]:
    """Build the declarative SHOWCASE list.

    Each entry defines: id, name, label, fps, loop, and a frames factory.

    :returns: List of showcase entry dicts.
    """
    from justdoit.animate.presets import typewriter, scanline, glitch, pulse, dissolve, neon_glitch, neon_word_glitch, neon_tube_glitch, neon_sign_startup, density_dissolve, plasma_wave, flame_flicker, voronoi_stained_glass, plasma_lava_lamp, flame_gradient_color, flame_bloom, bloom_pulse, plasma_bloom, iso_depth_breathe, turing_bio, turing_morphogenesis, plasma_flame, plasma_warp, fractal_color_cycle, turing_warp, flame_iso_bloom, noise_warp, plasma_noise_warp, living_fill, living_color
    from justdoit.core.rasterizer import render

    text = render(_TEXT, font="block")
    text_plain = _TEXT  # plain text for presets that re-render each frame (e.g. plasma_wave)

    return [
        {
            "id": "A01",
            "name": "typewriter",
            "label": "typewriter",
            "frames": lambda: list(typewriter(text)),
            "fps": 12.0,
            "loop": False,
        },
        {
            "id": "A02",
            "name": "scanline",
            "label": "scanline",
            "frames": lambda: list(scanline(text)),
            "fps": 4.0,
            "loop": False,
        },
        {
            "id": "A03",
            "name": "glitch",
            "label": "glitch",
            "frames": lambda: list(glitch(text)),
            "fps": 24.0,
            "loop": True,
        },
        {
            "id": "A03s",
            "name": "neon-sign",
            "label": "neon-sign-cyan",
            "frames": lambda: list(neon_sign_startup(_TEXT, color="cyan", faulty_word_idx=1, n_flickers=3, hold_frames=12, seed=7)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A03s2",
            "name": "neon-sign",
            "label": "neon-sign-magenta",
            "frames": lambda: list(neon_sign_startup(_TEXT, color="magenta", faulty_word_idx=2, n_flickers=4, hold_frames=12, seed=13)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A03w",
            "name": "neon-word",
            "label": "neon-word-cyan",
            "frames": lambda: list(neon_word_glitch(_TEXT, color="cyan", n_frames=36, seed=1)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A03w2",
            "name": "neon-word",
            "label": "neon-word-magenta",
            "frames": lambda: list(neon_word_glitch(_TEXT, color="magenta", n_frames=36, seed=2)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A03w3",
            "name": "neon-word",
            "label": "neon-word-multi",
            "frames": lambda: list(neon_word_glitch(_TEXT, colors=["cyan", "magenta", "yellow"], n_frames=36, seed=3)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A03sf",
            "name": "neon-sign",
            "label": "neon-sign-flicker-cyan",
            "frames": lambda: list(neon_sign_startup(_TEXT, color="cyan",
                faulty_word_idx=1, n_flickers=3, hold_frames=20,
                pulse=True, flicker_hold=True, seed=7)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A03sf2",
            "name": "neon-sign",
            "label": "neon-sign-flicker-magenta",
            "frames": lambda: list(neon_sign_startup(_TEXT, color="magenta",
                faulty_word_idx=2, n_flickers=4, hold_frames=20,
                pulse=True, flicker_hold=True, seed=13)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A03t",
            "name": "neon-tube",
            "label": "neon-tube-cyan",
            "frames": lambda: list(neon_tube_glitch(text, color="cyan", n_frames=36, seed=1)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A03u",
            "name": "neon-tube",
            "label": "neon-tube-magenta",
            "frames": lambda: list(neon_tube_glitch(text, color="magenta", n_frames=36, seed=2)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A03a",
            "name": "neon-glitch",
            "label": "neon-cyan",
            "frames": lambda: list(neon_glitch(text, color="cyan", n_frames=36, seed=1)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A03b",
            "name": "neon-glitch",
            "label": "neon-magenta",
            "frames": lambda: list(neon_glitch(text, color="magenta", n_frames=36, seed=2)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A03c",
            "name": "neon-glitch",
            "label": "neon-multi",
            "frames": lambda: _neon_multi_frames(_TEXT),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A04",
            "name": "pulse",
            "label": "pulse",
            "frames": lambda: list(pulse(text)),
            "fps": 24.0,
            "loop": True,
        },
        {
            "id": "A05",
            "name": "dissolve",
            "label": "dissolve",
            "frames": lambda: _dissolve_in_out(text),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A05d",
            "name": "density-dissolve",
            "label": "density-dissolve",
            "frames": lambda: list(density_dissolve(text, n_frames=36, direction="loop", seed=42)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A05e",
            "name": "density-dissolve",
            "label": "density-dissolve-cyan",
            "frames": lambda: list(density_dissolve(text, n_frames=36, direction="loop", color="cyan", seed=7)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A10",
            "name": "plasma-wave",
            "label": "plasma-wave",
            "frames": lambda: list(plasma_wave(text_plain, n_frames=36, preset="default", loop=True)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A10b",
            "name": "plasma-wave",
            "label": "plasma-wave-cyan",
            "frames": lambda: list(plasma_wave(text_plain, n_frames=36, preset="tight", color="cyan", loop=True)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A08",
            "name": "flame-flicker",
            "label": "flame-flicker",
            "frames": lambda: list(flame_flicker(text_plain, n_frames=24, preset="default", loop=True)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A08b",
            "name": "flame-flicker",
            "label": "flame-flicker-hot-red",
            "frames": lambda: list(flame_flicker(text_plain, n_frames=24, preset="hot", color="red", loop=True)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A_VOR1",
            "name": "voronoi-stained-glass",
            "label": "voronoi-stained-glass-spectral",
            "frames": lambda: list(voronoi_stained_glass(text_plain, n_frames=30, palette_name="spectral", loop=True)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A_VOR1b",
            "name": "voronoi-stained-glass",
            "label": "voronoi-stained-glass-fire",
            "frames": lambda: list(voronoi_stained_glass(text_plain, n_frames=30, palette_name="fire", loop=True)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A10c",
            "name": "plasma-lava-lamp",
            "label": "plasma-lava-lamp",
            "frames": lambda: list(plasma_lava_lamp(text_plain, n_frames=36, palette_name="lava", loop=True)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A10c",
            "name": "plasma-lava-spectral",
            "label": "plasma-lava-spectral",
            "frames": lambda: list(plasma_lava_lamp(text_plain, n_frames=36, palette_name="spectral", loop=True)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A08c",
            "name": "flame-gradient-color",
            "label": "flame-gradient-color",
            "frames": lambda: list(flame_gradient_color(text_plain, n_frames=24, preset="default", loop=True)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "X_FLAME_BLOOM",
            "name": "flame-bloom",
            "label": "flame-bloom",
            "frames": lambda: list(flame_bloom(text_plain, n_frames=24, preset="hot", loop=True)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A_BLOOM1",
            "name": "bloom-pulse",
            "label": "bloom-pulse-fire",
            "frames": lambda: list(bloom_pulse(text_plain, n_frames=24, preset="hot", palette_name="fire", tone_curve="aces", bloom_color_name="orange", base_radius=4, bloom_amplitude=2, loop=True)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "X_PLASMA_BLOOM",
            "name": "Plasma Bloom",
            "label": "plasma-bloom-spectral",
            "frames": lambda: list(plasma_bloom(text_plain, n_frames=36, preset="default", palette_name="spectral", radius=3, falloff=0.88, loop=True)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A_ISO1",
            "name": "Isometric Depth Breathe",
            "label": "iso-depth-breathe",
            "frames": lambda: list(iso_depth_breathe(text_plain, n_frames=24, fill="plasma", base_depth=4, amplitude=3, loop=True)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "X_TURING_BIO",
            "name": "Turing Biological Coat Colors",
            "label": "turing-bio-spots",
            "frames": lambda: list(turing_bio(text_plain, preset="spots", seed=42, n_frames=36, palette_name="bio", loop=True)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "X_TURING_BIO",
            "name": "Turing Biological Coat Stripes",
            "label": "turing-bio-stripes",
            "frames": lambda: list(turing_bio(text_plain, preset="stripes", seed=42, n_frames=36, palette_name="bio", loop=True)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A_N09a",
            "name": "Turing Morphogenesis",
            "label": "turing-morphogenesis-spots",
            "frames": lambda: list(turing_morphogenesis(text_plain, preset="spots", seed=42, snapshot_steps=[50, 100, 200, 400, 800, 1500, 2500, 3500], palette_name="bio", loop=True)),
            "fps": 4.0,
            "loop": True,
        },
        {
            "id": "A08d",
            "name": "Plasma-Modulated Flame",
            "label": "plasma-flame",
            "frames": lambda: list(plasma_flame(text_plain, n_frames=36, flame_preset="hot", plasma_preset="default", palette_name="fire", tone_curve="aces", bloom_color_name="orange", base_radius=3, bloom_amplitude=1.5, modulator_strength=1.2, loop=True)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "X_PLASMA_WARP",
            "name": "Plasma-Modulated Sine Warp",
            "label": "plasma-warp-spectral",
            "frames": lambda: list(plasma_warp(text_plain, n_frames=36, plasma_preset="default", fill="plasma", max_amplitude=6.0, frequency=1.0, palette_name="spectral", bloom_color_name="cyan", bloom_radius=2, bloom_falloff=0.75, loop=True)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "X_FRACTAL_CLASSIC",
            "name": "fractal-color-cycle",
            "label": "fractal-escape-escape",
            "frames": lambda: list(fractal_color_cycle(text_plain, n_frames=72, loop=True)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "X_TURING_WARP",
            "name": "Turing Morphogenesis-Modulated Sine Warp",
            "label": "turing-warp-spots",
            "frames": lambda: list(turing_warp(text_plain, n_frames=36, turing_preset="spots", seed=42, max_amplitude=5.0, frequency=1.0, palette_name="bio", bloom_color_name="green", bloom_radius=2, bloom_falloff=0.75, loop=True)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "X_FLAME_ISO_BLOOM",
            "name": "Flame Isometric Bloom",
            "label": "flame-iso-bloom-fire",
            "frames": lambda: list(flame_iso_bloom(text_plain, n_frames=36, depth=4, flame_preset="default", palette_name="fire", tone_curve="aces", bloom_color_name="fire", bloom_radius=4, bloom_falloff=0.85, loop=True)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "X_NOISE_WARP",
            "name": "Perlin Noise Phase-Map Sine Warp",
            "label": "noise-warp-spectral",
            "frames": lambda: list(noise_warp(text_plain, n_frames=36, noise_scale=0.4, noise_seed=42, max_amplitude=5.0, max_phase_spread=3.14159, palette_name="spectral", bloom_color_name="cyan", bloom_radius=2, bloom_falloff=0.75, loop=True)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "X_PLASMA_NOISE_WARP",
            "name": "Plasma Amplitude × Noise Phase Sine Warp",
            "label": "plasma-noise-warp-spectral",
            "frames": lambda: list(plasma_noise_warp(text_plain, n_frames=36, plasma_preset="default", noise_scale=0.4, noise_seed=42, max_amplitude=6.0, max_phase_spread=3.14159, frequency=1.0, palette_name="spectral", bloom_color_name="cyan", bloom_radius=2, bloom_falloff=0.75, loop=True)),
            "fps": 12.0,
            "loop": True,
        },
        {
            "id": "A06",
            "name": "Living Fill — Conway GoL",
            "label": "living-fill",
            "frames": lambda: list(living_fill(text_plain, n_frames=120, seed=42, alive_prob=0.4, color="green", loop=False)),
            "fps": 10.0,
            "loop": False,
        },
        {
            "id": "X_LIVING_COLOR",
            "name": "Living Color — GoL Age-Heat",
            "label": "living-color-age",
            "frames": lambda: list(living_color(text_plain, n_frames=72, seed=42, alive_prob=0.4, max_age=20, palette_name="age", bloom_color_name="cyan", bloom_radius=2, bloom_falloff=0.70, loop=True)),
            "fps": 10.0,
            "loop": True,
        },
    ]


# -------------------------------------------------------------------------
def _stem(entry: dict) -> str:
    """Build the filename stem for an entry.

    :param entry: Showcase entry dict.
    :returns: Filename stem like 'A01-typewriter'.
    """
    return f"{entry['id']}-{entry['label']}"


# -------------------------------------------------------------------------
def generate_gallery(verbose: bool = True) -> None:
    """Generate .cast and .apng files for all showcase entries.

    :param verbose: Print progress to stdout if True.
    """
    from justdoit.output.cast import save_cast

    try:
        from justdoit.output.apng import save_apng
        _has_pil = True
    except ImportError:
        _has_pil = False
        if verbose:
            print("  [warn] Pillow not available — skipping .apng generation")

    GALLERY_DIR.mkdir(parents=True, exist_ok=True)

    showcase = _build_showcase()
    results = []

    for entry in showcase:
        stem = _stem(entry)
        frames = entry["frames"]()
        fps = entry["fps"]
        loop_int = 0 if entry["loop"] else 1
        title = f"JustDoIt — {entry['name']}"

        # .cast — always
        cast_path = GALLERY_DIR / f"{stem}.cast"
        save_cast(frames, cast_path, fps=fps, title=title)
        if verbose:
            print(f"  saved  {cast_path.name}  ({len(frames)} frames @ {fps}fps)")

        # .apng — Pillow required
        apng_path = None
        if _has_pil:
            apng_path = GALLERY_DIR / f"{stem}.apng"
            save_apng(frames, apng_path, fps=fps, loop=loop_int)
            if verbose:
                print(f"  saved  {apng_path.name}")

        results.append({
            "entry": entry,
            "stem": stem,
            "cast_path": cast_path,
            "apng_path": apng_path,
            "n_frames": len(frames),
        })

    _write_readme(results, verbose=verbose)


# -------------------------------------------------------------------------
def _write_readme(results: list[dict], verbose: bool = True) -> None:
    """Auto-generate docs/anim_gallery/README.md.

    :param results: List of result dicts from generate_gallery().
    :param verbose: Print progress to stdout if True.
    """
    lines = [
        "# Animation Gallery",
        "",
        f"Auto-generated {datetime.now().strftime('%Y-%m-%d')} — do not edit manually.",
        "Run `uv run python scripts/generate_anim_gallery.py` to regenerate.",
        "",
        "Each animation is saved as an APNG (embeds inline) and an asciinema `.cast`",
        "(plays back as a real terminal via `asciinema play`).",
        "",
        "---",
        "",
    ]

    for r in results:
        entry = r["entry"]
        stem = r["stem"]
        n_frames = r["n_frames"]
        fps = entry["fps"]
        loop_label = "looping" if entry["loop"] else "play-once"

        lines.append(f"## {entry['id']} — {entry['name'].title()}")
        lines.append("")
        lines.append(f"**{n_frames} frames** · **{fps}fps** · {loop_label}")
        lines.append("")

        # Table header
        lines.append("| Variant | Preview | Terminal |")
        lines.append("|---------|---------|----------|")

        apng_cell = f"![{entry['label']}]({stem}.apng)" if r["apng_path"] else "*(Pillow not installed)*"
        cast_cell = f"[▶ terminal]({stem}.cast)"
        lines.append(f"| {entry['label']} | {apng_cell} | {cast_cell} |")

        lines.append("")

    readme_path = GALLERY_DIR / "README.md"
    readme_path.write_text("\n".join(lines), encoding="utf-8")
    if verbose:
        print(f"  wrote  {readme_path}")


# -------------------------------------------------------------------------
if __name__ == "__main__":
    logging = _logging
    logging.basicConfig(level=logging.WARNING)
    print(f"Generating animation gallery → {GALLERY_DIR}")
    generate_gallery(verbose=True)
    print("Done.")
