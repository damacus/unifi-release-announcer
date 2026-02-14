FROM mcr.microsoft.com/devcontainers/python:dev-3.13-trixie@sha256:c24c48c4992bb19de9680ee49b2a4da2b20724c58a9de7195b7f693a94494874

# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1
# ENV DEVCONTAINER=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest@sha256:94a23af2d50e97b87b522d3cea24aaf8a1faedec1344c952767434f69585cbf9 /uv /uvx /bin/

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
