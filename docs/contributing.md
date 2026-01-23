# Contributing

Thank you for your interest in contributing to the UniFi Release Announcer! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.13
- [uv](https://github.com/astral-sh/uv) package manager
- [Task](https://taskfile.dev/) task runner
- Docker and Docker Compose (for container testing)

### Getting Started

1. **Fork and clone the repository**:

   ```bash
   git clone https://github.com/YOUR_USERNAME/unifi-release-announcer.git
   cd unifi-release-announcer
   ```

2. **Install development dependencies**:

   ```bash
   task dev-install
   ```

3. **Set up environment variables**:

   Create a `.env` file:
   ```env
   DISCORD_BOT_TOKEN=your_test_bot_token
   DISCORD_CHANNEL_ID=your_test_channel_id
   SCRAPER_BACKEND=graphql
   TAGS=unifi-protect
   ```

4. **Run tests to verify setup**:

   ```bash
   task test
   ```

## Development Workflow

### Using Taskfile

This project uses [Taskfile](https://taskfile.dev/) for common development tasks:

```bash
# Show all available tasks
task

# Install dependencies
task dev-install

# Run tests
task test

# Run tests with coverage
task test-cov

# Run linting
task lint

# Auto-fix linting issues
task lint-fix

# Format code
task format

# Type checking
task type-check

# Run all checks
task check

# Run the application
task run

# Build Docker image
task build

# Run in Docker
task docker-run

# Clean cache files
task clean

# Pre-commit checks (format, lint, test)
task pre-commit

# CI pipeline (test-cov, lint, type-check)
task ci
```

### Code Quality

We maintain high code quality standards:

- **Linting**: Using [Ruff](https://github.com/astral-sh/ruff)
- **Type Checking**: Using [MyPy](https://mypy-lang.org/)
- **Testing**: Using [Pytest](https://pytest.org/)
- **Code Coverage**: Aiming for high test coverage

Before submitting a PR, run:

```bash
task pre-commit
```

This will:
1. Format your code
2. Fix linting issues
3. Run all tests

## Project Structure

```
.
├── main.py                     # Main Discord bot application
├── scraper_interface.py        # Scraper backend interface and factory
├── scraper_backends/           # Scraper backend implementations
│   ├── graphql_backend.py     # GraphQL API backend
│   └── rss_backend.py         # RSS feed backend
├── release_parser.py           # Release data parsing utilities
├── state_manager.py            # State persistence management
├── tests/                      # Test files
│   ├── test_graphql_backend.py
│   ├── test_rss_backend.py
│   ├── test_scraper_interface.py
│   └── test_integration.py
├── docs/                       # MkDocs documentation
├── k8s/                        # Kubernetes manifests
├── pyproject.toml              # Project dependencies and config
├── Taskfile.yml                # Task definitions
├── docker-compose.yml          # Docker Compose configuration
└── Dockerfile                  # Container image definition
```

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

Use descriptive branch names:
- `feature/` for new features
- `fix/` for bug fixes
- `docs/` for documentation changes
- `refactor/` for code refactoring

### 2. Make Your Changes

- Write clear, concise code
- Follow existing code style
- Add type hints to all functions
- Write docstrings for public functions and classes

### 3. Add Tests

All new features and bug fixes should include tests:

```python
# tests/test_your_feature.py
import pytest
from your_module import your_function

def test_your_function():
    """Test that your_function works correctly."""
    result = your_function("input")
    assert result == "expected_output"
```

Run tests:
```bash
task test
```

### 4. Update Documentation

If your change affects usage:
- Update relevant documentation in `docs/`
- Update the README.md if needed
- Add examples if appropriate

### 5. Run Quality Checks

Before committing:

```bash
# Run all pre-commit checks
task pre-commit

# Or run individually
task format      # Format code
task lint-fix    # Fix linting issues
task type-check  # Check types
task test        # Run tests
```

### 6. Commit Your Changes

Write clear commit messages:

```bash
git add .
git commit -m "feat: add support for new tag filtering"
```

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test changes
- `refactor:` for code refactoring
- `chore:` for maintenance tasks

### 7. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear description of changes
- Link to any related issues
- Screenshots (if UI changes)
- Test results

## Testing

### Running Tests

```bash
# Run all tests
task test

# Run with coverage
task test-cov

# Run specific test file
uv run pytest tests/test_graphql_backend.py -v

# Run specific test
uv run pytest tests/test_graphql_backend.py::test_get_latest_release -v
```

### Writing Tests

We use pytest for testing. Example test structure:

```python
import pytest
from unittest.mock import Mock, patch

def test_feature():
    """Test description."""
    # Arrange
    input_data = "test"
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected_output

@pytest.mark.asyncio
async def test_async_feature():
    """Test async function."""
    result = await async_function()
    assert result is not None
```

### Mocking External Services

Use `respx` for HTTP mocking and `unittest.mock` for other mocks:

```python
import respx
from httpx import Response

@respx.mock
def test_api_call():
    """Test API call with mocked response."""
    respx.post("https://api.example.com").mock(
        return_value=Response(200, json={"status": "ok"})
    )
    
    result = make_api_call()
    assert result["status"] == "ok"
```

## Adding New Features

### Adding a New Scraper Backend

1. Create a new file in `scraper_backends/`:

```python
# scraper_backends/new_backend.py
from scraper_interface import ScraperInterface

class NewBackend(ScraperInterface):
    """New scraper backend implementation."""
    
    def get_latest_release(self) -> dict:
        """Fetch the latest release."""
        # Implementation
        pass
```

2. Register in `scraper_interface.py`:

```python
def create_scraper(backend: str = "graphql") -> ScraperInterface:
    """Factory function to create scraper instances."""
    if backend == "new":
        from scraper_backends.new_backend import NewBackend
        return NewBackend()
    # ... existing backends
```

3. Add tests:

```python
# tests/test_new_backend.py
from scraper_backends.new_backend import NewBackend

def test_new_backend():
    """Test new backend."""
    backend = NewBackend()
    release = backend.get_latest_release()
    assert release is not None
```

### Adding New Configuration Options

1. Add to environment variables in `main.py`
2. Update documentation in `docs/configuration.md`
3. Update `docker-compose.yml` and `k8s/deployment.yaml`
4. Add tests for the new configuration

## Documentation

### Building Documentation Locally

```bash
# Install mkdocs if not already installed
task dev-install

# Serve documentation locally
mkdocs serve
```

Then visit http://127.0.0.1:8000

### Documentation Style

- Use clear, concise language
- Include code examples
- Add screenshots where helpful
- Use admonitions for warnings/notes:

```markdown
!!! warning "Important"
    This is a warning message.

!!! note
    This is a note.

!!! tip
    This is a helpful tip.
```

## Release Process

Releases are automated using [Release Please](https://github.com/googleapis/release-please):

1. Merge PRs to main
2. Release Please creates a release PR
3. Merge the release PR to trigger a release
4. GitHub Actions builds and publishes the Docker image

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Help others learn and grow
- Follow the project's coding standards

## Getting Help

- **Questions**: Open a discussion on GitHub
- **Bugs**: Open an issue with reproduction steps
- **Features**: Open an issue to discuss before implementing
- **Security**: Email maintainers directly (see README)

## Recognition

Contributors will be recognized in:
- CHANGELOG.md
- GitHub contributors page
- Release notes

Thank you for contributing! 🎉
