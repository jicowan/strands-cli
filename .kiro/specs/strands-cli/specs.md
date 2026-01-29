# Strands CLI Tool Specifications

## Overview

The Strands CLI Tool is a command-line utility designed to streamline the development and deployment of Strands agents to Amazon EKS. It provides a standardized project structure, boilerplate code generation, and deployment manifests to accelerate the process of building and deploying Strands agents.

## Objectives

- Create a standardized project structure for Python-based Strands agents
- Generate boilerplate code for Strands agents with FastAPI wrappers
- Produce Docker configurations for containerization
- Generate Kubernetes manifests and/or Helm charts for EKS deployment
- Provide deployment guidance and scripts for various environments

## CLI Features and Commands

### Core Commands

| Command | Description | Options |
|---------|-------------|---------|
| `init` | Initialize a new Strands agent project | `--name`, `--description`, `--template` |
| `build` | Build Docker image for the agent | `--push`, `--registry`, `--tag` |
| `generate helm` | Generate Helm chart for deployment | `--set key=value`, `--values-file` |
| `generate k8s` | Generate raw Kubernetes manifests | `--namespace`, `--output-dir` |

### Command Details

#### `init`
- Creates project directory structure
- Generates boilerplate agent code
- Creates FastAPI wrapper with streaming and non-streaming endpoints
- Adds Docker configuration files
- Sets up deployment directory

#### `build`
- Builds Docker image using the provided Dockerfile
- Optionally pushes to a container registry
- Supports tagging and versioning

#### `generate helm`
- Generates a complete Helm chart in the deployment directory
- Customizable through command-line values or values files
- Creates environment-specific values files (dev, prod)

#### `generate k8s`
- Generates raw Kubernetes manifests as an alternative to Helm
- Customizable through command-line parameters
- Creates properly namespaced resources

## Project Structure

The CLI will generate the following project structure:

```
[agent_name]/
├── README.md                  # Project documentation with deployment instructions
├── pyproject.toml
├── agent/
│   ├── __init__.py
│   ├── agent.py               # Strands agent implementation
│   ├── tools.py               # Custom tools for the agent
│   └── prompts.py             # System prompts
├── api/
│   ├── __init__.py
│   ├── app.py                 # FastAPI wrapper
│   ├── models.py              # Pydantic models
│   └── routes.py              # API routes
├── deployment/
│   ├── docker/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── helm/                  # Helm chart for deployment
│   │   ├── Chart.yaml
│   │   ├── values.yaml
│   │   ├── values-dev.yaml    # Environment-specific values
│   │   ├── values-prod.yaml   # Environment-specific values
│   │   └── templates/         # Helm templates
│   │       ├── _helpers.tpl
│   │       ├── deployment.yaml
│   │       ├── service.yaml
│   │       ├── serviceaccount.yaml
│   │       ├── ingress.yaml
│   │       └── poddisruptionbudget.yaml
│   └── k8s/                   # Raw K8s manifests (alternative to Helm)
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── serviceaccount.yaml
│       ├── ingress.yaml
│       └── poddisruptionbudget.yaml
└── scripts/
    ├── build.sh               # Build Docker image
    ├── push.sh                # Push to registry
    └── deploy.sh              # Instructions for deploying using kubectl or helm
```

## Template Specifications

### Agent Templates

The agent code will use the Strands Agents SDK and implement:
- Configurable system prompt
- Custom tool registration
- Proper error handling
- Optional streaming capabilities

### FastAPI Wrapper

The FastAPI wrapper will include:
- Health check endpoint for load balancer probes
- Standard request endpoint for agent interactions
- Streaming endpoint for incremental responses
- Proper error handling and status codes
- Configurable through environment variables
- Pydantic models for request/response validation

### Docker Configuration

The Dockerfile will:
- Use Python 3.12-slim base image from AWS ECR
- Install necessary system dependencies
- Set up proper Python environment
- Run as non-root user for security
- Configure for multi-worker Uvicorn
- Include best practices for container security

### Kubernetes Deployments

The Kubernetes manifests/Helm chart will include:
- Deployment with configurable replicas
- Service for internal communication
- ServiceAccount for IAM role binding
- Ingress/ALB configuration
- PodDisruptionBudget for high availability
- Resource requests/limits
- Health and readiness probes

## Deployment Options

### Helm Deployment

The generated Helm chart will support:
- Customization through values files
- Environment-specific configurations
- AWS-specific annotations for ALB integration
- Horizontal Pod Autoscaling
- Topology spread constraints for high availability

### Raw Manifest Deployment

The raw Kubernetes manifests will:
- Be directly applicable via kubectl
- Support environment variable substitution
- Include necessary resources for EKS deployment
- Support AWS Load Balancer Controller integration

## Requirements and Dependencies

### CLI Tool Dependencies
- Python 3.8+
- Click/Typer for CLI interface
- Jinja2 for templating
- PyYAML for configuration parsing
- Docker SDK for Python (optional for build command)

### Generated Project Dependencies
- Python 3.8+
- Strands Agents SDK
- FastAPI
- Uvicorn
- Pydantic
- Environment-specific dependencies based on agent functionality

## Extensibility

The CLI tool will support:
- Custom agent templates
- Pluggable deployment targets
- Extension through hooks or plugins
- CI/CD integration templates

## Future Considerations

- Support for additional deployment targets beyond EKS
- Integration with AWS CDK for infrastructure as code
- Built-in monitoring and observability setup
- Multi-agent deployment orchestration
- Support for specialized agent types and configurations

## Security Considerations

- Non-root container execution
- Principle of least privilege for service accounts
- Network policy templates
- Secrets management guidance
- Resource isolation and constraints