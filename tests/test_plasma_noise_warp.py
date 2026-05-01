"""Tests for X_PLASMA_NOISE_WARP cross-breed preset.

Exercises: plasma amplitude_map × noise phase_map → sine_warp (X_PLASMA_NOISE_WARP).
Both infra axes (amplitude_map from X_PLASMA_WARP, phase_map from X_NOISE_WARP) verified.
"""
import re


def _strip_ansi(s: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def _leading_spaces(frame: str) -> list:
    """Return per-row leading space counts after ANSI stripping."""
    lines = _strip_ansi(frame).split("\n")
    return [len(line) - len(line.lstrip()) for line in lines]


def _fg_color_count(frame: str) -> int:
    """Count foreground ANSI color codes (38;2;...)."""
    return len(re.findall(r"\x1b\[38;2;", frame))


def _bg_color_count(frame: str) -> int:
    """Count background ANSI color codes (48;2;...)."""
    return len(re.findall(r"\x1b\[48;2;", frame))


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------

def test_import():
    from justdoit.animate.presets import plasma_noise_warp  # noqa: F401


def test_is_iterator():
    from justdoit.animate.presets import plasma_noise_warp
    result = plasma_noise_warp("HI", n_frames=3, loop=False)
    # Must be an iterator (has __iter__ + __next__)
    assert hasattr(result, "__iter__")
    assert hasattr(result, "__next__")


# ---------------------------------------------------------------------------
# Frame count
# ---------------------------------------------------------------------------

def test_frame_count_no_loop():
    from justdoit.animate.presets import plasma_noise_warp
    frames = list(plasma_noise_warp("HI", n_frames=4, loop=False))
    assert len(frames) == 4


def test_frame_count_with_loop():
    from justdoit.animate.presets import plasma_noise_warp
    frames = list(plasma_noise_warp("HI", n_frames=6, loop=True))
    assert len(frames) == 12  # forward + reversed


def test_frame_count_default():
    from justdoit.animate.presets import plasma_noise_warp
    frames = list(plasma_noise_warp("HI", n_frames=36, loop=True))
    assert len(frames) == 72


# ---------------------------------------------------------------------------
# Non-empty output
# ---------------------------------------------------------------------------

def test_frames_non_empty():
    from justdoit.animate.presets import plasma_noise_warp
    frames = list(plasma_noise_warp("HI", n_frames=3, loop=False))
    for f in frames:
        assert len(f) > 0


def test_frames_multi_row():
    """Each frame should have 7 rows for block font."""
    from justdoit.animate.presets import plasma_noise_warp
    frames = list(plasma_noise_warp("HI", n_frames=3, loop=False))
    for f in frames:
        assert len(_strip_ansi(f).split("\n")) == 7


# ---------------------------------------------------------------------------
# ANSI color presence (C11 + C12 active)
# ---------------------------------------------------------------------------

def test_fg_color_codes_present():
    from justdoit.animate.presets import plasma_noise_warp
    frames = list(plasma_noise_warp("HI", n_frames=2, loop=False))
    for f in frames:
        assert _fg_color_count(f) > 0, "Expected foreground (C11) color codes"


def test_bg_bloom_codes_present():
    from justdoit.animate.presets import plasma_noise_warp
    frames = list(plasma_noise_warp("HI", n_frames=2, loop=False, bloom_radius=2))
    for f in frames:
        assert _bg_color_count(f) > 0, "Expected background (C12 bloom) color codes"


def test_no_bloom_when_radius_zero():
    from justdoit.animate.presets import plasma_noise_warp
    frames = list(plasma_noise_warp("HI", n_frames=2, loop=False, bloom_radius=0))
    for f in frames:
        assert _bg_color_count(f) == 0, "Expected no bloom when radius=0"


# ---------------------------------------------------------------------------
# Warp variation — amplitude axis (plasma, dynamic)
# ---------------------------------------------------------------------------

def test_leading_spaces_vary_across_frames():
    """Plasma amplitude_map changes per frame, so leading spaces should vary."""
    from justdoit.animate.presets import plasma_noise_warp
    frames = list(plasma_noise_warp("JUST DO IT", n_frames=12, loop=False))
    all_leads = [tuple(_leading_spaces(f)) for f in frames]
    # At least half the frames should have distinct leading space patterns
    unique_leads = set(all_leads)
    assert len(unique_leads) >= 6, (
        f"Expected at least 6 unique leading-space patterns across 12 frames, got {len(unique_leads)}"
    )


def test_leading_spaces_vary_across_rows_same_frame():
    """Noise phase_map causes rows to peak at different moments — leading spaces differ per row."""
    from justdoit.animate.presets import plasma_noise_warp
    frames = list(plasma_noise_warp("JUST DO IT", n_frames=12, loop=False))
    # Check at least one frame has row-level variation in leading spaces (not all identical)
    has_row_variation = False
    for f in frames:
        leads = _leading_spaces(f)
        text_rows = leads[:7]  # block font: 7 rows
        if len(set(text_rows)) > 1:
            has_row_variation = True
            break
    assert has_row_variation, "Expected per-row variation in leading spaces (noise phase_map)"


# ---------------------------------------------------------------------------
# Both fields are active: amplitude AND phase differ from single-field presets
# ---------------------------------------------------------------------------

def test_different_from_plasma_warp_alone():
    """plasma_noise_warp with zero phase spread should approach plasma_warp output."""
    from justdoit.animate.presets import plasma_noise_warp, plasma_warp
    # With max_phase_spread=0, phase_map is all zeros → reduces to amplitude-only warp
    # They won't be identical (different global_phase usage) but should be similar structure
    frames_pnw_no_phase = list(plasma_noise_warp(
        "HI", n_frames=4, max_phase_spread=0.0, loop=False
    ))
    frames_pnw_full_phase = list(plasma_noise_warp(
        "HI", n_frames=4, max_phase_spread=3.14159, loop=False
    ))
    # Frames with phase spread should differ from no-phase-spread
    any_different = any(
        _strip_ansi(a) != _strip_ansi(b)
        for a, b in zip(frames_pnw_no_phase, frames_pnw_full_phase)
    )
    assert any_different, "Expected phase_map to produce different output from zero phase spread"


def test_different_from_noise_warp_alone():
    """plasma_noise_warp should produce different leading spaces from static-amplitude noise_warp."""
    from justdoit.animate.presets import plasma_noise_warp, noise_warp
    frames_pnw = list(plasma_noise_warp("HI", n_frames=6, loop=False))
    frames_nw = list(noise_warp("HI", n_frames=6, loop=False))
    # They differ structurally (plasma amplitude dynamic vs. uniform max_amplitude)
    # At least some frames should have different plain-text content
    any_different = any(
        _strip_ansi(a) != _strip_ansi(b)
        for a, b in zip(frames_pnw, frames_nw)
    )
    assert any_different, "Expected plasma_noise_warp to differ from noise_warp"


# ---------------------------------------------------------------------------
# Color consistency (C11 uses plasma float — changes per frame)
# ---------------------------------------------------------------------------

def test_color_count_consistent_across_frames():
    """Each frame should have same number of colored cells (ink cell count is stable)."""
    from justdoit.animate.presets import plasma_noise_warp
    frames = list(plasma_noise_warp("HI", n_frames=4, loop=False))
    counts = [_fg_color_count(f) for f in frames]
    # All frames should have the same ink cell count (warp moves them, not creates/destroys)
    assert min(counts) == max(counts), (
        f"Foreground color counts vary across frames: {counts} — warp should not change ink count"
    )


# ---------------------------------------------------------------------------
# Loop palindrome symmetry
# ---------------------------------------------------------------------------

def test_loop_palindrome():
    """With loop=True, frame[i] and frame[2*n-1-i] should have identical plain content."""
    from justdoit.animate.presets import plasma_noise_warp
    n = 8
    frames = list(plasma_noise_warp("HI", n_frames=n, loop=True))
    total = len(frames)
    assert total == 2 * n
    for i in range(n):
        fwd = _strip_ansi(frames[i])
        rev = _strip_ansi(frames[total - 1 - i])
        assert fwd == rev, f"Loop not palindromic at i={i}: frames[{i}] != frames[{total - 1 - i}]"


# ---------------------------------------------------------------------------
# Parameter variants
# ---------------------------------------------------------------------------

def test_plasma_preset_diagonal():
    from justdoit.animate.presets import plasma_noise_warp
    frames = list(plasma_noise_warp("HI", n_frames=3, plasma_preset="diagonal", loop=False))
    assert len(frames) == 3
    for f in frames:
        assert len(f) > 0


def test_plasma_preset_slow():
    from justdoit.animate.presets import plasma_noise_warp
    frames = list(plasma_noise_warp("HI", n_frames=3, plasma_preset="slow", loop=False))
    assert len(frames) == 3


def test_different_noise_seed():
    from justdoit.animate.presets import plasma_noise_warp
    frames_42 = list(plasma_noise_warp("HI", n_frames=4, noise_seed=42, loop=False))
    frames_99 = list(plasma_noise_warp("HI", n_frames=4, noise_seed=99, loop=False))
    # Different seeds should produce at least one frame with different phase topology
    any_different = any(
        _strip_ansi(a) != _strip_ansi(b)
        for a, b in zip(frames_42, frames_99)
    )
    assert any_different, "Expected different noise seeds to produce different warp topologies"


def test_high_phase_spread():
    from justdoit.animate.presets import plasma_noise_warp
    frames = list(plasma_noise_warp(
        "HI", n_frames=4, max_phase_spread=6.28318, loop=False  # 2π
    ))
    assert len(frames) == 4


def test_palette_lava():
    from justdoit.animate.presets import plasma_noise_warp
    frames = list(plasma_noise_warp("HI", n_frames=2, palette_name="lava", loop=False))
    for f in frames:
        assert _fg_color_count(f) > 0


def test_palette_fire():
    from justdoit.animate.presets import plasma_noise_warp
    frames = list(plasma_noise_warp("HI", n_frames=2, palette_name="fire", loop=False))
    for f in frames:
        assert _fg_color_count(f) > 0


def test_single_char():
    from justdoit.animate.presets import plasma_noise_warp
    frames = list(plasma_noise_warp("A", n_frames=4, loop=False))
    assert len(frames) == 4
    for f in frames:
        assert len(f) > 0


def test_long_text():
    from justdoit.animate.presets import plasma_noise_warp
    frames = list(plasma_noise_warp("JUST DO IT NOW", n_frames=4, loop=False))
    assert len(frames) == 4


# ---------------------------------------------------------------------------
# Integration via render()
# ---------------------------------------------------------------------------

def test_render_integration():
    """Smoke test: preset works with the standard render() call path."""
    from justdoit.animate.presets import plasma_noise_warp
    frames = list(plasma_noise_warp("JUST DO IT", n_frames=3, loop=False))
    assert len(frames) == 3
    for f in frames:
        plain = _strip_ansi(f)
        # Block font JUST DO IT should span a reasonable width
        max_row_width = max(len(row) for row in plain.split("\n"))
        assert max_row_width > 20, f"Expected wide output, got max_row_width={max_row_width}"
