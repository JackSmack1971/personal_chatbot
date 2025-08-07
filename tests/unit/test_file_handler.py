import os
import pathlib
import pytest

# We rely on the presence of safe join and extension allowlist behaviors.
from personal_chatbot.src import file_handler as fh


def test_safe_join_prevents_path_traversal(tmp_path):
    base = tmp_path
    # Attempt to break out of base using '..'
    with pytest.raises(ValueError):
        fh.safe_join(base, "../evil.txt")

    # Normal join within base should work
    p = fh.safe_join(base, "ok.txt")
    assert str(p).startswith(str(base))
    assert p.parent == base


def test_is_extension_allowed_positive_and_negative_cases(monkeypatch):
    # Assume module exposes ALLOWED_EXTENSIONS and is_extension_allowed
    assert fh.is_extension_allowed("doc.txt") is True
    assert fh.is_extension_allowed("image.png") is True
    assert fh.is_extension_allowed("archive.zip") is False
    assert fh.is_extension_allowed("noext") is False
    assert fh.is_extension_allowed("UPPER.PDF") is True


def test_ensure_runtime_dirs_idempotent(tmp_path, monkeypatch):
    uploads = tmp_path / "uploads"
    exports = tmp_path / "exports"

    # Monkeypatch module-level constants if present
    if hasattr(fh, "UPLOADS_DIR"):
        monkeypatch.setattr(fh, "UPLOADS_DIR", uploads)
    if hasattr(fh, "EXPORTS_DIR"):
        monkeypatch.setattr(fh, "EXPORTS_DIR", exports)

    # First call should create
    fh.ensure_runtime_dirs()
    assert uploads.exists() and uploads.is_dir()
    assert exports.exists() and exports.is_dir()

    # Second call should be idempotent (no exception)
    fh.ensure_runtime_dirs()
    assert uploads.exists() and exports.exists()