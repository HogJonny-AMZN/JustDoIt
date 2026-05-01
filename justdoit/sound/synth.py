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


# -------------------------------------------------------------------------
def bandpass_noise(
    center_hz: float,
    bandwidth_hz: float,
    duration: float,
    amplitude: float = 0.1,
    sample_rate: int = 44100,
) -> np.ndarray:
    """White noise filtered to a frequency band via FFT (shimmer/noise layer).

    Uses FFT zeroing — no scipy required. RMS is normalized to amplitude.

    :param center_hz: Centre frequency of the passband in Hz.
    :param bandwidth_hz: Width of the passband in Hz.
    :param duration: Duration in seconds.
    :param amplitude: Target RMS amplitude (default: 0.1).
    :param sample_rate: Sample rate in Hz (default: 44100).
    :returns: float32 array of length int(sample_rate * duration).
    """
    n = int(sample_rate * duration)
    noise = np.random.default_rng().standard_normal(n).astype(np.float32)
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)
    spectrum = np.fft.rfft(noise)
    lo = center_hz - bandwidth_hz / 2.0
    hi = center_hz + bandwidth_hz / 2.0
    spectrum[(freqs < lo) | (freqs > hi)] = 0.0
    filtered = np.fft.irfft(spectrum, n=n).astype(np.float32)
    rms = float(np.sqrt(np.mean(filtered ** 2)))
    if rms > 1e-9:
        filtered *= amplitude / rms
    return filtered


# -------------------------------------------------------------------------
def sparkle_bursts(
    count: int,
    freq_range: tuple,
    duration: float,
    sample_rate: int = 44100,
) -> np.ndarray:
    """Random short sine bursts scattered across a duration (TNG sparkle layer).

    Each burst is ~75ms, windowed with a Hann envelope to avoid clicks.

    :param count: Number of bursts to scatter.
    :param freq_range: (low_hz, high_hz) range for random burst frequencies.
    :param duration: Total duration in seconds.
    :param sample_rate: Sample rate in Hz (default: 44100).
    :returns: float32 array of length int(sample_rate * duration).
    """
    n = int(sample_rate * duration)
    output = np.zeros(n, dtype=np.float32)
    if count == 0:
        return output
    rng = np.random.default_rng()
    burst_len = int(0.075 * sample_rate)  # 75ms per burst
    t_burst = np.arange(burst_len) / sample_rate
    window = np.hanning(burst_len).astype(np.float32)
    for _ in range(count):
        freq = rng.uniform(freq_range[0], freq_range[1])
        onset = rng.integers(0, max(1, n - burst_len))
        burst = (np.sin(2.0 * np.pi * freq * t_burst) * window).astype(np.float32)
        amplitude = rng.uniform(0.02, 0.08)
        end = min(onset + burst_len, n)
        output[onset:end] += burst[: end - onset] * amplitude
    return output
