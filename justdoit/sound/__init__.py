"""
Package: justdoit.sound
Optional audio engine — procedural synthesis + frame-synchronized playback.

Gracefully unavailable when numpy or sounddevice are not installed.
All public API is no-op-safe when SOUND_AVAILABLE is False.
"""

import logging as _logging

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.sound"
__updated__ = "2026-04-30 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

# -------------------------------------------------------------------------
try:
    import numpy as _np  # noqa: F401
    import sounddevice as _sd  # noqa: F401
    from justdoit.sound.synth import (  # noqa: F401
        bandpass_noise,
        exponential_decay,
        pitch_waver,
        sawtooth_sweep,
        sine_sweep,
        sparkle_bursts,
    )
    from justdoit.sound.player import SoundPlayer  # noqa: F401
    SOUND_AVAILABLE: bool = True
except ImportError as _e:
    _LOGGER.debug("Sound unavailable: %s", _e)
    SOUND_AVAILABLE: bool = False
