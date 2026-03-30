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
