# Healthcheck: Least Privilege and Bounded Execution

Status: recommended (non-blocking), REQUIRED for production
Owner: DevOps Engineer, Security Reviewer
Review Cadence: each release and when healthcheck logic changes

## Objective
Ensure the container healthcheck runs with least privilege, executes quickly with bounded timeouts/retries, and produces reliable exit codes without requiring elevated permissions.

## Policy
- Healthcheck MUST run as the same non-root user as the service.
- Healthcheck MUST have a strict timeout and bounded retries/intervals.
- Healthcheck MUST avoid privileged operations (no sudo, no root-only paths).
- Exit code semantics:
  - 0 = healthy
  - non-zero = unhealthy (transient or hard failure)
- Healthcheck MUST be side-effect free (read-only checks where possible).

## Acceptance Criteria
- Compose/K8s specifies timeout, interval, retries, start_period.
- The script uses `set -euo pipefail`, bounded network timeouts, and does not require root.
- Healthcheck failures are observable in logs and metrics docking.

## Implementation Guidance

### 1) Healthcheck script pattern
```bash
#!/usr/bin/env bash
# scripts/healthcheck.sh
set -euo pipefail

# Configuration
ENDPOINT="${HEALTH_ENDPOINT:-http://127.0.0.1:8080/healthz}"
TIMEOUT="${HEALTH_TIMEOUT_SECONDS:-2}"

# Use curl with timeouts; fallback to busybox/wget if needed
if command -v curl >/dev/null 2>&1; then
  curl --fail --silent --show-error --max-time "$TIMEOUT" "$ENDPOINT" >/dev/null
elif command -v wget >/dev/null 2>&1; then
  wget -q -T "$TIMEOUT" -O - "$ENDPOINT" >/dev/null
else
  echo "No HTTP client available for healthcheck" >&2
  exit 1
fi
```

- Ensure script is executable: `chmod +x scripts/healthcheck.sh`
- Script MUST NOT escalate privileges or touch protected paths.

### 2) Compose example (bounded)
```yaml
services:
  app:
    user: "10001:10001"
    healthcheck:
      test: ["CMD", "/bin/sh", "-c", "/app/scripts/healthcheck.sh"]
      interval: 15s
      timeout: 3s
      retries: 3
      start_period: 20s
```

### 3) Kubernetes example
```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 20
  periodSeconds: 15
  timeoutSeconds: 3
  failureThreshold: 3
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 2
  failureThreshold: 3
```

### 4) Observability
- Log healthcheck failures and reasons in the application logs (not in the script).
- Export counters for unhealthy transitions if app exposes metrics.

## Validation Checklist
- Healthcheck runs as non-root user.
- Timeout and retry parameters defined and reasonable.
- No privileged commands or file access required.
- Script exits promptly under failure within timeout budget.

## References
- Docker healthcheck docs
- Kubernetes probes best practices