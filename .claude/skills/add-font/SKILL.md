# Skill: add-font

You are adding a new font to JustDoIt. Fonts come in three flavours — pick the right path.

---

## Path A — Builtin font (hand-crafted glyph arrays)

Use when: you want a custom pixel font with no dependencies.

### A1 — Create the module

`justdoit/fonts/builtin/myfont.py`:

```python
"""
Package: justdoit.fonts.builtin.myfont
Brief description of the font style.
"""
import logging as _logging

_MODULE_NAME = "justdoit.fonts.builtin.myfont"
__updated__ = "YYYY-MM-DD 00:00:00"
__version__ = "0.1.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)

# -------------------------------------------------------------------------
# Height must be consistent across ALL glyphs — verify before registering
MYFONT: dict[str, list[str]] = {
    "A": [
        " ## ",
        "#  #",
        "####",
        "#  #",
        "#  #",
    ],
    # ... all glyphs same height
    " ": ["    ", "    ", "    ", "    ", "    "],
}
```

**Critical:** every glyph must have identical row counts. Mismatched heights corrupt output silently.

### A2 — Register in fonts/__init__.py

```python
from justdoit.fonts.builtin.myfont import MYFONT
FONTS["myfont"] = MYFONT
```

### A3 — Write tests

```python
def test_myfont_all_glyphs_same_height():
    from justdoit.fonts.builtin.myfont import MYFONT
    heights = {k: len(v) for k, v in MYFONT.items()}
    assert len(set(heights.values())) == 1, f"Height mismatch: {heights}"

def test_myfont_render():
    from justdoit import render
    out = render("HELLO", font="myfont")
    assert len(out) > 0
```

---

## Path B — FIGlet font (.flf)

Use when: you want to add a community FIGlet font.

### B1 — Drop the .flf file

Place it in `justdoit/fonts/figlet_fonts/myfont.flf`.

### B2 — Register in fonts/__init__.py

```python
FIGLET_FONTS = ["banner", "big", "block", "bubble", "digital", "slant", "myfont"]
```

(Follow the existing pattern — the parser is already written in `figlet.py`.)

### B3 — Test

```python
def test_figlet_myfont():
    from justdoit import render
    out = render("HI", font="myfont")
    assert len(out) > 0
```

---

## Path C — TTF/OTF system font

Use when: you want to use a system font via Pillow.

TTF fonts auto-register via `justdoit/fonts/ttf.py` — no code changes needed.

Test with:
```bash
uv run python justdoit.py "Hello" --ttf DejaVuSans
```

TTF tests require Pillow and use `pytest.importorskip("PIL")` — never hard-fail.

---

## All paths: final checklist

- [ ] Tests pass: `uv run pytest tests/ -q`
- [ ] `python justdoit.py --list-fonts` shows the new font
- [ ] `render("HELLO", font="myfont")` produces correct output
- [ ] Commit: `feat: add <fontname> font (Path A/B/C)`
