# Multi-stage build for minimal final image
FROM python:3.14-alpine@sha256:26730869004e2b9c4b9ad09cab8625e81d256d1ce97e72df5520e806b1709f92 AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    && rm -rf /var/cache/apk/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest@sha256:3d868e555f8f1dbc324afa005066cd11e1053fc4743b9808ca8025283e65efa5 /uv /uvx /bin/

# Create virtual environment and install dependencies
COPY pyproject.toml uv.lock ./
RUN uv venv && uv sync --no-dev

# Runtime stage
FROM python:3.14-alpine@sha256:26730869004e2b9c4b9ad09cab8625e81d256d1ce97e72df5520e806b1709f92 AS runtime

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
