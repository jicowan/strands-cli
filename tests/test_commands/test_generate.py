"""Tests for the generate commands."""

import os
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest

from strands_cli.commands.generate import (
    generate_helm_chart,
    generate_k8s_manifests,
    is_strands_project
)


class TestGenerateCommands:
    """Tests for generate commands."""

    def test_is_strands_project_valid(self, mock_strands_project):
        """Test checking if a directory is a valid Strands project (valid case)."""
        assert is_strands_project(mock_strands_project) is True

    def test_is_strands_project_invalid(self, temp_dir):
        """Test checking if a directory is a valid Strands project (invalid case)."""
        assert is_strands_project(temp_dir) is False

    @patch("strands_cli.commands.generate.create_helm_template_files")
    @patch("strands_cli.commands.generate.render_from_file")
    @patch("strands_cli.commands.generate.is_strands_project")
    @patch("strands_cli.commands.generate.load_values_file")
    @patch("strands_cli.commands.generate.parse_set_values")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.cwd")
    def test_generate_helm_chart_success(
        self, mock_cwd, mock_mkdir,
        mock_parse_set_values, mock_load_values, mock_is_strands_project,
        mock_render_from_file, mock_create_helm_template_files,
        mock_strands_project
    ):
        """Test generating a Helm chart (success case)."""
        # Mock the current working directory to be the test project
        mock_cwd.return_value = mock_strands_project
        mock_is_strands_project.return_value = True

        # Mock values
        mock_load_values.return_value = {"key1": "value1"}
        mock_parse_set_values.return_value = {"key2": "value2"}

        # Set values for command
        set_values = ("image.repository=my-registry/my-image",)

        # Call the function
        generate_helm_chart(set_values=set_values)

        # Verify function calls
        mock_is_strands_project.assert_called_once()
        mock_parse_set_values.assert_called_once_with(set_values)

        # Verify directories were created
        assert mock_mkdir.call_count >= 2, "Should create helm and templates directories"

        # Verify that templates are rendered
        assert mock_render_from_file.call_count >= 3, "Should render Chart.yaml, VALUES.md, and values.yaml"
        mock_create_helm_template_files.assert_called_once()

    @patch("strands_cli.commands.generate.create_helm_template_files")
    @patch("strands_cli.commands.generate.render_from_file")
    @patch("strands_cli.commands.generate.is_strands_project")
    @patch("strands_cli.commands.generate.console")
    @patch("strands_cli.commands.generate.parse_set_values")
    @patch("pathlib.Path.cwd")
    def test_generate_helm_chart_with_set_flags(
        self, mock_cwd, mock_parse_set_values,
        mock_console, mock_is_strands_project,
        mock_render_from_file, mock_create_helm_template_files,
        mock_strands_project
    ):
        """Test generating a Helm chart with --set flags following Helm conventions."""
        # Mock the current working directory to be the test project
        mock_cwd.return_value = mock_strands_project
        mock_is_strands_project.return_value = True

        # Mock parsed values to simulate --set flags
        mock_parse_set_values.return_value = {
            "image": {
                "repository": "test-registry/test-image",
                "tag": "v1.0"
            },
            "serviceAccount": {
                "name": "test-sa",
                "create": False
            }
        }

        # Set values that would come from --set flags
        set_values = (
            "image.repository=test-registry/test-image",
            "image.tag=v1.0",
            "serviceAccount.name=test-sa",
            "serviceAccount.create=false"
        )

        # Call the function with the set values
        generate_helm_chart(set_values=set_values)

        # Verify parse_set_values was called
        mock_parse_set_values.assert_called_once_with(set_values)

        # Verify template rendering
        render_calls = mock_render_from_file.call_args_list

        # Find the values.yaml rendering call
        values_call = None
        for call in render_calls:
            if "values.yaml.j2" in str(call[0][0]):
                values_call = call
                break

        assert values_call is not None, "Should render values.yaml.j2 template"

        # Check context passed to the values template
        context = values_call[0][1]  # Second arg is the context
        assert "values" in context

        # The values dict is now nested in the context
        values_dict = context["values"]

        # Verify the values that should be passed
        assert "image" in values_dict
        assert values_dict["image"]["repository"] == "test-registry/test-image"
        assert values_dict["image"]["tag"] == "v1.0"
        assert "serviceAccount" in values_dict
        assert values_dict["serviceAccount"]["name"] == "test-sa"
        assert values_dict["serviceAccount"]["create"] is False

        # Check that warning messages about service account were printed
        assert mock_console.print.call_count >= 3

        # Verify that Helm chart files are generated
        assert mock_render_from_file.call_count >= 3, "Should render Chart.yaml, VALUES.md, and values.yaml"
        mock_create_helm_template_files.assert_called_once()

    @patch("strands_cli.commands.generate.is_strands_project")
    @patch("pathlib.Path.cwd")
    def test_generate_helm_chart_not_in_project_dir(self, mock_cwd, mock_is_strands_project, temp_dir):
        """Test generating a Helm chart when not in a Strands agent project directory."""
        # Mock the current working directory to be outside a project
        mock_cwd.return_value = temp_dir
        mock_is_strands_project.return_value = False

        # Expect a ValueError
        with pytest.raises(ValueError, match="Are you in a Strands agent project directory"):
            generate_helm_chart(set_values=tuple())

    @patch("strands_cli.commands.generate.is_strands_project")
    @patch("strands_cli.commands.generate.load_values_file")
    @patch("pathlib.Path.cwd")
    def test_generate_helm_chart_values_file_not_found(
        self, mock_cwd, mock_load_values, mock_is_strands_project, mock_strands_project
    ):
        """Test generating a Helm chart with a non-existent values file."""
        # Mock the current working directory to be the test project
        mock_cwd.return_value = mock_strands_project
        mock_is_strands_project.return_value = True

        # Mock values file not found
        mock_load_values.side_effect = FileNotFoundError("Values file not found")

        # Expect a FileNotFoundError
        with pytest.raises(FileNotFoundError, match="Values file not found"):
            generate_helm_chart(set_values=tuple(), values_file="non_existent.yaml")

    @patch("strands_cli.commands.generate.is_strands_project")
    @patch("strands_cli.commands.generate.render_template")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.cwd")
    def test_generate_k8s_manifests_success(
        self, mock_cwd, mock_mkdir, mock_render_template, mock_is_strands_project,
        mock_strands_project, temp_dir
    ):
        """Test generating Kubernetes manifests (success case)."""
        # Mock the current working directory to be the test project
        mock_cwd.return_value = mock_strands_project
        mock_is_strands_project.return_value = True

        # Use the default output directory, which will create it under the project dir
        output_dir = "deployment/k8s"

        # Mock template rendering
        mock_render_template.return_value = "rendered content"

        # Call the function
        generate_k8s_manifests(namespace="test-namespace", output_dir=output_dir)

        # Verify directory was created
        mock_mkdir.assert_called_once()

        # Verify render_template was called for each manifest
        assert mock_render_template.call_count >= 5  # At least 5 manifests

    @patch("strands_cli.commands.generate.is_strands_project")
    @patch("pathlib.Path.cwd")
    def test_generate_k8s_manifests_not_in_project_dir(self, mock_cwd, mock_is_strands_project, temp_dir):
        """Test generating Kubernetes manifests when not in a Strands agent project directory."""
        # Mock the current working directory to be outside a project
        mock_cwd.return_value = temp_dir
        mock_is_strands_project.return_value = False

        # Use default output directory
        output_dir = "deployment/k8s"

        # Expect a ValueError
        with pytest.raises(ValueError, match="Are you in a Strands agent project directory"):
            generate_k8s_manifests(namespace="test-namespace", output_dir=output_dir)