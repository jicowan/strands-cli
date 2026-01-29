"""Main CLI entry point for the Strands CLI tool."""

import sys
from typing import Optional

import click
from rich.console import Console

from strands_cli import __version__

# Set up Rich console for pretty output
console = Console()


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="strands-cli")
def cli() -> None:
    """Strands CLI tool for generating and deploying Strands agents to Amazon EKS.

    This tool helps you create a standardized project structure for Python-based Strands agents,
    generate boilerplate code, containerize your agent, and deploy it to Amazon EKS.
    """
    pass


@cli.command("create-pod-identity")
@click.argument("service_account", type=str)
@click.argument("policy_arn", type=str)
@click.option(
    "--cluster-name",
    type=str,
    help="Name of the EKS cluster (default: uses current kubectl context)",
    default=None,
)
@click.option(
    "--namespace",
    "-n",
    type=str,
    help="Kubernetes namespace for the service account",
    default="default",
)
@click.option(
    "--role-name",
    type=str,
    help="Name for the IAM role (default: eks-pod-identity-<service_account>)",
    default=None,
)
def create_pod_identity_command(
    service_account: str,
    policy_arn: str,
    cluster_name: Optional[str],
    namespace: str,
    role_name: Optional[str],
) -> None:
    """Create an IAM role and pod identity association for EKS.

    This command creates an IAM role with a pod identity trust policy,
    attaches the specified policy to the role, and creates a pod identity
    association in EKS. The role will be used by the specified service
    account to access AWS services.

    SERVICE_ACCOUNT is the name of the Kubernetes service account.
    POLICY_ARN is the ARN of the policy to attach to the role.

    Example: strands-cli create-pod-identity bedrock-agent arn:aws:iam::aws:policy/AmazonBedrockFullAccess
    """
    # Import here to avoid circular imports
    from strands_cli.commands.pod_identity import create_pod_identity_association

    try:
        success, message = create_pod_identity_association(
            service_account_name=service_account,
            policy_arn=policy_arn,
            cluster_name=cluster_name,
            namespace=namespace,
            role_name=role_name
        )
        if success:
            console.print(f"✅ {message}")
        else:
            console.print(f"❌ {message}", style="bold red")
            sys.exit(1)
    except Exception as e:
        console.print(f"❌ Error creating pod identity association: {str(e)}", style="bold red")
        sys.exit(1)


@cli.command("init")
@click.argument("name", type=str)
@click.option(
    "--description",
    "-d",
    type=str,
    help="Short description of the agent",
    default="A Strands agent",
)
@click.option(
    "--template",
    "-t",
    type=str,
    help="Template to use for agent creation",
    default="default",
)
@click.option(
    "--output-dir",
    "-o",
    type=str,
    help="Directory where the project will be created",
    default=".",
)
def init_command(name: str, description: str, template: str, output_dir: str) -> None:
    """Initialize a new Strands agent project.

    Creates a new directory with the given NAME and populates it with a
    standardized project structure for a Strands agent.
    """
    # Import here to avoid circular imports
    from strands_cli.commands.init import create_project

    try:
        create_project(name, description, template, output_dir)
        console.print(f"✅ Successfully created Strands agent project: [bold]{name}[/bold]")
    except Exception as e:
        console.print(f"❌ Error creating project: {str(e)}", style="bold red")
        sys.exit(1)


@cli.command("build")
@click.option("--push", is_flag=True, help="Push image to registry after building")
@click.option("--registry", "-r", type=str, help="Registry URL", default=None)
@click.option(
    "--tag", "-t", type=str, help="Image tag (default: latest)", default="latest"
)
@click.option(
    "--multi-arch", is_flag=True, help="Build for multiple architectures (AMD64 and ARM64)"
)
@click.option(
    "--platform",
    multiple=True,
    help="Platforms to build for (e.g., linux/amd64, linux/arm64). Can be specified multiple times."
)
def build_command(push: bool, registry: Optional[str], tag: str, multi_arch: bool, platform: tuple) -> None:
    """Build a Docker image for the Strands agent.

    Must be run from within a Strands agent project directory.

    When using --multi-arch, the image will be built for both AMD64 and ARM64 architectures by default.
    You can specify specific platforms with --platform (e.g., --platform linux/amd64 --platform linux/arm64).
    """
    # Import here to avoid circular imports
    from strands_cli.commands.build import build_image

    # Convert platform tuple to list if specified
    platforms = list(platform) if platform else None

    try:
        build_image(
            push=push,
            registry=registry,
            tag=tag,
            multi_arch=multi_arch,
            platforms=platforms
        )
        console.print(f"✅ Successfully built Docker image")
        if push:
            console.print(f"✅ Successfully pushed Docker image")
    except Exception as e:
        console.print(f"❌ Error building image: {str(e)}", style="bold red")
        sys.exit(1)


@cli.group("generate")
def generate_command() -> None:
    """Generate deployment manifests for the Strands agent."""
    pass


@generate_command.command("helm")
@click.option(
    "--set",
    "set_values",
    multiple=True,
    help="Set values on the command line (can specify multiple or separate values with commas: key1=val1,key2=val2). "
         "Examples: --set image.repository=my-registry/my-agent --set image.tag=v1.0.0 --set serviceAccount.name=bedrock-agent",
)
@click.option(
    "--values-file",
    "-f",
    type=str,
    help="Values file to use (default: values.yaml)",
    default=None,
)
def generate_helm_command(
    set_values: tuple,
    values_file: Optional[str]
) -> None:
    """Generate a Helm chart for deploying the Strands agent.

    Use --set to configure values following Helm conventions:
    - Image: --set image.repository=my-registry/my-agent --set image.tag=v1.0.0
    - Service Account: --set serviceAccount.name=bedrock-agent --set serviceAccount.create=false
    - Replicas: --set replicaCount=3

    When using a service account, ensure it is mapped to an IAM role using pod identities
    and the role has rights to invoke the model hosted on AWS Bedrock.
    """
    # Import here to avoid circular imports
    from strands_cli.commands.generate import generate_helm_chart

    try:
        generate_helm_chart(set_values, values_file)
        console.print(f"✅ Successfully generated Helm chart")
    except Exception as e:
        console.print(f"❌ Error generating Helm chart: {str(e)}", style="bold red")
        sys.exit(1)


@generate_command.command("k8s")
@click.option(
    "--namespace", "-n", type=str, help="Kubernetes namespace", default="default"
)
@click.option(
    "--output-dir",
    "-o",
    type=str,
    help="Directory where the manifests will be created",
    default="deployment/k8s",
)
@click.option(
    "--image-uri",
    type=str,
    help="URI of the container image (e.g., your-registry/image-name)",
    default=None,
)
@click.option(
    "--image-tag",
    type=str,
    help="Tag of the container image (e.g., latest, v1.0)",
    default=None,
)
@click.option(
    "--service-account",
    type=str,
    help="Name of the service account to use with pod identity for AWS Bedrock access",
    default=None,
)
def generate_k8s_command(
    namespace: str,
    output_dir: str,
    image_uri: Optional[str],
    image_tag: Optional[str],
    service_account: Optional[str]
) -> None:
    """Generate raw Kubernetes manifests for deploying the Strands agent.

    When using --service-account, ensure this service account is mapped to an IAM role
    using pod identities and the role has rights to invoke the model hosted on AWS Bedrock.
    """
    # Import here to avoid circular imports
    from strands_cli.commands.generate import generate_k8s_manifests

    try:
        generate_k8s_manifests(namespace, output_dir, image_uri, image_tag, service_account)
        console.print(f"✅ Successfully generated Kubernetes manifests")
    except Exception as e:
        console.print(f"❌ Error generating Kubernetes manifests: {str(e)}", style="bold red")
        sys.exit(1)


@cli.command("run")
@click.option(
    "--port",
    type=int,
    help="Port to expose the UI",
    default=8501,
)
@click.option(
    "--agent-port",
    type=int,
    help="Port for the agent API",
    default=8000,
)
@click.option(
    "--no-ui",
    is_flag=True,
    help="Run only the agent without UI (for headless testing)",
)
@click.option(
    "--detach",
    is_flag=True,
    help="Run in background mode",
)
@click.option(
    "--build",
    is_flag=True,
    help="Build the agent image before running",
    default=True,
)
@click.option(
    "--image-uri",
    type=str,
    help="URI of an existing container image (e.g., registry/name:tag) to use instead of building",
    default=None,
)
@click.option(
    "--restart",
    type=str,
    help="Restart policy",
    default="unless-stopped",
)
@click.option(
    "--aws-profile",
    type=str,
    help="AWS profile to use for credentials",
    default=None,
)
def run_command(
    port: int,
    agent_port: int,
    no_ui: bool,
    detach: bool,
    build: bool,
    image_uri: Optional[str],
    restart: str,
    aws_profile: Optional[str],
) -> None:
    """Run the Strands agent locally with a Streamlit UI for testing.

    This command orchestrates the agent and UI containers using Docker Compose, making it
    easy to test your agent locally before deploying it to production.

    Must be run from within a Strands agent project directory.

    If --image-uri is specified, the specified image will be used instead of building locally.
    For example: --image-uri registry/name:tag
    """
    # Import here to avoid circular imports
    from strands_cli.commands.run import run_agent

    try:
        run_agent(
            port=port,
            agent_port=agent_port,
            no_ui=no_ui,
            detach=detach,
            build=build,
            image_uri=image_uri,
            restart=restart,
            aws_profile=aws_profile,
        )
        # Output is handled by the run_agent function
    except Exception as e:
        console.print(f"❌ Error running agent: {str(e)}", style="bold red")
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()