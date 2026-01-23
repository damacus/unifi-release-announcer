# Multi-stage build for minimal final image
FROM python:3.14-alpine@sha256:7af51ebeb83610fb69d633d5c61a2efb87efa4caf66b59862d624bb6ef788345 AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    && rm -rf /var/cache/apk/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest@sha256:9a23023be68b2ed09750ae636228e903a54a05ea56ed03a934d00fe9fbeded4b /uv /uvx /bin/

# Create virtual environment and install dependencies
COPY pyproject.toml uv.lock ./
RUN uv venv && uv sync --no-dev

# Runtime stage
FROM python:3.14-alpine@sha256:7af51ebeb83610fb69d633d5c61a2efb87efa4caf66b59862d624bb6ef788345 AS runtime

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
