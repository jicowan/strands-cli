"""Implementation of the build command."""

import os
from pathlib import Path
from typing import Optional, List

from rich.console import Console

from strands_cli.utils.docker import build_docker_image

console = Console()


def build_image(
    push: bool = False,
    registry: Optional[str] = None,
    tag: str = "latest",
    multi_arch: bool = False,
    platforms: Optional[List[str]] = None
) -> None:
    """Build a Docker image for the Strands agent.

    Args:
        push: Whether to push the image to a registry.
        registry: The registry to push the image to.
        tag: The tag to use for the image.
        multi_arch: Whether to build for multiple architectures.
        platforms: List of platforms to build for (e.g., ["linux/amd64", "linux/arm64"]).
                  Defaults to both AMD64 and ARM64 if multi_arch is True.

    Raises:
        ValueError: If the current directory is not a Strands agent project.
        RuntimeError: If the Docker build fails.
    """
    # Check if we're in a Strands agent project directory
    project_dir = Path.cwd()

    # Basic validation of project structure
    required_dirs = [
        project_dir / "agent",
        project_dir / "api",
        project_dir / "deployment" / "docker",
    ]

    for directory in required_dirs:
        if not directory.exists() or not directory.is_dir():
            raise ValueError(
                f"Directory {directory} not found. "
                "Are you in a Strands agent project directory?"
            )

    # Check for Dockerfile
    dockerfile_path = project_dir / "deployment" / "docker" / "Dockerfile"
    if not dockerfile_path.exists():
        raise ValueError(
            f"Dockerfile not found at {dockerfile_path}. "
            "Are you in a Strands agent project directory?"
        )

    # If push is requested but no registry provided, check environment variables
    if push and not registry:
        # Check common environment variables for container registries
        registry = (
            os.environ.get("ECR_REGISTRY") or
            os.environ.get("DOCKER_REGISTRY") or
            os.environ.get("CONTAINER_REGISTRY")
        )

        if not registry:
            raise ValueError(
                "No registry specified for push. "
                "Please provide a registry with --registry or set one of "
                "the environment variables ECR_REGISTRY, DOCKER_REGISTRY, "
                "or CONTAINER_REGISTRY."
            )

    # Set default platforms if multi_arch is True but no platforms are specified
    if multi_arch and not platforms:
        platforms = ["linux/amd64", "linux/arm64"]

    # Build the Docker image
    success, message = build_docker_image(
        project_dir=project_dir,
        tag=tag,
        registry=registry,
        push=push,
        multi_arch=multi_arch,
        platforms=platforms,
    )

    if not success:
        raise RuntimeError(f"Failed to build Docker image: {message}")

    console.print(f"✅ {message}")