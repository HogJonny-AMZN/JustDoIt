"""
Package: scripts.demo_animate
Animation showcase for JustDoIt — runs each preset sequentially.

Keeps animations in their own script so they don't overwrite the
static technique output from scripts/demo.py.

Run with:
    .venv/bin/python scripts/demo_animate.py
    .venv/bin/python scripts/demo_animate.py "CO3DEX"
    .venv/bin/python scripts/demo_animate.py --fps 20
    .venv/bin/python scripts/demo_animate.py --loop    # loop each animation; Ctrl+C to advance

Each animation plays fully, then pauses briefly before the next one starts.
Press Ctrl+C during any animation to skip to the next.
"""

import argparse
import logging as _logging
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "scripts.demo_animate"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_DIM    = "\033[2m"
_HEADER = "\033[38;2;80;220;220m"
_SEP    = "\033[38;2;60;60;80m"


# -------------------------------------------------------------------------
def _header(label: str, desc: str) -> None:
    print(f"\n{_SEP}{'─' * 60}{_RESET}")
    print(f"{_BOLD}{_HEADER}{label}{_RESET}  {_DIM}{desc}{_RESET}")
    print(f"{_SEP}{'─' * 60}{_RESET}")


# -------------------------------------------------------------------------
def _play_one(label: str, desc: str, frames, fps: float, loop: bool) -> None:
    """Print header and play one animation, catching Ctrl+C to skip.

    :param label: Technique label for the header.
    :param desc: Short description for the header.
    :param frames: Iterator/generator yielding frame strings.
    :param fps: Playback speed.
    :param loop: Whether to loop the animation until Ctrl+C.
    """
    from justdoit.animate.player import play
    _header(label, desc)
    try:
        play(frames, fps=fps, loop=loop)
    except KeyboardInterrupt:
        pass
    # Brief pause so the final frame stays visible before next header
    time.sleep(0.4)


# -------------------------------------------------------------------------
def run(text: str = "CO3DEX", fps: float = 12.0, loop: bool = False) -> None:
    """Play all animation presets in sequence.

    :param text: Text to render (default: 'CO3DEX').
    :param fps: Playback speed in frames per second (default: 12.0).
    :param loop: If True, loop each animation until Ctrl+C before advancing.
    """
    from justdoit.core.rasterizer import render
    from justdoit.effects.gradient import linear_gradient, per_glyph_palette, parse_color, PRESETS
    from justdoit.effects.isometric import isometric_extrude
    from justdoit.animate.presets import typewriter, scanline, glitch, pulse, dissolve

    plain = render(text, font="block")
    iso   = isometric_extrude(plain, depth=3)
    grad  = linear_gradient(plain, parse_color("gold"), parse_color("cyan"), direction="horizontal")
    neon  = per_glyph_palette(plain, PRESETS["neon"])

    loop_hint = "Ctrl+C to advance" if loop else ""

    # ------------------------------------------------------------------
    _play_one(
        "A01  typewriter",
        f"characters appear left-to-right  {loop_hint}",
        typewriter(plain, chars_per_frame=3),
        fps=fps, loop=loop,
    )

    # ------------------------------------------------------------------
    _play_one(
        "A02  scanline",
        f"text builds top to bottom  {loop_hint}",
        scanline(plain, rows_per_frame=1),
        fps=fps * 0.7, loop=loop,
    )

    # ------------------------------------------------------------------
    _play_one(
        "A03  glitch",
        f"random corruption, snaps back  {loop_hint}",
        glitch(plain, n_frames=24, intensity=0.3, seed=42),
        fps=fps, loop=loop,
    )

    # ------------------------------------------------------------------
    _play_one(
        "A03  glitch (on gradient)",
        f"corruption over true-color gradient  {loop_hint}",
        glitch(grad, n_frames=24, intensity=0.3, seed=7),
        fps=fps, loop=loop,
    )

    # ------------------------------------------------------------------
    _play_one(
        "A04  pulse",
        f"brightness oscillation  {loop_hint}",
        pulse(plain, n_cycles=3),
        fps=fps * 0.8, loop=loop,
    )

    # ------------------------------------------------------------------
    _play_one(
        "A04  pulse (neon palette)",
        f"neon palette cycling  {loop_hint}",
        pulse(neon, n_cycles=3),
        fps=fps * 0.8, loop=loop,
    )

    # ------------------------------------------------------------------
    _play_one(
        "A05  dissolve",
        f"characters scatter and fade out  {loop_hint}",
        dissolve(plain, chars_per_frame=4, seed=0),
        fps=fps * 1.5, loop=loop,
    )

    # ------------------------------------------------------------------
    _play_one(
        "A01  typewriter (iso + gradient)",
        f"typewriter reveal on isometric 3D with gold→red gradient  {loop_hint}",
        typewriter(
            linear_gradient(iso, parse_color("gold"), parse_color("red"), direction="vertical"),
            chars_per_frame=4,
        ),
        fps=fps * 1.5, loop=loop,
    )

    # ------------------------------------------------------------------
    _play_one(
        "A03  glitch (iso)",
        f"glitch on isometric 3D  {loop_hint}",
        glitch(iso, n_frames=24, intensity=0.2, seed=99),
        fps=fps, loop=loop,
    )

    # ------------------------------------------------------------------
    print(f"\n{_SEP}{'─' * 60}{_RESET}")
    print(f"{_BOLD}{_HEADER}Animation showcase complete.{_RESET}\n")


# -------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="JustDoIt animation showcase — all presets in sequence.",
    )
    parser.add_argument(
        "text", nargs="?", default="CO3DEX",
        help="Text to render (default: CO3DEX)",
    )
    parser.add_argument(
        "--fps", type=float, default=12.0,
        help="Playback speed in frames per second (default: 12)",
    )
    parser.add_argument(
        "--loop", action="store_true",
        help="Loop each animation until Ctrl+C before advancing to the next",
    )
    args = parser.parse_args()
    run(text=args.text.upper(), fps=args.fps, loop=args.loop)
