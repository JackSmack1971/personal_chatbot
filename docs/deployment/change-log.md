# Deployment-Impacting Change Log

Chronological record of changes that affect deployment, operations, and runtime behavior for the personal_chatbot service. This log complements commit history by highlighting operator-relevant items.

Format
- Date (UTC)
- Category: Container | Healthcheck | Compose | CI/CD | Security | Env Contract | Ops
- Summary
- Impact: What operators must know/do
- References: Files and image tags/digests

2025-08-07
- Category: Container
- Summary: Finalized hardened container (non-root user, tini as PID 1, stdout/stderr logging only); scoped writable directories for uploads and exports.
- Impact: Ensure host mounts exist and are writable by the container’s UID/GID; do not expect file-based logs inside the container.
- References:
  - Dockerfile
  - personal_chatbot/setup/entrypoint.sh
  - Writable dirs: personal_chatbot/uploads, personal_chatbot/exports

2025-08-07
- Category: Healthcheck
- Summary: Externalized healthcheck to docker-compose.yml via Compose-level healthcheck invoking scripts/healthcheck.sh.
- Impact: Operators should use docker inspect and the Compose health state for readiness; tune start_period/interval/retries in Compose for environment variance.
- References:
  - docker-compose.yml
  - scripts/healthcheck.sh

2025-08-07
- Category: Compose
- Summary: Local development and ops supported via docker compose build && docker compose up with service name personal_chatbot; volumes mount uploads and exports.
- Impact: Use docker compose logs -f personal_chatbot for logs; backup mounted host directories to preserve artifacts.
- References:
  - docker-compose.yml

2025-08-07
- Category: CI/CD
- Summary: CD publishes images to ghcr.io/${{ github.repository }}/personal-chatbot with sha, branch, and (if used) semver tags; SAST and dependency scans integrated.
- Impact: For private repositories, grant Packages permission to consumers; pin by digest for production deployments.
- References:
  - .github/workflows/ci.yml
  - .github/workflows/cd.yml
  - .github/workflows/README-deployment-notes.json

2025-08-07
- Category: Env Contract
- Summary: Environment variable contract codified; defaults/fallbacks aligned to code. Sensitive values must be provided via env/secrets.
- Impact: Populate OPENROUTER_API_KEY and other required settings in environment; avoid committing secrets.
- References:
  - docs/deployment/environment-contract.md
  - personal_chatbot/src/* (defaults)
  - personal_chatbot/README.md

2025-08-07
- Category: Security
- Summary: SAST and dependency scans enforced in CI; guidance to block High/Critical by default.
- Impact: Failed scans should be remediated before promotion; exceptions require documented rationale.
- References:
  - .github/workflows/ci.yml
  - docs/deployment/ci-cd.md

Operational guidance
- Start here: docs/deployment/README.md
- Day-2 operations: docs/deployment/operations-guide.md
- Troubleshooting: docs/deployment/troubleshooting.md

Image reference
- ghcr.io/${{ github.repository }}/personal-chatbot
- Prefer digest pinning for production: ghcr.io/${{ github.repository }}/personal-chatbot@sha256:<digest>