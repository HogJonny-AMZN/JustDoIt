# ADR-006: Dependency Approval Rubric

**Date:** 2026-03-29  
**Status:** Accepted  
**Supersedes:** The informal "commonly used" language in ADR-001

---

## Problem

ADR-001 permits "commonly used scientific packages" but does not define what
that means. Without a rubric, any agent or contributor can rationalize adding
any package. This ADR provides an objective scoring gate.

---

## The Rubric

Score a candidate package across five dimensions. **Total must be ≥ 15/25 to
auto-approve.** Below 15 requires explicit approval from Jonny.

### 1. PyPI Download Volume (0–5)

Proxy for ecosystem adoption. Check via `pypistats.org` or `libraries.io`.

| Monthly downloads | Score |
|-------------------|-------|
| > 100M | 5 |
| 10M – 100M | 4 |
| 1M – 10M | 3 |
| 100K – 1M | 2 |
| 10K – 100K | 1 |
| < 10K | 0 |

### 2. Mainstream Scientific / Creative Ecosystem Presence (0–5)

Is it a standard tool in its domain?

| Criteria | Score |
|----------|-------|
| Listed in official Python scientific stack (numpy, scipy, matplotlib, etc.) | 5 |
| Default dependency in major frameworks (PyTorch, TensorFlow, etc.) | 4 |
| Standard in its specific domain (e.g., sounddevice for audio) | 3 |
| Used by several well-known packages but not default anywhere | 2 |
| Niche but referenced in academic literature | 1 |
| Unknown / single-purpose / personal project | 0 |

### 3. Maintenance Health (0–5)

| Criteria | Score |
|----------|-------|
| Actively maintained, releases in last 6 months, responsive to issues | 5 |
| Maintained, releases in last 12 months | 4 |
| Stable, infrequent releases (mature/complete package) | 3 |
| Last release 1–2 years ago, open issues | 2 |
| Last release > 2 years ago | 1 |
| Abandoned / archived | 0 |

### 4. Supply Chain Risk (0–5)

Lower risk = higher score.

| Criteria | Score |
|----------|-------|
| Minimal transitive deps (0–2), well-audited, no known CVEs | 5 |
| Small dep tree (3–5), reputable maintainers | 4 |
| Moderate dep tree (6–10), established organization | 3 |
| Large dep tree (> 10) or less-known maintainers | 2 |
| Known CVEs or security concerns | 1 |
| Obfuscated code, no source available, or suspicious history | 0 |

### 5. Necessity (0–5)

Could this be avoided with reasonable effort?

| Criteria | Score |
|----------|-------|
| Cannot be replicated in pure Python at acceptable quality/performance | 5 |
| Would require 500+ lines of pure Python to approximate | 4 |
| Would require 100–500 lines, with quality trade-offs | 3 |
| Could be done in pure Python with moderate effort | 2 |
| Pure Python version exists and is adequate | 1 |
| Pure Python version is trivial | 0 |

---

## Scoring Examples

### `numpy` — Score: 25/25 ✅ Auto-approved

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Downloads | 5 | > 100M/month |
| Ecosystem | 5 | Foundational scientific Python |
| Maintenance | 5 | Actively maintained by NumFOCUS |
| Supply chain | 5 | Minimal deps, extensively audited |
| Necessity | 5 | Vectorized array ops not practical in pure Python at scale |

### `scipy` — Score: 23/25 ✅ Auto-approved

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Downloads | 5 | > 50M/month |
| Ecosystem | 5 | Core scientific Python |
| Maintenance | 5 | Actively maintained by NumFOCUS |
| Supply chain | 4 | Depends on numpy + Fortran libs |
| Necessity | 4 | Signal processing, ODE solvers not worth hand-rolling |

### `sounddevice` — Score: 16/25 ✅ Auto-approved (barely)

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Downloads | 3 | ~2M/month |
| Ecosystem | 3 | Standard in Python audio domain |
| Maintenance | 4 | Regularly maintained |
| Supply chain | 4 | Minimal deps (PortAudio binding) |
| Necessity | 2 | Could use pyaudio or wave+os, but sounddevice is cleaner |

### `Pillow` — Score: 23/25 ✅ Auto-approved (already in use)

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Downloads | 5 | > 60M/month |
| Ecosystem | 5 | De facto Python imaging standard |
| Maintenance | 5 | Actively maintained |
| Supply chain | 4 | C extensions, some historical CVEs (all patched) |
| Necessity | 4 | TTF rendering not practical without it |

### `hypothetical-cool-lib` — Score: 8/25 ❌ Requires Jonny approval

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Downloads | 1 | ~50K/month |
| Ecosystem | 2 | Used by a few packages |
| Maintenance | 2 | Last release 18 months ago |
| Supply chain | 2 | 15 transitive deps |
| Necessity | 1 | Pure Python version exists |

---

## Process

1. **Score the package** using the rubric above
2. **Document the scores** in the PR or commit message
3. **≥ 15**: add as optional dep, gate with `ImportError` fallback, proceed
4. **< 15**: stop, flag to Jonny with the score breakdown, wait for approval
5. **Any score of 0 in Supply Chain**: automatic escalation regardless of total

---

## Pre-Approved Packages (scored, on file)

| Package | Score | Status |
|---------|-------|--------|
| `numpy` | 25/25 | ✅ Pre-approved |
| `scipy` | 23/25 | ✅ Pre-approved |
| `Pillow` | 23/25 | ✅ Pre-approved (in use) |
| `sounddevice` | 16/25 | ✅ Pre-approved |

All others require scoring + approval gate.
