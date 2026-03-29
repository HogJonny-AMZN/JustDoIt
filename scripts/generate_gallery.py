"""
Package: scripts.generate_gallery
Generate SVG gallery from curated showcase renders + daily agent outputs.

Run with:
    python scripts/generate_gallery.py
    python scripts/generate_gallery.py --text "HELLO"
    python scripts/generate_gallery.py --index-only   # rebuild README without re-rendering

Saves SVGs to docs/gallery/ and regenerates docs/gallery/README.md.
Each SVG is self-contained and renders inline on GitHub.
"""

import argparse
import logging as _logging
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "scripts.generate_gallery"
__updated__ = "2026-03-27 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

GALLERY_DIR = Path(__file__).parent.parent / "docs" / "gallery"
_GRID_COLS = 2   # columns in the README grid


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

    # Composition
    add("S-F02-noise-radial",     "F02+C02 — Noise fill + radial gradient",
        radial_gradient(render(text, font="block", fill="noise"), parse_color("cyan"), parse_color("blue")))

    return entries


# -------------------------------------------------------------------------
def render_showcase(text: str) -> None:
    """Render curated showcase entries and save as SVGs.

    :param text: Text to render (will be uppercased).
    """
    from justdoit.output.svg import save_svg

    GALLERY_DIR.mkdir(parents=True, exist_ok=True)
    entries = _curated_entries(text.upper())

    for stem, label, rendered in entries:
        path = GALLERY_DIR / f"{stem}.svg"
        save_svg(rendered, str(path))
        print(f"  saved  {path.name}  ({label})")


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
def _table(pairs: list) -> list:
    """Render a list of (filename, label) pairs as an HTML grid table.

    :param pairs: List of (svg_filename, label) tuples.
    :returns: List of HTML lines.
    """
    lines = ['<table>']
    for i in range(0, len(pairs), _GRID_COLS):
        lines.append("<tr>")
        for fname, label in pairs[i:i + _GRID_COLS]:
            lines.append(
                f'<td align="center">'
                f'<img src="{fname}" width="480"><br>'
                f'<sub><b>{label}</b></sub>'
                f'</td>'
            )
        lines.append("</tr>")
    lines.append("</table>")
    return lines


# -------------------------------------------------------------------------
def build_index() -> None:
    """Scan docs/gallery/ for all SVGs and regenerate README.md.

    Showcase SVGs (S- prefix) are grouped by technique category with
    section headers and a table of contents. Daily agent outputs
    (YYYY-MM-DD- prefix) appear in a separate section, newest first.
    """
    svgs = sorted(GALLERY_DIR.glob("*.svg"))
    if not svgs:
        print("  no SVGs found — nothing to index")
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
        lines += _table(pairs)
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
        lines += _table(daily_pairs)
        lines.append("")

    lines.append(
        f"*Last updated: {datetime.now().strftime('%Y-%m-%d')} — "
        f"{total} technique{'s' if total != 1 else ''}*"
    )
    lines.append("")

    readme = GALLERY_DIR / "README.md"
    readme.write_text("\n".join(lines), encoding="utf-8")
    print(f"  index  {readme}  ({total} entries)")


# -------------------------------------------------------------------------
def run(text: str = "Just Do It") -> None:
    """Render curated showcase SVGs and rebuild the gallery index.

    :param text: Text to render (default: 'JDI').
    """
    print(f"Rendering showcase for '{text}' ...")
    render_showcase(text)
    print("Building index ...")
    build_index()
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
    args = parser.parse_args()

    if args.index_only:
        print("Rebuilding index only ...")
        build_index()
        print("Done.")
    else:
        run(text=args.text.upper())
