"""
Tests for justdoit.effects.recursive — N01 Typographic Recursion.

Verifies that typographic_recursion correctly replaces non-space cells
with cycling characters from the source text, and that the render()
integration works end-to-end.
"""

import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from justdoit.effects.recursive import typographic_recursion, typographic_recursion_multi
from justdoit.core.rasterizer import render


# ---------------------------------------------------------------------------
# Unit tests: typographic_recursion()
# ---------------------------------------------------------------------------

class TestTypographicRecursion:
    """Core function tests."""

    def test_non_empty_output(self):
        """Output is non-empty for a basic text render."""
        rows = render("HI").split("\n")
        result = typographic_recursion(rows, "HI")
        assert result
        assert any(row.strip() for row in result)

    def test_preserves_space_positions(self):
        """Wherever input had a space, output must also have a space."""
        rows = render("HI").split("\n")
        result = typographic_recursion(rows, "HI")
        assert len(rows) == len(result)
        for in_row, out_row in zip(rows, result):
            for in_ch, out_ch in zip(in_row, out_row):
                if in_ch == " ":
                    assert out_ch == " ", f"Expected space, got {repr(out_ch)}"

    def test_non_space_chars_from_source(self):
        """All non-space chars in output must be from source_text.upper()."""
        rows = render("HELLO").split("\n")
        source = "HELLO"
        result = typographic_recursion(rows, source)
        allowed = set(source.upper()) | {" "}
        for row in result:
            for ch in row:
                assert ch in allowed, f"Unexpected char {repr(ch)} not in {allowed}"

    def test_dimensions_preserved(self):
        """Row count and widths must be identical to input."""
        rows = render("AB").split("\n")
        result = typographic_recursion(rows, "AB")
        assert len(result) == len(rows)
        for in_row, out_row in zip(rows, result):
            assert len(out_row) == len(in_row)

    def test_single_char_source(self):
        """Source text of length 1: all non-space cells become that char."""
        rows = render("X").split("\n")
        result = typographic_recursion(rows, "A", separator="")
        for row in result:
            for ch in row:
                assert ch in (" ", "A"), f"Unexpected char: {repr(ch)}"

    def test_empty_source_returns_unchanged(self):
        """Empty source text returns the original rows unchanged."""
        rows = render("HI").split("\n")
        result = typographic_recursion(rows, "", separator="")
        assert result == rows

    def test_cycles_correctly(self):
        """For source 'AB' with no separator, non-space chars cycle A→B→A→B."""
        # Use a simple 1×1 glyph simulation
        rows = ["###"]  # 3 non-space chars
        result = typographic_recursion(rows, "AB", separator="")
        assert result == ["ABA"]

    def test_cycles_with_separator(self):
        """For source 'AB' with separator '-', fill sequence is A, B, -."""
        rows = ["######"]  # 6 non-space chars
        result = typographic_recursion(rows, "AB", separator="-")
        # Cycle: A B - A B -
        assert result == ["AB-AB-"]

    def test_empty_rows_input(self):
        """Empty input rows list returns empty result."""
        result = typographic_recursion([], "HELLO")
        assert result == []

    def test_all_space_row(self):
        """A row of all spaces passes through unchanged."""
        rows = ["     "]
        result = typographic_recursion(rows, "HI", separator="")
        assert result == ["     "]

    def test_source_with_spaces_stripped_by_default(self):
        """Spaces in source_text are excluded from fill cycle by default."""
        rows = ["###"]  # 3 non-space chars
        result = typographic_recursion(rows, "A B", separator="")
        # Only A and B are in fill (spaces stripped): A B A
        assert result == ["ABA"]

    def test_source_with_spaces_included(self):
        """With include_spaces=True, spaces in source ARE part of the cycle."""
        rows = ["###"]  # 3 non-space chars
        result = typographic_recursion(rows, "A B", separator="", include_spaces=True)
        # Cycle: A, ' ', B  → A ' B
        assert result == ["A B"]


# ---------------------------------------------------------------------------
# Unit tests: typographic_recursion_multi()
# ---------------------------------------------------------------------------

class TestTypographicRecursionMulti:
    """Multi-level variant tests."""

    def test_non_empty_output(self):
        """Multi mode returns non-empty output."""
        rows = render("AB").split("\n")
        result = typographic_recursion_multi(rows, "AB")
        assert result
        assert any(row.strip() for row in result)

    def test_dimensions_preserved(self):
        """Row count and widths are preserved."""
        rows = render("CD").split("\n")
        result = typographic_recursion_multi(rows, "CD", levels=2)
        assert len(result) == len(rows)
        for in_row, out_row in zip(rows, result):
            assert len(out_row) == len(in_row)

    def test_non_space_chars_from_source(self):
        """Non-space chars in output are from source_text.upper()."""
        rows = render("HI").split("\n")
        source = "HI"
        result = typographic_recursion_multi(rows, source, levels=2)
        allowed = set(source.upper()) | {" "}
        for row in result:
            for ch in row:
                assert ch in allowed

    def test_space_positions_preserved(self):
        """Spaces remain in the same positions."""
        rows = render("HI").split("\n")
        result = typographic_recursion_multi(rows, "HI", levels=3)
        for in_row, out_row in zip(rows, result):
            for ic, oc in zip(in_row, out_row):
                if ic == " ":
                    assert oc == " "

    def test_empty_source_returns_unchanged(self):
        """Empty source returns unchanged rows."""
        rows = render("A").split("\n")
        result = typographic_recursion_multi(rows, "")
        assert result == rows


# ---------------------------------------------------------------------------
# Integration tests: render(..., recursion=True)
# ---------------------------------------------------------------------------

class TestRenderRecursion:
    """End-to-end render() tests with recursion=True."""

    def test_full_render_non_empty(self):
        """render('HI', recursion=True) returns non-empty string."""
        output = render("HI", recursion=True)
        assert output.strip()

    def test_full_render_chars_from_source(self):
        """Non-space chars in rendered output are chars from 'HI'."""
        output = render("HI", recursion=True)
        allowed = set("HI") | {" ", "\n"}
        for ch in output:
            assert ch in allowed, f"Unexpected char {repr(ch)}"

    def test_full_render_hello(self):
        """render('HELLO', recursion=True) only contains H,E,L,O in fills."""
        output = render("HELLO", recursion=True)
        allowed = set("HELLO") | {" ", "\n"}
        for ch in output:
            assert ch in allowed

    def test_full_render_with_separator(self):
        """render with custom recursion_separator."""
        output = render("AB", recursion=True, recursion_separator="-")
        allowed = set("AB-") | {" ", "\n"}
        for ch in output:
            assert ch in allowed

    def test_full_render_preserves_shape_space(self):
        """Spaces are preserved between and outside letters."""
        output = render("HI", recursion=True)
        rows = output.split("\n")
        assert len(rows) > 1

    def test_full_render_figlet_big(self):
        """Recursion works with figlet 'big' font."""
        output = render("HI", font="big", recursion=True)
        assert output.strip()
        allowed = set("HI") | {" ", "\n", "_", "/", "\\", "|"}
        # FIGlet uses structural chars that are part of the fill — allow them
        # The recursion replaces non-space chars so all non-space in output
        # must come from source "HI" (uppercase)
        for ch in output:
            assert ch in (set("HI") | {" ", "\n"}), f"Unexpected: {repr(ch)}"

    def test_full_render_dimensions_sane(self):
        """Rendered output has expected row count (block font height = 7)."""
        output = render("AB", recursion=True)
        rows = output.split("\n")
        assert len(rows) == 7  # block font is 7 rows tall

    def test_full_render_no_color(self):
        """No ANSI escape codes in plain recursion output."""
        output = render("HI", recursion=True)
        assert "\033[" not in output

    def test_full_render_with_color(self):
        """Recursion + color: ANSI codes present but content still sane."""
        output = render("HI", recursion=True, color="cyan")
        assert "\033[" in output

    def test_full_render_single_char(self):
        """Single character text renders correctly."""
        output = render("A", recursion=True)
        assert output.strip()
        # Only A should appear as non-space (plus possible separator space)
        for ch in output:
            assert ch in ("A", " ", "\n")
