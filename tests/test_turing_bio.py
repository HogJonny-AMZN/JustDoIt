"""Tests for turing_float_grid(), _turing_morphogenesis_snapshots(),
turing_bio(), and turing_morphogenesis() presets.

Covers:
  - Return types and shapes
  - Value ranges for ink/exterior cells
  - Determinism with fixed seed
  - Seed variation produces different results
  - Preset coverage
  - Animation frame counts (loop / no loop)
  - ANSI escape codes present in colored output
  - Frame content varies across the animation
"""

import re
from typing import Iterator

import pytest


# -------------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------------

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")

SIMPLE_TEXT = "HI"
FULL_TEXT = "JUST DO IT"
MASK_1X1 = [[1.0]]
MASK_EMPTY = []


def _has_ansi(text: str) -> bool:
    return bool(_ANSI_RE.search(text))


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


# -------------------------------------------------------------------------
# turing_float_grid() tests
# -------------------------------------------------------------------------

class TestTuringFloatGrid:
    """turing_float_grid() — returns raw FHN activator U float grid."""

    def _make_mask(self, text="A", font="block"):
        from justdoit.core.glyph import glyph_to_mask
        from justdoit.fonts import FONTS
        glyph = FONTS["block"]["A"]
        ink = "".join({c for row in glyph for c in row if c != " "}) or chr(9608)
        return glyph_to_mask(glyph, ink_chars=ink)

    def test_returns_list(self):
        from justdoit.effects.generative import turing_float_grid
        mask = self._make_mask()
        result = turing_float_grid(mask, preset="spots", seed=1)
        assert isinstance(result, list)

    def test_row_count_matches_mask(self):
        from justdoit.effects.generative import turing_float_grid
        mask = self._make_mask()
        result = turing_float_grid(mask, preset="spots", seed=1)
        assert len(result) == len(mask)

    def test_col_count_matches_mask(self):
        from justdoit.effects.generative import turing_float_grid
        mask = self._make_mask()
        result = turing_float_grid(mask, preset="spots", seed=1)
        orig_cols = max(len(row) for row in mask)
        for row in result:
            assert len(row) == orig_cols

    def test_ink_cells_in_unit_range(self):
        from justdoit.effects.generative import turing_float_grid
        mask = self._make_mask()
        result = turing_float_grid(mask, preset="spots", seed=1)
        for r, row in enumerate(result):
            for c, val in enumerate(row):
                if c < len(mask[r]) and mask[r][c] >= 0.5:
                    assert 0.0 <= val <= 1.0, f"ink cell ({r},{c})={val} out of range"

    def test_exterior_cells_are_zero(self):
        from justdoit.effects.generative import turing_float_grid
        mask = self._make_mask()
        result = turing_float_grid(mask, preset="spots", seed=1)
        for r, row in enumerate(result):
            for c, val in enumerate(row):
                is_ink = c < len(mask[r]) and mask[r][c] >= 0.5
                if not is_ink:
                    assert val == 0.0, f"exterior cell ({r},{c})={val} should be 0.0"

    def test_deterministic_with_same_seed(self):
        from justdoit.effects.generative import turing_float_grid
        mask = self._make_mask()
        r1 = turing_float_grid(mask, preset="spots", seed=7)
        r2 = turing_float_grid(mask, preset="spots", seed=7)
        assert r1 == r2

    def test_different_seeds_give_different_results(self):
        from justdoit.effects.generative import turing_float_grid
        mask = self._make_mask()
        r1 = turing_float_grid(mask, preset="spots", seed=1)
        r2 = turing_float_grid(mask, preset="spots", seed=99)
        # Highly unlikely to be identical given RNG sensitivity
        assert r1 != r2

    def test_presets_all_work(self):
        from justdoit.effects.generative import turing_float_grid
        mask = self._make_mask()
        for preset in ("spots", "stripes", "maze", "labyrinth"):
            result = turing_float_grid(mask, preset=preset, seed=1)
            assert isinstance(result, list), f"preset={preset} did not return list"
            assert len(result) == len(mask)

    def test_invalid_preset_raises(self):
        from justdoit.effects.generative import turing_float_grid
        mask = self._make_mask()
        with pytest.raises(ValueError):
            turing_float_grid(mask, preset="invalid_preset_xyz", seed=1)

    def test_empty_mask_returns_empty(self):
        from justdoit.effects.generative import turing_float_grid
        result = turing_float_grid([], preset="spots", seed=1)
        assert result == []

    def test_steps_override(self):
        from justdoit.effects.generative import turing_float_grid
        mask = self._make_mask()
        # Low steps should still return correct shape
        result = turing_float_grid(mask, preset="spots", steps=50, seed=1)
        assert len(result) == len(mask)

    def test_returns_floats(self):
        from justdoit.effects.generative import turing_float_grid
        mask = self._make_mask()
        result = turing_float_grid(mask, preset="spots", seed=1)
        for row in result:
            for val in row:
                assert isinstance(val, float), f"expected float, got {type(val)}"


# -------------------------------------------------------------------------
# _turing_morphogenesis_snapshots() tests
# -------------------------------------------------------------------------

class TestTuringMorphogenesisSnapshots:
    """_turing_morphogenesis_snapshots() — single-pass FHN sim with step captures."""

    def _make_mask(self):
        from justdoit.core.glyph import glyph_to_mask
        from justdoit.fonts import FONTS
        glyph = FONTS["block"]["O"]
        ink = "".join({c for row in glyph for c in row if c != " "}) or chr(9608)
        return glyph_to_mask(glyph, ink_chars=ink)

    def test_returns_list_of_tuples(self):
        from justdoit.effects.generative import _turing_morphogenesis_snapshots
        mask = self._make_mask()
        result = _turing_morphogenesis_snapshots(mask, preset="spots",
                                                  snapshot_steps=[50, 100], seed=1)
        assert isinstance(result, list)
        assert len(result) == 2
        for tup in result:
            assert len(tup) == 3  # (step, orig_ink, float_grid)

    def test_snapshot_step_values(self):
        from justdoit.effects.generative import _turing_morphogenesis_snapshots
        mask = self._make_mask()
        steps = [50, 200]
        result = _turing_morphogenesis_snapshots(mask, preset="spots",
                                                  snapshot_steps=steps, seed=1)
        returned_steps = [tup[0] for tup in result]
        assert returned_steps == steps

    def test_float_grids_in_unit_range(self):
        from justdoit.effects.generative import _turing_morphogenesis_snapshots
        mask = self._make_mask()
        result = _turing_morphogenesis_snapshots(mask, preset="spots",
                                                  snapshot_steps=[100], seed=1)
        step, orig_ink, float_grid = result[0]
        for r, row in enumerate(float_grid):
            for c, val in enumerate(row):
                is_ink = r < len(orig_ink) and c < len(orig_ink[r]) and orig_ink[r][c]
                if is_ink:
                    assert 0.0 <= val <= 1.0

    def test_exterior_cells_zero(self):
        from justdoit.effects.generative import _turing_morphogenesis_snapshots
        mask = self._make_mask()
        result = _turing_morphogenesis_snapshots(mask, preset="spots",
                                                  snapshot_steps=[100], seed=1)
        step, orig_ink, float_grid = result[0]
        for r, row in enumerate(float_grid):
            for c, val in enumerate(row):
                is_ink = r < len(orig_ink) and c < len(orig_ink[r]) and orig_ink[r][c]
                if not is_ink:
                    assert val == 0.0

    def test_deterministic(self):
        from justdoit.effects.generative import _turing_morphogenesis_snapshots
        mask = self._make_mask()
        steps = [50, 100]
        r1 = _turing_morphogenesis_snapshots(mask, preset="spots",
                                              snapshot_steps=steps, seed=42)
        r2 = _turing_morphogenesis_snapshots(mask, preset="spots",
                                              snapshot_steps=steps, seed=42)
        # Compare float grids
        for (s1, i1, g1), (s2, i2, g2) in zip(r1, r2):
            assert s1 == s2
            assert g1 == g2

    def test_early_vs_late_snapshots_differ(self):
        from justdoit.effects.generative import _turing_morphogenesis_snapshots
        mask = self._make_mask()
        result = _turing_morphogenesis_snapshots(mask, preset="spots",
                                                  snapshot_steps=[50, 1500], seed=42)
        _, _, early_grid = result[0]
        _, _, late_grid = result[1]
        # The pattern should have evolved; at least some cells differ
        flat_early = [v for row in early_grid for v in row]
        flat_late = [v for row in late_grid for v in row]
        assert flat_early != flat_late, "Early and late snapshots should differ"


# -------------------------------------------------------------------------
# turing_bio() tests
# -------------------------------------------------------------------------

class TestTuringBio:
    """turing_bio() — X_TURING_BIO animation preset."""

    def test_returns_iterator(self):
        from justdoit.animate.presets import turing_bio
        result = turing_bio("HI", preset="spots", seed=1, n_frames=4, loop=False)
        assert hasattr(result, "__iter__")

    def test_yields_strings(self):
        from justdoit.animate.presets import turing_bio
        frames = list(turing_bio("HI", preset="spots", seed=1, n_frames=4, loop=False))
        for f in frames:
            assert isinstance(f, str)

    def test_frame_count_no_loop(self):
        from justdoit.animate.presets import turing_bio
        n = 4
        frames = list(turing_bio("HI", preset="spots", seed=1, n_frames=n, loop=False))
        assert len(frames) == n

    def test_frame_count_loop(self):
        from justdoit.animate.presets import turing_bio
        n = 4
        frames = list(turing_bio("HI", preset="spots", seed=1, n_frames=n, loop=True))
        # forward + reversed (full copy, no endpoint dedup) = 2*n
        assert len(frames) == 2 * n

    def test_frames_non_empty(self):
        from justdoit.animate.presets import turing_bio
        frames = list(turing_bio("HI", preset="spots", seed=1, n_frames=3, loop=False))
        for f in frames:
            stripped = _strip_ansi(f).strip()
            assert len(stripped) > 0, "Frame should not be entirely whitespace"

    def test_frames_contain_ansi(self):
        from justdoit.animate.presets import turing_bio
        frames = list(turing_bio("HI", preset="spots", seed=1, n_frames=3, loop=False))
        colored_count = sum(1 for f in frames if _has_ansi(f))
        assert colored_count > 0, "At least some frames should contain ANSI color codes"

    def test_frames_differ_across_animation(self):
        from justdoit.animate.presets import turing_bio
        n = 8
        frames = list(turing_bio("HI", preset="spots", seed=1, n_frames=n, loop=False))
        # Not all frames should be identical (color rotation should change something)
        unique = set(frames)
        assert len(unique) > 1, "Color rotation should produce different frames"

    def test_line_count_per_frame(self):
        from justdoit.animate.presets import turing_bio
        from justdoit.core.rasterizer import render
        ref = render("HI", font="block")
        ref_lines = len(ref.split("\n"))
        frames = list(turing_bio("HI", preset="spots", seed=1, n_frames=3, loop=False))
        for f in frames:
            assert len(f.split("\n")) == ref_lines

    def test_stripes_preset_works(self):
        from justdoit.animate.presets import turing_bio
        frames = list(turing_bio("HI", preset="stripes", seed=1, n_frames=3, loop=False))
        assert len(frames) == 3

    def test_bio_palette_default(self):
        from justdoit.animate.presets import turing_bio
        frames = list(turing_bio("HI", preset="spots", seed=1, n_frames=3, loop=False))
        # Bio palette is green-based — check at least one frame has green-ish ANSI
        # (38;2;r;g;b where g > r and g > b)
        for f in frames:
            matches = re.findall(r"38;2;(\d+);(\d+);(\d+)", f)
            if matches:
                green_dominant = any(int(g) > int(r) and int(g) > int(b)
                                     for r, g, b in matches)
                if green_dominant:
                    return  # Found expected green coloring
        pytest.fail("No green-dominant ANSI colors found; bio palette not applied")

    def test_spectral_palette_works(self):
        from justdoit.animate.presets import turing_bio
        frames = list(turing_bio("HI", preset="spots", seed=1, n_frames=3,
                                  palette_name="spectral", loop=False))
        assert len(frames) == 3
        assert any(_has_ansi(f) for f in frames)


# -------------------------------------------------------------------------
# turing_morphogenesis() tests
# -------------------------------------------------------------------------

class TestTuringMorphogenesis:
    """turing_morphogenesis() — A_N09a animation preset."""

    _FAST_STEPS = [50, 200]  # Short steps for unit tests

    def test_returns_iterator(self):
        from justdoit.animate.presets import turing_morphogenesis
        result = turing_morphogenesis(
            "HI", preset="spots", seed=1,
            snapshot_steps=self._FAST_STEPS, loop=False
        )
        assert hasattr(result, "__iter__")

    def test_yields_strings(self):
        from justdoit.animate.presets import turing_morphogenesis
        frames = list(turing_morphogenesis(
            "HI", preset="spots", seed=1,
            snapshot_steps=self._FAST_STEPS, loop=False
        ))
        for f in frames:
            assert isinstance(f, str)

    def test_frame_count_no_loop(self):
        from justdoit.animate.presets import turing_morphogenesis
        steps = self._FAST_STEPS
        frames = list(turing_morphogenesis(
            "HI", preset="spots", seed=1, snapshot_steps=steps, loop=False
        ))
        assert len(frames) == len(steps)

    def test_frame_count_loop(self):
        from justdoit.animate.presets import turing_morphogenesis
        steps = self._FAST_STEPS  # 2 steps
        frames = list(turing_morphogenesis(
            "HI", preset="spots", seed=1, snapshot_steps=steps, loop=True
        ))
        # 2 forward + 2 reversed = 4 total (no dedup because loop appends full reversed)
        assert len(frames) == 2 * len(steps)

    def test_frames_non_empty(self):
        from justdoit.animate.presets import turing_morphogenesis
        frames = list(turing_morphogenesis(
            "HI", preset="spots", seed=1,
            snapshot_steps=self._FAST_STEPS, loop=False
        ))
        for f in frames:
            stripped = _strip_ansi(f).strip()
            assert len(stripped) > 0

    def test_frames_contain_ansi(self):
        from justdoit.animate.presets import turing_morphogenesis
        frames = list(turing_morphogenesis(
            "HI", preset="spots", seed=1,
            snapshot_steps=self._FAST_STEPS, loop=False
        ))
        colored_count = sum(1 for f in frames if _has_ansi(f))
        assert colored_count > 0, "Frames should contain ANSI color codes from bio palette"

    def test_early_and_late_frames_differ(self):
        from justdoit.animate.presets import turing_morphogenesis
        # Use distinct enough steps to see pattern evolution
        frames = list(turing_morphogenesis(
            "HI", preset="spots", seed=42,
            snapshot_steps=[50, 800], loop=False
        ))
        assert len(frames) == 2
        # Strip ANSI and compare chars — they should differ as pattern evolves
        early_chars = _strip_ansi(frames[0])
        late_chars = _strip_ansi(frames[1])
        assert early_chars != late_chars, "Early and late frames should differ"

    def test_line_count_per_frame(self):
        from justdoit.animate.presets import turing_morphogenesis
        from justdoit.core.rasterizer import render
        ref = render("HI", font="block")
        ref_lines = len(ref.split("\n"))
        frames = list(turing_morphogenesis(
            "HI", preset="spots", seed=1,
            snapshot_steps=self._FAST_STEPS, loop=False
        ))
        for f in frames:
            assert len(f.split("\n")) == ref_lines

    def test_stripes_preset_works(self):
        from justdoit.animate.presets import turing_morphogenesis
        frames = list(turing_morphogenesis(
            "HI", preset="stripes", seed=1,
            snapshot_steps=self._FAST_STEPS, loop=False
        ))
        assert len(frames) == len(self._FAST_STEPS)

    def test_different_seeds_produce_different_evolution(self):
        from justdoit.animate.presets import turing_morphogenesis
        steps = [50, 400]
        frames_42 = list(turing_morphogenesis(
            "HI", preset="spots", seed=42, snapshot_steps=steps, loop=False
        ))
        frames_99 = list(turing_morphogenesis(
            "HI", preset="spots", seed=99, snapshot_steps=steps, loop=False
        ))
        # At least one frame should differ between seeds
        any_diff = any(f1 != f2 for f1, f2 in zip(frames_42, frames_99))
        assert any_diff, "Different seeds should produce different morphogenesis patterns"

    def test_bio_palette_applied(self):
        from justdoit.animate.presets import turing_morphogenesis
        frames = list(turing_morphogenesis(
            "HI", preset="spots", seed=1,
            snapshot_steps=self._FAST_STEPS, loop=False
        ))
        # Check that bio palette (green-dominant) ANSI codes appear
        for f in frames:
            matches = re.findall(r"38;2;(\d+);(\d+);(\d+)", f)
            if matches:
                green_dominant = any(int(g) > int(r) and int(g) >= int(b)
                                     for r, g, b in matches)
                if green_dominant:
                    return
        pytest.fail("No green-dominant ANSI colors found; bio palette not applied")
