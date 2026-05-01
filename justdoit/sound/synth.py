"""
Package: justdoit.sound.synth
Procedural waveform synthesis helpers for the JustDoIt sound engine.

All functions return float32 numpy arrays at the given sample_rate.
Requires numpy — import is not gated here; callers must ensure SOUND_AVAILABLE.
"""

import logging as _logging

import numpy as np

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.sound.synth"
__updated__ = "2026-04-30 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
def sine_sweep(
    f_start: float,
    f_end: float,
    duration: float,
    sample_rate: int = 44100,
) -> np.ndarray:
    """Linear frequency sweep between two frequencies using a sine waveform.

    :param f_start: Start frequency in Hz.
    :param f_end: End frequency in Hz.
    :param duration: Duration in seconds.
    :param sample_rate: Sample rate in Hz (default: 44100).
    :returns: float32 array of length int(sample_rate * duration).
    """
    n = int(sample_rate * duration)
    t = np.linspace(0.0, duration, n, endpoint=False)
    # Instantaneous phase: integral of 2π * f(t) where f(t) ramps linearly
    phase = 2.0 * np.pi * (f_start * t + (f_end - f_start) * t ** 2 / (2.0 * duration))
    return np.sin(phase).astype(np.float32)


# -------------------------------------------------------------------------
def sawtooth_sweep(
    f_start: float,
    f_end: float,
    duration: float,
    sample_rate: int = 44100,
) -> np.ndarray:
    """Linear frequency sweep using a sawtooth waveform (TOS 'electrical' quality).

    :param f_start: Start frequency in Hz.
    :param f_end: End frequency in Hz.
    :param duration: Duration in seconds.
    :param sample_rate: Sample rate in Hz (default: 44100).
    :returns: float32 array of length int(sample_rate * duration), values in [-1, 1].
    """
    n = int(sample_rate * duration)
    t = np.linspace(0.0, duration, n, endpoint=False)
    # Accumulated cycles: same chirp phase as sine_sweep divided by 2π
    cycles = f_start * t + (f_end - f_start) * t ** 2 / (2.0 * duration)
    # Sawtooth: map fractional cycle to [-1, 1]
    return (2.0 * (cycles - np.floor(cycles)) - 1.0).astype(np.float32)
