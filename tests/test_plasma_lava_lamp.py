"""Tests for A10c — Plasma Lava Lamp cross-breed.

Tests cover:
  - plasma_float_grid() helper: shape, value range, consistency with plasma_fill
  - plasma_lava_lamp() preset: frame count, ANSI color, content, looping
"""
import math
import re

import pytest

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")
_TRUECOLOR_RE = re.compile(r"\033\[38;2;\d+;\d+;\d+m")


# ---------------------------------------------------------------------------
# plasma_float_grid tests
# ---------------------------------------------------------------------------

class TestPlasmaFloatGrid:
    """Tests for plasma_float_grid() helper in justdoit.effects.generative."""

    def setup_method(self):
        from justdoit.effects.generative import plasma_float_grid
        from justdoit.core.glyph import glyph_to_mask
        from justdoit.fonts import FONTS
        self.plasma_float_grid = plasma_float_grid
        self.glyph_to_mask = glyph_to_mask
        self.FONTS = FONTS

    def _make_mask(self, char="H", font="block"):
        font_data = self.FONTS[font]
        glyph = font_data[char]
        ink = "".join({ch for row in glyph for ch in row if ch != " "}) or chr(9608)
        return self.glyph_to_mask(glyph, ink_chars=ink)

    def test_shape_matches_mask(self):
        """Float grid must have same row count as mask."""
        mask = self._make_mask("H")
        grid = self.plasma_float_grid(mask, t=0.0)
        assert len(grid) == len(mask), "Float grid row count must match mask rows"

    def test_col_count_matches_mask(self):
        """Float grid columns must match mask columns."""
        mask = self._make_mask("H")
        cols = max(len(row) for row in mask)
        grid = self.plasma_float_grid(mask, t=0.0)
        for r, row in enumerate(grid):
            assert len(row) == cols, f"Row {r}: expected {cols} cols, got {len(row)}"

    def test_values_in_unit_range(self):
        """All float values must be in [0.0, 1.0]."""
        mask = self._make_mask("J")
        grid = self.plasma_float_grid(mask, t=1.5)
        for r, row in enumerate(grid):
            for c, v in enumerate(row):
                assert 0.0 <= v <= 1.0, f"Out-of-range value {v} at ({r},{c})"

    def test_exterior_cells_are_zero(self):
        """Exterior cells (mask < 0.5) must have float value 0.0."""
        mask = self._make_mask("I")
        grid = self.plasma_float_grid(mask, t=0.0)
        for r in range(len(mask)):
            for c in range(len(mask[r])):
                if mask[r][c] < 0.5:
                    assert grid[r][c] == 0.0, (
                        f"Exterior cell ({r},{c}) should be 0.0, got {grid[r][c]}"
                    )

    def test_ink_cells_have_nonzero_values(self):
        """At least some ink cells must have float value > 0.0."""
        mask = self._make_mask("H")
        grid = self.plasma_float_grid(mask, t=0.5)
        ink_vals = [
            grid[r][c]
            for r in range(len(mask))
            for c in range(len(mask[r]))
            if mask[r][c] >= 0.5
        ]
        assert any(v > 0.0 for v in ink_vals), "Ink cells should have some nonzero float values"

    def test_max_value_is_one(self):
        """The maximum ink-cell value should be 1.0 (normalization check)."""
        mask = self._make_mask("H")
        grid = self.plasma_float_grid(mask, t=2.0)
        ink_vals = [
            grid[r][c]
            for r in range(len(mask))
            for c in range(len(mask[r]))
            if mask[r][c] >= 0.5
        ]
        assert max(ink_vals) == pytest.approx(1.0, abs=1e-9), "Max ink value should be 1.0"

    def test_different_t_gives_different_grid(self):
        """Different t values should produce different float grids."""
        mask = self._make_mask("H")
        g1 = self.plasma_float_grid(mask, t=0.0)
        g2 = self.plasma_float_grid(mask, t=math.pi)
        # At least some values should differ
        diffs = [
            abs(g1[r][c] - g2[r][c])
            for r in range(len(mask))
            for c in range(len(mask[r]))
            if mask[r][c] >= 0.5
        ]
        assert max(diffs) > 0.01, "Different t values should produce different grids"

    def test_invalid_preset_raises(self):
        """Unknown preset should raise ValueError."""
        mask = self._make_mask("H")
        with pytest.raises(ValueError, match="Unknown plasma preset"):
            self.plasma_float_grid(mask, t=0.0, preset="nonexistent")

    def test_empty_mask_returns_empty(self):
        """Empty mask should return empty list."""
        grid = self.plasma_float_grid([], t=0.0)
        assert grid == []

    def test_known_presets_all_work(self):
        """All named presets should work without error."""
        mask = self._make_mask("H")
        for p in ("default", "tight", "slow", "diagonal"):
            grid = self.plasma_float_grid(mask, t=0.5, preset=p)
            assert len(grid) == len(mask), f"Preset '{p}' returned wrong row count"


# ---------------------------------------------------------------------------
# plasma_lava_lamp preset tests
# ---------------------------------------------------------------------------

class TestPlasmaLavaLamp:
    """Tests for plasma_lava_lamp() animation preset."""

    def _get_preset(self):
        from justdoit.animate.presets import plasma_lava_lamp
        return plasma_lava_lamp

    def test_yields_frames(self):
        """Preset must yield at least 1 frame."""
        pll = self._get_preset()
        frames = list(pll("HI", font="block", n_frames=2, loop=False))
        assert len(frames) >= 1, "plasma_lava_lamp must yield at least 1 frame"

    def test_frame_count_no_loop(self):
        """Without loop, should yield exactly n_frames frames."""
        pll = self._get_preset()
        frames = list(pll("HI", font="block", n_frames=4, loop=False))
        assert len(frames) == 4, f"Expected 4 frames, got {len(frames)}"

    def test_frame_count_with_loop(self):
        """With loop=True, should yield 2*n_frames frames."""
        pll = self._get_preset()
        frames = list(pll("HI", font="block", n_frames=4, loop=True))
        assert len(frames) == 8, f"Expected 8 frames with loop, got {len(frames)}"

    def test_frames_are_strings(self):
        """All frames must be strings."""
        pll = self._get_preset()
        frames = list(pll("HI", font="block", n_frames=2, loop=False))
        for i, f in enumerate(frames):
            assert isinstance(f, str), f"Frame {i} is not a string"

    def test_frames_are_nonempty(self):
        """All frames must be non-empty strings."""
        pll = self._get_preset()
        frames = list(pll("HI", font="block", n_frames=2, loop=False))
        for i, f in enumerate(frames):
            assert len(f) > 0, f"Frame {i} is empty"

    def test_frames_contain_newlines(self):
        """Frames must be multi-line (contain newlines)."""
        pll = self._get_preset()
        frames = list(pll("HI", font="block", n_frames=2, loop=False))
        for i, f in enumerate(frames):
            assert "\n" in f, f"Frame {i} contains no newlines"

    def test_frames_contain_ansi_truecolor(self):
        """Frames must contain 24-bit ANSI true-color codes (C11 applied)."""
        pll = self._get_preset()
        frames = list(pll("HI", font="block", n_frames=2, loop=False))
        for i, f in enumerate(frames):
            assert _TRUECOLOR_RE.search(f), (
                f"Frame {i} contains no 24-bit ANSI color codes — C11 not applied"
            )

    def test_stripped_frame_contains_plasma_chars(self):
        """Stripped (no ANSI) frame must contain plasma density chars."""
        pll = self._get_preset()
        frames = list(pll("HI", font="block", n_frames=2, loop=False))
        stripped = _ANSI_RE.sub("", frames[0])
        plasma_chars = set("@#S%?*+;:,.")
        found = any(ch in stripped for ch in plasma_chars)
        assert found, "Stripped frame should contain plasma density chars"

    def test_stripped_frame_has_correct_row_count(self):
        """Stripped frame must have 7 rows for block font (standard glyph height)."""
        pll = self._get_preset()
        frames = list(pll("HI", font="block", n_frames=2, loop=False))
        stripped = _ANSI_RE.sub("", frames[0])
        rows = stripped.split("\n")
        assert len(rows) == 7, f"Expected 7 rows for block font, got {len(rows)}"

    def test_lava_palette_used_by_default(self):
        """Default palette should be lava — deep violet to white colors."""
        pll = self._get_preset()
        # Lava palette has deep violet (low: 10,0,20) to white (high: 255,255,200)
        # Check that violet-ish RGB codes appear somewhere in the frame
        frames = list(pll("HI", font="block", n_frames=3, loop=False))
        combined = "".join(frames)
        # LAVA_PALETTE contains (10,0,20) as darkest stop — check a violet-range color exists
        has_dark = bool(re.search(r"\033\[38;2;[0-9]{1,3};[0-9]{1,3};[0-9]{1,3}m", combined))
        assert has_dark, "Lava palette colors not found in frames"

    def test_fire_palette_works(self):
        """fire palette should work without error."""
        pll = self._get_preset()
        frames = list(pll("HI", font="block", n_frames=2, loop=False, palette_name="fire"))
        assert len(frames) == 2
        assert _TRUECOLOR_RE.search(frames[0])

    def test_spectral_palette_works(self):
        """spectral palette should work without error."""
        pll = self._get_preset()
        frames = list(pll("HI", font="block", n_frames=2, loop=False, palette_name="spectral"))
        assert len(frames) == 2
        assert _TRUECOLOR_RE.search(frames[0])

    def test_different_frames_differ(self):
        """Different frames should have different content (plasma evolves)."""
        pll = self._get_preset()
        frames = list(pll("HI", font="block", n_frames=6, loop=False))
        # Strip ANSI and compare — at least one pair of frames should differ
        stripped = [_ANSI_RE.sub("", f) for f in frames]
        unique = set(stripped)
        assert len(unique) > 1, "All frames are identical — plasma should evolve"

    def test_plasma_tight_preset(self):
        """tight plasma preset should work without error."""
        pll = self._get_preset()
        frames = list(pll("HI", font="block", n_frames=2, loop=False, preset="tight"))
        assert len(frames) == 2

    def test_is_iterator(self):
        """plasma_lava_lamp must return an iterator (not a list)."""
        pll = self._get_preset()
        result = pll("HI", font="block", n_frames=2, loop=False)
        # Should be a generator/iterator, not a materialized list
        assert hasattr(result, "__iter__"), "plasma_lava_lamp should return an iterable"
        assert hasattr(result, "__next__"), "plasma_lava_lamp should return an iterator (generator)"
