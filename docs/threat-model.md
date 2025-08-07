# Threat Model — Personal Chatbot

Version: 1.0  
Scope: Local, single-user Gradio app with OpenRouter and Supabase

Method: Lightweight STRIDE adaptation for a personal tool, focusing on practical mitigations.

## 1. System Context

Assets:
- Secrets: OpenRouter API key, Supabase URL and anon key
- Data: Conversations, messages, file metadata
- Local Files: Uploads and exports on disk

Trust boundaries:
- Local machine (UI, files)
- Network calls to OpenRouter
- Network calls to Supabase (PostgREST)

## 2. Entry Points and Actors

- Local user via browser UI (Gradio)
- File inputs via drag-and-drop / file selector
- Outbound HTTP(S) to OpenRouter/Supabase
- Disk I/O for uploads/exports

## 3. STRIDE Analysis

### 3.1 Spoofing
- Risk: N/A (single user, no auth). Browser session is local.
- Control: No multi-user assumptions; CSRF not applicable for local-only; keep Gradio interface on localhost.

### 3.2 Tampering
- Risk: Path traversal or malicious filenames overwriting files.
- Mitigations:
  - safe_filename(): strip/normalize and disallow path separators, dots beyond extension.
  - unique_path(): avoid overwriting existing files; atomic move from temp.
  - Store relative paths; never resolve to arbitrary absolute paths.

### 3.3 Repudiation
- Risk: Low for personal tool; activity logs limited.
- Mitigations:
  - Minimal logs with timestamps for key operations (upload, export, API call failure).
  - No PII or secrets logged.

### 3.4 Information Disclosure
- Risks:
  - Secrets leaked to logs/UI.
  - Exported transcripts shared inadvertently with file paths.
- Mitigations:
  - Mask secrets in UI by default; redact() in logs.
  - Clear export headers and file lists; user awareness; local-only storage.
  - HTTPS for all network calls.

### 3.5 Denial of Service
- Risks:
  - Large or numerous files causing parse/CPU spikes.
  - Aggressive streaming updates causing UI jank.
- Mitigations:
  - Size limit (50MB default); concurrent parse cap (2–3 workers).
  - Preview character cap; streaming flush throttling.

### 3.6 Elevation of Privilege
- Risk: File contents leading to code execution or XSS.
- Mitigations:
  - Use safe parsers (PyMuPDF, python-docx, openpyxl).
  - Render previews as Markdown code fences; no raw HTML execution.
  - Gradio sanitization; do not embed unsafe HTML.

## 4. External Dependencies

- OpenRouter API: Requires API key; network reliability and quota limits.
  - Mitigation: Retries; user-friendly errors; allow model switching.

- Supabase: Anon key with database access scoped to project; availability risk.
  - Mitigation: Retries; graceful degradation when unavailable.

## 5. Secure Defaults and Operational Guidance

- Keep app bound to localhost.
- Store config.json in project root; optionally restrict file permissions on multi-user machines.
- Back up config.json and exports/ cautiously (personal data).

## 6. Residual Risks

- Parser zero-day vulnerabilities (low probability).
- Local machine compromise compromises secrets and data.
- No at-rest encryption for local files (by design simplicity).

## 7. Validation Checklist

- [x] Filenames sanitized and unique
- [x] Size/type validation enforced
- [x] Secrets masked in UI and logs
- [x] HTTPS for all external calls
- [x] Retry with capped attempts
- [x] Previews rendered safely
- [x] Concurrency limits in place
