# Integration Interfaces — Personal Chatbot

Version: 1.0  
Status: Implementation-Ready

This document defines the integration contracts between modules and with external services (OpenRouter, Supabase), aligned with the pseudocode and data structures.

## 1. Module Interfaces

### 1.1 OpenRouterClient (src/openrouter_client.py)

Responsibilities:
- Perform chat completions with streaming and non-streaming modes.
- Handle retries for transient errors.
- Abstract provider specifics behind a simple interface.

Interface:
```python
class OpenRouterClient:
    def __init__(
        self,
        api_key: str,
        default_model: str = "openrouter/horizon-beta",
        retry: int = 2,
        backoff: tuple[float, ...] = (0.5, 1.0),
        timeout: int = 60
    ): ...

    def chat_stream(
        self,
        messages: list[OpenRouterMessage],
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None
    ) -> typing.Iterator[str]: ...
    """
    Inputs: OpenRouter-style messages, optional model override.
    Output: Iterator yielding incremental text tokens (already decoded to str).
    Errors: Raises NetworkError on final failure; internal retries applied for 429/5xx.
    """

    def chat_once(
        self,
        messages: list[OpenRouterMessage],
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None
    ) -> str: ...
```

Notes:
- Headers include Authorization: Bearer <api_key>, HTTP-Referer: "http://localhost", X-Title: "Personal Assistant".
- Endpoint: POST https://openrouter.ai/api/v1/chat/completions with {stream: true} for streaming.

### 1.2 MemoryManager (src/memory_manager.py)

Responsibilities:
- Encapsulate Supabase DB operations for conversations, messages, files.
- Provide search utilities and export.

Interface:
```python
class MemoryManager:
    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        retry: int = 3,
        backoff: tuple[float, ...] = (0.5, 1.0, 2.0)
    ): ...

    # Conversations
    def create_conversation(self, title: str = "Untitled") -> dict: ...
    def update_conversation_title(self, conversation_id: str, title: str) -> None: ...
    def touch_conversation(self, conversation_id: str) -> None: ...
    def get_recent_conversations(self, limit: int = 50) -> list[dict]: ...

    # Messages
    def add_message(
        self,
        conversation_id: str,
        role: str,             # "user" | "assistant" | "system"
        content: str,
        file_paths: list[str] | None,
        timestamp: str
    ) -> dict: ...
    def get_messages(self, conversation_id: str) -> list[dict]: ...

    # Files
    def add_file_record(
        self,
        filename: str,
        file_path: str,
        file_type: str | None,
        upload_date: str,
        conversation_id: str | None = None
    ) -> dict: ...

    # Search
    def search_conversations(self, query: str, limit: int = 50) -> list[dict]: ...

    # Export
    def export_conversation_markdown(
        self,
        conversation_id: str,
        out_dir: str = "./exports"
    ) -> str: ...
```

Data types:
- Uses structures from docs/data-structures.md.
- All timestamps are ISO-8601 UTC strings.

### 1.3 FileHandler (src/file_handler.py)

Responsibilities:
- Validate, store, and extract content from uploaded files.
- Produce previews and manage upload directories.

Interface:
```python
class FileHandler:
    def __init__(
        self,
        base_upload_dir: str,
        max_mb: int,
        allowed_types: list[str],
        preview_chars: int = 2000
    ): ...

    def conversation_upload_dir(self, conversation_id: str) -> str: ...

    def validate_file(self, filepath: str, size_bytes: int) -> ValidationResult: ...

    def save_uploaded_file(
        self,
        file_obj,                 # gradio file object
        conversation_id: str
    ) -> SavedUpload: ...

    def extract_content(self, path: str) -> tuple[str, dict]: ...
    def make_preview(self, text: str, limit: int | None = None) -> str: ...
    def cleanup_temp(self, older_than_days: int = 7) -> int: ...
```

### 1.4 Chat UI (src/chat_ui.py)

Responsibilities:
- Compose Gradio Blocks; bind UI to FileHandler, MemoryManager, and OpenRouterClient.
- Wire streaming into Chatbot component.

Entrypoint:
```python
def create_app(
    memory: MemoryManager,
    files: FileHandler,
    llm: OpenRouterClient,
    cfg: dict
) -> gr.Blocks: ...
```

---

## 2. External Service Contracts

### 2.1 OpenRouter

Endpoint:
- POST https://openrouter.ai/api/v1/chat/completions

Headers:
- Authorization: Bearer {api_key}
- Content-Type: application/json
- HTTP-Referer: http://localhost
- X-Title: Personal Assistant

Request Body (streaming):
```json
{
  "model": "openrouter/horizon-beta",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello"}
  ],
  "stream": true
}
```

Streaming Response:
- Server-sent events or chunked JSON with deltas; client aggregates `content` delta into final assistant text.
- On error HTTP 429/5xx: retry with backoff (bounded attempts).

Non-Streaming:
- "stream": false; parse choices[0].message.content.

Models (UI dropdown):
- "openrouter/horizon-beta" (default)
- "anthropic/claude-3.5-sonnet"
- "openai/gpt-4"

### 2.2 Supabase (PostgREST/Client SDK)

Tables:
- conversations(id, title, created_at, updated_at)
- messages(id, conversation_id, role, content, file_paths, timestamp)
- files(id, filename, file_path, file_type, upload_date)

Operations:
- Insert/select/update via Supabase Python client; use RPC if necessary (not required for v1).
- Search:
  - conversations.title ilike
  - messages.content ilike, grouped by conversation_id
  - files.filename ilike, grouped by conversation_id
  - Union conversation_ids; fetch conversations sorted by updated_at desc.

Auth:
- Use anon key; intended for personal project.
- Store credentials in config.json and/or environment variables.

Retry Policy:
- Attempts: 3
- Delays: 0.5s, 1.0s, 2.0s
- Failure: raise DatabaseError with redacted details.

---

## 3. Error and Retry Semantics

### 3.1 Error Classes
```python
class AppError(Exception): ...
class ValidationError(AppError): ...
class NetworkError(AppError): ...
class DatabaseError(AppError): ...
class ProcessingError(AppError): ...
```

### 3.2 Retryable Conditions
- OpenRouter: HTTP 429, 5xx, timeouts
- Supabase: network errors, 5xx from PostgREST
- File parsing: not retried automatically (deterministic)

### 3.3 Backoff
- Exponential backoff sequence per module config.
- Jitter optional (not required for v1).

---

## 4. Security and Privacy Boundaries

- Secrets only in config.json or environment; never logged.
- Error messages redact API keys and sensitive content.
- File validation occurs before disk writes where possible; otherwise delete invalid saves.
- No execution of uploaded content; only parsing with safe libraries.

---

## 5. UI Contract Details

- Chatbot displays Markdown; code fences for previews use ```preview or language-tag for syntax.
- File upload accepts multiple; drag-and-drop integrated into main area.
- Theme toggle impacts Gradio theme (dark/light) stored in cfg (persistence optional in v1).
- Export action calls MemoryManager.export_conversation_markdown and shows toast with path.

---

## 6. Configuration Contract

- config.json keys (see data-structures.md).
- Missing critical keys produce UI warnings and limit functionality:
  - Missing openrouter_api_key: chat disabled; settings prompts user.
  - Missing Supabase creds: persistence disabled; in-memory only until provided.

---

## 7. Testing and Mocking Interfaces

- OpenRouterClient can be replaced with a stub:
```python
class DummyLLM:
    def chat_stream(self, messages, model=None, **kw):
        for ch in "This is a test.":
            yield ch
```

- MemoryManager can be swapped with an in-memory fake for unit tests.
- FileHandler can point to a temp directory with limited parsers enabled.

---

## 8. Versioning and Compatibility

- Requirements pinned in requirements.txt; compatible with Python 3.10+.
- OpenRouter and Supabase APIs are stable; breaking changes will be recorded in decisionLog.md if encountered.
