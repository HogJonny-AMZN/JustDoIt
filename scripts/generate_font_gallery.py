"""
generate_font_gallery.py — TTF Font Comparison Gallery for JustDoIt

Renders text through TTF fonts using wide-gallery style (fit_ttf_size ~160 cols,
save_svg). Supports two modes:

1. Manual mode (default): render all discovered fonts in assets/fonts/
2. Batch mode (--batch N): render the next N unrendered fonts from the Google
   Fonts manifest (assets/fonts/google/.manifest.json), update state.

Usage:
    # Render all fonts in assets/fonts/ (manual set)
    uv run python scripts/generate_font_gallery.py

    # Render next 10 from Google Fonts batch
    uv run python scripts/generate_font_gallery.py --batch 10

    # Custom text / cols
    uv run python scripts/generate_font_gallery.py --text "HELLO" --cols 200

    # Show batch progress
    uv run python scripts/generate_font_gallery.py --status
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Config ────────────────────────────────────────────────────────────────────
DEFAULT_TEXT   = "JUST DO IT"
DEFAULT_COLS   = 160
SVG_FONT_SIZE  = 28
IMG_WIDTH      = 780
OUT_DIR        = Path(__file__).parent.parent / "docs" / "gallery-fonts"
ASSETS_DIR     = Path(__file__).parent.parent / "assets" / "fonts"
GOOGLE_DIR     = ASSETS_DIR / "google"
MANIFEST_PATH  = GOOGLE_DIR / ".manifest.json"

# Manual font search paths (non-Google)
MANUAL_FONT_DIRS = [
    ASSETS_DIR,
    Path("/usr/share/fonts/truetype/dejavu"),
]

# Display name overrides for known font stems
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
}


# ── Font discovery ────────────────────────────────────────────────────────────
def discover_manual_fonts() -> list[tuple[str, Path]]:
    """Return (label, path) for all TTF/OTF in manual font dirs, deduplicated."""
    seen: set = set()
    found: list = []
    for d in MANUAL_FONT_DIRS:
        if not d.exists():
            continue
        for ext in ("*.ttf", "*.otf"):
            for fp in sorted(d.glob(ext)):
                # Skip google subdir — handled separately
                if "google" in fp.parts:
                    continue
                if fp.stem not in seen:
                    seen.add(fp.stem)
                    label = FONT_LABELS.get(fp.stem, fp.stem)
                    found.append((label, fp))
    return found


def load_manifest() -> list[dict]:
    """Load Google Fonts manifest, return [] if not present."""
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    return []


def save_manifest(manifest: list[dict]) -> None:
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))


def pick_batch(manifest: list[dict], n: int) -> list[dict]:
    """Return the next N unrendered entries from the manifest."""
    return [f for f in manifest if not f.get("rendered")][:n]


# ── Rendering ─────────────────────────────────────────────────────────────────
def render_font_svg(
    text: str,
    font_path: Path,
    target_cols: int,
    svg_font_size: int,
) -> str | None:
    """Render text with a TTF font, return SVG string or None on failure."""
    try:
        from justdoit.layout import fit_ttf_size
        from justdoit.fonts.ttf import load_ttf_font
        from justdoit import render
        from justdoit.output.svg import save_svg
        import tempfile

        pt_size = fit_ttf_size(text, target_cols, str(font_path))
        font = load_ttf_font(str(font_path), font_size=pt_size)
        rendered = render(text, font=font)

        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
            tmp = f.name
        try:
            save_svg(rendered, tmp, font_size=svg_font_size)
            return Path(tmp).read_text(encoding="utf-8")
        finally:
            os.unlink(tmp)

    except Exception as exc:
        print(f"    SKIP ({type(exc).__name__}: {exc})", file=sys.stderr)
        return None


# ── README ────────────────────────────────────────────────────────────────────
def write_readme(out_dir: Path, entries: list[tuple[str, str]]) -> None:
    """Write/update README.md with full table of all SVGs in out_dir."""
    # Scan all existing SVGs so README stays in sync across multiple batch runs
    existing = sorted(out_dir.glob("*.svg"))
    # Build stem -> label map from entries passed in + stems already on disk
    label_map: dict = {stem: label for stem, label in entries}
    for p in existing:
        if p.stem not in label_map:
            label_map[p.stem] = p.stem  # fallback: use stem as label

    # Group: manual (F- prefix from this run) and google-batch (G- prefix)
    manual  = [(s, l) for s, l in sorted(label_map.items()) if not s.startswith("G-")]
    batched = [(s, l) for s, l in sorted(label_map.items()) if s.startswith("G-")]

    lines = [
        "# Font Gallery",
        "",
        "> TTF font comparison — each entry shows how that font renders as ASCII art.",
        "> Rendered at ~160 cols target width, wide-gallery style.",
        f"> **{len(label_map)} fonts rendered** (manual + Google Fonts batch).",
        "",
    ]

    if manual:
        lines += ["## Curated Fonts", ""]
        lines += ["| Font | Preview |", "|------|---------|"]
        for stem, label in manual:
            lines.append(f"| **{label}** | ![{label}]({stem}.svg) |")
        lines.append("")

    if batched:
        lines += ["## Google Fonts Batch", ""]
        lines += ["| Font | Preview |", "|------|---------|"]
        for stem, label in batched:
            lines.append(f"| **{label}** | ![{label}]({stem}.svg) |")
        lines.append("")

    (out_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"  index  {out_dir}/README.md  ({len(label_map)} total fonts)")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="TTF font comparison gallery")
    parser.add_argument("--text",    default=DEFAULT_TEXT, help="Text to render")
    parser.add_argument("--cols",    type=int, default=DEFAULT_COLS)
    parser.add_argument("--batch",   type=int, default=0,
                        help="Render next N unrendered Google Fonts (0 = manual mode)")
    parser.add_argument("--status",  action="store_true",
                        help="Show Google Fonts batch progress and exit")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Status mode ───────────────────────────────────────────────────────────
    if args.status:
        manifest = load_manifest()
        if not manifest:
            print("No Google Fonts manifest found.")
            print("Run: uv run python scripts/download_google_fonts.py")
        else:
            total     = len(manifest)
            rendered  = sum(1 for f in manifest if f.get("rendered"))
            remaining = total - rendered
            print(f"Google Fonts batch progress:")
            print(f"  Total:     {total}")
            print(f"  Rendered:  {rendered}")
            print(f"  Remaining: {remaining}")
            if remaining:
                nxt = pick_batch(manifest, 3)
                print(f"  Next up:   {', '.join(f['stem'] for f in nxt)}")
        return

    entries: list[tuple[str, str]] = []

    # ── Batch mode (Google Fonts) ─────────────────────────────────────────────
    if args.batch > 0:
        manifest = load_manifest()
        if not manifest:
            print("No Google Fonts manifest. Run download_google_fonts.py first.")
            sys.exit(1)

        batch = pick_batch(manifest, args.batch)
        total     = len(manifest)
        rendered  = sum(1 for f in manifest if f.get("rendered"))
        remaining = len([f for f in manifest if not f.get("rendered")])

        if not batch:
            print(f"All {total} Google Fonts already rendered!")
            print("Time to find more fonts. See RESEARCH_LOG for next font sources.")
            return

        print(f"Google Fonts batch: rendering {len(batch)} fonts "
              f"({rendered}/{total} done, {remaining} remaining)")
        print()

        for entry in batch:
            font_path = GOOGLE_DIR / entry["path"]
            label = entry.get("label") or entry["stem"]
            stem  = f"G-{entry['stem']}"
            print(f"  {label}  ({font_path.name})")

            if not font_path.exists():
                print(f"    SKIP (file not found)")
                continue

            svg = render_font_svg(args.text, font_path, args.cols, SVG_FONT_SIZE)
            if svg is not None:
                (OUT_DIR / f"{stem}.svg").write_text(svg, encoding="utf-8")
                entries.append((stem, label))
                # Mark rendered in manifest
                entry["rendered"] = True
                entry["label"]    = label
            # Always mark attempted so we don't retry broken fonts forever
            entry["rendered"] = True

        save_manifest(manifest)
        print()

    # ── Manual mode (curated assets/fonts/) ───────────────────────────────────
    else:
        fonts = discover_manual_fonts()
        if not fonts:
            print("No fonts found in assets/fonts/. Add TTFs or run download_google_fonts.py.")
            sys.exit(1)

        print(f"Rendering '{args.text}' in {len(fonts)} fonts → {OUT_DIR}/")
        print()

        for label, font_path in fonts:
            stem = f"F-{font_path.stem}"
            print(f"  {label}  ({font_path.name})")
            svg = render_font_svg(args.text, font_path, args.cols, SVG_FONT_SIZE)
            if svg is not None:
                (OUT_DIR / f"{stem}.svg").write_text(svg, encoding="utf-8")
                entries.append((stem, label))
            print() if svg is None else None

    # ── Update README ─────────────────────────────────────────────────────────
    print()
    write_readme(OUT_DIR, entries)
    print(f"\nDone → {OUT_DIR}/")


if __name__ == "__main__":
    main()
