"""Project setup bootstrap (scaffolding).

Responsibilities (scaffold level):
- Create runtime directories (uploads/, exports/)
- Optionally emit an .env.example template (no secrets)
- Print next steps for developers (tests, running app)

This script performs idempotent filesystem actions only. It does not fetch
dependencies or manage secrets.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

ROOT: Final[Path] = Path(__file__).resolve().parents[1]
UPLOADS_DIR: Final[Path] = ROOT / "uploads"
EXPORTS_DIR: Final[Path] = ROOT / "exports"
ENV_EXAMPLE: Final[Path] = ROOT / ".env.example"


ENV_TEMPLATE: Final[str] = """# personal_chatbot environment template
# Copy to .env and fill values as appropriate. Do NOT commit real secrets.

# Application
APP_ENV=development

# OpenRouter
OPENROUTER_API_KEY=YOUR_API_KEY_HERE

# Supabase
SUPABASE_URL=https://project-ref.supabase.co
SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY

# Optional configuration
LOG_LEVEL=INFO
"""


def ensure_dirs() -> None:
    """Create runtime directories if missing."""
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


def write_env_example() -> None:
    """Create .env.example if not present."""
    if not ENV_EXAMPLE.exists():
        ENV_EXAMPLE.write_text(ENV_TEMPLATE, encoding="utf-8")


def main() -> int:
    print(f"[install] Project root: {ROOT}")
    ensure_dirs()
    write_env_example()
    print(f"[install] Ensured runtime dirs: {UPLOADS_DIR.relative_to(ROOT)}, {EXPORTS_DIR.relative_to(ROOT)}")
    print(f"[install] Ensured {ENV_EXAMPLE.name} (no secrets)")
    print("[install] Next steps:")
    print("  1) python -m venv .venv && .venv/Scripts/activate (Windows) or source .venv/bin/activate (Unix)")
    print("  2) pip install -r personal_chatbot/requirements.txt")
    print("  3) cp personal_chatbot/.env.example personal_chatbot/.env and populate secrets")
    print("  4) python -m pytest -q (once tests are added)")
    print("  5) python -m personal_chatbot.main")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())