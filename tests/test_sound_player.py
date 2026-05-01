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
        def start(self) -> None: pass
        def stop(self) -> None: pass
        def update(self, frame_idx: int, total_frames: int) -> None:
            update_calls.append((frame_idx, total_frames))

    sound = _TrackingPlayer(waveform, _play_fn=lambda _: None, _stop_fn=lambda _: None)
    anim_player.play(iter(["frame0\n", "frame1\n", "frame2\n"]), fps=100.0, sound_player=sound)

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
        def start(self) -> None: events.append("start")
        def stop(self) -> None: events.append("stop")
        def update(self, frame_idx: int, total_frames: int) -> None: pass  # noqa: ARG002

    sound = _TrackingPlayer(waveform, _play_fn=lambda _: None, _stop_fn=lambda _: None)
    anim_player.play(iter(["frame\n"]), fps=100.0, sound_player=sound)

    assert events == ["start", "stop"]


def test_animate_player_without_sound_player_unchanged():
    """animate.player.play() with no sound_player behaves identically to before."""
    import io
    from justdoit.animate import player as anim_player

    out = io.StringIO()
    anim_player.play(iter(["hello\n", "world\n"]), fps=100.0, stream=out)
    assert len(out.getvalue()) > 0
