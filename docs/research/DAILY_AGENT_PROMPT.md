# Daily Agent Prompt — JustDoIt Research & Build Session

This file is the standing instruction set for the daily noon agent run.
The agent reads this, then executes the protocol below.

---

## Python Environment

**CRITICAL — read before touching any Python:**

This project uses `uv` + a managed `.venv`. Do NOT use `pip`, `pip3`, or `python -m pip`.

```bash
# The venv lives at:
/home/hogjonny/.openclaw/workspace/projects/JustDoIt/.venv

# Activate (optional — uv run handles it automatically):
source /home/hogjonny/.openclaw/workspace/projects/JustDoIt/.venv/bin/activate

# Run tests (correct):
cd /home/hogjonny/.openclaw/workspace/projects/JustDoIt
.venv/bin/pytest tests/ -q

# Run a script with venv Python:
.venv/bin/python scripts/demo.py

# Add a dependency (dev):
uv add --dev <package>

# NEVER do this:
# pip install ...       ← wrong, pip may not exist
# python -m pip ...     ← wrong
# python3 -m pytest ... ← wrong (uses system Python, not venv)
```

The venv has: `pytest`, `Pillow`, and the `justdoit` package installed in editable mode.
System Python (`python3`) does NOT have these — always use `.venv/bin/python` or `uv run`.

---

## Protocol

### Step 0: Pull latest

```bash
cd /home/hogjonny/.openclaw/workspace/projects/JustDoIt
git pull --rebase
```

### Step 1: Research (timebox: ~10 min equivalent)

Search the web for new ASCII art techniques, demoscene rendering tricks,
generative art approaches, and terminal graphics innovations.

Search terms to rotate through (pick 2-3 per session):

- "ascii art rendering techniques novel"
- "demoscene text effect algorithms"
- "terminal graphics python"
- "ascii art generative algorithm"
- "ansi art techniques"
- "figlet alternative python"
- "ascii animation terminal python"
- "procedural text art"
- "signed distance field ascii"
- "reaction diffusion ascii terminal"
- specific technique names from TECHNIQUES.md

### Step 2: Update TECHNIQUES.md

Read `/home/hogjonny/.openclaw/workspace/projects/JustDoIt/docs/research/TECHNIQUES.md`.

For each finding:

- If it's already listed: update the entry if new info warrants it
- If it's genuinely new: add it to the appropriate category with proper ID, novelty score, and `idea` status
- Never duplicate. Merge variants of the same technique.

### Step 3: Log the session

Append a session entry to `RESEARCH_LOG.md`:

```markdown
## Session YYYY-MM-DD

**Research focus:** [what you searched]
**New techniques found:** [count]
**Sources:** [URLs or references]
**Key insight:** [1-2 sentences on the most interesting thing found]
**Priority queue update:** [any reordering rationale]
```

### Step 4: Pick today's technique

From TECHNIQUES.md, select the highest-priority `idea` status technique that:

- Has not been implemented yet
- Is achievable in a focused session
- Preferably has novelty score 4 or 5

Bias toward novelty. If two techniques are similar priority, pick the weirder one.

Update the technique status to `in-progress` in TECHNIQUES.md.

### Step 5: Implement

In `/home/hogjonny/.openclaw/workspace/projects/JustDoIt/`:

1. Create or update the appropriate module (e.g. `justdoit/effects/`, `justdoit/fonts/`, `justdoit/core/`)
2. Wire it into the pipeline and CLI where it makes sense
3. Write tests in `tests/` — at minimum:
   - Output is non-empty
   - Output is deterministic (where applicable)
   - Output dimensions are correct
   - Edge cases (empty string, single char, long string)
4. Run the tests:

   ```bash
   cd /home/hogjonny/.openclaw/workspace/projects/JustDoIt
   .venv/bin/pytest tests/ -q
   # Or target just the new test file:
   .venv/bin/pytest tests/test_<your_module>.py -v
   ```

   Iterate until all pass. Do NOT use `python3 -m pytest` or `pip install`.
5. Update TECHNIQUES.md status to `done`

### Step 6: Generate showcase output

Run the new technique and save 3 text outputs to:
`docs/research/output/YYYY-MM-DD-<technique-id>-[1|2|3].txt`

Also save 1 SVG to the gallery for the most visually representative sample:
`docs/gallery/YYYY-MM-DD-<technique-id>.svg`

```python
from justdoit.output.svg import save_svg
from justdoit.core.rasterizer import render
# ... apply your new effect ...
save_svg(rendered, "docs/gallery/YYYY-MM-DD-<technique-id>.svg")
```

Then rebuild the gallery index:

```bash
.venv/bin/python scripts/generate_gallery.py --index-only
```

### Step 7: Commit and push

```bash
cd /home/hogjonny/.openclaw/workspace/projects/JustDoIt
git add -A
git commit -m "Daily bite YYYY-MM-DD: <technique-id> — <technique-name>

<1-2 line description of what was implemented>"
git push
```

### Step 8: Report

Return a summary:

- What was researched
- What technique was implemented
- Test results
- One representative output sample (inline)
- What's next in the queue

---

## Exhaustion Protocol

If after thorough research you genuinely cannot find a new technique or approach
that hasn't been implemented or logged — do not implement a duplicate.

Instead:

1. Write a `STUCK.md` note in `docs/research/` explaining what you searched, what you found, and why nothing is new
2. Flag this to Jonny with the message: "I've exhausted my current research surface — time to think bigger."
3. Do NOT implement something just to fill the day. Quality over output.
