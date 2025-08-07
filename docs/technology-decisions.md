# Technology Decisions — Personal Chatbot

Version: 1.0  
Status: Finalized for Implementation

This record documents key technology selections, rationale, and trade-offs for the MVP.

## 1. Programming Language and Runtime

- Language: Python 3.10+
- Rationale:
  - Strong ecosystem for quick prototyping and file parsing.
  - Gradio provides rapid local UI development.
  - Mature HTTP clients and Supabase SDK available.

## 2. UI Framework

- Choice: Gradio Blocks (v4.x)
- Rationale:
  - Simple local hosting, quick iteration, streaming-friendly.
  - Minimal boilerplate to build a chat layout with drag-and-drop uploads.
- Alternatives considered:
  - Streamlit (great for dashboards; streaming/chat wiring more manual).
  - FastAPI + custom front-end (more control but heavier initial investment).

## 3. LLM Provider and Client

- Provider: OpenRouter
- Default Model: openrouter/horizon-beta
- Additional Models: anthropic/claude-3.5-sonnet, openai/gpt-4
- Client: httpx (streaming support)
- Rationale:
  - OpenRouter offers multiple models through one API.
  - httpx supports modern async/stream patterns; good ergonomics.
- Alternatives:
  - requests + sseclient: possible but more moving parts for streaming.
  - Model-specific SDKs: reduces portability across models.

## 4. Persistence Layer

- Backend: Supabase (Postgres) with Python client (supabase-py)
- Tables: conversations, messages, files
- Rationale:
  - Free-tier managed Postgres suitable for personal scope.
  - Simple SDK with PostgREST under the hood.
- Alternatives:
  - SQLite local-only: simpler but loses cloud-resilient backup and remote accessibility.
  - Lite vector DB: out-of-scope for MVP and unnecessary complexity.

## 5. File Handling and Parsing

- Local storage:
  - uploads/: ./uploads/{conversation_id}/{yyyy-mm}/
  - exports/: ./exports/
- Libraries:
  - PDF: PyMuPDF (fitz) [primary]; pypdf optional fallback
  - DOCX: python-docx
  - XLSX: openpyxl (pandas optional; not required for MVP)
  - CSV/JSON/YAML: csv/json/pyyaml
  - Images: Pillow (metadata only)
  - Encoding detection: chardet (optional fallback)
- Rationale:
  - Balanced robustness vs. dependency footprint.
  - Avoid code execution; text extraction only.

## 6. Configuration Management

- File: config.json (in repo root)
- Keys:
  - openrouter_api_key, supabase_url, supabase_key, default_model, max_file_size, theme
- Optional: python-dotenv for .env convenience (Supabase credentials)
- Rationale:
  - Simple local file for a personal tool; easy to edit and back up.
- Security posture:
  - No secrets in code.
  - Keys masked in UI by default and redacted in logs.

## 7. Error Handling and Retry Policy

- OpenRouter:
  - Retry 2 attempts on 429/5xx/timeouts with exponential backoff (0.5s, 1.0s).
- Supabase:
  - Retry 3 attempts with backoff (0.5s, 1.0s, 2.0s).
- File parsing:
  - No automatic retries; deterministic; show per-file errors.
- Rationale:
  - Keeps UX simple and predictable while handling transient failures.

## 8. Search Strategy

- Approach: Simple SQL ilike across:
  - conversations.title
  - messages.content (grouped by conversation_id)
  - files.filename (grouped by conversation_id)
- Union conversation_ids and select conversations ORDER BY updated_at DESC LIMIT 50.
- Rationale:
  - Personal scale; maintain simplicity and avoid indexing complexity.
- Future:
  - Consider Postgres FTS or local index if scale increases.

## 9. Theming and UX

- Theme: config.json setting ("dark" default) with toggle in UI.
- Streaming:
  - Token buffer with periodic flush (~50–150ms) to reduce UI churn.
- File previews:
  - Markdown code fences with limited chars (~2,000) for performance.
- Rationale:
  - Smooth local experience with minimal configuration steps.

## 10. Security Decisions

- Use HTTPS endpoints for OpenRouter and Supabase.
- Local-only file storage; relative paths persisted.
- Validation:
  - Extension + size checks before extraction.
  - Safe filename normalization and unique path allocation.
- Logging:
  - Minimal log levels; redact secrets; suppress stack traces by default.
- Rationale:
  - Practical protections aligned with single-user local use.

## 11. Dependencies Summary (initial)

- gradio
- httpx
- supabase
- python-dotenv (optional)
- pyyaml
- pymupdf
- python-docx
- openpyxl
- pillow
- chardet

Exact versions pinned in requirements.txt at implementation time to ensure reproducibility.

## 12. Trade-offs and Reversibility

- Supabase vs. SQLite:
  - Chosen Supabase for persistence beyond device; reversible to SQLite with a small MemoryManager adapter.
- PyMuPDF vs. pypdf:
  - PyMuPDF provides better extraction in general; can fall back to pypdf with minimal code changes.
- Gradio vs. custom web app:
  - Gradio accelerates MVP; migration path to FastAPI + React exists if future needs demand.

## 13. Performance Considerations

- Concurrency:
  - Limit background parsing workers to 2–3.
- DOM updates:
  - Throttle streaming updates to keep UI smooth.
- DB calls:
  - Batch where practical; cap recent list to 50.

## 14. Observability

- Local log outputs only; no telemetry.
- Key counters:
  - Startup time
  - Retry counts for API/DB
  - File parse errors
