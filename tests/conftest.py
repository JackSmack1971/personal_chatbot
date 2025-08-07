import os
import time
import types
from typing import Any, Dict, Protocol, List, Optional
import pytest


class DummyTransport(Protocol):
    def post(self, path: str, json: Dict[str, Any], timeout: float) -> Dict[str, Any]: ...


class _MockTransport:
    def __init__(self, response: Dict[str, Any] | None = None, raise_exc: Exception | None = None):
        self.calls: List[Dict[str, Any]] = []
        self._response = response or {"choices": [{"message": {"role": "assistant", "content": "Hello"}}]}
        self._raise = raise_exc

    def post(self, path: str, json: Dict[str, Any], timeout: float) -> Dict[str, Any]:
        self.calls.append({"path": path, "json": json, "timeout": timeout})
        if self._raise:
            raise self._raise
        return self._response


@pytest.fixture
def mock_transport() -> _MockTransport:
    return _MockTransport()


@pytest.fixture(autouse=True)
def no_side_effect_imports(monkeypatch):
    # Ensure no modules trigger network or FS at import; we can monkeypatch env/dirs if needed later
    # Placeholder to keep extensibility; currently does nothing.
    yield


@pytest.fixture
def env_config(monkeypatch, tmp_path):
    # Provide minimal environment variables without secrets
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("CHATBOT_DEFAULT_MODEL", "openrouter/test-model")
    return {
        "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY"),
        "OPENROUTER_BASE_URL": os.getenv("OPENROUTER_BASE_URL"),
        "CHATBOT_DEFAULT_MODEL": os.getenv("CHATBOT_DEFAULT_MODEL"),
    }


@pytest.fixture
def in_memory_store():
    from personal_chatbot.src.memory_manager import InMemoryStore
    return InMemoryStore()


@pytest.fixture
def perf_timer():
    class Timer:
        def __enter__(self):
            self.start = time.perf_counter()
            return self

        def __exit__(self, *exc):
            self.end = time.perf_counter()
            self.duration = (self.end - self.start) * 1000.0  # ms

    return Timer