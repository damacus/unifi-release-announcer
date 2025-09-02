FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv by copying the binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install system dependencies, create virtual environment, and install packages
COPY pyproject.toml uv.lock ./
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/* \
    && uv venv \
    && uv sync \
    && /app/.venv/bin/playwright install --with-deps chromium

# Set the path to include the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

COPY scraper_backends/ /app/scraper_backends/
COPY main.py /app/main.py
COPY scraper_interface.py /app/scraper_interface.py

# Set environment variables
ENV SCRAPER_BACKEND=playwright

CMD ["uv", "run", "main.py"]
