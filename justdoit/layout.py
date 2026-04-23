"""
Package: justdoit.layout
Layout primitives for size, scale, and resolution-aware rendering.

Provides:
  measure()       — compute (cols, rows) of a render without rendering
  RenderTarget    — dataclass for display-aware font sizing
  DISPLAYS        — named display presets
  fit_text()      — truncate text to fit within a column limit
  terminal_size() — detect terminal dimensions with fallback

Pure Python stdlib — no Pillow, no render dependencies beyond FONTS.
"""

import logging as _logging
import os
import re
from dataclasses import dataclass

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "justdoit.layout"
__updated__ = "2026-04-04 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
def measure(
    text: str,
    font: str = "block",
    gap: int = 1,
    iso_depth: int = 0,
    bloom_radius: int = 0,
    warp_amplitude: float = 0.0,
) -> tuple[int, int]:
    """Return ``(cols, rows)`` of the rendered output without rendering.

    Pure measurement — no ANSI output, no file I/O. Used to check whether
    text will fit a given terminal width before committing to a full render.

    Glyph widths are variable per character and per font; this function
    iterates actual glyph data from the FONTS dict rather than assuming a
    fixed width.

    :param text: Input text string (same as ``render()``).
    :param font: Font name (default: ``'block'``).
    :param gap: Gap between characters in spaces (default: ``1``).
    :param iso_depth: If > 0, add isometric extrusion footprint (default: ``0``).
    :param bloom_radius: If > 0, add bloom halo margin on all sides (default: ``0``).
        TODO: update when C12 (bloom effect) is built — margin calculation may change.
    :param warp_amplitude: If > 0, add sine-warp horizontal overflow (default: ``0.0``).
    :returns: ``(cols, rows)`` as integers.
    :raises ValueError: If ``font`` is not found in the FONTS registry.

    .. note::
       TTF fonts are not supported — their glyph widths require Pillow to
       measure. TTF measurement is a separate code path (future work).
    """
    from justdoit.fonts import FONTS

    font_data = FONTS.get(font)
    if font_data is None:
        raise ValueError(
            f"Unknown font {font!r}. Available fonts: {list(FONTS.keys())}"
        )

    # Font height: all glyphs in a font have the same height.
    font_height = len(next(iter(font_data.values())))

    if not text:
        return 0, font_height

    text_upper = text.upper()
    cols = 0
    for char in text_upper:
        glyph = font_data.get(char, font_data.get(" "))
        glyph_w = max(len(row) for row in glyph)
        # Mirror the rasterizer's behavior: gap is added after every character
        # (including the last), because the rasterizer appends `row + spacer`
        # unconditionally in its assembly loop.
        cols += glyph_w + gap

    rows = font_height

    # Spatial effect footprints — expand bounding box to include effect margins.
    if iso_depth > 0:
        cols += iso_depth
        rows += iso_depth
    if bloom_radius > 0:
        # TODO: update when C12 (bloom effect) is built — margins may differ.
        cols += bloom_radius * 2
        rows += bloom_radius * 2
    if warp_amplitude > 0:
        cols += int(warp_amplitude) + 1

    return cols, rows


# -------------------------------------------------------------------------
@dataclass
class RenderTarget:
    """Describes a physical display target for size/scale calculations.

    Used to compute font sizes, maximum column counts, and SVG dimensions
    for a given display configuration.

    :param display_w: Display width in pixels.
    :param display_h: Display height in pixels.
    :param dpi: Display DPI (default: ``96`` — standard Windows/Linux).
    :param scaling: OS DPI scaling factor, e.g. ``1.5`` for 150% (default: ``1.0``).
    :param char_w_ratio: Monospace cell width as fraction of cell height (default: ``0.6``).

    Example::

        rt = RenderTarget(3840, 2160)
        cols, rows = measure("JUST DO IT", font="block")
        pt = rt.max_font_pt(cols, rows)
        px = rt.svg_font_size_px(pt)
    """

    display_w: int
    display_h: int
    dpi: float = 96.0
    scaling: float = 1.0
    char_w_ratio: float = 0.6

    @property
    def effective_dpi(self) -> float:
        """DPI after OS scaling is applied.

        :returns: ``dpi * scaling``
        """
        return self.dpi * self.scaling

    def cell_size_px(self, font_pt: float) -> tuple[float, float]:
        """Return ``(cell_width_px, cell_height_px)`` for a given font size in points.

        :param font_pt: Font size in typographic points.
        :returns: ``(cell_w, cell_h)`` as floats.
        """
        cell_h = font_pt * (self.effective_dpi / 72.0)
        cell_w = cell_h * self.char_w_ratio
        return cell_w, cell_h

    def max_columns(self, font_pt: float) -> int:
        """Maximum terminal columns available at this font size.

        :param font_pt: Font size in typographic points.
        :returns: Integer column count.
        """
        cell_w, _ = self.cell_size_px(font_pt)
        return int(self.display_w / cell_w)

    def max_rows(self, font_pt: float) -> int:
        """Maximum terminal rows available at this font size.

        :param font_pt: Font size in typographic points.
        :returns: Integer row count.
        """
        _, cell_h = self.cell_size_px(font_pt)
        return int(self.display_h / cell_h)

    def max_font_pt(self, cols_needed: int, rows_needed: int) -> int:
        """Largest integer font pt size where ``cols_needed`` and ``rows_needed`` both fit.

        Scans the full range 1–499 and returns the *last* point size where
        both column and row constraints are simultaneously satisfied. No early
        break is used because at extreme sizes a tall display may satisfy rows
        but fail cols (or vice versa) — scanning the full range handles
        non-monotone cases correctly.

        :param cols_needed: Required number of terminal columns.
        :param rows_needed: Required number of terminal rows.
        :returns: Largest valid font point size (integer, minimum ``1``).
        """
        best = 1
        for pt in range(1, 500):
            if (self.max_columns(pt) >= cols_needed
                    and self.max_rows(pt) >= rows_needed):
                best = pt
            # No early break — scan full range for non-monotone display configs.
        return best

    def svg_font_size_px(self, font_pt: float) -> int:
        """SVG ``font-size`` in pixels for this font point size at this target's effective DPI.

        :param font_pt: Font size in typographic points.
        :returns: Pixel size as integer.
        """
        return int(font_pt * (self.effective_dpi / 72.0))

    def fit_font_pt(
        self,
        text: str,
        font: str = "block",
        gap: int = 1,
        iso_depth: int = 0,
        bloom_radius: int = 0,
    ) -> int:
        """Return the largest font point size where ``text`` fits on this display.

        Uses :func:`measure` to determine the render's column/row footprint,
        then finds the largest point size where that footprint fits within
        display bounds.

        :param text: Input text string.
        :param font: Font name (default: ``'block'``).
        :param gap: Gap between characters (default: ``1``).
        :param iso_depth: Isometric depth footprint (default: ``0``).
        :param bloom_radius: Bloom halo margin (default: ``0``).
        :returns: Font point size as integer.
        """
        cols, rows = measure(
            text, font=font, gap=gap,
            iso_depth=iso_depth, bloom_radius=bloom_radius,
        )
        return self.max_font_pt(cols, rows)

    @classmethod
    def from_string(cls, spec: str, **kwargs) -> "RenderTarget":
        """Parse a display spec string like ``'3840x2160'`` or ``'3840x2160@1.5x'``.

        Format: ``WxH``  or  ``WxH@SCALINGx``  (e.g. ``'3840x2160@2.0x'``)

        :param spec: Display spec string.
        :param kwargs: Additional keyword arguments passed to :class:`RenderTarget`.
        :returns: :class:`RenderTarget` instance.
        :raises ValueError: If ``spec`` format is invalid.
        """
        m = re.fullmatch(r"(\d+)x(\d+)(?:@([\d.]+)x)?", spec)
        if not m:
            raise ValueError(
                f"Invalid display spec {spec!r}. "
                "Expected format: WxH or WxH@SCALINGx (e.g. '3840x2160' or '3840x2160@2.0x')"
            )
        w = int(m.group(1))
        h = int(m.group(2))
        scaling = float(m.group(3)) if m.group(3) else 1.0
        return cls(display_w=w, display_h=h, scaling=scaling, **kwargs)


# -------------------------------------------------------------------------
#: Named display presets for common configurations.
DISPLAYS: dict[str, RenderTarget] = {
    "fhd":       RenderTarget(1920, 1080),
    "qhd":       RenderTarget(2560, 1440),
    "4k":        RenderTarget(3840, 2160),
    "5k":        RenderTarget(5120, 2880),
    "ultrawide": RenderTarget(5120, 1440),
    "4k-hidpi":  RenderTarget(3840, 2160, scaling=2.0),
    "fhd-hidpi": RenderTarget(1920, 1080, scaling=2.0),
}


# -------------------------------------------------------------------------
def fit_text(
    text: str,
    target_cols: int,
    font: str = "block",
    gap: int = 1,
    iso_depth: int = 0,
    bloom_radius: int = 0,
    truncate: bool = True,
    truncation_suffix: str = "…",
) -> tuple[str, int]:
    """Find the longest prefix of ``text`` that fits within ``target_cols``.

    The truncation suffix is included in the column measurement — the
    returned text always fits within ``target_cols`` including the suffix.

    :param text: Input text string.
    :param target_cols: Maximum column width to fit within.
    :param font: Font name (default: ``'block'``).
    :param gap: Gap between characters (default: ``1``).
    :param iso_depth: Isometric depth footprint (default: ``0``).
    :param bloom_radius: Bloom halo margin (default: ``0``).
    :param truncate: If ``True``, truncate text to fit. If ``False``, raise
        :exc:`ValueError` when text is too wide (default: ``True``).
    :param truncation_suffix: Suffix to append when truncating (default: ``'…'``).
    :returns: ``(fitted_text, actual_cols)`` tuple.
    :raises ValueError: If ``truncate=False`` and text exceeds ``target_cols``.
    :raises ValueError: If ``font`` is not found in the FONTS registry.
    """
    def _measure(t: str) -> int:
        if not t:
            return 0
        cols, _ = measure(t, font=font, gap=gap,
                          iso_depth=iso_depth, bloom_radius=bloom_radius)
        return cols

    full_cols = _measure(text)
    if full_cols <= target_cols:
        return text, full_cols

    if not truncate:
        raise ValueError(
            f"Text too wide: {full_cols} cols > {target_cols}. "
            f"Pass truncate=True or reduce text length."
        )

    # Binary search: find longest prefix where prefix + suffix fits.
    low, high = 0, len(text)
    best_len = 0
    best_cols = _measure(truncation_suffix)

    while low <= high:
        mid = (low + high) // 2
        candidate = text[:mid] + truncation_suffix
        c = _measure(candidate)
        if c <= target_cols:
            best_len = mid
            best_cols = c
            low = mid + 1
        else:
            high = mid - 1

    return text[:best_len] + truncation_suffix, best_cols


# -------------------------------------------------------------------------
def terminal_size() -> tuple[int, int]:
    """Return ``(cols, rows)`` of the current terminal.

    Uses :func:`os.get_terminal_size` with a fallback to ``(80, 24)`` if
    stdout is not a TTY (e.g. piped output, CI environment).

    :returns: ``(cols, rows)`` tuple.
    """
    try:
        ts = os.get_terminal_size()
        return ts.columns, ts.lines
    except OSError:
        return 80, 24


# -------------------------------------------------------------------------
def fit_ttf_size(
    text: str,
    target_cols: int,
    font_path: str,
    gap: int = 1,
    iso_depth: int = 0,
    bloom_radius: int = 0,
    size_min: int = 8,
    size_max: int = 200,
) -> int:
    """Find the largest TTF rasterization size where text fits within target_cols.

    Performs a two-pass search: a coarse scan in steps of 8pt to bracket the
    answer, then a fine binary search in the bracketed range. Caches rasterized
    font measurements to avoid redundant Pillow calls.

    Requires Pillow (``pip install Pillow``).

    :param text: Text to render (same as render()).
    :param target_cols: Maximum terminal columns to fit within.
    :param font_path: Path to a .ttf or .otf font file.
    :param gap: Character gap between letters (default: 1).
    :param iso_depth: Isometric depth footprint to account for (default: 0).
    :param bloom_radius: Bloom halo margin on each side (default: 0).
    :param size_min: Minimum font size to try in points (default: 8).
    :param size_max: Maximum font size to try in points (default: 200).
    :returns: Optimal TTF font size in points as an integer.
    :raises ImportError: If Pillow is not installed.
    :raises ValueError: If even size_min produces output wider than target_cols,
        or if the font file cannot be loaded.
    """
    try:
        from justdoit.fonts.ttf import load_ttf_font
    except ImportError:
        raise ImportError(
            "fit_ttf_size() requires Pillow. Install with: pip install Pillow"
        )

    # Cache: (font_path, size) -> cols so we don't re-rasterize same size twice
    _cache: dict = {}

    def _cols_at_size(size: int) -> int:
        if (font_path, size) not in _cache:
            fname = load_ttf_font(font_path, font_size=size)
            c, _ = measure(text, font=fname, gap=gap,
                           iso_depth=iso_depth, bloom_radius=bloom_radius)
            _cache[(font_path, size)] = c
        return _cache[(font_path, size)]

    # Validate minimum size fits
    if _cols_at_size(size_min) > target_cols:
        raise ValueError(
            f"Text '{text}' at minimum TTF size {size_min}pt requires "
            f"{_cols_at_size(size_min)} cols — exceeds target {target_cols}. "
            f"Use shorter text or increase target_cols."
        )

    # Pass 1: coarse scan in steps of 8 to bracket the answer
    coarse_step = 8
    coarse_sizes = list(range(size_min, size_max + 1, coarse_step))

    best_coarse = size_min
    for s in coarse_sizes:
        if _cols_at_size(s) <= target_cols:
            best_coarse = s
        else:
            break

    # Pass 2: fine binary search in [best_coarse, best_coarse + coarse_step]
    lo = best_coarse
    hi = min(best_coarse + coarse_step, size_max)

    # If hi already fits, extend search upward (stop at size_max to avoid infinite loop)
    while hi < size_max and _cols_at_size(hi) <= target_cols:
        lo = hi
        hi = min(hi + coarse_step, size_max)

    best = lo
    while lo <= hi:
        mid = (lo + hi) // 2
        if _cols_at_size(mid) <= target_cols:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1

    return best


# -------------------------------------------------------------------------
def fit_ttf_to_row_count(
    target_rows: int,
    font_path: str,
    size_min: int = 4,
    size_max: int = 200,
) -> int:
    """Find the TTF point size that produces glyphs with exactly ``target_rows`` rows.

    Binary-searches point sizes so that :func:`rasterize_ttf` produces glyph
    dicts whose row count equals ``target_rows``.  Because ``rasterize_ttf``
    uses ``font_size`` as the target height directly, the answer is simply
    ``target_rows`` — but this function validates that and falls back to a
    binary search if the relationship ever changes.

    :param target_rows: Desired number of rows per glyph.
    :param font_path: Path to a .ttf or .otf font file.
    :param size_min: Minimum point size to try (default: 8).
    :param size_max: Maximum point size to try (default: 200).
    :returns: TTF point size as an integer.
    :raises ImportError: If Pillow is not installed.
    """
    try:
        from justdoit.fonts.ttf import rasterize_ttf
    except ImportError:
        raise ImportError(
            "fit_ttf_to_row_count() requires Pillow. Install with: pip install Pillow"
        )

    def _rows_at_size(size: int) -> int:
        glyphs = rasterize_ttf(font_path, font_size=size)
        sample = next(iter(glyphs.values()))
        return len(sample) if sample else 0

    # rasterize_ttf uses font_size as target_height, so try direct match first
    if size_min <= target_rows <= size_max:
        if _rows_at_size(target_rows) == target_rows:
            return target_rows

    # Fallback: binary search
    best = size_min
    lo, hi = size_min, size_max
    while lo <= hi:
        mid = (lo + hi) // 2
        r = _rows_at_size(mid)
        if r == target_rows:
            return mid
        elif r < target_rows:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return best


# -------------------------------------------------------------------------
def find_default_ttf() -> "str | None":
    """Return path to a usable system TTF font, or None if none found.

    Checks common system font locations. Returns the first monospace font
    found, falling back to the first TTF found.

    :returns: Absolute path to a .ttf file, or None.
    """
    candidates = [
        # Prefer monospace fonts for ASCII art
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
        "/mnt/c/Windows/Fonts/consola.ttf",   # Consolas (WSL)
        "/mnt/c/Windows/Fonts/cour.ttf",       # Courier New (WSL)
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    # Fall back: first TTF found anywhere
    try:
        from justdoit.fonts.ttf import find_system_fonts
        fonts = find_system_fonts()
        return fonts[0] if fonts else None
    except ImportError:
        return None
