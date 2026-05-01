"""
Tests for justdoit.sound — gated on numpy and sounddevice availability.
"""
import pytest


def test_sound_available_is_bool():
    """SOUND_AVAILABLE must be a bool regardless of whether deps are installed."""
    from justdoit.sound import SOUND_AVAILABLE
    assert isinstance(SOUND_AVAILABLE, bool)


def test_sound_import_does_not_crash_without_deps(monkeypatch):
    """Importing justdoit.sound must never raise even if numpy/sounddevice absent."""
    import sys
    # Remove cached module so the import re-runs
    for key in list(sys.modules):
        if key.startswith("justdoit.sound"):
            del sys.modules[key]
    # Patch numpy import to fail
    real_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

    def fake_import(name, *args, **kwargs):
        if name in ("numpy", "sounddevice"):
            raise ImportError(f"Fake missing: {name}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)
    from justdoit import sound  # noqa: F401  — must not raise
    assert sound.SOUND_AVAILABLE is False
