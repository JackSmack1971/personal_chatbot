# Non-Functional Requirements — Personal Chatbot

Version: 1.0  
Status: Approved for Architecture

These NFRs constrain implementation to ensure the app is fast, reliable, and safe for personal use.

## 1. Performance

- Startup time: < 10 seconds on a typical laptop (Intel i5/8GB RAM).
- UI responsiveness: interactions (clicks, typing) acknowledge within 100ms.
- Streaming latency: visible token updates every ≤250ms (target) or as delivered by provider.
- File processing:
  - Non-blocking: runs async; chat remains responsive.
  - Large files (up to configured limit): processed within reasonable time or reported with progress.
- Search:
  - Local filtering of recent conversations (≤50) is instant (< 100ms).
  - Server-side query for message content completes < 2s under free-tier conditions.

## 2. Reliability & Resilience

- OpenRouter requests:
  - Retry on transient errors (HTTP 429/5xx) up to 2 times with exponential backoff.
  - Single failure surfaces a clear, actionable message.
- Supabase connection:
  - Retry up to 3 attempts with exponential backoff.
  - If unavailable, app degrades gracefully (local-only mode for chat UI; warn persistence is offline).
- File system:
  - Unique filenames to avoid collisions.
  - Safe writes with temp file then atomic move when applicable.

## 3. Security & Privacy

- No secrets in source code.
- Secrets in config.json; redact in logs and UI (toggle visibility).
- Validate file type and size on upload; reject unsupported or oversized files.
- Use safe parsers for PDFs/Docs; never execute uploaded content.
- Error messages avoid leaking sensitive details (stack traces hidden by default).
- Local files remain on disk under ./personal_chatbot/uploads/ and ./personal_chatbot/exports/.
- Network access limited to OpenRouter and Supabase endpoints.

## 4. Maintainability

- Code structure follows modular layout; each module < 500 LOC.
- Clear separation of concerns:
  - UI (Gradio), OpenRouter client, Memory manager (Supabase), File handler, Utilities.
- Dependencies pinned in requirements.txt with versions.
- Basic unit tests for critical utilities and file handler parsing branches (happy-path at minimum).

## 5. Operability

- Single entry point: python main.py
- Configured via config.json and environment variables (for Supabase allowed).
- Logs:
  - Minimal, readable messages.
  - Info for lifecycle events; warnings/errors for failures.
  - No PII or secrets in logs.
- Graceful shutdown closes open streams and pending writes.

## 6. Compatibility

- Python: 3.10+
- OS: Windows 11, macOS 13+, Ubuntu 22.04+
- Browser: App runs in local browser via Gradio; tested on Chromium-based browsers.

## 7. Usability

- Dark/light theme toggle.
- Drag-and-drop files anywhere in chat area.
- Model selector visible and defaults to openrouter/horizon-beta.
- Clear status toasts for upload, parsing, retries, and errors.
- Accessible labels and keyboard navigation for primary actions.

## 8. Data Management

- Supabase tables per schema; timestamps in UTC.
- Exports are Markdown files with transcript and file references.
- Backups:
  - Manual: user can copy exports/ and config.json.
  - Optional: export all conversations to a zip via UI (future).

## 9. Observability (Local Scope)

- Basic metrics via logs:
  - Startup time
  - Request attempts/retries for OpenRouter
  - File processing successes/failures
- No remote telemetry.

## 10. Constraints

- Personal, single-user scenario; no authentication system.
- Free-tier Supabase usage expected; avoid heavy queries and indexes.
- No containerization or cloud deployment provided.

## 11. Quality Gates

- Functional acceptance criteria all pass.
- NFR sampling checks:
  - Manual timing confirms startup < 10s.
  - UI remains responsive during a 20MB PDF parse.
  - Error redaction verified.
  - Retry paths verified with simulated failures.
