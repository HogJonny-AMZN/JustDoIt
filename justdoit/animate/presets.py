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
# Density-weighted dissolve character scale — light scatter to full block
# Each step represents increasing "mass" / fill density
_DENSITY_SCALE: list[str] = [" ", ".", ":", "+", "*", "%", "#", "▓", "█"]
_DENSITY_LEN: int = len(_DENSITY_SCALE)  # 9 steps


def density_dissolve(
    text: str,
    n_frames: int = 40,
    stagger: float = 0.6,
    direction: str = "in",
    color: Optional[str] = None,
    seed: Optional[int] = None,
) -> Iterator[str]:
    """Density-weighted dissolve — cells materialize through character weight (A05d).

    Each ink cell transitions independently through a density scale:
      ' ' → '.' → ':' → '+' → '*' → '%' → '#' → '▓' → '█'

    Cells start at random offsets in the animation so they don't all
    move together — matter assembles from scattered noise into solid form.

    direction='in':  space → full block (materialize)
    direction='out': full block → space (dematerialize)
    direction='loop': in then out, suitable for looping APNG

    :param text: Multi-line rendered string from render().
    :param n_frames: Total frames for one in or out pass (default: 40).
    :param stagger: Fraction of n_frames used as random start offset range (default: 0.6).
                   Higher = more scattered/chaotic arrival. 0 = all cells move together.
    :param direction: 'in', 'out', or 'loop' (default: 'in').
    :param color: Optional ANSI color name to apply to ink cells (default: None).
    :param seed: Optional random seed for reproducibility.
    :returns: Iterator of frame strings.
    """
    if not text:
        yield text
        return

    rng = random.Random(seed)
    grid = _blank_grid(text)
    n_rows = len(grid)
    n_cols = max(len(row) for row in grid) if grid else 0

    # All ink cell positions
    ink_cells = [
        (r, c)
        for r in range(n_rows)
        for c in range(len(grid[r]))
        if grid[r][c] != " "
    ]

    if not ink_cells:
        yield text
        return

    # Assign random start offset per cell — controls when each cell begins transitioning
    max_stagger = int(n_frames * stagger)
    cell_offsets: dict[tuple, int] = {
        cell: rng.randint(0, max(0, max_stagger)) for cell in ink_cells
    }

    def _build_frame(frame_idx: int, reverse: bool = False) -> str:
        """Build one frame of the density transition.

        :param frame_idx: Current frame index (0-based).
        :param reverse: If True, transition runs block→space instead of space→block.
        :returns: Multi-line frame string.
        """
        display = [[" "] * max(len(row), 1) for row in grid]
        # Pad display rows
        for r in range(n_rows):
            display[r] = list(grid[r]) if not reverse else [" "] * len(grid[r])

        for (r, c) in ink_cells:
            offset = cell_offsets[(r, c)]
            # How far into this cell's transition are we?
            local_frame = frame_idx - offset
            if local_frame < 0:
                step = 0 if not reverse else _DENSITY_LEN - 1
            else:
                # Map local_frame → density step
                progress = min(1.0, local_frame / max(1, n_frames - max_stagger))
                if reverse:
                    step = int((1.0 - progress) * (_DENSITY_LEN - 1))
                else:
                    step = int(progress * (_DENSITY_LEN - 1))
            ch = _DENSITY_SCALE[step]
            if c < len(display[r]):
                display[r][c] = ch

        rows_out = []
        for row in display:
            line = "".join(row).rstrip()
            if color:
                # Apply color only to non-space chars
                colored = ""
                from justdoit.effects.color import colorize, COLORS
                for ch in line:
                    if ch != " ":
                        colored += colorize(ch, color)
                    else:
                        colored += ch
                rows_out.append(colored)
            else:
                rows_out.append(line)
        return "\n".join(rows_out)

    if direction == "in":
        for i in range(n_frames):
            yield _build_frame(i, reverse=False)
        yield _build_frame(n_frames, reverse=False)  # hold final full frame

    elif direction == "out":
        yield _build_frame(0, reverse=False)  # start from full
        for i in range(n_frames):
            yield _build_frame(i, reverse=True)

    elif direction == "loop":
        hold = max(4, n_frames // 8)
        # In pass
        for i in range(n_frames):
            yield _build_frame(i, reverse=False)
        # Hold full
        full_frame = _build_frame(n_frames, reverse=False)
        for _ in range(hold):
            yield full_frame
        # Out pass
        for i in range(n_frames):
            yield _build_frame(i, reverse=True)
        # Hold blank
        blank = "\n".join(" " * n_cols for _ in range(n_rows))
        for _ in range(hold):
            yield blank

    else:
        raise ValueError(f"direction must be 'in', 'out', or 'loop', got '{direction}'")


# -------------------------------------------------------------------------
# Neon color definitions — ANSI codes + dim variants + fringe neighbors + pulse cycle
# pulse: slow brightness oscillation simulating gas tube instability
#   bright → full → full → dim → full → full → bright → ...  (6-step cycle)
_NEON_COLORS: dict = {
    "cyan":    {
        "full":  "\033[96m",  "dim": "\033[2;96m", "off": "\033[2;34m",
        "fringe": ["\033[94m", "\033[92m"],
        "pulse": ["\033[1;96m", "\033[96m", "\033[96m", "\033[2;96m", "\033[96m", "\033[96m"],
    },
    "magenta": {
        "full":  "\033[95m",  "dim": "\033[2;95m", "off": "\033[2;35m",
        "fringe": ["\033[91m", "\033[94m"],
        "pulse": ["\033[1;95m", "\033[95m", "\033[95m", "\033[2;95m", "\033[95m", "\033[95m"],
    },
    "red":     {
        "full":  "\033[91m",  "dim": "\033[2;91m", "off": "\033[2;31m",
        "fringe": ["\033[95m", "\033[93m"],
        "pulse": ["\033[1;91m", "\033[91m", "\033[91m", "\033[2;91m", "\033[91m", "\033[91m"],
    },
    "yellow":  {
        "full":  "\033[93m",  "dim": "\033[2;93m", "off": "\033[2;33m",
        "fringe": ["\033[92m", "\033[91m"],
        "pulse": ["\033[1;93m", "\033[93m", "\033[93m", "\033[2;93m", "\033[93m", "\033[93m"],
    },
    "green":   {
        "full":  "\033[92m",  "dim": "\033[2;92m", "off": "\033[2;32m",
        "fringe": ["\033[96m", "\033[93m"],
        "pulse": ["\033[1;92m", "\033[92m", "\033[92m", "\033[2;92m", "\033[92m", "\033[92m"],
    },
    "blue":    {
        "full":  "\033[94m",  "dim": "\033[2;94m", "off": "\033[2;34m",
        "fringe": ["\033[96m", "\033[95m"],
        "pulse": ["\033[1;94m", "\033[94m", "\033[94m", "\033[2;94m", "\033[94m", "\033[94m"],
    },
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


def neon_sign_startup(
    text: str,
    color: str = "cyan",
    faulty_word_idx: int = 1,
    n_flickers: int = 3,
    hold_frames: int = 12,
    pulse: bool = True,
    flicker_hold: bool = False,
    flicker_prob: float = 0.25,
    dead_prob: float = 0.08,
    fringe_prob: float = 0.10,
    seed: Optional[int] = None,
) -> Iterator[str]:
    """Scripted neon sign power-on loop (A03s).

    Narrative sequence:
      1. Power-on: words light up staggered left-to-right, each settling full
      2. Faulty word: flickers on/off n_flickers times before holding
      3. Hold: steady (pulse+buzz) OR live flicker (per-word random tube state)
      4. Flicker-off: quick flash then all dark, ready to loop

    Designed to loop cleanly — last frame is all-dark, matches start.

    :param text: Space-separated words to display (e.g. 'JUST DO IT').
    :param color: Neon tube color — key in _NEON_COLORS (default: 'cyan').
    :param faulty_word_idx: Index (0-based) of the word with the bad tube (default: 1 → 'DO').
    :param n_flickers: How many on/off cycles the faulty word does before settling (default: 3).
    :param hold_frames: Frames for the hold/flicker phase (default: 12 → 1s @ 12fps).
    :param pulse: If True, apply slow brightness pulse to 'full' state tubes (default: True).
    :param flicker_hold: If True, hold phase uses per-word random tube flicker instead of
        steady pulse+buzz — sign stays alive and unstable after power-on (default: False).
    :param flicker_prob: Per-word dim probability during flicker hold (default: 0.25).
    :param dead_prob: Per-word dead probability during flicker hold (default: 0.08).
    :param fringe_prob: Per-word fringe probability during flicker hold (default: 0.10).
    :param seed: Optional random seed.
    :returns: Iterator of frame strings.
    :raises ValueError: If color is not a known neon color.
    """
    if color not in _NEON_COLORS:
        raise ValueError(f"Unknown neon color '{color}'. Available: {', '.join(_NEON_COLORS)}")

    if not text:
        yield text
        return

    from justdoit.core.rasterizer import render as _render

    # Accept raw word string (e.g. 'JUST DO IT') — split and render each word
    source_words = _ANSI_RE.sub("", text).strip().split()
    if not source_words:
        yield text
        return

    faulty_word_idx = faulty_word_idx % len(source_words)
    neon = _NEON_COLORS[color]

    # Render each word individually — gives us per-word row lists
    words = source_words
    word_renders: list[list[str]] = []
    for w in words:
        rendered = _render(w.upper(), font="block")
        word_renders.append(rendered.split("\n"))

    n_rows = max(len(wr) for wr in word_renders)
    # Pad all words to same row count
    for wr in word_renders:
        while len(wr) < n_rows:
            wr.append("")

    word_gap = "  "  # 2-space gap between words
    pulse_cycle = neon["pulse"]
    pulse_len = len(pulse_cycle)

    def _colorize_word(row_lines: list[str], state: str, rng_: random.Random,
                       frame_idx: int = 0) -> list[str]:
        """Apply neon state to all rows of a word.

        When state is 'full' and pulse is enabled, cycles through pulse_cycle
        for natural gas-tube brightness oscillation.
        """
        out = []
        for line in row_lines:
            plain = _ANSI_RE.sub("", line)
            if not plain.strip():
                out.append(plain)
                continue
            if state == "off":
                out.append(" " * len(plain))
            elif state == "fringe":
                code = rng_.choice(neon["fringe"])
                out.append(f"{code}{plain}{_RESET}")
            elif state == "full" and pulse:
                code = pulse_cycle[frame_idx % pulse_len]
                out.append(f"{code}{plain}{_RESET}")
            else:
                out.append(f"{neon[state]}{plain}{_RESET}")
        return out

    def _composite(word_states: list[str], rng_: random.Random,
                   buzz_prob: float = 0.12, frame_idx: int = 0) -> str:
        """Build one frame from per-word states.

        When state is 'full': pulse cycles brightness (if enabled) and
        buzz_prob adds occasional dim flicker on top — independent per word.
        """
        row_parts: list[list[str]] = [[] for _ in range(n_rows)]
        for widx, (wr, state) in enumerate(zip(word_renders, word_states)):
            effective_state = state
            # Buzz: occasional dim regardless of pulse
            if state == "full" and rng_.random() < buzz_prob:
                effective_state = "dim"
            colored = _colorize_word(wr, effective_state, rng_, frame_idx=frame_idx)
            for ridx in range(n_rows):
                if ridx < len(colored):
                    row_parts[ridx].append(colored[ridx])
                else:
                    row_parts[ridx].append("")
        return "\n".join(word_gap.join(row) for row in row_parts)

    rng = random.Random(seed)
    frame_counter = 0

    def _yield(states_: list[str], buzz_: float = 0.12) -> str:
        nonlocal frame_counter
        frame = _composite(states_, rng, buzz_prob=buzz_, frame_idx=frame_counter)
        frame_counter += 1
        return frame

    # --- Phase 1: Power-on — words light up staggered, one word per 2 frames ---
    states: list[str] = ["off"] * len(words)
    yield _yield(states, buzz_=0.0)  # initial dark frame — no buzz on off tubes

    for widx in range(len(words)):
        if widx == faulty_word_idx:
            continue
        states[widx] = "dim"
        yield _yield(states, buzz_=0.0)
        states[widx] = "full"
        yield _yield(states)

    # --- Phase 2: Faulty word struggles ---
    for flick in range(n_flickers):
        states[faulty_word_idx] = "dim"
        yield _yield(states, buzz_=0.0)
        states[faulty_word_idx] = "full"
        yield _yield(states)
        if flick < n_flickers - 1:
            states[faulty_word_idx] = "off"
            yield _yield(states, buzz_=0.0)
            states[faulty_word_idx] = "fringe"
            yield _yield(states, buzz_=0.0)

    # Final settle
    states[faulty_word_idx] = "full"

    # --- Phase 3: Hold ---
    if flicker_hold:
        # Live flicker — per-word random tube state each frame
        for _ in range(hold_frames):
            live_states = []
            for widx in range(len(words)):
                roll = rng.random()
                if roll < dead_prob:
                    live_states.append("off")
                elif roll < dead_prob + flicker_prob:
                    live_states.append("dim")
                elif roll < dead_prob + flicker_prob + fringe_prob:
                    live_states.append("fringe")
                else:
                    live_states.append("full")
            yield _yield(live_states)
    else:
        # Steady hold — pulse + buzz
        for _ in range(hold_frames):
            yield _yield(states)

    # --- Phase 4: Flicker-off ---
    all_dim = ["dim"] * len(words)
    yield _yield(all_dim, buzz_=0.0)
    all_off = ["off"] * len(words)
    yield _yield(all_off, buzz_=0.0)
    yield _yield(all_off, buzz_=0.0)  # clean loop point


def neon_word_glitch(
    text: str,
    color: str = "cyan",
    colors: Optional[list] = None,
    n_frames: int = 36,
    flicker_prob: float = 0.25,
    dead_prob: float = 0.08,
    fringe_prob: float = 0.12,
    seed: Optional[int] = None,
) -> Iterator[str]:
    """Per-word neon tube glitch — each word is one independent tube (A03w).

    Each word rolls its own state every frame: full, dim, off, or fringe.
    Simpler than neon_sign_startup — no narrative, just live chaotic flicker.

    :param text: Space-separated words (e.g. 'JUST DO IT').
    :param color: Single neon color for all words (default: 'cyan').
                  Ignored if colors is provided.
    :param colors: Optional list of color names per word. Cycles if shorter
                   than word count (e.g. ['cyan', 'magenta', 'yellow']).
    :param n_frames: Total frames to produce (default: 36).
    :param flicker_prob: Per-word dim probability per frame (default: 0.25).
    :param dead_prob: Per-word dead probability per frame (default: 0.08).
    :param fringe_prob: Per-word fringe probability per frame (default: 0.12).
    :param seed: Optional random seed.
    :returns: Iterator of frame strings.
    """
    if not text:
        yield text
        return

    from justdoit.core.rasterizer import render as _render

    source_words = _ANSI_RE.sub("", text).strip().split()
    if not source_words:
        yield text
        return

    # Resolve per-word color list
    if colors:
        for c in colors:
            if c not in _NEON_COLORS:
                raise ValueError(f"Unknown neon color '{c}'. Available: {', '.join(_NEON_COLORS)}")
        word_colors = [colors[i % len(colors)] for i in range(len(source_words))]
    else:
        if color not in _NEON_COLORS:
            raise ValueError(f"Unknown neon color '{color}'. Available: {', '.join(_NEON_COLORS)}")
        word_colors = [color] * len(source_words)

    word_renders = [_render(w.upper(), font="block").split("\n") for w in source_words]
    n_rows = max(len(wr) for wr in word_renders)
    for wr in word_renders:
        while len(wr) < n_rows:
            wr.append("")

    word_gap = "  "
    rng = random.Random(seed)

    def _colorize(line: str, color_name: str, state: str) -> str:
        plain = _ANSI_RE.sub("", line)
        if not plain.strip():
            return plain
        neon = _NEON_COLORS[color_name]
        if state == "off":
            return " " * len(plain)
        elif state == "fringe":
            code = rng.choice(neon["fringe"])
        else:
            code = neon[state]
        return f"{code}{plain}{_RESET}"

    for _ in range(n_frames):
        # Roll independent state per word
        word_states = []
        for widx in range(len(source_words)):
            roll = rng.random()
            if roll < dead_prob:
                word_states.append("off")
            elif roll < dead_prob + flicker_prob:
                word_states.append("dim")
            elif roll < dead_prob + flicker_prob + fringe_prob:
                word_states.append("fringe")
            else:
                word_states.append("full")

        frame_lines = []
        for row_idx in range(n_rows):
            row_segs = []
            for widx, wr in enumerate(word_renders):
                line = wr[row_idx] if row_idx < len(wr) else ""
                row_segs.append(_colorize(line, word_colors[widx], word_states[widx]))
            frame_lines.append(word_gap.join(row_segs))
        yield "\n".join(frame_lines)


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


# -------------------------------------------------------------------------
# Plasma Wave animation — A10
#
# Sweeps the plasma sin-field time parameter t from 0 → 2π, yielding
# frames where the character density pattern inside each glyph morphs
# smoothly through one full plasma cycle. Each frame is re-rendered with
# a fresh plasma fill at the new t value.
#
# Novelty vs asciimatics Plasma: (1) drives character *density selection*,
# not color; (2) confined to the glyph mask, not the full terminal;
# (3) bidirectional (forward then reverse) for seamless loop.
#


def plasma_wave(
    text_plain: str,
    font: str = "block",
    n_frames: int = 36,
    preset: str = "default",
    color: Optional[str] = None,
    loop: bool = True,
) -> Iterator[str]:
    """Plasma Wave animation — demoscene sin-field drives char density inside glyph mask (A10).

    Re-renders the text at each frame with a time-varying plasma fill, sweeping
    the phase parameter ``t`` from 0 → 2π (one full plasma cycle). The letterforms
    pulse and morph organically as the sinusoidal field evolves.

    This preset accepts the *plain text string* (not a pre-rendered frame) because
    it must re-render with different fill parameters each frame.

    :param text_plain: Plain text to render (e.g. 'JUST DO IT').
    :param font: Font name for rendering (default 'block').
    :param n_frames: Number of frames for one half-cycle (default 36). Full animation
        is 2×n_frames when loop=True (forward + reverse for seamless loop).
    :param preset: Plasma preset name — 'default', 'tight', 'slow', 'diagonal'.
    :param color: Optional ANSI color name applied after fill (e.g. 'cyan', 'magenta').
    :param loop: If True, yield forward then reverse frames for a seamless loop (default True).
    :returns: Iterator of frame strings.
    """
    import math as _math
    from justdoit.core.rasterizer import render as _render

    TWO_PI = 2.0 * _math.pi

    # Generate t values for one forward sweep [0, 2π)
    t_values = [TWO_PI * i / n_frames for i in range(n_frames)]
    if loop:
        # Append reverse sweep to create a seamless forward-back loop
        t_values = t_values + list(reversed(t_values))

    for t_val in t_values:
        frame = _render(
            text_plain,
            font=font,
            color=color,
            fill="plasma",
            fill_kwargs={"t": t_val, "preset": preset},
        )
        yield frame


# -------------------------------------------------------------------------
def flame_flicker(
    text_plain: str,
    font: str = "block",
    n_frames: int = 24,
    preset: str = "default",
    color: Optional[str] = None,
    loop: bool = True,
) -> Iterator[str]:
    """Flame Flicker animation — Doom-fire simulation flickering inside glyph mask (A08).

    Re-renders the text at each frame with a different random seed, producing a
    new flame heat pattern per frame.  The result is a natural flickering fire
    effect — each frame is a statistically independent snapshot of the flame,
    so the animation never loops identically even when ``loop=True``.

    When ``loop=True``, the frame sequence repeats seamlessly (both directions
    are identical since each frame is independently random).

    :param text_plain: Plain text to render (e.g. 'JUST DO IT').
    :param font: Font name for rendering (default 'block').
    :param n_frames: Total number of animation frames (default 24).
    :param preset: Flame preset name — 'default', 'hot', 'cool', 'embers'.
    :param color: Optional ANSI color name applied after fill (e.g. 'red', 'yellow').
    :param loop: If True, append a second copy of frames in reverse for a seamless loop
        (default True). Total frames = 2×n_frames when loop=True.
    :returns: Iterator of frame strings.
    """
    from justdoit.core.rasterizer import render as _render

    seeds = list(range(n_frames))
    if loop:
        seeds = seeds + list(reversed(seeds))

    for frame_seed in seeds:
        frame = _render(
            text_plain,
            font=font,
            color=color,
            fill="flame",
            fill_kwargs={"preset": preset, "seed": frame_seed},
        )
        yield frame


# -------------------------------------------------------------------------
def flame_gradient_color(
    text_plain: str,
    font: str = "block",
    n_frames: int = 24,
    preset: str = "default",
    palette_name: str = "fire",
    loop: bool = True,
) -> "Iterator[str]":
    """Flame Gradient Color animation — char and color both driven by flame heat (A08c).

    Per frame, the flame heat simulation drives BOTH character density selection AND
    per-cell 24-bit color simultaneously. Hot cells (heat ≈ 1.0) render as dense
    ``@#`` chars colored white/yellow; cooling cells render as sparse ``;:,.`` chars
    colored deep orange/red. Both the character texture and color evolve from the
    same underlying flame float field each frame.

    Implementation mirrors plasma_lava_lamp: for each frame, flame_fill() provides
    chars while flame_float_grid() (with same seed) provides the float grid for
    fill_float_colorize(). Total coupling: char density and color are always the
    same simulation data.

    :param text_plain: Plain text to render (e.g. 'JUST DO IT').
    :param font: Font name for rendering (default 'block').
    :param n_frames: Number of animation frames (default 24). Total = 2*n_frames
        when loop=True.
    :param preset: Flame preset — 'default', 'hot', 'cool', 'embers'.
    :param palette_name: Palette from PALETTE_REGISTRY (default 'fire').
    :param loop: If True, append reversed frames for seamless loop (default True).
    :returns: Iterator of colored frame strings.
    """
    from justdoit.core.rasterizer import render as _render
    from justdoit.effects.generative import flame_float_grid as _flame_float_grid
    from justdoit.effects.color import fill_float_colorize as _colorize, PALETTE_REGISTRY
    from justdoit.core.glyph import glyph_to_mask as _glyph_to_mask
    from justdoit.fonts import FONTS as _FONTS

    palette = PALETTE_REGISTRY.get(palette_name, PALETTE_REGISTRY["fire"])

    font_data = _FONTS.get(font, {})
    text_upper = text_plain.upper()
    gap = 1

    def _assemble_float_grid(frame_seed: int) -> list:
        """Build combined float grid for the full text at given seed."""
        if not font_data:
            return []
        sample_glyph = next(iter(font_data.values()))
        height = len(sample_glyph)

        combined: list = [[] for _ in range(height)]

        for ch in text_upper:
            glyph = font_data.get(ch, font_data.get(" "))
            ink_chars = "".join({c for row in glyph for c in row if c != " "}) or chr(9608)
            mask = _glyph_to_mask(glyph, ink_chars=ink_chars)
            fg = _flame_float_grid(mask, preset=preset, seed=frame_seed)

            glyph_cols = max(len(row) for row in mask) if mask else 0

            for r in range(height):
                row_floats = fg[r] if r < len(fg) else []
                row_floats = row_floats[:glyph_cols]
                while len(row_floats) < glyph_cols:
                    row_floats.append(0.0)
                combined[r].extend(row_floats)
                combined[r].extend([0.0] * gap)

        return combined

    seeds = list(range(n_frames))
    if loop:
        seeds = seeds + list(reversed(seeds))

    for frame_seed in seeds:
        char_frame = _render(
            text_plain,
            font=font,
            fill="flame",
            fill_kwargs={"preset": preset, "seed": frame_seed},
        )
        float_grid = _assemble_float_grid(frame_seed)
        colored_frame = _colorize(char_frame, float_grid, palette)
        yield colored_frame


# -------------------------------------------------------------------------
_FLAME_CHARS_BLOOM = "@#S%?*+;:,."


def flame_bloom(
    text_plain: str,
    font: str = "block",
    n_frames: int = 24,
    preset: str = "default",
    palette_name: str = "fire",
    tone_curve: str = "blown_out",
    bloom_color_name: str = "orange",
    radius: int = 4,
    falloff: float = 0.88,
    loop: bool = True,
) -> "Iterator[str]":
    """Flame Bloom animation — three-axis composite flagship (X_FLAME_BLOOM).

    Three axes simultaneously:
      1. Flame fill (A08) — Doom-fire heat simulation drives char density
      2. Fire palette color (C11/A08c) — same heat drives 24-bit color
      3. C13 blown_out tone curve — white-hot core blows out to solid ``@``
      4. C12 bloom — orange light bleeds into surrounding space cells

    White-hot core blows out to solid ``@``; orange light bleeds into
    surrounding space. The project's 20/20 flagship composite visual.

    :param text_plain: Plain text to render (e.g. 'JUST DO IT').
    :param font: Font name for rendering (default 'block').
    :param n_frames: Number of animation frames (default 24). Total = 2*n_frames
        when loop=True.
    :param preset: Flame preset — 'default', 'hot', 'cool', 'embers'.
    :param palette_name: Palette from PALETTE_REGISTRY (default 'fire').
    :param tone_curve: Tone curve to apply (default 'blown_out').
    :param bloom_color_name: Bloom hue from BLOOM_COLORS (default 'orange').
    :param radius: Bloom radius in cells (default 4).
    :param falloff: Per-cell bloom falloff (default 0.88).
    :param loop: If True, append reversed frames for seamless loop (default True).
    :returns: Iterator of colored+bloomed frame strings.
    """
    from justdoit.effects.generative import flame_float_grid as _flame_float_grid
    from justdoit.effects.color import (
        fill_float_colorize as _colorize,
        apply_tone_curve as _apply_tone_curve,
        PALETTE_REGISTRY,
        bloom as _bloom,
        BLOOM_COLORS,
    )
    from justdoit.core.glyph import glyph_to_mask as _glyph_to_mask
    from justdoit.fonts import FONTS as _FONTS

    palette = PALETTE_REGISTRY.get(palette_name, PALETTE_REGISTRY["fire"])
    bc = BLOOM_COLORS.get(bloom_color_name, BLOOM_COLORS.get("orange", (255, 140, 0)))

    font_data = _FONTS.get(font, {})
    text_upper = text_plain.upper()
    gap = 1
    n_bloom_chars = len(_FLAME_CHARS_BLOOM)

    def _assemble_frame(frame_seed: int) -> str:
        """Build one flame_bloom frame from scratch."""
        if not font_data:
            return ""
        sample_glyph = next(iter(font_data.values()))
        height = len(sample_glyph)

        # Assemble combined float grid + char lines simultaneously
        float_grid: list = [[] for _ in range(height)]
        char_lines: list = ["" for _ in range(height)]

        for ch in text_upper:
            glyph = font_data.get(ch, font_data.get(" "))
            ink_chars = "".join({c for row in glyph for c in row if c != " "}) or chr(9608)
            mask = _glyph_to_mask(glyph, ink_chars=ink_chars)
            heat_grid = _flame_float_grid(mask, preset=preset, seed=frame_seed)

            # Apply tone curve to get tone_mapped floats (used for char mapping)
            tone_mapped = _apply_tone_curve(heat_grid, curve=tone_curve)

            glyph_cols = max(len(row) for row in mask) if mask else 0
            glyph_height = len(mask)

            # Build ink mask for char mapping
            ink = [
                [
                    bool(mask[r][c] >= 0.5) if c < len(mask[r]) else False
                    for c in range(glyph_cols)
                ]
                for r in range(glyph_height)
            ]

            for r in range(height):
                # Float grid row (use raw heat for color, not tone-mapped)
                raw_row = heat_grid[r] if r < len(heat_grid) else []
                raw_row = raw_row[:glyph_cols]
                while len(raw_row) < glyph_cols:
                    raw_row.append(0.0)
                float_grid[r].extend(raw_row)
                float_grid[r].extend([0.0] * gap)

                # Char row from tone-mapped values
                tone_row = tone_mapped[r] if r < len(tone_mapped) else []
                line = ""
                for c in range(glyph_cols):
                    if r < glyph_height and c < len(ink[r]) and ink[r][c]:
                        h = tone_row[c] if c < len(tone_row) else 0.0
                        h = max(0.0, min(1.0, h))
                        idx = int((1.0 - h) * (n_bloom_chars - 1) + 0.5)
                        idx = max(0, min(n_bloom_chars - 1, idx))
                        line += _FLAME_CHARS_BLOOM[idx]
                    else:
                        line += " "
                # Add gap spaces
                line += " " * gap
                char_lines[r] += line

        char_frame = "\n".join(char_lines)
        colored_frame = _colorize(char_frame, float_grid, palette)
        bloomed_frame = _bloom(colored_frame, bc, radius=radius, falloff=falloff)
        return bloomed_frame

    seeds = list(range(n_frames))
    if loop:
        seeds = seeds + list(reversed(seeds))

    for frame_seed in seeds:
        yield _assemble_frame(frame_seed)


# -------------------------------------------------------------------------
def voronoi_stained_glass(
    text_plain: str,
    font: str = "block",
    n_frames: int = 30,
    palette_name: str = "spectral",
    loop: bool = True,
) -> Iterator[str]:
    """Voronoi Stained Glass animation (A_VOR1).

    Renders text with voronoi_cracked fill, then animates by rotating color
    assignments through a named palette. Each Voronoi cell "pane" holds a
    stable structural shape (the cracked-earth borders never move); the palette
    offset advances each frame so the color "light" shifts through the glass.
    Border characters (``@``) are rendered silver — the lead strips of stained
    glass.

    Structural permanence + fluid color motion = stained-glass window with
    light shifting through it.

    This preset uses a prime-based spatial hash (``row * 6271 + col * 7919``
    modulo N_REGIONS) to assign stable per-cell region IDs without requiring
    Voronoi region tracking. The hash distributes cells into 17 color groups
    with a natural-looking irregular pattern that reads as distinct panes.

    :param text_plain: Plain text to render (e.g. 'JUST DO IT').
    :param font: Font name for rendering (default 'block').
    :param n_frames: Frames per palette cycle (default 30). Total =
        2×n_frames when loop=True (seamless forward+reverse).
    :param palette_name: Palette from PALETTE_REGISTRY — 'spectral' (default),
        'fire', 'lava', or 'bio'.
    :param loop: If True, yield forward then reverse for a seamless loop
        (default True).
    :returns: Iterator of colored frame strings.
    """
    from justdoit.core.rasterizer import render as _render
    from justdoit.effects.color import PALETTE_REGISTRY

    palette = PALETTE_REGISTRY.get(palette_name, PALETTE_REGISTRY["spectral"])
    n_palette = len(palette)

    # Render with voronoi_cracked fill (stable geometry, seed=42 by default)
    rendered = _render(text_plain, font=font, fill="voronoi_cracked")
    lines = rendered.split("\n")

    # Strip any ANSI codes to get clean characters
    clean_lines = [_ANSI_RE.sub("", ln) for ln in lines]
    n_cols = max((len(ln) for ln in clean_lines), default=0)
    clean_lines = [ln.ljust(n_cols) for ln in clean_lines]

    # Constants for the stained-glass effect
    BORDER_CHAR = "@"          # voronoi_cracked border character = lead strips
    SILVER = (180, 180, 180)   # lead color
    N_REGIONS = 17             # prime → good irregular distribution of pane colors
    _RESET_SG = "\033[0m"

    def _tc(r: int, g: int, b: int) -> str:
        return f"\033[38;2;{r};{g};{b}m"

    def _lerp(t: float) -> tuple:
        """Interpolate palette at float t ∈ [0, 1]."""
        t = max(0.0, min(1.0, t))
        scaled = t * (n_palette - 1)
        lo = int(scaled)
        hi = min(lo + 1, n_palette - 1)
        frac = scaled - lo
        a, b_ = palette[lo], palette[hi]
        return (
            int(a[0] + (b_[0] - a[0]) * frac),
            int(a[1] + (b_[1] - a[1]) * frac),
            int(a[2] + (b_[2] - a[2]) * frac),
        )

    def _make_frame(offset: int) -> str:
        result = []
        for r, line in enumerate(clean_lines):
            out = ""
            for c, ch in enumerate(line):
                if ch == " ":
                    out += ch
                elif ch == BORDER_CHAR:
                    # Border cells = silver lead strips, not animated
                    out += _tc(*SILVER) + ch + _RESET_SG
                else:
                    # Assign a stable region to this cell via prime hash
                    region = (r * 6271 + c * 7919) % N_REGIONS
                    # Rotate color assignment by offset
                    t = ((region + offset) % N_REGIONS) / N_REGIONS
                    rgb = _lerp(t)
                    out += _tc(*rgb) + ch + _RESET_SG
            result.append(out)
        return "\n".join(result)

    offsets = list(range(n_frames))
    if loop:
        offsets = offsets + list(reversed(offsets))

    for off in offsets:
        yield _make_frame(off)


# -------------------------------------------------------------------------
def plasma_lava_lamp(
    text_plain: str,
    font: str = "block",
    n_frames: int = 36,
    preset: str = "default",
    palette_name: str = "lava",
    loop: bool = True,
) -> "Iterator[str]":
    """Plasma Lava Lamp animation -- both chars and color driven by plasma float (A10c).

    The plasma sin-field drives BOTH character density selection AND per-cell
    24-bit color simultaneously using C11 infrastructure. High plasma values
    produce dense chars (``@#S``) colored white/yellow; low values produce sparse
    chars (``;:,.``) colored deep violet/purple. Both the character texture and
    the color evolve from the same underlying float field each frame -- the
    letterforms appear to contain slow-moving lava-lamp fluid.

    Implementation: for each frame, the plasma float grid is assembled by calling
    ``plasma_float_grid()`` per glyph (mirroring how the rasterizer assembles
    glyph columns) then applying ``fill_float_colorize()`` over the rendered char
    output. Both functions use the same normalized plasma field, ensuring char
    density and color are always in correspondence -- the brightest, densest cells
    are always the hottest color, and the sparsest cells are always the coolest.

    :param text_plain: Plain text to render (e.g. 'JUST DO IT').
    :param font: Font name for rendering (default 'block').
    :param n_frames: Number of frames for one half-cycle (default 36). Full
        animation is 2*n_frames when loop=True (forward + reverse).
    :param preset: Plasma preset -- 'default', 'tight', 'slow', 'diagonal'.
    :param palette_name: Palette from PALETTE_REGISTRY -- 'lava' (default),
        'fire', 'spectral', or 'bio'.
    :param loop: If True, yield forward then reverse for a seamless loop (default True).
    :returns: Iterator of colored frame strings.
    """
    import math as _math
    from justdoit.core.rasterizer import render as _render
    from justdoit.effects.generative import plasma_float_grid as _plasma_float_grid
    from justdoit.effects.color import fill_float_colorize as _colorize, PALETTE_REGISTRY
    from justdoit.core.glyph import glyph_to_mask as _glyph_to_mask
    from justdoit.fonts import FONTS as _FONTS

    palette = PALETTE_REGISTRY.get(palette_name, PALETTE_REGISTRY["lava"])
    TWO_PI = 2.0 * _math.pi

    # Pre-compute glyph masks for each character (matches rasterizer assembly order)
    font_data = _FONTS.get(font, {})
    text_upper = text_plain.upper()
    gap = 1  # rasterizer default gap

    def _assemble_float_grid(t_val: float) -> list:
        """Build the combined float grid for the full text at time t_val.

        Mirrors the rasterizer's row assembly loop: for each char, compute its
        glyph float grid and append it (+ gap columns of 0.0) to the row.
        """
        # Determine the height from the font
        if not font_data:
            return []
        sample_glyph = next(iter(font_data.values()))
        height = len(sample_glyph)

        combined: list = [[] for _ in range(height)]

        for i, ch in enumerate(text_upper):
            glyph = font_data.get(ch, font_data.get(" "))
            ink = "".join({c for row in glyph for c in row if c != " "}) or chr(9608)
            mask = _glyph_to_mask(glyph, ink_chars=ink)
            fg = _plasma_float_grid(mask, t=t_val, preset=preset)

            glyph_cols = max(len(row) for row in mask) if mask else 0

            for r in range(height):
                row_floats = fg[r] if r < len(fg) else []
                # Pad/trim to glyph_cols
                row_floats = row_floats[:glyph_cols]
                while len(row_floats) < glyph_cols:
                    row_floats.append(0.0)
                combined[r].extend(row_floats)
                # Add gap columns of 0.0 (space chars between glyphs)
                combined[r].extend([0.0] * gap)

        return combined

    t_values = [TWO_PI * i / n_frames for i in range(n_frames)]
    if loop:
        t_values = t_values + list(reversed(t_values))

    for t_val in t_values:
        # Render chars using plasma fill (same t and preset)
        char_frame = _render(
            text_plain,
            font=font,
            fill="plasma",
            fill_kwargs={"t": t_val, "preset": preset},
        )
        # Build combined float grid
        float_grid = _assemble_float_grid(t_val)
        # Apply C11 color: same float values drive char AND color
        colored_frame = _colorize(char_frame, float_grid, palette)
        yield colored_frame


# -------------------------------------------------------------------------
def neon_bloom(
    text_plain: str,
    font: str = "block",
    n_frames: int = 30,
    color: str = "cyan",
    bloom_color_name: str = "cyan",
    radius: int = 4,
    falloff: float = 0.88,
    loop: bool = True,
) -> "Iterator[str]":
    """Neon text with exterior bloom glow — C12 cross-breed (X_NEON_BLOOM).

    Renders text with a neon color, then applies C12 bloom so surrounding
    space cells glow with the neon hue. The bloom radius breathes (oscillates)
    per frame via a sine-driven falloff variation, creating a pulsing halo
    effect around the letterforms.

    Each frame: render → neon colorize → bloom(breathing falloff)

    The bloom color is spatially stable — only its intensity breathes. The
    letterforms themselves never move. Structural permanence + fluid light
    motion = neon sign that glows in the dark.

    Cross-breed axes: C07 (24-bit color) × C12 (bloom) × A (falloff animation).
    Visual interest scores: tension=5, emergence=4, distinctness=5, wow=5 → 19/20.

    :param text_plain: Plain text to render (e.g. 'JUST DO IT').
    :param font: Font name (default 'block').
    :param n_frames: Frames in one half-cycle (default 30). Total = 2*n_frames
        if loop=True.
    :param color: Neon foreground color name from COLORS dict (default 'cyan').
    :param bloom_color_name: Bloom hue from BLOOM_COLORS (default 'cyan').
    :param radius: Bloom radius in cells (default 4).
    :param falloff: Base per-cell bloom falloff (default 0.88). Animated
        ±0.06 per frame via sine to create a breathing halo.
    :param loop: Yield forward + reverse for seamless loop (default True).
    :returns: Iterator of colored+bloomed frame strings.
    """
    import math as _math
    from justdoit.core.rasterizer import render as _render
    from justdoit.effects.color import (
        bloom as _bloom,
        BLOOM_COLORS,
        colorize as _colorize,
    )

    bc = BLOOM_COLORS.get(bloom_color_name, BLOOM_COLORS["cyan"])
    TWO_PI = 2.0 * _math.pi

    # Render once — the letterforms never change between frames
    base = _render(text_plain, font=font)
    colored_base = _colorize(base, color)

    # Build frame indices for one half-cycle
    frame_indices = list(range(n_frames))
    if loop:
        frame_indices = frame_indices + list(reversed(frame_indices))

    for i in frame_indices:
        # Animate bloom falloff: gentle sine oscillation around base falloff
        # This creates a breathing halo — the glow expands and contracts
        frame_falloff = falloff + 0.06 * _math.sin(TWO_PI * i / n_frames)
        frame_falloff = max(0.5, min(0.99, frame_falloff))  # keep in valid range
        yield _bloom(colored_base, bc, radius=radius, falloff=frame_falloff)


# -------------------------------------------------------------------------
def bloom_pulse(
    text_plain: str,
    font: str = "block",
    n_frames: int = 24,
    preset: str = "hot",
    palette_name: str = "fire",
    tone_curve: str = "aces",
    bloom_color_name: str = "orange",
    base_radius: int = 4,
    bloom_amplitude: int = 2,
    falloff: float = 0.88,
    loop: bool = True,
) -> "Iterator[str]":
    """Bloom Pulse animation — breathing halo around burning letterforms (A_BLOOM1).

    Three axes simultaneously:
      1. Flame fill (A08) — Doom-fire heat simulation drives char density
      2. Fire palette color (C11/A08c) — same heat drives 24-bit color
      3. C13 ACES tone curve — punchy mids, more char variety than blown_out
      4. C12 bloom — exterior glow with radius oscillating via sin(t)

    The bloom radius breathes in and out on a sine cycle while the flame
    flickers independently. The interplay between the periodic bloom breathing
    (smooth, rhythmic) and the stochastic flame (chaotic, independent) creates
    the illusion of a living fire that inhales and exhales.

    Distinct from X_FLAME_BLOOM: that preset uses ``blown_out`` tone curve and
    fixed bloom radius. This uses ``aces`` (more char variety in the hot zone,
    softer rolloff) and an *animated* bloom radius — the glow itself breathes.

    Cross-breed axes: A08 (flame) × C11 (fire_palette color) × C13 (ACES curve)
    × C12 (bloom) × A (bloom radius animation).
    Visual interest scores: tension=4, emergence=4, distinctness=5, wow=5 → 18/20.

    :param text_plain: Plain text to render (e.g. 'JUST DO IT').
    :param font: Font name for rendering (default 'block').
    :param n_frames: Number of unique flame frames (default 24). Total = 2*n_frames
        when loop=True.
    :param preset: Flame preset — 'default', 'hot', 'cool', 'embers'.
    :param palette_name: Palette from PALETTE_REGISTRY (default 'fire').
    :param tone_curve: Tone curve applied to flame floats (default 'aces').
    :param bloom_color_name: Bloom hue from BLOOM_COLORS (default 'orange').
    :param base_radius: Base bloom radius in cells (default 4). Oscillates
        ±bloom_amplitude around this value.
    :param bloom_amplitude: Half-amplitude of radius oscillation in cells (default 2).
        Radius sweeps from base_radius-amplitude to base_radius+amplitude.
    :param falloff: Per-cell bloom falloff (default 0.88). Fixed across frames.
    :param loop: If True, append reversed frames for seamless loop (default True).
    :returns: Iterator of colored+bloomed frame strings.
    """
    import math as _math
    from justdoit.effects.generative import flame_float_grid as _flame_float_grid
    from justdoit.effects.color import (
        fill_float_colorize as _colorize,
        apply_tone_curve as _apply_tone_curve,
        PALETTE_REGISTRY,
        bloom as _bloom,
        BLOOM_COLORS,
    )
    from justdoit.core.glyph import glyph_to_mask as _glyph_to_mask
    from justdoit.fonts import FONTS as _FONTS

    palette = PALETTE_REGISTRY.get(palette_name, PALETTE_REGISTRY["fire"])
    bc = BLOOM_COLORS.get(bloom_color_name, BLOOM_COLORS.get("orange", (255, 140, 0)))

    font_data = _FONTS.get(font, {})
    text_upper = text_plain.upper()
    gap = 1
    TWO_PI = 2.0 * _math.pi
    n_bloom_chars = len(_FLAME_CHARS_BLOOM)

    def _assemble_frame(frame_seed: int, current_radius: int) -> str:
        """Build one bloom_pulse frame: flame chars + ACES tone + fire palette + bloom."""
        if not font_data:
            return ""
        sample_glyph = next(iter(font_data.values()))
        height = len(sample_glyph)

        float_grid: list = [[] for _ in range(height)]
        char_lines: list = ["" for _ in range(height)]

        for ch in text_upper:
            glyph = font_data.get(ch, font_data.get(" "))
            ink_chars = "".join({c for row in glyph for c in row if c != " "}) or chr(9608)
            mask = _glyph_to_mask(glyph, ink_chars=ink_chars)
            heat_grid = _flame_float_grid(mask, preset=preset, seed=frame_seed)

            # Apply ACES tone curve to derive char density mapping
            tone_mapped = _apply_tone_curve(heat_grid, curve=tone_curve)

            glyph_cols = max(len(row) for row in mask) if mask else 0
            glyph_height = len(mask)

            ink = [
                [
                    bool(mask[r][c] >= 0.5) if c < len(mask[r]) else False
                    for c in range(glyph_cols)
                ]
                for r in range(glyph_height)
            ]

            for r in range(height):
                raw_row = heat_grid[r] if r < len(heat_grid) else []
                raw_row = raw_row[:glyph_cols]
                while len(raw_row) < glyph_cols:
                    raw_row.append(0.0)
                float_grid[r].extend(raw_row)
                float_grid[r].extend([0.0] * gap)

                tone_row = tone_mapped[r] if r < len(tone_mapped) else []
                line = ""
                for c in range(glyph_cols):
                    if r < glyph_height and c < len(ink[r]) and ink[r][c]:
                        h = tone_row[c] if c < len(tone_row) else 0.0
                        h = max(0.0, min(1.0, h))
                        idx = int((1.0 - h) * (n_bloom_chars - 1) + 0.5)
                        idx = max(0, min(n_bloom_chars - 1, idx))
                        line += _FLAME_CHARS_BLOOM[idx]
                    else:
                        line += " "
                line += " " * gap
                char_lines[r] += line

        char_frame = "\n".join(char_lines)
        colored_frame = _colorize(char_frame, float_grid, palette)
        bloomed_frame = _bloom(colored_frame, bc, radius=current_radius, falloff=falloff)
        return bloomed_frame

    seeds = list(range(n_frames))
    if loop:
        seeds = seeds + list(reversed(seeds))

    total = len(seeds)
    for i, frame_seed in enumerate(seeds):
        # Bloom radius breathes: sine oscillation around base_radius
        # Phase is tied to frame index (0..total-1), giving a full breath per loop
        raw_radius = base_radius + bloom_amplitude * _math.sin(TWO_PI * i / total)
        current_radius = max(1, int(round(raw_radius)))
        yield _assemble_frame(frame_seed, current_radius)


# -------------------------------------------------------------------------
# X_PLASMA_BLOOM chromatic bloom color presets
# Maps plasma intensity (0.0–1.0) through a visible spectrum shift.
# Used to derive per-frame bloom color from mean plasma float.
_PLASMA_BLOOM_SPECTRUM: list = [
    (120, 0, 220),    # 0.0 — deep violet
    (0, 60, 255),     # 0.2 — indigo-blue
    (0, 200, 255),    # 0.4 — cyan
    (0, 255, 100),    # 0.6 — green-cyan
    (200, 255, 0),    # 0.8 — yellow-green
    (255, 80, 0),     # 1.0 — orange-red
]


def plasma_bloom(
    text_plain: str,
    font: str = "block",
    n_frames: int = 36,
    preset: str = "default",
    palette_name: str = "spectral",
    radius: int = 3,
    falloff: float = 0.88,
    loop: bool = True,
) -> "Iterator[str]":
    """Plasma Bloom — chromatic bloom halo driven by plasma field intensity (X_PLASMA_BLOOM).

    Two axes interact to produce behavior neither produces alone:
      1. Plasma fill (A10) — demoscene sin-field drives char density inside glyphs
      2. C11 spectral colorization — same plasma float drives per-cell 24-bit color
      3. C12 chromatic bloom — *mean plasma intensity* for each frame is mapped
         through the visible spectrum to derive the bloom halo color, so the
         surrounding glow shifts hue (violet → cyan → orange) as the plasma wave
         cycles.

    The key structural tension: the plasma field is deterministic and periodic
    (the letterforms morph on a fixed sin-field cycle), while the bloom color
    shifts through the spectrum as the mean intensity rises and falls across
    frames. The result: text that appears to be bathed in shifting colored light
    emanating from within the letterforms themselves.

    Chromatic bloom — bloom color derived from fill state — has no prior art in
    ASCII art tooling (asciimatics, aalib, blessed, rich).

    :param text_plain: Plain text to render (e.g. 'JUST DO IT').
    :param font: Font name for rendering (default 'block').
    :param n_frames: Frames for one forward sweep (default 36). Total = 2×n_frames
        when loop=True (forward+reverse seamless loop).
    :param preset: Plasma fill preset — 'default', 'tight', 'slow', 'diagonal'.
    :param palette_name: Palette for ink cell coloring via C11 (default 'spectral').
    :param radius: Bloom radius in cells (default 3). Fixed — use A_BLOOM1 for
        animated radius.
    :param falloff: Per-cell bloom falloff (default 0.88).
    :param loop: If True, yield forward then reverse frames for a seamless loop
        (default True).
    :returns: Iterator of colored+bloomed frame strings.
    """
    import math as _math
    from justdoit.core.rasterizer import render as _render
    from justdoit.effects.generative import plasma_float_grid as _plasma_float_grid
    from justdoit.effects.color import (
        fill_float_colorize as _colorize,
        PALETTE_REGISTRY,
        bloom as _bloom,
    )
    from justdoit.core.glyph import glyph_to_mask as _glyph_to_mask
    from justdoit.fonts import FONTS as _FONTS

    TWO_PI = 2.0 * _math.pi
    palette = PALETTE_REGISTRY.get(palette_name, PALETTE_REGISTRY["spectral"])
    font_data = _FONTS.get(font, {})
    text_upper = text_plain.upper()
    gap = 1

    def _lerp_spectrum(t: float) -> tuple:
        """Map float t in [0, 1] to an (r, g, b) bloom color via _PLASMA_BLOOM_SPECTRUM."""
        n = len(_PLASMA_BLOOM_SPECTRUM)
        t = max(0.0, min(1.0, t))
        scaled = t * (n - 1)
        lo = int(scaled)
        hi = min(lo + 1, n - 1)
        frac = scaled - lo
        a = _PLASMA_BLOOM_SPECTRUM[lo]
        b_ = _PLASMA_BLOOM_SPECTRUM[hi]
        return (
            int(a[0] + (b_[0] - a[0]) * frac),
            int(a[1] + (b_[1] - a[1]) * frac),
            int(a[2] + (b_[2] - a[2]) * frac),
        )

    def _assemble_frame(t_val: float) -> str:
        """Build one plasma_bloom frame: plasma chars + spectral color + chromatic bloom."""
        if not font_data:
            return ""
        sample_glyph = next(iter(font_data.values()))
        height = len(sample_glyph)

        float_grid: list = [[] for _ in range(height)]

        for ch in text_upper:
            glyph = font_data.get(ch, font_data.get(" "))
            ink_chars = "".join({c for row in glyph for c in row if c != " "}) or chr(9608)
            mask = _glyph_to_mask(glyph, ink_chars=ink_chars)
            pg = _plasma_float_grid(mask, t=t_val, preset=preset)

            glyph_cols = max(len(row) for row in mask) if mask else 0

            for r in range(height):
                raw_row = pg[r] if r < len(pg) else []
                raw_row = raw_row[:glyph_cols]
                while len(raw_row) < glyph_cols:
                    raw_row.append(0.0)
                float_grid[r].extend(raw_row)
                float_grid[r].extend([0.0] * gap)

        # Render char frame using plasma fill (same t as float grid)
        char_frame = _render(
            text_plain,
            font=font,
            fill="plasma",
            fill_kwargs={"t": t_val, "preset": preset},
        )

        # Apply spectral C11 colorization
        colored_frame = _colorize(char_frame, float_grid, palette)

        # Derive bloom color from plasma phase t directly.
        # t sweeps 0 → 2π (one full plasma cycle); map to [0, 1] for spectrum
        # interpolation. This produces a full violet→cyan→orange→violet sweep
        # synchronized with the plasma wave — truly chromatic bloom.
        phase_norm = (t_val % TWO_PI) / TWO_PI  # 0.0–1.0, periodic
        bloom_color = _lerp_spectrum(phase_norm)

        # Apply C12 bloom with chromatic color
        bloomed_frame = _bloom(colored_frame, bloom_color, radius=radius, falloff=falloff)
        return bloomed_frame

    # Generate t values: 0 → 2π forward sweep
    t_values = [TWO_PI * i / n_frames for i in range(n_frames)]
    if loop:
        t_values = t_values + list(reversed(t_values))

    for t_val in t_values:
        yield _assemble_frame(t_val)
