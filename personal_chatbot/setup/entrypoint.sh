#!/usr/bin/env sh
set -eu

# Ensure runtime directories exist and are writable
mkdir -p /app/personal_chatbot/uploads /app/personal_chatbot/exports

# Redacted env summary to stdout (operational visibility)
redact() {
  if [ -n "${1:-}" ]; then
    echo "***REDACTED***"
  else
    echo ""
  fi
}

echo "[startup] personal_chatbot container"
echo "[startup] LOG_LEVEL=${LOG_LEVEL:-INFO}"
echo "[startup] OPENROUTER_BASE_URL=${OPENROUTER_BASE_URL:-https://api.openrouter.ai}"
echo "[startup] OPENROUTER_DEFAULT_MODEL=${OPENROUTER_DEFAULT_MODEL:-}"
echo "[startup] CHATBOT_DEFAULT_MODEL=${CHATBOT_DEFAULT_MODEL:-openrouter/auto}"
# redact secrets
echo "[startup] OPENROUTER_API_KEY=$(redact "${OPENROUTER_API_KEY:-}")"
echo "[startup] API_KEY=$(redact "${API_KEY:-}")"

# Execute application (Python module entrypoint)
exec python -m personal_chatbot.main