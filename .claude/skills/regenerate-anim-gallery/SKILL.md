# Skill: regenerate-anim-gallery

Regenerates all animation gallery artifacts in `docs/anim_gallery/`.
Run this whenever a new animation preset is added or an existing one changes.

## Steps

1. **Sync environment**
   ```bash
   uv sync --dev
   ```

2. **Run the generator**
   ```bash
   uv run python scripts/generate_anim_gallery.py
   ```

3. **Spot-check** 2-3 APNGs in a browser, and play a .cast file:
   ```bash
   asciinema play docs/anim_gallery/A03-glitch.cast
   ```

4. **Commit**
   ```bash
   git add docs/anim_gallery/
   git commit -m "docs: regenerate animation gallery"
   git push
   ```

## Loop policy

| Effect     | loop       | Reason           |
|------------|------------|------------------|
| typewriter | play-once  | reveal narrative |
| scanline   | play-once  | reveal narrative |
| glitch     | infinite   | ambient effect   |
| pulse      | infinite   | ambient effect   |
| dissolve   | play-once  | exit narrative   |

In `to_apng()`: `loop=0` = infinite, `loop=1` = play-once.

## Adding a new animation

1. Implement preset in `justdoit/animate/presets.py`
2. Add entry to `SHOWCASE` in `scripts/generate_anim_gallery.py`
3. Re-run this skill

See `docs/ANIMATION_GALLERY_PLAN.md` for the full pipeline design.
