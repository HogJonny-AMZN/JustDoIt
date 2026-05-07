# Changelog

All notable changes to JustDoIt will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- CLI integration test suite (51 tests covering validation, file output, effects)
- Input validation for text length (1000 char limit), TTF paths, save paths
- VS Code workspace settings for unified Python tooling (Ruff linter/formatter)
- CONTRIBUTING.md with development guidelines
- CHANGELOG.md (this file)
- Ruff configuration with import sorting (isort rules)
- `pytest` markers configuration (slow tests)

### Fixed
- Windows subprocess encoding issues in CLI integration tests (UTF-8 configuration)
- Unused imports auto-fixed across codebase (12 imports)
- Import ordering standardized via Ruff isort rules (63 files)
- Markdown linting issues in documentation files
- Flake8/mypy IDE configuration errors (migrated to Ruff)

### Changed
- Bloom effect documentation in `layout.py` (removed outdated TODOs)
- Python linting/formatting consolidated to Ruff (disabled flake8, mypy, isort extensions)
- Logging levels improved for better granularity (info/warning/error separation)

### Documentation
- Clarified numpy dependency status (optional, with fallback)
- Updated README.md with clearer dependency documentation
- Enhanced `.github/python-instructions.md` with logging patterns

---

## [0.1.0] - 2026-04-30

Initial public release.

### Core Features
- Zero-dependency ASCII art rendering engine
- Builtin fonts: `block` (7-row), `slim` (3-row)
- FIGlet font support with 6 bundled fonts (banner, big, block, bubble, digital, slant)
- TTF/OTF font rasterization via Pillow (optional)
- ANSI color support with rainbow mode

### Fill Effects
- Density fill (`@#S%?*+;:,.`)
- SDF-based outline and glow
- Noise fills (Perlin, cellular)
- Fractal fills (Mandelbrot, Julia, IFS)
- Generative fills (reaction-diffusion, slime mold, strange attractors, Turing patterns)
- Isometric 3D extrusion
- Shape-based fills
- Plasma and flame effects
- Voronoi patterns
- Wave distortion

### Animation
- Typewriter effect
- Scanline/glitch effects
- Pulse and bloom animations
- Dissolve transitions
- Star Trek transporter effect
- Living color and fill animations
- Plasma and flame animations
- Output formats: APNG, asciinema `.cast`

### Color & Gradients
- 16 color palette (ANSI)
- RGB true color support
- Linear gradients
- Trek-era color palettes (TOS, TNG, DS9)
- Tone curve adjustments

### Output Formats
- Terminal (ANSI-colored text)
- SVG with configurable font size and display targets
- PNG (via Pillow)
- APNG (animated PNG)
- HTML (styled text)
- asciinema `.cast` (terminal playback)

### CLI
- `--font`, `--color`, `--fill`, `--animate` flags
- `--iso` for 3D extrusion
- `--gradient` for color gradients
- `--warp` for sine wave distortion
- `--save-svg`, `--save-png`, `--save-html`, `--save-cast`, `--save-apng`
- `--measure` for display fit analysis
- `--target` for display-specific sizing
- `--fit` for auto-truncation to terminal width
- `--list-fonts`, `--list-colors` for discovery

### Testing
- 1105+ unit tests across 50+ test modules
- PIL-gated tests with graceful skipping
- Test coverage for all fill effects, animations, and formats

### Documentation
- Comprehensive gallery system (static, wide, 4K, fonts, animations)
- VISION.md — project direction and roadmap
- TECHNIQUES.md — full technique registry with novelty tracking
- SIZE_SCALE_RESOLUTION.md — size/scale/resolution architecture
- Animation gallery design docs
- Sound design specification
- Architecture decision records (ADRs)

### Infrastructure
- `uv` for fast dependency management
- `pytest` test framework
- `ruff` for linting and formatting
- GitHub Actions CI (planned)
- `pyproject.toml` build configuration

---

## Version History

- **0.1.0** (2026-04-30) — Initial release
- **Unreleased** — Current development

---

[Unreleased]: https://github.com/HogJonny-AMZN/JustDoIt/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/HogJonny-AMZN/JustDoIt/releases/tag/v0.1.0
