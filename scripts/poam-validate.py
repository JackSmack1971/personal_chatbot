#!/usr/bin/env python3
"""
POAM validator: enforce CI vulnerability gate exception policy.

Validates .security/poam.yaml structure and time-bound rules:
- meta fields present
- each exception has required fields
- due_by must be in the future or marked closed/mitigated
- severity limited to CRITICAL/HIGH
- status must be one of: pending|approved|mitigated|closed

Usage:
  python scripts/poam-validate.py .security/poam.yaml

Exit codes:
  0 = pass
  1 = fail
"""

import sys
import re
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:
    # Minimal fallback parser for simple YAML via json-like lines (not robust).
    # Strongly recommend installing PyYAML in CI if this triggers.
    print("::warning title=PyYAML not available::Install PyYAML for robust POAM parsing. Attempting naive fallback.")
    yaml = None  # sentinel


REQUIRED_EXCEPTION_FIELDS = {
    "id", "severity", "owner", "created_on", "due_by", "status", "remediation_plan"
}
ALLOWED_SEVERITIES = {"CRITICAL", "HIGH"}
ALLOWED_STATUS = {"pending", "approved", "mitigated", "closed"}

@dataclass
class Violation:
    message: str

def parse_yaml(path: Path):
    if yaml:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    # Extremely naive fallback for tiny templates; will likely fail on complex YAML.
    # Try to convert YAML-ish to JSON by removing comments and building key-values.
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = [l for l in text.splitlines() if l.strip() and not l.strip().startswith("#")]
    # Fallback: try to detect top-level keys and list under exceptions.
    data = {"meta": {}, "exceptions": []}
    current_exc = None
    for raw in lines:
        line = raw.strip()
        if line.startswith("meta:"):
            continue
        if line.startswith("exceptions:"):
            continue
        if line.startswith("- "):
            if current_exc:
                data["exceptions"].append(current_exc)
            current_exc = {}
            kv = line[2:].split(":", 1)
            if len(kv) == 2:
                current_exc[kv[0].strip()] = kv[1].strip().strip('"')
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            v = v.strip().strip('"')
            if current_exc is not None:
                current_exc[k.strip()] = v
            else:
                data["meta"][k.strip()] = v
    if current_exc:
        data["exceptions"].append(current_exc)
    return data

def iso_date(d: str) -> datetime:
    # Accept YYYY-MM-DD or full ISO
    try:
        if "T" in d:
            return datetime.fromisoformat(d.replace("Z", "+00:00"))
        return datetime.fromisoformat(d + "T00:00:00+00:00")
    except Exception:
        raise ValueError(f"Invalid ISO date format: {d}")

def validate(poam: dict) -> list[Violation]:
    violations: list[Violation] = []

    if not isinstance(poam, dict):
        violations.append(Violation("POAM root must be a mapping"))
        return violations

    if "exceptions" not in poam or not isinstance(poam["exceptions"], list):
        violations.append(Violation("POAM must contain 'exceptions' list"))
        return violations

    now = datetime.now(timezone.utc)

    for idx, exc in enumerate(poam["exceptions"], start=1):
        if not isinstance(exc, dict):
            violations.append(Violation(f"exceptions[{idx}] must be a mapping"))
            continue

        missing = REQUIRED_EXCEPTION_FIELDS - set(exc.keys())
        if missing:
            violations.append(Violation(f"{exc.get('id','exceptions['+str(idx)+']')} missing required fields: {', '.join(sorted(missing))}"))

        sev = str(exc.get("severity", "")).upper()
        if sev and sev not in ALLOWED_SEVERITIES:
            violations.append(Violation(f"{exc.get('id','exceptions['+str(idx)+']')} has invalid severity '{sev}' (allowed: {', '.join(sorted(ALLOWED_SEVERITIES))})"))

        status = str(exc.get("status", "")).lower()
        if status and status not in ALLOWED_STATUS:
            violations.append(Violation(f"{exc.get('id','exceptions['+str(idx)+']')} has invalid status '{status}' (allowed: {', '.join(sorted(ALLOWED_STATUS))})"))

        # Date checks
        try:
            due = iso_date(str(exc.get("due_by", "")))
            # Normalize to aware
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
            if status not in {"mitigated", "closed"} and due < now:
                violations.append(Violation(f"{exc.get('id','exceptions['+str(idx)+']')} is past due_by ({exc.get('due_by')}) and not mitigated/closed"))
        except Exception as e:
            violations.append(Violation(f"{exc.get('id','exceptions['+str(idx)+']')} invalid due_by: {e}"))

        try:
            created = iso_date(str(exc.get("created_on", "")))
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if created > now:
                violations.append(Violation(f"{exc.get('id','exceptions['+str(idx)+']')} created_on is in the future"))
        except Exception as e:
            violations.append(Violation(f"{exc.get('id','exceptions['+str(idx)+']')} invalid created_on: {e}"))

        # Minimal evidence check
        if not exc.get("remediation_plan"):
            violations.append(Violation(f"{exc.get('id','exceptions['+str(idx)+']')} must include remediation_plan"))
        # Optional references
        # cve or finding id
        if not exc.get("cve") and not exc.get("finding_id"):
            violations.append(Violation(f"{exc.get('id','exceptions['+str(idx)+']')} must include cve or finding_id"))

    return violations

def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: poam-validate.py <path-to-poam.yaml>")
        sys.exit(1)
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"::error title=POAM::File not found at {path}")
        sys.exit(1)

    try:
        data = parse_yaml(path)
    except Exception as e:
        print(f"::error title=POAM parse failure::{e}")
        sys.exit(1)

    violations = validate(data)
    if violations:
        print("::error title=POAM policy violations detected::")
        for v in violations:
            print(f"- {v.message}")
        sys.exit(1)

    print("POAM validation passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()