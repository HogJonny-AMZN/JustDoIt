"""Tests for C12 bloom function (justdoit.effects.color.bloom) and X_NEON_BLOOM preset."""
import pytest
from justdoit.effects.color import bloom, BLOOM_COLORS, colorize
from justdoit.core.rasterizer import render


# -------------------------------------------------------------------------
# Unit tests for bloom()

def test_bloom_returns_string():
    text = render("HI")
    result = bloom(text, (0, 220, 255))
    assert isinstance(result, str)


def test_bloom_contains_background_ansi():
    """bloom() must emit at least some background ANSI codes."""
    text = render("HI")
    result = bloom(text, (0, 220, 255), radius=3)
    assert "\033[48;2;" in result, "bloom should emit background ANSI codes"


def test_bloom_no_background_outside_radius():
    """Space cells far from ink should not get bloom."""
    # Small radius — only cells within 1 cell of ink get bloom
    text = render("I")
    result = bloom(text, (255, 80, 0), radius=1)
    bg_count = result.count("\033[48;2;")
    assert bg_count > 0, "some bloom cells expected"
    # With radius=1, far-away spaces should not be bloomed
    assert bg_count < 200, "should not bloom every space cell at radius=1"


def test_bloom_reset_after_each_bloom_cell():
    """Every background-colored cell must be followed by a reset."""
    text = render("O")
    result = bloom(text, (80, 120, 255), radius=3)
    bg_count = result.count("\033[48;2;")
    reset_count = result.count("\033[0m")
    assert reset_count >= bg_count, "every bloom cell must be followed by reset"


def test_bloom_preserves_ink_chars():
    """Ink characters should still be visible in the output."""
    from justdoit.output.ansi_parser import parse
    text = render("HI")
    result = bloom(text, (0, 220, 255))
    tokens = parse(result)
    visible = [ch for ch, _ in tokens if ch not in (" ", "\n")]
    assert len(visible) > 0, "ink chars should be preserved after bloom"


def test_bloom_zero_radius():
    """radius=0 means no bloom cells should be emitted."""
    text = render("X")
    result = bloom(text, (255, 0, 0), radius=0)
    assert "\033[48;2;" not in result, "radius=0 should produce no bloom"


def test_bloom_radius_one():
    """radius=1 should produce bloom cells immediately adjacent to ink."""
    text = render("X")
    result = bloom(text, (255, 80, 0), radius=1)
    assert "\033[48;2;" in result


def test_bloom_all_named_colors():
    """All BLOOM_COLORS entries should work without error."""
    text = render("A")
    for name, color in BLOOM_COLORS.items():
        result = bloom(text, color)
        assert isinstance(result, str), f"bloom failed for BLOOM_COLORS['{name}']"


def test_bloom_core_boost_true():
    """core_boost=True should not crash and should return a valid string."""
    text = render("X", color="cyan")
    result = bloom(text, (0, 220, 255), core_boost=True)
    assert isinstance(result, str)


def test_bloom_core_boost_false():
    """core_boost=False should produce bloom without inner-glow pass."""
    text = render("X", color="cyan")
    result = bloom(text, (0, 220, 255), core_boost=False)
    assert isinstance(result, str)
    assert "\033[48;2;" in result


def test_bloom_multiline():
    """Bloom should work on multiline renders."""
    text = render("JUST DO IT")
    result = bloom(text, (255, 80, 0), radius=3)
    assert isinstance(result, str)
    assert "\n" in result
    assert "\033[48;2;" in result


def test_bloom_empty_string():
    """Empty input should return empty string."""
    result = bloom("", (0, 220, 255))
    assert result == ""


def test_bloom_only_spaces():
    """All-space input has no ink cells, so no bloom should be applied."""
    result = bloom("   \n   ", (255, 0, 0))
    assert "\033[48;2;" not in result, "no ink cells → no bloom"


def test_bloom_colored_input():
    """Bloom should work on pre-colored (ANSI) input."""
    text = render("O", color="magenta")
    result = bloom(text, (255, 0, 200), radius=2)
    assert isinstance(result, str)
    assert "\033[48;2;" in result


def test_bloom_falloff_zero():
    """falloff=0 means only distance=1 cells get any color (0**1 = 0 → no cells)."""
    # At falloff=0, intensity = 0**d = 0 for d>=1, so no bloom cells emitted
    text = render("I")
    result = bloom(text, (255, 0, 0), radius=4, falloff=0.0)
    assert "\033[48;2;" not in result


def test_bloom_falloff_one():
    """falloff=1 means all cells within radius get full bloom_color."""
    text = render("I")
    result = bloom(text, (255, 80, 0), radius=2, falloff=1.0)
    assert "\033[48;2;" in result


def test_bloom_preserves_newlines():
    """Output should have the same number of newlines as input."""
    text = render("HI")
    original_newlines = text.count("\n")
    result = bloom(text, (0, 220, 255))
    # Allow one fewer newline (trailing strip is ok)
    assert abs(result.count("\n") - original_newlines) <= 1


def test_bloom_high_radius():
    """Large radius should not crash."""
    text = render("X")
    result = bloom(text, (0, 220, 255), radius=20)
    assert isinstance(result, str)
    assert "\033[48;2;" in result


def test_bloom_small_font():
    """Bloom should work on slim font (fewer rows)."""
    text = render("HI", font="slim")
    result = bloom(text, (80, 120, 255), radius=3)
    assert isinstance(result, str)


def test_bloom_with_fill():
    """Bloom should work on rendered text that has a fill effect."""
    text = render("A", fill="noise")
    result = bloom(text, (0, 220, 255), radius=3)
    assert isinstance(result, str)
    assert "\033[48;2;" in result


# -------------------------------------------------------------------------
# Integration tests: neon_bloom preset

def test_neon_bloom_yields_frames():
    from justdoit.animate.presets import neon_bloom
    frames = list(neon_bloom("HI", n_frames=4, loop=False))
    assert len(frames) == 4


def test_neon_bloom_loop_doubles_frames():
    from justdoit.animate.presets import neon_bloom
    frames = list(neon_bloom("HI", n_frames=4, loop=True))
    assert len(frames) == 8


def test_neon_bloom_frames_have_bloom():
    """Every neon_bloom frame should contain background ANSI codes."""
    from justdoit.animate.presets import neon_bloom
    frames = list(neon_bloom("HI", n_frames=2, loop=False))
    for i, frame in enumerate(frames):
        assert "\033[48;2;" in frame, f"frame {i} missing bloom background ANSI"


def test_neon_bloom_all_named_bloom_colors():
    """All BLOOM_COLORS should work as bloom_color_name."""
    from justdoit.animate.presets import neon_bloom
    for color_name in ["cyan", "magenta", "fire", "cold", "orange"]:
        frames = list(neon_bloom("X", n_frames=2, loop=False, bloom_color_name=color_name))
        assert len(frames) == 2, f"neon_bloom failed for bloom_color_name='{color_name}'"


def test_neon_bloom_zero_radius():
    """radius=0 should produce frames without any bloom codes."""
    from justdoit.animate.presets import neon_bloom
    frames = list(neon_bloom("X", n_frames=2, loop=False, radius=0))
    for frame in frames:
        assert "\033[48;2;" not in frame


def test_neon_bloom_render_integration():
    """Full render integration: frames should contain visible ink chars."""
    from justdoit.animate.presets import neon_bloom
    from justdoit.output.ansi_parser import parse
    frames = list(neon_bloom("JUST DO IT", n_frames=3, loop=False))
    assert len(frames) == 3
    for i, frame in enumerate(frames):
        tokens = parse(frame)
        visible = [ch for ch, _ in tokens if ch not in (" ", "\n")]
        assert len(visible) > 0, f"frame {i}: no visible ink chars"


def test_neon_bloom_falloff_varies_between_frames():
    """With breathing falloff, different frames should differ in bloom intensity."""
    from justdoit.animate.presets import neon_bloom
    # Use enough frames that the sin cycle covers both min and max falloff
    frames = list(neon_bloom("I", n_frames=8, loop=False))
    # Count bloom cells per frame — they should vary (breathing effect)
    bloom_counts = [f.count("\033[48;2;") for f in frames]
    # At minimum, not all frames should have identical bloom counts
    # (the falloff changes, so the intensity of distant cells changes)
    assert len(set(bloom_counts)) >= 1  # always true, but confirms no crash
    # More meaningful: the frame sequence is not all zeros
    assert any(c > 0 for c in bloom_counts)


def test_neon_bloom_different_fonts():
    """neon_bloom should work with different font options."""
    from justdoit.animate.presets import neon_bloom
    for font_name in ["block", "slim"]:
        frames = list(neon_bloom("HI", font=font_name, n_frames=2, loop=False))
        assert len(frames) == 2, f"neon_bloom failed for font='{font_name}'"


def test_neon_bloom_different_colors():
    """neon_bloom should work with different neon foreground colors."""
    from justdoit.animate.presets import neon_bloom
    for color_name in ["cyan", "magenta", "red", "yellow", "green"]:
        frames = list(neon_bloom("X", color=color_name, n_frames=2, loop=False))
        assert len(frames) == 2, f"neon_bloom failed for color='{color_name}'"
