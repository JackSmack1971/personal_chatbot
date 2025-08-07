# Day-2 Operations Guide

Operational procedures for running, monitoring, and maintaining the personal_chatbot container. This guide assumes the Compose service name personal_chatbot and uses a Compose-level healthcheck that invokes scripts/healthcheck.sh inside the container.

> Hardening cross-references for operators:
> - Digest Pinning Policy and refresh: docs/deployment/hardening/digest-pinning.md
> - Non-root runtime and mount ownership: docs/deployment/hardening/runtime-ownership.md
> - Least-privilege healthcheck requirements: docs/deployment/hardening/healthcheck-lp.md
> - Dockerfile capabilities baseline (cap_drop ALL): docs/deployment/hardening/dockerfile-caps.md
> - Vulnerability gates and POAM exceptions (how to request/track): docs/deployment/hardening/ci-vuln-gates-poam.md and .security/poam.yaml
> - ADR summary: memory-bank/decisionLog.md

Service lifecycle

Start/stop/restart (local)
- Start (foreground): docker compose up
- Start (detached): docker compose up -d
- Stop: docker compose down
- Restart service only: docker compose restart personal_chatbot

Upgrading
- Pull a new tag or digest:
  - docker pull ghcr.io/${{ github.repository }}/personal-chatbot:branch-main
  - or pin by digest: docker pull ghcr.io/${{ github.repository }}/personal-chatbot@sha256:<digest>
- Update Compose image reference if needed and apply:
  - docker compose up -d
- Verify healthcheck status and perform functional smoke tests

Configuration changes
- Edit .env or environment section in docker-compose.yml
- Apply: docker compose up -d
- Validate:
  - docker compose logs -f personal_chatbot
  - docker inspect --format '{{json .State.Health}}' $(docker compose ps -q personal_chatbot)

Health management

Healthcheck model
- Compose defines a healthcheck that runs: bash scripts/healthcheck.sh
- Standard parameters (example, see your docker-compose.yml):
  - interval: 10s
  - timeout: 3s
  - retries: 6
  - start_period: 20s
- The script should:
  - Probe the app readiness (e.g., HTTP GET to http://localhost:${PORT}/health or equivalent internal check)
  - Exit 0 on success; non-zero on failure
- Least-privilege expectations (enforced in CI and recommended in ops):
  - Runs as the same non-root user configured for the container
  - Uses bounded timeouts/retries as above
  - Does not require elevated capabilities or write access

Manual checks
- Execute healthcheck script manually:
  - docker compose exec personal_chatbot bash scripts/healthcheck.sh
- Inspect container health JSON:
  - docker inspect --format '{{json .State.Health}}' $(docker compose ps -q personal_chatbot)
- Curl the health endpoint (if exposed):
  - docker compose exec personal_chatbot curl -fsS http://localhost:${PORT}/health || echo "unhealthy"

Observability

Logs
- Tail runtime logs:
  - docker compose logs -f personal_chatbot
- Time-ranged logs:
  - docker compose logs --since=10m personal_chatbot
- Note: Application logs exclusively to stdout/stderr (no file logs inside container).

Metrics and traces
- If sidecar/agent collection is used, point it to collect container stdout and health status.
- Suggested labels/annotations can be added in Compose for better indexing (optional).

Storage and persistence

Writable directories (scoped)
- /app/personal_chatbot/uploads
- /app/personal_chatbot/exports
- Both should be mount-bound by Compose to host directories:
  - ./personal_chatbot/uploads:/app/personal_chatbot/uploads
  - ./personal_chatbot/exports:/app/personal_chatbot/exports

Backups
- Include mounted host paths in backup jobs.
- Recommended cadence: daily (adjust to RPO).
- Restore procedure:
  - Stop container: docker compose stop personal_chatbot
  - Restore host directories from backup
  - Start: docker compose up -d
  - Verify data presence and application health

Security operations

Image provenance and pinning
- Use GHCR source: ghcr.io/${{ github.repository }}/personal-chatbot
- For production, pin by digest for immutability:
  - ghcr.io/${{ github.repository }}/personal-chatbot@sha256:<digest>
- Maintain a known-good digest list in deployment records.
- Refresh cadence and acceptance criteria: see docs/deployment/hardening/digest-pinning.md

Secrets handling
- Provide secrets via environment (Compose .env or orchestrator secrets)
- Never commit secrets to the repo
- In GitHub Actions, use encrypted Secrets with least privilege
- Validate presence without printing secret values in logs

User and permissions
- Container runs as non-root; ensure mounted paths are writable by that UID/GID
- On permission errors, set correct ownership on host paths or adjust Compose volume options
- Runtime ownership validation steps: see docs/deployment/hardening/runtime-ownership.md

Capacity and performance

Scaling assumptions
- Service is designed to run as a single instance for local/edge usage; stateless components (model API calls) allow horizontal scaling if deployed to an orchestrator.
- Ensure writable paths are either per-instance or shared with appropriate concurrency controls.

Resource recommendations (baseline local)
- CPU: 0.5–1 vCPU
- Memory: 512–1024 MiB
- Adjust based on model latency and concurrency.

Incident response

Common failure signals
- Healthcheck flapping: investigate app startup time and health thresholds; review scripts/healthcheck.sh behavior and docs/deployment/hardening/healthcheck-lp.md
- 5xx spikes: check external model availability, timeouts, and retry settings
- Permission denied: verify host mount ownership for uploads/exports (see runtime-ownership guide)
- GHCR pull failures: validate docker login and Packages permission; confirm digest pinning correctness

Triage steps
- Check container state:
  - docker compose ps
- Review recent logs:
  - docker compose logs --since=15m personal_chatbot
- Run healthcheck manually:
  - docker compose exec personal_chatbot bash scripts/healthcheck.sh
- Validate environment:
  - docker compose exec personal_chatbot env | sort
- Connectivity:
  - docker compose exec personal_chatbot curl -I https://openrouter.ai/api/v1 || true

Rollback

Procedure
- Select prior sha or digest (from release notes or registry)
- Update Compose to the prior tag/digest
- docker compose pull && docker compose up -d
- Confirm health, then deprecate the faulty version in notes

Compliance and audits

- Dependency and SAST scans run in CI; review results per pipeline summary
- Keep a copy of image digests deployed and the matching scan reports for audit trails
- Vulnerability gates and exception handling: see docs/deployment/hardening/ci-vuln-gates-poam.md and .security/poam.yaml

References
- Runbook: deployment/README.md
- Env contract: deployment/environment-contract.md
- Troubleshooting: deployment/troubleshooting.md
- CI: .github/workflows/ci.yml
- CD: .github/workflows/cd.yml
- Healthcheck: scripts/healthcheck.sh
- Hardening index: docs/deployment/hardening/README.md
- ADR: memory-bank/decisionLog.md