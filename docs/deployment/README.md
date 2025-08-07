# personal_chatbot Deployment and Operations Runbook

This runbook documents how to build, run, observe, and operate the personal_chatbot container locally and in CI/CD. It is aligned with SPARC Completion quality gates and references the hardened container (non-root, tini, stdout-only), external healthcheck via Compose, and GHCR publishing.

Quick start (local)
- Build and run:
  - docker compose build
  - docker compose up
- Tail logs:
  - docker compose logs -f personal_chatbot
- Check health:
  - docker inspect --format '{{json .State.Health}}' $(docker compose ps -q personal_chatbot)
  - or run the healthcheck script inside the container:
    - docker compose exec personal_chatbot bash scripts/healthcheck.sh

Container image coordinates
- Registry: ghcr.io
- Image: ghcr.io/${{ github.repository }}/personal-chatbot
- Tags produced by pipelines:
  - sha-<short-sha>
  - branch-<branch-name>
  - semver tags if release tagging is used
- Pull examples:
  - docker pull ghcr.io/${{ github.repository }}/personal-chatbot:sha-abcdef1
  - docker pull ghcr.io/${{ github.repository }}/personal-chatbot:branch-main
- Pin by digest for production immutability:
  - docker pull ghcr.io/${{ github.repository }}/personal-chatbot@sha256:<digest>

Security by design (implemented)
- Non-root execution: Container runs as a dedicated non-root user with scoped writable directories only.
- Init process: tini used as PID 1 to properly handle signals and reap zombies.
- Logging: Application logs to stdout/stderr only. Do not write logs to files inside the image.
- Writable directories:
  - personal_chatbot/uploads (mounted by Compose)
  - personal_chatbot/exports (mounted by Compose)
  - Any other paths must be explicitly mounted if persistence is required.
- No secrets in image: All credentials and API keys provided via environment variables or secret stores.

Healthcheck model
- External healthcheck is defined at the Compose level and calls scripts/healthcheck.sh inside the running container.
- The script should validate service readiness (e.g., HTTP /health endpoint or internal probe), return 0 on success, non-zero on failure.
- Typical behavior:
  - start_period: grace period while app boots
  - interval, timeout, retries: tuned for stable readiness reporting
- Manual runs:
  - docker compose exec personal_chatbot bash scripts/healthcheck.sh

Environment variables
- The complete contract is documented in [deployment/environment-contract.md](environment-contract.md).
- Defaults and fallbacks match code and Dockerfile ENV where applicable.
- Provide sensitive values via environment or secrets providers (Actions secrets, local .env not committed).

Operations tasks
- Logs:
  - docker compose logs -f personal_chatbot
- Restart:
  - docker compose restart personal_chatbot
- Update configuration:
  - Edit .env or Compose environment, then docker compose up -d to apply.
- Backups (persistent data):
  - Back up mounted directories (uploads, exports) at your desired cadence.

Rollback procedure
- Select a previously known good tag (e.g., sha-<short-sha>) or digest.
- Edit Compose image tag or export IMAGE env, then:
  - docker compose pull
  - docker compose up -d
- Verify health (healthcheck and functional smoke tests).
- Revert if new version fails health checks.

CI/CD overview
- CI: .github/workflows/ci.yml
  - SAST and dependency scans
  - Build and test
- CD: .github/workflows/cd.yml
  - Builds and publishes image to ghcr.io/${{ github.repository }}/personal-chatbot with sha/branch/tag tags on push to main.
  - For private repositories, ensure “Packages” permission is granted to readers/deployers.
- Ops Notes (JSON): .github/workflows/README-deployment-notes.json summarizes pipeline behavior and ops details.

Local developer workflow
- Edit code
- docker compose build --no-cache personal_chatbot
- docker compose up personal_chatbot
- Verify health (Compose healthcheck or manual script)
- Run tests (if applicable in your local environment)

References
- Dockerfile: [../../Dockerfile](../../Dockerfile)
- Entrypoint: [../../personal_chatbot/setup/entrypoint.sh](../../personal_chatbot/setup/entrypoint.sh)
- Healthcheck script: [../../scripts/healthcheck.sh](../../scripts/healthcheck.sh)
- Compose: [../../docker-compose.yml](../../docker-compose.yml)
- CI: [../../.github/workflows/ci.yml](../../.github/workflows/ci.yml)
- CD: [../../.github/workflows/cd.yml](../../.github/workflows/cd.yml)
- Ops Notes JSON: [../../.github/workflows/README-deployment-notes.json](../../.github/workflows/README-deployment-notes.json)
- Env contract: [environment-contract.md](environment-contract.md)

Appendix: common commands
- Build: docker compose build
- Start: docker compose up -d
- Stop: docker compose down
- Logs: docker compose logs -f personal_chatbot
- Exec: docker compose exec personal_chatbot bash
- Health: docker compose ps; docker inspect --format '{{json .State.Health}}' $(docker compose ps -q personal_chatbot)