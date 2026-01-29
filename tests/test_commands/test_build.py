"""Tests for the build command."""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from strands_cli.commands.build import build_image


class TestBuildCommand:
    """Tests for build command."""

    @patch("strands_cli.commands.build.build_docker_image")
    @patch("pathlib.Path.cwd")
    def test_build_image_success(self, mock_cwd, mock_build_docker_image, mock_strands_project):
        """Test building a Docker image (success case)."""
        # Mock the current working directory to be the test project
        mock_cwd.return_value = mock_strands_project

        # Mock successful image build
        mock_build_docker_image.return_value = (True, "Success message")

        # Call the build_image function
        build_image()

        # Verify build_docker_image was called with the correct parameters
        mock_build_docker_image.assert_called_once_with(
            project_dir=mock_strands_project,
            tag="latest",
            registry=None,
            push=False,
            multi_arch=False,
            platforms=None,
        )

    @patch("strands_cli.commands.build.build_docker_image")
    @patch("pathlib.Path.cwd")
    def test_build_image_with_custom_params(self, mock_cwd, mock_build_docker_image, mock_strands_project):
        """Test building a Docker image with custom parameters."""
        # Mock the current working directory to be the test project
        mock_cwd.return_value = mock_strands_project

        # Mock successful image build
        mock_build_docker_image.return_value = (True, "Success message")

        # Custom parameters
        tag = "v1.0"
        registry = "my-registry"
        push = True

        # Call the build_image function with custom parameters
        build_image(push=push, registry=registry, tag=tag)

        # Verify build_docker_image was called with the correct parameters
        mock_build_docker_image.assert_called_once_with(
            project_dir=mock_strands_project,
            tag=tag,
            registry=registry,
            push=push,
            multi_arch=False,
            platforms=None,
        )

    @patch("pathlib.Path.cwd")
    def test_build_image_not_in_project_dir(self, mock_cwd, temp_dir):
        """Test building an image when not in a Strands agent project directory."""
        # Mock the current working directory to be outside a project
        mock_cwd.return_value = temp_dir

        # Expect a ValueError
        with pytest.raises(ValueError, match="Are you in a Strands agent project directory"):
            build_image()

    @patch("strands_cli.commands.build.build_docker_image")
    @patch("pathlib.Path.cwd")
    def test_build_image_build_failure(self, mock_cwd, mock_build_docker_image, mock_strands_project):
        """Test building a Docker image when the build fails."""
        # Mock the current working directory to be the test project
        mock_cwd.return_value = mock_strands_project

        # Mock failed image build
        mock_build_docker_image.return_value = (False, "Error message")

        # Expect a RuntimeError
        with pytest.raises(RuntimeError, match="Failed to build Docker image"):
            build_image()

    @patch("strands_cli.commands.build.build_docker_image")
    @patch("pathlib.Path.cwd")
    @patch.dict(os.environ, {"ECR_REGISTRY": "ecr-registry"})
    def test_build_image_push_with_env_registry(self, mock_cwd, mock_build_docker_image, mock_strands_project):
        """Test pushing an image with registry from environment."""
        # Mock the current working directory to be the test project
        mock_cwd.return_value = mock_strands_project

        # Mock successful image build
        mock_build_docker_image.return_value = (True, "Success message")

        # Call the build_image function with push but no explicit registry
        build_image(push=True)

        # Verify build_docker_image was called with the registry from environment
        mock_build_docker_image.assert_called_once_with(
            project_dir=mock_strands_project,
            tag="latest",
            registry="ecr-registry",
            push=True,
            multi_arch=False,
            platforms=None,
        )

    @patch("pathlib.Path.cwd")
    def test_build_image_push_no_registry(self, mock_cwd, mock_strands_project):
        """Test pushing an image without a registry specified."""
        # Mock the current working directory to be the test project
        mock_cwd.return_value = mock_strands_project

        # Expect a ValueError for push without registry
        with pytest.raises(ValueError, match="No registry specified for push"):
            build_image(push=True)