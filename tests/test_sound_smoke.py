"""
Manual smoke test for the SO01 sound engine.

Requires real audio hardware (speakers/headphones). Excluded from CI.
Run via: uv run pytest tests/test_sound_smoke.py -v -s
      or: tests\\launch\\smoke_sound.bat
"""
import time

import pytest


@pytest.mark.manual
def test_tng_transporter_sweep():
    """Play a TNG-style transporter materialize sweep and verify it completes.

    Expected: ~1.2s rising shimmer sweep audible through speakers.
    Pass criterion: no exception raised; SoundPlayer starts and stops cleanly.
    """
    np = pytest.importorskip("numpy")
    pytest.importorskip("sounddevice")
    from justdoit.sound.synth import (
        bandpass_noise,
        exponential_decay,
        sine_sweep,
        sparkle_bursts,
    )
    from justdoit.sound.player import SoundPlayer

    duration = 1.2
    sample_rate = 44100

    base    = sine_sweep(300.0, 1800.0, duration, sample_rate=sample_rate)
    shimmer = bandpass_noise(1000.0, 400.0, duration, amplitude=0.05, sample_rate=sample_rate)
    sparkle = sparkle_bursts(12, (800.0, 3000.0), duration, sample_rate=sample_rate)
    mix     = exponential_decay(base + shimmer + sparkle, decay_time=0.4, sample_rate=sample_rate)

    peak = float(np.max(np.abs(mix)))
    if peak > 1e-9:
        mix = mix / peak
    mix = (mix * 0.7).astype(np.float32)

    player = SoundPlayer(mix, sample_rate=sample_rate)
    player.start()
    time.sleep(duration + 0.3)  # slight tail for reverb decay
    player.stop()


@pytest.mark.manual
def test_tos_transporter_sweep():
    """Play a TOS-style transporter sweep (sawtooth, faster, drier) and verify it completes.

    Expected: ~0.8s sharper electrical sweep.
    Pass criterion: no exception raised.
    """
    np = pytest.importorskip("numpy")
    pytest.importorskip("sounddevice")
    from justdoit.sound.synth import (
        bandpass_noise,
        exponential_decay,
        sawtooth_sweep,
    )
    from justdoit.sound.player import SoundPlayer

    duration = 0.8
    sample_rate = 44100

    base    = sawtooth_sweep(150.0, 2500.0, duration, sample_rate=sample_rate)
    noise   = bandpass_noise(1200.0, 600.0, duration, amplitude=0.15, sample_rate=sample_rate)
    mix     = exponential_decay(base + noise, decay_time=0.1, sample_rate=sample_rate)

    peak = float(np.max(np.abs(mix)))
    if peak > 1e-9:
        mix = mix / peak
    mix = (mix * 0.7).astype(np.float32)

    player = SoundPlayer(mix, sample_rate=sample_rate)
    player.start()
    time.sleep(duration + 0.1)
    player.stop()


@pytest.mark.manual
def test_ent_transporter_sweep():
    """Play an ENT-style transporter sweep (slow, uncertain, with pitch waver).

    Expected: ~2.0s anxious, slightly unstable sweep.
    Pass criterion: no exception raised.
    """
    np = pytest.importorskip("numpy")
    pytest.importorskip("sounddevice")
    from justdoit.sound.synth import (
        bandpass_noise,
        exponential_decay,
        pitch_waver,
        sine_sweep,
    )
    from justdoit.sound.player import SoundPlayer

    duration = 2.0
    sample_rate = 44100

    base    = sine_sweep(200.0, 1200.0, duration, sample_rate=sample_rate)
    wobbly  = pitch_waver(base, deviation=0.05, rate=2.5, sample_rate=sample_rate)
    noise   = bandpass_noise(700.0, 500.0, duration, amplitude=0.2, sample_rate=sample_rate)
    mix     = exponential_decay(wobbly + noise, decay_time=0.8, sample_rate=sample_rate)

    peak = float(np.max(np.abs(mix)))
    if peak > 1e-9:
        mix = mix / peak
    mix = (mix * 0.7).astype(np.float32)

    player = SoundPlayer(mix, sample_rate=sample_rate)
    player.start()
    time.sleep(duration + 0.2)
    player.stop()
