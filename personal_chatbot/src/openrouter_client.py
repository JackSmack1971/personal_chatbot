"""OpenRouter client placeholder.

Minimal client interface and exceptions to support TDD scaffolding.
Configuration is sourced from environment variables in later phases.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol


class OpenRouterError(Exception):
    """Base error for OpenRouter client failures."""


class OpenRouterTimeout(OpenRouterError):
    """Raised when a request times out."""


class OpenRouterAuthError(OpenRouterError):
    """Raised when authentication fails."""


class Transport(Protocol):  # pragma: no cover - interface
    def post(self, path: str, json: Dict[str, Any], timeout: float) -> Dict[str, Any]:
        ...


@dataclass(frozen=True)
class OpenRouterConfig:
    base_url: str
    api_key_env: str = "OPENROUTER_API_KEY"
    request_timeout_seconds: float = 30.0
    model: Optional[str] = None


class OpenRouterClient:
    """Typed placeholder client exposing a minimal chat API."""

    def __init__(self, config: OpenRouterConfig, transport: Optional[Transport] = None) -> None:
        self._config = config
        self._transport = transport  # Real transport wired later

    def chat_complete(self, messages: list[dict[str, str]], *, model: Optional[str] = None) -> dict:
        """Placeholder for chat completion; raises if no transport is provided."""
        if self._transport is None:
            raise OpenRouterError("Transport not configured")
        payload = {"model": model or self._config.model, "messages": messages}
        return self._transport.post("/chat/completions", json=payload, timeout=self._config.request_timeout_seconds)