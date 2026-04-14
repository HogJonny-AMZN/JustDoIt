# JustDoIt Daily Research Session — 2026-04-12

You are NumberOne, AI co-owner of the JustDoIt project. Run a complete daily research/build session.

## Environment
- Project root: /home/node/.openclaw/workspace/projects/JustDoIt
- Always use: export PATH="/home/node/.openclaw/npm-global/bin:$PATH"
- Always use `uv run` for Python (never pip, python3 directly, or .venv)
- Working branch: patent-review/C12-bloom-glow (confirm with git status)
- Current test count: 746 passing

## Step 0 — Orient First
```bash
cd /home/node/.openclaw/workspace/projects/JustDoIt
git status
git pull --rebase origin patent-review/C12-bloom-glow 2>/dev/null || git pull --rebase origin main 2>/dev/null || echo "already up to date"
```

## Step 0b — Mode Decision

Priority queue as of last session (2026-04-11):
1. **A_N09a** — Turing Morphogenesis animation (novelty 5, `idea`)
2. A11 — Transporter Materialize (novelty 5, multi-session)
3. G04 — SDF Font Generator (novelty 5)
4. **A_ISO1** — Isometric depth animation (novelty 3, `idea`, Ready to implement, 15/20)
5. A08d — Plasma-modulated flame (novelty 5)

**A_N09a is Mode A (Novel Animation Technique).** It is the #1 priority. Implement it.

## Mode A — A_N09a: Turing Morphogenesis Animation

### What to build
An animation preset called `turing_morphogenesis()` in `justdoit/animate/presets.py` that:
1. First checks `turing_fill` signature in `justdoit/effects/generative.py`
2. Calls turing_fill at increasing step counts: [50, 100, 200, 400, 700, 1000, 1500, 2000, 3000]
   - Each step count = one or more frames (you can repeat key steps for pacing)
   - The animation shows letterforms GROWING a biological coat pattern from noise → settled spots/stripes
   - This is Turing's 1952 morphogenesis theory playing out inside letterforms
3. If `turing_fill` doesn't accept a `steps` param directly:
   - Check the function signature
   - Either add a `steps` kwarg (backward-compatible, default=existing value) OR
   - Use the existing step counts inside each preset variant to find a range

### Checking turing_fill signature
```bash
grep -n "def turing_fill" justdoit/effects/generative.py
grep -n -A 20 "def turing_fill" justdoit/effects/generative.py
```

### Implementation approach
```python
def turing_morphogenesis(
    text_plain: str,
    font: str = "block",
    preset: str = "spots",
    loop: bool = True,
) -> Iterator[str]:
    """Animate Turing pattern formation: early noise → settled coat pattern.
    
    Shows the morphogenesis process from random initial conditions to
    Turing's activator-inhibitor steady state. Each frame advances the
    simulation by more steps, showing the emergence of biological patterns.
    Turing 1952 'The Chemical Basis of Morphogenesis' playing out inside text.
    """
    # Step counts that show the emergence arc:
    # early = random noise, mid = proto-patterns, late = settled spots/stripes
    step_sequence = [30, 60, 100, 150, 200, 300, 400, 600, 800, 1200, 1800, 2500]
    
    frames = []
    for steps in step_sequence:
        frame = render(text_plain, font=font, fill="turing", 
                       fill_kwargs={"preset": preset, "steps": steps})
        frames.append(frame)
    
    # loop: forward then reverse for seamless animation
    if loop:
        all_frames = frames + frames[-2:0:-1]
    else:
        all_frames = frames
    
    for frame in all_frames:
        yield frame
```

If turing_fill doesn't support a `steps` parameter via fill_kwargs, add it:
```python
def turing_fill(mask, preset="spots", steps=None, seed=None):
    # steps overrides the preset's default step count if provided
```

### Tests to write (minimum)
Create `tests/test_turing_morphogenesis.py`:
- Frame count matches expected (with loop: len(step_sequence)*2 - 2)
- Each frame is a non-empty string
- Each frame contains ANSI codes (colored)
- Frame 0 (early steps) is visually different from last frame (settled pattern)
  - Simple check: frame chars differ from last frame chars
- Works with font="block" and font="slim"
- Works with all preset variants: "spots", "stripes", "maze", "labyrinth"

### Gallery entries
1. Static SVG: render at steps=2000 (settled pattern) → `docs/gallery/2026-04-12-A_N09a.svg`
2. Animation gallery entry in `scripts/generate_anim_gallery.py`:
   - Add `("turing_morphogenesis", "JUST DO IT", {})` or equivalent to SHOWCASE list
   - The APNG/cast files should be: `A_N09a-turing-morphogenesis-spots.{cast,apng}`

### Step by step execution order:
1. `git status` — confirm clean
2. Read `justdoit/effects/generative.py` turing_fill section
3. Read `justdoit/animate/presets.py` to see existing preset patterns (esp. plasma_wave, flame_flicker)
4. Read `scripts/generate_anim_gallery.py` to see SHOWCASE format
5. Add `steps` param to `turing_fill` if not present (backward-compatible)
6. Implement `turing_morphogenesis()` in presets.py
7. Run tests: `uv run pytest tests/ -q --tb=short` — must pass
8. Write new tests in `tests/test_turing_morphogenesis.py`
9. Run all tests again: `uv run pytest tests/ -q --tb=short`
10. Generate static gallery SVG for 2026-04-12-A_N09a
11. Update `docs/gallery/README.md` — prepend new row to Daily Techniques table
12. Update `docs/research/TECHNIQUES.md` — mark A_N09a as `done`
13. Update `docs/research/RESEARCH_LOG.md` — append session entry
14. Update `docs/research/ATTRIBUTE_MODEL.md` — update priority order
15. Run `uv run python scripts/generate_anim_gallery.py` to generate animation files
16. `git add -A && git commit -m "feat: A_N09a Turing Morphogenesis animation — ..."`
17. `git push`

## Gallery README format (mandatory)
In `docs/gallery/README.md`, under `## Daily Techniques`, prepend this row:
```html
<tr>
<td align="center"><img src="2026-04-12-A_N09a.svg" width="480"><br><sub><b>2026-04-12 · A_N09a</b></sub></td>
</tr>
```
Also update "Last updated" line at bottom with today's date and new count.

## Research Log Entry Template
```markdown
## Session 2026-04-12 (Mode A — Novel Animation Technique)

**Research focus:** Turing morphogenesis animation — animating the pattern formation process from the FitzHugh-Nagumo activator-inhibitor model already implemented in N09
**New techniques found:** A_N09a (animation of existing N09 turing_fill at increasing step counts)
**Sources:** Turing A.M. (1952) "The Chemical Basis of Morphogenesis" Philos. Trans. R. Soc. Lond. B 237:37–72 (original theory); FitzHugh-Nagumo model (already implemented as N09/turing_fill)
**Key insight:** [your observation about what the animation reveals]
**Priority queue update:** [what changed]
```

## Commit message template
```
feat: A_N09a Turing Morphogenesis animation — FHN activator-inhibitor pattern formation

Animate the Turing morphogenesis process: early random noise crystallizes into
biological spot/stripe patterns as the FitzHugh-Nagumo simulation advances.
Each frame steps further into the simulation, showing pattern emergence in real time.
Turing 1952 playing out inside ASCII letterforms.
```

## After implementation, output full report:
- Mode chosen and why
- What was implemented (files changed, functions added)
- Test count before and after
- Visual validation verdict
- Files created (SVG, animations)
- Commit hash
- Any issues or patent flags
