import pytest
from typing import Any, Dict

from personal_chatbot.src.openrouter_client import (
    OpenRouterClient,
    OpenRouterConfig,
    OpenRouterError,
)


def test_chat_complete_raises_without_transport():
    config = OpenRouterConfig(base_url="https://openrouter.ai/api/v1", model="test-model", request_timeout_seconds=5.0)
    client = OpenRouterClient(config=config, transport=None)

    with pytest.raises(OpenRouterError) as exc:
        client.chat_complete([{"role": "user", "content": "Hello"}])

    assert "Transport not configured" in str(exc.value)


def test_chat_complete_invokes_transport_with_payload_and_timeout(mock_transport):
    config = OpenRouterConfig(base_url="https://openrouter.ai/api/v1", model="test-model", request_timeout_seconds=7.5)
    client = OpenRouterClient(config=config, transport=mock_transport)

    messages = [{"role": "user", "content": "Hi"}]
    result = client.chat_complete(messages)

    # Transport call verification (London School behavior test)
    assert len(mock_transport.calls) == 1
    call = mock_transport.calls[0]
    assert call["path"] == "/chat/completions"
    assert call["timeout"] == pytest.approx(7.5)
    assert call["json"]["model"] == "test-model"
    assert call["json"]["messages"] == messages

    # Basic contract for result structure (minimal placeholder)
    assert isinstance(result, dict)
    assert "choices" in result
    assert isinstance(result["choices"], list)