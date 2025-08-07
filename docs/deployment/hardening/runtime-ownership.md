# Runtime Ownership and Non-Root Execution

Status: recommended (non-blocking), REQUIRED for production
Owner: DevOps Engineer, Security Reviewer
Review Cadence: each release and when mounts/users change

## Objective
Ensure containers run as non-root and writable mounts are owned by the runtime UID:GID to avoid permission escalations and runtime failures.

## Policy
- Containers MUST run as a non-root user (fixed UID:GID).
- All writable paths (bind mounts and volumes) MUST be owned by that UID:GID at runtime.
- Ownership changes SHOULD happen build-time when feasible; if not possible, a minimal init step MAY perform targeted chown once.
- Document the chown/init step, scope it to necessary paths only, and make it idempotent.

## Acceptance Criteria
- Dockerfile defines USER non-root (e.g., `USER 10001:10001`).
- Entrypoint verifies effective UID/GID; logs and exits non-zero if root unless explicitly allowed for init.
- For each writable mount, ownership is correct or an init step adjusts it exactly once.
- Documentation includes host directory preparation or init behavior.

## Implementation Guidance

### 1) Dockerfile user and directories
```dockerfile
# Dockerfile (excerpt)
RUN addgroup --system app && adduser --system --ingroup app --uid 10001 app
WORKDIR /app
# Ensure app-owned writable dirs
RUN mkdir -p /data /var/run/app && chown -R 10001:10001 /data /var/run/app
USER 10001:10001
```

### 2) Entrypoint ownership verification (optional minimal chown)
```bash
#!/usr/bin/env bash
set -euo pipefail

TARGET_UID="${APP_UID:-10001}"
TARGET_GID="${APP_GID:-10001}"
WRITABLES="${WRITABLE_PATHS:-/data,/var/run/app}"

current_uid="$(id -u)"
current_gid="$(id -g)"

if [ "$current_uid" -eq 0 ]; then
  echo "ERROR: Running as root is not permitted by policy." >&2
  exit 1
fi

IFS=',' read -ra paths <<< "$WRITABLES"
for p in "${paths[@]}"; do
  [ -e "$p" ] || continue
  owner_uid="$(stat -c "%u" "$p" || echo "$current_uid")"
  owner_gid="$(stat -c "%g" "$p" || echo "$current_gid")"
  if [ "$owner_uid" != "$TARGET_UID" ] || [ "$owner_gid" != "$TARGET_GID" ]; then
    echo "WARN: $p owner is $owner_uid:$owner_gid, expected $TARGET_UID:$TARGET_GID"
    # If strict mode required, exit 1 here; otherwise rely on documented host prep.
  fi
done

exec "$@"
```

Notes:
- Prefer preparing host directories to already match UID:GID to avoid runtime chown on large mounts.
- If an init chown is absolutely required (e.g., Kubernetes initContainer), perform minimal and bounded scope.

### 3) Compose examples
```yaml
# docker-compose.yml (dev)
services:
  app:
    user: "10001:10001"
    volumes:
      - ./data:/data
    environment:
      - APP_UID=10001
      - APP_GID=10001
      - WRITABLE_PATHS=/data
```

### 4) Kubernetes init (alternative to runtime chown)
- Use an initContainer running as root to chown specific mount paths to 10001:10001, then main container runs as non-root.

## Host Preparation
- On the host, set directory ownership: `sudo chown -R 10001:10001 ./data`
- Ensure umask/permissions support container write needs.

## Validation Checklist
- Effective UID/GID not 0.
- All writable mounts are owned by container UID:GID or are world-writable with controlled permissions (prefer ownership).
- No setuid binaries present on writable mounts.

## References
- CIS Docker Benchmark: 4.1 Run containers as non-root