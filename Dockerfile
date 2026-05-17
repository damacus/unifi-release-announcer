# Multi-stage build for minimal final image
FROM python:3.14-alpine@sha256:5a824eb82cc75361f98611f3cfc5091ea33f10a6ccea4d4ebdabbc523b9a1614 AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    && rm -rf /var/cache/apk/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest@sha256:841c8e6fe30a8b07b4478d12d0c608cba6de66102d29d65d1cc423af86051563 /uv /uvx /bin/

# Create virtual environment and install dependencies
COPY pyproject.toml uv.lock ./
RUN uv venv && uv sync --no-dev

# Runtime stage
FROM python:3.14-alpine@sha256:5a824eb82cc75361f98611f3cfc5091ea33f10a6ccea4d4ebdabbc523b9a1614 AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-root user with explicit UID/GID 1000
RUN addgroup -S -g 1000 appgroup && \
    adduser -S -u 1000 appuser -G appgroup

# Copy virtual environment from builder
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv

# Set the path to include the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Copy application files
COPY --chown=appuser:appgroup scraper_backends/ /app/scraper_backends/
COPY --chown=appuser:appgroup main.py /app/main.py
COPY --chown=appuser:appgroup scraper_interface.py /app/scraper_interface.py

# Switch to non-root user
USER appuser

CMD ["python", "main.py"]
