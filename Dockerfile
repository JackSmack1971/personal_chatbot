# syntax=docker/dockerfile:1.7
# Multi-stage Dockerfile for personal_chatbot (Python 3.11)
# Principles:
# - Minimal, deterministic, non-root
# - Logs to stdout/stderr
# - Healthcheck via lightweight Python module call
# - Only writable dirs: /app/personal_chatbot/uploads and /app/personal_chatbot/exports

ARG PYTHON_VERSION=3.11-slim

FROM python:${PYTHON_VERSION} AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System dependencies kept minimal; add build deps only if needed in a separate stage
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    ca-certificates curl tini \
 && rm -rf /var/lib/apt/lists/*

# Copy requirement files first for better layer caching
COPY personal_chatbot/requirements.txt ./personal_chatbot/requirements.txt

# Install dependencies into a venv to keep global clean (optional)
RUN python -m venv /opt/venv && . /opt/venv/bin/activate \
 && pip install --upgrade pip \
 && pip install -r personal_chatbot/requirements.txt

ENV PATH="/opt/venv/bin:${PATH}"

# Copy application code
COPY personal_chatbot/ ./personal_chatbot/
COPY tests/ ./tests/
COPY README.md ./

# Create non-root user and set ownership
RUN groupadd -r appuser && useradd -r -g appuser -s /usr/sbin/nologin appuser \
 && mkdir -p /app/personal_chatbot/uploads /app/personal_chatbot/exports \
 && chown -R appuser:appuser /app

# Entrypoint script to ensure runtime dirs and print safe env summary
COPY personal_chatbot/setup/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

USER appuser

# Default environment (can be overridden at runtime)
ENV LOG_LEVEL=INFO

# Healthcheck: use external shell script to avoid modifying app code in this mode
COPY scripts/healthcheck.sh /app/scripts/healthcheck.sh
RUN chmod +x /app/scripts/healthcheck.sh
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=10s \
 CMD sh /app/scripts/healthcheck.sh

ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["./entrypoint.sh"]