# IMPLEMENTATION TASK: A_ISO1 — Isometric Depth Breathing Animation

## Context
You are implementing a new animation preset for the JustDoIt ASCII art project.
The project uses uv (at /home/node/.openclaw/npm-global/bin/uv) for all Python operations.

## Goal
Implement `iso_depth_breathe()` in `justdoit/animate/presets.py` — an animation where
isometric extrusion depth oscillates via a sine wave, making block letters appear to
breathe in 3D.

## Function signature

```python
def iso_depth_breathe(
    text_plain: str,
    font: str = "block",
    n_frames: int = 24,
    fill: str = "plasma",
    fill_kwargs: Optional[dict] = None,
    base_depth: int = 4,
    amplitude: int = 3,
    direction: str = "right",
    loop: bool = True,
) -> Iterator[str]:
```

## Algorithm per-frame i (0..n_frames-1)

```python
import math
depth = max(1, base_depth + int(round(amplitude * math.sin(2 * math.pi * i / n_frames))))
rendered = render(text_plain, font=font, fill=fill, fill_kwargs=fill_kwargs or {})
frame = isometric_extrude(rendered, depth=depth, direction=direction)
yield frame
```

## Loop strategy
When loop=True: yield frames 0..n_frames-1 forward, then reversed frames from
n_frames-2 down to 1 (forward-reverse seamless loop, not duplicating endpoints).
Total = 2*n_frames - 2 frames when loop=True.
When loop=False: yield exactly n_frames frames.

## Imports to use inside the function body (lazy imports like other presets)
- `from justdoit.core.rasterizer import render as _render`
- `from justdoit.effects.isometric import isometric_extrude as _isometric_extrude`
- `import math as _math`

## Depth sweep behavior
- base_depth=4, amplitude=3: sweeps depth values from 1 (4-3) to 7 (4+3) and back
- Letters appear to breathe — extrusion grows and shrinks each cycle
- Use max(1, ...) to clamp depth to minimum 1

## Fill
Use whatever fill the caller specifies (default 'plasma'). This textures the front face.
The depth face uses _DEPTH_SHADES from isometric_extrude (already implemented — don't change it).

## Docstring
Include a full docstring explaining:
- What A_ISO1 is (S03 isometric + depth animation cross-breed)
- The sine-sweep depth breathing mechanism
- Each parameter with types
- Returns description

## Tests
Create `tests/test_iso_depth_breathe.py` with at least 25 tests covering:

1. Return type is Iterator (not a list)
2. Frame count: exactly n_frames frames when loop=False
3. Frame count: exactly 2*n_frames-2 frames when loop=True with n_frames > 1
4. Each frame is a non-empty string
5. Each frame is a multi-line string (contains newlines)
6. Frames contain isometric depth characters (at least one of: ▓ ▒ ░ ·) — proving extrusion happened
7. Depth oscillation: with amplitude > 0, the frame at i=0 and frame at i=n_frames//2 differ in depth-char count (sine gives different depths)
8. Works with fill='plasma'
9. Works with fill='flame'
10. Works with fill='density'
11. Works with font='block'
12. Works with font='slim'
13. Works with direction='left'
14. direction='right' (default) produces output containing depth chars on right side
15. Loop=False gives exactly n_frames=8 frames
16. Loop=True gives exactly 2*8-2=14 frames for n_frames=8
17. base_depth parameter is respected (base_depth=1, amplitude=0: all frames have shallow depth)
18. amplitude=0: all frames have same depth-char count (constant depth)
19. fill_kwargs passed through (e.g. fill_kwargs={'t': 0.5} for plasma)
20. n_frames=1, loop=False: yields exactly 1 frame
21. n_frames=2, loop=True: yields exactly 2 frames (2*2-2=2)
22. base_depth=1, amplitude=0: depth is always 1 (minimum depth letters)
23. With default args, output is non-empty
24. Generator is lazy (doesn't fail before iteration)
25. First and last frames of a loop are not identical (loop cuts duplicate endpoints correctly)

## SHOWCASE entry
Add this entry to the SHOWCASE list in `scripts/generate_anim_gallery.py`:

1. Add `iso_depth_breathe` to the existing import line in `_build_showcase()`:
   Find the line starting with:
   `from justdoit.animate.presets import typewriter, ...`
   and append `, iso_depth_breathe` to it.

2. Add this entry dict AFTER the existing X_PLASMA_BLOOM entry (before the closing `]`):

```python
        {
            "id": "A_ISO1",
            "name": "Isometric Depth Breathe",
            "label": "iso-depth-breathe",
            "frames": lambda: list(iso_depth_breathe(text_plain, n_frames=24, fill="plasma", base_depth=4, amplitude=3, loop=True)),
            "fps": 12.0,
            "loop": True,
        },
```

## Existing patterns to follow
- Look at `bloom_pulse()` and `plasma_bloom()` in `justdoit/animate/presets.py` for the
  generator pattern (imports inside function body, forward+reverse loop strategy).
- Look at `plasma_wave()` for the simpler forward-only loop pattern.

## DO NOT
- Do not modify any existing functions
- Do not change `isometric_extrude()` in `justdoit/effects/isometric.py`
- Do not use pip, python3, or .venv/bin
- All Python runs via: `/home/node/.openclaw/npm-global/bin/uv run`

## Verification step
After implementing, run:
  /home/node/.openclaw/npm-global/bin/uv run pytest tests/test_iso_depth_breathe.py -v
All tests must pass. Fix any failures before considering the task done.
