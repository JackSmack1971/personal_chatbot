# Personal Chatbot with Persistent Memory and File Upload — Specification

Version: 1.0  
Owner: 📋 Specification Writer  
Status: Approved for Pseudocode and Architecture phases

## 1. Overview

A local-first personal chatbot application with:
- Gradio Blocks UI with streaming
- OpenRouter API integration (default model: openrouter/horizon-beta)
- Persistent memory via Supabase (conversations, messages, files)
- Local drag-and-drop file uploads with extraction and preview
- Simple configuration with local config.json and environment variables

Primary objective: Ship a minimal, reliable tool that “just works” locally with easy setup.

## 2. Goals and Non-Goals

### Goals
- Fast local UI for interactive chat with token streaming
- Smooth drag-and-drop uploads for common file types with extraction
- Persistent memory: conversation history, search, exports
- Simple, editable configuration
- Model selection with working defaults

### Non-Goals
- Multi-user account system (personal, single-user scope)
- Cloud containerization and managed deployment
- Complex analytics/telemetry
- Advanced RAG/vector DB (out-of-scope for v1)

## 3. User Stories (Summary)
- As a user, I can chat and see streaming responses.
- As a user, I can drag-and-drop files and see previews.
- As a user, I can switch models from a dropdown.
- As a user, I can view and search recent conversations.
- As a user, I can export a conversation to Markdown.
- As a user, I can configure API keys and preferences easily.

(Full scenarios in docs/user-scenarios.md)

## 4. Core Functional Requirements

### 4.1 Chat and Streaming
- Display a chat transcript with roles (user/assistant) and timestamps.
- Stream OpenRouter tokens into the chat area live.
- Show typing/streaming indicator during generation.
- Support system or instruction prefix (optional) applied to each conversation.

### 4.2 Model Selection
- Dropdown with models:
  - openrouter/horizon-beta (default)
  - anthropic/claude-3.5-sonnet
  - openai/gpt-4
- Switching model affects subsequent generations in the active conversation.

### 4.3 File Upload and Processing
- Drag-and-drop and button-based upload, integrated with chat input area.
- Validate file types and enforce size limit (default 50 MB).
- Store uploaded files under ./personal_chatbot/uploads/<conversation_id>/<yyyy-mm>/
- Extract content for: txt, md, py, js, json, yaml, csv, pdf, docx, xlsx, html, css, sql, xml.
- Generate a compact preview snippet (first N chars/lines) with syntax highlighting where feasible.
- Link files to the current conversation; display file badges in messages.

### 4.4 Persistent Memory (Supabase)
- Tables:
  - conversations(id, title, created_at, updated_at)
  - messages(id, conversation_id, role, content, file_paths, timestamp)
  - files(id, filename, file_path, file_type, upload_date)
- Persist all messages and metadata.
- Maintain a recent conversations list (last 50).
- Smart titling: after first assistant reply, set conversation title based on early message text.

### 4.5 Search and History
- Search bar to filter conversations by:
  - title
  - message content (simple keyword search)
  - file name
- Display filtered list and allow loading any conversation.

### 4.6 Export
- Export a single conversation to Markdown under ./personal_chatbot/exports/<conversation_title>-<timestamp>.md
- Include referenced files list and a brief metadata header.

### 4.7 Settings and Configuration
- config.json stores:
  - openrouter_api_key (string)
  - supabase_url (string)
  - supabase_key (string)
  - default_model (string)
  - max_file_size (number, MB)
  - theme (string: dark|light)
- Toggle to show/hide API key in UI.
- Validate presence of required config values at startup; inline UI warnings if missing.

### 4.8 Error Handling
- API failures: user-friendly error with retry button; auto-retry up to 2 attempts.
- File processing failures: skip with a visible warning and continue chat workflow.
- Supabase connection retry with exponential backoff (max 3 attempts).
- Clear status updates in UI.

## 5. Non-Functional Requirements (Summary)
- Startup time < 10 seconds on typical laptop
- UI remains responsive during file processing (off-main-thread or async)
- Local-only file storage
- Minimal logging; redact secrets
- Dependencies pinned in requirements.txt

(Full list in docs/non-functional-requirements.md)

## 6. Data Model

### Conversation
- id: UUID
- title: text
- created_at: timestamp
- updated_at: timestamp

### Message
- id: UUID
- conversation_id: UUID
- role: enum('user','assistant','system')
- content: text
- file_paths: text[] or JSON array of strings
- timestamp: timestamp

### File
- id: UUID
- filename: text
- file_path: text (local relative path)
- file_type: text (MIME or extension)
- upload_date: timestamp

## 7. API Integrations

### OpenRouter
- Default model: openrouter/horizon-beta
- Streaming endpoint usage with token callbacks
- On change: anthropic/claude-3.5-sonnet, openai/gpt-4
- Configurable with API key from config.json

### Supabase
- Use standard Supabase Python client.
- Connection values via environment variables or config.json.
- SQL schema provided in setup/create_tables.sql.

## 8. UI Layout

- Top bar: Model selector, settings button (API key visibility toggle, theme)
- Left sidebar: Recent conversations list with search/filter (collapsible)
- Main area: Chat stream with file previews and typing indicator
- Bottom: Text input, send button, file upload controls; drag-and-drop anywhere in main area

## 9. Constraints and Assumptions
- Single user; no auth.
- Internet required for OpenRouter; app may show offline fallback (no generation).
- Supabase free tier sufficient for personal use.
- Python 3.10+ recommended.

## 10. Setup and Configuration Flow
- pip install -r requirements.txt
- Create Supabase project; run setup/create_tables.sql
- Fill config.json with API keys and preferences.
- Run python main.py

## 11. Acceptance Criteria Traceability
See docs/acceptance-criteria.md for the complete checklist mapped to this specification.

## 12. Risks
- Dependence on OpenRouter availability.
- File parsing robustness across formats.
- Supabase connectivity from local network.

## 13. Out-of-Scope for v1 (Potential Enhancements)
- Vector search/RAG
- Multi-user roles
- Desktop packaging
- Voice input and notifications (future)