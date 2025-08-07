# Acceptance Criteria — Personal Chatbot with Persistent Memory and File Upload

Version: 1.0  
Status: Ready for Verification

This checklist is the verification gate for v1 completion. Each item is testable and mapped to the specification.

## 1. Chat and Streaming

- [ ] Chat UI displays a conversation transcript with alternating roles (user/assistant) and timestamps.
- [ ] On send, assistant output is streamed token-by-token into the chat display.
- [ ] A typing/streaming indicator is visible during generation and disappears when complete.
- [ ] Sending a new message appends to the current conversation and persists to Supabase.
- [ ] Optional system/instruction prefix can be set and applied across the conversation (if provided).

## 2. Model Selection

- [ ] Model dropdown exists with options:
  - openrouter/horizon-beta (default)
  - anthropic/claude-3.5-sonnet
  - openai/gpt-4
- [ ] Selected model is used for subsequent assistant generations in the active conversation.
- [ ] Changing models does not crash streaming; selection persists during the session.

## 3. File Upload and Processing

- [ ] Users can drag-and-drop files anywhere in the main chat area.
- [ ] Users can click an upload button to select files.
- [ ] Files larger than the configured max size (default 50MB) are rejected with a clear message.
- [ ] Unsupported file types are rejected with a clear message.
- [ ] Accepted files are saved under ./personal_chatbot/uploads/<conversation_id>/<yyyy-mm>/ with unique filenames.
- [ ] Content extraction works for:
  - Text/code: .txt, .md, .py, .js, .json, .yaml, .csv, .html, .css, .sql, .xml
  - Documents: .pdf, .docx, .xlsx
- [ ] A preview snippet is displayed with basic syntax highlighting where feasible.
- [ ] The uploaded files appear visually linked to the relevant user message (badges or thumbnails).
- [ ] File metadata is persisted to Supabase (files table), and link association is recorded with the message.

## 4. Persistent Memory (Supabase)

- [ ] Supabase connection is established with retry (up to 3 attempts with backoff).
- [ ] New conversation rows are created on first message; updated_at changes on new messages.
- [ ] Messages are written with role, content, file_paths (JSON/array), and timestamp.
- [ ] Recent conversations list shows the last 50 conversations, sorted by updated_at desc.
- [ ] Smart title is set after the first assistant response (e.g., first 6–10 words of user prompt or model summary).
- [ ] Loading an existing conversation correctly displays all messages and associated files.

## 5. Search and History

- [ ] A search input filters the sidebar conversations in real-time by:
  - Title (case-insensitive contains)
  - Message content keyword
  - File name
- [ ] Result selection loads the chosen conversation without page reload.

## 6. Export

- [ ] From a conversation, a user can export to Markdown.
- [ ] The export file is written to ./personal_chatbot/exports/<conversation_title>-<timestamp>.md
- [ ] Export contains:
  - Metadata header (title, created_at, updated_at, model)
  - Full transcript with roles and timestamps
  - Referenced file list (filenames and relative paths)

## 7. Settings and Configuration

- [ ] config.json supports keys:
  - openrouter_api_key, supabase_url, supabase_key
  - default_model, max_file_size, theme
- [ ] Startup validation reports missing/invalid values with actionable messages.
- [ ] UI allows toggling API key visibility (masked by default).
- [ ] Theme toggle (dark/light) updates UI without restart (preferred) or on reload.

## 8. Error Handling and Resilience

- [ ] API generation failures show a clear message and a “Retry” button.
- [ ] Automatic retry attempts up to 2 times for transient API errors.
- [ ] File extraction errors are shown per-file while the rest of the chat remains functional.
- [ ] Supabase connection retry uses exponential backoff and surfaces status in UI if failing.
- [ ] Errors do not leak secrets; logs and UI messages are redacted.

## 9. Performance and UX

- [ ] Application cold start completes in < 10 seconds on a typical laptop.
- [ ] File uploads and extraction do not block the UI (async/background).
- [ ] Streaming is smooth with visible token updates within 250ms intervals (target).
- [ ] Scrolling in chat remains responsive during long generations.

## 10. Installation and Setup

- [ ] pip install -r requirements.txt completes with pinned versions.
- [ ] setup/create_tables.sql initializes required Supabase tables without manual edits.
- [ ] After adding credentials to config.json, python main.py starts the app successfully.
- [ ] README or docs contain a Quick Start section that matches observed setup behavior.

## 11. Data and Storage

- [ ] All local files are stored under ./personal_chatbot/uploads/ and ./personal_chatbot/exports/.
- [ ] No secrets are stored in code; only in config.json or environment.
- [ ] Export/import preserves content fidelity and timestamps (where available).

## 12. Quality Gates Mapping

- [ ] Functional: Chat streaming, file upload, persistence, export, model switching, search — all pass.
- [ ] Personal Use: Startup time, responsiveness, non-blocking file processing, easy config, no data loss — all pass.
- [ ] Security: No secrets in logs; robust file type/size validation; safe parsers; graceful error handling — all pass.

## 13. Out-of-Scope Confirmations (v1)

- [ ] No multi-user auth implemented.
- [ ] No containerization.
- [ ] No vector DB/RAG.
- [ ] No voice input or desktop notifications (may be noted as future).
