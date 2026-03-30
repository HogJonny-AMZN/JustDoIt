"""
Package: justdoit.animate.presets
Animation preset generators for ASCII art.

Each function is a generator that yields frames (strings) for playback
via animate.player.play(). Presets operate on a fully-rendered string.

Implemented techniques:
  A01 — typewriter:   characters appear sequentially, left-to-right, row-by-row
  A02 — scanline:     text builds from top row to bottom, one row at a time
  A03 — glitch:       random character corruption that snaps back to the original
  A03n — neon_glitch: neon sign flicker — color tubes dim/die, fringe to adjacent hues
  A04 — pulse:        brightness/color oscillation via cycling ANSI color codes
  A05 — dissolve:     characters scatter and fade out on exit (reverse of typewriter)

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


# -------------------------------------------------------------------------
# Neon color definitions — ANSI codes + dim variants + fringe neighbors
_NEON_COLORS: dict = {
    "cyan":    {"full": "\033[96m", "dim": "\033[2;96m", "off": "\033[2;34m",  "fringe": ["\033[94m", "\033[92m"]},
    "magenta": {"full": "\033[95m", "dim": "\033[2;95m", "off": "\033[2;35m",  "fringe": ["\033[91m", "\033[94m"]},
    "red":     {"full": "\033[91m", "dim": "\033[2;91m", "off": "\033[2;31m",  "fringe": ["\033[95m", "\033[93m"]},
    "yellow":  {"full": "\033[93m", "dim": "\033[2;93m", "off": "\033[2;33m",  "fringe": ["\033[92m", "\033[91m"]},
    "green":   {"full": "\033[92m", "dim": "\033[2;92m", "off": "\033[2;32m",  "fringe": ["\033[96m", "\033[93m"]},
    "blue":    {"full": "\033[94m", "dim": "\033[2;94m", "off": "\033[2;34m",  "fringe": ["\033[96m", "\033[95m"]},
}
_RESET = "\033[0m"


def _apply_neon_color(text: str, color_name: str, state: str, rng: random.Random) -> str:
    """Wrap a plain text string in neon ANSI codes based on tube state.

    States: 'full' (bright), 'dim' (flickering), 'off' (dead), 'fringe' (color bleed).

    :param text: Plain (ANSI-stripped) text to colorize.
    :param color_name: Key in _NEON_COLORS.
    :param state: One of 'full', 'dim', 'off', 'fringe'.
    :param rng: Random instance for fringe color selection.
    :returns: ANSI-wrapped string.
    """
    neon = _NEON_COLORS[color_name]
    if state == "fringe":
        code = rng.choice(neon["fringe"])
    else:
        code = neon[state]
    return f"{code}{text}{_RESET}"


def neon_tube_glitch(
    text: str,
    color: str = "cyan",
    n_frames: int = 36,
    flicker_prob: float = 0.20,
    dead_prob: float = 0.06,
    fringe_prob: float = 0.10,
    seed: Optional[int] = None,
) -> Iterator[str]:
    """Per-letter neon tube flicker — each letter is one bent tube (A03t).

    Each letter behaves as a single independent neon tube. The whole letter
    goes dim, dead, or fringe together — not horizontal row slices.
    Spaces between letters are always blank (no tube there).

    This is the authentic neon sign failure mode: a tube bent into a letter
    shape either works, flickers, or dies as a unit.

    :param text: Multi-line rendered string from render() — plain, no ANSI color.
    :param color: Neon tube color — key in _NEON_COLORS (default: 'cyan').
    :param n_frames: Total frames to produce (default: 36).
    :param flicker_prob: Probability of dim flicker per letter per frame (default: 0.20).
    :param dead_prob: Probability of tube death per letter per frame (default: 0.06).
    :param fringe_prob: Probability of color fringe per letter per frame (default: 0.10).
    :param seed: Optional random seed for reproducibility.
    :returns: Iterator of frame strings.
    :raises ValueError: If color is not a known neon color.
    """
    if color not in _NEON_COLORS:
        raise ValueError(f"Unknown neon color '{color}'. Available: {', '.join(_NEON_COLORS)}")

    if not text:
        yield text
        return

    from justdoit.fonts import FONTS

    # We need to know the column span of each source character so we can
    # apply per-letter state to the right columns in the rendered output.
    # Render each source char individually to get its column width.
    font_data = FONTS.get("block", {})
    gap = 1  # default gap used by render()

    # Strip ANSI from input — we re-color ourselves
    plain_lines = [_ANSI_RE.sub("", line) for line in text.split("\n")]
    n_rows = len(plain_lines)

    # Build letter column spans: for each source char, what column range does it occupy?
    # render() appends: glyph_cols + gap spacer, for each char in text.upper()
    source_chars = [c for c in text.upper()]
    col_spans: list[tuple[int, int]] = []  # (start_col, end_col) exclusive, per source char
    col = 0
    for ch in source_chars:
        glyph = font_data.get(ch, font_data.get(" "))
        if glyph is None:
            col_spans.append((col, col))
            continue
        glyph_width = len(glyph[0]) if glyph else 0
        span_end = col + glyph_width  # gap cols are blank, not part of the letter tube
        col_spans.append((col, span_end))
        col += glyph_width + gap  # advance past glyph + gap spacer

    rng = random.Random(seed)
    neon = _NEON_COLORS[color]

    for _ in range(n_frames):
        # Roll tube state per source character
        letter_states: list[str] = []
        for ch in source_chars:
            if ch == " ":
                letter_states.append("space")
                continue
            roll = rng.random()
            if roll < dead_prob:
                letter_states.append("off")
            elif roll < dead_prob + flicker_prob:
                letter_states.append("dim")
            elif roll < dead_prob + flicker_prob + fringe_prob:
                letter_states.append("fringe")
            else:
                letter_states.append("full")

        # Build frame row by row — colorize each letter's column span independently
        frame_lines = []
        for row_idx in range(n_rows):
            line = plain_lines[row_idx] if row_idx < len(plain_lines) else ""
            if not line.strip():
                frame_lines.append(line)
                continue

            # Rebuild line char by char, wrapping each letter span in its tube color
            result = []
            line_list = list(line)
            for letter_idx, (start, end) in enumerate(col_spans):
                state = letter_states[letter_idx]
                # Extract this letter's columns from the line
                seg = "".join(line_list[start:end]) if end <= len(line_list) else ""
                if not seg.strip() or state == "space":
                    result.append(seg)
                    continue
                if state == "fringe":
                    code = rng.choice(neon["fringe"])
                else:
                    code = neon[state]
                result.append(f"{code}{seg}{_RESET}")
            # Append anything after the last span (trailing gap/space)
            last_end = col_spans[-1][1] if col_spans else 0
            if last_end < len(line_list):
                result.append("".join(line_list[last_end:]))
            frame_lines.append("".join(result))

        yield "\n".join(frame_lines)


def neon_glitch(
    text: str,
    color: str = "cyan",
    n_frames: int = 30,
    flicker_prob: float = 0.25,
    dead_prob: float = 0.08,
    fringe_prob: float = 0.12,
    seed: Optional[int] = None,
) -> Iterator[str]:
    """Neon sign flicker effect — tubes dim, die, and bleed color (A03n).

    Operates on the whole text as a neon tube of a single color.
    Each frame independently rolls per-row tube state:
      - 'full'   — tube is on (most frames)
      - 'dim'    — tube flickers to half-brightness
      - 'off'    — tube is dead (dark)
      - 'fringe' — color bleeds to adjacent hue (electrical fringe)

    :param text: Multi-line rendered string from render().
    :param color: Neon tube color — key in _NEON_COLORS (default: 'cyan').
    :param n_frames: Total frames to produce (default: 30).
    :param flicker_prob: Probability of a dim flicker per row per frame (default: 0.25).
    :param dead_prob: Probability of a tube going dark per row per frame (default: 0.08).
    :param fringe_prob: Probability of color fringe per row per frame (default: 0.12).
    :param seed: Optional random seed for reproducibility.
    :returns: Iterator of frame strings.
    :raises ValueError: If color is not a known neon color.
    """
    if color not in _NEON_COLORS:
        raise ValueError(f"Unknown neon color '{color}'. Available: {', '.join(_NEON_COLORS)}")

    if not text:
        yield text
        return

    rng = random.Random(seed)
    plain_lines = [_ANSI_RE.sub("", line) for line in text.split("\n")]

    for _ in range(n_frames):
        frame_lines = []
        for line in plain_lines:
            if not line.strip():
                frame_lines.append(line)
                continue
            roll = rng.random()
            if roll < dead_prob:
                state = "off"
            elif roll < dead_prob + flicker_prob:
                state = "dim"
            elif roll < dead_prob + flicker_prob + fringe_prob:
                state = "fringe"
            else:
                state = "full"
            frame_lines.append(_apply_neon_color(line, color, state, rng))
        yield "\n".join(frame_lines)
