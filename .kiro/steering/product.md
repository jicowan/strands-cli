# Product Overview

Strands CLI is a command-line tool for generating, building, and deploying Python-based AI agents to Amazon EKS. It provides a standardized project structure and deployment pipeline for agents that integrate with AWS Bedrock.

## Core Features

- **Project Scaffolding**: Creates standardized Python agent projects with FastAPI wrappers
- **Local Development**: Docker Compose orchestration with Streamlit UI for testing
- **Containerization**: Multi-architecture Docker builds with registry push support
- **Deployment**: Generates Helm charts and Kubernetes manifests for EKS deployment
- **AWS Integration**: Pod Identity setup for secure Bedrock access without static credentials

## Target Users

Developers building AI agents that need to be deployed to Kubernetes clusters, particularly those using AWS Bedrock for LLM capabilities.

## Key Workflows

1. **Initialize** → **Develop** → **Test Locally** → **Build** → **Generate Deployment Assets** → **Deploy**
2. Local testing with `strands-cli run` provides interactive Streamlit UI
3. Deployment assets are generated on-demand with specific configuration parameters
4. AWS Pod Identity integration eliminates need for static AWS credentials in containers