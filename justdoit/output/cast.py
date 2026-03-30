"""
Package: justdoit.output.cast
asciinema v2 .cast file writer for animation frame sequences.

Converts a list of ANSI frame strings into an asciinema recording
that can be played back in the terminal or embedded in a browser.
Pure Python stdlib — no external dependencies.
"""

import json
import logging as _logging
import re
from pathlib import Path
from typing import Optional

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.output.cast"
__updated__ = "2026-03-30 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

_ANSI_RE = re.compile(r"\033\[[0-9;]*[mABCDHJKfsu]")


# -------------------------------------------------------------------------
def _strip_ansi(text: str) -> str:
    """Strip ANSI escape sequences from a string.

    :param text: String possibly containing ANSI escape codes.
    :returns: Plain text string.
    """
    return _ANSI_RE.sub("", text)


# -------------------------------------------------------------------------
def _detect_dims(frames: list[str]) -> tuple[int, int]:
    """Auto-detect terminal dimensions from frame content.

    Measures the maximum line width and line count across all frames.

    :param frames: List of ANSI frame strings.
    :returns: (cols, rows) tuple.
    """
    max_cols = 0
    max_rows = 0
    for frame in frames:
        lines = _strip_ansi(frame).split("\n")
        max_cols = max(max_cols, max(len(line) for line in lines) if lines else 0)
        max_rows = max(max_rows, len(lines))
    # Add a small margin so content never clips
    return max(max_cols + 2, 40), max(max_rows + 1, 10)


# -------------------------------------------------------------------------
def to_cast(
    frames: list[str],
    fps: float = 24.0,
    title: str = "JustDoIt",
    cols: Optional[int] = None,
    rows: Optional[int] = None,
) -> str:
    """Serialize a frame list to asciinema v2 .cast format string.

    Each frame is emitted as a clear-screen + home-cursor sequence followed
    by the frame content, so playback always starts from position (0,0).

    :param frames: List of ANSI frame strings (one string per frame).
    :param fps: Playback speed in frames per second.
    :param title: Recording title (appears in asciinema player).
    :param cols: Terminal width (auto-detected from frames if None).
    :param rows: Terminal height (auto-detected from frames if None).
    :returns: asciinema v2 format string (JSON lines).
    """
    if not frames:
        raise ValueError("frames must not be empty")
    if fps <= 0:
        raise ValueError("fps must be positive")

    if cols is None or rows is None:
        auto_cols, auto_rows = _detect_dims(frames)
        cols = cols if cols is not None else auto_cols
        rows = rows if rows is not None else auto_rows

    header = {
        "version": 2,
        "width": cols,
        "height": rows,
        "title": title,
    }

    dt = 1.0 / fps
    lines = [json.dumps(header, separators=(",", ":"))]

    for i, frame in enumerate(frames):
        timestamp = round(i * dt, 6)
        # Clear screen + home cursor, then emit frame
        content = f"\033[2J\033[H{frame}"
        lines.append(json.dumps([timestamp, "o", content], separators=(",", ":")))

    return "\n".join(lines) + "\n"


# -------------------------------------------------------------------------
def save_cast(
    frames: list[str],
    path: str | Path,
    fps: float = 24.0,
    title: str = "JustDoIt",
    cols: Optional[int] = None,
    rows: Optional[int] = None,
) -> None:
    """Save an animation frame list as an asciinema v2 .cast file.

    :param frames: List of ANSI frame strings (one string per frame).
    :param path: Output file path (e.g. 'output.cast').
    :param fps: Playback speed in frames per second.
    :param title: Recording title (appears in asciinema player).
    :param cols: Terminal width (auto-detected from frames if None).
    :param rows: Terminal height (auto-detected from frames if None).
    """
    cast = to_cast(frames, fps=fps, title=title, cols=cols, rows=rows)
    Path(path).write_text(cast, encoding="utf-8")
    _LOGGER.info(f"Saved .cast to {path} ({len(frames)} frames @ {fps}fps)")
