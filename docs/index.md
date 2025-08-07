# Deployment and Operations Documentation Index

This index links to all Completion-phase operational documents for the personal_chatbot service. These documents are aligned to SPARC Completion quality gates and reference the production-ready container, Compose healthcheck, and CI/CD to GHCR.

- Start here: [docs/deployment/README.md](deployment/README.md)
- Environment variables contract: [docs/deployment/environment-contract.md](deployment/environment-contract.md)
- Day-2 operations guide: [docs/deployment/operations-guide.md](deployment/operations-guide.md)
- Troubleshooting: [docs/deployment/troubleshooting.md](deployment/troubleshooting.md)
- CI/CD reference: [docs/deployment/ci-cd.md](deployment/ci-cd.md)
- Change log: [docs/deployment/change-log.md](deployment/change-log.md)

Audience targeting
- Operators/SRE: deployment/README.md, operations-guide.md, troubleshooting.md
- Dev/DevOps: environment-contract.md, ci-cd.md
- Stakeholders/Traceability: change-log.md

References to core artifacts
- Container: [Dockerfile](../Dockerfile)
- Entrypoint: [personal_chatbot/setup/entrypoint.sh](../personal_chatbot/setup/entrypoint.sh)
- Healthcheck: [scripts/healthcheck.sh](../scripts/healthcheck.sh)
- Compose: [docker-compose.yml](../docker-compose.yml)
- CI: [.github/workflows/ci.yml](../.github/workflows/ci.yml)
- CD: [.github/workflows/cd.yml](../.github/workflows/cd.yml)
- Ops Notes (JSON): [.github/workflows/README-deployment-notes.json](../.github/workflows/README-deployment-notes.json)