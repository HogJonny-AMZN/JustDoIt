"""Tests for A_SLIME1 — Slime Mold Time-Lapse Animation preset."""

import re
import collections.abc

import pytest


# ---------------------------------------------------------------------------
# _slime_mold_snapshots tests
# ---------------------------------------------------------------------------

def test_snapshots_returns_correct_count():
    """_slime_mold_snapshots returns one entry per snapshot step."""
    from justdoit.effects.generative import _slime_mold_snapshots
    mask = [[1.0] * 5 for _ in range(5)]
    snaps = _slime_mold_snapshots(mask, snapshot_steps=[5, 10, 20], seed=0)
    assert len(snaps) == 3


def test_snapshots_step_values():
    """Each snapshot tuple contains the correct step count."""
    from justdoit.effects.generative import _slime_mold_snapshots
    mask = [[1.0] * 5 for _ in range(5)]
    steps = [5, 15, 30]
    snaps = _slime_mold_snapshots(mask, snapshot_steps=steps, seed=1)
    for i, (step, _ink, _fg) in enumerate(snaps):
        assert step == steps[i]


def test_snapshots_float_grid_shape():
    """Each snapshot float_grid has the correct dimensions."""
    from justdoit.effects.generative import _slime_mold_snapshots
    mask = [[1.0] * 8 for _ in range(5)]
    snaps = _slime_mold_snapshots(mask, snapshot_steps=[10, 30], seed=2)
    for _step, ink, fg in snaps:
        assert len(fg) == 5
        assert all(len(row) == 8 for row in fg)


def test_snapshots_float_grid_range():
    """All float values in snapshots are in [0, 1]."""
    from justdoit.effects.generative import _slime_mold_snapshots
    mask = [[1.0] * 6 for _ in range(4)]
    snaps = _slime_mold_snapshots(mask, snapshot_steps=[5, 20], seed=3)
    for _step, ink, fg in snaps:
        for row in fg:
            for v in row:
                assert 0.0 <= v <= 1.0 + 1e-9, f"Float out of range: {v}"


def test_snapshots_empty_mask():
    """Empty mask returns correct count with empty float grids."""
    from justdoit.effects.generative import _slime_mold_snapshots
    snaps = _slime_mold_snapshots([], snapshot_steps=[5, 10], seed=0)
    assert len(snaps) == 2


def test_snapshots_reproducible():
    """Same seed produces identical snapshots."""
    from justdoit.effects.generative import _slime_mold_snapshots
    mask = [[1.0] * 7 for _ in range(5)]
    s1 = _slime_mold_snapshots(mask, snapshot_steps=[10, 50], seed=99)
    s2 = _slime_mold_snapshots(mask, snapshot_steps=[10, 50], seed=99)
    for (st1, ink1, fg1), (st2, ink2, fg2) in zip(s1, s2):
        assert st1 == st2
        assert fg1 == fg2


def test_snapshots_ink_mask_matches_input():
    """The ink mask returned is the correct shape."""
    from justdoit.effects.generative import _slime_mold_snapshots
    mask = [[1.0] * 6 for _ in range(4)]
    snaps = _slime_mold_snapshots(mask, snapshot_steps=[10], seed=5)
    _step, ink, fg = snaps[0]
    assert len(ink) == 4
    assert all(len(row) == 6 for row in ink)


# ---------------------------------------------------------------------------
# slime_mold_anim preset tests
# ---------------------------------------------------------------------------

def test_anim_returns_iterator():
    """slime_mold_anim() returns an iterator."""
    from justdoit.animate.presets import slime_mold_anim
    result = slime_mold_anim("HI", snapshot_steps=[5, 10], loop=False, seed=0)
    assert isinstance(result, collections.abc.Iterator)


def test_anim_frame_count_no_loop():
    """Without loop, frame count equals len(snapshot_steps)."""
    from justdoit.animate.presets import slime_mold_anim
    steps = [5, 15, 30]
    frames = list(slime_mold_anim("HI", snapshot_steps=steps, loop=False, seed=1))
    assert len(frames) == len(steps)


def test_anim_frame_count_with_loop():
    """With loop=True, frame count is 2 * len(snapshot_steps)."""
    from justdoit.animate.presets import slime_mold_anim
    steps = [5, 15, 30]
    frames = list(slime_mold_anim("HI", snapshot_steps=steps, loop=True, seed=2))
    assert len(frames) == 2 * len(steps)


def test_anim_frames_are_non_empty_strings():
    """All frames are non-empty strings."""
    from justdoit.animate.presets import slime_mold_anim
    frames = list(slime_mold_anim("HI", snapshot_steps=[5, 10], loop=False, seed=3))
    for f in frames:
        assert isinstance(f, str)
        assert len(f) > 0


def test_anim_frames_contain_non_space():
    """At least one character in each frame is a non-space character."""
    from justdoit.animate.presets import slime_mold_anim
    # Use enough steps so trail has formed
    frames = list(slime_mold_anim("HI", snapshot_steps=[20, 50], loop=False, seed=4))
    for f in frames:
        clean = re.sub(r'\x1b\[[0-9;]*m', '', f)
        assert any(c != ' ' and c != '\n' for c in clean), (
            f"Frame is all spaces: {repr(f[:100])}"
        )


def test_anim_via_render():
    """Integration test: slime_mold_anim('JUST DO IT') doesn't crash."""
    from justdoit.animate.presets import slime_mold_anim
    frames = list(slime_mold_anim("JUST DO IT", snapshot_steps=[5, 30], loop=False, seed=7))
    assert len(frames) == 2
    for f in frames:
        assert isinstance(f, str)


def test_anim_no_bloom():
    """slime_mold_anim works without bloom (bloom_color_name=None)."""
    from justdoit.animate.presets import slime_mold_anim
    frames = list(slime_mold_anim(
        "HI", snapshot_steps=[10], loop=False, seed=5, bloom_color_name=None
    ))
    assert len(frames) == 1
    assert isinstance(frames[0], str)


def test_anim_deterministic():
    """Same seed produces identical frames."""
    from justdoit.animate.presets import slime_mold_anim
    f1 = list(slime_mold_anim("HI", snapshot_steps=[10, 30], loop=False, seed=11))
    f2 = list(slime_mold_anim("HI", snapshot_steps=[10, 30], loop=False, seed=11))
    assert f1 == f2


def test_anim_exterior_cells_are_spaces():
    """Cells outside glyph mask remain spaces (no bloom variant)."""
    from justdoit.animate.presets import slime_mold_anim
    # Use single char 'J' — block font row 3 starts with '   ██  '
    # so the LAST column of the row should be a space (index -1)
    frames = list(slime_mold_anim(
        "J", snapshot_steps=[10], loop=False, seed=6, bloom_color_name=None
    ))
    for frame in frames:
        clean = re.sub(r'\x1b\[[0-9;]*m', '', frame)
        rows = clean.split('\n')
        # Row index 3 (mid-letter) in block font has '   ██  '
        # meaning col -1 is a space.
        for row in rows:
            if row and len(row) > 0:
                # Last column is always exterior space in all block glyphs
                assert row[-1] == ' ', f"Last char not space: {repr(row)}"
