"""
Tests for A_VOR1 — Voronoi Stained Glass animation preset.
"""

import pytest
from justdoit.animate.presets import voronoi_stained_glass


# -------------------------------------------------------------------------
class TestVoronoiStainedGlass:
    def test_yields_frames(self):
        frames = list(voronoi_stained_glass("HI", n_frames=4, loop=False))
        assert len(frames) == 4

    def test_loop_doubles_frames(self):
        frames_no_loop = list(voronoi_stained_glass("HI", n_frames=4, loop=False))
        frames_loop = list(voronoi_stained_glass("HI", n_frames=4, loop=True))
        assert len(frames_loop) == 2 * len(frames_no_loop)

    def test_frames_contain_ansi_color(self):
        frames = list(voronoi_stained_glass("HI", n_frames=2, loop=False))
        for frame in frames:
            assert "\033[38;2;" in frame, "Frame should contain 24-bit ANSI color codes"

    def test_frames_are_strings(self):
        frames = list(voronoi_stained_glass("HI", n_frames=2, loop=False))
        for frame in frames:
            assert isinstance(frame, str)

    def test_frames_are_multiline(self):
        frames = list(voronoi_stained_glass("HI", n_frames=2, loop=False))
        for frame in frames:
            assert "\n" in frame, "Frame should be multi-line (ASCII art rows)"

    def test_different_offsets_differ(self):
        frames = list(voronoi_stained_glass("JUST DO IT", n_frames=5, loop=False))
        # With enough frames and content, frames should differ (palette rotating)
        # At least some frames should be different
        assert len(set(frames)) > 1, "Animated frames should differ from each other"

    def test_silver_border_present(self):
        """Border chars '@' should be colored silver (180,180,180)."""
        frames = list(voronoi_stained_glass("O", n_frames=1, loop=False))
        # 'O' with voronoi_cracked will have '@' border chars
        # Check that silver color code appears in any frame
        any_silver = any("\033[38;2;180;180;180m" in f for f in frames)
        assert any_silver, "Silver border color should be present in frames"

    def test_accepts_different_palettes(self):
        for palette in ["spectral", "fire", "lava", "bio"]:
            frames = list(voronoi_stained_glass("HI", n_frames=2, loop=False, palette_name=palette))
            assert len(frames) == 2

    def test_accepts_different_fonts(self):
        frames = list(voronoi_stained_glass("HI", font="block", n_frames=2, loop=False))
        assert len(frames) == 2

    def test_is_generator(self):
        import types
        gen = voronoi_stained_glass("HI", n_frames=2, loop=False)
        assert isinstance(gen, types.GeneratorType)

    def test_frame_row_count_consistent(self):
        """All frames should have the same number of rows."""
        frames = list(voronoi_stained_glass("HI", n_frames=5, loop=False))
        row_counts = [f.count("\n") for f in frames]
        assert len(set(row_counts)) == 1, "All frames should have same row count"
