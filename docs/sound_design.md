# Sound Design — Design Document

**Status:** Design / Pre-implementation  
**Created:** 2026-03-29  
**Author:** NumberOne + Jonny Galloway  
**Technique IDs:** SO01, SO02, SO03 (see TECHNIQUES.md)

---

## Overview

Sound is optional, gracefully degraded, and frame-synchronized. A great silent
animation beats a mediocre one with audio. But a great animation with
canon-accurate audio is a different creature entirely.

The sound system has three layers:

| Layer | Technique | Description |
|-------|-----------|-------------|
| Engine | SO01 | Core audio I/O — procedural synthesis, frame sync, silent fallback |
| Synth effects | SO02 | Procedurally generated sounds (Trek transporter, etc.) |
| Asset playback | SO03 | WAV/OGG file playback for pre-recorded effects |

---

## SO01 — Synthesized Sound Engine

### Architecture

```
justdoit/sound/
  __init__.py       # gated import, SOUND_AVAILABLE flag
  synth.py          # procedural tone generation (numpy + sounddevice)
  player.py         # frame-synchronized playback
  presets.py        # named sound presets (transporter_tos, transporter_tng, etc.)
  assets/           # optional: bundled WAV/OGG files for SO03
```

### Gated Import Pattern

```python
try:
    from justdoit.sound import player
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False
```

If `sounddevice` or `numpy` are absent, all sound calls are no-ops. The
animation runs silently at the same timing. No crashes, no warnings to the
user unless they explicitly requested audio.

### Dependencies

Both pre-approved per ADR-006:

| Package | Score | Role |
|---------|-------|------|
| `numpy` | 25/25 | Waveform generation, FFT, signal processing |
| `sounddevice` | 16/25 | Audio I/O (PortAudio binding) |

Install via optional dep group:
```bash
uv sync --extra sound
```

`pyproject.toml`:
```toml
[project.optional-dependencies]
sound = ["numpy", "sounddevice"]
```

### Frame Sync

The animation player calls `sound.player.update(frame, total_frames)` each
frame. The player advances the audio envelope to match the current animation
phase. Timing is driven by the animation loop — audio follows, not leads.

```python
# In animation loop:
for frame_idx, frame in enumerate(frames):
    renderer.render(frame)
    if SOUND_AVAILABLE:
        sound.player.update(frame_idx, total_frames)
    time.sleep(frame_duration)
```

---

## SO02 — Transporter Beam Audio

Trek-specific synthesized sounds. Lives in `presets.py`. Each era has its own
envelope, frequency sweep, and noise characteristics.

> See `star_trek_effects.md` for the full Trek context — era variants, visual
> sync, and canon accuracy notes. This section covers the synthesis specs.

### TNG Transporter

```
Base:     Sine sweep 300Hz → 1800Hz over 1.2s (materialize)
Shimmer:  Bandpass-filtered white noise, -20dB below base
Sparkle:  Random short sine bursts (50–100ms), 800Hz–3kHz, very low amplitude
Tail:     Reverb simulation — exponential decay of base frequency
```

Warmest, most musical. The reference implementation. Nail this one first.

### TOS Transporter

```
Base:     Sharper sweep, 150Hz → 2500Hz over 0.8s
Waveform: Slightly sawtooth (not pure sine) — that's the "electrical" quality
Noise:    Higher ratio of white noise to tone vs. TNG
Reverb:   Minimal — dry room
```

Faster, drier, more raw. Less forgiving than TNG — the waveform shape matters.

### ENT Transporter (Prototype)

```
Base:     Slow, uncertain sweep — 200Hz → 1200Hz over 2.0s
Variation: Pitch wavers slightly (±5%) — prototype instability
Noise:    Higher noise floor throughout the sweep
Tail:     Brief descending tone at completion (prototype hiccup)
```

The anxiety is the effect. It should sound like it might not work.

### DS9 / VOY / Kelvin

> **[JONNY]** DS9 Cardassian and Bajoran transporter audio signatures —
> any production notes or reference you'd reach for? These are estimated
> until you weigh in.

Placeholders:
- **DS9 Cardassian:** harsher, more industrial — lower base frequency (~100Hz), more noise
- **DS9 Bajoran/Starfleet:** close to TNG, slightly warmer
- **Kelvin:** faster attack, more cinematic — shorter sweep, white-out flash correlation

### Synthesis Helper Functions (`synth.py`)

```python
def sine_sweep(f_start, f_end, duration, sample_rate=44100) -> np.ndarray:
    """Linear frequency sweep between two frequencies."""

def sawtooth_sweep(f_start, f_end, duration, sample_rate=44100) -> np.ndarray:
    """Sawtooth waveform frequency sweep (TOS 'electrical' quality)."""

def bandpass_noise(center_hz, bandwidth_hz, duration, amplitude=0.1, sample_rate=44100) -> np.ndarray:
    """White noise through bandpass filter (shimmer layer)."""

def sparkle_bursts(count, freq_range, duration, sample_rate=44100) -> np.ndarray:
    """Random short sine bursts scattered across a duration (TNG sparkle)."""

def exponential_decay(signal, decay_time, sample_rate=44100) -> np.ndarray:
    """Apply exponential decay envelope (reverb tail simulation)."""

def pitch_waver(signal, deviation=0.05, rate=3.0, sample_rate=44100) -> np.ndarray:
    """Modulate pitch slightly over time (ENT prototype instability)."""
```

---

## SO03 — Sound Asset Playback

For effects that can't be practically synthesized — or where a specific
pre-recorded sample is the right call.

### Architecture

```python
def play_asset(name: str, volume: float = 1.0) -> None:
    """Play a named sound asset from justdoit/sound/assets/.

    :param name: Asset name without extension (e.g. 'whoosh', 'beep').
    :param volume: Playback volume 0.0–1.0.
    Supported formats: WAV (always), OGG (if sounddevice supports it).
    Silent no-op if SOUND_AVAILABLE is False.
    """
```

Assets directory: `justdoit/sound/assets/`
- Bundled assets ship with the package (keep small — < 500KB total)
- User-provided assets: support a configurable search path

### Dependency

`pygame.mixer` is one option but heavy. Prefer `sounddevice` + `scipy.io.wavfile`
for WAV playback — already pre-approved, no new deps needed for basic asset support.

```python
import sounddevice as sd
from scipy.io import wavfile

def play_asset(name: str, volume: float = 1.0) -> None:
    path = _find_asset(name)
    sample_rate, data = wavfile.read(path)
    sd.play(data * volume, sample_rate)
```

---

## General Sound Design Principles

### For Animation-Paired Effects

- **Audio follows animation** — frame sync is non-negotiable
- **Silent-first** — visuals must work without sound; audio is enhancement
- **Phase-aware** — map animation phases (shimmer, scatter, lock-in, resolve) to
  audio envelope stages; they should feel unified, not incidentally timed
- **Duration match** — audio envelope duration = animation frame count / fps

### For Ambient / Looping Effects

- **Seamless loop** — ensure waveform phase matches at loop boundary
- **Subtle** — ambient audio should not fatigue; -12dB to -20dB below
  "foreground" effects is a reasonable starting point
- **Interruptible** — can be faded out cleanly when the effect ends

### For One-Shot Effects

- **Short** — < 500ms for UI feedback sounds
- **Non-blocking** — fire and forget; don't hold the animation loop
- **Falloff** — always apply a brief fade-out at the end to avoid clicks

---

## Future: Music-Reactive Visuals (N05)

`N05` in TECHNIQUES.md: ASCII art driven by audio FFT data. The sound engine
infrastructure (numpy, sounddevice) is the foundation for this. When N05
moves from `idea` to `planned`:

- `synth.py` already has the FFT tooling from synthesis work
- Add an input capture path: `sounddevice.InputStream` for mic/system audio
- Map FFT bins → zone brightness → character selection
- The glyph mask becomes a frequency visualizer

This is downstream — get SO01/SO02 solid first.

---

## Action Items

### NumberOne (implement)

- [ ] Implement `justdoit/sound/__init__.py` with gated import + `SOUND_AVAILABLE`
- [ ] Implement `justdoit/sound/synth.py` helper functions
- [ ] Implement `justdoit/sound/player.py` frame-sync player
- [ ] Implement `justdoit/sound/presets.py` — TNG first, then TOS, then ENT
- [ ] Implement `justdoit/sound/assets/` + SO03 playback
- [ ] Wire frame sync into animation loop
- [ ] Tests: `tests/test_sound_synth.py` — waveform shape, duration, sample rate
- [ ] Gate all sound tests with `pytest.importorskip("sounddevice")`

### Jonny — need your ear on these

- [ ] **[JONNY-S1]** DS9 Cardassian transporter audio — any production reference?
  Harsher/industrial is the working assumption.
- [ ] **[JONNY-S2]** TNG sparkle layer — the "musical" quality. Is that a specific
  harmonic interval or just random high-frequency bursts? Your ear will know.
- [ ] **[JONNY-S3]** ENT pitch waver — subtle tremolo or more pronounced? The prototype
  instability should read as *anxiety*, not malfunction.
- [ ] **[JONNY-S4]** Did the EF2 audio team work from Paramount reference material
  or reconstruct from scratch? Any frequency/envelope notes that survived?
- [ ] **[JONNY-S5]** Asset sounds beyond Trek — any non-Trek effects where a
  pre-recorded asset beats synthesis? (UI beeps, whooshes, etc.)

---

## Related Docs

- `star_trek_effects.md` — Trek visual + audio design, era variants, action items
- `animation_gallery.md` — APNG/cast export; sound does not appear in gallery artifacts
- `research/TECHNIQUES.md` — SO01/SO02/SO03 technique registry
- `decisions/ADR-001-zero-dependency-core.md` — dependency policy (numpy/sounddevice pre-approved)
- `decisions/ADR-006-dependency-approval-rubric.md` — rubric for future audio deps
