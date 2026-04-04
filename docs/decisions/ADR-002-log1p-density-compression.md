# ADR-002: log1p compression for generative fill density mapping

**Date:** 2026-03-23  
**Status:** Accepted

## Context

Generative fill algorithms (noise, cellular automata, reaction-diffusion, strange attractor, L-system, etc.) produce raw accumulation counts or float values over the glyph mask. Mapping these linearly to density characters produces flat, uninteresting output — most characters end up in the same density bucket.

## Decision

All generative fills use **`log1p` compression** before mapping to density characters:

```python
import math
compressed = math.log1p(raw_value) / math.log1p(max_value + 1e-9)
char_index = int(compressed * (len(DENSITY_CHARS) - 1))
```

## Rationale

- **Perceptual balance** — human vision is logarithmic; log compression matches how we perceive density gradients
- **Dynamic range** — raw simulation outputs often have a heavy-tailed distribution (a few cells accumulate most of the value); log compression spreads them across the density scale
- **Visual consistency** — all fills feel like they belong to the same aesthetic family

## Consequences

- All new generative fills must use this pattern for visual consistency
- Do not use linear mapping — output will look flat and wrong
- The compression constant (`log1p(max + 1e-9)`) uses a small epsilon to avoid `log(0)`
- Exterior cells (`mask < 0.5`) always map to `' '` regardless of compression
