"""
Package: justdoit.animate.player
Terminal animation frame-loop player.

Drives any generator that yields strings (frames) at a given fps.
Uses ANSI cursor control to redraw in-place without scrolling.

Cursor is hidden during playback and restored on exit, even on Ctrl+C.
Pure Python stdlib — no external dependencies.
"""

import logging as _logging
import sys
import time
from typing import Iterator, Optional, Protocol

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.animate.player"
__updated__ = "2026-03-23 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

# ANSI control sequences
_HIDE_CURSOR = "\033[?25l"
_SHOW_CURSOR = "\033[?25h"
_CLEAR_LINE  = "\033[2K\r"


# -------------------------------------------------------------------------
class _SoundPlayerProtocol(Protocol):
    """Duck-type interface expected by play() for optional audio sync."""

    def start(self) -> None: ...
    def update(self, frame_idx: int, total_frames: int) -> None: ...
    def stop(self) -> None: ...


# -------------------------------------------------------------------------
def _move_up(n: int) -> str:
    """Return ANSI sequence to move cursor up n lines.

    :param n: Number of lines to move up.
    :returns: ANSI escape string.
    """
    if n <= 0:
        return ""
    return f"\033[{n}A"


# -------------------------------------------------------------------------
def _clear_frame(n_lines: int) -> None:
    """Clear n_lines of terminal output so the next frame can overwrite them.

    :param n_lines: Number of lines to clear (height of last frame).
    """
    sys.stdout.write(_move_up(n_lines))
    for _ in range(n_lines):
        sys.stdout.write(_CLEAR_LINE + "\n")
    sys.stdout.write(_move_up(n_lines))
    sys.stdout.flush()


# -------------------------------------------------------------------------
def play(
    frames: Iterator[str],
    fps: float = 12.0,
    loop: bool = False,
    stream=None,
    sound_player: Optional[_SoundPlayerProtocol] = None,
) -> None:
    """Play an animation by driving a frame generator at a fixed fps.

    Renders frames in-place in the terminal using ANSI cursor control.
    Hides the cursor during playback and restores it on exit (including Ctrl+C).

    :param frames: Iterator/generator yielding one string per frame.
    :param fps: Playback speed in frames per second (default: 12.0).
    :param loop: If True, collect all frames then loop indefinitely until Ctrl+C.
    :param stream: Output stream (default: sys.stdout).
    :param sound_player: Optional SoundPlayer from justdoit.sound. If provided,
        start() is called before the loop, update(frame_idx, total) each frame,
        and stop() after. If None, playback is silent (default behaviour).
    """
    out = stream or sys.stdout
    frame_time = 1.0 / max(fps, 0.1)
    last_height = 0

    out.write(_HIDE_CURSOR)
    out.flush()

    try:
        if loop:
            all_frames = list(frames)
            if not all_frames:
                return
            total = len(all_frames)
            if sound_player is not None:
                sound_player.start()
            idx = 0
            while True:
                frame = all_frames[idx % total]
                _render_frame(out, frame, last_height)
                last_height = frame.count("\n") + 1
                if sound_player is not None:
                    sound_player.update(idx % total, total)
                idx += 1
                time.sleep(frame_time)
        else:
            all_frames = list(frames)
            total = len(all_frames)
            if sound_player is not None:
                sound_player.start()
            for idx, frame in enumerate(all_frames):
                _render_frame(out, frame, last_height)
                last_height = frame.count("\n") + 1
                if sound_player is not None:
                    sound_player.update(idx, total)
                time.sleep(frame_time)
    except KeyboardInterrupt:
        pass
    finally:
        if sound_player is not None:
            sound_player.stop()
        out.write(_SHOW_CURSOR)
        out.write("\n")
        out.flush()


# -------------------------------------------------------------------------
def _render_frame(out, frame: str, last_height: int) -> None:
    """Clear the previous frame and write the new one.

    :param out: Output stream.
    :param frame: The new frame string to render.
    :param last_height: Height of the previous frame (lines to clear).
    """
    if last_height > 0:
        _clear_frame(last_height)
    out.write(frame)
    out.flush()
