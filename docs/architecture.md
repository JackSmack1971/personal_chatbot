# Architecture — Personal Chatbot with Persistent Memory and File Upload

Version: 1.0
Status: Approved for Implementation

This document defines the system architecture, component boundaries, data flow, and technology selections for the MVP.

> Non-functional deployment hardening constraints (cross-references):
> - Digest Pinning Policy: docs/deployment/hardening/digest-pinning.md
> - Runtime Ownership (non-root, writable mounts): docs/deployment/hardening/runtime-ownership.md
> - Least-Privilege Healthcheck: docs/deployment/hardening/healthcheck-lp.md
> - CI Vulnerability Gates + POAM exceptions: docs/deployment/hardening/ci-vuln-gates-poam.md and .security/poam.yaml
> - Dockerfile Capabilities Baseline (cap_drop ALL): docs/deployment/hardening/dockerfile-caps.md
> - Consolidated ADR: memory-bank/decisionLog.md

## 1. Architectural Overview

Local-first Python application with:
- UI: Gradio Blocks (web UI served locally)
- AI: OpenRouter API (default model: openrouter/horizon-beta) with streaming
- Persistence: Supabase (Postgres) for conversations, messages, files
- Files: Local storage under ./uploads and ./exports

Key principles:
- Simple, modular code under 500 LOC per module
- Async/non-blocking UX for streaming and file parsing
- Clear error handling with retries and user-friendly messages
- No secrets in code; local config.json for user-managed keys

## 2. Component Diagram

```
+------------------+          +---------------------+         +----------------------+
|   Gradio Blocks  |          |  OpenRouterClient   |         |    MemoryManager     |
|  (src/chat_ui)   |          | (src/openrouter...) |         | (src/memory_manager) |
+---------+--------+          +----------+----------+         +----------+-----------+
          |                              |                               |
          | user input / uploads         | REST: chat completions        | PostgREST via Supabase SDK
          | model select, search         | SSE/chunks (streaming)        | CRUD conversations/messages/files
          v                              v                               v
+------------------+          +---------------------+         +----------------------+
|   FileHandler    |          |   OpenRouter API    |         |     Supabase DB      |
| (src/file_hand.) |          |  https://openrouter |         |  (conversations,     |
+------------------+          +---------------------+         |   messages, files)   |
       |   ^                                                     +----------------------+
       |   | local disk
       v   |
./uploads/, ./exports/
```

## 3. Data Flow

### 3.1 Chat Flow
1. User types a message → chat_ui sends to stream handler.
2. chat_ui ensures a conversation exists; persists user message via MemoryManager.
3. chat_ui calls OpenRouterClient.chat_stream(messages, model).
4. Streamed tokens update Chatbot UI incrementally.
5. On completion, assistant message is persisted; smart title may update conversation title.

### 3.2 File Upload Flow
1. User drags/drops file(s) or uses button → chat_ui receives file objects.
2. FileHandler saves file(s) to ./uploads/{conversation_id}/{yyyy-mm}/ with safe unique names.
3. FileHandler extracts content/preview (text, metadata).
4. MemoryManager records file metadata; chat_ui injects preview snippet as a system note/message.
5. Subsequent prompts include file context (summarized preview) in conversation messages.

### 3.3 Search and Load
1. User enters a query in sidebar search.
2. MemoryManager.search_conversations performs ilike queries on title, messages, filenames; unions conversation_ids.
3. UI shows filtered list; selecting one loads messages to Chatbot.

### 3.4 Export
1. User clicks export → MemoryManager.export_conversation_markdown writes ./exports/{title}-{timestamp}.md with header + transcript + files list.
2. UI displays success toast/path.

## 4. Module Boundaries

- src/chat_ui.py
  - Gradio UI composition, state, event handlers
  - Delegates to MemoryManager, FileHandler, and OpenRouterClient
  - No direct HTTP or DB logic

- src/openrouter_client.py
  - HTTP client to OpenRouter including streaming
  - Retry and error normalization
  - No UI or DB logic

- src/memory_manager.py
  - Supabase CRUD, search, export
  - Retry and error normalization
  - No UI or HTTP to OpenRouter

- src/file_handler.py
  - File validation, saving, extraction, preview
  - No DB or OpenRouter logic

- src/utils.py
  - Config validation, filenames, timestamps, backoff helpers, redaction

## 5. Technology Stack

- Python 3.10+
- Gradio >= 4.x
- httpx (streaming HTTP client) or requests + sseclient for streaming
- supabase (supabase-py) client
- File parsing:
  - Text: built-in open with chardet fallback (optional)
  - PDF: pymupdf (fitz) or pypdf; choose PyMuPDF for robust extraction
  - DOCX: python-docx
  - XLSX: openpyxl or pandas (prefer openpyxl to reduce deps; pandas optional)
  - CSV/JSON/YAML: csv, json, pyyaml
  - Images: Pillow (metadata only)
- Utility: python-dotenv (optional), chardet (optional)

## 6. requirements.txt (initial selection)

Pinned versions will be finalized at implementation:
- gradio
- httpx
- supabase
- python-dotenv
- pyyaml
- pymupdf
- python-docx
- openpyxl
- pillow
- chardet

## 7. Persistence Model (Supabase)

Tables:
- conversations(id uuid pk, title text, created_at timestamptz default now(), updated_at timestamptz default now())
- messages(id uuid pk, conversation_id uuid fk, role text check in ('user','assistant','system'), content text, file_paths jsonb, timestamp timestamptz default now())
- files(id uuid pk, filename text, file_path text, file_type text, upload_date timestamptz default now())

Indexes (optional for personal scale):
- idx_messages_conversation_id_timestamp
- idx_conversations_updated_at
- idx_files_filename (text pattern ops)

## 8. Error Handling and Retry

- OpenRouterClient: retry 2 attempts on 429/5xx/timeouts; exponential backoff (0.5s, 1.0s)
- MemoryManager: retry 3 attempts on network/5xx; backoff (0.5s, 1.0s, 2.0s)
- FileHandler: no auto-retry; deterministic parse; per-file error messages
- UI: show concise errors and “Retry” action; never expose secrets

## 9. Security Design (summary)

- Keys in config.json only; UI mask toggle; never log secrets
- Validate file extension and size; safe parsers; no code execution
- Render previews as Markdown code fences to avoid HTML injection
- Supabase anon key used for personal use; user controls data

(See security-architecture.md for details and deployment hardening references.)

## 10. Theming and Settings

- Theme setting in config.json (“dark” default)
- UI theme toggle updates Gradio theme; persisting this toggle to config.json is optional in v1
- API key visibility toggle in a settings modal/panel

## 11. Concurrency and Responsiveness

- Streaming handled via generator/callback; buffers tokens and flushes periodically
- File parsing in background thread pool (concurrency 2–3) to avoid blocking UI loop
- Supabase operations are quick; long operations show spinner/toast

## 12. Deployment and Operation

- Local run: python main.py; Gradio opens browser
- No containerization or remote deployment
- Backup: copy ./exports and config.json; Supabase data export via Supabase dashboard

## 13. Risks and Mitigations

- OpenRouter outages → User sees retries and can switch model; non-blocking UI
- PDF/DOCX parsing variability → Use PyMuPDF and python-docx; if failure, display friendly message
- Supabase connectivity → Retry and graceful degradation (warn user; allow chat without persistence temporarily)

## 14. Future Enhancements

- Vector search/RAG
- Conversation tags and file collections
- Global export/import of all conversations
- Keyboard shortcuts and custom themes
