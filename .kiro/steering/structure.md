# Project Structure

## Repository Organization

```
strands-cli/
├── src/strands_cli/           # Main package source
│   ├── __init__.py           # Package version and exports
│   ├── cli.py                # Main CLI entry point with Click commands
│   ├── commands/             # Individual command implementations
│   │   ├── init.py          # Project initialization
│   │   ├── build.py         # Docker image building
│   │   ├── generate.py      # Deployment asset generation
│   │   ├── run.py           # Local development environment
│   │   └── pod_identity.py  # AWS Pod Identity setup
│   ├── templates/           # Jinja2 templates for code generation
│   │   ├── default/         # Default project template
│   │   │   ├── agent/       # Agent code templates
│   │   │   ├── api/         # FastAPI wrapper templates
│   │   │   ├── docker/      # Container configuration
│   │   │   ├── helm/        # Helm chart templates
│   │   │   ├── k8s/         # Kubernetes manifest templates
│   │   │   ├── root/        # Project root files
│   │   │   └── scripts/     # Utility script templates
│   │   ├── docker-compose/ # Docker Compose templates
│   │   └── ui/              # Streamlit UI templates
│   └── utils/               # Shared utilities
│       ├── docker.py        # Docker operations
│       ├── helm.py          # Helm chart utilities
│       └── template.py      # Template rendering
├── tests/                   # Test suite
│   ├── test_cli.py         # CLI command tests
│   ├── test_commands/      # Command-specific tests
│   └── test_utils/         # Utility function tests
├── pyproject.toml          # Python project configuration
├── Makefile               # Build and version management
└── README.md              # User documentation
```

## Generated Project Structure

When `strands-cli init` creates a new project:

```
[agent-name]/
├── README.md              # Project documentation
├── pyproject.toml        # Python dependencies and config
├── agent/                # Core agent implementation
│   ├── __init__.py
│   ├── agent.py         # Main agent logic with factory function
│   ├── tools.py         # Custom agent tools
│   └── prompts.py       # System prompts and templates
├── api/                  # FastAPI wrapper for agent
│   ├── __init__.py
│   ├── app.py           # FastAPI application setup
│   ├── models.py        # Pydantic request/response models
│   └── routes.py        # API endpoint definitions
├── deployment/           # Container and deployment configs
│   └── docker/
│       ├── Dockerfile   # Multi-stage container build
│       └── requirements.txt
└── scripts/             # Utility scripts (executable)
    ├── build.sh         # Docker build script
    ├── push.sh          # Registry push script
    └── deploy.sh        # Deployment script
```

## Naming Conventions

- **Package Names**: snake_case (e.g., `strands_cli`)
- **Module Names**: snake_case (e.g., `pod_identity.py`)
- **Class Names**: PascalCase (e.g., `AgentBuilder`)
- **Function Names**: snake_case (e.g., `create_project`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `TEMPLATES_DIR`)
- **CLI Commands**: kebab-case (e.g., `create-pod-identity`)
- **Project Names**: kebab-case (e.g., `my-weather-agent`)

## File Organization Patterns

- **Commands**: Each CLI command has its own module in `commands/`
- **Templates**: Organized by category (agent, api, docker, helm, k8s)
- **Tests**: Mirror the source structure with `test_` prefix
- **Utilities**: Shared functionality in `utils/` with focused modules
- **Configuration**: Single `pyproject.toml` for all Python project settings

## Template Context Variables

Standard variables passed to all Jinja2 templates:

- `name`: Project name (kebab-case)
- `description`: Project description
- `package_name`: Python package name (snake_case)
- `class_name`: Python class name (PascalCase)

## Import Patterns

- **Lazy Imports**: Commands import their dependencies inside functions to avoid circular imports
- **Relative Imports**: Use relative imports within the package
- **External Dependencies**: Import at module level for utilities, inside functions for commands