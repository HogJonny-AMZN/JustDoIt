"""
Package: justdoit.sound.player
Frame-synchronized audio player for JustDoIt animations.

Pre-mixes a waveform at animation start and plays it asynchronously
via sounddevice. The update() hook is called each frame by animate.player
and can be extended for envelope-phase-aware effects.
"""

import logging as _logging
from typing import Callable, Optional

import numpy as np

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.sound.player"
__updated__ = "2026-04-30 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
class SoundPlayer:
    """Pre-mixed waveform player synchronized to animation frames.

    Pre-mixes the provided waveform at construction time. Audio starts
    on start() and runs asynchronously — the animation loop drives timing,
    not the audio. update() is called each frame and is a no-op reserved
    for future envelope-phase-aware extensions.

    :param waveform: Pre-mixed float32 numpy array (full animation duration).
    :param sample_rate: Sample rate in Hz (default: 44100).
    :param _play_fn: Injectable play callback for testing.
        Called as _play_fn((waveform, sample_rate)). Default: sounddevice.play.
    :param _stop_fn: Injectable stop callback for testing.
        Called as _stop_fn(None). Default: sounddevice.stop.
    """

    def __init__(
        self,
        waveform: np.ndarray,
        sample_rate: int = 44100,
        _play_fn: Optional[Callable] = None,
        _stop_fn: Optional[Callable] = None,
    ) -> None:
        self._waveform = waveform
        self._sample_rate = sample_rate
        self._started = False

        if _play_fn is not None:
            self._play = lambda: _play_fn((waveform, sample_rate))
        else:
            def _default_play() -> None:
                import sounddevice as sd
                sd.play(self._waveform, self._sample_rate)
            self._play = _default_play

        if _stop_fn is not None:
            self._stop = lambda: _stop_fn(None)
        else:
            def _default_stop() -> None:
                import sounddevice as sd
                sd.stop()
            self._stop = _default_stop

    # -------------------------------------------------------------------------
    def start(self) -> None:
        """Begin async playback. Call once before the animation loop starts.

        Silently ignores duplicate start() calls.
        """
        if self._started:
            _LOGGER.warning("SoundPlayer.start() called while already playing — ignored")
            return
        self._play()
        self._started = True
        _LOGGER.debug("SoundPlayer: playback started (%d samples @ %dHz)",
                      len(self._waveform), self._sample_rate)

    # -------------------------------------------------------------------------
    def update(self, frame_idx: int, total_frames: int) -> None:
        """Advance audio envelope to match the current animation frame.

        Currently a no-op — audio runs asynchronously from start().
        Reserved for future envelope-phase-aware extensions.

        :param frame_idx: Current frame index (0-based).
        :param total_frames: Total frames in the animation.
        """

    # -------------------------------------------------------------------------
    def stop(self) -> None:
        """Stop playback. Safe to call even if start() was never called.

        :returns: None
        """
        if not self._started:
            return
        self._stop()
        self._started = False
        _LOGGER.debug("SoundPlayer: playback stopped")
