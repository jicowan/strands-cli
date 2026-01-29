"""Tests for Docker authentication error handling."""

import subprocess
from unittest.mock import patch, MagicMock

import pytest

from strands_cli.utils.docker import build_docker_image, build_multi_arch_docker_image


class TestDockerAuthHandling:
    """Tests for Docker authentication error handling."""

    @patch("strands_cli.utils.docker.check_docker_installed")
    @patch("subprocess.run")
    def test_build_docker_image_auth_error(self, mock_subprocess_run, mock_check_docker):
        """Test handling of authentication errors when pushing Docker images."""
        # Mock Docker is installed
        mock_check_docker.return_value = True

        # Setup mocks for tag command (success) and push command (auth failure)
        def mock_run_side_effect(cmd, *args, **kwargs):
            if "push" in cmd:
                # Create a mock process that returns auth error for push command
                mock_process = MagicMock()
                mock_process.returncode = 1
                mock_process.stderr = "authentication required"
                return mock_process
            # Return successful completion for other commands
            return MagicMock(returncode=0)

        mock_subprocess_run.side_effect = mock_run_side_effect

        # Test inputs
        project_dir = MagicMock()
        project_dir.name = "test-project"
        registry = "test-registry"
        tag = "latest"

        # Call the function
        success, message = build_docker_image(
            project_dir=project_dir,
            tag=tag,
            registry=registry,
            push=True
        )

        # Verify result
        assert success is False
        assert f"not currently logged in to {registry}" in message
        assert "Please login and try again" in message

    @patch("strands_cli.utils.docker.check_docker_installed")
    @patch("strands_cli.utils.docker.check_buildx_installed")
    @patch("subprocess.run")
    def test_build_multi_arch_image_auth_error(
        self, mock_subprocess_run, mock_check_buildx, mock_check_docker
    ):
        """Test handling of authentication errors when pushing multi-arch Docker images."""
        # Mock Docker and BuildX are installed
        mock_check_docker.return_value = True
        mock_check_buildx.return_value = True

        # Mock subprocess.run for buildx command to return auth error
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stderr = "denied: access to repository denied"
        mock_subprocess_run.return_value = mock_process

        # Test inputs
        project_dir = MagicMock()
        project_name = "test-project"
        dockerfile_path = MagicMock()
        registry = "test-registry"
        tag = "latest"

        # Call the function
        success, message = build_multi_arch_docker_image(
            project_dir=project_dir,
            project_name=project_name,
            dockerfile_path=dockerfile_path,
            tag=tag,
            registry=registry,
            push=True
        )

        # Verify result
        assert success is False
        assert f"not currently logged in to {registry}" in message
        assert "Please login and try again" in message

    @patch("strands_cli.utils.docker.check_docker_installed")
    @patch("subprocess.run")
    def test_build_docker_image_subprocess_auth_error(self, mock_subprocess_run, mock_check_docker):
        """Test handling of authentication errors raised as subprocess exceptions."""
        # Mock Docker is installed
        mock_check_docker.return_value = True

        # Mock subprocess.run to raise SubprocessError with auth error message
        auth_error = subprocess.SubprocessError("unauthorized: authentication required")
        mock_subprocess_run.side_effect = [MagicMock(), auth_error]  # tag succeeds, push fails

        # Test inputs
        project_dir = MagicMock()
        project_dir.name = "test-project"
        registry = "test-registry"
        tag = "latest"

        # Call the function
        success, message = build_docker_image(
            project_dir=project_dir,
            tag=tag,
            registry=registry,
            push=True
        )

        # Verify result
        assert success is False
        assert f"not currently logged in to {registry}" in message
        assert "Please login and try again" in message