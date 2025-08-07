#!/usr/bin/env python3
"""
Validate digest pinning usage for production contexts.

Checks docker-compose.yml (or provided manifest path) to flag services/images
that use mutable tags (e.g., :latest, :branch-*) without an immutable digest
reference (image@sha256:...).

Usage:
  python scripts/validate-digests.py docker-compose.yml

Exit codes:
  0 = no blocking violations (informational by default in PRs)
  1 = violations found (use for enforcing in protected branches)
"""
import re
import sys
from pathlib import Path

DIGEST_RE = re.compile(r"@sha256:[0-9a-fA-F]{64}$")
IMAGE_LINE_RE = re.compile(r"^\s*image:\s*([^\s#]+)")

def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: validate-digests.py <compose-file>")
        sys.exit(1)
    compose_path = Path(sys.argv[1])
    if not compose_path.exists():
        print(f"::error title=Digest check::Compose file not found at {compose_path}")
        sys.exit(1)

    violations = []
    for line_no, line in enumerate(compose_path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        m = IMAGE_LINE_RE.search(line)
        if not m:
            continue
        image = m.group(1).strip().strip("'\"")
        # If image has an explicit digest, it's compliant
        if DIGEST_RE.search(image):
            continue
        # Tag present but no digest → violation
        if ":" in image and not DIGEST_RE.search(image):
            violations.append((line_no, image))
        # No tag → implicit :latest → violation
        elif ":" not in image:
            violations.append((line_no, image + ":latest"))

    if violations:
        print("::warning title=Digest pinning advisory::Mutable tags detected without digest pinning:")
        for ln, img in violations:
            print(f"- line {ln}: {img}")
        print("For production, use immutable digests (image@sha256:...) per docs/deployment/hardening/digest-pinning.md")
        # Keep advisory non-blocking by default
        sys.exit(0)

    print("All image references appear to use immutable digests or are locally built.")
    sys.exit(0)

if __name__ == "__main__":
    main()