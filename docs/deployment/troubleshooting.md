# Troubleshooting Guide

This guide lists common operational issues for the personal_chatbot container and how to diagnose and resolve them. Assumes docker compose with service name personal_chatbot and a Compose-level healthcheck that invokes scripts/healthcheck.sh inside the container.

General diagnostics
- Show service status:
  - docker compose ps
- Tail recent logs:
  - docker compose logs --since=15m personal_chatbot
- Inspect health:
  - docker inspect --format '{{json .State.Health}}' $(docker compose ps -q personal_chatbot)
- Exec shell:
  - docker compose exec personal_chatbot bash

1) Healthcheck failing or flapping
Symptoms
- Status shows unhealthy or repeatedly alternates healthy/unhealthy.
- Deployments hang waiting for healthy state.

Checks
- Run healthcheck manually:
  - docker compose exec personal_chatbot bash scripts/healthcheck.sh; echo $?
- Verify app port:
  - echo $PORT inside container (default 8000)
  - netstat -tulpn or ss -lnt to confirm listening on 0.0.0.0:$PORT
- Curl the health endpoint:
  - docker compose exec personal_chatbot curl -fsS http://localhost:${PORT}/health || echo "unhealthy"
- Review start timings vs healthcheck thresholds:
  - start_period, interval, timeout, retries in docker-compose.yml

Fixes
- Increase start_period or retries if app boot is slower in your environment.
- Ensure HOST=0.0.0.0 and PORT are set correctly.
- Verify external dependencies (e.g., OpenRouter availability) if health depends on them.

2) Permission denied on writable directories
Symptoms
- Errors writing to /app/personal_chatbot/uploads or /app/personal_chatbot/exports.
- Traceback mentions EACCES or PermissionError.

Checks
- Confirm mounts:
  - docker compose exec personal_chatbot mount | grep personal_chatbot
- Check ownership and perms on host:
  - ls -la ./personal_chatbot/uploads ./personal_chatbot/exports

Fixes
- Align host directory ownership to match the container’s non-root UID/GID (e.g., chown -R <uid>:<gid>).
- Alternatively, adjust volume options to set appropriate permissions.
- Recreate directories if created by root previously.

3) GHCR pull/push permission errors
Symptoms
- docker pull returns denied: permission_denied or 401.
- CI publish step fails with insufficient scopes.

Checks
- Login:
  - echo $CR_PAT | docker login ghcr.io -u USERNAME --password-stdin
- Validate GitHub token scopes:
  - Packages: read for pulling; write for publishing
- Private repos require explicit Packages permission.

Fixes
- Update PAT scopes or repository permissions.
- Ensure image path matches:
  - ghcr.io/${{ github.repository }}/personal-chatbot

4) External API timeouts or 5xx errors
Symptoms
- Logs show timeouts or errors when calling model provider.
- Health may be impacted if healthcheck relies on external calls.

Checks
- Confirm env:
  - OPENROUTER_API_KEY present (do not echo value)
  - OPENROUTER_BASE_URL reachable from container:
    - docker compose exec personal_chatbot curl -I https://openrouter.ai/api/v1 || true
- Review timeout/retry settings:
  - REQUEST_TIMEOUT_SECONDS, MAX_RETRIES, RETRY_BACKOFF_SECONDS

Fixes
- Increase REQUEST_TIMEOUT_SECONDS within reasonable bounds.
- Tune retries/backoff; ensure circuit-breaking behavior in code is respected.
- Validate network egress and DNS resolution from container.

5) Entry point or startup failures
Symptoms
- Container exits immediately with non-zero code.
- Logs mention /bin/sh, bash, or permission errors.

Checks
- Examine logs for stack trace or shell errors.
- Validate line endings for scripts on Windows:
  - .gitattributes enforcing LF for sh scripts recommended
- Confirm shebang and executable bit on scripts:
  - scripts/healthcheck.sh and setup/entrypoint.sh must be executable

Fixes
- Convert CRLF to LF for shell scripts.
- chmod +x personal_chatbot/setup/entrypoint.sh scripts/healthcheck.sh (commit with proper perms).
- Verify tini invocation in Dockerfile and correct ENTRYPOINT.

6) Network binding conflicts on host
Symptoms
- Host port already in use; Compose fails to start or app unreachable.

Checks
- Inspect Compose port mappings.
- Identify conflicting process on host (e.g., netstat/ss/lsof).

Fixes
- Change host port mapping in docker-compose.yml (e.g., 8080:8000).
- Stop conflicting service or rebind it.

7) Dependency or SAST scan failures in CI
Symptoms
- CI pipeline red; security scan job failing.

Checks
- View CI logs in GitHub Actions.
- Identify vulnerable dependency and severity thresholds.

Fixes
- Upgrade dependencies to patched versions.
- For acceptable risks, document rationale; do not suppress without review.
- Re-run CI to confirm remediation.

8) Slow startup or memory pressure
Symptoms
- Healthcheck fails within start_period; OOM kills or high RSS.

Checks
- Review container memory with docker stats.
- Analyze logs for startup steps and model initialization.

Fixes
- Increase start_period and retries.
- Allocate more memory or reduce concurrency.
- Pre-warm caches only if necessary and documented.

Support data collection checklist
- Output of:
  - docker compose ps
  - docker compose logs --since=15m personal_chatbot
  - docker inspect --format '{{json .State.Health}}' $(docker compose ps -q personal_chatbot)
  - docker compose exec personal_chatbot env | sort | sed 's/=.*/=[REDACTED]/' (for secrets)
  - docker compose exec personal_chatbot bash scripts/healthcheck.sh; echo $?
- Note image tag/digest in use:
  - docker inspect --format '{{.RepoDigests}}' $(docker compose ps -q personal_chatbot)

References
- Runbook: deployment/README.md
- Operations: deployment/operations-guide.md
- Env contract: deployment/environment-contract.md
- CI/CD: .github/workflows/ci.yml, .github/workflows/cd.yml
- Healthcheck script: scripts/healthcheck.sh