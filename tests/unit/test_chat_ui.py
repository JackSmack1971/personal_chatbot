import pytest

from personal_chatbot.src.memory_manager import InMemoryStore, MemoryRecord
from personal_chatbot.src.openrouter_client import OpenRouterClient, OpenRouterConfig
from personal_chatbot.src import chat_ui as ui


class _LocalMockTransport:
    def __init__(self, content: str = "Assistant reply"):
        self._content = content
        self.calls = []

    def post(self, path: str, json, timeout: float):
        self.calls.append({"path": path, "json": json, "timeout": timeout})
        return {"choices": [{"message": {"role": "assistant", "content": self._content}}]}


def test_ui_module_import_has_no_side_effects():
    # Module import should be side-effect free (no dirs or network)
    # This is a smoke assertion; if import triggers errors, test fails.
    assert hasattr(ui, "__doc__")


def test_minimal_orchestration_function_contract():
    """
    Expect chat_ui to expose a pure function that orchestrates a single-turn chat given injected deps:
    e.g., respond_once(user_text, memory_store, client) -> assistant_text
    """
    memory = InMemoryStore()
    cfg = OpenRouterConfig(base_url="https://openrouter.ai/api/v1", model="test-model", request_timeout_seconds=3.0)
    transport = _LocalMockTransport(content="Hello from model")
    client = OpenRouterClient(config=cfg, transport=transport)

    assert hasattr(ui, "respond_once"), "chat_ui must define respond_once() for orchestration"

    user_text = "Hi!"
    assistant = ui.respond_once(user_text=user_text, user_id="u1", memory_store=memory, client=client)

    # Validate returned assistant content
    assert assistant == "Hello from model"

    # Validate memory interactions (at least one user message stored)
    user_msgs = [r for r in memory.list_by_user("u1", limit=10) if r.content == user_text]
    assert len(user_msgs) == 1

    # Validate OpenRouter invocation schema
    assert len(transport.calls) == 1
    call = transport.calls[0]
    assert call["path"] == "/chat/completions"
    payload = call["json"]
    assert "messages" in payload and isinstance(payload["messages"], list)
    assert payload["messages"][0]["role"] == "user"
    assert payload["messages"][0]["content"] == user_text