"""Tests for the init command."""

import os
import re
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from strands_cli.commands.init import create_project, create_directory_structure, create_project_files


class TestInitCommand:
    """Tests for init command."""

    def test_create_directory_structure(self, temp_dir: Path):
        """Test creating the project directory structure."""
        project_dir = temp_dir / "test-agent"
        project_dir.mkdir()

        create_directory_structure(project_dir)

        # Check that required directories were created
        assert (project_dir / "agent").exists()
        assert (project_dir / "api").exists()
        assert (project_dir / "deployment" / "docker").exists()
        assert (project_dir / "scripts").exists()

        # Helm and k8s directories should NOT be created during initialization
        assert not (project_dir / "deployment" / "helm").exists()
        assert not (project_dir / "deployment" / "k8s").exists()

    @patch("strands_cli.commands.init.render_from_file")
    def test_create_project_files(self, mock_render_from_file, temp_dir: Path):
        """Test creating project files."""
        project_dir = temp_dir / "test-agent"
        project_dir.mkdir()

        # Create the directory structure first
        create_directory_structure(project_dir)

        # Create project files
        context = {
            "name": "test-agent",
            "description": "Test agent",
            "package_name": "test_agent",
            "class_name": "TestAgent",
        }
        # Mock render_from_file to simulate file creation for testing
        mock_render_from_file.return_value = None

        create_project_files(project_dir, context)

        # Verify render_from_file was called for key files but not for Helm files
        assert mock_render_from_file.call_count > 0

        # Check that Helm Chart files are not being generated
        helm_related_calls = [
            call for call in mock_render_from_file.call_args_list
            if "helm/Chart.yaml" in str(call) or
               "helm/values.yaml" in str(call) or
               "helm/VALUES.md" in str(call)
        ]
        assert len(helm_related_calls) == 0, "Helm files should not be generated during init"

    @patch("strands_cli.commands.init.create_directory_structure")
    @patch("strands_cli.commands.init.create_project_files")
    def test_create_project_success(
        self, mock_create_project_files, mock_create_directory_structure, temp_dir: Path
    ):
        """Test creating a new project (success case)."""
        name = "test-agent"
        description = "Test agent"
        template = "default"
        output_dir = str(temp_dir)

        # Create the project
        create_project(name, description, template, output_dir)

        # Verify the functions were called
        mock_create_directory_structure.assert_called_once()
        mock_create_project_files.assert_called_once()

    def test_create_project_invalid_name(self, temp_dir: Path):
        """Test creating a project with an invalid name."""
        name = "test agent"  # Contains a space
        description = "Test agent"
        template = "default"
        output_dir = str(temp_dir)

        # Expect a ValueError due to the invalid name
        with pytest.raises(ValueError, match="Agent name must contain only alphanumeric"):
            create_project(name, description, template, output_dir)

    def test_create_project_directory_exists(self, temp_dir: Path):
        """Test creating a project when the directory already exists."""
        name = "existing-agent"
        description = "Test agent"
        template = "default"
        output_dir = str(temp_dir)

        # Create the directory beforehand
        project_dir = temp_dir / name
        project_dir.mkdir()

        # Expect a FileExistsError
        with pytest.raises(FileExistsError, match="Directory already exists"):
            create_project(name, description, template, output_dir)