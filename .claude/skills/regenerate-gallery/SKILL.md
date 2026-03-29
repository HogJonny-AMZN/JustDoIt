# Skill: regenerate-gallery

Regenerate all gallery SVGs and update the gallery README.

## When to use

- After implementing a new fill, font, or spatial effect
- After fixing a visual bug in an existing effect
- When gallery output looks stale vs. current code

## Steps

### 1 — Run the gallery generator

```bash
.venv/bin/python scripts/generate_gallery.py
```

This overwrites all SVGs in `docs/gallery/`. Expect it to take 30–60 seconds.

### 2 — Check for errors

If any effect fails during generation:
- Read the traceback carefully
- Do NOT silently skip the failing effect — fix it or flag it
- Re-run after fixing

### 3 — Spot-check the output

Open a few SVGs and confirm:
- Text is legible
- Fill effects are visible and correct
- No empty/all-space output
- No ANSI escape codes leaking into SVG content

### 4 — Commit

Stage all changed SVGs plus the README:

```bash
git add docs/gallery/
git commit -m "docs: regenerate gallery SVGs"
```

Do not stage unrelated changes in the same commit.

## Notes

- Gallery uses `"Just Do It"` as default text (was `"JDI"` — do not revert)
- SVG output uses `justdoit/output/svg.py`
- Each showcase entry in `generate_gallery.py` has an ID like `S-F01`, `S-C02` etc. — match TECHNIQUES.md
- The gallery README is auto-generated; do not hand-edit it
