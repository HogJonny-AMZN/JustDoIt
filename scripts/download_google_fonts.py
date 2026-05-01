"""
download_google_fonts.py — Download and unpack the Google Fonts repository snapshot.

Downloads https://github.com/google/fonts/archive/main.zip (~1GB) and extracts
all TTF/OTF files to assets/fonts/google/, organized by category (apache, ofl, ufl).

Usage:
    uv run python scripts/download_google_fonts.py
    uv run python scripts/download_google_fonts.py --list   # list fonts without downloading
    uv run python scripts/download_google_fonts.py --force  # re-download even if present

Output:
    assets/fonts/google/<category>/<family>/<file>.ttf
    assets/fonts/google/.manifest.json  — index of all fonts with metadata
"""

import argparse
import json
import os
import sys
import zipfile
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

FONTS_ZIP_URL = "https://github.com/google/fonts/archive/main.zip"
ASSETS_DIR    = Path(__file__).parent.parent / "assets" / "fonts" / "google"
MANIFEST_PATH = ASSETS_DIR / ".manifest.json"

# Known open-source font repos worth checking after Google Fonts is exhausted
FUTURE_FONT_SOURCES = [
    {
        "name": "SDL_ttf bundled fonts",
        "url": "https://github.com/libsdl-org/SDL_ttf",
        "notes": "Includes DejaVu and other reference fonts used by SDL projects",
    },
    {
        "name": "Nerd Fonts",
        "url": "https://github.com/ryanoasis/nerd-fonts",
        "notes": "Patched fonts with icons — useful for PUA glyph exploration (G10)",
    },
    {
        "name": "GNU FreeFont",
        "url": "https://www.gnu.org/software/freefont/",
        "notes": "Free UCS Outline Fonts — comprehensive Unicode coverage",
    },
    {
        "name": "Adobe Source Fonts",
        "url": "https://github.com/adobe-fonts",
        "notes": "Source Code Pro, Source Sans, Source Serif — high quality OFL",
    },
]


def download_with_progress(url: str, dest: Path) -> None:
    """Download url to dest with a simple progress indicator."""
    req = Request(url, headers={"User-Agent": "JustDoIt-font-downloader/1.0"})
    try:
        with urlopen(req) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            chunk = 65536
            with open(dest, "wb") as f:
                while True:
                    block = resp.read(chunk)
                    if not block:
                        break
                    f.write(block)
                    downloaded += len(block)
                    if total:
                        pct = downloaded * 100 // total
                        mb = downloaded / 1_048_576
                        print(f"\r  {mb:.0f}MB / {total/1_048_576:.0f}MB  ({pct}%)", end="", flush=True)
            print()
    except URLError as e:
        print(f"\nERROR downloading {url}: {e}", file=sys.stderr)
        sys.exit(1)


def extract_fonts(zip_path: Path, dest_dir: Path) -> list[dict]:
    """Extract all TTF/OTF files from the zip, return manifest entries."""
    manifest = []
    dest_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        all_names = zf.namelist()
        font_names = [n for n in all_names if n.lower().endswith((".ttf", ".otf"))]
        print(f"  Found {len(font_names)} font files in archive")

        for i, name in enumerate(font_names):
            # Strip leading "fonts-main/" prefix from zip paths
            # zip structure: fonts-main/apache/familyname/Font-Style.ttf
            parts = Path(name).parts
            if len(parts) < 3:
                continue
            # parts[0] = "fonts-main", parts[1] = category, rest = family/file
            rel = Path(*parts[1:])
            out_path = dest_dir / rel
            out_path.parent.mkdir(parents=True, exist_ok=True)

            with zf.open(name) as src, open(out_path, "wb") as dst:
                dst.write(src.read())

            manifest.append({
                "path": str(rel),
                "stem": out_path.stem,
                "category": parts[1] if len(parts) > 1 else "unknown",
                "family": parts[2] if len(parts) > 2 else "unknown",
                "rendered": False,
            })

            if (i + 1) % 500 == 0:
                print(f"  Extracted {i+1}/{len(font_names)}...")

    print(f"  Extracted {len(manifest)} font files to {dest_dir}")
    return manifest


def load_manifest() -> list[dict]:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    return []


def save_manifest(manifest: list[dict]) -> None:
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))


def list_fonts(manifest: list[dict]) -> None:
    total = len(manifest)
    rendered = sum(1 for f in manifest if f.get("rendered"))
    remaining = total - rendered
    print(f"Google Fonts manifest: {total} fonts total, {rendered} rendered, {remaining} remaining")
    print()
    categories: dict = {}
    for f in manifest:
        categories.setdefault(f["category"], 0)
        categories[f["category"]] += 1
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Google Fonts snapshot")
    parser.add_argument("--list",  action="store_true", help="List manifest without downloading")
    parser.add_argument("--force", action="store_true", help="Re-download even if already present")
    args = parser.parse_args()

    if args.list:
        manifest = load_manifest()
        if not manifest:
            print("No manifest found. Run without --list to download first.")
        else:
            list_fonts(manifest)
        return

    zip_path = ASSETS_DIR.parent / "_google_fonts_main.zip"

    # Check if already downloaded and extracted
    if MANIFEST_PATH.exists() and not args.force:
        manifest = load_manifest()
        print(f"Already downloaded: {len(manifest)} fonts in {ASSETS_DIR}")
        print("Use --force to re-download, --list to see manifest.")
        return

    # Download
    ASSETS_DIR.parent.mkdir(parents=True, exist_ok=True)
    if not zip_path.exists() or args.force:
        print(f"Downloading Google Fonts snapshot (~1GB)...")
        print(f"  Source: {FONTS_ZIP_URL}")
        download_with_progress(FONTS_ZIP_URL, zip_path)
        print(f"  Saved to {zip_path}")
    else:
        print(f"Using cached zip: {zip_path}")

    # Extract
    print(f"Extracting to {ASSETS_DIR}...")
    manifest = extract_fonts(zip_path, ASSETS_DIR)
    save_manifest(manifest)
    print(f"Manifest saved: {MANIFEST_PATH}")
    print()
    list_fonts(manifest)
    print()
    print("Future font sources when Google Fonts is exhausted:")
    for src in FUTURE_FONT_SOURCES:
        print(f"  - {src['name']}: {src['url']}")
        print(f"    {src['notes']}")


if __name__ == "__main__":
    main()
