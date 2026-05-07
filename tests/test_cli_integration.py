"""
Package: tests.test_cli_integration
Integration tests for JustDoIt CLI using subprocess.

Tests the command-line interface as users actually invoke it,
verifying exit codes, stdout/stderr handling, file I/O, and error messages.
These tests run the CLI as a real subprocess to catch issues that
unit tests might miss (imports, encoding, path resolution, etc.).
"""

import logging as _logging
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "tests.test_cli_integration"
__updated__ = "2026-04-30 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
def run_cli(*args, input_text=None, timeout=10):
    """Helper to run justdoit CLI as subprocess.

    :param args: Command-line arguments (e.g., "HELLO", "--color", "cyan").
    :param input_text: Optional stdin input.
    :param timeout: Timeout in seconds (default: 10).
    :returns: (stdout, stderr, returncode) tuple.
    """
    import os
    
    cmd = [sys.executable, "justdoit.py"] + list(args)
    
    # Set up environment with UTF-8 encoding for Windows compatibility
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    # Set UTF-8 encoding explicitly for Windows compatibility
    # Use errors='replace' to handle any encoding issues gracefully
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        input=input_text,
        timeout=timeout,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    return result.stdout, result.stderr, result.returncode


# -------------------------------------------------------------------------
class TestBasicExecution:
    """Test basic CLI execution patterns."""

    def test_basic_render_succeeds(self):
        """Basic text render should succeed with exit code 0."""
        stdout, stderr, code = run_cli("HELLO")
        assert code == 0
        assert len(stdout) > 0
        assert "█" in stdout or "#" in stdout  # Block or ASCII chars

    def test_no_args_shows_help(self):
        """No arguments should print help and exit 1."""
        stdout, stderr, code = run_cli()
        assert code == 1
        # Help goes to stdout or stderr depending on argparse
        help_text = stdout + stderr
        assert "usage:" in help_text.lower() or "justdoit" in help_text.lower()

    def test_help_flag_exits_zero(self):
        """--help should succeed with exit code 0."""
        stdout, stderr, code = run_cli("--help")
        assert code == 0
        assert "usage:" in stdout.lower()
        assert "justdoit" in stdout.lower()

    def test_single_char_renders(self):
        """Single character should render successfully."""
        stdout, stderr, code = run_cli("A")
        assert code == 0
        assert len(stdout) > 10  # Should be multi-line ASCII art

    def test_short_word_renders(self):
        """Short word should render successfully."""
        stdout, stderr, code = run_cli("HI")
        assert code == 0
        lines = stdout.strip().split("\n")
        assert len(lines) >= 3  # Block font is 7 rows, slim is 3


# -------------------------------------------------------------------------
class TestInputValidation:
    """Test input validation and error handling."""

    def test_text_too_long_rejects(self):
        """Text exceeding 1000 chars should be rejected."""
        long_text = "A" * 1001
        stdout, stderr, code = run_cli(long_text)
        assert code == 1
        assert "too long" in stderr.lower()
        assert "1001" in stderr  # Should mention actual length
        assert "1000" in stderr  # Should mention limit

    def test_text_exactly_1000_accepts(self):
        """Text at exactly 1000 chars should be accepted."""
        text = "A" * 1000
        stdout, stderr, code = run_cli(text)
        assert code == 0  # Should succeed

    def test_text_just_under_limit_accepts(self):
        """Text at 999 chars should be accepted."""
        text = "A" * 999
        stdout, stderr, code = run_cli(text)
        assert code == 0

    def test_nonexistent_ttf_rejects(self):
        """Nonexistent TTF file should be rejected."""
        stdout, stderr, code = run_cli("TEST", "--ttf", "/nonexistent/font.ttf")
        assert code == 1
        assert "not found" in stderr.lower()
        assert "font.ttf" in stderr

    def test_wrong_ttf_extension_rejects(self):
        """File with wrong extension should be rejected."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            f.write("dummy")
            temp_path = f.name

        try:
            stdout, stderr, code = run_cli("TEST", "--ttf", temp_path)
            assert code == 1
            assert ".ttf" in stderr.lower() or ".otf" in stderr.lower()
            assert ".txt" in stderr
        finally:
            Path(temp_path).unlink()

    def test_ttf_directory_instead_of_file_rejects(self):
        """TTF path pointing to directory should be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_cli("TEST", "--ttf", tmpdir)
            assert code == 1
            assert "not a file" in stderr.lower() or "directory" in stderr.lower()

    def test_invalid_font_name_exits_nonzero(self):
        """Unknown font name should be rejected by argparse."""
        stdout, stderr, code = run_cli("TEST", "--font", "nonexistent_font_xyz")
        assert code != 0  # argparse exits 2 for invalid choice

    def test_invalid_fill_name_exits_nonzero(self):
        """Unknown fill name should be rejected by argparse."""
        stdout, stderr, code = run_cli("TEST", "--fill", "nonexistent_fill_xyz")
        assert code != 0  # argparse exits 2 for invalid choice


# -------------------------------------------------------------------------
class TestFileOutput:
    """Test file output flags."""

    def test_save_svg_creates_file(self):
        """--save-svg should create an SVG file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            svg_path = Path(tmpdir) / "output.svg"
            stdout, stderr, code = run_cli("HI", "--save-svg", str(svg_path))

            assert code == 0
            assert svg_path.exists()
            assert svg_path.stat().st_size > 0

            content = svg_path.read_text(encoding="utf-8")
            assert "<svg" in content
            assert "</svg>" in content

    def test_save_html_creates_file(self):
        """--save-html should create an HTML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = Path(tmpdir) / "output.html"
            stdout, stderr, code = run_cli("HI", "--save-html", str(html_path))

            assert code == 0
            assert html_path.exists()

            content = html_path.read_text(encoding="utf-8")
            assert "<html" in content.lower() or "<pre" in content.lower()

    def test_save_to_nonexistent_dir_fails(self):
        """Saving to nonexistent directory should fail."""
        bad_path = Path("/nonexistent_dir_12345/subdir/output.svg")
        stdout, stderr, code = run_cli("HI", "--save-svg", str(bad_path))

        assert code == 1
        assert "not exist" in stderr.lower() or "no such" in stderr.lower()

    def test_wrong_svg_extension_warns(self):
        """Wrong file extension should produce warning."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wrong_path = Path(tmpdir) / "output.txt"
            stdout, stderr, code = run_cli("HI", "--save-svg", str(wrong_path))

            # Should succeed but warn
            assert code == 0
            assert "warning" in stderr.lower()
            assert ".svg" in stderr.lower()

    def test_terminal_output_with_file_save(self):
        """Terminal output should still happen with --save-svg."""
        with tempfile.TemporaryDirectory() as tmpdir:
            svg_path = Path(tmpdir) / "output.svg"
            stdout, stderr, code = run_cli("HI", "--save-svg", str(svg_path))

            assert code == 0
            # Should still print to stdout
            assert len(stdout) > 0
            assert "█" in stdout or "#" in stdout


# -------------------------------------------------------------------------
class TestColorAndEffects:
    """Test color and effect flags."""

    def test_color_flag_adds_ansi(self):
        """--color should add ANSI escape codes."""
        stdout, stderr, code = run_cli("HI", "--color", "cyan")
        assert code == 0
        assert "\033[" in stdout  # ANSI escape sequence

    def test_rainbow_color_adds_ansi(self):
        """--color rainbow should add multiple ANSI codes."""
        stdout, stderr, code = run_cli("HI", "--color", "rainbow")
        assert code == 0
        assert stdout.count("\033[") > 2  # Multiple color codes

    def test_no_color_no_ansi(self):
        """Without --color, output should have no ANSI codes."""
        stdout, stderr, code = run_cli("HI")
        assert code == 0
        # May have some ANSI (reset codes), but significantly less than colored
        ansi_count = stdout.count("\033[")
        # Plain output should have 0 or very few ANSI codes
        assert ansi_count < 5

    def test_fill_density_changes_chars(self):
        """--fill density should use varied density characters."""
        stdout, stderr, code = run_cli("A", "--fill", "density")
        assert code == 0
        # Density fill uses Unicode block chars and ASCII: █▓▒░@#S%?*+;:,.
        # Check for any density characters (Unicode or ASCII)
        density_chars = set("\u2588\u2593\u2592\u2591@#S%?*+;:,.")
        output_chars = set(stdout.replace("\n", "").replace(" ", ""))
        # Should contain at least a few density chars
        assert len(output_chars & density_chars) > 0

    def test_fill_noise_renders(self):
        """--fill noise should render successfully."""
        stdout, stderr, code = run_cli("A", "--fill", "noise")
        assert code == 0
        assert len(stdout) > 0

    def test_gap_parameter_changes_width(self):
        """--gap should change output width."""
        stdout_gap1, _, _ = run_cli("AB", "--gap", "1")
        stdout_gap3, _, _ = run_cli("AB", "--gap", "3")

        # Gap 3 should produce wider output
        width_gap1 = max(len(line) for line in stdout_gap1.split("\n"))
        width_gap3 = max(len(line) for line in stdout_gap3.split("\n"))
        assert width_gap3 > width_gap1


# -------------------------------------------------------------------------
class TestListCommands:
    """Test --list-* informational commands."""

    def test_list_fonts_exits_zero(self):
        """--list-fonts should succeed."""
        stdout, stderr, code = run_cli("--list-fonts")
        assert code == 0
        assert "block" in stdout.lower()
        assert "slim" in stdout.lower()

    def test_list_colors_exits_zero(self):
        """--list-colors should succeed."""
        stdout, stderr, code = run_cli("--list-colors")
        assert code == 0
        assert "cyan" in stdout.lower()
        assert "red" in stdout.lower()

    def test_list_fonts_no_text_required(self):
        """--list-fonts should work without text argument."""
        stdout, stderr, code = run_cli("--list-fonts")
        assert code == 0
        # Should not complain about missing text
        assert "required" not in stderr.lower()

    def test_list_colors_contains_ansi_samples(self):
        """--list-colors should show colored samples."""
        stdout, stderr, code = run_cli("--list-colors")
        assert code == 0
        # Should contain ANSI codes for the color samples
        assert "\033[" in stdout


# -------------------------------------------------------------------------
class TestMeasureCommand:
    """Test --measure flag."""

    def test_measure_exits_zero(self):
        """--measure should succeed."""
        stdout, stderr, code = run_cli("HELLO", "--measure")
        assert code == 0

    def test_measure_prints_dimensions(self):
        """--measure should print column and row counts."""
        stdout, stderr, code = run_cli("HI", "--measure")
        assert code == 0
        output = stdout + stderr
        assert "cols" in output.lower()
        assert "rows" in output.lower()
        # Should contain numbers
        assert any(char.isdigit() for char in output)

    def test_measure_no_ascii_art(self):
        """--measure should not render ASCII art."""
        stdout, stderr, code = run_cli("HELLO", "--measure")
        assert code == 0
        # Should not contain block characters
        assert "█" not in stdout


# -------------------------------------------------------------------------
class TestEdgeCases:
    """Test edge cases and special characters."""

    def test_empty_string_handled(self):
        """Empty string should be handled gracefully."""
        stdout, stderr, code = run_cli("")
        # Empty string passes validation (< 1000 chars) but has no text arg
        # Should exit 1 (no text provided) or render empty
        assert code in (0, 1)

    def test_spaces_only_renders(self):
        """String with only spaces should render."""
        stdout, stderr, code = run_cli("   ")
        assert code == 0
        # Spaces map to space glyphs, should produce some output

    def test_numbers_render(self):
        """Numeric characters should render."""
        stdout, stderr, code = run_cli("123")
        assert code == 0
        assert len(stdout) > 0

    def test_punctuation_renders(self):
        """Common punctuation should render."""
        stdout, stderr, code = run_cli("A.B")
        assert code == 0
        assert len(stdout) > 0

    def test_lowercase_uppercased(self):
        """Lowercase input should be auto-uppercased."""
        stdout_lower, _, _ = run_cli("hello")
        stdout_upper, _, _ = run_cli("HELLO")
        # Should produce identical output
        assert stdout_lower == stdout_upper

    def test_mixed_case_uppercased(self):
        """Mixed case should be uppercased."""
        stdout_mixed, _, _ = run_cli("HeLLo")
        stdout_upper, _, _ = run_cli("HELLO")
        assert stdout_mixed == stdout_upper


# -------------------------------------------------------------------------
class TestFontSelection:
    """Test font selection via --font flag."""

    def test_block_font_default(self):
        """Block font should be default."""
        stdout_default, _, _ = run_cli("A")
        stdout_explicit, _, _ = run_cli("A", "--font", "block")
        assert stdout_default == stdout_explicit

    def test_slim_font_different(self):
        """Slim font should produce different output than block."""
        stdout_block, _, _ = run_cli("A", "--font", "block")
        stdout_slim, _, _ = run_cli("A", "--font", "slim")
        assert stdout_block != stdout_slim
        # Slim is shorter (3 rows vs 7)
        lines_block = len(stdout_block.strip().split("\n"))
        lines_slim = len(stdout_slim.strip().split("\n"))
        assert lines_slim < lines_block


# -------------------------------------------------------------------------
class TestErrorMessages:
    """Test quality and clarity of error messages."""

    def test_text_too_long_error_is_clear(self):
        """Text length error should be actionable."""
        long_text = "X" * 1500
        stdout, stderr, code = run_cli(long_text)
        assert code == 1
        # Should mention the limit clearly
        assert "1000" in stderr
        # Should mention actual length
        assert "1500" in stderr
        # Should use word "maximum" or "limit"
        assert "maximum" in stderr.lower() or "limit" in stderr.lower()

    def test_file_not_found_mentions_path(self):
        """File not found error should mention the path."""
        bad_path = "/this/does/not/exist.ttf"
        stdout, stderr, code = run_cli("A", "--ttf", bad_path)
        assert code == 1
        # Should echo back the bad path
        assert bad_path in stderr or "not/exist" in stderr

    def test_wrong_extension_mentions_expected(self):
        """Wrong extension error should mention valid extensions."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            stdout, stderr, code = run_cli("A", "--ttf", temp_path)
            assert code == 1
            # Should mention what extensions are valid
            assert ".ttf" in stderr.lower()
            assert ".otf" in stderr.lower()
        finally:
            Path(temp_path).unlink()


# -------------------------------------------------------------------------
@pytest.mark.slow
class TestPerformance:
    """Test performance and resource constraints.

    These tests are marked as slow since they process large inputs.
    Run with: pytest -m slow
    """

    def test_max_length_text_completes(self):
        """1000-char text should complete within timeout."""
        text = "HELLO" * 200  # 1000 chars
        stdout, stderr, code = run_cli(text, timeout=15)
        assert code == 0
        # Should complete (not timeout)

    def test_complex_fill_completes(self):
        """Complex generative fill should complete."""
        stdout, stderr, code = run_cli("TEST", "--fill", "turing", timeout=15)
        assert code == 0

    def test_long_single_word_completes(self):
        """Very long single word should complete."""
        text = "A" * 500
        stdout, stderr, code = run_cli(text, timeout=15)
        assert code == 0


# -------------------------------------------------------------------------
class TestStdoutStderrSeparation:
    """Test that stdout and stderr are used correctly."""

    def test_normal_render_only_stdout(self):
        """Normal render should write only to stdout."""
        stdout, stderr, code = run_cli("HI")
        assert code == 0
        assert len(stdout) > 0
        assert stderr == ""  # No errors or warnings

    def test_validation_error_only_stderr(self):
        """Validation errors should write only to stderr."""
        stdout, stderr, code = run_cli("A" * 1001)
        assert code == 1
        assert len(stderr) > 0
        assert stdout == ""  # No output on error

    def test_list_fonts_uses_stdout(self):
        """--list-fonts should write to stdout."""
        stdout, stderr, code = run_cli("--list-fonts")
        assert code == 0
        assert "block" in stdout.lower()
        # Stderr should be empty or minimal
        assert len(stderr) < 50


# -------------------------------------------------------------------------
class TestRealWorldUsage:
    """Test realistic usage patterns."""

    def test_typical_usage_pattern(self):
        """Common usage: text + font + color."""
        stdout, stderr, code = run_cli("HELLO", "--font", "block", "--color", "cyan")
        assert code == 0
        assert len(stdout) > 0
        assert "\033[" in stdout  # Has color

    def test_save_to_file_pattern(self):
        """Common pattern: render to SVG file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            svg_path = Path(tmpdir) / "art.svg"
            stdout, stderr, code = run_cli(
                "HELLO",
                "--font", "slim",
                "--color", "cyan",
                "--save-svg", str(svg_path)
            )
            assert code == 0
            assert svg_path.exists()
            # Still prints to terminal
            assert len(stdout) > 0

    def test_creative_fill_pattern(self):
        """Pattern: creative fill with color."""
        stdout, stderr, code = run_cli(
            "ART",
            "--fill", "noise",
            "--color", "rainbow"
        )
        assert code == 0
        assert len(stdout) > 0
