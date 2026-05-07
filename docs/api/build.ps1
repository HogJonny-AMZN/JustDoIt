# Sphinx API Documentation Build Script
# Run this after installing dependencies: uv sync --dev

Write-Host "JustDoIt - Sphinx API Documentation Builder" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "conf.py")) {
    Write-Host "Error: Must run from docs/api/ directory" -ForegroundColor Red
    Write-Host "Usage: cd docs/api && ./build.ps1" -ForegroundColor Yellow
    exit 1
}

# Step 1: Check if Sphinx is installed
Write-Host "[1/4] Checking Sphinx installation..." -ForegroundColor Yellow
$sphinxCheck = & uv run python -c "import sphinx; print(sphinx.__version__)" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Sphinx not installed" -ForegroundColor Red
    Write-Host "Run: uv sync --dev" -ForegroundColor Yellow
    exit 1
}
Write-Host "      ✓ Sphinx $sphinxCheck installed" -ForegroundColor Green

# Step 2: Generate module stubs
Write-Host "[2/4] Generating module stubs with sphinx-apidoc..." -ForegroundColor Yellow
& uv run sphinx-apidoc -o . ../../justdoit --separate --force
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: sphinx-apidoc failed" -ForegroundColor Red
    exit 1
}
Write-Host "      ✓ Module stubs generated" -ForegroundColor Green

# Step 3: Build HTML documentation
Write-Host "[3/4] Building HTML documentation..." -ForegroundColor Yellow
& uv run sphinx-build -b html . _build/html
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: sphinx-build failed" -ForegroundColor Red
    exit 1
}
Write-Host "      ✓ HTML documentation built" -ForegroundColor Green

# Step 4: Open in browser
Write-Host "[4/4] Opening documentation in browser..." -ForegroundColor Yellow
$htmlPath = Resolve-Path "_build/html/index.html"
Start-Process $htmlPath
Write-Host "      ✓ Opened: $htmlPath" -ForegroundColor Green

Write-Host ""
Write-Host "Documentation successfully built!" -ForegroundColor Cyan
Write-Host "Output: docs/api/_build/html/" -ForegroundColor White
