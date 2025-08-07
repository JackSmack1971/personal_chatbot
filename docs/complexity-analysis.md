# Complexity Analysis — Personal Chatbot

Version: 1.0  
Scope: Streaming chat, file processing, persistence, search, and UI concurrency

## 1. Streaming Chat Rendering

- Token streaming rate is provider-bound; UI updates should throttle to ~30–60 updates/sec to avoid excessive DOM churn.
- Complexity per streamed message:
  - O(T) where T is tokens; each update appends to a buffer (amortized O(1) per token if using incremental render).
- Risk:
  - Frequent updates may cause UI jank in browsers; mitigate with small buffer (accumulate tokens and flush at ~50–150ms intervals).

## 2. File Processing

### Supported Types
- Text/Code: .txt, .md, .py, .js, .json, .yaml/.yml, .csv, .html, .css, .sql, .xml
- Documents: .pdf, .docx, .xlsx
- Images: .png, .jpg, .jpeg, .gif, .webp (metadata only)

### Complexity Considerations
- Text/Code: O(N) for file size N (single pass read).
- CSV/XLSX:
  - CSV: O(N) read; memory proportional to line length; may stream line-by-line.
  - XLSX: O(R×C) where R rows, C columns; prefer reading only the first sheet and sampling rows for preview.
- PDF:
  - Library-dependent; page iteration O(P) pages; text extraction cost varies by font encodings.
- DOCX:
  - O(N) with python-docx; largely linear in document complexity.

### Concurrency
- Parsing must be async to avoid blocking UI.
- Limit concurrent parse jobs to 2–3 to keep CPU free for UI responsiveness.

## 3. Persistence (Supabase)

- Recent list query: O(50) with ORDER BY updated_at DESC LIMIT 50 — fast on free tier.
- Search:
  - Title ilike: O(n) across conversations (n small in personal use).
  - Message content ilike: O(m) across messages; can be heavier; mitigate with LIMIT and post-filtering.
  - File name ilike: O(k) across files.
- For personal scale (hundreds to thousands of messages), full-text search is unnecessary; simple ilike is acceptable.

## 4. Export to Markdown

- Exporting one conversation is O(M) for M messages; writes single file.
- Include files list (no file content) — negligible overhead.

## 5. Error Handling and Retries

- OpenRouter retry: up to 2 attempts with exponential backoff (e.g., 0.5s, 1.0s).
- Supabase retry: up to 3 attempts with 0.5s, 1.0s, 2.0s.
- Complexity increase is bounded; ensure non-blocking sleep via async or worker thread to keep UI responsive.

## 6. Memory Use

- Chat buffer: store recent messages only; lazy load older if needed (not required for v1).
- File previews: cap preview length (e.g., 2,000 chars) to prevent large DOM nodes.
- Keep file content out of memory after preview generation; do not hold full binary blobs.

## 7. Security and Validation

- File type detection by extension; optional secondary sniff via mimetypes; no execution paths.
- Reject > max size early using file_obj.size when available; otherwise check after save.
- Redact secrets in error messages; sanitize markup (render_md via Gradio is restricted, but avoid injecting untrusted HTML).

## 8. Operational Safeguards

- Atomic write pattern:
  - Write to temp path, then rename to final; reduces risk of partial files on crash.
- Cleanup:
  - Periodic cleanup of temp files older than 7 days; O(number of temp files).

## 9. Algorithmic Choices Summary

- Streaming: token buffer with interval flush (reduces UI churn).
- Search: simple ilike with union of conversation_ids across title, messages, and files.
- Export: linear write; safe and simple.
- Parsing: safe libraries, async workers, preview-only extraction to bound cost.

## 10. Expected Scale and Headroom

- Conversations: 100–500
- Messages: 1k–10k total
- Files: 100–1k total
- At this scale, naive queries and linear passes are acceptable; pivot to indexing/full-text only if growth exceeds personal scope.
