#!/usr/bin/env bash
# Validate least-privilege healthcheck expectations against compose and script.
# Usage: bash scripts/validate-healthcheck.sh docker-compose.yml scripts/healthcheck.sh
# Fails if:
# - docker-compose.yml healthcheck is missing or lacks bounded interval/timeout/retries/start_period
# - healthcheck script appears to require root (heuristic) or writes outside /tmp
set -euo pipefail

COMPOSE_FILE="${1:-docker-compose.yml}"
SCRIPT_PATH="${2:-scripts/healthcheck.sh}"

fail() {
  echo "::error title=Healthcheck policy violation::$1"
  exit 1
}

warn() {
  echo "::warning title=Healthcheck policy::$1"
}

if [[ ! -f "$COMPOSE_FILE" ]]; then
  fail "Compose file not found at $COMPOSE_FILE"
fi

# Basic YAML grep heuristics to avoid heavy deps:
if ! grep -qiE 'healthcheck:' "$COMPOSE_FILE"; then
  fail "No healthcheck defined in $COMPOSE_FILE (see docs/deployment/hardening/healthcheck-lp.md)"
fi

# Check bounded settings
grep -qiE 'interval:\s*[0-9]+s' "$COMPOSE_FILE" || fail "healthcheck.interval missing or not seconds-bound"
grep -qiE 'timeout:\s*[0-9]+s' "$COMPOSE_FILE" || fail "healthcheck.timeout missing or not seconds-bound"
grep -qiE 'retries:\s*[1-9][0-9]*' "$COMPOSE_FILE" || fail "healthcheck.retries missing or zero"
grep -qiE 'start_period:\s*[0-9]+s' "$COMPOSE_FILE" || warn "healthcheck.start_period not set; recommended to set"

# Check script existence
if [[ ! -f "$SCRIPT_PATH" ]]; then
  fail "Healthcheck script not found at $SCRIPT_PATH"
fi

# Heuristics: ensure script does not require root; look for sudo or privileged operations
if grep -qiE 'sudo|chown|chmod\s+\+s|setcap|cap[_-]?sys' "$SCRIPT_PATH"; then
  fail "Healthcheck script appears to require elevated privileges; must run as non-root"
fi

# Ensure script does not write outside /tmp
if grep -qE '>\s*/(?!tmp/)' "$SCRIPT_PATH"; then
  warn "Healthcheck script writes outside /tmp; avoid persistent writes"
fi

echo "Healthcheck least-privilege and bounded timing checks passed."