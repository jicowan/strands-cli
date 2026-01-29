# Technology Stack

## Core Technologies

- **Python 3.8+**: Primary language with type hints and modern Python features
- **Click**: CLI framework for command-line interface with rich console output
- **Jinja2**: Template engine for code generation and configuration files
- **Docker**: Containerization with multi-architecture build support
- **Kubernetes/Helm**: Deployment orchestration and package management
- **FastAPI**: Web framework for agent API wrappers
- **Streamlit**: UI framework for local testing interface

## Key Dependencies

```toml
# Core dependencies
click>=8.1.0          # CLI framework
jinja2>=3.0.0         # Template engine
pyyaml>=6.0           # YAML processing
rich>=12.0.0          # Console formatting
docker>=6.0.0         # Docker SDK

# Development dependencies
pytest>=7.0.0         # Testing framework
black>=23.0.0         # Code formatting
isort>=5.0.0          # Import sorting
mypy>=1.0.0           # Type checking
ruff>=0.0.85          # Linting
```

## Build System

- **Build Backend**: Hatchling (modern Python packaging)
- **Package Manager**: pip with optional development dependencies
- **Version Management**: Makefile-based semantic versioning

## Development Environment

**Always use a virtual environment for local development and testing.**
**Always use `python3` instead of `python` for Python commands.**
**For testing PostgreSQL, always run PostgreSQL as a container.**

## Common Commands

```bash
# Virtual environment setup (REQUIRED)
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate   # On Windows

# Development setup (after activating venv)
pip install -e ".[dev]"

# Building and versioning
make build              # Build package (patch increment)
make patch             # Patch version increment
make minor             # Minor version increment  
make major             # Major version increment
make release           # Build and create git tag

# Testing
pytest                 # Run test suite
pytest tests/test_cli.py  # Run specific test file

# Code quality
black .                # Format code
isort .                # Sort imports
mypy src/              # Type checking
ruff check src/        # Linting

# PostgreSQL testing (containerized)
docker run --name postgres-test -e POSTGRES_PASSWORD=testpass -e POSTGRES_DB=testdb -p 5432:5432 -d postgres:15
docker stop postgres-test     # Stop test database
docker rm postgres-test       # Remove test container
```

## Architecture Patterns

- **Command Pattern**: Each CLI command is a separate module in `commands/`
- **Template-Based Generation**: Jinja2 templates for all generated code and configs
- **Factory Pattern**: Agent creation through factory functions
- **Dependency Injection**: Context variables passed to templates
- **Error Handling**: Rich console output with graceful error messages