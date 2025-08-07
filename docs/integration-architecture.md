# Integration Architecture — Personal Chatbot

Version: 1.0  
Status: Finalized for Implementation

This document details how modules interact internally and with external services (OpenRouter, Supabase). It complements docs/architecture.md and defines concrete integration sequences, payloads, and failure behaviors.

## 1. High-Level Integration Map

```
[Gradio UI (chat_ui)]
   |  user input / file drops / actions
   v
[FileHandler] ----(saved paths, previews)---> [Gradio UI]
   | (local disk writes)                          |
   v                                              v
./uploads/  ./exports/                        [MemoryManager]
                                                 | (CRUD/search/export via SDK)
                                                 v
                                            [Supabase (PostgREST)]
                                                 ^
[OpenRouterClient] <---- messages/context ------/
   |
   | HTTPS (streaming)
   v
[OpenRouter API]
```

Key integration properties:
- UI orchestrates flows; other modules are pure services.
- All outbound network traffic is HTTPS.
- Local file paths are relative; no absolute paths persisted.

## 2. Core Sequences

### 2.1 Send Message with Streaming

1) User presses Send in UI  
2) chat_ui:
- Ensures a conversation exists (MemoryManager.create_conversation if None).
- Persists the user message (MemoryManager.add_message).
- Builds OpenRouter-formatted messages from in-memory state.
- Calls OpenRouterClient.chat_stream(messages, model).

3) OpenRouterClient:
- POST https://openrouter.ai/api/v1/chat/completions
- Headers:
  - Authorization: Bearer {API_KEY}
  - Content-Type: application/json
  - HTTP-Referer: http://localhost
  - X-Title: Personal Assistant
- Body:
```json
{
  "model": "openrouter/horizon-beta",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Prompt text"}
  ],
  "stream": true
}
```
- Yields incremental text tokens to UI.

4) chat_ui:
- Aggregates tokens to update Chatbot display.
- On completion:
  - Persists assistant message (MemoryManager.add_message).
  - If conversation title is "Untitled", auto-title using short_title_from_text().
  - Touches conversation updated_at.

Errors:
- 429/5xx/timeouts → retry (2 attempts) within OpenRouterClient.
- Final failure → UI shows retry prompt; user can re-send.

### 2.2 Drag-and-Drop File Upload

1) User drops files into UI  
2) chat_ui:
- Ensures conversation exists.
- For each file:
  - FileHandler.save_uploaded_file(file_obj, conversation_id)
  - FileHandler.validate_file(path, size)
  - FileHandler.extract_content(path)
  - FileHandler.make_preview(text)
  - MemoryManager.add_file_record(filename, path, type, upload_date, conversation_id)
- Appends a system message with combined previews to UI state for context.
- Optionally persists this system note as a message (v1 may keep it UI-only or persist as "system" role).

Notes:
- Validation rejects unsupported types or files > max size.
- On parse errors, continue processing other files and show per-file warnings.

### 2.3 Search and Conversation Load

1) User types query in search box  
2) chat_ui calls MemoryManager.search_conversations(q, limit=50)  
3) MemoryManager:
- title ilike '%q%'
- OR conversation_ids from messages.content ilike '%q%'
- OR conversation_ids from files.filename ilike '%q%'
- Union, deduplicate, load conversations ORDER BY updated_at DESC LIMIT 50
4) UI displays results; on selection:
- chat_ui calls MemoryManager.get_messages(conversation_id)
- UI state populated; Chatbot re-renders transcript.

### 2.4 Export Conversation

1) User clicks Export  
2) MemoryManager.export_conversation_markdown(conversation_id, out_dir="./exports")  
3) Steps:
- Load conversation + messages
- Derive safe filename: {safe_title}-{YYYYMMDD_HHMMSS}.md
- Create metadata header and transcript
- Append file reference list
- Return saved path to UI

## 3. Error Contracts and Degradation

- OpenRouterClient errors:
  - NetworkError (retries exhausted): UI shows toast and a "Retry" button.
- Supabase errors:
  - DatabaseError (retries exhausted): UI shows "Persistence temporarily unavailable." Users can continue chatting (in-memory). When connectivity returns, messages resume persisting on next actions.
- FileHandler errors:
  - ProcessingError: UI shows per-file warning; no crash.

Redaction:
- No secrets in error messages.
- Logs contain high-level categories only.

## 4. Data Normalization

- Paths:
  - Store relative paths (e.g., uploads/{conversation_id}/{yyyy-mm}/filename.ext)
  - No OS-specific separators in DB; normalize to forward slashes.
- Timestamps:
  - UTC ISO-8601; DB timestamptz defaults to now().

## 5. State Synchronization Rules

- UI State is the short-lived source for rendering; DB is the durable source.
- After successful persistence of messages/files, UI state aligns with latest DB content.
- On load, always re-hydrate UI state from DB to ensure consistency.

## 6. Configuration and Theme Flow

- config.json read at startup; validate_config produces warnings for missing keys.
- UI setting toggles:
  - Theme: apply Gradio light/dark; persisting to config.json is optional in v1.
  - API key visibility: UI mask toggle only; no writeback to file.

## 7. Security Gates in Integration

- FileHandler.safe_filename() before saving
- FileHandler.validate_file() before extraction
- Markdown code fences for previews; render_markdown enabled in Chatbot
- HTTPS enforced; supabase and openrouter URLs validated by scheme

## 8. Performance Integration

- Streaming throttle in UI: buffer tokens and flush on a timer (~50–150ms).
- File parsing:
  - Background threads (2–3 max) to avoid UI stalls.
  - Preview length capped at ~2,000 chars.

## 9. Supabase Table DDL and Indices (Recap)

See setup/create_tables.sql to create:
- conversations
- messages
- files

Recommended indices for responsiveness:
- CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC);
- CREATE INDEX IF NOT EXISTS idx_messages_conversation_id_timestamp ON messages(conversation_id, timestamp DESC);
- CREATE INDEX IF NOT EXISTS idx_files_filename ON files USING GIN (to_tsvector('simple', filename)) OR simple btree for ilike.

Note: Full-text index is optional given personal scale.

## 10. Versioning and Compatibility

- Dependencies pinned in requirements.txt; code references compatible APIs only.
- Minimal adapter layer required to swap:
  - OpenRouterClient implementation
  - MemoryManager persistence backend (e.g., SQLite variant in the future)

## 11. Open Questions and Decisions

- Persist system preview messages?
  - Decision: Optional. v1 may keep them UI-only to reduce DB noise; previews are reproducible by re-parsing.
- Model temperature/max_tokens controls in UI?
  - Decision: Defer; keep UI simple with default behavior; add later if needed.

## 12. Integration Test Hooks

- DummyLLM for streaming simulation in tests.
- In-memory MemoryManager stub for unit tests.
- Temporary directory for FileHandler tests.

## 13. Success Criteria Linkage

- Meets acceptance criteria for streaming chat, file upload, persistence, search, export, and model switching.
- NFR adherence: startup time, responsiveness, and safe error behavior are enforced by throttles/retries/async processing.
