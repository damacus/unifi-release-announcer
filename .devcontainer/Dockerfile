FROM mcr.microsoft.com/devcontainers/python:dev-3.13-trixie@sha256:2d1ddf6df8b7f1d266eb5db3c6c641e67602d99b999383cbfe995970f829ae56

# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1
# ENV DEVCONTAINER=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest@sha256:5aa820129de0a600924f166aec9cb51613b15b68f1dcd2a02f31a500d2ede568 /uv /uvx /bin/

RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    procps \
    psmisc \
    git \
    vim \
    htop \
    tree \
    jq \
    dbus \
    network-manager \
    libpulse0 \
    xz-utils

COPY pyproject.toml uv.lock ./
RUN uv venv \
    && uv sync --extra dev \
    && /app/.venv/bin/playwright install --with-deps chromium

ENV PATH="/app/.venv/bin:$PATH"

CMD ["sleep", "infinity"]
