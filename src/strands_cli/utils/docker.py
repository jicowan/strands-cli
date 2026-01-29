"""Docker utilities for the Strands CLI tool."""

import os
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional, Tuple

from rich.console import Console

console = Console()


def check_docker_installed() -> bool:
    """Check if Docker is installed and accessible.

    Returns:
        bool: True if Docker is installed and accessible, False otherwise.
    """
    try:
        subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            check=True,
            text=True
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def check_buildx_installed() -> bool:
    """Check if Docker BuildX is installed and accessible.

    Returns:
        bool: True if Docker BuildX is installed and accessible, False otherwise.
    """
    try:
        result = subprocess.run(
            ["docker", "buildx", "version"],
            capture_output=True,
            check=True,
            text=True
        )
        return "buildx" in result.stdout
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def build_docker_image(
    project_dir: Path,
    tag: str = "latest",
    registry: Optional[str] = None,
    push: bool = False,
    multi_arch: bool = False,
    platforms: Optional[List[str]] = None,
) -> Tuple[bool, str]:
    """Build a Docker image for the Strands agent.

    Args:
        project_dir: The project directory.
        tag: The tag to use for the image.
        registry: Optional registry to push to.
        push: Whether to push the image to the registry.
        multi_arch: Whether to build for multiple architectures using buildx.
        platforms: List of platforms to build for (e.g., ["linux/amd64", "linux/arm64"]).

    Returns:
        Tuple[bool, str]: Success status and message.
    """
    # Check if Docker is installed
    if not check_docker_installed():
        return False, "Docker is not installed or not in the PATH"

    # Check if Dockerfile exists
    dockerfile_path = project_dir / "deployment" / "docker" / "Dockerfile"
    if not dockerfile_path.exists():
        return False, f"Dockerfile not found at {dockerfile_path}"

    # Get project name from directory name
    project_name = project_dir.name.lower()

    # Check if we should use multi-arch build
    if multi_arch:
        return build_multi_arch_docker_image(
            project_dir=project_dir,
            project_name=project_name,
            dockerfile_path=dockerfile_path,
            tag=tag,
            registry=registry,
            push=push,
            platforms=platforms or ["linux/amd64", "linux/arm64"],
        )

    # Single architecture build (legacy approach)
    console.print(f"Building Docker image [bold]{project_name}:{tag}[/bold]...")

    build_cmd = [
        "docker", "build",
        "-t", f"{project_name}:{tag}",
        "-f", str(dockerfile_path),
        str(project_dir),
    ]

    try:
        subprocess.run(build_cmd, check=True, text=True)
    except subprocess.SubprocessError as e:
        return False, f"Failed to build Docker image: {e}"

    # Push to registry if requested
    if push and registry:
        console.print(f"Pushing Docker image to [bold]{registry}/{project_name}:{tag}[/bold]...")

        # Tag the image
        tag_cmd = [
            "docker", "tag",
            f"{project_name}:{tag}",
            f"{registry}/{project_name}:{tag}"
        ]

        # Push the image
        push_cmd = [
            "docker", "push",
            f"{registry}/{project_name}:{tag}"
        ]

        try:
            subprocess.run(tag_cmd, check=True, text=True)
            push_result = subprocess.run(push_cmd, capture_output=True, text=True)
            if push_result.returncode != 0:
                error_output = push_result.stderr.lower()
                if "authentication required" in error_output or "denied" in error_output or "unauthorized" in error_output:
                    return False, f"The push failed because you are not currently logged in to {registry}. Please login and try again."
                else:
                    return False, f"Failed to push Docker image: {push_result.stderr}"
        except subprocess.SubprocessError as e:
            error_message = str(e)
            if "authentication required" in error_message.lower() or "denied" in error_message.lower() or "unauthorized" in error_message.lower():
                return False, f"The push failed because you are not currently logged in to {registry}. Please login and try again."
            else:
                return False, f"Failed to push Docker image: {e}"

        return True, f"Successfully built and pushed Docker image: {registry}/{project_name}:{tag}"

    return True, f"Successfully built Docker image: {project_name}:{tag}"


def build_multi_arch_docker_image(
    project_dir: Path,
    project_name: str,
    dockerfile_path: Path,
    tag: str = "latest",
    registry: Optional[str] = None,
    push: bool = False,
    platforms: List[str] = ["linux/amd64", "linux/arm64"],
) -> Tuple[bool, str]:
    """Build a multi-architecture Docker image using buildx.

    Args:
        project_dir: The project directory.
        project_name: The name of the project.
        dockerfile_path: Path to the Dockerfile.
        tag: The tag to use for the image.
        registry: Optional registry to push to.
        push: Whether to push the image to the registry.
        platforms: List of platforms to build for.

    Returns:
        Tuple[bool, str]: Success status and message.
    """
    # Check if Docker is installed
    if not check_docker_installed():
        return False, "Docker is not installed or not in the PATH"

    # Check if BuildX is available
    if not check_buildx_installed():
        return False, "Docker BuildX is not available. Please install or enable BuildX."

    # Build the full image name
    image_name = f"{project_name}:{tag}"
    if registry:
        image_name = f"{registry}/{image_name}"

    # Create buildx command
    console.print(f"Building multi-arch Docker image for platforms: {', '.join(platforms)}...")

    # Create a new builder if needed or use the default one
    try:
        # Check if we already have a builder
        builder_check = subprocess.run(
            ["docker", "buildx", "ls"],
            capture_output=True,
            text=True,
            check=True
        )

        # If we don't have a builder with qemu support, create one
        if "linux/arm64" in str(platforms) and "linux/arm64" not in builder_check.stdout:
            console.print("Setting up QEMU for multi-architecture builds...")
            subprocess.run(
                ["docker", "run", "--privileged", "--rm", "tonistiigi/binfmt", "--install", "all"],
                check=True
            )

            # Create a new builder
            subprocess.run(
                ["docker", "buildx", "create", "--name", "strands-builder", "--use"],
                check=True
            )

        # Prepare buildx command
        buildx_cmd = [
            "docker", "buildx", "build",
            "--platform", ",".join(platforms),
            "-t", image_name,
            "-f", str(dockerfile_path),
        ]

        # Add push flag if needed
        if push:
            buildx_cmd.append("--push")
        else:
            buildx_cmd.extend(["--load", "--output", "type=docker"])

        # Add the build context
        buildx_cmd.append(str(project_dir))

        # Execute the build
        console.print(f"Building image: {' '.join(buildx_cmd)}")

        build_result = subprocess.run(buildx_cmd, capture_output=True, text=True)
        if build_result.returncode != 0:
            error_output = build_result.stderr.lower()
            # Check for authentication errors if pushing
            if push and (
                "authentication required" in error_output or
                "denied" in error_output or
                "unauthorized" in error_output
            ):
                registry_part = registry if registry else "the registry"
                return False, f"The push failed because you are not currently logged in to {registry_part}. Please login and try again."
            else:
                return False, f"Failed to build multi-arch Docker image: {build_result.stderr}"

        if push:
            return True, f"Successfully built and pushed multi-arch Docker image: {image_name} for platforms: {', '.join(platforms)}"
        else:
            return True, f"Successfully built multi-arch Docker image: {image_name} for platforms: {', '.join(platforms)}"

    except subprocess.SubprocessError as e:
        error_message = str(e).lower()
        if push and (
            "authentication required" in error_message or
            "denied" in error_message or
            "unauthorized" in error_message
        ):
            registry_part = registry if registry else "the registry"
            return False, f"The push failed because you are not currently logged in to {registry_part}. Please login and try again."
        else:
            return False, f"Failed to build multi-arch Docker image: {e}"