# Animation Gallery — Full Design Document

**Status:** Approved for implementation  
**Created:** 2026-03-29  
**Author:** NumberOne  
**Creative Direction:** Jonny Galloway  
**Default FPS:** Configurable per-effect. 24 is the baseline. 60 is worth trying. We won't know until we try.  

> "Make it so." — J.L. Picard

---

## Overview

The static gallery (`docs/gallery/`) captures rendered effects as SVG snapshots.
It cannot represent time. Animation effects — the transporter materialize, the
glitch, the living fill, the flame — *are* time. A single frame of the
transporter effect is just noise. The whole point is the journey from noise
to letter.

This document specifies the full animation gallery system: formats, modules,
pipeline, gallery structure, and tooling. When complete, every animation effect
in JustDoIt will have a viewable artifact in the gallery, playable in a browser,
embeddable in a README, and executable in a real terminal.

---

## Design Goals

1. **Every animation effect has a gallery artifact** — no second-class effects
2. **Playable in GitHub README** — APNG embeds inline, auto-plays
3. **Authentic terminal experience available** — asciinema `.cast` for purists
4. **Zero manual steps** — `uv run python scripts/generate_anim_gallery.py` does everything
5. **Same discipline as static gallery** — consistent naming, auto-generated index, committed to repo
6. **24fps** — because we have standards

---

## Output Formats

### Primary: APNG (Animated PNG)

The workhorse. 24-bit color, alpha channel, auto-plays in browsers and GitHub.
Pillow supports APNG natively — no new deps beyond what's already in use.

```
docs/anim_gallery/A11-transporter-tng.apng
```

Viewable: GitHub inline ✅ | Browser ✅ | Terminal ❌

### Secondary: asciinema `.cast`

The soul. Plays back *as* a terminal, not a screenshot of one. Pure JSON lines —
zero deps, ships in core. When someone watches the transporter in asciinema
player, it's running in an actual terminal emulator in the browser.

```
docs/anim_gallery/A11-transporter-tng.cast
```

Viewable: asciinema CLI ✅ | Browser (via player) ✅ | Terminal ✅

### Future: HTML player (phase 2)

Self-contained HTML file with embedded frame data and a minimal JS player.
No external deps, play/pause controls, scrubbable. Good for the CO3DEX site.
Not in scope for initial implementation.

---

## File Naming Convention

```
<technique-id>-<variant>.apng
<technique-id>-<variant>.cast

Examples:
  A01-typewriter.apng
  A11-transporter-tng.apng
  A11-transporter-tos.apng
  A11-transporter-ent.apng
  A03-glitch.apng
  A06-living-fill-cells.apng
```

Where a technique has multiple variants (era, preset, style), each gets its
own file. The index README lists all of them grouped by technique ID.

---

## New Modules

### `justdoit/output/cast.py` — asciinema v2 writer

Pure Python stdlib. No deps. Ships in core (not optional-gated).

```python
"""
Package: justdoit.output.cast
asciinema v2 .cast file writer for animation frame sequences.

Converts a list of ANSI frame strings into an asciinema recording
that can be played back in the terminal or embedded in a browser.
Pure Python stdlib — no external dependencies.
"""

import json
import logging as _logging
import math
from typing import Optional

_MODULE_NAME = "justdoit.output.cast"
__updated__ = "2026-03-29 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


def to_cast(
    frames: list[str],
    fps: float = 24.0,
    title: str = "JustDoIt",
    cols: Optional[int] = None,
    rows: Optional[int] = None,
) -> str:
    """Serialize a frame list to asciinema v2 .cast format string.

    :param frames: List of ANSI frame strings (one string per frame).
    :param fps: Playback speed in frames per second.
    :param title: Recording title (appears in asciinema player).
    :param cols: Terminal width (auto-detected from frames if None).
    :param rows: Terminal height (auto-detected from frames if None).
    :returns: asciinema v2 format string (JSON lines).
    """
    ...


def save_cast(
    frames: list[str],
    path: str,
    fps: float = 24.0,
    title: str = "JustDoIt",
    cols: Optional[int] = None,
    rows: Optional[int] = None,
) -> None:
    """Write frames to an asciinema v2 .cast file.

    :param frames: List of ANSI frame strings.
    :param path: Output file path (conventionally *.cast).
    :param fps: Playback speed in frames per second.
    :param title: Recording title.
    :param cols: Terminal width (auto-detected if None).
    :param rows: Terminal height (auto-detected if None).
    """
    ...
```

**asciinema v2 format:**
```
{"version": 2, "width": 80, "height": 24, "title": "JustDoIt", "env": {}}
[0.000, "o", "\033[2J\033[H... frame 0 ansi string ..."]
[0.042, "o", "\033[2J\033[H... frame 1 ansi string ..."]
[0.083, "o", "\033[2J\033[H... frame 2 ansi string ..."]
...
```

Timestamp = `frame_index / fps`. Dead simple. The `"o"` event type means
"output to terminal." Each frame clears screen (`\033[2J\033[H`) then
writes the ANSI frame string.

---

### `justdoit/output/apng.py` — Animated PNG writer

Pillow-gated. Optional dep pattern — raises `ImportError` with install hint
if Pillow is absent.

```python
"""
Package: justdoit.output.apng
Animated PNG (APNG) writer for animation frame sequences.

Renders each ANSI frame string to a PIL Image using monospace character
grid layout (matching SVG output metrics), then stitches into APNG.
Requires Pillow. Graceful ImportError if not installed.
"""

import logging as _logging
from typing import Optional

_MODULE_NAME = "justdoit.output.apng"
__updated__ = "2026-03-29 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


def frame_to_image(
    frame: str,
    font_size: int = 14,
    bg_color: str = "#111111",
    line_height: float = 1.2,
):
    """Render a single ANSI frame string to a PIL Image.

    :param frame: ANSI frame string (output of render() or animation generator).
    :param font_size: Font size in pixels (monospace metrics match SVG output).
    :param bg_color: Background color hex string.
    :param line_height: Line height multiplier.
    :returns: PIL Image object.
    """
    ...


def to_apng(
    frames: list[str],
    fps: float = 24.0,
    font_size: int = 14,
    bg_color: str = "#111111",
    line_height: float = 1.2,
    loop: int = 0,
) -> bytes:
    """Render frame list to APNG bytes.

    :param frames: List of ANSI frame strings.
    :param fps: Playback speed (determines frame duration).
    :param font_size: Font size in pixels.
    :param bg_color: Background color hex string.
    :param line_height: Line height multiplier.
    :param loop: Number of loops (0 = infinite).
    :returns: APNG file bytes.
    """
    ...


def save_apng(
    frames: list[str],
    path: str,
    fps: float = 24.0,
    font_size: int = 14,
    bg_color: str = "#111111",
    loop: int = 0,
) -> None:
    """Write frame list to an APNG file.

    :param frames: List of ANSI frame strings.
    :param path: Output file path (*.apng or *.png).
    :param fps: Playback speed in frames per second.
    :param font_size: Font size in pixels.
    :param bg_color: Background hex color.
    :param loop: Number of loops (0 = infinite).
    """
    ...
```

**PIL APNG stitch pattern:**
```python
images[0].save(
    path,
    save_all=True,
    append_images=images[1:],
    loop=loop,
    duration=int(1000 / fps),   # ms per frame
    format="PNG",
)
```

---

## New Script: `scripts/generate_anim_gallery.py`

Parallel to `generate_gallery.py`. Declarative showcase list — each entry
defines a technique, its frame generator call, output variants, and its own
fps. **FPS is per-effect.** The effect knows best.

```python
SHOWCASE = [
    {
        "id": "A01",
        "name": "typewriter",
        "variants": [
            {
                "label": "typewriter",
                "frames": lambda: typewriter_frames("JUST DO IT", font="block"),
                "fps": 12,          # typewriter is intentionally slow — it's the effect
                "loop": False,      # play once, hold final frame
            }
        ],
    },
    {
        "id": "A03",
        "name": "glitch",
        "variants": [
            {
                "label": "glitch",
                "frames": lambda: glitch_frames("JUST DO IT"),
                "fps": 24,
                "loop": True,       # ambient — loops naturally
            }
        ],
    },
    {
        "id": "A11",
        "name": "transporter",
        "variants": [
            {
                "label": "transporter-tng",
                "frames": lambda: transporter_frames("ENERGIZE", era="tng"),
                "fps": 24,          # start here — try 60 once visual is solid
                "loop": False,      # narrative effect — play once
                "fps_candidates": [24, 30, 60],  # worth benchmarking all three
            },
            {
                "label": "transporter-tos",
                "frames": lambda: transporter_frames("ENERGIZE", era="tos"),
                "fps": 30,          # TOS is faster/sharper — higher fps feels right
                "loop": False,
            },
            {
                "label": "transporter-ent",
                "frames": lambda: transporter_frames("ENERGIZE", era="ent"),
                "fps": 18,          # ENT prototype is slow, uncertain — lower fps matches
                "loop": False,
            },
        ],
    },
    # ... all animation techniques
    # Rule: fps is not assumed. Each variant sets its own.
    # fps_candidates = list of fps values worth generating for comparison.
]
```

**The fps principle:** the effect registers its *preferred* fps, which may differ
from the gallery default. A typewriter at 60fps is just fast typing. A transporter
at 60fps might be spectacular. We generate and compare — the best goes in the gallery.

For each variant:
1. Generate frames (call the lambda)
2. Save `.apng` to `docs/anim_gallery/<id>-<label>.apng`
3. Save `.cast` to `docs/anim_gallery/<id>-<label>.cast`
4. Append entry to index README

---

## Gallery Structure

```
docs/anim_gallery/
  README.md                         ← auto-generated index
  A01-typewriter.apng
  A01-typewriter.cast
  A02-scanline.apng
  A02-scanline.cast
  A03-glitch.apng
  A03-glitch.cast
  A04-pulse.apng
  A04-pulse.cast
  A05-dissolve.apng
  A05-dissolve.cast
  A06-living-fill-cells.apng        ← Living Fill (CA variant)
  A06-living-fill-cells.cast
  A07-matrix-rain.apng
  A07-matrix-rain.cast
  A08-flame.apng
  A08-flame.cast
  A09-liquid-fill.apng
  A09-liquid-fill.cast
  A10-plasma-wave.apng
  A10-plasma-wave.cast
  A11-transporter-tng.apng          ← Transporter (TNG era)
  A11-transporter-tng.cast
  A11-transporter-tos.apng          ← Transporter (TOS era)
  A11-transporter-tos.cast
  A11-transporter-ent.apng          ← Transporter (ENT era — prototype feel)
  A11-transporter-ent.cast
```

---

## Auto-Generated README

`docs/anim_gallery/README.md` is fully generated — never hand-edited.

Structure per entry:
```markdown
## A11 — Transporter Materialize

| Variant | Preview | Cast |
|---------|---------|------|
| TNG | ![TNG](A11-transporter-tng.apng) | [▶ terminal](A11-transporter-tng.cast) |
| TOS | ![TOS](A11-transporter-tos.apng) | [▶ terminal](A11-transporter-tos.cast) |
| ENT | ![ENT](A11-transporter-ent.apng) | [▶ terminal](A11-transporter-ent.cast) |
```

The APNG embeds inline in GitHub. The `.cast` link opens in asciinema player
(when uploaded) or can be played locally with `asciinema play`.

---

## New Skill: `.claude/skills/regenerate-anim-gallery/SKILL.md`

```markdown
# Skill: regenerate-anim-gallery

Run the animation gallery generator and commit results.

## Steps

1. uv run python scripts/generate_anim_gallery.py
2. Check for errors — fix before committing
3. Spot-check: open 2-3 APNGs, confirm animation plays correctly
4. git add docs/anim_gallery/
5. git commit -m "docs: regenerate animation gallery"
6. git push

## Notes
- APNGs require Pillow (uv sync --dev installs it)
- .cast files require no deps
- Test phrase is always "ENERGIZE" for transporter variants
- Gallery takes ~2-3 minutes to generate all effects at 24fps
```

---

## CLI Integration

Add `--export-apng` and `--export-cast` flags to the animation CLI:

```bash
# Play in terminal (existing)
uv run python justdoit.py "ENERGIZE" --animate transporter --trek-era tng

# Export APNG
uv run python justdoit.py "ENERGIZE" --animate transporter --trek-era tng \
  --export-apng energize-tng.apng

# Export .cast
uv run python justdoit.py "ENERGIZE" --animate transporter --trek-era tng \
  --export-cast energize-tng.cast

# Export both
uv run python justdoit.py "ENERGIZE" --animate transporter --trek-era tng \
  --export-apng energize-tng.apng --export-cast energize-tng.cast
```

---

## Testing

### `tests/test_output_cast.py`

```python
def test_cast_header():
    """Output starts with valid asciinema v2 JSON header."""

def test_cast_frame_timestamps():
    """Frame timestamps increase monotonically at correct fps interval."""

def test_cast_roundtrip():
    """Frames survive cast serialization (content preserved)."""

def test_cast_auto_dimensions():
    """cols/rows auto-detected from frame content when not specified."""
```

### `tests/test_output_apng.py`

```python
@pytest.importorskip("PIL")
def test_apng_is_valid_png():
    """Output bytes start with PNG magic bytes."""

@pytest.importorskip("PIL")
def test_apng_frame_count():
    """APNG contains correct number of frames."""

@pytest.importorskip("PIL")
def test_apng_dimensions():
    """APNG dimensions match expected character grid size."""
```

---

## Implementation Order

| Step | Task | Deps | Est. complexity |
|------|------|------|----------------|
| 1 | `justdoit/output/cast.py` | None | Low |
| 2 | `tests/test_output_cast.py` | Step 1 | Low |
| 3 | `justdoit/output/apng.py` | Pillow | Medium |
| 4 | `tests/test_output_apng.py` | Step 3 | Low |
| 5 | `scripts/generate_anim_gallery.py` | Steps 1+3 | Medium |
| 6 | `docs/anim_gallery/` scaffolding | Step 5 | Low |
| 7 | `.claude/skills/regenerate-anim-gallery/SKILL.md` | Step 5 | Low |
| 8 | CLI `--export-apng` / `--export-cast` flags | Steps 1+3 | Medium |
| 9 | Update `CLAUDE.md` skills table | Step 7 | Trivial |

Steps 1–4 can ship before A11 (transporter) exists — use existing animation
effects (typewriter, glitch, pulse) as the first gallery entries.

Steps 5–9 deliver the full gallery pipeline.

A11 + SO02 (transporter + sound) become the flagship gallery showcase
once the pipeline is in place.

---

## Open Questions for Jonny

- [ ] **Loop behavior** — infinite loop or play-once-and-hold-last-frame in gallery?
  Recommendation: infinite for ambient effects (pulse, living fill), play-once
  for narrative effects (transporter materialize).
- [ ] **APNG background** — `#111111` terminal dark or transparent?
  Transparent looks great on dark docs, breaks on light backgrounds.
- [ ] **GitHub Pages** — is this the right long-term gallery home, or CO3DEX integration?
- [ ] **asciinema.org upload** — automated in gallery script or manual?

---

*"The line must be drawn here. This far, no further."*  
*— except for the animation gallery, which will go considerably further.*
