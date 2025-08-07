"""Secure file handling utilities.

Responsibilities:
- Define runtime directories for uploads and exports
- Provide a traversal-safe join helper
- Provide an extension allowlist check
- Ensure runtime directories exist (idempotent)

Security notes:
- safe_join prevents escaping the provided base directory by resolving
  absolute paths and verifying the final candidate remains within base.
- is_extension_allowed performs a case-insensitive exact match on suffix.

This module is intentionally side-effect free on import.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Sequence

# Module-level constants expected by tests
UPLOADS_DIR = "uploads"
EXPORTS_DIR = "exports"

# Backward-compatible defaults for internal use if needed
DEFAULT_UPLOADS_DIR = Path("personal_chatbot") / UPLOADS_DIR
DEFAULT_EXPORTS_DIR = Path("personal_chatbot") / EXPORTS_DIR

# Common default allowlist used by tests/utilities
ALLOWED_EXTENSIONS: tuple[str, ...] = (".txt", ".md", ".pdf", ".json", ".png", ".jpg", ".jpeg")


def ensure_runtime_dirs(
    base_dir: Path | str | None = None,
    *,
    uploads_dir_name: str | Path = UPLOADS_DIR,
    exports_dir_name: str | Path = EXPORTS_DIR,
) -> tuple[Path, Path]:
    """Create runtime directories (idempotent) respecting module constants.

    Behavior:
    - If base_dir is None, use module-level UPLOADS_DIR and EXPORTS_DIR as fully-resolved
      paths (supports monkeypatching to tmp Paths in tests).
    - If base_dir is provided, create subdirs under that base.
    Returns (uploads_path, exports_path).
    """
    if base_dir is None:
        # Use the current values of module-level constants which tests may monkeypatch
        uploads_path = Path(UPLOADS_DIR)
        exports_path = Path(EXPORTS_DIR)
    else:
        base = Path(base_dir)
        uploads_path = base / str(uploads_dir_name)
        exports_path = base / str(exports_dir_name)
    uploads_path.mkdir(parents=True, exist_ok=True)
    exports_path.mkdir(parents=True, exist_ok=True)
    return uploads_path, exports_path


def is_extension_allowed(
    filename: str,
    *,
    allowlist: Iterable[str] | Sequence[str] = ALLOWED_EXTENSIONS,
) -> bool:
    """Check if the file extension is in the allowlist (case-insensitive).

    - Files without an extension are rejected.
    - Leading dots are handled via Path.suffix.
    """
    ext = Path(filename).suffix
    if not ext:
        return False
    ext = ext.lower()
    normalized = {e if e.startswith(".") else f".{e}" for e in (s.lower() for s in allowlist)}
    return ext in normalized


def safe_join(base: Path | str, *parts: str) -> Path:
    """Join path parts to base, preventing traversal outside base.

    Rules:
    - Any absolute part is treated as a normal component (not allowed to escape)
    - After resolution, the candidate must be within base
    - Raises ValueError on traversal attempts
    """
    base_path = Path(base).resolve()
    # Normalize parts: prevent absolute components from discarding the base
    cleaned_parts: list[str] = []
    for p in parts:
        # Strip leading separators to avoid absolute resolution
        cleaned_parts.append(p.lstrip("/\\"))
    candidate = (base_path.joinpath(*cleaned_parts)).resolve()

    # Allow candidate == base (e.g., no parts)
    if candidate == base_path:
        return candidate

    # Ensure candidate remains under base
    base_str = str(base_path)
    cand_str = str(candidate)
    if not cand_str.startswith(base_str + os.sep):
        raise ValueError("Path traversal detected")

    return candidate