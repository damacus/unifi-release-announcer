FROM mcr.microsoft.com/devcontainers/python:dev-3.13-trixie@sha256:246e64cc27365c35e40f203097d0a7e180d771a69ff16f7b5b3e67128688a145

# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1
# ENV DEVCONTAINER=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest@sha256:99ea34acedc870ba4ad11a1f540a1c04267c9f30aadc465a94406f52dfda2c36 /uv /uvx /bin/

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
