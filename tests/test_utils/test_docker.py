"""Tests for the Docker utility module."""

import os
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from strands_cli.utils.docker import check_docker_installed, build_docker_image


class TestDockerUtils:
    """Tests for Docker utilities."""

    @patch("subprocess.run")
    def test_check_docker_installed_success(self, mock_run):
        """Test checking if Docker is installed (success case)."""
        mock_run.return_value = MagicMock(returncode=0)

        assert check_docker_installed() is True
        mock_run.assert_called_once_with(
            ["docker", "--version"],
            capture_output=True,
            check=True,
            text=True
        )

    @patch("subprocess.run")
    def test_check_docker_installed_failure(self, mock_run):
        """Test checking if Docker is installed (failure case)."""
        mock_run.side_effect = FileNotFoundError("Docker not found")

        assert check_docker_installed() is False
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_check_docker_installed_error(self, mock_run):
        """Test checking if Docker is installed (error case)."""
        mock_run.side_effect = subprocess.SubprocessError("Docker error")

        assert check_docker_installed() is False
        mock_run.assert_called_once()

    @patch("strands_cli.utils.docker.check_docker_installed")
    @patch("subprocess.run")
    def test_build_docker_image_success(self, mock_run, mock_check_docker, mock_strands_project):
        """Test building a Docker image (success case)."""
        mock_check_docker.return_value = True
        mock_run.return_value = MagicMock(returncode=0)

        success, message = build_docker_image(mock_strands_project)

        assert success is True
        assert f"Successfully built Docker image: {mock_strands_project.name}:latest" in message
        mock_check_docker.assert_called_once()
        mock_run.assert_called_once()

    @patch("strands_cli.utils.docker.check_docker_installed")
    def test_build_docker_image_no_docker(self, mock_check_docker, mock_strands_project):
        """Test building a Docker image when Docker is not installed."""
        mock_check_docker.return_value = False

        success, message = build_docker_image(mock_strands_project)

        assert success is False
        assert "Docker is not installed" in message
        mock_check_docker.assert_called_once()

    @patch("strands_cli.utils.docker.check_docker_installed")
    def test_build_docker_image_no_dockerfile(self, mock_check_docker, temp_dir):
        """Test building a Docker image when Dockerfile does not exist."""
        mock_check_docker.return_value = True

        # Create a project directory without a Dockerfile
        project_dir = temp_dir / "test-agent"
        project_dir.mkdir()
        (project_dir / "deployment").mkdir()
        (project_dir / "deployment" / "docker").mkdir()

        success, message = build_docker_image(project_dir)

        assert success is False
        assert "Dockerfile not found" in message
        mock_check_docker.assert_called_once()

    @patch("strands_cli.utils.docker.check_docker_installed")
    @patch("subprocess.run")
    def test_build_docker_image_build_error(self, mock_run, mock_check_docker, mock_strands_project):
        """Test building a Docker image when build fails."""
        mock_check_docker.return_value = True
        mock_run.side_effect = subprocess.SubprocessError("Build error")

        success, message = build_docker_image(mock_strands_project)

        assert success is False
        assert "Failed to build Docker image" in message
        mock_check_docker.assert_called_once()
        mock_run.assert_called_once()

    @patch("strands_cli.utils.docker.check_docker_installed")
    @patch("subprocess.run")
    def test_build_docker_image_with_push_success(self, mock_run, mock_check_docker, mock_strands_project):
        """Test building and pushing a Docker image (success case)."""
        mock_check_docker.return_value = True
        mock_run.return_value = MagicMock(returncode=0)

        registry = "my-registry"
        success, message = build_docker_image(mock_strands_project, tag="test", registry=registry, push=True)

        assert success is True
        assert f"Successfully built and pushed Docker image: {registry}/{mock_strands_project.name}:test" in message
        mock_check_docker.assert_called_once()
        assert mock_run.call_count == 3  # build, tag, push

    @patch("strands_cli.utils.docker.check_docker_installed")
    @patch("subprocess.run")
    def test_build_docker_image_with_push_error(self, mock_run, mock_check_docker, mock_strands_project):
        """Test building and pushing a Docker image when push fails."""
        mock_check_docker.return_value = True

        # First call succeeds (build), second or third call fails (tag or push)
        def side_effect(*args, **kwargs):
            if args[0][0] == "docker" and args[0][1] == "push":
                raise subprocess.SubprocessError("Push error")
            return MagicMock(returncode=0)

        mock_run.side_effect = side_effect

        registry = "my-registry"
        success, message = build_docker_image(mock_strands_project, tag="test", registry=registry, push=True)

        assert success is False
        assert "Failed to push Docker image" in message
        mock_check_docker.assert_called_once()
        assert mock_run.call_count >= 2  # At least build and either tag or push