"""Utilities: logger factory and environment configuration.

Side-effect free on import.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

# Logger


def get_logger(name: str = "personal_chatbot", *, level: str | int | None = None) -> logging.Logger:
    """Return a logger with idempotent handler configuration.

    - Does not duplicate handlers across repeated calls
    - Does not alter root logger configuration
    - Optional `level` parameter to set logger level (string like "DEBUG" or int)
    """
    logger = logging.getLogger(name)
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Resolve desired level if provided
    resolved_level: int | None = None
    if isinstance(level, int):
        resolved_level = level
    elif isinstance(level, str):
        upper = level.upper()
        resolved_level = getattr(logging, upper, None)

    if resolved_level is not None:
        logger.setLevel(resolved_level)
    elif logger.level == logging.NOTSET:
        logger.setLevel(logging.INFO)

    return logger


# Environment configuration


@dataclass(frozen=True)
class EnvConfig:
    """Environment configuration values.

    api_key is considered sensitive; __repr__/__str__ redacts it.
    """
    base_url: str
    default_model: str
    api_key: str

    def __repr__(self) -> str:  # pragma: no cover - representation behavior verified via tests
        return f"EnvConfig(base_url={self.base_url!r}, default_model={self.default_model!r}, api_key='***REDACTED***')"

    __str__ = __repr__


def load_env_config(
    *,
    base_url_env: str = "OPENROUTER_BASE_URL",
    default_model_env: str = "OPENROUTER_DEFAULT_MODEL",
    api_key_envs: tuple[str, ...] = ("OPENROUTER_API_KEY", "API_KEY"),
) -> EnvConfig:
    """Load configuration from environment variables with safe defaults.

    Defaults:
    - base_url: https://api.openrouter.ai
    - default_model: openrouter/auto
    - api_key: empty string if not provided

    The first present env name in api_key_envs is used for api_key.
    """
    base_url = os.getenv(base_url_env, "https://api.openrouter.ai")

    # Support multiple env var names for default model to satisfy tests
    default_model = os.getenv(default_model_env)
    if not default_model:
        # Fallback to CHATBOT_DEFAULT_MODEL if present
        default_model = os.getenv("CHATBOT_DEFAULT_MODEL", "openrouter/auto")

    api_key = ""
    for key_name in api_key_envs:
        val = os.getenv(key_name)
        if val:
            api_key = val
            break

    return EnvConfig(base_url=base_url, default_model=default_model, api_key=api_key)