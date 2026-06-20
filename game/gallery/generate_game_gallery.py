"""
Package: game.gallery.generate_game_gallery
Game design visualization gallery for GLYPHSTER.

Generates animated APNGs showing zone aesthetics, Glyphster character forms,
room mockups, and UI elements — using JustDoIt's existing effect pipeline.

Run with:
    uv run python -m game.gallery.generate_game_gallery

Output: docs/game_gallery/
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# -------------------------------------------------------------------------
_MODULE_NAME = "game.gallery.generate_game_gallery"
__updated__  = "2026-05-01"
__version__  = "0.1.0"
__author__   = ["jGalloway"]

_LOGGER = logging.getLogger(_MODULE_NAME)

GALLERY_DIR = Path(__file__).parent.parent.parent / "docs" / "game_gallery"

# -------------------------------------------------------------------------
# Custom ASCII art content strings
# These are passed directly to pre-rendered-text presets (glitch, neon_glitch, etc.)
# -------------------------------------------------------------------------

_GLYPHSTER_START = """\
    ╲  │  ╱
     ╲─┼─╱
   ──(◆◆◆)──
     ╱─┼─╲
    ╱  │  ╲    """

_GLYPHSTER_MID = """\
  ◇  ╲  │  ╱  ◇
      ╲─┼─╱
  ───(◈◆◆◈)───
      ╱─┼─╲
  ◇  ╱  │  ╲  ◇  """

_GLYPHSTER_FULL = """\
╔═╗  ╲  │  ╱  ╔═╗
╚═╝   ╲─┼─╱   ╚═╝
   ◈(◉◆◉◆◉)◈
╔═╗   ╱─┼─╲   ╔═╗
╚═╝  ╱  │  ╲  ╚═╝"""

_CHARGE_STATES = """\
  ○   EMPTY    ·  ·  ·  ·    charge: 0/4
  ◌   LOW     [─] ·  ·  ·    charge: 1/4
  ◎   HALF    [─][─] ·  ·    charge: 2/4
  ◉   HIGH    [─][─][─] ·    charge: 3/4
  ⊛   FULL    [─][─][─][─]   charge: 4/4"""

_AIM_CURSORS = """\
  ⌖   THE TERMINAL    amber    legacy mainframe
  ◎   THE CONDUIT     cyan     network backbone
  ×   THE ROT         red      corrupted sector
  ◈   THE VAULT       blue     cold storage
  +   THE CORE        white    root process"""

_AIM_LINE_STATES = """\
  [empty]   · · · · · · · ◎
  [1 pip]   ─ · · · · · · ◎
  [2 pips]  ─ ─ · · · · · ◎
  [3 pips]  ─ ─ ─ · · · · ◎
  [  full]  ─ ─ ─ ─ ─ ─ ─ ◎"""

_TERMINAL_ROOM = """\
╔═══════════════════════════════════════════════╗
║ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ ║
║ ░░  ╔═══════════════╗  ░░░  [◆◆◆]  ░░░░░░░░ ║
║ ░░  ║ SYS//TERM-01  ║  ░░░░░░░░░░░░░░░░░░░░ ║
║ ░░  ║ > BOOT OK_    ║  ░░░░░░░░░░░░░░░░░░░░ ║
║ ░░  ╚═══════════════╝  ░░░░░░░░░░░░░░░░░░░░ ║
║ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ ║
╠══════════╦════════════════╦═══════════════════╣
║▓▓▓▓▓▓▓▓▓║░░░░░░░░░░░░░░░║▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓║
╚══════════╩════════════════╩═══════════════════╝"""

_CONDUIT_ROOM = """\
╔════╦══════════════════════════════════╦════╗
║    ║ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ ║    ║
╠════╣ ░░  ╔══════╗  ╔══╗  ╔══════╗  ░╠════╣
║    ║ ░░  ║ NODE ╠══╣  ╠══╣ NET  ║  ░║    ║
╠════╣ ░░  ╚══════╝  ╚══╝  ╚══════╝  ░╠════╣
║    ║ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ ║    ║
║    ╠════════════╦═════════════════╦══╝    ║
║    ║▓▓▓▓▓▓▓▓▓▓▓║▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓║       ║
╚════╩════════════╩═════════════════╝═══════╝"""

_WALL_ROOM = """\
╔══╦══╦══╦══╦══╦══╦══╦══╦══╦══╦══╦══╗
║  ║  ║░░║  ║  ║░░║  ║░░║  ║  ║  ║  ║
╠══╬══╬══╬══╬══╬══╬══╬══╬══╬══╬══╬══╣
║▓▓║  ║  ║  ║░░║  ║  ║  ║░░║  ║▓▓║  ║
╠══╬══╬══╬══╬══╬══╬══╬══╬══╬══╬══╬══╣
║  ║░░║  ║▓▓║  ║  ║░░║  ║  ║░░║  ║  ║
╠══╬══╬══╬══╬══╬══╬══╬══╬══╬══╬══╬══╣
║  ║  ║░░║  ║  ║[◆]  ║░░║  ║  ║  ║  ║
╚══╩══╩══╩══╩══╩══╩══╩══╩══╩══╩══╩══╝"""

# -------------------------------------------------------------------------
# ANSI color codes for spider walk-cycle coloring
# Parsed by justdoit.output.ansi_parser — bright codes 91–97 only.
_ESC   = "\033"
_A_RED = f"{_ESC}[91m"   # bright red   — core glyph ◆
_A_CYN = f"{_ESC}[96m"   # bright cyan  — legs/connectors ╲ │ ╱ ─ ┼ ╬
_A_WHT = f"{_ESC}[97m"   # white        — brackets ( )
_A_YLW = f"{_ESC}[93m"   # bright yellow — body orbs ◈ ◉
_A_MGT = f"{_ESC}[95m"   # magenta      — sigils ◇
_A_BLU = f"{_ESC}[94m"   # bright blue  — carapace ╔═╗ ╚═╝
_A_RST = f"{_ESC}[0m"    # reset


# -------------------------------------------------------------------------
def _walk_frames_start() -> list[str]:
    """5-frame walk cycle — Starting spider form with ANSI colors.

    Cycle: neutral → right-stride (middle /, outer-right backslash) → peak (all |)
           → left-stride (outer-left flips to /) → settle.

    :returns: List of 5 ANSI-colored frame strings.
    """
    R, C, W, X = _A_RED, _A_CYN, _A_WHT, _A_RST

    f0 = (  # neutral
        f"  {C}╲  │  ╱{X}\n"
        f"   {C}╲─┼─╱{X}\n"
        f"    {W}({X}{R}◆{X}{W}){X}\n"
        f"   {C}╱─┼─╲{X}\n"
        f"  {C}╱  │  ╲{X}"
    )
    f1 = (  # LEFT stays ╲, mid extends to /, RIGHT settles to |
        f"  {C}╲   /  |{X}\n"
        f"   {C}╲─┼──╱{X}\n"
        f"    {W}({X}{R}◆{X}{W}){X}\n"
        f"   {C}╱─┼──╲{X}\n"
        f"  {C}╱   \\  |{X}"
    )
    f2 = (  # LEFT=|, mid=|, RIGHT=\ — rear inner arm ends straighten to |
        f"  {C}|   |  \\{X}\n"
        f"   {C}╲──┼──|{X}\n"
        f"     {W}({X}{R}◆{X}{W}){X}\n"
        f"   {C}╱──┼──|{X}\n"
        f"  {C}|   |  /{X}"
    )
    f3 = (  # LEFT=/, mid=\, RIGHT=| — rear inner arm starts straighten to |
        f"  {C}/  \\  |{X}\n"
        f"  {C}|──┼─╱{X}\n"
        f"    {W}({X}{R}◆{X}{W}){X}\n"
        f"  {C}|──┼─╲{X}\n"
        f"  {C}\\  /  |{X}"
    )
    f4 = (  # LEFT=|, mid=|, RIGHT=╱ (right tip cycles ╱→|→\→|→╱)
        f"  {C}|  |  ╱{X}\n"
        f"  {C}╲──┼─╱{X}\n"
        f"    {W}({X}{R}◆{X}{W}){X}\n"
        f"  {C}╱──┼─╲{X}\n"
        f"  {C}|  |  ╲{X}"
    )
    return [f0, f1, f2, f3, f4]


# -------------------------------------------------------------------------
def _walk_frames_mid() -> list[str]:
    """5-frame walk cycle — Mid-game spider form (◇ sigil leg tips).

    ◇ sigils ride the outermost tips and extend/flip with them each frame.
    Mirrors the scratch.md 5-frame pattern.

    :returns: List of 5 ANSI-colored frame strings.
    """
    R, C, W, Y, M, X = _A_RED, _A_CYN, _A_WHT, _A_YLW, _A_MGT, _A_RST

    f0 = (  # neutral — form at base position +2
        f"  {M}◇{X}{C}╲  │  ╱{X}{M}◇{X}\n"
        f"    {C}╲─┼─╱{X}\n"
        f"    {W}({X}{Y}◈{X}{R}◆{X}{Y}◈{X}{W}){X}\n"
        f"    {C}╱─┼─╲{X}\n"
        f"  {M}◇{X}{C}╱  │  ╲{X}{M}◇{X}"
    )
    f1 = (  # LEFT stays ╲, mid /, RIGHT=| — stride lunge adds +1 (total +3)
        f"   {M}◇{X}{C}╲   /  |{X}{M}◇{X}\n"
        f"     {C}╲─┼──╱{X}\n"
        f"     {W}({X}{Y}◈{X}{R}◆{X}{Y}◈{X}{W}){X}\n"
        f"     {C}╱─┼──╲{X}\n"
        f"   {M}◇{X}{C}╱   \\  |{X}{M}◇{X}"
    )
    f2 = (  # LEFT=|, mid=|, RIGHT=\ — rear inner arm ends straighten to |
        f"   {M}◇{X}{C}|   |  \\{X}{M}◇{X}\n"
        f"     {C}╲──┼──|{X}\n"
        f"      {W}({X}{Y}◈{X}{R}◆{X}{Y}◈{X}{W}){X}\n"
        f"     {C}╱──┼──|{X}\n"
        f"   {M}◇{X}{C}|   |  /{X}{M}◇{X}"
    )
    f3 = (  # LEFT=/, mid=\, RIGHT=| — rear inner arm starts straighten to |
        f"  {M}◇{X}{C}/  \\  |{X}{M}◇{X}\n"
        f"   {C}|──┼─╱{X}\n"
        f"    {W}({X}{Y}◈{X}{R}◆{X}{Y}◈{X}{W}){X}\n"
        f"   {C}|──┼─╲{X}\n"
        f"  {M}◇{X}{C}\\  /  |{X}{M}◇{X}"
    )
    f4 = (  # LEFT=|, mid=|, RIGHT=╱ — settled at base +2
        f"  {M}◇{X}{C}|  |  ╱{X}{M}◇{X}\n"
        f"   {C}╲──┼─╱{X}\n"
        f"    {W}({X}{Y}◈{X}{R}◆{X}{Y}◈{X}{W}){X}\n"
        f"   {C}╱──┼─╲{X}\n"
        f"  {M}◇{X}{C}|  |  ╲{X}{M}◇{X}"
    )
    return [f0, f1, f2, f3, f4]


# -------------------------------------------------------------------------
def _walk_frames_full() -> list[str]:
    """5-frame walk cycle — Full Progression form (carapace + ◉ core + ◈ junctions).

    Carapace pins outer ◇ tips — inner ╲/╱ chars change direction in place.
    Mirrors the scratch.md 5-frame pattern: neutral → right-stride → peak (all |)
    → left-stride (╲ inside carapace flips to /) → settle.

    :returns: List of 5 ANSI-colored frame strings.
    """
    R, C, W, Y, M, B, X = _A_RED, _A_CYN, _A_WHT, _A_YLW, _A_MGT, _A_BLU, _A_RST

    f0 = (  # neutral — ◈ at col3, ╬ at col6, ◆ at col6
        f"{B}╔═{X}{M}◇{X}{C}╲  │  ╱{X}{M}◇{X}{B}═╗{X}\n"
        f"   {Y}◈{X}{C}╲─╬─╱{X}{Y}◈{X}\n"
        f"    {W}({X}{Y}◉{X}{R}◆{X}{Y}◉{X}{W}){X}\n"
        f"   {Y}◈{X}{C}╱─╬─╲{X}{Y}◈{X}\n"
        f"{B}╚═{X}{M}◇{X}{C}╱  │  ╲{X}{M}◇{X}{B}═╝{X}"
    )
    f1 = (  # LEFT stays ╲, mid /, RIGHT=| — right arm extends to carapace ◇
        f"{B}╔═{X}{M}◇{X}{C}╲   /  |{X}{M}◇{X}{B}═╗{X}\n"
        f"   {Y}◈{X}{C}╲─╬──╱{X}{Y}◈{X}\n"
        f"    {W}({X}{Y}◉{X}{R}◆{X}{Y}◉{X}{W}){X}\n"
        f"   {Y}◈{X}{C}╱─╬──╲{X}{Y}◈{X}\n"
        f"{B}╚═{X}{M}◇{X}{C}╱   \\  |{X}{M}◇{X}{B}═╝{X}"
    )
    f2 = (  # LEFT=|, mid=|, RIGHT=\ — rear inner arm ends straighten to |
        f"{B}╔═{X}{M}◇{X}{C}|   |  \\{X}{M}◇{X}{B}═╗{X}\n"
        f"   {Y}◈{X}{C}╲──╬─|{X}{Y}◈{X}\n"
        f"     {W}({X}{Y}◉{X}{R}◆{X}{Y}◉{X}{W}){X}\n"
        f"   {Y}◈{X}{C}╱──╬─|{X}{Y}◈{X}\n"
        f"{B}╚═{X}{M}◇{X}{C}|   |  /{X}{M}◇{X}{B}═╝{X}"
    )
    f3 = (  # LEFT=/, mid=\, RIGHT=| — rear inner arm starts straighten to |
        f"{B}╔═{X}{M}◇{X}{C}/  \\  |{X}{M}◇{X}{B}═╗{X}\n"
        f"  {Y}◈{X}{C}|──╬─╱{X}{Y}◈{X}\n"
        f"    {W}({X}{Y}◉{X}{R}◆{X}{Y}◉{X}{W}){X}\n"
        f"  {Y}◈{X}{C}|──╬─╲{X}{Y}◈{X}\n"
        f"{B}╚═{X}{M}◇{X}{C}\\  /  |{X}{M}◇{X}{B}═╝{X}"
    )
    f4 = (  # LEFT=|, mid=|, RIGHT=╱ — inner same as f3
        f"{B}╔═{X}{M}◇{X}{C}|  |  ╱{X}{M}◇{X}{B}═╗{X}\n"
        f"  {Y}◈{X}{C}╲──╬─╱{X}{Y}◈{X}\n"
        f"    {W}({X}{Y}◉{X}{R}◆{X}{Y}◉{X}{W}){X}\n"
        f"  {Y}◈{X}{C}╱──╬─╲{X}{Y}◈{X}\n"
        f"{B}╚═{X}{M}◇{X}{C}|  |  ╲{X}{M}◇{X}{B}═╝{X}"
    )
    return [f0, f1, f2, f3, f4]


# -------------------------------------------------------------------------
def _build_entries() -> list[dict]:
    """Build the declarative gallery entry list.

    Each entry: id, category, name, label, description, frames (callable → list[str]), fps, loop.

    :returns: List of gallery entry dicts.
    """
    from justdoit.core.rasterizer import render
    from justdoit.animate.presets import (
        typewriter,
        scanline,
        glitch,
        pulse,
        density_dissolve,
        neon_glitch,
        neon_tube_glitch,
        neon_word_glitch,
        neon_sign_startup,
        living_fill,
        plasma_wave,
        flame_bloom,
        turing_bio,
        turing_warp,
        flame_iso_bloom,
    )

    # Pre-render zone names using block font — used with string-operation presets
    t_glyphster = render("GLYPHSTER",   font="block")
    t_rot       = render("THE ROT",     font="block")
    t_core      = render("THE CORE",    font="block")

    # Plain-text versions for image-pipeline presets that re-render internally
    p_mesh      = "THE MESH"
    p_terminal  = "TERMINAL"
    p_conduit   = "CONDUIT"
    p_rot       = "THE ROT"
    p_vault     = "THE VAULT"

    return [

        # ── GLYPHSTER CHARACTER ──────────────────────────────────────────────

        {
            "id": "G01", "category": "Glyphster",
            "name": "glyphster-title",
            "label": "GLYPHSTER — Living Fill",
            "description": "Conway's Game of Life grows inside the letterforms. The entity is alive.",
            "frames": lambda: list(living_fill("GLYPHSTER", n_frames=48)),
            "fps": 8.0, "loop": True,
        },
        {
            "id": "G02", "category": "Glyphster",
            "name": "glyphster-density",
            "label": "GLYPHSTER — Materialize",
            "description": "Density dissolve: the entity assembles from scattered glyph noise into solid form.",
            "frames": lambda: list(density_dissolve(t_glyphster, n_frames=40, direction="loop", color="cyan", seed=7)),
            "fps": 12.0, "loop": True,
        },
        {
            "id": "G03", "category": "Glyphster",
            "name": "glyphster-start-form",
            "label": "Spider Form — Starting",
            "description": "Compact core, 8 legs. The rogue process awakens.",
            "frames": lambda: list(neon_glitch(_GLYPHSTER_START, color="cyan", n_frames=36, seed=1)),
            "fps": 10.0, "loop": True,
        },
        {
            "id": "G04", "category": "Glyphster",
            "name": "glyphster-mid-form",
            "label": "Spider Form — Mid-Game",
            "description": "Orbital sigils appear. Two abilities unlocked. The form grows.",
            "frames": lambda: list(neon_tube_glitch(_GLYPHSTER_MID, color="magenta", n_frames=36, seed=3)),
            "fps": 10.0, "loop": True,
        },
        {
            "id": "G05", "category": "Glyphster",
            "name": "glyphster-full-form",
            "label": "Spider Form — Full Progression",
            "description": "Carapace formed. All abilities active. The character sheet is complete.",
            "frames": lambda: list(neon_glitch(_GLYPHSTER_FULL, color="yellow", n_frames=36, seed=7)),
            "fps": 10.0, "loop": True,
        },
        {
            "id": "G06", "category": "Glyphster",
            "name": "glyphster-start-dissolve",
            "label": "Spider Form — Materialize",
            "description": "Density dissolve: the entity assembles from scattered glyph noise.",
            "frames": lambda: list(density_dissolve(_GLYPHSTER_START, n_frames=40, direction="loop", color="cyan", seed=42)),
            "fps": 12.0, "loop": True,
        },

        # ── WALK CYCLES ──────────────────────────────────────────────────────

        {
            "id": "W01", "category": "Walk",
            "name": "walk-start",
            "label": "Walk Cycle — Starting Form",
            "description": "5-frame stride. Red core, cyan legs. The compact rogue process begins to move.",
            "frames": _walk_frames_start,
            "fps": 8.0, "loop": True,
        },
        {
            "id": "W02", "category": "Walk",
            "name": "walk-mid",
            "label": "Walk Cycle — Mid-Game Form",
            "description": "5-frame stride with ◇ sigil tips. Two abilities online. The form has presence.",
            "frames": _walk_frames_mid,
            "fps": 8.0, "loop": True,
        },
        {
            "id": "W03", "category": "Walk",
            "name": "walk-full",
            "label": "Walk Cycle — Full Progression",
            "description": "5-frame stride. Carapace active. ◉ core, ◈ junctions, ◇ sigils. Full entity.",
            "frames": _walk_frames_full,
            "fps": 8.0, "loop": True,
        },

        # ── ZONE AESTHETICS ──────────────────────────────────────────────────

        {
            "id": "Z01", "category": "Zone",
            "name": "zone-the-mesh",
            "label": "THE MESH — World Title",
            "description": "The dying distributed system. The world Glyphster crawls through.",
            "frames": lambda: list(neon_word_glitch(p_mesh, colors=["cyan", "magenta", "yellow"], n_frames=48, seed=7)),
            "fps": 12.0, "loop": True,
        },
        {
            "id": "Z02", "category": "Zone",
            "name": "zone-terminal",
            "label": "Zone 1 — THE TERMINAL",
            "description": "Legacy mainframe. Amber phosphor. The entry point. Old and slow and sure.",
            "frames": lambda: list(neon_sign_startup(
                p_terminal, color="yellow",
                faulty_word_idx=0, n_flickers=4,
                hold_frames=16, pulse=True, flicker_hold=True, seed=11,
            )),
            "fps": 12.0, "loop": True,
        },
        {
            "id": "Z03", "category": "Zone",
            "name": "zone-conduit",
            "label": "Zone 2 — THE CONDUIT",
            "description": "Network backbone. Data in motion. Bloom + chromatic aberration.",
            "frames": lambda: list(plasma_wave(p_conduit, n_frames=36, preset="tight", color="cyan", loop=True)),
            "fps": 12.0, "loop": True,
        },
        {
            "id": "Z04", "category": "Zone",
            "name": "zone-rot",
            "label": "Zone 3 — THE ROT",
            "description": "Corrupted sector. Turing decay spreads through every surface.",
            "frames": lambda: list(turing_bio(p_rot, preset="spots", seed=42, n_frames=36, palette_name="bio", loop=True)),
            "fps": 10.0, "loop": True,
        },
        {
            "id": "Z04b", "category": "Zone",
            "name": "zone-rot-glitch",
            "label": "Zone 3 — THE ROT (Glitch)",
            "description": "High-intensity character corruption — the system cannot hold its own memory.",
            "frames": lambda: list(glitch(t_rot, n_frames=30, intensity=0.35, seed=99)),
            "fps": 18.0, "loop": True,
        },
        {
            "id": "Z05", "category": "Zone",
            "name": "zone-vault",
            "label": "Zone 4 — THE VAULT",
            "description": "Encrypted cold storage. Overdriven bloom. Deep darkness.",
            "frames": lambda: list(flame_iso_bloom(p_vault, n_frames=36, loop=True)),
            "fps": 12.0, "loop": True,
        },
        {
            "id": "Z06", "category": "Zone",
            "name": "zone-core",
            "label": "Zone 5 — THE CORE",
            "description": "No post-process. No decay. Raw and real. The most unsettling room.",
            "frames": lambda: list(density_dissolve(t_core, n_frames=36, direction="loop", seed=13)),
            "fps": 8.0, "loop": True,
        },

        # ── ROOM MOCKUPS ─────────────────────────────────────────────────────

        {
            "id": "R01", "category": "Room",
            "name": "room-terminal",
            "label": "Room — Terminal (floor plan)",
            "description": "Standard gravity room. Amber CRT. Platform below, display terminals above.",
            "frames": lambda: list(neon_glitch(_TERMINAL_ROOM, color="yellow", n_frames=30, seed=5)),
            "fps": 8.0, "loop": True,
        },
        {
            "id": "R02", "category": "Room",
            "name": "room-conduit",
            "label": "Room — Conduit (floor plan)",
            "description": "Standard gravity room. Network nodes on platforms. Physarum growth on walls.",
            "frames": lambda: list(neon_tube_glitch(_CONDUIT_ROOM, color="cyan", n_frames=30, seed=3)),
            "fps": 8.0, "loop": True,
        },
        {
            "id": "R03", "category": "Room",
            "name": "room-wall",
            "label": "Room — Wall-Room (gravity 90°)",
            "description": "Gravity rotated. Conduit paths become floors. Junction boxes become platforms.",
            "frames": lambda: list(neon_tube_glitch(_WALL_ROOM, color="magenta", n_frames=30, seed=8)),
            "fps": 8.0, "loop": True,
        },

        # ── GLYPH-GROWTH (wall sub-layer simulations) ────────────────────────

        {
            "id": "GG01", "category": "GlyphGrowth",
            "name": "growth-terminal-gol",
            "label": "Glyph-Growth — Terminal (Conway GoL)",
            "description": "Zone 1 wall sub-layer: slow Conway's Game of Life — data age.",
            "frames": lambda: list(living_fill("TERMINAL", n_frames=48)),
            "fps": 6.0, "loop": True,
        },
        {
            "id": "GG02", "category": "GlyphGrowth",
            "name": "growth-conduit-plasma",
            "label": "Glyph-Growth — Conduit (Plasma Wave)",
            "description": "Zone 2 wall sub-layer: Physarum-style live routing simulation.",
            "frames": lambda: list(plasma_wave(p_conduit, n_frames=36, preset="tight", color="cyan", loop=True)),
            "fps": 12.0, "loop": True,
        },
        {
            "id": "GG03", "category": "GlyphGrowth",
            "name": "growth-rot-turing",
            "label": "Glyph-Growth — The Rot (Turing FHN)",
            "description": "Zone 3 wall sub-layer: Turing reaction-diffusion spots — spreading corruption.",
            "frames": lambda: list(turing_bio(p_rot, preset="spots", seed=77, n_frames=48, palette_name="bio", loop=True)),
            "fps": 8.0, "loop": True,
        },
        {
            "id": "GG04", "category": "GlyphGrowth",
            "name": "growth-rot-turing-warp",
            "label": "Glyph-Growth — The Rot (Turing + Warp)",
            "description": "Zone 3 advanced: Turing pattern warped — the corruption bends space.",
            "frames": lambda: list(turing_warp(p_rot, n_frames=36, palette_name="bio", loop=True)),
            "fps": 10.0, "loop": True,
        },
        {
            "id": "GG05", "category": "GlyphGrowth",
            "name": "growth-vault-flame",
            "label": "Glyph-Growth — Vault (Flame Bloom)",
            "description": "Zone 4 wall sub-layer: flame bloom — deep light leaking through cold storage.",
            "frames": lambda: list(flame_bloom(p_vault, n_frames=24, preset="hot", loop=True)),
            "fps": 12.0, "loop": True,
        },

        # ── UI / AIM SYSTEM ──────────────────────────────────────────────────

        {
            "id": "U01", "category": "UI",
            "name": "ui-aim-cursors",
            "label": "Aim Cursors — Zone Variants",
            "description": "⌖ amber · ◎ cyan · × red · ◈ blue · + white. The cursor IS the aim.",
            "frames": lambda: list(scanline(_AIM_CURSORS)),
            "fps": 3.0, "loop": False,
        },
        {
            "id": "U02", "category": "UI",
            "name": "ui-aim-line",
            "label": "Aim Line — Charge States",
            "description": "· · · ◎ at 30% alpha → ─────◎ at 100%. No HUD — the line tells everything.",
            "frames": lambda: list(typewriter(_AIM_LINE_STATES, chars_per_frame=2)),
            "fps": 8.0, "loop": False,
        },
        {
            "id": "U03", "category": "UI",
            "name": "ui-charge-pips",
            "label": "Charge Pips — Core Glyph States",
            "description": "○ ◌ ◎ ◉ ⊛ — the charge meter lives in the body itself. No HUD bar anywhere.",
            "frames": lambda: list(typewriter(_CHARGE_STATES, chars_per_frame=3)),
            "fps": 6.0, "loop": False,
        },
        {
            "id": "U04", "category": "UI",
            "name": "ui-charge-pulse",
            "label": "Charge Pips — Full Charge Pulse",
            "description": "Core overbrightens at ⊛ full charge. The body signals readiness.",
            "frames": lambda: list(pulse(_CHARGE_STATES, n_cycles=4)),
            "fps": 12.0, "loop": True,
        },
    ]


# -------------------------------------------------------------------------
def _write_readme(entries: list[dict], generated_at: str) -> None:
    """Write the gallery README.md with embedded APNGs.

    :param entries: Processed entry dicts (with 'apng_path' added).
    :param generated_at: ISO timestamp string.
    """
    lines: list[str] = []
    lines += [
        "# GLYPHSTER — Visualization Gallery",
        "",
        "Game design visualization for the **GLYPHSTER** ASCII metroidvania.  ",
        f"Generated: {generated_at}  ",
        "Script: `game/gallery/generate_game_gallery.py`",
        "",
        "---",
        "",
    ]

    categories = [
        ("Glyphster",   "Glyphster Character"),
        ("Walk",        "Walk Cycles"),
        ("Zone",        "Zone Aesthetics"),
        ("Room",        "Room Mockups"),
        ("GlyphGrowth", "Glyph-Growth Sub-Layers"),
        ("UI",          "UI / Aim System"),
    ]

    for cat_key, cat_label in categories:
        cat_entries = [e for e in entries if e["category"] == cat_key]
        if not cat_entries:
            continue

        lines += [f"## {cat_label}", ""]

        for i in range(0, len(cat_entries), 2):
            pair = cat_entries[i:i + 2]
            if len(pair) == 2:
                lines += [
                    "| | |",
                    "|---|---|",
                    f"| ![{pair[0]['id']}]({pair[0]['apng_name']}) | ![{pair[1]['id']}]({pair[1]['apng_name']}) |",
                    f"| **{pair[0]['label']}** | **{pair[1]['label']}** |",
                    f"| {pair[0]['description']} | {pair[1]['description']} |",
                    "",
                ]
            else:
                e = pair[0]
                lines += [
                    "| |",
                    "|---|",
                    f"| ![{e['id']}]({e['apng_name']}) |",
                    f"| **{e['label']}** |",
                    f"| {e['description']} |",
                    "",
                ]

        lines.append("---")
        lines.append("")

    readme = GALLERY_DIR / "README.md"
    readme.write_text("\n".join(lines), encoding="utf-8")
    _LOGGER.info("README written → %s", readme)


# -------------------------------------------------------------------------
def main() -> None:
    """Generate all gallery APNGs and write README.md."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

    try:
        from justdoit.output.apng import save_apng
    except ImportError as exc:
        _LOGGER.error("Pillow required for APNG output — run: uv sync --dev\n%s", exc)
        raise SystemExit(1) from exc

    GALLERY_DIR.mkdir(parents=True, exist_ok=True)

    _LOGGER.info("Building gallery entries…")
    entries = _build_entries()

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ok = 0
    fail = 0

    for entry in entries:
        apng_name = f"{entry['id']}-{entry['name']}.apng"
        apng_path = GALLERY_DIR / apng_name
        entry["apng_name"] = apng_name
        entry["apng_path"] = apng_path

        _LOGGER.info("[%s] %s — generating frames…", entry["id"], entry["label"])
        try:
            frames = entry["frames"]()
            save_apng(frames, apng_path, fps=entry["fps"], loop=0 if entry["loop"] else 1)
            _LOGGER.info("[%s] saved %d frames → %s", entry["id"], len(frames), apng_path.name)
            ok += 1
        except Exception as exc:
            _LOGGER.error("[%s] FAILED: %s", entry["id"], exc)
            fail += 1
            entry["apng_name"] = f"(failed: {entry['id']})"

    _write_readme(entries, generated_at)
    _LOGGER.info("Done — %d OK, %d failed. Gallery: %s", ok, fail, GALLERY_DIR)


# -------------------------------------------------------------------------
if __name__ == "__main__":
    main()
