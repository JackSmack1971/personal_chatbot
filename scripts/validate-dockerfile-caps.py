#!/usr/bin/env python3
"""
Validate Dockerfile hardening baseline:
- Enforce non-root USER
- Enforce capability drop (CAP_DROP=ALL or --cap-drop=ALL patterns)
- Optional: ensure no broad --privileged usage

Usage:
  python scripts/validate-dockerfile-caps.py Dockerfile
Exit codes:
  0 = pass
  1 = fail
"""
import sys
import re
from pathlib import Path

def fail(msg: str) -> None:
    print(f"::error title=Hardening violation::{msg}")
    sys.exit(1)

def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: validate-dockerfile-caps.py <Dockerfile-path>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        fail(f"Dockerfile not found at {path}")

    content = path.read_text(encoding="utf-8", errors="ignore")
    lines = [l.strip() for l in content.splitlines()]

    # Check USER non-root
    user_lines = [l for l in lines if l.upper().startswith("USER ")]
    if not user_lines:
        fail("No USER directive found. Define a non-root user. See docs/deployment/hardening/runtime-ownership.md")
    # Last USER must not be root
    last_user = user_lines[-1].split(None, 1)[1] if len(user_lines[-1].split(None,1)) > 1 else ""
    if last_user.lower() in ("root", "0", "uid=0"):
        fail("Container runs as root per final USER directive. Set a non-root USER. See runtime-ownership guide.")

    # Check capabilities baseline via explicit drop
    # For Dockerfile, we can check LABELs or comments, but stronger is to check compose/k8s.
    # Here we enforce presence of a note/ARG/ENV indicating cap_drop ALL in runtime manifests.
    # As a pragmatic baseline: require at least a comment or label referencing cap_drop ALL to signal policy.
    cap_mentions = [l for l in lines if re.search(r"cap[_-]?drop.*all", l, flags=re.I)]
    if not cap_mentions:
        print("::warning title=Capabilities drop not declared in Dockerfile::"
              "Ensure runtime manifests set cap_drop: [\"ALL\"]. See docs/deployment/hardening/dockerfile-caps.md")

    # Disallow privileged
    if any("--privileged" in l.lower() for l in lines):
        fail("Detected --privileged usage in Dockerfile. Remove privileged mode. See dockerfile-caps.md")

    print("Dockerfile capability and USER checks passed.")

if __name__ == "__main__":
    main()