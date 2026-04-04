# ADR-003: Fill registry pattern in rasterizer

**Date:** 2026-03-23  
**Status:** Accepted

## Context

As fill effects multiplied, the rasterizer needed a way to dispatch from a fill name (string) to the correct function without a growing `if/elif` chain.

## Decision

All fill functions are registered in a single dict `_FILL_FNS` in `justdoit/core/rasterizer.py`:

```python
_FILL_FNS: dict = {
    "density":   density_fill,
    "sdf":       sdf_fill,
    "noise":     noise_fill,
    ...
}
```

The `render()` function dispatches via `_FILL_FNS.get(fill)`.

## Rationale

- **Single source of truth** — adding a fill requires exactly one registration point, not scattered conditionals
- **CLI discoverability** — `_FILL_FNS.keys()` can be used to enumerate valid `--fill` values
- **Testability** — the registry can be inspected in tests to verify all fills are reachable
- **Extensibility** — third-party code can register custom fills by importing and mutating `_FILL_FNS`

## Consequences

- Every new fill **must** be added to `_FILL_FNS` — it will be silently ignored otherwise
- Fill keys are part of the public CLI API — choose them carefully, rename requires a deprecation path
- The registry is imported at module load — circular imports from `effects/` back to `core/` are forbidden

## Fill key naming convention

- Short, lowercase, no hyphens: `density`, `noise`, `truchet`, `lsystem`
- Descriptive enough to be guessable from the CLI: `--fill truchet` should be self-explanatory
