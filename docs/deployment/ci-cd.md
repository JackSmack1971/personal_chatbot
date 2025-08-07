# CI/CD Reference

This document summarizes the CI and CD pipelines for personal_chatbot, the image publishing strategy to GHCR, and security scanning expectations. It aligns with SPARC Completion quality gates.

> Hardening references used by CI/CD:
> - Digest Pinning: docs/deployment/hardening/digest-pinning.md
> - Vulnerability Gates + POAM: docs/deployment/hardening/ci-vuln-gates-poam.md and .security/poam.yaml
> - Dockerfile Capabilities Baseline: docs/deployment/hardening/dockerfile-caps.md
> - Healthcheck Least-Privilege: docs/deployment/hardening/healthcheck-lp.md
> - Runtime Ownership (non-root): docs/deployment/hardening/runtime-ownership.md
> - ADR: memory-bank/decisionLog.md

Pipeline overview

CI: .github/workflows/ci.yml
- Purpose: Build, test, lint, and perform security scans (SAST + dependency).
- Typical jobs (indicative; see workflow for exact names):
  - setup: Checkout, set up Python, cache deps.
  - test: Run unit/integration tests.
  - lint/sast: Static analysis and security scanning.
  - dependency-audit: Dependency vulnerability scan.
  - hardening-validate: run scripts/validate-dockerfile-caps.py, scripts/validate-healthcheck.sh
- Artifacts:
  - Test reports and logs (if configured).
  - Scan reports (if uploaded or annotated).

CD: .github/workflows/cd.yml
- Purpose: Build and publish container image to GHCR on push to main.
- Image name:
  - ghcr.io/${{ github.repository }}/personal-chatbot
- Tags emitted:
  - sha-<short-sha>
  - branch-<branch-name>
  - semver tags (if release tagging is in place)
- Permissions:
  - Actions must be allowed to write to GHCR.
  - For private repositories, ensure “Packages” permission for consumers pulling the image.
- Security steps:
  - SAST and dependency scan gate before publish (either in CI or within CD pre-steps).
  - Digest check gate (scripts/validate-digests.py) before promotion to environments.
  - Optionally sign images and/or attach SBOM if configured.

Tagging strategy

- sha- tags:
  - Immutable mapping to a specific commit; recommended for rollbacks and precise pinning.
- branch- tags:
  - Track the head of a branch; useful for non-prod deployments or ephemeral environments.
- semver tags:
  - Human-readable releases; recommended for production alongside digest pinning.
- Digest pinning:
  - For production, use the digest: ghcr.io/${{ github.repository }}/personal-chatbot@sha256:<digest>

Operational usage examples

Build (local)
- docker compose build

Run (local)
- docker compose up -d

Pull from GHCR (consumer)
- docker pull ghcr.io/${{ github.repository }}/personal-chatbot:sha-abcdef1
- docker pull ghcr.io/${{ github.repository }}/personal-chatbot:branch-main
- docker pull ghcr.io/${{ github.repository }}/personal-chatbot@sha256:<digest>

Login to GHCR (if needed)
- echo $CR_PAT | docker login ghcr.io -u USERNAME --password-stdin
  - CR_PAT must include Packages:read to pull; write to publish.

Security scanning

- SAST:
  - Static application security testing runs in CI (and/or CD pre-publish).
  - Failing thresholds should block merges; reports appear in workflow logs or security tab.
- Dependency scanning:
  - Identifies vulnerable dependencies; failing thresholds must be remediated or explicitly risk-accepted.
- Suggested policy:
  - Block Critical/High findings by default; document exceptions in .security/poam.yaml with due dates and link to memory-bank/decisionLog.md (ADR).
  - See template at .security/poam.yaml (created in this change set).

Gating and exceptions

- Vulnerability gates:
  - CI fails on Critical/High by default.
  - Exceptions require:
    - POAM entry in .security/poam.yaml with owner, rationale, and remediation date.
    - Reference to affected package/CVE and PR link.
- Hardening gates:
  - Fail if Dockerfile lacks USER non-root or cap_drop: ALL.
  - Fail if healthcheck violates least-privilege/timeouts policy.
  - Fail if deployment inputs use mutable tags for production without digest pinning.

Workflow triggers (indicative)

- CI:
  - pull_request: run tests, scans, and hardening validations on proposed changes.
  - push: run on branches to keep status current.
- CD:
  - push to main: build and publish image to GHCR.
  - optional: release: semver tag builds.

Release and promotion

- Recommended flow:
  - On tag vX.Y.Z, build and push semver tag.
  - Promote by referencing the semver tag and record the digest being deployed.
  - Store deployed digest and scan results for audit.

Auditability and evidence

- Retain:
  - Commit SHA, image digest, SAST/dependency scan results.
  - Deployment notes: .github/workflows/README-deployment-notes.json
- Traceability:
  - Link PRs/commits to images via sha- tags for precise provenance.

References

- CI Workflow: .github/workflows/ci.yml
- CD Workflow: .github/workflows/cd.yml
- Security Gates Workflow: .github/workflows/security-gates.yml
- Hardening: docs/deployment/hardening/README.md
- ADR: memory-bank/decisionLog.md
- Ops Notes (JSON): .github/workflows/README-deployment-notes.json
- Runbook: deployment/README.md
- Troubleshooting: deployment/troubleshooting.md