# Multi-stage build for minimal final image
FROM python:3.13-alpine@sha256:9ba6d8cbebf0fb6546ae71f2a1c14f6ffd2fdab83af7fa5669734ef30ad48844 AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    && rm -rf /var/cache/apk/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest@sha256:e4644cb5bd56fdc2c5ea3ee0525d9d21eed1603bccd6a21f887a938be7e85be1 /uv /uvx /bin/

# Create virtual environment and install dependencies
COPY pyproject.toml uv.lock ./
RUN uv venv && uv sync --no-dev

# Runtime stage
FROM python:3.13-alpine@sha256:9ba6d8cbebf0fb6546ae71f2a1c14f6ffd2fdab83af7fa5669734ef30ad48844 AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Set the path to include the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Copy application files
COPY scraper_backends/ /app/scraper_backends/
COPY main.py /app/main.py
COPY scraper_interface.py /app/scraper_interface.py
COPY state_manager.py /app/state_manager.py

CMD ["python", "main.py"]
