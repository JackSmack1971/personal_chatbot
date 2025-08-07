# Data Structures — Personal Chatbot

Version: 1.0  
Status: Implementation-Ready

This document defines canonical in-memory and storage structures used across modules.

## 1. Configuration

```json
{
  "openrouter_api_key": "string",
  "supabase_url": "string",
  "supabase_key": "string",
  "default_model": "string",
  "max_file_size": 50,
  "theme": "dark"
}
```

Validation:
- openrouter_api_key: required non-empty string
- supabase_url, supabase_key: required for persistence (UI must warn if missing)
- default_model: one of ["openrouter/horizon-beta","anthropic/claude-3.5-sonnet","openai/gpt-4"]
- max_file_size: number (MB), default 50
- theme: "dark" | "light"

## 2. Conversation

In-memory (Python dict):
```python
Conversation = {
  "id": "uuid",
  "title": "str",
  "created_at": "iso8601",
  "updated_at": "iso8601"
}
```

DB schema: see setup/create_tables.sql

## 3. Message

In-memory:
```python
Message = {
  "id": "uuid",
  "conversation_id": "uuid",
  "role": "user" | "assistant" | "system",
  "content": "str",
  "file_paths": ["str", ...] | None,  # relative local paths
  "timestamp": "iso8601"
}
```

DB messages.file_paths stored as jsonb array.

## 4. File Record

In-memory:
```python
FileRecord = {
  "id": "uuid",
  "filename": "str",
  "file_path": "str",      # relative local path (uploads/..)
  "file_type": "str",      # extension or MIME
  "upload_date": "iso8601"
}
```

Note: Linking files to messages is implicit via Message.file_paths. For cross-conversation search by file name, use files table.

## 5. UI State

```python
UIState = {
  "conversation_id": "uuid | None",
  "messages": [ {"role": "user|assistant|system", "content": "str"} ],
  "model": "str",
  "streaming": "bool",
  "api_key_masked": "bool",
  "recent_conversations": [Conversation, ...]
}
```

## 6. Upload Handling

Accepted extensions:
```text
.txt .md .py .js .json .yaml .yml .csv
.pdf .docx .xlsx
.html .css .sql .xml
.png .jpg .jpeg .gif .webp
```

Validation result:
```python
ValidationResult = {
  "ok": bool,
  "errors": [str, ...],
  "warnings": [str, ...]
}
```

Saved upload return:
```python
SavedUpload = {
  "filename": "str",
  "path": "str",      # relative to project root (uploads/..)
  "ext": "str",       # lowercased extension with leading dot
  "size": int         # bytes
}
```

Extraction output:
```python
ExtractedContent = {
  "text": "str",      # may be placeholder for images
  "meta": {
    "chars": int,
    "lines": int,
    "ext": "str",
    "pages": int | None,        # for pdf
    "sheets": int | None,       # for xlsx
    "dimensions": [w, h] | None # for images
  }
}
```

Preview:
```python
Preview = "str"  # first N chars of text plus ellipsis
```

## 7. Search Results

```python
SearchResult = {
  "conversations": [Conversation, ...],  # sorted by updated_at desc
}
```

Search query structure:
```python
SearchQuery = {
  "q": "str",            # free text
  "limit": 50            # default; applied to conversations result
}
```

## 8. Export Format (Markdown)

File name:
```
./exports/{safe_title}-{yyyyMMdd_HHmmss}.md
```

Front matter-like header:
```markdown
---
title: "{conversation.title}"
created_at: "{conversation.created_at}"
updated_at: "{conversation.updated_at}"
model: "{selected_model}"
---
```

Transcript block:
```markdown
## Transcript

- [YYYY-MM-DD HH:MM] user:
  ```
  message text
  ```
- [YYYY-MM-DD HH:MM] assistant:
  ```
  assistant text
  ```
```

Files section:
```markdown
## Referenced Files
- {filename} — {relative_path}
```

## 9. Error Structures

```python
AppError = {
  "type": "ValidationError | NetworkError | DatabaseError | ProcessingError",
  "message": "str",
  "code": "str | None",
  "context": { "operation": "str", ... }  # non-sensitive
}
```

Retry policy configuration:
```python
RetryPolicy = {
  "attempts": int,
  "delays": [0.5, 1.0, 2.0]  # seconds
}
```

## 10. OpenRouter Message Format

Request messages:
```python
OpenRouterMessage = {
  "role": "system|user|assistant",
  "content": "str"
}
```

Streaming yields incremental `content` tokens (delta) aggregated into final assistant message.

## 11. Paths

- Upload base directory: `./uploads/{conversation_id}/{yyyy-mm}/`
- Export directory: `./exports/`

All stored paths should be relative (not absolute) to facilitate portability and backup.
