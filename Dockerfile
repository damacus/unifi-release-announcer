# Multi-stage build for minimal final image
FROM python:3.14-alpine@sha256:7c2135f3b4c04e61b8e42c8a3149f520b55b5543cda68f1b879d419727347772 AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    && rm -rf /var/cache/apk/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest@sha256:4c1ad814fe658851f50ff95ecd6948673fffddb0d7994bdb019dcb58227abd52 /uv /uvx /bin/

# Create virtual environment and install dependencies
COPY pyproject.toml uv.lock ./
RUN uv venv && uv sync --no-dev

# Runtime stage
FROM python:3.14-alpine@sha256:7c2135f3b4c04e61b8e42c8a3149f520b55b5543cda68f1b879d419727347772 AS runtime

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
