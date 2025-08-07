# Dockerfile: Non-Root and Minimal Capabilities

Status: recommended (non-blocking), REQUIRED for production
Owner: DevSecOps, Security Reviewer
Review Cadence: each release and upon privilege-related change

## Objective
Run containers as non-root and ensure no ambient capabilities are granted beyond what is strictly necessary. Periodically validate the baseline as the application evolves.

## Policy
- Dockerfile MUST define a non-root `USER` with fixed UID:GID.
- Default capability set MUST be “drop all”; only add specific capabilities if absolutely required.
- No `--privileged`, no host PID/IPC namespace sharing in production.
- Periodic validation MUST assert non-root execution and that no unexpected capabilities are present at runtime.

## Acceptance Criteria
- Dockerfile sets `USER` to non-root, writable directories owned appropriately.
- Runtime configuration (Compose/K8s) does not add privileged flags.
- If a capability is added, a justification exists in docs and ADR with expiry review.
- CI includes a check that runs the built image and prints effective UID and capabilities; pipeline fails if UID=0 or unexpected caps detected.

## Implementation Guidance

### 1) Dockerfile hardening pattern
```dockerfile
# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS base

# Create non-root user
RUN addgroup --system app && adduser --system --ingroup app --uid 10001 app

WORKDIR /app
COPY . /app

# Prepare writable dirs and ownership
RUN mkdir -p /data /var/run/app \
  && chown -R 10001:10001 /app /data /var/run/app

# Drop root
USER 10001:10001

# Avoid shell history, pin dependencies elsewhere, etc.
ENTRYPOINT ["python", "-m", "personal_chatbot.main"]
```

### 2) Compose runtime restrictions
```yaml
services:
  app:
    image: ghcr.io/org/app@sha256:...
    user: "10001:10001"
    cap_drop:
      - ALL
    # Only add what is strictly necessary (example):
    # cap_add:
    #   - NET_BIND_SERVICE
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp:rw,nosuid,nodev,noexec,size=64m
    # volumes:
    #   - ./data:/data:rw
```

### 3) Kubernetes runtime restrictions
```yaml
securityContext:
  runAsUser: 10001
  runAsGroup: 10001
  runAsNonRoot: true
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop: ["ALL"]
    # add: ["NET_BIND_SERVICE"]
```

### 4) CI validation examples
- Verify non-root and capability set at runtime:
```bash
docker run --rm --entrypoint sh ghcr.io/org/app@sha256:... -lc '
  echo "uid=$(id -u) gid=$(id -g)";
  # On many distros, capsh may be unavailable; use /proc
  if command -v getpcaps >/dev/null 2>&1; then
    getpcaps $$
  elif [ -r /proc/$$/status ]; then
    grep Cap /proc/$$/status || true
  else
    echo "WARN: capability introspection not supported"
  fi
'
```
- Fail pipeline if `id -u` prints `0` or capability mask not empty when unexpected.

### 5) Capability request process
- Require ADR and justification for any capability added:
  - Capability name, reason, scope, and alternatives considered.
  - Expiry review date (≤ 6 months).
  - Monitoring for misuse and runtime verification plan.

## Periodic Validation Runbook
- Quarterly job:
  1. Build image from Dockerfile.
  2. Run container; assert non-root and dropped caps.
  3. Scan for suid binaries: `find / -perm -4000 -type f 2>/dev/null | wc -l` (expect 0).
  4. Confirm Compose/K8s manifests have cap_drop: ALL and no privileged flags.
  5. Record results in Memory Bank (progress.md).

## References
- Docker and Kubernetes security contexts
- CIS Docker/Kubernetes Benchmarks
- Linux capabilities man pages