"""Application entrypoint (scaffolding).

Bootstraps minimal wiring and ensures runtime directories exist.
Real application wiring will follow tests and architecture in Phase 4.
"""

from __future__ import annotations

from personal_chatbot.src.file_handler import ensure_runtime_dirs
from personal_chatbot.src.utils import get_logger, load_config


def main() -> int:
    logger = get_logger()
    cfg = load_config()
    logger.info("Starting personal_chatbot in environment=%s", cfg.environment)

    # Ensure runtime directories for uploads/exports exist
    ensure_runtime_dirs()

    # Placeholder: real app bootstrap (UI/API) comes later
    logger.info("Bootstrap complete (scaffolding)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())