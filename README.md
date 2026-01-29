# Strands CLI Tool

A command-line utility for generating and deploying Strands agents to Amazon EKS.

## Features

- Create a standardized project structure for Python-based Strands agents
- Generate boilerplate code for Strands agents with FastAPI wrappers
- Produce Docker configurations for containerization
- Generate Kubernetes manifests and/or Helm charts for EKS deployment
- Provide deployment guidance and scripts for various environments

## Installation

```bash
pip install strands-cli
```

For development:
```bash
git clone https://github.com/yourusername/strands-cli.git
cd strands-cli
pip install -e ".[dev]"
```

## Usage

### Initialize a New Strands Agent Project

```bash
strands-cli init my-weather-agent --description "Weather forecast agent"
```

This command creates a project skeleton with the core directories and files needed for agent development (agent code, API wrapper, Docker configuration). It **does not** create any deployment directories or files. Deployment assets for Helm and Kubernetes are only generated when you explicitly run the respective `generate` commands.

### Build Docker Image

```bash
cd my-weather-agent
strands-cli build --push
```

### Run Locally with Streamlit UI

Test your agent locally with an interactive chat UI before deploying:

```bash
cd my-weather-agent
strands-cli run
```

This will:
- Build your agent image (if needed)
- Start your agent in a container
- Launch a Streamlit UI for interactive testing

You can access the UI at http://localhost:8501 and the agent API at http://localhost:8000.

> **Important for Docker Desktop users (macOS/Windows)**: You need to enable file sharing for your home directory to allow AWS credentials access. Go to Docker Desktop → Settings → Resources → File Sharing and add your home directory (e.g., `/Users/username`) to the list of shared folders. The agent container will mount your local `.aws` directory to `/home/appuser/.aws` inside the container.

Options:
```bash
# Custom ports
strands-cli run --port 3000 --agent-port 8080

# Run without UI (headless mode)
strands-cli run --no-ui

# Run in background
strands-cli run --detach

# Use an existing image instead of building locally
strands-cli run --image-uri registry/name:tag

# Specify AWS profile for credentials
strands-cli run --aws-profile myprofile
```

### Generate Deployment Assets

After building your Docker image, you need to explicitly generate all deployment assets:

#### Generate Helm Chart

```bash
# Using set values
strands-cli generate helm --set image.repository=my-registry/my-weather-agent --set image.tag=latest

# Using direct flags (recommended)
strands-cli generate helm --image-uri my-registry/my-weather-agent --image-tag latest --service-account my-bedrock-sa
```

This command generates all necessary Helm files, including:
- Chart.yaml file
- Helm template files (deployment.yaml, service.yaml, etc.)
- values.yaml with your configuration
- VALUES.md documentation

#### Generate Raw Kubernetes Manifests

```bash
# Basic usage
strands-cli generate k8s --namespace my-agents

# With image and service account configuration
strands-cli generate k8s --namespace my-agents \
  --image-uri my-registry/my-weather-agent \
  --image-tag latest \
  --service-account my-bedrock-sa
```

> **Note:** All deployment assets are only generated when you explicitly run the `generate` commands. This allows you to include specific parameters like image URIs and service account names.

### Create Pod Identity for AWS Bedrock Access

```bash
strands-cli create-pod-identity my-bedrock-sa arn:aws:iam::aws:policy/AmazonBedrockFullAccess --namespace my-agents
```

## Documentation

For detailed documentation, see the [SPECIFICATIONS.md](./SPECIFICATIONS.md) file.

## License

MIT