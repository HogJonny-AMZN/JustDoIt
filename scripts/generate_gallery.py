"""
Package: scripts.generate_gallery
Generate SVG gallery from curated showcase renders + daily agent outputs.

Run with:
    python scripts/generate_gallery.py
    python scripts/generate_gallery.py --text "HELLO"
    python scripts/generate_gallery.py --index-only   # rebuild README without re-rendering
    python scripts/generate_gallery.py --profile wide
    python scripts/generate_gallery.py --profile all

Saves SVGs to docs/gallery/ (or profile-specific dir) and regenerates README.md.
Each SVG is self-contained and renders inline on GitHub.
"""

import argparse
import logging as _logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from justdoit.layout import measure

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "scripts.generate_gallery"
__updated__ = "2026-04-04 00:00:00"
__version__ = "0.2.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

GALLERY_DIR = Path(__file__).parent.parent / "docs" / "gallery"
_GRID_COLS = 2   # columns in the README grid


# -------------------------------------------------------------------------
@dataclass
class GalleryProfile:
    """Gallery render tier — controls SVG font size and README thumbnail width.

    :param name: Profile name (standard/wide/4k).
    :param svg_font_size: Font size in pixels for SVG output.
    :param readme_img_width: img width in README table cells.
    :param output_dir: Path to output directory for this profile.
    :param text: Default render text (default: 'JUST DO IT').
    """
    name: str
    svg_font_size: int
    readme_img_width: int
    output_dir: Path
    text: str = "JUST DO IT"


PROFILES: dict[str, "GalleryProfile"] = {
    "standard": GalleryProfile(
        name="standard",
        svg_font_size=14,
        readme_img_width=480,
        output_dir=Path(__file__).parent.parent / "docs" / "gallery",
    ),
    "wide": GalleryProfile(
        name="wide",
        svg_font_size=28,
        readme_img_width=800,
        output_dir=Path(__file__).parent.parent / "docs" / "gallery-wide",
    ),
    "4k": GalleryProfile(
        name="4k",
        svg_font_size=72,
        readme_img_width=1600,
        output_dir=Path(__file__).parent.parent / "docs" / "gallery-4k",
    ),
}


# -------------------------------------------------------------------------
def _validate_text(text: str, font: str = "block", gap: int = 1) -> None:
    """Warn if text renders unusually wide; raise if empty output.

    :param text: Text to validate.
    :param font: Font name (default: 'block').
    :param gap: Character gap (default: 1).
    :raises ValueError: If text produces empty output.
    """
    cols, _ = measure(text, font=font, gap=gap)
    if cols == 0:
        raise ValueError(f"Text {text!r} produces empty output with font {font!r}")
    if cols > 400:
        print(
            f"Warning: {text!r} renders to {cols} columns — SVGs will be very wide.",
            file=sys.stderr,
        )


# -------------------------------------------------------------------------
def _curated_entries(text: str) -> list[tuple[str, str, str]]:
    """Render all curated showcase techniques.

    :param text: Text to render.
    :returns: List of (filename_stem, label, rendered_string).
    """
    from justdoit.core.rasterizer import render
    from justdoit.effects.gradient import (
        PRESETS, linear_gradient, parse_color, per_glyph_palette, radial_gradient,
    )
    from justdoit.effects.isometric import isometric_extrude
    from justdoit.effects.spatial import perspective_tilt, shear, sine_warp

    plain = render(text, font="block")
    entries: list[tuple[str, str, str]] = []

    def add(stem: str, label: str, rendered: str) -> None:
        entries.append((stem, label, rendered))

    # Fonts
    add("S-F00-block-baseline",   "F00 — Block (baseline)",           plain)
    add("S-G01-figlet-big",       "G01 — FIGlet 'big'",               render(text, font="big"))
    add("S-G01-figlet-slant",     "G01 — FIGlet 'slant'",             render(text, font="slant"))
    add("S-G01-slim",             "G01 — Slim font",                  render(text, font="slim"))

    # Fill effects
    add("S-F01-density-fill",     "F01 — Density fill",               render(text, font="block", fill="density"))
    add("S-F06-sdf-fill",         "F06 — SDF fill",                   render(text, font="block", fill="sdf"))
    add("S-F07-shape-fill",       "F07 — Shape fill",                 render(text, font="block", fill="shape"))
    add("S-F02-noise-fill",       "F02 — Perlin noise fill",          render(text, font="block", fill="noise"))
    add("S-F03-cells-fill",       "F03 — Cellular automata fill",     render(text, font="block", fill="cells"))
    add("S-F09-wave-default",     "F09 — Wave interference (default)", render(text, font="block", fill="wave"))
    add("S-F09-wave-moire",       "F09 — Wave interference (moire)",   render(text, font="block", fill="wave"))
    add("S-F05-fractal-default",  "F05 — Fractal/Mandelbrot (default)", render(text, font="block", fill="fractal"))
    add("S-F05-fractal-julia",    "F05 — Fractal/Julia (julia_swirl)", render(text, font="block", fill="fractal"))

    # Color effects
    add("S-C01-gradient-horiz",   "C01 — Gradient (horizontal)",
        linear_gradient(plain, parse_color("red"), parse_color("cyan"), direction="horizontal"))
    add("S-C01-gradient-diag",    "C01 — Gradient (diagonal)",
        linear_gradient(plain, parse_color("magenta"), parse_color("green"), direction="diagonal"))
    add("S-C02-radial",           "C02 — Radial gradient",
        radial_gradient(plain, parse_color("white"), parse_color("purple")))
    add("S-C03-fire",             "C03 — Fire palette",               per_glyph_palette(plain, PRESETS["fire"]))
    add("S-C03-neon",             "C03 — Neon palette",               per_glyph_palette(plain, PRESETS["neon"]))
    add("S-C03-ocean",            "C03 — Ocean palette",              per_glyph_palette(plain, PRESETS["ocean"]))

    # Spatial effects
    add("S-S01-sine-warp",        "S01 — Sine warp",                  sine_warp(plain, amplitude=4.0, frequency=1.5))
    add("S-S02-perspective-top",  "S02 — Perspective tilt (top)",     perspective_tilt(plain, strength=0.5, direction="top"))
    add("S-S08-shear-right",      "S08 — Shear (right)",              shear(plain, amount=1.2, direction="right"))

    # Isometric
    iso = isometric_extrude(plain, depth=4, direction="right")
    add("S-S03-iso-right",        "S03 — Isometric extrude",          iso)
    add("S-S03-iso-gradient",     "S03+C01 — Iso + gradient",
        linear_gradient(iso, parse_color("gold"), parse_color("red"), direction="vertical"))
    add("S-S03-iso-neon-warp",    "S03+C03+S01 — Iso + neon + warp",
        sine_warp(per_glyph_palette(isometric_extrude(plain, depth=3), PRESETS["neon"]), amplitude=2.0))

    # Generative simulation fills
    add("S-N09-turing-stripes",   "N09 — Turing stripes (FHN activator-inhibitor)",
        render(text, font="block", fill="turing"))
    add("S-N09-turing-spots",     "N09 — Turing spots",
        render(text, font="block", fill="turing"))
    add("S-N09-turing-maze",      "N09 — Turing maze (labyrinthine)",
        render(text, font="block", fill="turing"))
    add("S-F07-voronoi-default",  "F07 — Voronoi fill (default)",
        render(text, font="block", fill="voronoi"))
    add("S-F07-voronoi-cracked",  "F07 — Voronoi cracked (stained-glass)",
        render(text, font="block", fill="voronoi_cracked"))
    add("S-F07-voronoi-fine",     "F07 — Voronoi fine (dense cells)",
        render(text, font="block", fill="voronoi_fine"))
    add("S-F07-voronoi-coarse",   "F07 — Voronoi coarse (large cells)",
        render(text, font="block", fill="voronoi_coarse"))

    # A10 — Plasma Wave fill
    add("S-A10-plasma-default",   "A10 — Plasma Wave (default)",
        render(text, font="block", fill="plasma"))
    add("S-A10-plasma-tight",     "A10 — Plasma tight (high freq)",
        render(text, font="block", fill="plasma_tight"))
    add("S-A10-plasma-slow",      "A10 — Plasma slow (large blobs)",
        render(text, font="block", fill="plasma_slow"))
    add("S-A10-plasma-diagonal",  "A10 — Plasma diagonal (stripe bias)",
        render(text, font="block", fill="plasma_diagonal"))

    # A08 — Flame Simulation fill
    add("S-A08-flame-default",  "A08 — Flame Simulation (balanced fire)",
        render(text, font="block", fill="flame"))
    add("S-A08-flame-hot",      "A08 — Flame hot (tall, intense flame)",
        render(text, font="block", fill="flame_hot"))
    add("S-A08-flame-embers",   "A08 — Flame embers (dying embers)",
        render(text, font="block", fill="flame_embers"))

    # Composition
    add("S-F02-noise-radial",     "F02+C02 — Noise fill + radial gradient",
        radial_gradient(render(text, font="block", fill="noise"), parse_color("cyan"), parse_color("blue")))

    return entries


# Category metadata: code prefix → (heading, anchor, description)
_CATEGORIES: dict = {
    "G": ("Fonts",          "fonts",        "Builtin, FIGlet, and TTF rasterized fonts"),
    "F": ("Fill Effects",   "fill-effects", "Character fill modes applied inside glyph masks"),
    "C": ("Color Effects",  "color-effects","Gradients, palettes, and ANSI colorization"),
    "S": ("Spatial & 3D",   "spatial--3d",  "Warps, perspective, shear, and isometric extrusion"),
}


# -------------------------------------------------------------------------
def _showcase_label(stem: str) -> str:
    """Convert a showcase SVG stem to a human-readable label.

    :param stem: SVG filename stem, e.g. 'S-F07-shape-fill'.
    :returns: Label string, e.g. 'F07 — Shape Fill'.
    """
    rest = stem[2:]  # strip "S-"
    parts = rest.split("-", 1)
    code = parts[0].upper()
    slug = parts[1].replace("-", " ").title() if len(parts) > 1 else ""
    return f"{code} — {slug}"


# -------------------------------------------------------------------------
def _daily_label(stem: str) -> str:
    """Convert a daily agent SVG stem to a human-readable label.

    :param stem: SVG filename stem, e.g. '2026-03-26-N10-slime-mold'.
    :returns: Label string, e.g. '2026-03-26 · N10 Slime Mold'.
    """
    parts = stem.split("-", 3)
    if len(parts) >= 4:
        date = "-".join(parts[:3])
        rest = parts[3].replace("-", " ").title()
        return f"{date} · {rest}"
    return stem.replace("-", " ").title()


# -------------------------------------------------------------------------
def _table(pairs: list, img_width: int = 480) -> list:
    """Render a list of (filename, label) pairs as an HTML grid table.

    :param pairs: List of (svg_filename, label) tuples.
    :param img_width: Width in pixels for thumbnail images.
    :returns: List of HTML lines.
    """
    lines = ['<table>']
    for i in range(0, len(pairs), _GRID_COLS):
        lines.append("<tr>")
        for fname, label in pairs[i:i + _GRID_COLS]:
            lines.append(
                f'<td align="center">'
                f'<img src="{fname}" width="{img_width}"><br>'
                f'<sub><b>{label}</b></sub>'
                f'</td>'
            )
        lines.append("</tr>")
    lines.append("</table>")
    return lines


# -------------------------------------------------------------------------
def _write_readme(profile: GalleryProfile, entries: list[tuple[str, str, str]]) -> None:
    """Scan profile output_dir for all SVGs and write README.md.

    Showcase SVGs (S- prefix) are grouped by technique category with
    section headers and a table of contents. Daily agent outputs
    (YYYY-MM-DD- prefix) appear in a separate section, newest first.

    :param profile: Gallery profile controlling output path and img width.
    :param entries: List of (stem, label, rendered) tuples (used for ordering).
    """
    gallery_dir = profile.output_dir
    svgs = sorted(gallery_dir.glob("*.svg"))
    if not svgs:
        print(f"  no SVGs found in {gallery_dir} — nothing to index")
        return

    # Split into showcase (S- prefix) and daily (date prefix)
    showcase = [p for p in svgs if p.stem.startswith("S-")]
    daily    = sorted([p for p in svgs if not p.stem.startswith("S-")], reverse=True)

    # Group showcase by category letter (second char of code after "S-")
    groups: dict = {k: [] for k in _CATEGORIES}
    for p in showcase:
        code = p.stem[2:].split("-")[0].upper()   # e.g. "F07"
        cat = code[0] if code else "S"
        groups.setdefault(cat, []).append((p.name, _showcase_label(p.stem)))

    total = len(showcase) + len(daily)

    # --- Table of contents ---
    lines = [
        "# JustDoIt Gallery",
        "",
        "Auto-generated visual showcase of rendering techniques.",
        "Run `python scripts/demo.py --gallery` to regenerate.",
        "",
        "## Contents",
        "",
    ]
    for cat, (heading, anchor, _) in _CATEGORIES.items():
        if groups.get(cat):
            n = len(groups[cat])
            lines.append(f"- [{heading} ({n})](#{anchor})")
    if daily:
        lines.append(f"- [Daily Techniques ({len(daily)})](#daily-techniques)")
    lines.append("")

    # --- Showcase sections ---
    for cat, (heading, anchor, desc) in _CATEGORIES.items():
        pairs = groups.get(cat, [])
        if not pairs:
            continue
        lines += [
            f"## {heading}",
            "",
            f"*{desc}*",
            "",
        ]
        lines += _table(pairs, img_width=profile.readme_img_width)
        lines.append("")

    # --- Daily section ---
    if daily:
        lines += [
            "## Daily Techniques",
            "",
            "*New technique added each day by the daily agent — newest first.*",
            "",
        ]
        daily_pairs = [(_p.name, _daily_label(_p.stem)) for _p in daily]
        lines += _table(daily_pairs, img_width=profile.readme_img_width)
        lines.append("")

    lines.append(
        f"*Last updated: {datetime.now().strftime('%Y-%m-%d')} — "
        f"{total} technique{'s' if total != 1 else ''}*"
    )
    lines.append("")

    readme = gallery_dir / "README.md"
    readme.write_text("\n".join(lines), encoding="utf-8")
    print(f"  index  {readme}  ({total} entries)")


# -------------------------------------------------------------------------
def _generate_for_profile(profile: GalleryProfile, text: str) -> None:
    """Generate all gallery SVGs and README for a given profile.

    :param profile: Gallery profile controlling font size and output paths.
    :param text: Text to render for all gallery entries.
    """
    from justdoit.output.svg import save_svg

    profile.output_dir.mkdir(parents=True, exist_ok=True)
    entries = _curated_entries(text)

    for stem, label, rendered in entries:
        path = profile.output_dir / f"{stem}.svg"
        save_svg(rendered, str(path), font_size=profile.svg_font_size)
        print(f"  saved  {path.name}  ({label})")

    _write_readme(profile, entries)


# -------------------------------------------------------------------------
def build_index() -> None:
    """Scan docs/gallery/ for all SVGs and regenerate README.md.

    Showcase SVGs (S- prefix) are grouped by technique category with
    section headers and a table of contents. Daily agent outputs
    (YYYY-MM-DD- prefix) appear in a separate section, newest first.
    """
    standard_profile = PROFILES["standard"]
    _write_readme(standard_profile, [])


# -------------------------------------------------------------------------
def run(text: str = "Just Do It") -> None:
    """Render curated showcase SVGs and rebuild the gallery index.

    :param text: Text to render (default: 'JDI').
    """
    print(f"Rendering showcase for '{text}' ...")
    profile = PROFILES["standard"]
    profile.output_dir.mkdir(parents=True, exist_ok=True)
    _generate_for_profile(profile, text)
    print("Done.")


# -------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate JustDoIt SVG gallery and README index.",
    )
    parser.add_argument(
        "--text", default="Just Do It",
        help="Text to render (default: Just Do It)",
    )
    parser.add_argument(
        "--index-only", action="store_true",
        help="Only rebuild the README index, do not re-render SVGs",
    )
    parser.add_argument(
        "--profile", default="standard",
        choices=list(PROFILES.keys()) + ["all"],
        help="Gallery render profile: standard (14px/480px), wide (28px/800px), "
             "4k (72px/1600px), all. Default: standard",
    )
    args = parser.parse_args()

    if args.index_only:
        print("Rebuilding index only ...")
        build_index()
        print("Done.")
    else:
        text = args.text.upper()

        # Determine which profiles to run
        if args.profile == "all":
            profiles_to_run = list(PROFILES.values())
        else:
            profiles_to_run = [PROFILES[args.profile]]

        _validate_text(text)

        for profile in profiles_to_run:
            profile.output_dir.mkdir(parents=True, exist_ok=True)
            print(f"Rendering [{profile.name}] profile for '{text}' ...")
            _generate_for_profile(profile, text)
            print(f"[{profile.name}] Done → {profile.output_dir}")
