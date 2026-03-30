# Animation Gallery — Implementation Plan

**Status:** Ready to build  
**Created:** 2026-03-30  
**Author:** NumberOne + Jonny Galloway  
**Goal:** Go from zero animated artifacts to a fully populated `docs/anim_gallery/` in one focused build session.

---

## Current State

| What exists | What doesn't |
|-------------|-------------|
| `justdoit/animate/presets.py` — 5 animations: `typewriter`, `scanline`, `glitch`, `pulse`, `dissolve` | `justdoit/output/cast.py` |
| `justdoit/output/svg.py`, `image.py`, `html.py` | `justdoit/output/apng.py` |
| `scripts/generate_gallery.py` (static) | `scripts/generate_anim_gallery.py` |
| `docs/animation_gallery.md` (full spec) | `docs/anim_gallery/` (directory + contents) |
| `docs/anim_gallery/README.md` (auto-generated) | `.claude/skills/regenerate-anim-gallery/SKILL.md` |

The animation pipeline is **design-complete**. Implementation is 0%.

---

## The Plan

### Phase 1 — `cast.py` (Priority 0)
**Pure stdlib. No deps. ~60 lines. Unblocks everything.**

File: `justdoit/output/cast.py`

What it does: converts a list of ANSI frame strings → asciinema v2 `.cast` file.

Format:
```
{"version": 2, "width": 80, "height": 24, "title": "JustDoIt"}
[0.000, "o", "\033[2J\033[H<frame0>"]
[0.042, "o", "\033[2J\033[H<frame1>"]
...
```

Key functions:
- `to_cast(frames, fps, title, cols, rows) -> str`
- `save_cast(frames, path, fps, title, cols, rows) -> None`
- Auto-detect `cols`/`rows` from frame content if not specified

Tests: `tests/test_output_cast.py`
- Header is valid JSON
- Timestamps increase monotonically at `1/fps` intervals
- Frame content is preserved (roundtrip)
- Auto-dimensions work

**Deliverable:** `.cast` files for all 5 existing animations, no new effects needed.

---

### Phase 2 — `apng.py` (Priority 1)
**Pillow-gated. ~80 lines. Unlocks GitHub-embeddable animated previews.**

File: `justdoit/output/apng.py`

What it does: converts ANSI frame strings → PIL Images → APNG file.

Key functions:
- `frame_to_image(frame, font_size, bg_color, line_height) -> PIL.Image`
- `to_apng(frames, fps, font_size, bg_color, loop) -> bytes`
- `save_apng(frames, path, fps, font_size, bg_color, loop) -> None`

PIL stitch pattern:
```python
images[0].save(path, save_all=True, append_images=images[1:],
               loop=loop, duration=int(1000/fps), format="PNG")
```

Loop policy (resolved):
- `loop=0` → infinite (ambient effects: `glitch`, `pulse`)
- `loop=1` → play-once, hold last frame (narrative: `typewriter`, `scanline`, `dissolve`)

Tests: `tests/test_output_apng.py` (all gated with `pytest.importorskip("PIL")`)
- Output starts with PNG magic bytes
- Correct frame count
- Correct dimensions

**Deliverable:** `.apng` files for all 5 existing animations.

---

### Phase 3 — `generate_anim_gallery.py` (Priority 2)
**Wires Phase 1+2 into a gallery generator. Populates `docs/anim_gallery/`.**

File: `scripts/generate_anim_gallery.py`

Declarative SHOWCASE list — each entry defines effect, fps, loop behavior:

```python
SHOWCASE = [
    {
        "id": "A01", "name": "typewriter",
        "variants": [{
            "label": "typewriter",
            "frames": lambda: list(typewriter("JUST DO IT", font="block")),
            "fps": 12,
            "loop": False,   # play-once — it's a reveal
        }],
    },
    {
        "id": "A02", "name": "scanline",
        "variants": [{
            "label": "scanline",
            "frames": lambda: list(scanline("JUST DO IT")),
            "fps": 12,
            "loop": False,
        }],
    },
    {
        "id": "A03", "name": "glitch",
        "variants": [{
            "label": "glitch",
            "frames": lambda: list(glitch("JUST DO IT")),
            "fps": 24,
            "loop": True,    # ambient — loops naturally
        }],
    },
    {
        "id": "A04", "name": "pulse",
        "variants": [{
            "label": "pulse",
            "frames": lambda: list(pulse("JUST DO IT")),
            "fps": 24,
            "loop": True,    # ambient
        }],
    },
    {
        "id": "A05", "name": "dissolve",
        "variants": [{
            "label": "dissolve",
            "frames": lambda: list(dissolve("JUST DO IT")),
            "fps": 24,
            "loop": False,   # narrative — play-once
        }],
    },
    # A11 transporter variants added when A11 is implemented
]
```

For each variant: save `.cast` + `.apng` to `docs/anim_gallery/`, append to README.

Auto-generated `docs/anim_gallery/README.md` structure:
```markdown
## A03 — Glitch
| Variant | Preview | Cast |
|---------|---------|------|
| glitch | ![glitch](A03-glitch.apng) | [▶ terminal](A03-glitch.cast) |
```

**Deliverable:** populated `docs/anim_gallery/` — 5 effects × 2 formats = 10 files + README.

---

### Phase 4 — Skill + CI hook (Priority 3)
**Makes regeneration a one-command operation.**

File: `.claude/skills/regenerate-anim-gallery/SKILL.md`

```markdown
# Skill: regenerate-anim-gallery

1. uv sync --dev
2. uv run python scripts/generate_anim_gallery.py
3. Spot-check: confirm 2-3 APNGs animate correctly
4. git add docs/anim_gallery/
5. git commit -m "docs: regenerate animation gallery"
6. git push
```

Also: add `generate_anim_gallery.py` call to the daily research-session Step 6b
so the gallery stays current as new animation effects are added.

**Deliverable:** one-command gallery regeneration, daily agent keeps it current.

---

## Milestone: A11 Transporter (Phase 5 — after Phase 1-4)

Once the pipeline exists, A11 slots in cleanly:

```python
{
    "id": "A11", "name": "transporter",
    "variants": [
        {"label": "transporter-tng", "frames": lambda: list(transporter("ENERGIZE", era="tng")), "fps": 24, "loop": False},
        {"label": "transporter-tos", "frames": lambda: list(transporter("ENERGIZE", era="tos")), "fps": 30, "loop": False},
        {"label": "transporter-ent", "frames": lambda: list(transporter("ENERGIZE", era="ent")), "fps": 18, "loop": False},
    ],
},
```

The pipeline waits for the effect. The effect doesn't have to wait for the pipeline.

---

## Build Order Summary

```
Phase 1: cast.py          → .cast files for 5 existing animations  (1 session, ~60 lines)
Phase 2: apng.py          → .apng files for 5 existing animations  (1 session, ~80 lines)
Phase 3: generate_anim_gallery.py → docs/anim_gallery/ populated   (1 session, ~100 lines)
Phase 4: skill + CI hook  → daily regeneration automated           (30 min)
─────────────────────────────────────────────────────────────────────────────────────────
Total: ~3-4 focused sessions → animation gallery goes live

Phase 5: A11 transporter  → flagship gallery showcase              (2-3 sessions)
Phase 6: N12 particle vol → endgame                                (multiple sessions)
```

---

## Notes

- Phases 1-3 use **only existing animations** — no new effects required
- Phase 1 (cast.py) is the highest-leverage single task in the codebase right now
- The static gallery took ~2 sessions to build; animation gallery should be faster (spec is complete)
- Test phrase for transporter: `"ENERGIZE"` — obviously

---

*"Engage."*
