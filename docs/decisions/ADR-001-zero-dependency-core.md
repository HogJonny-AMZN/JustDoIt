# ADR-001: Dependency Policy

**Date:** 2026-03-23  
**Revised:** 2026-03-29  
**Status:** Revised

## Original Decision (2026-03-23)

Pure Python stdlib only for core. No numpy, no Pillow, no third-party packages.
Optional features gated behind `Pillow` with graceful `ImportError` degradation.

## Revision (2026-03-29)

Policy relaxed by Jonny Galloway. **Commonly used scientific packages are now
permitted** where they produce meaningfully better work — cleaner code, better
performance, or capabilities not practically achievable in pure Python.

### Tier 1 — Core stdlib (always available, no install required)
`math`, `random`, `itertools`, `wave`, `os`, `pathlib`, etc.
Use freely everywhere.

### Tier 2 — Permitted scientific packages (add to `pyproject.toml` as optional deps)
- **`numpy`** — array ops, FFT, signal processing, linear algebra. Permitted.
- **`scipy`** — signal processing, image ops, optimization. Permitted.
- **`sounddevice`** — audio I/O for sound engine (SO01). Permitted.

These go in `[project.optional-dependencies]`, not `[dependencies]`.
Gate with graceful `ImportError` fallback — never hard-require.

### Tier 3 — Permitted feature deps (already established)
- **`Pillow`** — TTF fonts, PNG export. Existing pattern.

### Tier 4 — Requires explicit approval
Anything not in Tiers 1–3. Score it using **ADR-006** (dependency approval
rubric). Score ≥ 15/25 = auto-approved. Score < 15 = flag to Jonny.

## Numpy Refactoring Flag

When `numpy` is first added as a dependency, trigger a review of existing
fill implementations for refactoring potential. The following modules do
significant manual 2D array work that numpy would simplify:

- `justdoit/effects/generative.py` — all simulation fills (noise, cells, RD, slime, attractor, lsystem)
- `justdoit/effects/fill.py` — density_fill, sdf_fill
- `justdoit/effects/shape_fill.py` — neighbor connectivity analysis
- `justdoit/core/glyph.py` — mask generation, SDF computation
- `justdoit/effects/spatial.py` — grid transforms (sine warp, perspective, shear)

Refactoring is optional — do not break working code — but flag the opportunity
and capture it in a `docs/decisions/ADR-005-numpy-refactor.md` after review.

## Rationale for Revision

- The transporter animation (A11) and sound engine (SO01/SO02) genuinely need
  numpy for synthesis quality and animation performance
- Several existing fills would be cleaner and faster with numpy array ops
- Pure-Python constraint produced good algorithms but is now a ceiling, not a feature
- Commonly used packages (numpy, scipy) have minimal supply-chain risk and are
  universally trusted in the scientific Python ecosystem

## What Does NOT Change

- Zero-dependency *install* for the base CLI — optional deps remain optional
- Graceful degradation — if numpy is absent, falls back to pure Python path
- No obscure or single-purpose packages without explicit approval
- PIL-gated tests use `pytest.importorskip("PIL")` pattern — same for numpy
