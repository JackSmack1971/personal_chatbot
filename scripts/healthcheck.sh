#!/usr/bin/env sh
# Lightweight container healthcheck without modifying app code.
# Checks:
# 1) Python import of critical modules
# 2) Required runtime directories exist and are writable
# 3) Environment configuration presence (API key presence, model fallback)

set -eu

fail() {
  echo "[health] FAIL: $1" >&2
  exit 1
}

ok() {
  echo "[health] OK: $1"
}

# 1) Python import sanity (modules should import without side effects)
python - <<'PYCODE' || fail "Python import of core modules failed"
import importlib, sys
mods = [
  "personal_chatbot.main",
  "personal_chatbot.src.utils",
  "personal_chatbot.src.file_handler",
  "personal_chatbot.src.openrouter_client",
  "personal_chatbot.src.memory_manager",
]
for m in mods:
  importlib.import_module(m)
print("imports-ok")
PYCODE
ok "Python modules import"

# 2) Runtime directories
for d in /app/personal_chatbot/uploads /app/personal_chatbot/exports; do
  [ -d "$d" ] || fail "Missing directory $d"
  # test write permission with a temp file
  touch "$d/.healthcheck_tmp" 2>/dev/null || fail "Cannot write to $d"
  rm -f "$d/.healthcheck_tmp" || true
done
ok "Runtime directories exist and are writable"

# 3) Env configuration presence
# API key can be in OPENROUTER_API_KEY or API_KEY; model can be in OPENROUTER_DEFAULT_MODEL or CHATBOT_DEFAULT_MODEL
API_KEY_VALUE="${OPENROUTER_API_KEY:-${API_KEY:-}}"
if [ -z "${API_KEY_VALUE}" ]; then
  echo "[health] WARN: API key not set (OPENROUTER_API_KEY or API_KEY). Functionality may be limited." >&2
fi

MODEL_VALUE="${OPENROUTER_DEFAULT_MODEL:-${CHATBOT_DEFAULT_MODEL:-openrouter/auto}}"
if [ -z "${MODEL_VALUE}" ]; then
  fail "No default model resolved"
fi
ok "Environment variables resolved (model=${MODEL_VALUE})"

exit 0