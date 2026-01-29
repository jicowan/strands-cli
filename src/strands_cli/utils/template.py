"""Template utilities for the Strands CLI tool."""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import jinja2
import yaml
from jinja2 import Environment, FileSystemLoader, PackageLoader, select_autoescape

# Get the package directory
PACKAGE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = PACKAGE_DIR / "templates"


def get_template_environment() -> Environment:
    """Get the Jinja2 environment for template rendering.

    Returns:
        Environment: The Jinja2 environment.
    """
    # Try to use the package loader first, fall back to FileSystemLoader
    try:
        env = Environment(
            loader=PackageLoader("strands_cli", "templates"),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
    except (ImportError, ModuleNotFoundError, ValueError):
        # Fall back to FileSystemLoader for development
        env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    return env


def render_template(
    template_path: str, context: Dict[str, Any], output_path: Optional[Union[str, Path]] = None
) -> str:
    """Render a template with the given context.

    Args:
        template_path: Path to the template file relative to the templates directory.
        context: Dictionary of context variables to pass to the template.
        output_path: Optional path to write the rendered template to.

    Returns:
        str: The rendered template.

    Raises:
        FileNotFoundError: If the template file does not exist.
        jinja2.exceptions.TemplateError: If there is an error rendering the template.
    """
    env = get_template_environment()
    template = env.get_template(template_path)
    rendered = template.render(**context)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")

    return rendered


def load_values_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Load values from a YAML file.

    Args:
        file_path: Path to the YAML file.

    Returns:
        Dict[str, Any]: The loaded values.

    Raises:
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If there is an error parsing the YAML file.
    """
    with open(file_path, "r") as f:
        return yaml.safe_load(f) or {}


def parse_set_values(set_values: tuple) -> Dict[str, Any]:
    """Parse values set on the command line.

    Args:
        set_values: Tuple of values in the format key1=val1,key2=val2.

    Returns:
        Dict[str, Any]: The parsed values.
    """
    result = {}

    for values_str in set_values:
        pairs = values_str.split(",")
        for pair in pairs:
            if "=" not in pair:
                continue

            key, value = pair.split("=", 1)

            # Handle nested keys (e.g., image.repository)
            keys = key.split(".")
            current = result
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]

            # Try to convert value to appropriate type
            if value.lower() == "true":
                current[keys[-1]] = True
            elif value.lower() == "false":
                current[keys[-1]] = False
            elif value.isdigit():
                current[keys[-1]] = int(value)
            elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
                current[keys[-1]] = float(value)
            else:
                current[keys[-1]] = value

    return result


def render_from_file(
    template_path: Union[str, Path], context: Dict[str, Any], output_path: Optional[Union[str, Path]] = None
) -> str:
    """Render a template from a file path with the given context.

    Args:
        template_path: Absolute path to the template file.
        context: Dictionary of context variables to pass to the template.
        output_path: Optional path to write the rendered template to.

    Returns:
        str: The rendered template.

    Raises:
        FileNotFoundError: If the template file does not exist.
        jinja2.exceptions.TemplateError: If there is an error rendering the template.
    """
    env = Environment(
        loader=FileSystemLoader(Path(template_path).parent),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(Path(template_path).name)
    rendered = template.render(**context)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")

    return rendered