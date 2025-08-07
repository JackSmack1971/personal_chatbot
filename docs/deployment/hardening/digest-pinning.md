# Digest Pinning for Production Deployments

Status: recommended (non-blocking), REQUIRED for production
Owner: DevOps Engineer, Security Reviewer
Review Cadence: quarterly or on image refresh

## Objective
Prevent image tag drift by pinning container images to immutable digests in production deployments.

## Policy
- All production Compose/Orchestrator references MUST use `@sha256:` digests.
- Tags like `:latest` or floating minor tags are not permitted in production.
- A prod override (e.g., docker-compose.prod.yml) SHALL contain only digested images.
- CI MUST fail if non-digested images are referenced in production manifests.

## Acceptance Criteria
- Production manifests reference images in format: `registry/repo:tag@sha256:...`.
- CI check enforces no non-digested images in prod.
- Documented refresh procedure is published and followed.

## Implementation Guidance
1) Create a production override (example):
```yaml
# docker-compose.prod.yml
services:
  app:
    image: ghcr.io/org/app:1.2.3@sha256:aaaaaaaaaaaaaaaa...
  worker:
    image: ghcr.io/org/worker:0.9.1@sha256:bbbbbbbbbbbbbbbb...
```

2) Obtain digests (examples):
- docker: `docker buildx imagetools inspect ghcr.io/org/app:1.2.3`
- crane: `crane digest ghcr.io/org/app:1.2.3`
- cosign: `cosign verify --certificate-identity ...`

3) CI Enforcement (concept):
- Step scans `docker-compose.prod.yml` and fails if any `image:` lacks `@sha256:`.

## Digest Refresh Procedure
- Trigger: release, base image CVE fix, or monthly maintenance.
- Steps:
  1. Pull/tag intended version and retrieve digest.
  2. Update `docker-compose.prod.yml` with the new digest.
  3. Run vulnerability scan on final locked images.
  4. Commit with message referencing CVE/POAM if applicable.
  5. Deploy after passing gates.

## Rollback Strategy
- Keep previous digested file version.
- Rollback is deterministic by reverting to last known digest.

## References
- Supply-chain security best practices (SLSA, Sigstore)