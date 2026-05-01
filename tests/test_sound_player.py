"""
Tests for justdoit.sound.player.SoundPlayer.

SoundPlayer is tested without real audio hardware by injecting a
fake _play_fn. No sounddevice calls hit the OS in these tests.
"""
import pytest


def _make_player(duration: float = 1.0):
    """Return a SoundPlayer with a sine sweep waveform and fake play fn."""
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
        player.update(i, 24)


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
        _play_fn=lambda w: None,
        _stop_fn=stop_calls.append,
    )
    player.start()
    player.stop()
    assert len(stop_calls) == 1


def test_sound_player_not_started_stop_is_safe():
    """stop() before start() does not raise."""
    player, _ = _make_player()
    player.stop()
