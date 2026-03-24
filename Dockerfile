# Multi-stage build for minimal final image
FROM python:3.14-alpine@sha256:faee120f7885a06fcc9677922331391fa690d911c020abb9e8025ff3d908e510 AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    && rm -rf /var/cache/apk/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest@sha256:72ab0aeb448090480ccabb99fb5f52b0dc3c71923bffb5e2e26517a1c27b7fec /uv /uvx /bin/

# Create virtual environment and install dependencies
COPY pyproject.toml uv.lock ./
RUN uv venv && uv sync --no-dev

# Runtime stage
FROM python:3.14-alpine@sha256:faee120f7885a06fcc9677922331391fa690d911c020abb9e8025ff3d908e510 AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-root user and set up cache directory
RUN addgroup -S appgroup && \
    adduser -S appuser -G appgroup && \
    mkdir /cache && \
    chown appuser:appgroup /cache

# Copy virtual environment from builder
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv

# Set the path to include the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Copy application files
COPY --chown=appuser:appgroup scraper_backends/ /app/scraper_backends/
COPY --chown=appuser:appgroup main.py /app/main.py
COPY --chown=appuser:appgroup scraper_interface.py /app/scraper_interface.py
COPY --chown=appuser:appgroup state_manager.py /app/state_manager.py

# Switch to non-root user
USER appuser

CMD ["python", "main.py"]
