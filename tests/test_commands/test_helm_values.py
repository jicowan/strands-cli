"""Tests for Helm values file generation."""

import os
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from strands_cli.commands.init import create_project
from strands_cli.commands.generate import generate_helm_chart


class TestHelmValuesGeneration:
    """Tests for Helm values file generation."""

    @patch("strands_cli.commands.generate.create_helm_template_files")
    @patch("strands_cli.commands.generate.render_from_file")
    @patch("strands_cli.commands.generate.console.print")
    @patch("strands_cli.commands.generate.is_strands_project")
    @patch("pathlib.Path.cwd")
    def test_helm_values_files_generation(
        self, mock_cwd, mock_is_strands_project, mock_console_print,
        mock_render_from_file, mock_create_helm_template_files, temp_dir: Path
    ):
        """Test that only values.yaml and VALUES.md are generated, not environment-specific values files."""
        # Setup project
        name = "test-agent"
        description = "Test agent"
        template = "default"
        output_dir = str(temp_dir)

        # Create the project (will only create directories, not files)
        create_project(name, description, template, output_dir)

        # Get the project directory
        project_dir = temp_dir / name

        # Mock current working directory and project validation
        mock_cwd.return_value = project_dir
        mock_is_strands_project.return_value = True

        # Mock render_from_file to track what files were rendered
        def mock_render_side_effect(template_path, context, output_path):
            # Create empty file at the output path to simulate rendering
            Path(output_path).touch()
            return None

        mock_render_from_file.side_effect = mock_render_side_effect

        # Generate the Helm chart
        generate_helm_chart(set_values=tuple())

        # Verify values.yaml exists
        assert (project_dir / "deployment" / "helm" / "values.yaml").exists()

        # Verify VALUES.md exists
        assert (project_dir / "deployment" / "helm" / "VALUES.md").exists()

        # Verify environment-specific values files don't exist
        assert not (project_dir / "deployment" / "helm" / "values-dev.yaml").exists()
        assert not (project_dir / "deployment" / "helm" / "values-prod.yaml").exists()

    @patch("strands_cli.commands.generate.is_strands_project")
    @patch("pathlib.Path.cwd")
    def test_values_yaml_content(self, mock_cwd, mock_is_strands_project, temp_dir: Path):
        """Test that values.yaml contains all required configuration parameters."""
        # Setup project
        name = "test-values"
        description = "Test values"
        template = "default"
        output_dir = str(temp_dir)

        # Create the project (will only create directories, not files)
        create_project(name, description, template, output_dir)

        # Get the project directory
        project_dir = temp_dir / name

        # Mock current working directory and project validation
        mock_cwd.return_value = project_dir
        mock_is_strands_project.return_value = True

        # Generate the Helm chart
        generate_helm_chart(set_values=tuple())

        # Get the values.yaml file
        values_yaml_path = project_dir / "deployment" / "helm" / "values.yaml"

        # Verify the file exists
        assert values_yaml_path.exists()

        # Read the content
        with open(values_yaml_path, 'r') as f:
            values_data = yaml.safe_load(f)

        # Check for required keys that should be in the default values
        assert "image" in values_data
        assert "repository" in values_data["image"]
        assert "tag" in values_data["image"]
        assert "pullPolicy" in values_data["image"]

        # Check that all major sections exist
        required_sections = [
            "replicaCount",
            "serviceAccount",
            "service",
            "ingress",
            "resources",
            "autoscaling",
            "nodeSelector",
            "tolerations",
            "affinity",
            "podSecurityContext",
            "securityContext",
            "podAnnotations",
            "topologySpreadConstraints",
            "podDisruptionBudget",
            "env"
        ]

        for section in required_sections:
            assert section in values_data, f"Missing required section: {section}"

        # Check specific nested values
        assert values_data["service"]["type"] == "ClusterIP"
        assert values_data["service"]["port"] == 80
        assert values_data["service"]["targetPort"] == 8000

        assert values_data["ingress"]["enabled"] is False
        assert "hosts" in values_data["ingress"]

        assert "limits" in values_data["resources"]
        assert "requests" in values_data["resources"]

    @patch("strands_cli.commands.generate.is_strands_project")
    @patch("pathlib.Path.cwd")
    def test_values_md_documentation(self, mock_cwd, mock_is_strands_project, temp_dir: Path):
        """Test that VALUES.md documentation file is generated with comprehensive information."""
        # Setup project
        name = "test-docs"
        description = "Test docs"
        template = "default"
        output_dir = str(temp_dir)

        # Create the project (will only create directories, not files)
        create_project(name, description, template, output_dir)

        # Get the project directory
        project_dir = temp_dir / name

        # Mock current working directory and project validation
        mock_cwd.return_value = project_dir
        mock_is_strands_project.return_value = True

        # Generate the Helm chart
        generate_helm_chart(set_values=tuple())

        # Get the VALUES.md file
        values_md_path = project_dir / "deployment" / "helm" / "VALUES.md"

        # Verify the file exists
        assert values_md_path.exists()

        # Read the content
        content = values_md_path.read_text()

        # Check for documentation sections
        required_sections = [
            "# Helm Values Configuration",
            "## Quick Reference",
            "## Available Configuration Parameters",
            "### Core Settings",
            "### Image Configuration",
            "### Service Account",
            "### Ingress Configuration",
            "### Resource Management",
            "### Autoscaling",
            "### High Availability & Reliability",
            "### Environment Variables"
        ]

        for section in required_sections:
            assert section in content, f"Missing documentation section: {section}"