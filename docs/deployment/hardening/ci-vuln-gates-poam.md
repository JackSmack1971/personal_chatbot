# CI Vulnerability Gates and POAM Exceptions

Status: recommended (non-blocking), REQUIRED for production
Owner: DevSecOps, Security Reviewer
Review Cadence: each release and monthly vulnerability review

## Objective
Break builds on High/Critical vulnerabilities by default. Allow time-bound, documented exceptions via a Plan of Actions and Milestones (POAM) maintained in the repository and Memory Bank.

## Policy
- CI MUST fail if any High or Critical vulnerabilities are detected in application dependencies or container images.
- Exceptions are allowed only with an approved, time-bound POAM entry listing mitigation and due date.
- POAM entries MUST be tracked in-repo (e.g., .security/poam.yaml) and mirrored in Memory Bank with expiry.
- CI MUST fail when exceptions expire or if severity escalates beyond approved threshold.

## Acceptance Criteria
- CI pipeline includes a scanner step (e.g., Trivy/Grype/GHAS) and fails on High/Critical issues unless an active POAM exists.
- SBOM and scan reports are produced and stored as artifacts.
- A POAM file exists, schema is validated, and entries include owner, CVE(s), affected component, mitigation, and “expiresAt”.
- Memory Bank records POAM exceptions and their expiry.

## Implementation Guidance

### 1) Example CI configuration (concept)
- Use any CI: GitHub Actions, GitLab CI, Jenkins. The logic:
  1. Generate SBOM (e.g., syft or cyclonedx).
  2. Scan artifacts (Trivy/Grype/GHAS).
  3. Parse results; compare against .security/poam.yaml.
  4. Fail if High/Critical remain without valid exception or if expired.

### 2) Example POAM file
```yaml
# .security/poam.yaml
version: 1
exceptions:
  - id: POAM-2025-08-SEC-001
    cves: ["CVE-2025-12345"]
    component: "base-image: ghcr.io/org/app-base:1.2.3@sha256:..."
    severity: "CRITICAL"
    justification: "Awaiting upstream base image fix; compensating control: WAF rule and network egress restricted."
    mitigationPlan: "Upgrade to base image >=1.2.4 once released; rebuild with digest pinning."
    owner: "security@example.com"
    createdAt: "2025-08-01T00:00:00Z"
    expiresAt: "2025-09-01T00:00:00Z"
    status: "approved"
```

### 3) Example GitHub Actions skeleton
```yaml
name: security-scan
on: [push, pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Generate SBOM
        run: |
          pipx run syft packages dir:. -o cyclonedx-json > sbom.json || true
      - name: Trivy scan filesystem
        uses: aquasecurity/trivy-action@0.24.0
        with:
          scan-type: 'fs'
          format: 'json'
          output: 'trivy-fs.json'
          severity: 'HIGH,CRITICAL'
          ignore-unfixed: true
      - name: Enforce gates with POAM
        run: |
          python ./.security/enforce_poam.py --report trivy-fs.json --poam .security/poam.yaml
```

### 4) Enforcement script expectations
- Validate POAM schema (version, array of exceptions).
- Evaluate each finding; allow only when an exception with matching CVE/component exists and is unexpired.
- Produce a summary and exit non-zero if violations remain.

### 5) Memory Bank Integration
- Copy approved exceptions to Memory Bank with context:
  - memory-bank/decisionLog.md: rationale for exception model and risk acceptance.
  - memory-bank/progress.md: current active exceptions and expiry dates.
  - memory-bank/systemPatterns.md: scanner and POAM enforcement patterns.

## Runbook
- When a High/Critical is discovered:
  1. Attempt immediate remediation (upgrade dependency/container).
  2. If not possible, author a POAM entry with mitigation and expiry ≤ 30 days.
  3. Submit for Security approval; on approval, CI passes until expiry.
  4. Track mitigation progress; remove exception when fixed.
  5. If expiry reached without remediation, CI fails until resolved.

## References
- NIST POA&M guidance
- Trivy, Grype, GHAS documentation
- CycloneDX / SPDX SBOM standards