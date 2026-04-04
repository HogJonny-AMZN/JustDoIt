# Implementation Plan — Size, Scale & Resolution (L01–L05)

**Created:** 2026-04-04  
**Design doc:** `docs/SIZE_SCALE_RESOLUTION.md`  
**Status:** Ready to implement  
**Estimated sessions:** 3 (Phase 1 + 2 together, Phase 3, Phase 4)

---

## Pre-Implementation Checklist

Before starting any session:

```bash
cd /path/to/JustDoIt
git pull --rebase origin main
/home/node/.local/bin/uv run pytest tests/ -q   # must be green
```

Read:
- `docs/SIZE_SCALE_RESOLUTION.md` — the full design
- This file — the concrete task list
- `justdoit/fonts/__init__.py` — FONTS dict structure
- `justdoit/output/svg.py` — to_svg() / save_svg()
- `scripts/generate_gallery.py` — gallery structure

---

## Key facts established during analysis

- Block font: glyphs are **variable width** per character (A=6w, J=6w at block; A=11w at figlet-block)
- `measure()` MUST iterate actual glyph widths from FONTS dict — cannot assume a fixed width
- FIGlet glyphs also have variable widths (slant A=8w, J=9w)
- `svg.py` `to_svg()` already accepts `font_size: int = 14` — it's just never passed by callers
- `cast.py` already has `_detect_dims()` that auto-sizes from frame content — do NOT break this
- `FONTS` dict maps `{font_name: {char: [row_str, ...]}}` — glyph width = `max(len(row) for row in glyph)`
- All builtin+FIGlet fonts have fixed height per font (all glyphs same height)
- TTF fonts: variable width, needs Pillow — defer to future work, document limitation
- Tests use `_MODULE_NAME`, `__updated__`, `__version__`, `__author__` header pattern — follow it

---

## Phase 1+2 — Core Primitives + SVG Scaling

**One session. Target: ~150 lines of new code + ~60 lines of tests.**

### Task 1.1 — Create `justdoit/layout.py`

New file. All functions are pure Python stdlib — no Pillow, no render deps.

#### `measure(text, font, gap, iso_depth, bloom_radius, warp_amplitude) → (cols, rows)`

```python
def measure(
    text: str,
    font: str = "block",
    gap: int = 1,
    iso_depth: int = 0,
    bloom_radius: int = 0,
    warp_amplitude: float = 0.0,
) -> tuple[int, int]:
```

**Implementation notes:**
- Import `FONTS` from `justdoit.fonts`
- Look up `font_data = FONTS.get(font)` — raise `ValueError` if unknown (same as rasterizer)
- For each char in `text.upper()`: `glyph = font_data.get(char, font_data.get(" "))`
- `glyph_w = max(len(row) for row in glyph)`
- Accumulate: `cols += glyph_w`; add `gap` between chars (not after last)
- `rows = len(next(iter(font_data.values())))` — font height (all glyphs same height)
- Apply spatial footprints after base measurement:
  - `iso_depth > 0`: cols += iso_depth; rows += iso_depth
  - `bloom_radius > 0`: cols += bloom_radius * 2; rows += bloom_radius * 2 (# TODO: update when C12 is built)
  - `warp_amplitude > 0`: cols += int(warp_amplitude) + 1
- Return `(cols, rows)`

**Edge cases:**
- Empty string `""` → `(0, font_height)` — don't crash
- Single char → no gap added
- Space char `" "` → use space glyph width
- TTF fonts not in `FONTS` dict → will raise ValueError (acceptable; document in docstring)

---

#### `RenderTarget` dataclass

```python
@dataclass
class RenderTarget:
    display_w: int
    display_h: int
    dpi: float = 96.0
    scaling: float = 1.0
    char_w_ratio: float = 0.6
```

Methods (all pure arithmetic — no imports beyond `math` and `dataclasses`):

| Method | Returns | Notes |
|--------|---------|-------|
| `effective_dpi` (property) | float | `dpi * scaling` |
| `cell_size_px(font_pt)` | `(cell_w, cell_h)` floats | `cell_h = pt * (eff_dpi/72)`, `cell_w = cell_h * ratio` |
| `max_columns(font_pt)` | int | `int(display_w / cell_w)` |
| `max_rows(font_pt)` | int | `int(display_h / cell_h)` |
| `max_font_pt(cols_needed, rows_needed)` | int | binary-search or linear scan 1→499, return last pt where both fit |
| `svg_font_size_px(font_pt)` | int | `int(pt * (eff_dpi / 72.0))` |
| `fit_font_pt(text, font, gap, iso_depth, bloom_radius)` | int | calls `measure()` then `max_font_pt()` |
| `from_string(spec, **kwargs)` (classmethod) | RenderTarget | parses `"3840x2160"` or `"3840x2160@2.0x"` |

**`max_font_pt` implementation:** linear scan is fine (500 iterations of trivial arithmetic
is ~microseconds). Binary search is not necessary.

```python
def max_font_pt(self, cols_needed: int, rows_needed: int) -> int:
    best = 1
    for pt in range(1, 500):
        if self.max_columns(pt) >= cols_needed and self.max_rows(pt) >= rows_needed:
            best = pt
        else:
            # Once we fail, keep going — at very high pt we might fail on rows
            # but a slightly smaller pt might still work on a tall display.
            # So scan the full range rather than breaking early.
            pass
    return best
```

Wait — actually break logic is wrong for tall displays. A 3840×2160 monitor
has MORE vertical room than a 5120×1440. At some pt, cols fail before rows.
Scan full range and track the *last* pt where BOTH conditions are satisfied.

**`from_string` format:** `r"(\d+)x(\d+)(?:@([\d.]+)x)?"` — see design doc.

---

#### Named display presets

```python
DISPLAYS: dict[str, RenderTarget] = {
    "fhd":         RenderTarget(1920,  1080),
    "qhd":         RenderTarget(2560,  1440),
    "4k":          RenderTarget(3840,  2160),
    "5k":          RenderTarget(5120,  2880),
    "ultrawide":   RenderTarget(5120,  1440),
    "4k-hidpi":    RenderTarget(3840,  2160, scaling=2.0),
    "fhd-hidpi":   RenderTarget(1920,  1080, scaling=2.0),
}
```

---

#### `fit_text(text, target_cols, font, gap, iso_depth, bloom_radius, truncate, truncation_suffix) → (str, int)`

```python
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
```

**Implementation notes:**
- First check full text: `cols, _ = measure(text, font, gap, iso_depth, bloom_radius)`
- If fits: return `(text, cols)` immediately
- If `truncate=False`: raise `ValueError(f"Text too wide: {cols} cols > {target_cols}")`
- Binary search on text length:
  - Low=0, High=len(text)
  - At each mid: `measure(text[:mid] + truncation_suffix, ...)` — include suffix in measurement
  - Find longest prefix where `cols <= target_cols`
- Return `(text[:best] + truncation_suffix, actual_cols)`
- If even 1 char + suffix doesn't fit: return `(truncation_suffix, suffix_cols)`

---

#### `terminal_size() → (cols, rows)`

```python
def terminal_size() -> tuple[int, int]:
    import os
    try:
        ts = os.get_terminal_size()
        return ts.columns, ts.lines
    except OSError:
        return 80, 24
```

Simple. Already exists scattered; make it canonical.

---

### Task 1.2 — Update `justdoit/output/svg.py`

**Only one change:** `save_svg()` should accept and pass through `font_size`:

```python
def save_svg(text: str, path: str, font_size: int = 14, **kwargs) -> None:
    svg = to_svg(text, font_size=font_size, **kwargs)
    ...
```

Currently `save_svg()` signature is `(text, path, **kwargs)` — `font_size` goes
via `**kwargs` to `to_svg()`. Making it explicit in the signature improves IDE
support and makes it obvious to callers.

**No changes to `to_svg()` itself.** The SVG structure, `_CHAR_W_RATIO`, and
`textLength` improvement are deferred to Phase 2+ (see open question §9.5 in design doc).

---

### Task 1.3 — Write `tests/test_layout.py`

```
tests/test_layout.py
```

Test cases (all pure Python, no Pillow, no TTF):

```python
# measure() — basic correctness
def test_measure_known_output():
    """measure() matches actual render() output dimensions."""
    from justdoit.core.rasterizer import render
    result = render("JUST DO IT", font="block", gap=1)
    lines = result.split("\n")
    actual_cols = max(len(l) for l in lines)
    actual_rows = len(lines)
    cols, rows = measure("JUST DO IT", font="block", gap=1)
    assert cols == actual_cols
    assert rows == actual_rows

def test_measure_empty():
    cols, rows = measure("", font="block", gap=1)
    assert cols == 0
    assert rows == 7   # block font height

def test_measure_single_char():
    cols, rows = measure("A", font="block", gap=1)
    assert cols > 0
    assert rows == 7

def test_measure_gap_zero():
    cols_gap1, _ = measure("HI", font="block", gap=1)
    cols_gap0, _ = measure("HI", font="block", gap=0)
    assert cols_gap0 < cols_gap1

def test_measure_iso_depth():
    base_cols, base_rows = measure("HI", font="block", gap=1)
    iso_cols, iso_rows = measure("HI", font="block", gap=1, iso_depth=4)
    assert iso_cols == base_cols + 4
    assert iso_rows == base_rows + 4

def test_measure_bloom():
    base_cols, base_rows = measure("HI", font="block", gap=1)
    bloom_cols, bloom_rows = measure("HI", font="block", gap=1, bloom_radius=4)
    assert bloom_cols == base_cols + 8   # both sides
    assert bloom_rows == base_rows + 8

def test_measure_figlet():
    """measure() works for FIGlet fonts too."""
    cols, rows = measure("JUST DO IT", font="slant", gap=1)
    result = render("JUST DO IT", font="slant", gap=1)
    lines = result.split("\n")
    assert cols == max(len(l) for l in lines)

def test_measure_unknown_font():
    with pytest.raises(ValueError):
        measure("HI", font="nonexistent_font")

# RenderTarget
def test_render_target_cell_size():
    rt = RenderTarget(3840, 2160, dpi=96.0, scaling=1.0)
    cell_w, cell_h = rt.cell_size_px(12)
    assert abs(cell_h - 16.0) < 0.1    # 12pt * 96/72 = 16px
    assert abs(cell_w - 9.6) < 0.1    # 16 * 0.6

def test_render_target_max_columns():
    rt = RenderTarget(3840, 2160)
    cols = rt.max_columns(12)
    assert cols == int(3840 / 9.6)  # 400

def test_render_target_max_font_pt():
    rt = RenderTarget(3840, 2160)
    cols, rows = measure("JUST DO IT", font="block", gap=1)
    pt = rt.max_font_pt(cols, rows)
    # Should be around 63 based on our prior calculation
    assert 55 <= pt <= 70

def test_render_target_hidpi():
    rt_100 = RenderTarget(3840, 2160, scaling=1.0)
    rt_200 = RenderTarget(3840, 2160, scaling=2.0)
    pt_100 = rt_100.max_font_pt(76, 19)
    pt_200 = rt_200.max_font_pt(76, 19)
    assert pt_200 < pt_100   # higher DPI scaling = smaller max pt

def test_render_target_from_string_basic():
    rt = RenderTarget.from_string("3840x2160")
    assert rt.display_w == 3840
    assert rt.display_h == 2160
    assert rt.scaling == 1.0

def test_render_target_from_string_with_scaling():
    rt = RenderTarget.from_string("3840x2160@2.0x")
    assert rt.display_w == 3840
    assert rt.scaling == 2.0

def test_render_target_from_string_invalid():
    with pytest.raises(ValueError):
        RenderTarget.from_string("notaresolution")

def test_displays_preset_4k():
    rt = DISPLAYS["4k"]
    assert rt.display_w == 3840
    assert rt.display_h == 2160

# fit_text()
def test_fit_text_already_fits():
    text, cols = fit_text("HI", target_cols=200)
    assert text == "HI"
    assert cols <= 200

def test_fit_text_truncates():
    text, cols = fit_text("JUST DO IT", target_cols=30, font="block")
    assert cols <= 30
    assert len(text) < len("JUST DO IT")

def test_fit_text_no_truncate_raises():
    with pytest.raises(ValueError):
        fit_text("JUST DO IT", target_cols=10, font="block", truncate=False)

def test_fit_text_suffix_included_in_width():
    """The truncation suffix must be included in the column measurement."""
    text, cols = fit_text("JUST DO IT", target_cols=40, font="block", truncation_suffix="...")
    assert cols <= 40

# terminal_size()
def test_terminal_size_fallback():
    """terminal_size() returns a valid (cols, rows) tuple."""
    cols, rows = terminal_size()
    assert cols >= 1
    assert rows >= 1
```

---

### Task 1.4 — Validate SVG at large font sizes

After implementing, do a manual sanity check:

```python
# Run once manually — not a unit test (visual check required)
from justdoit.core.rasterizer import render
from justdoit.output.svg import save_svg
from justdoit.layout import measure, RenderTarget, DISPLAYS

text = "JUST DO IT"
rt = DISPLAYS["4k"]
cols, rows = measure(text)
pt = rt.max_font_pt(cols, rows)
px = rt.svg_font_size_px(pt)

result = render(text, font="block", fill="flame", color="red")
save_svg(result, "/tmp/justdoit-4k-test.svg", font_size=px)
print(f"Rendered at {pt}pt ({px}px). Open /tmp/justdoit-4k-test.svg in browser.")
print(f"Check: are all columns aligned? No overlapping chars? No gaps?")
```

If columns drift visibly at large sizes, investigate `textLength` SVG fix (design doc §2.3).
Document findings in `docs/decisions/ADR-007-svg-large-font-metrics.md` before shipping Phase 4.

---

### Phase 1+2 commit

```bash
git add justdoit/layout.py tests/test_layout.py justdoit/output/svg.py
git commit -m "feat: L01-L03 layout primitives — measure(), RenderTarget, fit_text()

justdoit/layout.py (new):
  measure(text, font, gap, iso_depth, bloom_radius, warp_amplitude) → (cols, rows)
  RenderTarget dataclass: cell_size_px, max_columns, max_rows, max_font_pt,
    svg_font_size_px, fit_font_pt, from_string(), DISPLAYS presets
  fit_text(text, target_cols, ...) → (fitted_text, actual_cols)
  terminal_size() → (cols, rows) with 80×24 fallback

justdoit/output/svg.py:
  save_svg(): make font_size explicit param (was implicit **kwargs passthrough)

tests/test_layout.py (new):
  measure() correctness vs actual render() output
  RenderTarget arithmetic, from_string(), presets
  fit_text() truncation and suffix width inclusion
  terminal_size() fallback"
git push
```

---

## Phase 3 — CLI Flags

**One session. Target: ~80 lines in `cli.py`.**

### Task 3.1 — Add `--measure` flag

```python
parser.add_argument(
    "--measure", action="store_true",
    help="Print render dimensions (cols × rows) without rendering and exit.",
)
```

**Handler (runs before render, after font resolution):**

```python
if args.measure:
    from justdoit.layout import measure, DISPLAYS
    iso_d = args.iso if args.iso else 0
    cols, rows = measure(args.text, font=font_name, gap=args.gap, iso_depth=iso_d)
    print(f"Render size:  {cols} cols × {rows} rows")
    print()
    print("Display fits:")
    for label, rt in DISPLAYS.items():
        pt = rt.max_font_pt(cols, rows)
        cell_w, cell_h = rt.cell_size_px(pt)
        letter_h_in = (rows * cell_h) / 96.0
        print(f"  {label:<12} {rt.display_w}×{rt.display_h}  →  {pt}pt  "
              f"letter height {letter_h_in:.2f}\"  "
              f"grid {rt.max_columns(pt)}×{rt.max_rows(pt)}")
    sys.exit(0)
```

**Exit immediately after printing** — do not proceed to render.

---

### Task 3.2 — Add `--target` flag

```python
parser.add_argument(
    "--target", metavar="WxH[@Sx]",
    help="Display target spec for sizing (e.g. 3840x2160 or 3840x2160@2.0x). "
         "Used with --save-svg to auto-size font, or standalone to print fit info.",
)
```

**Handler:**

```python
_target_rt = None
if args.target:
    from justdoit.layout import RenderTarget
    try:
        _target_rt = RenderTarget.from_string(args.target)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
```

**Auto-size SVG when `--target` + `--save-svg`:**

```python
if args.save_svg:
    svg_font_size = args.svg_font_size   # may be None
    if svg_font_size is None and _target_rt is not None:
        from justdoit.layout import measure
        iso_d = args.iso if args.iso else 0
        cols, rows = measure(args.text, font=font_name, gap=args.gap, iso_depth=iso_d)
        pt = _target_rt.max_font_pt(cols, rows)
        svg_font_size = _target_rt.svg_font_size_px(pt)
    save_svg(output, args.save_svg, font_size=svg_font_size or 14)
```

**Standalone `--target` output** (when no `--save-svg`):

```python
if _target_rt is not None and not args.save_svg:
    from justdoit.layout import measure
    iso_d = args.iso if args.iso else 0
    cols, rows = measure(args.text, font=font_name, gap=args.gap, iso_depth=iso_d)
    pt = _target_rt.max_font_pt(cols, rows)
    cell_w, cell_h = _target_rt.cell_size_px(pt)
    letter_h = rows * cell_h / 96.0
    print(
        f"Target: {_target_rt.display_w}×{_target_rt.display_h} "
        f"@ {_target_rt.scaling:.1f}× scaling\n"
        f"Max font size: {pt}pt  (cell: {cell_w:.1f}×{cell_h:.1f}px)\n"
        f"Letter height: {letter_h:.2f}\"  ({letter_h*2.54:.2f} cm)\n"
        f"Terminal grid: {_target_rt.max_columns(pt)}×{_target_rt.max_rows(pt)}\n"
        f"SVG font-size: {_target_rt.svg_font_size_px(pt)}px",
        file=sys.stderr,
    )
    # continue to render and print normally — --target alone doesn't suppress output
```

Note: standalone `--target` info goes to **stderr** so it doesn't pollute
stdout when output is piped. The render still prints to stdout normally.

---

### Task 3.3 — Add `--svg-font-size` flag

```python
parser.add_argument(
    "--svg-font-size", type=int, default=None, metavar="N",
    help="Font size in pixels for SVG output (default: 14). Overrides --target.",
)
```

Wire into SVG save path (see Task 3.2 above — `args.svg_font_size` takes precedence
over `--target`-derived size).

---

### Task 3.4 — Add `--fit` flag

```python
parser.add_argument(
    "--fit", type=int, default=None, metavar="COLS",
    help="Truncate text to fit within COLS terminal columns before rendering.",
)
```

**Handler (before render call):**

```python
text_to_render = args.text
if args.fit is not None:
    from justdoit.layout import fit_text
    iso_d = args.iso if args.iso else 0
    text_to_render, actual_cols = fit_text(
        args.text,
        target_cols=args.fit,
        font=font_name,
        gap=args.gap,
        iso_depth=iso_d,
    )
    if text_to_render != args.text:
        print(
            f"Note: text truncated to fit {args.fit} cols "
            f"(rendered {actual_cols} cols)",
            file=sys.stderr,
        )
```

Then use `text_to_render` instead of `args.text` in the `render()` call.

---

### Task 3.5 — Update CLI epilog/help

Add to the `--help` examples section:

```
  %(prog)s "JUST DO IT" --measure
  %(prog)s "JUST DO IT" --target 3840x2160
  %(prog)s "JUST DO IT" --target 3840x2160 --save-svg out.svg
  %(prog)s "JUST DO IT" --fit 80
```

---

### Phase 3 commit

```bash
git add justdoit/cli.py
git commit -m "feat: L05 CLI size flags — --measure, --target, --fit, --svg-font-size

--measure: print (cols × rows) + fit table for all DISPLAYS presets, then exit
--target WxH[@Sx]: compute max font pt for display; auto-size SVG when combined
  with --save-svg; standalone prints sizing info to stderr, render continues
--svg-font-size N: explicit SVG pixel size, overrides --target-derived size
--fit N: truncate text to fit N columns via fit_text(), warn to stderr if truncated

All four flags use layout.py primitives — no arithmetic duplicated in cli.py"
git push
```

---

## Phase 4 — Gallery Profiles

**One session. Target: ~120 lines in `generate_gallery.py` + new dirs.**

### Task 4.1 — Add `GalleryProfile` dataclass

At the top of `scripts/generate_gallery.py`, after imports:

```python
from dataclasses import dataclass
from justdoit.layout import measure

@dataclass
class GalleryProfile:
    """Defines a gallery render tier — font size, README thumbnail width, output dir."""
    name: str
    svg_font_size: int
    readme_img_width: int
    output_dir: Path
    text: str = "JUST DO IT"

PROFILES: dict[str, GalleryProfile] = {
    "standard": GalleryProfile(
        name="standard",
        svg_font_size=14,
        readme_img_width=480,
        output_dir=Path(__file__).parent.parent / "docs" / "gallery",
    ),
    "wide": GalleryProfile(
        name="wide",
        svg_font_size=28,
        readme_img_width=800,
        output_dir=Path(__file__).parent.parent / "docs" / "gallery-wide",
    ),
    "4k": GalleryProfile(
        name="4k",
        svg_font_size=72,
        readme_img_width=1600,
        output_dir=Path(__file__).parent.parent / "docs" / "gallery-4k",
    ),
}
```

---

### Task 4.2 — Add `--profile` flag

```python
parser.add_argument(
    "--profile", default="standard",
    choices=list(PROFILES.keys()) + ["all"],
    help="Gallery render profile: standard (14px), wide (28px), 4k (72px), all (default: standard)",
)
```

---

### Task 4.3 — Refactor `_generate_for_profile(profile: GalleryProfile)`

Extract the current gallery generation loop into a profile-aware function:

```python
def _generate_for_profile(profile: GalleryProfile, text: str) -> None:
    """Generate all gallery SVGs and README for a given profile."""
    profile.output_dir.mkdir(parents=True, exist_ok=True)
    entries = _curated_entries(text)
    for stem, label, rendered in entries:
        path = profile.output_dir / f"{stem}.svg"
        save_svg(rendered, str(path), font_size=profile.svg_font_size)
    _write_readme(profile, entries)
    print(f"[{profile.name}] Generated {len(entries)} entries → {profile.output_dir}")
```

The `_write_readme()` function uses `profile.readme_img_width` instead of
the hardcoded `480`.

---

### Task 4.4 — Wire `--profile all`

```python
profiles_to_run = (
    list(PROFILES.values()) if args.profile == "all"
    else [PROFILES[args.profile]]
)
for profile in profiles_to_run:
    _generate_for_profile(profile, args.text)
```

---

### Task 4.5 — Pre-render validation

Before generating any profile, validate text fits reasonably:

```python
def _validate_text(text: str, font: str = "block", gap: int = 1) -> None:
    cols, rows = measure(text, font=font, gap=gap)
    if cols > 400:
        print(
            f"Warning: '{text}' renders to {cols} columns — SVGs will be very wide.",
            file=sys.stderr,
        )
    if cols == 0:
        raise ValueError(f"Text '{text}' produces empty output with font '{font}'")
```

Call before the profile loop. Not a hard error unless cols == 0.

---

### Task 4.6 — Empirical validation at 72px

After generating the 4k profile, inspect one SVG manually:

```bash
# Open in browser and inspect character alignment
open docs/gallery-4k/S-F00-block-baseline.svg   # macOS/Linux
start docs/gallery-4k/S-F00-block-baseline.svg  # Windows
```

Check:
- [ ] Characters are monospaced and columns align
- [ ] No overlapping chars or unexpected gaps
- [ ] Background fills the full canvas
- [ ] Colors render correctly

If columns drift at 72px: implement `textLength` SVG fix (see design doc §2.3)
and document in `docs/decisions/ADR-007-svg-large-font-metrics.md`.

---

### Phase 4 commit

```bash
git add scripts/generate_gallery.py docs/gallery-wide/ docs/gallery-4k/
git commit -m "feat: L04 gallery profiles — standard/wide/4k render tiers

scripts/generate_gallery.py:
  GalleryProfile dataclass: svg_font_size, readme_img_width, output_dir
  PROFILES dict: standard(14px/480px), wide(28px/800px), 4k(72px/1600px)
  --profile flag: standard | wide | 4k | all
  _generate_for_profile(): profile-aware SVG save + README generation
  _validate_text(): warn if render is unexpectedly wide

docs/gallery-wide/ — new: 28px SVG renders, 800px README thumbnails
docs/gallery-4k/   — new: 72px SVG renders, 1600px README thumbnails

SVG column alignment validated at 72px — see ADR-007 for findings"
git push
```

---

## Phase 5 — Integration & Polish (deferred)

Not required for the core feature. Pick these up in later sessions:

### Task 5.1 — FIGlet font `measure()` validation

FIGlet fonts have variable glyph widths and some use kerning. Validate that
`measure()` is accurate for all bundled FIGlet fonts:

```python
# Add to test_layout.py:
@pytest.mark.parametrize("font", ["big", "slant", "banner", "bubble", "digital", "figlet-block"])
def test_measure_all_figlet_fonts(font):
    from justdoit.core.rasterizer import render
    result = render("HI", font=font, gap=1)
    lines = result.split("\n")
    actual_cols = max(len(l) for l in lines)
    cols, _ = measure("HI", font=font, gap=1)
    assert cols == actual_cols, f"measure() wrong for font '{font}': {cols} != {actual_cols}"
```

If FIGlet kerning causes `measure()` to over-estimate (glyphs overlap in
render), document the known error margin. Don't add special-case code —
document the limitation.

### Task 5.2 — Animation gallery profile awareness

In `scripts/generate_anim_gallery.py`, add optional `target_display` to
SHOWCASE entries so a future `--profile 4k` flag can auto-size animation
terminal dimensions. Low priority — cast files are asciinema-native and
the player handles sizing at playback time.

### Task 5.3 — `textLength` SVG fix (if needed)

If Phase 4 validation reveals column drift at 72px, implement:

```python
# In to_svg(), replace:
elements.append(
    f'<text x="{x}" y="{y}" fill="{fill}" font-size="{font_size}" ...>{safe_ch}</text>'
)

# With:
elements.append(
    f'<text x="{x}" y="{y}" fill="{fill}" font-size="{font_size}" '
    f'textLength="{char_w:.1f}" lengthAdjust="spacing" ...>{safe_ch}</text>'
)
```

Gate behind `to_svg(..., fixed_width: bool = False)` parameter.
Document in ADR-007.

### Task 5.4 — Windows DPI auto-detection (platform-specific)

```python
def detect_windows_dpi() -> float:
    """Attempt to detect current DPI on Windows via ctypes. Returns 96.0 on failure."""
    try:
        import ctypes
        hdc = ctypes.windll.user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
        ctypes.windll.user32.ReleaseDC(0, hdc)
        return float(dpi)
    except Exception:
        return 96.0
```

Add to `layout.py`. Use in `terminal_size()` or expose as `detected_dpi()`.
This is a nice-to-have, not blocking.

---

## Testing Strategy

### What must pass before each phase merges

**Phase 1+2:**
```bash
uv run pytest tests/test_layout.py -v    # all new tests
uv run pytest tests/ -q                  # full suite, no regressions
```

**Phase 3:**
```bash
# Smoke test each new flag
uv run python -m justdoit.cli "JUST DO IT" --measure
uv run python -m justdoit.cli "JUST DO IT" --target 3840x2160
uv run python -m justdoit.cli "JUST DO IT" --target 3840x2160 --save-svg /tmp/test.svg
uv run python -m justdoit.cli "JUST DO IT" --fit 40
uv run pytest tests/ -q
```

**Phase 4:**
```bash
uv run python scripts/generate_gallery.py --profile standard  # must match current output
uv run python scripts/generate_gallery.py --profile wide
uv run python scripts/generate_gallery.py --profile 4k
# manual visual check of 4k SVGs in browser
uv run pytest tests/ -q
```

### What NOT to test

- Pixel-exact SVG rendering — browser differences make this untestable in CI
- DPI auto-detection — platform-specific, test manually on Windows
- Visual column alignment at large sizes — must be eyeballed

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| FIGlet kerning makes `measure()` inaccurate | Medium | Low | Document, don't special-case |
| SVG column drift at 72px | Medium | Medium | Validated in Phase 4; textLength fix in 5.3 if needed |
| `fit_text()` off-by-one at edge cases | Low | Low | Test suite covers suffix width inclusion |
| `max_font_pt()` scan misses non-monotone display configs | Low | Low | Full scan (no early break) handles this |
| Gallery 4k SVGs too large for GitHub (>1MB per file) | Medium | Low | Warn in script; GitHub renders SVGs up to ~10MB |
| Phase 4 `--profile all` slow (3× renders) | Low | Low | Gallery is already slow; document expected time |

---

## Dependencies Between Phases

```
Phase 1+2 ──────────────────→ Phase 3 (CLI)
    │                               │
    └───────────────────────→ Phase 4 (Gallery)
                                    │
                                Phase 5 (Polish)
```

Phase 3 and Phase 4 are **independent of each other** — both depend only on
Phase 1+2. They can be done in either order or in the same session if time allows.

---

## Session Execution Guide

### Running Phase 1+2 (recommended first session)

1. Orient: `git pull`, `uv run pytest tests/ -q`
2. Create `justdoit/layout.py` — implement in order: `measure()`, `RenderTarget`, `DISPLAYS`, `fit_text()`, `terminal_size()`
3. Update `justdoit/output/svg.py` — make `font_size` explicit in `save_svg()`
4. Write `tests/test_layout.py` — implement all tests from Task 1.3
5. Run `uv run pytest tests/ -q` — must be green
6. Manual SVG validation at 72px (Task 1.4)
7. Commit + push

### Running Phase 3 (second session)

1. Orient: `git pull`, `uv run pytest tests/ -q`
2. Add flags to `cli.py` in order: `--measure`, `--target`, `--svg-font-size`, `--fit`
3. Smoke test all four flags
4. Run `uv run pytest tests/ -q`
5. Commit + push

### Running Phase 4 (third session)

1. Orient: `git pull`, `uv run pytest tests/ -q`
2. Add `GalleryProfile` and `PROFILES` to `generate_gallery.py`
3. Refactor `_generate_for_profile()`
4. Add `--profile` flag
5. Generate all three profiles: `uv run python scripts/generate_gallery.py --profile all`
6. Visually validate 4k SVGs in browser — document findings
7. Run `uv run pytest tests/ -q`
8. Commit + push (including generated gallery files)

---

*This plan is the authoritative implementation guide. Update status inline as
phases complete. When all phases are done, archive to `docs/decisions/ADR-008-size-scale-resolution.md`.*
