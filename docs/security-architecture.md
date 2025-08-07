# Security Architecture — Personal Chatbot

Version: 1.0
Scope: Local-first personal tool using Gradio UI, OpenRouter, and Supabase

Security objective: Provide practical, low-friction controls appropriate for a single-user local app while preventing common risks in file handling, key management, and external API usage.

> See also: Deployment Hardening Baseline
> - Digest Pinning Policy: docs/deployment/hardening/digest-pinning.md
> - Runtime Ownership (non-root): docs/deployment/hardening/runtime-ownership.md
> - Least-Privilege Healthcheck: docs/deployment/hardening/healthcheck-lp.md
> - CI Vulnerability Gates + POAM: docs/deployment/hardening/ci-vuln-gates-poam.md
> - Dockerfile Capabilities Baseline: docs/deployment/hardening/dockerfile-caps.md
> - Consolidated ADR: memory-bank/decisionLog.md

## 1. Trust Model and Assets

- Single local user; no multi-user auth.
- Assets:
  - OpenRouter API key
  - Supabase URL and anon key
  - Local uploaded files and exports
  - Conversation transcripts (messages)

Threats addressed:
- Accidental leakage of secrets (logs/UI)
- Malicious or malformed files crashing parsers
- Excessive resource consumption from large files
- Transient network failures exposing stack traces
- Path traversal / unsafe file names

Out-of-scope (v1):
- Strong sandboxing of parsers
- Multi-tenant isolation
- End-to-end encryption of stored data

## 2. Secrets and Configuration

- Keys stored in config.json; never in source code.
- UI shows masked keys by default; user-controlled reveal.
- Logging redaction: redact(api_key) before logging any message containing secrets.
- Optional .env support via python-dotenv (local only).

Startup validation:
- If openrouter_api_key missing → disable chat; show UI warning.
- If Supabase creds missing → persistence disabled; warn user.

## 3. File Handling Safety

Validation steps:
1. Accept only known extensions: .txt, .md, .py, .js, .json, .yaml/.yml, .csv, .pdf, .docx, .xlsx, .html, .css, .sql, .xml, .png, .jpg, .jpeg, .gif, .webp
2. Enforce size limit: default 50 MB (configurable).
3. Use safe file name normalization: strip illegal characters, collapse whitespace, append random suffix; prevent path traversal.

Parsing safeguards:
- Use robust libraries:
  - PDF: PyMuPDF (fitz) or pypdf
  - DOCX: python-docx
  - XLSX: openpyxl
- Images: read metadata only (Pillow); no transformation/code execution.
- Parsing runs in background to avoid blocking; per-file try/except to isolate failures.
- On parse error: show friendly message; do not crash app; keep original file stored (user can remove manually).

Rendering:
- Previews displayed using Markdown code fences; do not render raw HTML from files.
- No client-side script execution.

## 4. Network and API Calls

OpenRouter:
- HTTPS only; Authorization header with Bearer token.
- Headers include local referer and title; no PII.
- Retries: 2 attempts on 429/5xx/timeouts with backoff; on final failure, show concise error.
- Do not include request body content in logs beyond minimal info.

Supabase:
- HTTPS only to project URL.
- Anon key usage (personal scope).
- Retries: 3 attempts with backoff; redacted error messages.

## 5. Error Handling and Logging

- Centralized error types: ValidationError, NetworkError, DatabaseError, ProcessingError.
- User-facing messages are friendly and non-technical.
- Logs:
  - Level: info/warn/error
  - No secrets or full stack traces by default.
  - Include operation name and high-level error category.

## 6. Data Storage and Backups

- Local directories:
  - ./uploads/{conversation_id}/{yyyy-mm}/ for uploaded files
  - ./exports/ for exported transcripts
- Paths are stored as relative paths in DB to ease backup/restore.
- Backups: copy exports/ and config.json; use Supabase dashboard for DB export.

## 7. Denial-of-Service and Resource Controls

- File size limit enforced prior to parse.
- Concurrency limit on parsing (2–3 workers).
- Preview length cap (e.g., 2,000 chars) to reduce memory/DOM churn.
- Streaming buffer throttled to ~50–150ms flush intervals to keep UI responsive.

## 8. Privacy Considerations

- Personal tool; no telemetry.
- Only connects to OpenRouter and Supabase endpoints configured by the user.
- Export files contain transcript and filenames/paths; user controls sharing.

## 9. Threat Model Summary

- TA1: Malicious file attempting to crash parser → mitigated via type/size validation and try/except isolation.
- TA2: Accidental secret leakage → masked UI, redacted logs, no secrets in exceptions.
- TA3: API instability → retries and graceful failures; no secrets in error surfaces.
- TA4: Path traversal in filenames → safe_filename and unique_path restrict and normalize.
- TA5: Large file UI freeze → async parsing, preview cap, worker limits.

## 10. Secure Defaults Checklist

- [x] Keys not in code
- [x] Masked by default in UI
- [x] Size/type validation on files
- [x] Safe parsers only
- [x] HTTPS for all network calls
- [x] Retry with capped attempts
- [x] Redacted logging
- [x] Relative paths for portability

## 11. Deployment Hardening Cross-References

To meet production-readiness, apply the following hardening controls and CI gates:
- Container image digest pinning and refresh procedure — see docs/deployment/hardening/digest-pinning.md
- Non-root runtime and writable mount ownership validation — see docs/deployment/hardening/runtime-ownership.md
- Least-privilege healthcheck (timeouts/retries, non-root) — see docs/deployment/hardening/healthcheck-lp.md
- CI vulnerability gates with POAM exceptions — see docs/deployment/hardening/ci-vuln-gates-poam.md and .security/poam.yaml
- Dockerfile capabilities baseline (drop ALL) and validation — see docs/deployment/hardening/dockerfile-caps.md

Architecture Decision Record:
- memory-bank/decisionLog.md — Architecture Decision Record: Container and CI Hardening Baseline
