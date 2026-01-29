"""Implementation of the generate commands."""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import yaml
from rich.console import Console

from strands_cli.utils.template import render_template, load_values_file, parse_set_values
from strands_cli.utils.helm import create_helm_template_files
from strands_cli.utils.template import TEMPLATES_DIR, render_from_file

console = Console()


def generate_helm_chart(
    set_values: tuple,
    values_file: Optional[str] = None
) -> None:
    """Generate a Helm chart for deploying the Strands agent.

    Args:
        set_values: Values to set on the command line.
        values_file: Path to a values file to use.

    Raises:
        ValueError: If the current directory is not a Strands agent project.
        FileNotFoundError: If the values file does not exist.
    """
    # Check if we're in a Strands agent project directory
    project_dir = Path.cwd()

    # Basic validation of project structure
    if not is_strands_project(project_dir):
        raise ValueError(
            "Are you in a Strands agent project directory? "
            "Expected to find agent/ and api/ directories."
        )

    # Create the helm directory and templates subdirectory if they don't exist
    helm_dir = project_dir / "deployment" / "helm"
    helm_dir.mkdir(parents=True, exist_ok=True)

    # Ensure templates directory exists
    helm_templates_dir = helm_dir / "templates"
    helm_templates_dir.mkdir(parents=True, exist_ok=True)

    # Check if the values file exists
    values = {}
    if values_file:
        values_file_path = Path(values_file)
        if not values_file_path.exists():
            raise FileNotFoundError(f"Values file not found: {values_file}")
        values.update(load_values_file(values_file_path))

    # Parse values set on the command line
    if set_values:
        command_line_values = parse_set_values(set_values)
        values.update(command_line_values)

    # Get project name from directory name
    project_name = project_dir.name.lower()

    # Create context for template generation
    context = {
        "name": project_name,
        "description": "A Strands agent",  # Default description
        "package_name": project_name.replace("-", "_"),
        "class_name": "".join(word.title() for word in project_name.split("-")),
    }

    # Generate Chart.yaml file
    render_from_file(
        TEMPLATES_DIR / "default/helm/Chart.yaml.j2",
        context,
        helm_dir / "Chart.yaml"
    )

    # Create Helm values documentation file
    render_from_file(
        TEMPLATES_DIR / "default/helm/VALUES.md.j2",
        context,
        helm_dir / "VALUES.md"
    )

    # Create values context with any overrides
    values_context = context.copy()

    # Create a dictionary of values for the values.yaml
    values_dict = {}
    if values:
        values_dict.update(values)

    # Check if service account is being set and provide guidance
    service_account_name = None
    if "serviceAccount" in values_dict and "name" in values_dict["serviceAccount"]:
        service_account_name = values_dict["serviceAccount"]["name"]
    elif any("serviceAccount.name=" in str(val) for val in set_values):
        # Extract service account name from --set values for warning
        for val in set_values:
            if "serviceAccount.name=" in str(val):
                service_account_name = str(val).split("serviceAccount.name=")[1].split(",")[0]
                break

    if service_account_name:
        console.print(f"ℹ️ Using service account: {service_account_name}")
        console.print("⚠️ Ensure this service account is mapped to an IAM role using pod identities")
        console.print("⚠️ The IAM role should have permissions to invoke models on AWS Bedrock")

    # Generate values.yaml from template - we'll use the project name in the template
    values_context["values"] = values_dict

    # Write the values file using the template
    values_path = helm_dir / "values.yaml"
    render_from_file(
        TEMPLATES_DIR / "default/helm/values.yaml.j2",
        values_context,
        values_path
    )

    # Create Helm template files
    create_helm_template_files(project_dir, context)

    console.print(f"✅ Helm chart generated in {helm_dir}")
    console.print(f"✅ Values written to {values_path}")
    console.print("")
    console.print("To deploy the Helm chart:")
    console.print(f"  helm upgrade --install {project_name} deployment/helm \\")
    console.print("    --namespace your-namespace --create-namespace")
    console.print("")
    console.print("To customize values, use --set flags:")
    console.print(f"  helm upgrade --install {project_name} deployment/helm \\")
    console.print("    --set image.repository=my-registry/my-agent \\")
    console.print("    --set image.tag=v1.0.0 \\")
    console.print("    --set serviceAccount.name=bedrock-agent \\")
    console.print("    --namespace your-namespace")


def generate_k8s_manifests(
    namespace: str,
    output_dir: str,
    image_uri: Optional[str] = None,
    image_tag: Optional[str] = None,
    service_account: Optional[str] = None
) -> None:
    """Generate raw Kubernetes manifests for deploying the Strands agent.

    Args:
        namespace: Kubernetes namespace to deploy to.
        output_dir: Directory to write the manifests to.
        image_uri: URI of the container image.
        image_tag: Tag of the container image.
        service_account: Name of the service account to use with pod identity.

    Raises:
        ValueError: If the current directory is not a Strands agent project.
    """
    # Check if we're in a Strands agent project directory
    project_dir = Path.cwd()

    # Basic validation of project structure
    if not is_strands_project(project_dir):
        raise ValueError(
            "Are you in a Strands agent project directory? "
            "Expected to find agent/ and api/ directories."
        )

    # Create the output directory if it doesn't exist
    # If using the default output directory, create it under deployment/k8s
    if output_dir == "deployment/k8s":
        output_path = project_dir / output_dir
    else:
        output_path = Path(output_dir)

    output_path.mkdir(parents=True, exist_ok=True)

    # Get project name from directory name
    project_name = project_dir.name.lower()

    # Context for templates
    context = {
        "name": project_name,
        "namespace": namespace,
    }

    # Add image URI if provided
    if image_uri:
        context["image_repository"] = image_uri
        console.print(f"ℹ️ Using image URI: {image_uri}")
    else:
        context["image_repository"] = f"your-registry/{project_name}"

    # Add image tag if provided
    if image_tag:
        context["image_tag"] = image_tag
        console.print(f"ℹ️ Using image tag: {image_tag}")
    else:
        context["image_tag"] = "latest"

    # Add service account if provided
    if service_account:
        context["service_account"] = service_account
        console.print(f"ℹ️ Using service account: {service_account}")
        console.print("⚠️ Ensure this service account is mapped to an IAM role using pod identities")
        console.print("⚠️ The IAM role should have permissions to invoke models on AWS Bedrock")

    # List of manifest files to generate
    manifest_files = [
        "deployment.yaml",
        "service.yaml",
        "serviceaccount.yaml",
        "ingress.yaml",
        "poddisruptionbudget.yaml",
    ]

    # Generate each manifest file
    for manifest in manifest_files:
        source_template = f"default/k8s/{manifest}.j2"
        output_file = output_path / manifest

        # Render the template
        content = render_template(source_template, context)

        # Write the rendered template to the output file
        output_file.write_text(content)

        console.print(f"✅ Generated {output_file}")

    console.print("")
    console.print("To deploy the manifests:")
    console.print(f"  kubectl apply -f {output_dir} -n {namespace}")
    console.print("")
    console.print("Before deploying, make sure to set the required environment variables:")
    console.print(f"  export IMAGE_REPOSITORY=your-registry/{project_name}")
    console.print("  export IMAGE_TAG=latest")
    console.print("  export INGRESS_HOST=your-hostname.example.com")


def is_strands_project(project_dir: Path) -> bool:
    """Check if the given directory is a Strands agent project.

    Args:
        project_dir: Directory to check.

    Returns:
        bool: True if the directory is a Strands agent project, False otherwise.
    """
    required_dirs = [
        project_dir / "agent",
        project_dir / "api",
        project_dir / "deployment",
    ]

    return all(directory.exists() and directory.is_dir() for directory in required_dirs)