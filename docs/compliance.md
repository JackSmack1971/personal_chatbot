# Compliance and Data Handling — Personal Chatbot

Version: 1.0  
Scope: Local personal-use assistant with Supabase persistence and local file storage

This document clarifies data handling practices and lightweight compliance considerations appropriate for a single-user local tool. It is not a legal document but a technical statement of intent and practices.

## 1. Data Classes and Locations

- Secrets
  - OpenRouter API key, Supabase URL and anon key
  - Location: config.json (local), optionally environment variables
- Conversation Data
  - Messages (roles, content, timestamps)
  - Location: Supabase (tables: conversations, messages)
- File Metadata
  - filename, relative path, type, upload date
  - Location: Supabase (files table)
- Local Files
  - Uploaded artifacts and exported transcripts
  - Location: ./uploads/, ./exports/ (local disk; relative paths used in DB)

## 2. Privacy Posture

- Single user; no multi-tenant data exposure.
- No telemetry or analytics collected by the app.
- External transmission limited to:
  - OpenRouter chat requests (message content leaves local machine)
  - Supabase DB operations (conversation/message/file metadata leaves local machine)
- Exports are plain Markdown files stored locally; user is responsible for sharing.

## 3. Security Practices Summary

- No secrets in source code or logs.
- Secrets masked in UI by default.
- HTTPS enforced for all outbound connections (OpenRouter, Supabase).
- File uploads validated (type/size) and parsed using safe libraries.
- Previews rendered via Markdown code fences; no HTML/script execution.

## 4. User Responsibilities

- Store config.json securely on machines with multiple users.
- Understand that conversation content is sent to OpenRouter and stored in Supabase.
- Backups: copy config.json, ./exports/, and manage Supabase backups via the dashboard.
- Avoid uploading sensitive files if concerned about preview text extraction.

## 5. Data Retention

- Conversations/messages/files persist in Supabase until user deletes them.
- Local uploads/exports remain on disk until removed by the user.
- Temporary files (if any) are cleaned periodically by the app’s cleanup routine.

## 6. Right-to-Delete (Personal Scope)

- Delete flows (future enhancement): add UI to delete a conversation and cascade its messages; local files are not auto-deleted to avoid accidental data loss (v1).
- For v1: manual deletion via Supabase dashboard and local filesystem.

## 7. Regulatory Context (Informational)

- GDPR/CCPA: This personal tool is not intended for multi-user or commercial deployment. If used with personal data:
  - Data controller is the user.
  - No automated profiling beyond AI responses.
  - Portability supported via conversation export to Markdown.
- SOC 2 / HIPAA: Out of scope for v1 (no commitments); do not upload PHI or other regulated data.

## 8. Incident Considerations (Personal Scope)

- In case of service outage (OpenRouter/Supabase), the app displays failures with retry; no automatic reporting.
- If local disk is compromised, secrets and data may be exposed; user should rotate API keys and manage OS-level protections.

## 9. Change Log and Commitments

- Changes impacting data handling or security will be documented in memory-bank/decisionLog.md and reflected here.
- Version pinning in requirements.txt reduces unexpected behavior from upstream dependencies.

## 10. Summary of Controls vs. Requirements

- Data Minimization: Only store what is necessary (message text, metadata, relative paths).
- Security: Secrets masked and never logged; validated file inputs; safe parsers.
- Transparency: Clear documentation of what is stored where and what is transmitted externally.
- Portability: Markdown exports of individual conversations.
- Deletion: Manual now; UI deletion planned in future versions.
