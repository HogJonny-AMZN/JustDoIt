"""
Package: justdoit.animate.presets
Animation preset generators for ASCII art.

Each function is a generator that yields frames (strings) for playback
via animate.player.play(). Presets operate on a fully-rendered string.

Implemented techniques:
  A01 — typewriter:  characters appear sequentially, left-to-right, row-by-row
  A02 — scanline:    text builds from top row to bottom, one row at a time
  A03 — glitch:      random character corruption that snaps back to the original
  A04 — pulse:       brightness/color oscillation via cycling ANSI color codes
  A05 — dissolve:    characters scatter and fade out on exit (reverse of typewriter)

All generators:
  - Accept a rendered multi-line string
  - Yield strings (frames) — one string per frame
  - Are pure Python stdlib — no external dependencies
  - Terminate naturally (finite frame count) unless noted
"""

import logging as _logging
import random
import re
from typing import Iterator, Optional

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.animate.presets"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_ANSI_RE = re.compile(r"(\033\[[0-9;]*m)")
_RESET = "\033[0m"

# Pulse color cycle — bright to dim, cycling ANSI codes
_PULSE_CYCLE: list = [
    "\033[97m",   # bright white
    "\033[37m",   # white
    "\033[2;37m", # dim white
    "\033[37m",   # white
]

# Glitch replacement chars — feel like corruption
_GLITCH_CHARS: str = "!@#$%^&*░▒▓█▀▄╔╗╚╝║═"


# -------------------------------------------------------------------------
def _visible_cells(text: str) -> list:
    """Extract (row, col, char) tuples for all visible non-space characters.

    ANSI sequences are ignored — only the visible character positions matter.

    :param text: Multi-line rendered string.
    :returns: List of (row_idx, col_idx, char) tuples.
    """
    cells = []
    for row_idx, line in enumerate(text.split("\n")):
        col_idx = 0
        i = 0
        while i < len(line):
            # Skip ANSI sequences
            m = _ANSI_RE.match(line, i)
            if m:
                i = m.end()
                continue
            ch = line[i]
            if ch != " ":
                cells.append((row_idx, col_idx, ch))
            col_idx += 1
            i += 1
    return cells


# -------------------------------------------------------------------------
def _blank_grid(text: str) -> list:
    """Build a 2D list of characters from a rendered string, stripping ANSI.

    :param text: Multi-line rendered string.
    :returns: 2D list[list[str]] — one sublist per row.
    """
    result = []
    for line in text.split("\n"):
        plain = _ANSI_RE.sub("", line)
        result.append(list(plain))
    return result


# -------------------------------------------------------------------------
def _grid_to_str(grid: list) -> str:
    """Convert a 2D character grid back to a multi-line string.

    :param grid: 2D list[list[str]] as produced by _blank_grid().
    :returns: Multi-line string with trailing spaces stripped per row.
    """
    return "\n".join("".join(row).rstrip() for row in grid)


# -------------------------------------------------------------------------
def typewriter(text: str, chars_per_frame: int = 3) -> Iterator[str]:
    """Reveal characters sequentially left-to-right, row-by-row (A01).

    Starts with a blank canvas and progressively reveals characters
    until the full text is displayed. Ends with one hold frame.

    :param text: Multi-line rendered string from render().
    :param chars_per_frame: How many characters to reveal per frame (default: 3).
    :returns: Iterator of frame strings.
    """
    if not text:
        yield text
        return

    lines = text.split("\n")
    # Strip ANSI for the display grid; we show plain chars
    grid = _blank_grid(text)
    n_rows = len(grid)
    n_cols = max(len(row) for row in grid) if grid else 0

    # Build ordered reveal sequence: all (row, col) positions left-to-right, top-to-bottom
    reveal_order = [
        (r, c)
        for r in range(n_rows)
        for c in range(n_cols)
        if c < len(grid[r]) and grid[r][c] != " "
    ]

    # Display grid starts blank
    display = [[" "] * max(len(row), n_cols) for row in grid]
    # Pad display rows to match grid
    for r in range(n_rows):
        display[r] = [" "] * max(len(grid[r]), 1)

    revealed = 0
    total = len(reveal_order)

    while revealed < total:
        batch_end = min(revealed + chars_per_frame, total)
        for r, c in reveal_order[revealed:batch_end]:
            if c < len(display[r]):
                display[r][c] = grid[r][c]
        revealed = batch_end
        yield _grid_to_str(display)

    # Hold the final complete frame
    yield _grid_to_str(display)


# -------------------------------------------------------------------------
def scanline(text: str, rows_per_frame: int = 1) -> Iterator[str]:
    """Reveal text row by row from top to bottom (A02).

    :param text: Multi-line rendered string from render().
    :param rows_per_frame: How many rows to reveal per frame (default: 1).
    :returns: Iterator of frame strings.
    """
    if not text:
        yield text
        return

    grid = _blank_grid(text)
    n_rows = len(grid)
    display = [[" "] * len(row) for row in grid]

    revealed_rows = 0
    while revealed_rows < n_rows:
        batch_end = min(revealed_rows + rows_per_frame, n_rows)
        for r in range(revealed_rows, batch_end):
            display[r] = grid[r][:]
        revealed_rows = batch_end
        yield _grid_to_str(display)

    # Hold final frame
    yield _grid_to_str(display)


# -------------------------------------------------------------------------
def glitch(
    text: str,
    n_frames: int = 20,
    intensity: float = 0.15,
    seed: Optional[int] = None,
) -> Iterator[str]:
    """Corrupt random characters then snap back (A03).

    Alternates between a glitched version and the clean original,
    with randomized corruption on each glitch frame.

    :param text: Multi-line rendered string from render().
    :param n_frames: Total number of frames to produce (default: 20).
    :param intensity: Fraction of ink characters to corrupt per glitch frame (default: 0.15).
    :param seed: Optional random seed for reproducibility.
    :returns: Iterator of frame strings.
    """
    if not text:
        yield text
        return

    rng = random.Random(seed)
    grid = _blank_grid(text)
    clean = _grid_to_str(grid)
    cells = [(r, c) for r in range(len(grid)) for c in range(len(grid[r])) if grid[r][c] != " "]
    n_corrupt = max(1, int(len(cells) * intensity))

    for i in range(n_frames):
        if i % 3 == 1:
            # Glitch frame: corrupt n_corrupt random cells
            g = [row[:] for row in grid]
            for r, c in rng.sample(cells, min(n_corrupt, len(cells))):
                g[r][c] = rng.choice(_GLITCH_CHARS)
            yield _grid_to_str(g)
        else:
            # Clean frame
            yield clean

    # End on the clean original
    yield clean


# -------------------------------------------------------------------------
def pulse(text: str, n_cycles: int = 3) -> Iterator[str]:
    """Oscillate brightness by cycling ANSI color codes (A04).

    Wraps each frame in a different ANSI intensity code, cycling
    through bright → normal → dim → normal → bright.

    :param text: Multi-line rendered string from render().
    :param n_cycles: Number of full brightness cycles (default: 3).
    :returns: Iterator of frame strings.
    """
    if not text:
        yield text
        return

    plain = re.sub(r"\033\[[0-9;]*m", "", text)
    n_steps = len(_PULSE_CYCLE)
    total_frames = n_cycles * n_steps

    for i in range(total_frames):
        code = _PULSE_CYCLE[i % n_steps]
        yield f"{code}{plain}{_RESET}"

    # End on default (no code)
    yield plain


# -------------------------------------------------------------------------
def dissolve(text: str, chars_per_frame: int = 3, seed: Optional[int] = None) -> Iterator[str]:
    """Scatter characters randomly until the canvas is blank (A05).

    Reverse of typewriter — removes characters in random order.
    Starts with the full text and ends with a blank canvas.

    :param text: Multi-line rendered string from render().
    :param chars_per_frame: How many characters to remove per frame (default: 3).
    :param seed: Optional random seed for reproducibility.
    :returns: Iterator of frame strings.
    """
    if not text:
        yield text
        return

    rng = random.Random(seed)
    grid = _blank_grid(text)
    display = [row[:] for row in grid]

    cells = [(r, c) for r in range(len(grid)) for c in range(len(grid[r])) if grid[r][c] != " "]
    rng.shuffle(cells)

    removed = 0
    total = len(cells)

    while removed < total:
        batch_end = min(removed + chars_per_frame, total)
        for r, c in cells[removed:batch_end]:
            if c < len(display[r]):
                display[r][c] = " "
        removed = batch_end
        yield _grid_to_str(display)

    # Final blank frame
    yield _grid_to_str(display)
