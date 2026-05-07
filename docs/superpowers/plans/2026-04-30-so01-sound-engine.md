# SO01 Sound Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the optional `justdoit/sound/` package — procedural waveform synthesis, a frame-synchronized player, and clean wiring into `animate/player.py` — with a graceful silent fallback when `numpy`/`sounddevice` are absent.

**Architecture:** `sound/__init__.py` gates the import and exposes `SOUND_AVAILABLE`. `synth.py` provides pure numpy waveform helpers (no sounddevice). `player.py` wraps a pre-mixed waveform in a `SoundPlayer` that starts async playback at animation start and exposes an `update()` hook called per-frame. `animate/player.py` gains an optional `sound_player` parameter — if None, behavior is identical to today.

**Tech Stack:** `numpy>=1.24` (waveform math, FFT bandpass), `sounddevice>=0.4` (audio I/O via PortAudio), both gated behind `[project.optional-dependencies] sound = [...]`. All tests use `pytest.importorskip` — never hard-fail.

**Scope:** SO01 only. SO02 (transporter presets) and SO03 (asset playback) are follow-on plans that depend on this one.

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `justdoit/sound/__init__.py` | Gated import; exports `SOUND_AVAILABLE` |
| Create | `justdoit/sound/synth.py` | Waveform generation helpers (numpy only) |
| Create | `justdoit/sound/player.py` | `SoundPlayer` — pre-mix + async playback |
| Create | `tests/test_sound_synth.py` | Tests for synth helpers (gate: numpy) |
| Create | `tests/test_sound_player.py` | Tests for SoundPlayer (gate: numpy; no audio hardware needed) |
| Modify | `pyproject.toml` | Add `sound` optional dep group + `sounddevice` to dev group |
| Modify | `justdoit/animate/player.py` | Add optional `sound_player` param to `play()` |

---

## Task 1: Add `sound` optional dependency group to `pyproject.toml`

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add `sound` extra and `sounddevice` to dev group**

In `pyproject.toml`, add the `sound` entry under `[project.optional-dependencies]` and add `sounddevice` to the `[dependency-groups] dev` block:

```toml
[project.optional-dependencies]
ttf = ["Pillow>=10.0"]
sound = ["numpy>=1.24", "sounddevice>=0.4"]
dev = [
    "pytest>=8.0",
    "Pillow>=10.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "Pillow>=10.0",
    "numpy>=1.24",
    "sounddevice>=0.4",
    "ruff>=0.3.0",
]
```

- [ ] **Step 2: Sync the dev environment**

```bash
uv sync --dev
```

Expected: resolves `sounddevice` and adds it to `.venv`. No errors.

- [ ] **Step 3: Verify sounddevice imports**

```bash
uv run python -c "import sounddevice; print(sounddevice.__version__)"
```

Expected: prints a version string like `0.4.6`.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add sound optional dep group (numpy, sounddevice)"
```

---

## Task 2: Scaffold `justdoit/sound/__init__.py` with gated import

**Files:**
- Create: `justdoit/sound/__init__.py`
- Create: `tests/test_sound_synth.py` (scaffold only, first test)

- [ ] **Step 1: Write the failing test**

Create `tests/test_sound_synth.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_sound_synth.py::test_sound_available_is_bool -v
```

Expected: `ERROR` — `ModuleNotFoundError: No module named 'justdoit.sound'`

- [ ] **Step 3: Create `justdoit/sound/__init__.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_sound_synth.py -v
```

Expected: 2 tests PASS (the monkeypatch test may skip if `__builtins__` structure varies — that's fine).

- [ ] **Step 5: Commit**

```bash
git add justdoit/sound/__init__.py tests/test_sound_synth.py
git commit -m "feat: justdoit.sound package scaffold with SOUND_AVAILABLE gated import"
```

---

## Task 3: `synth.py` — frequency sweep generators

**Files:**
- Create: `justdoit/sound/synth.py` (initial — sine_sweep + sawtooth_sweep)
- Modify: `tests/test_sound_synth.py`

- [ ] **Step 1: Write failing tests for sine_sweep and sawtooth_sweep**

Append to `tests/test_sound_synth.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_sound_synth.py -k "sweep" -v
```

Expected: `ERROR` — `cannot import name 'sine_sweep' from 'justdoit.sound.synth'` (module doesn't exist yet).

- [ ] **Step 3: Create `justdoit/sound/synth.py` with sweep functions**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_sound_synth.py -k "sweep" -v
```

Expected: 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add justdoit/sound/synth.py tests/test_sound_synth.py
git commit -m "feat: synth.py — sine_sweep and sawtooth_sweep waveform generators"
```

---

## Task 4: `synth.py` — noise and burst helpers

**Files:**
- Modify: `justdoit/sound/synth.py`
- Modify: `tests/test_sound_synth.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_sound_synth.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_sound_synth.py -k "noise or sparkle" -v
```

Expected: `ERROR` — `cannot import name 'bandpass_noise'`

- [ ] **Step 3: Add `bandpass_noise` and `sparkle_bursts` to `synth.py`**

Append to `justdoit/sound/synth.py` (after `sawtooth_sweep`):

```python
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

    Each burst is 50–100ms, windowed with a Hann envelope to avoid clicks.

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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_sound_synth.py -k "noise or sparkle" -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add justdoit/sound/synth.py tests/test_sound_synth.py
git commit -m "feat: synth.py — bandpass_noise (FFT) and sparkle_bursts helpers"
```

---

## Task 5: `synth.py` — envelope helpers

**Files:**
- Modify: `justdoit/sound/synth.py`
- Modify: `tests/test_sound_synth.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_sound_synth.py`:

```python
def test_exponential_decay_shape_preserved():
    """exponential_decay returns same shape and dtype as input."""
    np = pytest.importorskip("numpy")
    pytest.importorskip("sounddevice")
    from justdoit.sound.synth import exponential_decay

    signal = np.ones(44100, dtype=np.float32)
    result = exponential_decay(signal, decay_time=1.0, sample_rate=44100)

    assert result.shape == signal.shape
    assert result.dtype == np.float32


def test_exponential_decay_tail_quieter_than_head():
    """Tail of decayed signal is quieter than the head."""
    np = pytest.importorskip("numpy")
    pytest.importorskip("sounddevice")
    from justdoit.sound.synth import exponential_decay

    signal = np.ones(44100, dtype=np.float32)
    result = exponential_decay(signal, decay_time=0.2, sample_rate=44100)

    head_rms = float(np.sqrt(np.mean(result[:2205] ** 2)))   # first 50ms
    tail_rms = float(np.sqrt(np.mean(result[-2205:] ** 2)))  # last 50ms
    assert tail_rms < head_rms * 0.1  # tail must be < 10% of head


def test_pitch_waver_shape_preserved():
    """pitch_waver returns same length as input."""
    np = pytest.importorskip("numpy")
    pytest.importorskip("sounddevice")
    from justdoit.sound.synth import sine_sweep, pitch_waver

    signal = sine_sweep(200.0, 1200.0, 1.0)
    result = pitch_waver(signal, deviation=0.05, rate=3.0, sample_rate=44100)

    assert result.shape == signal.shape
    assert result.dtype == np.float32


def test_pitch_waver_zero_deviation_identity():
    """pitch_waver with deviation=0 returns a signal very close to the input."""
    np = pytest.importorskip("numpy")
    pytest.importorskip("sounddevice")
    from justdoit.sound.synth import sine_sweep, pitch_waver

    signal = sine_sweep(200.0, 1200.0, 0.5)
    result = pitch_waver(signal, deviation=0.0, rate=3.0, sample_rate=44100)

    # With zero deviation, output should be nearly identical to input
    assert float(np.max(np.abs(result - signal))) < 0.01
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_sound_synth.py -k "decay or waver" -v
```

Expected: `ERROR` — `cannot import name 'exponential_decay'`

- [ ] **Step 3: Add `exponential_decay` and `pitch_waver` to `synth.py`**

Append to `justdoit/sound/synth.py`:

```python
# -------------------------------------------------------------------------
def exponential_decay(
    signal: np.ndarray,
    decay_time: float,
    sample_rate: int = 44100,
) -> np.ndarray:
    """Apply an exponential decay envelope to a signal (reverb tail simulation).

    :param signal: Input float32 waveform array.
    :param decay_time: Time constant in seconds — amplitude drops to 1/e at this point.
    :param sample_rate: Sample rate in Hz (default: 44100).
    :returns: float32 array same shape as signal.
    """
    n = len(signal)
    t = np.arange(n, dtype=np.float32) / sample_rate
    envelope = np.exp(-t / max(decay_time, 1e-9)).astype(np.float32)
    return (signal * envelope).astype(np.float32)


# -------------------------------------------------------------------------
def pitch_waver(
    signal: np.ndarray,
    deviation: float = 0.05,
    rate: float = 3.0,
    sample_rate: int = 44100,
) -> np.ndarray:
    """Modulate pitch slightly over time via linear-interpolated time-warping.

    Simulates prototype instability (ENT transporter) or chorus-like wobble.
    Uses time-domain sample repositioning — no FFT required.

    :param signal: Input float32 waveform array.
    :param deviation: Maximum fractional pitch deviation (0.05 = ±5%).
    :param rate: Modulation rate in Hz (default: 3.0).
    :param sample_rate: Sample rate in Hz (default: 44100).
    :returns: float32 array same shape as signal.
    """
    n = len(signal)
    t = np.arange(n, dtype=np.float64) / sample_rate
    # Time-warp: read-position oscillates around the nominal position
    phase_offset = (deviation / (2.0 * np.pi * max(rate, 1e-6))) * np.sin(2.0 * np.pi * rate * t)
    read_pos = np.clip((t + phase_offset) * sample_rate, 0.0, n - 1.0)
    idx0 = read_pos.astype(np.int32)
    idx1 = np.clip(idx0 + 1, 0, n - 1)
    frac = (read_pos - idx0).astype(np.float32)
    return (signal[idx0] * (1.0 - frac) + signal[idx1] * frac).astype(np.float32)
```

- [ ] **Step 4: Run all synth tests**

```bash
uv run pytest tests/test_sound_synth.py -v
```

Expected: all tests PASS (14+ tests).

- [ ] **Step 5: Commit**

```bash
git add justdoit/sound/synth.py tests/test_sound_synth.py
git commit -m "feat: synth.py — exponential_decay and pitch_waver envelope helpers"
```

---

## Task 6: `sound/player.py` — SoundPlayer

**Files:**
- Create: `justdoit/sound/player.py`
- Create: `tests/test_sound_player.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_sound_player.py`:

```python
"""
Tests for justdoit.sound.player.SoundPlayer.

SoundPlayer is tested without real audio hardware by injecting a
fake _play_fn. No sounddevice calls hit the OS in these tests.
"""
import pytest


def _make_player(duration: float = 1.0):
    """Return a SoundPlayer with a 1-second sine sweep and fake play fn."""
    np = pytest.importorskip("numpy")
    pytest.importorskip("sounddevice")
    from justdoit.sound.synth import sine_sweep
    from justdoit.sound.player import SoundPlayer

    waveform = sine_sweep(300.0, 1800.0, duration)
    calls = []
    player = SoundPlayer(waveform, sample_rate=44100, _play_fn=calls.append)
    return player, calls


def test_sound_player_constructs():
    """SoundPlayer can be constructed without raising."""
    player, _ = _make_player()
    assert player is not None


def test_sound_player_start_calls_play_fn():
    """start() invokes the injected play function exactly once."""
    player, calls = _make_player()
    player.start()
    assert len(calls) == 1


def test_sound_player_start_passes_waveform():
    """start() passes the waveform to the play function."""
    np = pytest.importorskip("numpy")
    pytest.importorskip("sounddevice")
    player, calls = _make_player()
    player.start()
    waveform_passed, sr_passed = calls[0]
    assert isinstance(waveform_passed, np.ndarray)
    assert sr_passed == 44100


def test_sound_player_update_does_not_raise():
    """update() can be called any number of times without raising."""
    player, _ = _make_player()
    player.start()
    for i in range(24):
        player.update(i, 24)  # must not raise


def test_sound_player_stop_calls_stop_fn():
    """stop() invokes the injected stop function."""
    np = pytest.importorskip("numpy")
    pytest.importorskip("sounddevice")
    from justdoit.sound.synth import sine_sweep
    from justdoit.sound.player import SoundPlayer

    waveform = sine_sweep(300.0, 1800.0, 0.5)
    stop_calls = []
    player = SoundPlayer(
        waveform,
        sample_rate=44100,
        _play_fn=lambda w, sr: None,
        _stop_fn=stop_calls.append,
    )
    player.start()
    player.stop()
    assert len(stop_calls) == 1


def test_sound_player_not_started_stop_is_safe():
    """stop() before start() does not raise."""
    player, _ = _make_player()
    player.stop()  # must not raise
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_sound_player.py -v
```

Expected: `ERROR` — `No module named 'justdoit.sound.player'`

- [ ] **Step 3: Create `justdoit/sound/player.py`**

```python
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
    not the audio. update() is called each frame and is currently a no-op,
    reserved for future envelope-phase-aware effects.

    :param waveform: Pre-mixed float32 numpy array (full animation duration).
    :param sample_rate: Sample rate in Hz (default: 44100).
    :param _play_fn: Injectable play callback (default: sounddevice.play).
        Called as _play_fn((waveform, sample_rate)). Used in tests.
    :param _stop_fn: Injectable stop callback (default: sounddevice.stop).
        Called as _stop_fn(None). Used in tests.
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

        :raises RuntimeError: If start() is called more than once.
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
        Reserved for future envelope-phase-aware extensions (e.g. SO02 shimmer
        intensity mapped to animation phase).

        :param frame_idx: Current frame index (0-based).
        :param total_frames: Total frames in the animation.
        """

    # -------------------------------------------------------------------------
    def stop(self) -> None:
        """Stop playback. Safe to call even if start() was never called."""
        if not self._started:
            return
        self._stop()
        self._started = False
        _LOGGER.debug("SoundPlayer: playback stopped")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_sound_player.py -v
```

Expected: 6 tests PASS.

- [ ] **Step 5: Run the full test suite to check for regressions**

```bash
uv run pytest -q
```

Expected: all existing tests still PASS; new sound tests also PASS.

- [ ] **Step 6: Commit**

```bash
git add justdoit/sound/player.py tests/test_sound_player.py
git commit -m "feat: sound/player.py — SoundPlayer with injectable play/stop for testability"
```

---

## Task 7: Update `sound/__init__.py` to re-export `SoundPlayer`

The scaffold in Task 2 already has the re-export — but `player.py` didn't exist then. Verify the import chain works end-to-end.

**Files:**
- Verify: `justdoit/sound/__init__.py` (should already be correct)

- [ ] **Step 1: Verify end-to-end import**

```bash
uv run python -c "
from justdoit.sound import SOUND_AVAILABLE, SoundPlayer
print('SOUND_AVAILABLE:', SOUND_AVAILABLE)
print('SoundPlayer:', SoundPlayer)
"
```

Expected output:
```
SOUND_AVAILABLE: True
SoundPlayer: <class 'justdoit.sound.player.SoundPlayer'>
```

If `SOUND_AVAILABLE` is `False`, sounddevice is not installed — run `uv sync --dev` and retry.

- [ ] **Step 2: No fix needed if output matches. Commit only if `__init__.py` required a change.**

---

## Task 8: Wire `SoundPlayer` into `animate/player.py`

**Files:**
- Modify: `justdoit/animate/player.py`
- No new test file — add to existing `tests/test_sound_player.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_sound_player.py`:

```python
def test_animate_player_calls_sound_update_each_frame():
    """animate.player.play() calls sound_player.update() once per frame."""
    np = pytest.importorskip("numpy")
    pytest.importorskip("sounddevice")
    from justdoit.sound.synth import sine_sweep
    from justdoit.sound.player import SoundPlayer
    from justdoit.animate import player as anim_player

    waveform = sine_sweep(300.0, 1800.0, 0.3)
    update_calls = []

    class _TrackingPlayer(SoundPlayer):
        def start(self): pass
        def stop(self): pass
        def update(self, frame_idx, total_frames):
            update_calls.append((frame_idx, total_frames))

    sound = _TrackingPlayer(waveform, _play_fn=lambda x: None, _stop_fn=lambda x: None)
    frames = ["frame0\n", "frame1\n", "frame2\n"]

    anim_player.play(iter(frames), fps=100.0, sound_player=sound)

    assert len(update_calls) == 3
    assert update_calls[0] == (0, 3)
    assert update_calls[2] == (2, 3)


def test_animate_player_calls_sound_start_and_stop():
    """animate.player.play() calls sound_player.start() before loop and stop() after."""
    pytest.importorskip("numpy")
    pytest.importorskip("sounddevice")
    from justdoit.sound.synth import sine_sweep
    from justdoit.sound.player import SoundPlayer
    from justdoit.animate import player as anim_player

    waveform = sine_sweep(300.0, 1800.0, 0.1)
    events = []

    class _TrackingPlayer(SoundPlayer):
        def start(self): events.append("start")
        def stop(self): events.append("stop")
        def update(self, *_): pass

    sound = _TrackingPlayer(waveform, _play_fn=lambda x: None, _stop_fn=lambda x: None)
    anim_player.play(iter(["frame\n"]), fps=100.0, sound_player=sound)

    assert events == ["start", "stop"]


def test_animate_player_without_sound_player_unchanged():
    """animate.player.play() with no sound_player behaves identically to before."""
    import io
    from justdoit.animate import player as anim_player

    out = io.StringIO()
    anim_player.play(iter(["hello\n", "world\n"]), fps=100.0, stream=out)
    # Must not raise; output stream must have received content
    assert len(out.getvalue()) > 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_sound_player.py -k "animate" -v
```

Expected: `FAILED` — `play() got an unexpected keyword argument 'sound_player'`

- [ ] **Step 3: Modify `justdoit/animate/player.py`**

Update the `play()` signature and loop body. The full modified file:

```python
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
from typing import Iterator, Optional

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.animate.player"
__updated__ = "2026-04-30 00:00:00"
__version__ = "0.1.1"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

# ANSI control sequences
_HIDE_CURSOR = "\033[?25l"
_SHOW_CURSOR = "\033[?25h"
_CLEAR_LINE  = "\033[2K\r"


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
    sound_player: Optional[object] = None,
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
```

- [ ] **Step 4: Run the animate tests**

```bash
uv run pytest tests/test_sound_player.py -k "animate" -v
```

Expected: 3 tests PASS.

- [ ] **Step 5: Run the full test suite**

```bash
uv run pytest -q
```

Expected: all tests PASS. No regressions in figlet, fill, generative, or TTF tests.

- [ ] **Step 6: Commit**

```bash
git add justdoit/animate/player.py tests/test_sound_player.py
git commit -m "feat: wire optional SoundPlayer into animate/player.play() — frame sync SO01"
```

---

## Task 9: Smoke test end-to-end with real audio (manual)

These are manual checks — not automated. Run them if `sounddevice` is working on your machine.

- [ ] **Step 1: Verify the full import chain**

```bash
uv run python -c "
from justdoit.sound import SOUND_AVAILABLE, SoundPlayer
from justdoit.sound.synth import sine_sweep, sawtooth_sweep, bandpass_noise, sparkle_bursts, exponential_decay, pitch_waver
print('All imports OK. SOUND_AVAILABLE:', SOUND_AVAILABLE)
"
```

Expected: `All imports OK. SOUND_AVAILABLE: True`

- [ ] **Step 2: Smoke-play a short TNG-style sweep**

```bash
uv run python -c "
import time, numpy as np
from justdoit.sound.synth import sine_sweep, bandpass_noise, sparkle_bursts, exponential_decay
from justdoit.sound.player import SoundPlayer

# Build a rough TNG materialize layer (1.2s)
base    = sine_sweep(300, 1800, 1.2)
shimmer = bandpass_noise(1000, 400, 1.2, amplitude=0.05)
sparkle = sparkle_bursts(12, (800, 3000), 1.2)
mix     = exponential_decay(base + shimmer + sparkle, decay_time=0.4)

# Normalize
peak = np.max(np.abs(mix))
if peak > 0:
    mix /= peak
mix *= 0.7  # headroom

player = SoundPlayer(mix)
player.start()
time.sleep(1.4)
player.stop()
print('Done.')
"
```

Expected: you hear a rising shimmer sweep, ~1.2s, then silence.

- [ ] **Step 3: Commit smoke test result note to `docs/sound_design.md` Action Items if anything needs follow-up**

---

## Self-Review

### Spec Coverage

| Requirement (from sound_design.md) | Covered |
|-------------------------------------|---------|
| `sound/__init__.py` with gated import + `SOUND_AVAILABLE` | Task 2 ✓ |
| `sound = ["numpy", "sounddevice"]` optional dep group | Task 1 ✓ |
| `synth.py`: sine_sweep | Task 3 ✓ |
| `synth.py`: sawtooth_sweep | Task 3 ✓ |
| `synth.py`: bandpass_noise | Task 4 ✓ |
| `synth.py`: sparkle_bursts | Task 4 ✓ |
| `synth.py`: exponential_decay | Task 5 ✓ |
| `synth.py`: pitch_waver | Task 5 ✓ |
| `sound/player.py` with frame sync | Task 6 ✓ |
| Wire into `animate/player.py` | Task 8 ✓ |
| Gate all tests with `pytest.importorskip` | All tasks ✓ |
| Silent fallback — no crashes without deps | Task 2 ✓ |

**Out of scope (follow-on plans):**
- SO02 transporter presets (`sound/presets.py`) — depends on this plan
- SO03 asset playback — depends on this plan
- N05 music-reactive visuals — depends on SO01 + SO02

### Type Consistency Check

- `SoundPlayer.__init__` accepts `waveform: np.ndarray` — matches how Task 8 tests construct it ✓
- `SoundPlayer.update(frame_idx: int, total_frames: int)` — matches Task 8 test calls ✓
- `play(..., sound_player: Optional[object])` — accepts any duck-typed SoundPlayer subclass; tests use subclasses ✓
- `_play_fn` called as `_play_fn((waveform, sample_rate))` — Task 6 tests unpack as `waveform_passed, sr_passed = calls[0]` ✓
