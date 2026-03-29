# ADR-001: Zero-dependency core

**Date:** 2026-03-23  
**Status:** Accepted

## Context

JustDoIt started as a single-file script. When refactored into a package, a choice had to be made about dependencies.

## Decision

The core rendering pipeline (`justdoit/core/`, `justdoit/effects/`, `justdoit/fonts/builtin/`) must work with **pure Python stdlib only**. No numpy, no Pillow, no third-party packages.

Optional features (TTF fonts, PNG export) are gated behind `Pillow` with graceful `ImportError` degradation.

## Rationale

- **Portability** — `pip install justdoit` should work anywhere Python runs, including restricted environments
- **Trust** — users are more willing to run a tool with no supply-chain surface
- **Simplicity** — pure Python is easier to read, audit, and contribute to
- **Constraint breeds creativity** — every fill effect being implemented in pure Python has produced more interesting algorithms than reaching for scipy would

## Consequences

- All fill algorithms must be hand-rolled (no scipy signal processing, no sklearn, no PIL in the fill path)
- Numpy would simplify a lot of the 2D array work — we consciously accept that cost
- PIL-gated tests use `pytest.importorskip("PIL")` — never hard-fail
