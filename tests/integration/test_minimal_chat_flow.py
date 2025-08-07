import pytest

from personal_chatbot.src.memory_manager import InMemoryStore
from personal_chatbot.src.openrouter_client import OpenRouterClient, OpenRouterConfig


class _TransportRecorder:
    def __init__(self, content: str = "ok"):
        self.calls = []
        self._content = content

    def post(self, path: str, json, timeout: float):
        self.calls.append({"path": path, "json": json, "timeout": timeout})
        return {"choices": [{"message": {"role": "assistant", "content": self._content}}]}


def _respond_once(user_text: str, user_id: str, memory: InMemoryStore, client: OpenRouterClient) -> str:
    # Lightweight orchestration mirror to reflect expected contract without depending on UI yet.
    memory.create(
        # IDs are simplified for test purposes
        __import__("personal_chatbot.src.memory_manager", fromlist=["MemoryRecord"]).MemoryRecord(
            id=f"msg-{len(memory.list_by_user(user_id))+1}",
            user_id=user_id,
            content=user_text,
            metadata={},
        )
    )
    payload = [{"role": "user", "content": user_text}]
    result = client.chat_complete(payload)
    assistant = result["choices"][0]["message"]["content"]
    memory.create(
        __import__("personal_chatbot.src.memory_manager", fromlist=["MemoryRecord"]).MemoryRecord(
            id=f"msg-{len(memory.list_by_user(user_id))+1}",
            user_id=user_id,
            content=assistant,
            metadata={"role": "assistant"},
        )
    )
    return assistant


def test_minimal_flow_no_network_and_persists_messages(tmp_path):
    memory = InMemoryStore()
    cfg = OpenRouterConfig(base_url="https://openrouter.ai/api/v1", model="flow-model", request_timeout_seconds=2.0)
    transport = _TransportRecorder(content="assistant reply")
    client = OpenRouterClient(config=cfg, transport=transport)

    out = _respond_once("hello there", "u1", memory, client)
    assert out == "assistant reply"

    # Validate memory has both user and assistant messages
    msgs = memory.list_by_user("u1", limit=10)
    roles = []
    for m in msgs:
        if m.metadata.get("role") == "assistant":
            roles.append("assistant")
        else:
            roles.append("user")
    assert "user" in roles and "assistant" in roles

    # Validate single call, correct path and model present (optional model may be None in payload if not set)
    assert len(transport.calls) == 1
    call = transport.calls[0]
    assert call["path"] == "/chat/completions"
    assert isinstance(call["json"]["messages"], list)