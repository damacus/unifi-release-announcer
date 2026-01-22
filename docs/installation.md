# Installation

## Prerequisites

- Python 3.13
- Discord Bot Token
- Discord Channel ID where announcements will be posted

## Local Development

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd unifi-release-announcer
   ```

2. **Install dependencies using uv**:

   ```bash
   uv sync --extra dev
   ```

3. **Configure environment variables**:

   Create a `.env` file in the project root:

   ```env
   DISCORD_BOT_TOKEN=your_discord_bot_token
   DISCORD_CHANNEL_ID=your_discord_channel_id
   SCRAPER_BACKEND=graphql  # or 'rss' if you prefer
   ```

4. **Run the application**:

   ```bash
   uv run main.py
   ```

## Docker Development

1. **Build the Docker image**:

   ```bash
   docker compose build
   ```

2. **Run the container**:

   ```bash
   docker compose run announcer
   ```

## Dev Container (Recommended for Development)

For the best development experience, use the provided dev container configuration:

1. **Prerequisites**:
   - VS Code with the Dev Containers extension
   - Docker Desktop

2. **Open in Dev Container**:
   - Open the project in VS Code
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Select "Dev Containers: Reopen in Container"
   - Wait for the container to build and start

3. **Features included**:
   - Pre-configured Python environment with all dependencies
   - GraphQL API support
   - Python extensions (Black, Ruff, MyPy, Pytest)
   - Volume mounts for live code editing
   - Automatic dependency installation
