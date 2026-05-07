# Sphinx Setup - Next Steps

## ✅ Completed (Siloed Setup)

All files created in isolated `docs/api/` directory - **no conflicts with running agent**:

1. **Configuration:**
   - `conf.py` - Sphinx config with autodoc, napoleon, viewcode extensions
   - `index.rst` - API documentation structure
   - `.gitignore` - Ignore build outputs

2. **Build Tools:**
   - `Makefile` - Unix/Linux build commands
   - `make.bat` - Windows build commands
   - `build.ps1` - PowerShell automated build script

3. **Directories:**
   - `_static/` - Custom CSS/JS (empty)
   - `_templates/` - Custom Jinja2 templates (empty)

4. **Documentation:**
   - `README.md` - Setup instructions and troubleshooting

## ⏳ Pending (Requires File Modifications)

**These operations need to wait until the other agent finishes:**

### 1. Update `pyproject.toml`

Add to `[dependency-groups] dev = [...]`:
```toml
"sphinx>=7.0",
"sphinx-rtd-theme>=2.0",
"sphinx-autodoc-typehints>=1.25",
```

### 2. Update root `.gitignore`

Add:
```gitignore
# Sphinx build output
docs/api/_build/
docs/api/_autosummary/
```

### 3. Update `CONTRIBUTING.md`

Add section about building API docs (see `README.md` for content).

---

## Quick Start (When Ready)

```powershell
# 1. Install Sphinx dependencies (after updating pyproject.toml)
uv sync --dev

# 2. Build documentation (automatic)
cd docs/api
./build.ps1

# OR manual steps:
cd docs/api
uv run sphinx-apidoc -o . ../../justdoit --separate --force
uv run sphinx-build -b html . _build/html
start _build/html/index.html
```

---

## Manual Build Commands

```bash
# Generate module stubs
cd docs/api
uv run sphinx-apidoc -o . ../../justdoit --separate --force

# Build HTML
uv run sphinx-build -b html . _build/html

# Clean build
rm -rf _build

# Rebuild from scratch
rm -rf _build && uv run sphinx-build -b html . _build/html

# Using Makefile (after Sphinx installed)
make html       # Build HTML
make clean      # Clean build directory
make help       # Show all targets
```

---

## Verification Checklist

After running the build:

- [ ] HTML documentation opens in browser
- [ ] All modules appear in navigation
- [ ] Docstrings render correctly
- [ ] Type hints display properly
- [ ] [source] links work
- [ ] Search functionality works
- [ ] No import errors (mocked: PIL, numpy, sounddevice)

---

## Estimated Time to Complete

- Update pyproject.toml: 1 minute
- Install dependencies (`uv sync --dev`): 1-2 minutes
- Run build script (`./build.ps1`): 2-3 minutes
- Update .gitignore and CONTRIBUTING.md: 2-3 minutes

**Total: ~5-10 minutes**
