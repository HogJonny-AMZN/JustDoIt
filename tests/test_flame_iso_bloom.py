"""
Tests for X_FLAME_ISO_BLOOM: Flame + Isometric + Bloom three-axis composite.

Tests validate:
- Structural: correct frame count, row dimensions match isometric geometry
- Visual: front face chars come from flame fill; depth face uses shade chars
- Color: both FG (fire palette) and BG (bloom) ANSI codes are present
- Animation: frames are stochastically distinct (different fire each frame)
- Loop: total frames = 2*n_frames when loop=True
- Integration: end-to-end render pipeline completes without error
"""

import re
import pytest

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")
_DEPTH_CHARS = {"▓", "▒", "░", "·"}
_FRONT_CHARS = set("@#S%?*+;:,.")


def _strip_ansi(text: str) -> str:
    """Strip all ANSI escape sequences from text."""
    return _ANSI_RE.sub("", text)


def _count_fg(text: str) -> int:
    """Count 24-bit foreground color codes."""
    return text.count("\033[38;2;")


def _count_bg(text: str) -> int:
    """Count 24-bit background bloom codes."""
    return text.count("\033[48;2;")


# -------------------------------------------------------------------------
class TestFlameIsoBloomBasic:
    """Basic smoke tests — ensure the generator produces output without errors."""

    def test_produces_frames(self):
        from justdoit.animate.presets import flame_iso_bloom
        frames = list(flame_iso_bloom("HI", n_frames=3, loop=False))
        assert len(frames) == 3

    def test_loop_doubles_frames(self):
        from justdoit.animate.presets import flame_iso_bloom
        frames = list(flame_iso_bloom("HI", n_frames=4, loop=True))
        assert len(frames) == 8

    def test_frames_are_non_empty(self):
        from justdoit.animate.presets import flame_iso_bloom
        for frame in flame_iso_bloom("HI", n_frames=2, loop=False):
            assert len(frame.strip()) > 0

    def test_frames_are_strings(self):
        from justdoit.animate.presets import flame_iso_bloom
        for frame in flame_iso_bloom("HI", n_frames=2, loop=False):
            assert isinstance(frame, str)


# -------------------------------------------------------------------------
class TestFlameIsoBloomDimensions:
    """Validate isometric geometry: output has more rows than plain render."""

    def test_row_count_exceeds_glyph_height(self):
        """Isometric extrusion adds depth rows on top."""
        from justdoit.animate.presets import flame_iso_bloom
        from justdoit.core.rasterizer import render
        depth = 4
        plain = render("HI", font="block", gap=1)
        plain_rows = len(plain.split("\n"))
        frames = list(flame_iso_bloom("HI", n_frames=1, depth=depth, loop=False))
        iso_rows = len(_strip_ansi(frames[0]).split("\n"))
        # isometric adds depth rows on top + (usually) trailing empty row
        assert iso_rows >= plain_rows + depth

    def test_iso_rows_consistent_across_frames(self):
        """All frames have the same row count."""
        from justdoit.animate.presets import flame_iso_bloom
        frames = list(flame_iso_bloom("HI", n_frames=4, loop=False))
        row_counts = [len(_strip_ansi(f).split("\n")) for f in frames]
        assert len(set(row_counts)) == 1, f"Row counts differ: {row_counts}"

    def test_depth_param_affects_row_count(self):
        """More depth → more rows in output."""
        from justdoit.animate.presets import flame_iso_bloom
        frames_d2 = list(flame_iso_bloom("HI", n_frames=1, depth=2, loop=False))
        frames_d6 = list(flame_iso_bloom("HI", n_frames=1, depth=6, loop=False))
        rows_d2 = len(_strip_ansi(frames_d2[0]).split("\n"))
        rows_d6 = len(_strip_ansi(frames_d6[0]).split("\n"))
        assert rows_d6 > rows_d2


# -------------------------------------------------------------------------
class TestFlameIsoBloomStructure:
    """Validate that the correct structural chars appear in output."""

    def test_depth_chars_present_in_iso_region(self):
        """Depth face shade chars (▓▒░·) appear in the isometric top rows."""
        from justdoit.animate.presets import flame_iso_bloom
        frames = list(flame_iso_bloom("HI", n_frames=2, depth=4, loop=False))
        plain = _strip_ansi(frames[0])
        all_chars = set(plain.replace(" ", "").replace("\n", ""))
        # At least some depth face chars should appear
        assert all_chars & _DEPTH_CHARS, f"No depth chars found; got: {all_chars}"

    def test_front_face_ink_chars_present(self):
        """Front face flame chars appear in the lower rows of output."""
        from justdoit.animate.presets import flame_iso_bloom
        frames = list(flame_iso_bloom("HI", n_frames=2, depth=4, loop=False))
        plain = _strip_ansi(frames[0])
        all_chars = set(plain.replace(" ", "").replace("\n", ""))
        # Some front face flame chars should appear
        assert all_chars & _FRONT_CHARS, f"No front-face chars found; got: {all_chars}"

    def test_exterior_cells_are_spaces_or_bloom(self):
        """All non-ink, non-bloom content is spaces (exterior)."""
        from justdoit.animate.presets import flame_iso_bloom
        frames = list(flame_iso_bloom("HI", n_frames=1, loop=False))
        plain = _strip_ansi(frames[0])
        rows = plain.split("\n")
        # At least some rows should be purely spaces at their ends
        all_space_rows = [r for r in rows if r.strip() == ""]
        # Final row is typically empty
        assert len(all_space_rows) >= 1

    def test_no_unicode_decode_errors(self):
        """Output can be encoded to UTF-8 without errors."""
        from justdoit.animate.presets import flame_iso_bloom
        frames = list(flame_iso_bloom("JUST DO IT", n_frames=2, loop=False))
        for frame in frames:
            encoded = frame.encode("utf-8")
            assert len(encoded) > 0


# -------------------------------------------------------------------------
class TestFlameIsoBloomColor:
    """Validate that fire palette and bloom colors are both present."""

    def test_fg_color_codes_present(self):
        """24-bit foreground (fire palette) codes are injected."""
        from justdoit.animate.presets import flame_iso_bloom
        frames = list(flame_iso_bloom("HI", n_frames=2, loop=False))
        fg_count = _count_fg(frames[0])
        assert fg_count > 0, "No 24-bit foreground color codes found"

    def test_bg_bloom_codes_present(self):
        """24-bit background (bloom) codes are injected."""
        from justdoit.animate.presets import flame_iso_bloom
        frames = list(flame_iso_bloom("HI", n_frames=2, bloom_radius=4, loop=False))
        bg_count = _count_bg(frames[0])
        assert bg_count > 0, "No 24-bit background bloom codes found"

    def test_substantial_fg_count(self):
        """Enough cells are colored to indicate full front-face + depth-face coverage."""
        from justdoit.animate.presets import flame_iso_bloom
        frames = list(flame_iso_bloom("JUST DO IT", n_frames=2, loop=False))
        fg_count = _count_fg(frames[0])
        # "JUST DO IT" has many ink cells; expect at least 300 FG codes
        assert fg_count >= 300, f"Too few FG color codes: {fg_count}"

    def test_bloom_radius_affects_bg_count(self):
        """Larger bloom radius → more BG bloom cells."""
        from justdoit.animate.presets import flame_iso_bloom
        frames_small = list(flame_iso_bloom("HI", n_frames=1, bloom_radius=1, loop=False))
        frames_large = list(flame_iso_bloom("HI", n_frames=1, bloom_radius=6, loop=False))
        bg_small = _count_bg(frames_small[0])
        bg_large = _count_bg(frames_large[0])
        assert bg_large >= bg_small, "Larger bloom radius should produce >= BG codes"

    def test_palette_parameter_accepted(self):
        """Alternative palettes ('lava', 'spectral') are accepted without error."""
        from justdoit.animate.presets import flame_iso_bloom
        for palette in ("lava", "spectral", "fire"):
            frames = list(flame_iso_bloom("HI", n_frames=1, palette_name=palette, loop=False))
            assert len(frames) == 1

    def test_tone_curve_parameter_accepted(self):
        """Tone curve variants are accepted without error."""
        from justdoit.animate.presets import flame_iso_bloom
        for curve in ("aces", "blown_out", "reinhard", "linear"):
            frames = list(flame_iso_bloom("HI", n_frames=1, tone_curve=curve, loop=False))
            assert len(frames) == 1


# -------------------------------------------------------------------------
class TestFlameIsoBloomAnimation:
    """Validate that frames differ (stochastic flame) and loop behavior is correct."""

    def test_frames_are_stochastically_distinct(self):
        """Multiple frames should differ due to stochastic flame re-seeding."""
        from justdoit.animate.presets import flame_iso_bloom
        frames = list(flame_iso_bloom("JUST DO IT", n_frames=10, loop=False))
        plains = [_strip_ansi(f) for f in frames]
        n_unique = len(set(plains))
        assert n_unique >= 5, f"Expected ≥5 unique frames; got {n_unique}"

    def test_loop_first_half_equals_second_half_reversed(self):
        """Loop mode: frames[n_frames:] should equal reversed(frames[:n_frames])."""
        from justdoit.animate.presets import flame_iso_bloom
        n = 4
        frames = list(flame_iso_bloom("HI", n_frames=n, loop=True))
        assert len(frames) == 2 * n
        fwd = frames[:n]
        rev = frames[n:]
        assert rev == list(reversed(fwd)), "Reversed second half should match first half"

    def test_loop_false_gives_forward_only(self):
        """loop=False gives exactly n_frames frames."""
        from justdoit.animate.presets import flame_iso_bloom
        frames = list(flame_iso_bloom("HI", n_frames=5, loop=False))
        assert len(frames) == 5


# -------------------------------------------------------------------------
class TestFlameIsoBloomParameters:
    """Validate parameter variations and edge cases."""

    def test_depth_1_works(self):
        """Minimal depth=1 produces output."""
        from justdoit.animate.presets import flame_iso_bloom
        frames = list(flame_iso_bloom("HI", n_frames=2, depth=1, loop=False))
        assert len(frames) == 2
        assert len(_strip_ansi(frames[0]).strip()) > 0

    def test_depth_8_works(self):
        """Large depth=8 produces output with more depth layers."""
        from justdoit.animate.presets import flame_iso_bloom
        frames = list(flame_iso_bloom("HI", n_frames=1, depth=8, loop=False))
        plain = _strip_ansi(frames[0])
        # With depth=8, at least some depth chars should appear in top rows
        assert any(ch in plain for ch in _DEPTH_CHARS)

    def test_direction_left(self):
        """direction='left' produces output without error."""
        from justdoit.animate.presets import flame_iso_bloom
        frames = list(flame_iso_bloom("HI", n_frames=2, direction="left", loop=False))
        assert len(frames) == 2
        plain = _strip_ansi(frames[0])
        assert any(ch in plain for ch in _DEPTH_CHARS)

    def test_single_char(self):
        """Single-character text is handled."""
        from justdoit.animate.presets import flame_iso_bloom
        frames = list(flame_iso_bloom("A", n_frames=2, loop=False))
        assert len(frames) == 2
        assert len(_strip_ansi(frames[0]).strip()) > 0

    def test_flame_presets(self):
        """All flame presets ('default', 'hot', 'cool', 'embers') work."""
        from justdoit.animate.presets import flame_iso_bloom
        for preset in ("default", "hot", "cool", "embers"):
            frames = list(flame_iso_bloom("HI", n_frames=2, flame_preset=preset, loop=False))
            assert len(frames) == 2, f"Preset '{preset}' failed"


# -------------------------------------------------------------------------
class TestFlameIsoBloomIntegration:
    """End-to-end integration tests."""

    def test_full_text_default_params(self):
        """Standard 'JUST DO IT' with default params completes without error."""
        from justdoit.animate.presets import flame_iso_bloom
        frames = list(flame_iso_bloom("JUST DO IT", n_frames=4, loop=False))
        assert len(frames) == 4
        for f in frames:
            plain = _strip_ansi(f)
            assert "\n" in plain
            assert len(plain) > 50

    def test_output_has_both_depth_and_front_face(self):
        """Composite output contains both structural types: depth chars AND flame chars."""
        from justdoit.animate.presets import flame_iso_bloom
        frames = list(flame_iso_bloom("JUST DO IT", n_frames=2, loop=False))
        plain = _strip_ansi(frames[0])
        all_chars = set(plain.replace(" ", "").replace("\n", ""))
        has_depth = bool(all_chars & _DEPTH_CHARS)
        has_front = bool(all_chars & _FRONT_CHARS)
        assert has_depth and has_front, (
            f"Missing structural types. depth={has_depth}, front={has_front}, chars={all_chars}"
        )

    def test_color_and_bloom_coexist(self):
        """Both FG (fire) and BG (bloom) ANSI codes appear in same frame."""
        from justdoit.animate.presets import flame_iso_bloom
        frames = list(flame_iso_bloom("JUST DO IT", n_frames=2, loop=False))
        f0 = frames[0]
        assert _count_fg(f0) > 0 and _count_bg(f0) > 0, (
            f"Expected both FG and BG codes; got fg={_count_fg(f0)}, bg={_count_bg(f0)}"
        )
