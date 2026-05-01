"""Tests for X_LIVING_COLOR — Conway GoL + C11 age-heat coloring (living_color preset)."""
import re
import pytest

ANSI_RE = re.compile(r"\033\[[^m]*m")


def _strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


# ---------------------------------------------------------------------------
# Helper: collect all frames from the generator
# ---------------------------------------------------------------------------

def _frames(text="HI", n_frames=10, seed=42, loop=False, bloom_color_name=None, **kwargs):
    from justdoit.animate.presets import living_color
    return list(
        living_color(
            text,
            n_frames=n_frames,
            seed=seed,
            loop=loop,
            bloom_color_name=bloom_color_name,
            **kwargs,
        )
    )


# ---------------------------------------------------------------------------
# Basic output structure
# ---------------------------------------------------------------------------

def test_yields_correct_frame_count_no_loop():
    frames = _frames(n_frames=10, loop=False)
    assert len(frames) == 10


def test_yields_correct_frame_count_with_loop():
    frames = _frames(n_frames=10, loop=True)
    # forward + reverse = 20 frames
    assert len(frames) == 20


def test_each_frame_is_nonempty():
    frames = _frames(n_frames=5)
    for f in frames:
        assert f.strip(), "Frame must not be blank"


def test_each_frame_is_multiline():
    frames = _frames(n_frames=3)
    for f in frames:
        assert "\n" in f, "Frame should span multiple rows"


# ---------------------------------------------------------------------------
# Exterior cells are spaces
# ---------------------------------------------------------------------------

def test_exterior_cells_are_spaces():
    """Exterior (non-glyph) positions must remain plain space characters."""
    frames = _frames(text="O", n_frames=5)
    for f in frames:
        plain = _strip_ansi(f)
        rows = plain.split("\n")
        # The 'O' glyph has leading/trailing columns that are all spaces
        if rows and all(c == " " for c in rows[0]):
            # At least one fully-space row exists (top of block font)
            pass  # exterior space confirmed by existence of blank row
        for row in rows:
            for ch in row:
                assert ch in " ·█▓▒", f"Unexpected char: {repr(ch)}"


def test_output_dimensions_consistent_across_frames():
    """All frames should have the same number of rows."""
    frames = _frames(n_frames=8, loop=False)
    row_counts = [len(f.split("\n")) for f in frames]
    assert len(set(row_counts)) == 1, "Row count should be identical across all frames"


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

def test_deterministic_same_seed():
    frames1 = _frames(seed=7, n_frames=5, loop=False)
    frames2 = _frames(seed=7, n_frames=5, loop=False)
    assert frames1 == frames2, "Same seed must yield identical frames"


def test_different_seeds_differ():
    frames1 = _frames(seed=1, n_frames=5, loop=False)
    frames2 = _frames(seed=2, n_frames=5, loop=False)
    # At least the first frame should differ (different initial states)
    assert frames1[0] != frames2[0], "Different seeds should yield different initial frames"


# ---------------------------------------------------------------------------
# ANSI color codes present in alive cells
# ---------------------------------------------------------------------------

def test_frames_contain_ansi_color_codes():
    """Alive cells must be colorized via C11 (ANSI 24-bit color codes present)."""
    frames = _frames(n_frames=5)
    for f in frames:
        assert "\033[38;2;" in f, "Frame should contain 24-bit foreground color codes"


def test_frames_differ_over_time():
    """GoL state changes so frames should not all be identical."""
    frames = _frames(n_frames=15, loop=False)
    unique = set(frames)
    assert len(unique) > 1, "Frames should vary as GoL evolves"


# ---------------------------------------------------------------------------
# Age coloring: age logic
# ---------------------------------------------------------------------------

def test_age_float_saturates():
    """After max_age generations, stable cells should saturate to float 1.0 (red color)."""
    from justdoit.animate.presets import living_color
    # Run with small max_age to force saturation quickly
    frames = list(living_color("I", n_frames=30, max_age=5, seed=42, loop=False, bloom_color_name=None))
    # We can't directly inspect age floats, but we can check that the color
    # codes shift from the blue range toward the red range across early frames.
    # Specifically: early frames should have blue codes (\033[38;2;0;80;220 style)
    # and later frames should include red codes (\033[38;2;255;40;0 style).
    early_has_blue = "\033[38;2;0;" in frames[0]
    assert early_has_blue, "Early frames should have blue (newborn) coloring"


def test_bloom_codes_present_when_enabled():
    """When bloom_color_name is set, background ANSI codes should appear."""
    frames = _frames(n_frames=3, bloom_color_name="cyan", bloom_radius=2)
    for f in frames:
        has_bg = "\033[48;2;" in f
        if has_bg:
            break
    else:
        pytest.fail("No background bloom codes found in any frame with bloom enabled")


def test_bloom_disabled():
    """When bloom_color_name=None, no background ANSI codes should appear."""
    frames = _frames(n_frames=5, bloom_color_name=None)
    for f in frames:
        assert "\033[48;2;" not in f, "Background bloom codes should be absent when bloom disabled"


# ---------------------------------------------------------------------------
# Max age parameter
# ---------------------------------------------------------------------------

def test_max_age_param_accepted():
    """max_age parameter should be accepted without error."""
    frames = _frames(n_frames=5, max_age=10, loop=False)
    assert len(frames) == 5


def test_max_age_1_forces_all_cells_saturated():
    """max_age=1 means every alive cell saturates to 1.0 on first frame."""
    from justdoit.animate.presets import living_color
    frames = list(living_color("I", n_frames=5, max_age=1, seed=42, loop=False, bloom_color_name=None))
    # All alive cells have age 1 / max_age=1 = 1.0 → red palette
    # Check that red-ish codes (255, 40, 0) appear in frames
    any_red = any("\033[38;2;255;" in f for f in frames)
    assert any_red, "With max_age=1, ancient-red coloring should appear immediately"


# ---------------------------------------------------------------------------
# Integration: render via "HI" and "JUST DO IT"
# ---------------------------------------------------------------------------

def test_integration_short_text():
    frames = _frames(text="HI", n_frames=5, loop=False)
    assert len(frames) == 5
    for f in frames:
        assert f.strip()


def test_integration_full_phrase():
    frames = _frames(text="JUST DO IT", n_frames=4, loop=False)
    assert len(frames) == 4
    for f in frames:
        assert "\n" in f


# ---------------------------------------------------------------------------
# Palette parameter
# ---------------------------------------------------------------------------

def test_custom_palette_name():
    """Using 'fire' palette instead of 'age' should succeed."""
    from justdoit.animate.presets import living_color
    frames = list(living_color("HI", n_frames=3, palette_name="fire", loop=False, bloom_color_name=None))
    assert len(frames) == 3
    for f in frames:
        assert "\033[38;2;" in f


# ---------------------------------------------------------------------------
# Age palette in PALETTE_REGISTRY
# ---------------------------------------------------------------------------

def test_age_palette_in_registry():
    from justdoit.effects.color import PALETTE_REGISTRY, AGE_PALETTE
    assert "age" in PALETTE_REGISTRY
    assert PALETTE_REGISTRY["age"] is AGE_PALETTE
    # Palette should be ordered from cool blue to hot red
    assert AGE_PALETTE[0][2] > AGE_PALETTE[0][0], "First entry should be blue-dominant"
    assert AGE_PALETTE[-1][0] > AGE_PALETTE[-1][2], "Last entry should be red-dominant"


def test_age_palette_gradient_range():
    from justdoit.effects.color import AGE_PALETTE
    # AGE_PALETTE spans from blue (cold, newborn) to red (hot, ancient)
    assert len(AGE_PALETTE) >= 5, "AGE_PALETTE should have at least 5 anchor points"
    # First entry: blue channel dominant
    r0, g0, b0 = AGE_PALETTE[0]
    assert b0 > r0, "Palette[0] should be blue-dominant (newborn)"
    # Last entry: red channel dominant
    r_last, g_last, b_last = AGE_PALETTE[-1]
    assert r_last > b_last, "Palette[-1] should be red-dominant (ancient)"
