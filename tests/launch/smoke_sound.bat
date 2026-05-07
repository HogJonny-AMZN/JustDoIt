@echo off
:: SO01 Sound Engine — manual smoke test launcher
:: Plays TNG, TOS, and ENT transporter sweeps through your speakers.
:: Requires: uv, numpy, sounddevice (uv sync --dev)

cd /d "%~dp0..\.."

echo.
echo  JustDoIt Sound Engine — Smoke Test
echo  ------------------------------------
echo  You should hear three transporter sweeps:
echo    1. TNG  (~1.2s) — warm rising shimmer
echo    2. TOS  (~0.8s) — sharper electrical buzz
echo    3. ENT  (~2.0s) — slow, uncertain, slightly wobbly
echo.
echo  Turn up your speakers before continuing.
echo.
pause

uv run pytest tests/test_sound_smoke.py -v -s --no-header -m manual

echo.
pause
