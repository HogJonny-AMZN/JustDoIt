"""
Package: justdoit.sound
Optional audio engine — procedural synthesis + frame-synchronized playback.

Gracefully unavailable when numpy or sounddevice are not installed (including
when PortAudio is missing, which raises OSError on sounddevice import).
When SOUND_AVAILABLE is False, only that flag is exported — SoundPlayer and
the synth helpers are not defined. Check SOUND_AVAILABLE before importing them.
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
except (ImportError, OSError) as _e:
    _LOGGER.info("Sound module unavailable (requires numpy + sounddevice): %s", _e)
    SOUND_AVAILABLE: bool = False
