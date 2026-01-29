"""Implementation of the run command."""

import os
import signal
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Optional

import docker
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from strands_cli.utils.template import render_template, TEMPLATES_DIR

console = Console()


def run_agent(
    port: int,
    agent_port: int,
    no_ui: bool,
    detach: bool,
    build: bool,
    restart: str,
    image_uri: Optional[str] = None,
    aws_profile: Optional[str] = None,
) -> None:
    """Run the Strands agent locally with a Streamlit UI for testing.

    Args:
        port: Port to expose the UI.
        agent_port: Port for the agent API.
        no_ui: Whether to run only the agent without UI.
        detach: Whether to run in background mode.
        build: Whether to build the agent image before running.
        restart: Restart policy for the containers.
        image_uri: Optional URI of an existing container image to use instead of building.
        aws_profile: Optional AWS profile name to use for credentials.

    Raises:
        ValueError: If the current directory doesn't have a valid Strands agent structure.
        FileNotFoundError: If required files are missing.
        subprocess.CalledProcessError: If Docker commands fail.
    """
    # Check if we're in a Strands agent project directory
    if not _validate_agent_directory():
        raise ValueError(
            "Current directory does not appear to be a valid Strands agent project. "
            "Make sure you're running this command from the root of your Strands agent project."
        )

    # Check if Docker and Docker Compose are installed
    if not _check_docker_installed():
        raise ValueError(
            "Docker is not installed or not running. "
            "Please install Docker and make sure it's running before using this command."
        )

    if not _check_docker_compose_installed():
        raise ValueError(
            "Docker Compose is not installed. "
            "Please install Docker Compose before using this command."
        )

    # Use the specified image or build if requested
    # Get user's home directory for AWS credentials and environment
    home_dir = os.path.expanduser("~")

    if image_uri:
        console.print(f"Using existing container image: {image_uri}")
        build = False  # Skip build if image URI is provided
    elif build:
        console.print("Building agent image...")
        try:
            from strands_cli.commands.build import build_image
            build_image(push=False, registry=None, tag="latest", multi_arch=False, platforms=None)
        except Exception as e:
            raise ValueError(f"Failed to build agent image: {str(e)}")

    # Create a temporary directory for Docker Compose files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Generate Docker Compose configuration and get environment
        docker_compose_file = _generate_docker_compose_config(
            temp_dir, port, agent_port, no_ui, restart, image_uri, aws_profile, home_dir
        )

        # Create environment with HOME set for AWS credentials
        env = os.environ.copy()
        env["HOME"] = home_dir

        # Set AWS profile if provided
        if aws_profile:
            env["AWS_PROFILE"] = aws_profile
            console.print(f"Using AWS Profile: {aws_profile}")

        # Display if using specific image
        if image_uri:
            console.print(f"Using container image: {image_uri}")

        # Check for AWS credentials
        aws_creds_path = os.path.join(home_dir, ".aws")
        if not os.path.exists(aws_creds_path):
            console.print("AWS credentials directory not found. You may need to set up AWS credentials.", style="bold yellow")

        # Print a reminder about Docker Desktop file sharing for AWS credentials
        console.print("\nUsing AWS credentials from: ~/.aws (mounted to /home/appuser/.aws in container)", style="dim")

        # Run Docker Compose
        try:
            if detach:
                # Run in detached mode
                subprocess.run(
                    ["docker", "compose", "-f", docker_compose_file, "up", "-d"],
                    check=True,
                    env=env,
                )
                _print_access_info(port, agent_port, no_ui)
                console.print(
                    "✅ Containers started in background mode. "
                    "Use 'docker compose down' to stop them."
                )
            else:
                # Run in foreground mode with clean shutdown
                process = subprocess.Popen(
                    ["docker", "compose", "-f", docker_compose_file, "up"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    env=env,
                )

                # Set up signal handlers for graceful shutdown
                def shutdown_handler(sig, frame):
                    console.print("\\nShutting down containers...")
                    subprocess.run(
                        ["docker", "compose", "-f", docker_compose_file, "down"],
                        check=False,
                        env=env,
                    )
                    if process.poll() is None:
                        process.terminate()

                # Register signal handlers
                signal.signal(signal.SIGINT, shutdown_handler)
                signal.signal(signal.SIGTERM, shutdown_handler)

                # Print access information
                _print_access_info(port, agent_port, no_ui)

                # Stream process output
                try:
                    for line in process.stdout:
                        console.print(line, end="")
                except KeyboardInterrupt:
                    shutdown_handler(None, None)

                # Wait for process to complete
                process.wait()
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Failed to run Docker Compose: {str(e)}")


def _validate_agent_directory() -> bool:
    """Check if the current directory has a valid Strands agent structure.

    Returns:
        bool: True if the directory structure is valid, False otherwise.
    """
    # Check for key files and directories
    required_paths = [
        "agent",
        "agent/__init__.py",
        "agent/agent.py",
        "api",
        "api/app.py",
        "deployment/docker/Dockerfile",
    ]

    return all(Path(path).exists() for path in required_paths)


def _check_docker_installed() -> bool:
    """Check if Docker is installed and running.

    Returns:
        bool: True if Docker is installed and running, False otherwise.
    """
    try:
        client = docker.from_env()
        client.ping()
        return True
    except:
        return False


def _check_docker_compose_installed() -> bool:
    """Check if Docker Compose is installed.

    Returns:
        bool: True if Docker Compose is installed, False otherwise.
    """
    try:
        result = subprocess.run(
            ["docker", "compose", "version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return result.returncode == 0
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _generate_docker_compose_config(
    temp_dir: str,
    port: int,
    agent_port: int,
    no_ui: bool,
    restart: str,
    image_uri: Optional[str] = None,
    aws_profile: Optional[str] = None,
    home_dir: Optional[str] = None,
) -> str:
    """Generate Docker Compose configuration file.

    Args:
        temp_dir: Temporary directory to store the file.
        port: Port to expose the UI.
        agent_port: Port for the agent API.
        no_ui: Whether to run only the agent without UI.
        restart: Restart policy for the containers.
        image_uri: Optional URI of an existing container image.
        aws_profile: Optional AWS profile to use.
        home_dir: Optional home directory path (if not provided, will use os.path.expanduser("~")).

    Returns:
        str: Path to the generated Docker Compose file.
    """
    # Get current working directory
    cwd = Path.cwd()

    # Use provided home_dir or get the user's home directory for AWS credentials
    if home_dir is None:
        home_dir = os.path.expanduser("~")

    # Generate UI template files in the temporary directory
    ui_dir = Path(temp_dir) / "ui"
    ui_dir.mkdir()

    # Copy UI template files
    _copy_ui_template_files(ui_dir)

    # Set up environment for Docker Compose
    env = os.environ.copy()
    env["HOME"] = home_dir

    # Set AWS profile environment variable if provided
    aws_env = {}
    if aws_profile:
        aws_env = {"AWS_PROFILE": aws_profile}

    # Prepare context for Docker Compose template
    context = {
        "ui_port": port,
        "agent_port": agent_port,
        "include_ui": not no_ui,
        "restart_policy": restart,
        "ui_template_dir": str(ui_dir),
        "project_dir": str(cwd),
        "HOME": home_dir,  # Add HOME to context
        "AWS_HOME_DIR": os.path.join(home_dir, ".aws"),  # Add explicit AWS home dir path
        "image_uri": image_uri,  # Add image URI if provided
        "use_image": image_uri is not None,  # Flag to use image or build
        "aws_profile": aws_profile,  # Add AWS profile if provided
        "aws_env": aws_env,  # AWS environment variables
    }

    # Render Docker Compose template
    docker_compose_file = Path(temp_dir) / "docker-compose.yml"
    render_template(
        "docker-compose/docker-compose.yml.j2",
        context,
        docker_compose_file
    )

    # Generate Docker Compose file is now ready

    return str(docker_compose_file)


def _copy_ui_template_files(ui_dir: Path) -> None:
    """Copy UI template files to the temporary directory.

    Args:
        ui_dir: Directory to copy the files to.
    """
    # Ensure the UI templates directory exists in our package
    try:
        # Copy UI template files
        render_template("ui/app.py.j2", {}, ui_dir / "app.py")
        render_template("ui/Dockerfile.j2", {}, ui_dir / "Dockerfile")
        render_template("ui/requirements.txt.j2", {}, ui_dir / "requirements.txt")
    except Exception as e:
        raise ValueError(f"Failed to generate UI template files: {str(e)}")


def _print_access_info(port: int, agent_port: int, no_ui: bool) -> None:
    """Print access information for the running services.

    Args:
        port: Port for the UI service.
        agent_port: Port for the agent API.
        no_ui: Whether UI service is disabled.
    """
    # Print access information in a panel
    info = Text()
    info.append("Access your Strands agent at:\\n\\n")

    info.append("Agent API: ", style="bold")
    info.append(f"http://localhost:{agent_port}\\n")

    if not no_ui:
        info.append("Streamlit UI: ", style="bold")
        info.append(f"http://localhost:{port}\\n")

    console.print(Panel(info, title="Strands Agent Running", expand=False))