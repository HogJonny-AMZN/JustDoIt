"""
Package: tests.test_iso_depth_breathe
Tests for iso_depth_breathe() animation preset (A_ISO1).
"""

import types
import pytest

from justdoit.animate.presets import iso_depth_breathe

_DEPTH_CHARS = set("▓▒░·")


# -------------------------------------------------------------------------
# 1. Return type is Iterator (not a list)
def test_return_type_is_iterator():
    result = iso_depth_breathe("HI", n_frames=4, loop=False)
    assert isinstance(result, types.GeneratorType)


# -------------------------------------------------------------------------
# 2. Frame count: exactly n_frames when loop=False
def test_frame_count_loop_false():
    frames = list(iso_depth_breathe("HI", n_frames=6, loop=False))
    assert len(frames) == 6


# -------------------------------------------------------------------------
# 3. Frame count: 2*n_frames-2 when loop=True (n_frames > 1)
def test_frame_count_loop_true():
    n = 8
    frames = list(iso_depth_breathe("HI", n_frames=n, loop=True))
    assert len(frames) == 2 * n - 2


# -------------------------------------------------------------------------
# 4. Each frame is a non-empty string
def test_frames_are_nonempty_strings():
    for frame in iso_depth_breathe("HI", n_frames=4, loop=False):
        assert isinstance(frame, str)
        assert len(frame) > 0


# -------------------------------------------------------------------------
# 5. Each frame is a multi-line string (contains newlines)
def test_frames_are_multiline():
    for frame in iso_depth_breathe("HI", n_frames=4, loop=False):
        assert "\n" in frame


# -------------------------------------------------------------------------
# 6. Frames contain isometric depth characters
def test_frames_contain_depth_chars():
    for frame in iso_depth_breathe("HI", n_frames=4, loop=False):
        found = any(ch in _DEPTH_CHARS for ch in frame)
        assert found, f"No depth chars found in frame: {frame!r}"


# -------------------------------------------------------------------------
# 7. Depth oscillation: frames at i=0 and i=n//4 differ in depth-char count
# i=0 → sin(0)=0 → base_depth; i=n//4 → sin(π/2)=1 → base_depth+amplitude
def test_depth_oscillation_changes_depth_char_count():
    n = 12
    frames = list(iso_depth_breathe("HI", n_frames=n, amplitude=3, base_depth=4, loop=False))
    count_0 = sum(ch in _DEPTH_CHARS for ch in frames[0])
    count_quarter = sum(ch in _DEPTH_CHARS for ch in frames[n // 4])
    assert count_0 != count_quarter, "Depth oscillation should produce different depth-char counts"


# -------------------------------------------------------------------------
# 8. Works with fill='plasma'
def test_fill_plasma():
    frames = list(iso_depth_breathe("HI", n_frames=3, fill="plasma", loop=False))
    assert len(frames) == 3


# -------------------------------------------------------------------------
# 9. Works with fill='flame'
def test_fill_flame():
    frames = list(iso_depth_breathe("HI", n_frames=3, fill="flame", loop=False))
    assert len(frames) == 3


# -------------------------------------------------------------------------
# 10. Works with fill='density'
def test_fill_density():
    frames = list(iso_depth_breathe("HI", n_frames=3, fill="density", loop=False))
    assert len(frames) == 3


# -------------------------------------------------------------------------
# 11. Works with font='block'
def test_font_block():
    frames = list(iso_depth_breathe("HI", font="block", n_frames=3, loop=False))
    assert len(frames) == 3


# -------------------------------------------------------------------------
# 12. Works with font='slim'
def test_font_slim():
    frames = list(iso_depth_breathe("HI", font="slim", n_frames=3, loop=False))
    assert len(frames) == 3


# -------------------------------------------------------------------------
# 13. Works with direction='left'
def test_direction_left():
    frames = list(iso_depth_breathe("HI", n_frames=3, direction="left", loop=False))
    assert len(frames) == 3
    for frame in frames:
        assert "\n" in frame


# -------------------------------------------------------------------------
# 14. direction='right' produces depth chars (extrusion on right side)
def test_direction_right_has_depth_chars():
    frames = list(iso_depth_breathe("HI", n_frames=3, direction="right", loop=False))
    for frame in frames:
        assert any(ch in _DEPTH_CHARS for ch in frame)


# -------------------------------------------------------------------------
# 15. loop=False gives exactly n_frames=8 frames
def test_loop_false_8_frames():
    frames = list(iso_depth_breathe("HI", n_frames=8, loop=False))
    assert len(frames) == 8


# -------------------------------------------------------------------------
# 16. loop=True gives exactly 2*8-2=14 frames for n_frames=8
def test_loop_true_8_frames():
    frames = list(iso_depth_breathe("HI", n_frames=8, loop=True))
    assert len(frames) == 14


# -------------------------------------------------------------------------
# 17. base_depth=1, amplitude=0: all frames have shallow depth
def test_base_depth_1_amplitude_0_shallow():
    frames = list(iso_depth_breathe("HI", n_frames=4, base_depth=1, amplitude=0, loop=False))
    # With depth=1, fewer depth shade chars than with depth=4
    counts = [sum(ch in _DEPTH_CHARS for ch in f) for f in frames]
    # All counts should be the same (constant depth)
    assert len(set(counts)) == 1


# -------------------------------------------------------------------------
# 18. amplitude=0: all frames have same depth-char count
def test_amplitude_0_constant_depth():
    frames = list(iso_depth_breathe("HI", n_frames=6, amplitude=0, base_depth=4, loop=False))
    counts = [sum(ch in _DEPTH_CHARS for ch in f) for f in frames]
    assert len(set(counts)) == 1, f"Expected constant depth-char counts, got {counts}"


# -------------------------------------------------------------------------
# 19. fill_kwargs passed through (e.g. fill_kwargs={'t': 0.5} for plasma)
def test_fill_kwargs_passed_through():
    frames = list(iso_depth_breathe("HI", n_frames=3, fill="plasma", fill_kwargs={"t": 0.5}, loop=False))
    assert len(frames) == 3
    for frame in frames:
        assert isinstance(frame, str)
        assert len(frame) > 0


# -------------------------------------------------------------------------
# 20. n_frames=1, loop=False: yields exactly 1 frame
def test_n_frames_1_loop_false():
    frames = list(iso_depth_breathe("HI", n_frames=1, loop=False))
    assert len(frames) == 1


# -------------------------------------------------------------------------
# 21. n_frames=2, loop=True: yields exactly 2 frames (2*2-2=2)
def test_n_frames_2_loop_true():
    frames = list(iso_depth_breathe("HI", n_frames=2, loop=True))
    assert len(frames) == 2


# -------------------------------------------------------------------------
# 22. base_depth=1, amplitude=0: depth is always 1 (minimum depth letters)
def test_base_depth_1_amplitude_0_always_depth_1():
    # With depth=1, the isometric extrusion uses only 1 shade layer.
    # Each ink cell produces exactly one depth shade char at adjacent position.
    # We can verify this by comparing with a higher depth render.
    frames_d1 = list(iso_depth_breathe("HI", n_frames=2, base_depth=1, amplitude=0, fill="density", loop=False))
    frames_d4 = list(iso_depth_breathe("HI", n_frames=2, base_depth=4, amplitude=0, fill="density", loop=False))
    count_d1 = sum(ch in _DEPTH_CHARS for ch in frames_d1[0])
    count_d4 = sum(ch in _DEPTH_CHARS for ch in frames_d4[0])
    # d4 should have more depth shade characters than d1
    assert count_d4 > count_d1


# -------------------------------------------------------------------------
# 23. With default args, output is non-empty
def test_default_args_nonempty():
    frames = list(iso_depth_breathe("HI"))
    assert len(frames) > 0
    for frame in frames:
        assert len(frame) > 0


# -------------------------------------------------------------------------
# 24. Generator is lazy (doesn't fail before iteration)
def test_generator_is_lazy():
    # Constructing the generator should not raise or compute anything
    gen = iso_depth_breathe("HI", n_frames=6, loop=True)
    assert hasattr(gen, "__next__")
    # Advance one frame to confirm it works
    frame = next(gen)
    assert isinstance(frame, str)


# -------------------------------------------------------------------------
# 25. First and last frames of a loop are not identical (loop cuts duplicate endpoints)
def test_loop_no_duplicate_endpoints():
    n = 8
    frames = list(iso_depth_breathe("HI", n_frames=n, amplitude=3, base_depth=4, loop=True))
    # Total = 2*8-2 = 14. First frame (i=0) and last frame (i=1 reversed) should differ.
    assert frames[0] != frames[-1], "First and last frames should not be identical in seamless loop"
