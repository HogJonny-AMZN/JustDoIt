"""
generate_font_gallery.py — TTF Font Comparison Gallery for JustDoIt

Renders 'JUST DO IT' (and optionally any text) through every available TTF font
using the wide-gallery style: fit_ttf_size to ~160 cols, save_svg.

Produces docs/gallery-fonts/ with one SVG per font and a README.md comparison table.

Usage:
    uv run python scripts/generate_font_gallery.py
    uv run python scripts/generate_font_gallery.py --text "YOUR TEXT"
    uv run python scripts/generate_font_gallery.py --cols 200
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Config ────────────────────────────────────────────────────────────────────
DEFAULT_TEXT   = "JUST DO IT"
DEFAULT_COLS   = 160
SVG_FONT_SIZE  = 28          # matches gallery-wide
IMG_WIDTH      = 780         # README table cell width
OUT_DIR        = Path(__file__).parent.parent / "docs" / "gallery-fonts"

# Font search paths — project assets first, then system
FONT_SEARCH_DIRS = [
    Path(__file__).parent.parent / "assets" / "fonts",
    Path("/usr/share/fonts/truetype/dejavu"),
    Path("/usr/share/fonts/truetype"),
    Path("/usr/share/fonts"),
]

# Ordered display names for known fonts (stem -> label)
FONT_LABELS: dict = {
    "DejaVuSansMono":           "DejaVu Sans Mono",
    "DejaVuSansMono-Bold":      "DejaVu Sans Mono Bold",
    "DejaVuSans":               "DejaVu Sans",
    "DejaVuSans-Bold":          "DejaVu Sans Bold",
    "DejaVuSerif":              "DejaVu Serif",
    "DejaVuSerif-Bold":         "DejaVu Serif Bold",
    "RobotoMono-Regular":       "Roboto Mono",
    "RobotoMono-Bold":          "Roboto Mono Bold",
    "SpaceMono-Regular":        "Space Mono",
    "SpaceMono-Bold":           "Space Mono Bold",
    "Inconsolata-Regular":      "Inconsolata",
    "SourceCodePro-Regular":    "Source Code Pro",
    "SourceCodePro-Bold":       "Source Code Pro Bold",
    "ShareTechMono-Regular":    "Share Tech Mono",
    "PressStart2P-Regular":     "Press Start 2P  (pixel/retro)",
    "Oxanium-Bold":             "Oxanium Bold  (geometric/sci-fi)",
    "Bungee-Regular":           "Bungee  (display/wide)",
    "BungeeShade-Regular":      "Bungee Shade  (inline display)",
}


# ── Helpers ───────────────────────────────────────────────────────────────────
def discover_fonts() -> list[tuple[str, Path]]:
    """Return (label, path) pairs for all discovered TTF/OTF fonts, deduplicated."""
    seen_stems: set = set()
    found: list = []
    for d in FONT_SEARCH_DIRS:
        if not d.exists():
            continue
        for ext in ("*.ttf", "*.otf", "*.TTF", "*.OTF"):
            for fp in sorted(d.glob(ext)):
                if fp.stem not in seen_stems:
                    seen_stems.add(fp.stem)
                    label = FONT_LABELS.get(fp.stem, fp.stem)
                    found.append((label, fp))
    return found


def render_font_svg(
    text: str,
    font_path: Path,
    target_cols: int,
    svg_font_size: int,
) -> str | None:
    """Render text with a TTF font and return SVG string, or None on failure."""
    try:
        from justdoit.layout import fit_ttf_size
        from justdoit.fonts.ttf import load_ttf_font
        from justdoit import render
        from justdoit.output.svg import save_svg
        import io, tempfile, os

        pt_size = fit_ttf_size(text, target_cols, str(font_path))
        font = load_ttf_font(str(font_path), font_size=pt_size)
        rendered = render(text, font=font)

        # save_svg writes to a file; use a temp file and read it back
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
            tmp = f.name
        try:
            save_svg(rendered, tmp, font_size=svg_font_size)
            return Path(tmp).read_text(encoding="utf-8")
        finally:
            os.unlink(tmp)

    except Exception as exc:
        print(f"    ERROR: {exc}", file=sys.stderr)
        return None


def write_readme(out_dir: Path, entries: list[tuple[str, str]], img_width: int) -> None:
    """Write README.md comparing all font SVGs in a table."""
    lines = [
        "# Font Gallery",
        "",
        "> TTF font comparison — each entry shows how that font renders as ASCII art.",
        "> Rendered at ~160 cols target width, wide-gallery style.",
        "",
        "| Font | Preview |",
        "|------|---------|",
    ]
    for stem, label in entries:
        lines.append(f"| **{label}** | ![{label}]({stem}.svg) |")

    lines.append("")
    (out_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"  index  {out_dir}/README.md  ({len(entries)} fonts)")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Generate TTF font comparison gallery")
    parser.add_argument("--text", default=DEFAULT_TEXT, help="Text to render")
    parser.add_argument("--cols", type=int, default=DEFAULT_COLS, help="Target column count")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fonts = discover_fonts()

    if not fonts:
        print("No fonts found. Add TTFs to assets/fonts/ or install system fonts.")
        sys.exit(1)

    print(f"Rendering '{args.text}' in {len(fonts)} fonts → {OUT_DIR}/")
    print()

    entries: list[tuple[str, str]] = []

    for label, font_path in fonts:
        stem = f"F-{font_path.stem}"
        print(f"  {label}  ({font_path.name})")
        svg = render_font_svg(args.text, font_path, args.cols, SVG_FONT_SIZE)
        if svg is not None:
            (OUT_DIR / f"{stem}.svg").write_text(svg, encoding="utf-8")
            entries.append((stem, label))
        else:
            print(f"    skipped (render failed)")

    print()
    write_readme(OUT_DIR, entries, IMG_WIDTH)
    print(f"\nDone → {OUT_DIR}/")


if __name__ == "__main__":
    main()
