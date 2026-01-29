# Getting Started with Strands CLI

This guide will help you get started with the Strands CLI tool for generating and deploying Strands agents to Amazon EKS.

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Docker (for building and testing locally)
- kubectl (for deploying to Kubernetes)
- Helm (optional, for Helm chart deployments)

### Installing the CLI

#### Option 1: Install from PyPI (when available)

```bash
pip install strands-cli
```

#### Option 2: Install from GitHub

Install directly from the GitHub repository:

```bash
pip install git+https://github.com/yourusername/strands-cli.git
```

#### Option 3: Install from local source

Clone the repository and install in development mode:

```bash
git clone https://github.com/yourusername/strands-cli.git
cd strands-cli
pip install -e .
```

For development with test dependencies:

```bash
pip install -e ".[dev]"
```

Verify the installation by checking the version:

```bash
strands-cli --version
```

## Basic Usage

### Creating a New Agent Project

Create a new Strands agent project with the `init` command:

```bash
strands-cli init my-weather-agent --description "Weather forecast agent"
```

This will create a new directory `my-weather-agent` with the following structure:

```
my-weather-agent/
├── README.md                  # Project documentation
├── agent/                     # Strands agent implementation
│   ├── __init__.py
│   ├── agent.py               # Agent code
│   ├── tools.py               # Custom tools
│   └── prompts.py             # System prompts
├── api/                       # FastAPI wrapper
│   ├── __init__.py
│   ├── app.py                 # FastAPI application
│   ├── models.py              # Pydantic models
│   └── routes.py              # API endpoints
├── deployment/                # Deployment configurations
│   └── docker/                # Docker configuration
│       ├── Dockerfile
│       └── requirements.txt
└── scripts/                   # Utility scripts
    ├── build.sh
    ├── push.sh
    └── deploy.sh
```

> **Important:** The `init` command only creates the core directories and files needed for agent development. It does not create any deployment directories or files for Helm or Kubernetes.
>
> Use these commands to generate deployment assets when you're ready to deploy:
> - `strands-cli generate helm` - Creates the `deployment/helm` directory with all necessary Helm chart files
> - `strands-cli generate k8s` - Creates the `deployment/k8s` directory with all necessary Kubernetes manifest files

### Customizing Your Agent

1. Navigate to your new project directory:

```bash
cd my-weather-agent
```

2. Customize the agent's system prompt in `agent/prompts.py`.

3. Implement any custom tools in `agent/tools.py`.

4. Modify the FastAPI wrapper in `api/app.py` if needed.

### Building the Docker Image

Build a Docker image for your agent:

```bash
strands-cli build
```

To build and push to a registry:

```bash
strands-cli build --push --registry your-registry --tag v1.0
```

### Testing Locally with Streamlit UI

Test your agent locally with an interactive chat UI before deploying to production:

```bash
strands-cli run
```

This command will:
- Build your agent Docker image if needed
- Start your agent in a container
- Launch a Streamlit UI container that connects to your agent
- Set up a network for the containers to communicate

You can access:
- Streamlit UI: http://localhost:8501
- Agent API: http://localhost:8000

#### Docker Desktop Configuration

**Important:** If you're using Docker Desktop on macOS or Windows, you need to configure file sharing to allow the container to access your AWS credentials:

1. Open Docker Desktop
2. Go to Settings → Resources → File Sharing
3. Add your home directory to the list of shared folders (e.g., `/Users/username` on macOS or `C:\Users\username` on Windows)
4. Click "Apply & Restart"

This step is necessary because the agent container mounts your local AWS credentials directory to `/home/appuser/.aws` to authenticate with AWS services.

#### Run Command Options

```bash
# Custom ports
strands-cli run --port 3000 --agent-port 8080

# Run without UI (API only)
strands-cli run --no-ui

# Run in background (detached mode)
strands-cli run --detach

# Skip building the agent image
strands-cli run --build=false

# Use an existing image instead of building locally
strands-cli run --image-uri registry/name:tag

# Specify AWS profile for credentials
strands-cli run --aws-profile myprofile

# Set custom restart policy
strands-cli run --restart=no
```

When running in foreground mode, press Ctrl+C to gracefully stop the containers.

### Generating Deployment Assets

After customizing your agent and building the Docker image, you'll need to generate all deployment assets.
The `init` command does not create any deployment directories or files for Helm or Kubernetes. Instead, the `generate`
commands will create the necessary directories and files with your specific configuration parameters when you're ready to deploy.

#### Generate Helm Chart

Generate a complete Helm chart including all template files, Chart.yaml, and values:

```bash
# Using set values approach
strands-cli generate helm --set image.repository=your-registry/my-weather-agent --set image.tag=v1.0

# Using direct flags (recommended)
strands-cli generate helm --image-uri your-registry/my-weather-agent --image-tag v1.0
```

This command creates:
- The Chart.yaml file
- Helm template files in the templates/ directory
- The values.yaml file with your specified configuration
- VALUES.md documentation file

If your agent needs to access AWS Bedrock, you can specify a service account that will use pod identity:

```bash
strands-cli generate helm --image-uri your-registry/my-weather-agent --image-tag v1.0 --service-account bedrock-sa
```

#### Generate Kubernetes Manifests

Generate raw Kubernetes manifests:

```bash
# Basic usage
strands-cli generate k8s --namespace my-agents

# With image and service account configuration
strands-cli generate k8s --namespace my-agents \
  --image-uri your-registry/my-weather-agent \
  --image-tag v1.0 \
  --service-account bedrock-sa
```

This command creates the YAML manifest files directly in the k8s/ directory.

> **Note:** Both `generate helm` and `generate k8s` commands support the same flags for image and service account configuration.

### Creating Pod Identity for AWS Bedrock Access

To create an IAM role with pod identity trust policy and associate it with your service account:

```bash
strands-cli create-pod-identity bedrock-sa arn:aws:iam::aws:policy/AmazonBedrockFullAccess --namespace my-agents
```

This will:
1. Create an IAM role with pod identity trust policy
2. Attach the specified policy to the role
3. Create a pod identity association in your EKS cluster

### Deploying to Amazon EKS

Deploy using Helm:

```bash
helm upgrade --install my-weather-agent deployment/helm \
  --namespace my-agents \
  --create-namespace \
  --values deployment/helm/values-prod.yaml
```

Or deploy using kubectl:

```bash
# Set required environment variables
export IMAGE_REPOSITORY=your-registry/my-weather-agent
export IMAGE_TAG=v1.0
export INGRESS_HOST=your-agent.example.com

# Apply the manifests
kubectl apply -f deployment/k8s/ -n my-agents
```

## Command Reference

### `init`

Initialize a new Strands agent project.

```bash
strands-cli init NAME [OPTIONS]
```

Options:
- `--description`, `-d`: Short description of the agent
- `--template`, `-t`: Template to use (default: "default")
- `--output-dir`, `-o`: Directory where the project will be created (default: ".")

### `build`

Build a Docker image for the Strands agent.

```bash
strands-cli build [OPTIONS]
```

Options:
- `--push`: Push image to registry after building
- `--registry`, `-r`: Registry URL
- `--tag`, `-t`: Image tag (default: "latest")

### `generate helm`

Generate a Helm chart for deploying the Strands agent.

```bash
strands-cli generate helm [OPTIONS]
```

Options:
- `--set KEY=VALUE`: Set values (can specify multiple)
- `--values-file`, `-f`: Values file to use
- `--image-uri`: URI of the container image (e.g., your-registry/image-name)
- `--image-tag`: Tag of the container image (e.g., latest, v1.0)
- `--service-account`: Name of the service account to use with pod identity for AWS Bedrock access

### `generate k8s`

Generate raw Kubernetes manifests for deploying the Strands agent.

```bash
strands-cli generate k8s [OPTIONS]
```

Options:
- `--namespace`, `-n`: Kubernetes namespace (default: "default")
- `--output-dir`, `-o`: Output directory (default: "deployment/k8s")
- `--image-uri`: URI of the container image (e.g., your-registry/image-name)
- `--image-tag`: Tag of the container image (e.g., latest, v1.0)
- `--service-account`: Name of the service account to use with pod identity for AWS Bedrock access

### `run`

Run the Strands agent locally with a Streamlit UI for testing.

```bash
strands-cli run [OPTIONS]
```

Options:
- `--port`: Port to expose the UI (default: 8501)
- `--agent-port`: Port for the agent API (default: 8000)
- `--no-ui`: Run only the agent without UI (for headless testing)
- `--detach`: Run in background mode
- `--build`: Build the agent image before running (default: true)
- `--image-uri`: URI of an existing container image (e.g., registry/name:tag) to use instead of building
- `--aws-profile`: AWS profile to use for credentials
- `--restart`: Restart policy (default: "unless-stopped")

### `create-pod-identity`

Create an IAM role with pod identity trust policy and create a pod identity association in EKS.

```bash
strands-cli create-pod-identity SERVICE_ACCOUNT POLICY_ARN [OPTIONS]
```

Arguments:
- `SERVICE_ACCOUNT`: The name of the Kubernetes service account
- `POLICY_ARN`: The ARN of the policy to attach to the role

Options:
- `--cluster-name`: Name of the EKS cluster (default: uses current kubectl context)
- `--namespace`, `-n`: Kubernetes namespace for the service account (default: "default")
- `--role-name`: Name for the IAM role (default: eks-pod-identity-<service_account>)

## Example Workflow

Here's a complete workflow for creating and deploying a Strands agent:

```bash
# Step 1: Create a new project (creates directory structure only, no deployment assets)
strands-cli init my-weather-agent --description "Weather forecast agent"
cd my-weather-agent

# Step 2: Customize your agent (edit files as needed)
# ... modify agent/prompts.py, agent/tools.py, etc. ...

# Step 3: Build and push the Docker image
strands-cli build --push --registry your-registry --tag v1.0

# Step 4: Test locally with Streamlit UI
strands-cli run

# Step 5: Generate the deployment assets
# Option A: Generate Helm chart with service account for Bedrock access
strands-cli generate helm --image-uri your-registry/my-weather-agent --image-tag v1.0 --service-account bedrock-sa

# Option B: Or generate Kubernetes manifests (if not using Helm)
strands-cli generate k8s --namespace my-agents --image-uri your-registry/my-weather-agent --image-tag v1.0 --service-account bedrock-sa

# Step 6: Create pod identity association for AWS Bedrock access
strands-cli create-pod-identity bedrock-sa arn:aws:iam::aws:policy/AmazonBedrockFullAccess --namespace my-agents

# Step 7: Deploy to EKS
# Using Helm:
helm upgrade --install my-weather-agent deployment/helm \
  --namespace my-agents \
  --create-namespace

# Or using kubectl:
kubectl apply -f deployment/k8s/ -n my-agents
```

> **Note:** Steps 5-7 should be executed only after you've customized your agent and built the Docker image. The deployment assets (Helm chart or K8s manifests) are generated on demand with your specific configuration.

## Next Steps

- Check out the [SPECIFICATIONS.md](./SPECIFICATIONS.md) file for detailed information about the CLI tool
- Explore more advanced customization options for your Strands agent
- Set up CI/CD pipelines for automated deployments

For more information, visit the [Strands Agents documentation](https://strandsagents.com/latest/documentation/).