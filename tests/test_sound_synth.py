"""
Tests for justdoit.sound — gated on numpy and sounddevice availability.
"""
import pytest


def test_sound_available_is_bool():
    """SOUND_AVAILABLE must be a bool regardless of whether deps are installed."""
    from justdoit.sound import SOUND_AVAILABLE
    assert isinstance(SOUND_AVAILABLE, bool)


def test_sound_import_does_not_crash_without_deps(monkeypatch):
    """Importing justdoit.sound must never raise even if numpy/sounddevice absent."""
    import sys
    # Remove cached module so the import re-runs
    for key in list(sys.modules):
        if key.startswith("justdoit.sound"):
            del sys.modules[key]
    # Patch numpy import to fail
    real_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

    def fake_import(name, *args, **kwargs):
        if name in ("numpy", "sounddevice"):
            raise ImportError(f"Fake missing: {name}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)
    from justdoit import sound  # noqa: F401  — must not raise
    assert sound.SOUND_AVAILABLE is False


def test_sine_sweep_shape_and_dtype():
    """sine_sweep returns float32 array of correct length."""
    np = pytest.importorskip("numpy")
    pytest.importorskip("sounddevice")
    from justdoit.sound.synth import sine_sweep

    result = sine_sweep(300.0, 1800.0, 1.0, sample_rate=44100)

    assert isinstance(result, np.ndarray)
    assert result.dtype == np.float32
    assert result.shape == (44100,)


def test_sine_sweep_amplitude_bounded():
    """sine_sweep values stay within [-1, 1]."""
    pytest.importorskip("numpy")
    pytest.importorskip("sounddevice")
    from justdoit.sound.synth import sine_sweep

    result = sine_sweep(300.0, 1800.0, 0.5, sample_rate=44100)

    assert result.max() <= 1.0
    assert result.min() >= -1.0


def test_sine_sweep_duration_scaling():
    """Output length scales correctly with duration and sample_rate."""
    pytest.importorskip("numpy")
    pytest.importorskip("sounddevice")
    from justdoit.sound.synth import sine_sweep

    assert sine_sweep(300.0, 1800.0, 0.1, sample_rate=8000).shape == (800,)
    assert sine_sweep(300.0, 1800.0, 2.0, sample_rate=22050).shape == (44100,)


def test_sawtooth_sweep_shape_and_dtype():
    """sawtooth_sweep returns float32 array of correct length."""
    np = pytest.importorskip("numpy")
    pytest.importorskip("sounddevice")
    from justdoit.sound.synth import sawtooth_sweep

    result = sawtooth_sweep(150.0, 2500.0, 0.8, sample_rate=44100)

    assert isinstance(result, np.ndarray)
    assert result.dtype == np.float32
    assert result.shape == (int(0.8 * 44100),)


def test_sawtooth_sweep_amplitude_bounded():
    """sawtooth_sweep values stay within [-1, 1]."""
    pytest.importorskip("numpy")
    pytest.importorskip("sounddevice")
    from justdoit.sound.synth import sawtooth_sweep

    result = sawtooth_sweep(150.0, 2500.0, 0.5)

    assert result.max() <= 1.0
    assert result.min() >= -1.0


def test_bandpass_noise_shape_and_dtype():
    """bandpass_noise returns float32 array of correct length."""
    np = pytest.importorskip("numpy")
    pytest.importorskip("sounddevice")
    from justdoit.sound.synth import bandpass_noise

    result = bandpass_noise(1000.0, 200.0, 0.5, amplitude=0.1, sample_rate=44100)

    assert isinstance(result, np.ndarray)
    assert result.dtype == np.float32
    assert result.shape == (int(0.5 * 44100),)


def test_bandpass_noise_amplitude():
    """bandpass_noise RMS is close to the requested amplitude."""
    np = pytest.importorskip("numpy")
    pytest.importorskip("sounddevice")
    from justdoit.sound.synth import bandpass_noise

    target = 0.1
    result = bandpass_noise(1000.0, 200.0, 1.0, amplitude=target, sample_rate=44100)
    rms = float(np.sqrt(np.mean(result ** 2)))

    assert abs(rms - target) < 0.02  # within 20% of target


def test_sparkle_bursts_shape_and_dtype():
    """sparkle_bursts returns float32 array of correct length."""
    np = pytest.importorskip("numpy")
    pytest.importorskip("sounddevice")
    from justdoit.sound.synth import sparkle_bursts

    result = sparkle_bursts(10, (800.0, 3000.0), 1.2, sample_rate=44100)

    assert isinstance(result, np.ndarray)
    assert result.dtype == np.float32
    assert result.shape == (int(1.2 * 44100),)


def test_sparkle_bursts_zero_count():
    """sparkle_bursts with count=0 returns a silent array."""
    np = pytest.importorskip("numpy")
    pytest.importorskip("sounddevice")
    from justdoit.sound.synth import sparkle_bursts

    result = sparkle_bursts(0, (800.0, 3000.0), 0.5)

    assert np.all(result == 0.0)
