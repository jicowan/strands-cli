"""Implementation of the init command."""

import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict

import jinja2
from rich.console import Console

from strands_cli.utils.template import TEMPLATES_DIR
from strands_cli.utils.helm import create_helm_template_files

console = Console()


def create_project(name: str, description: str, template: str, output_dir: str) -> None:
    """Create a new Strands agent project.

    Args:
        name: Name of the agent.
        description: Short description of the agent.
        template: Template to use for agent creation.
        output_dir: Directory where the project will be created.

    Raises:
        ValueError: If the name contains invalid characters.
        FileExistsError: If the project directory already exists.
    """
    # Validate the name (no spaces, only alphanumeric and hyphen/underscore)
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        raise ValueError(
            "Agent name must contain only alphanumeric characters, hyphens, and underscores."
        )

    # Always use the default template for now
    template = "default"

    # Set up project directory
    project_dir = Path(output_dir) / name
    if project_dir.exists():
        raise FileExistsError(f"Directory already exists: {project_dir}")

    # Create project directory
    project_dir.mkdir(parents=True)

    # Set up context for templates
    context = {
        "name": name,
        "description": description,
        "package_name": name.replace("-", "_"),
        "class_name": "".join(word.title() for word in re.split(r"[-_]", name)),
    }

    try:
        # Create the directory structure
        create_directory_structure(project_dir)

        # Create the project files
        create_project_files(project_dir, context)

        console.print(f"Project created at: [bold]{project_dir}[/bold]")
        console.print("Next steps:")
        console.print(f"  1. cd {name}")
        console.print("  2. Install development dependencies:")
        console.print("     pip install -e '.[dev]'")
        console.print("  3. Edit agent/prompts.py to customize your agent's system prompt")
        console.print("  4. Build and deploy your agent:")
        console.print("     strands-cli build")
        console.print("     strands-cli generate helm")
    except Exception as e:
        # Clean up the project directory if any error occurs
        if project_dir.exists():
            shutil.rmtree(project_dir)
        # Re-raise with a clearer message
        raise ValueError(f"Error creating project: {str(e)}")


def create_directory_structure(project_dir: Path) -> None:
    """Create the project directory structure.

    Args:
        project_dir: Base directory for the project.
    """
    directories = [
        "agent",
        "api",
        "deployment/docker",
        "scripts",
    ]

    for directory in directories:
        (project_dir / directory).mkdir(parents=True, exist_ok=True)


def create_project_files(project_dir: Path, context: Dict[str, Any]) -> None:
    """Create the project files from templates.

    Args:
        project_dir: Base directory for the project.
        context: Template context variables.
    """
    # Project root files
    render_from_file(
        TEMPLATES_DIR / "default/root/README.md.j2",
        context,
        project_dir / "README.md"
    )
    render_from_file(
        TEMPLATES_DIR / "default/root/pyproject.toml.j2",
        context,
        project_dir / "pyproject.toml"
    )

    # Agent files
    render_from_file(
        TEMPLATES_DIR / "default/agent/__init__.py.j2",
        context,
        project_dir / "agent/__init__.py"
    )
    render_from_file(
        TEMPLATES_DIR / "default/agent/agent.py.j2",
        context,
        project_dir / "agent/agent.py"
    )
    render_from_file(
        TEMPLATES_DIR / "default/agent/tools.py.j2",
        context,
        project_dir / "agent/tools.py"
    )
    render_from_file(
        TEMPLATES_DIR / "default/agent/prompts.py.j2",
        context,
        project_dir / "agent/prompts.py"
    )

    # API files
    render_from_file(
        TEMPLATES_DIR / "default/api/__init__.py.j2",
        context,
        project_dir / "api/__init__.py"
    )
    render_from_file(
        TEMPLATES_DIR / "default/api/app.py.j2",
        context,
        project_dir / "api/app.py"
    )
    render_from_file(
        TEMPLATES_DIR / "default/api/models.py.j2",
        context,
        project_dir / "api/models.py"
    )
    render_from_file(
        TEMPLATES_DIR / "default/api/routes.py.j2",
        context,
        project_dir / "api/routes.py"
    )

    # Docker files
    render_from_file(
        TEMPLATES_DIR / "default/docker/Dockerfile.j2",
        context,
        project_dir / "deployment/docker/Dockerfile"
    )
    render_from_file(
        TEMPLATES_DIR / "default/docker/requirements.txt.j2",
        context,
        project_dir / "deployment/docker/requirements.txt"
    )

    # Note: Helm chart directory and files are not created here.
    # They should be created using the 'strands-cli generate helm' command.

    # Note: K8s manifest directory and files are not created here.
    # They should be created using the 'strands-cli generate k8s' command.

    # Scripts
    script_files = ["build.sh", "push.sh", "deploy.sh"]
    for script_file in script_files:
        script_path = project_dir / f"scripts/{script_file}"
        try:
            render_from_file(
                TEMPLATES_DIR / f"default/scripts/{script_file}.j2",
                context,
                script_path
            )

            # Make scripts executable
            if script_path.exists():
                os.chmod(script_path, 0o755)
        except Exception as e:
            console.print(f"Warning: Failed to render script {script_file}: {str(e)}")


def render_from_file(template_path: Path, context: Dict[str, Any], output_path: Path) -> None:
    """Render a template file directly.

    Args:
        template_path: Path to the template file.
        context: Dictionary of context variables.
        output_path: Path to write the rendered template.

    Raises:
        FileNotFoundError: If the template file does not exist.
    """
    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")

    try:
        # Read the template content
        template_content = template_path.read_text(encoding="utf-8")

        # Create a Jinja2 environment with the template string
        env = jinja2.Environment(
            autoescape=jinja2.select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Create a template from the string
        template = env.from_string(template_content)

        # Render the template with context
        rendered = template.render(**context)

        # Ensure the output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the rendered content
        output_path.write_text(rendered, encoding="utf-8")
    except Exception as e:
        raise ValueError(f"Failed to render template {template_path}: {str(e)}")