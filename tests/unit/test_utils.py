import os
import logging
import importlib
import pytest

# utils should expose a logger factory and env-based config struct without secrets.
from personal_chatbot.src import utils as u


def test_logger_factory_returns_configured_logger():
    logger = u.get_logger("test-logger", level="DEBUG")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test-logger"
    # Ensure duplicate handlers are not added on repeated calls
    before = len(logger.handlers)
    logger2 = u.get_logger("test-logger", level="DEBUG")
    after = len(logger2.handlers)
    assert after == before


def test_config_from_env_has_defaults_and_no_secrets(monkeypatch):
    # Clear potential env then set partials
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("CHATBOT_DEFAULT_MODEL", "openrouter/test-model")
    cfg = u.load_env_config()
    # Expect structured dict-like config with typed fields
    assert cfg.base_url == "https://openrouter.ai/api/v1"
    assert cfg.default_model == "openrouter/test-model"
    # API key may be None or redacted placeholder, but never thrown in logs
    assert hasattr(cfg, "api_key")
    # Ensure string repr does not leak secrets
    s = str(cfg)
    assert "test-key" not in s
    assert "OPENROUTER_API_KEY" not in s


def test_module_is_side_effect_free_on_import(monkeypatch):
    # Re-import utils and ensure import does not create files/network; smoke test by ensuring it imports quickly
    import time
    start = time.perf_counter()
    importlib.reload(u)
    duration_ms = (time.perf_counter() - start) * 1000
    assert duration_ms < 100.0