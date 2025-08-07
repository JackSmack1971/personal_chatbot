# Environment Variable Contract

This document specifies all runtime configuration for the personal_chatbot container. Defaults and fallbacks align with code and container configuration. Sensitive values must not be committed; provide them via environment variables or secret providers.

Conventions
- Scope: Runtime unless noted. Do not bake secrets into images.
- Sensitivity:
  - S: Sensitive (treat as secret)
  - N: Non-sensitive
- Source of default:
  - Code: Default defined in Python code
  - Docker: Default defined in Dockerfile ENV or entrypoint
  - None: No default; must be provided

Variables

1) Core networking
- HOST
  - Type: string
  - Required: No
  - Default: 0.0.0.0 (Code/Docker)
  - Sensitivity: N
  - Notes: Bind address inside container.
- PORT
  - Type: int
  - Required: No
  - Default: 8000 (Code)
  - Sensitivity: N
  - Notes: Service port inside container; Compose maps to host.
- LOG_LEVEL
  - Type: enum [DEBUG, INFO, WARNING, ERROR]
  - Required: No
  - Default: INFO (Code)
  - Sensitivity: N
  - Notes: Controls verbosity to stdout.

2) Model provider configuration
- OPENROUTER_API_KEY
  - Type: string
  - Required: Yes for external model usage
  - Default: None
  - Sensitivity: S
  - Notes: Provide via secrets; not stored on disk.
- OPENROUTER_BASE_URL
  - Type: string (URL)
  - Required: No
  - Default: https://openrouter.ai/api/v1 (Code)
  - Sensitivity: N
  - Notes: Override for alternative endpoints if needed.
- OPENROUTER_MODEL
  - Type: string
  - Required: No
  - Default: A reasonable model per code default (Code)
  - Sensitivity: N

3) Data locations
- UPLOADS_DIR
  - Type: path
  - Required: No
  - Default: personal_chatbot/uploads (Code)
  - Sensitivity: N
  - Notes: Mounted as a writable directory via Compose.
- EXPORTS_DIR
  - Type: path
  - Required: No
  - Default: personal_chatbot/exports (Code)
  - Sensitivity: N
  - Notes: Mounted as a writable directory via Compose.

4) HTTP client controls
- REQUEST_TIMEOUT_SECONDS
  - Type: int
  - Required: No
  - Default: 60 (Code)
  - Sensitivity: N
  - Notes: External API call timeout.
- MAX_RETRIES
  - Type: int
  - Required: No
  - Default: 3 (Code)
  - Sensitivity: N
  - Notes: Retry attempts for transient errors.
- RETRY_BACKOFF_SECONDS
  - Type: int/float
  - Required: No
  - Default: 2 (Code)
  - Sensitivity: N

5) UI/runtime behavior
- ENABLE_CHAT_UI
  - Type: bool
  - Required: No
  - Default: true (Code)
  - Sensitivity: N
- ENABLE_FILE_UPLOADS
  - Type: bool
  - Required: No
  - Default: true (Code)
  - Sensitivity: N

Compose bindings (example)
- docker-compose.yml excerpts:
  - service name: personal_chatbot
  - environment:
    - HOST=0.0.0.0
    - PORT=8000
    - LOG_LEVEL=INFO
    - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    - OPENROUTER_BASE_URL=${OPENROUTER_BASE_URL:-https://openrouter.ai/api/v1}
    - OPENROUTER_MODEL=${OPENROUTER_MODEL:-gpt-4o-mini}
    - UPLOADS_DIR=/app/personal_chatbot/uploads
    - EXPORTS_DIR=/app/personal_chatbot/exports
  - volumes:
    - ./personal_chatbot/uploads:/app/personal_chatbot/uploads
    - ./personal_chatbot/exports:/app/personal_chatbot/exports
  - healthcheck (Compose-level):
    - test: ["bash", "scripts/healthcheck.sh"]
    - interval: 10s
    - timeout: 3s
    - retries: 6
    - start_period: 20s

Sample .env (local, do not commit)
- OPENROUTER_API_KEY=sk-live-XXXX
- LOG_LEVEL=INFO
- PORT=8000

Validation and fallbacks
- Missing OPENROUTER_API_KEY will prevent external model calls; the service should fail gracefully or disable related features per code logic.
- Paths must exist and be writable by the non-root user. Compose mounts provide host-side persistence.
- Invalid LOG_LEVEL falls back to INFO.

Security guidance
- Store secrets in GitHub Actions secrets; grant least-privileged access.
- For private registries, ensure “Packages” permission for GHCR pulls.
- Avoid echoing sensitive envs in logs. Validate presence without printing values.

Image reference for docs and pipelines
- ghcr.io/${{ github.repository }}/personal-chatbot
- Use sha or digest pinning for production deployments.