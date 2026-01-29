"""Tests for the run command."""

import os
import signal
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest

from strands_cli.commands.run import (
    run_agent,
    _validate_agent_directory,
    _check_docker_installed,
    _check_docker_compose_installed,
    _generate_docker_compose_config,
    _copy_ui_template_files,
)


class TestRunCommand:
    """Tests for run command."""

    def test_validate_agent_directory_valid(self, tmp_path: Path):
        """Test validation with a valid agent directory structure."""
        # Create a mock agent directory structure
        agent_dir = tmp_path / "agent"
        api_dir = tmp_path / "api"
        deployment_dir = tmp_path / "deployment" / "docker"

        agent_dir.mkdir(parents=True)
        api_dir.mkdir(parents=True)
        deployment_dir.mkdir(parents=True)

        (agent_dir / "__init__.py").touch()
        (agent_dir / "agent.py").touch()
        (api_dir / "app.py").touch()
        (deployment_dir / "Dockerfile").touch()

        # Change to the temp directory for testing
        current_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            result = _validate_agent_directory()
            assert result is True
        finally:
            # Change back to original directory
            os.chdir(current_dir)

    def test_validate_agent_directory_invalid(self, tmp_path: Path):
        """Test validation with an invalid agent directory structure."""
        # Create an incomplete directory structure
        (tmp_path / "agent").mkdir()

        # Change to the temp directory for testing
        current_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            result = _validate_agent_directory()
            assert result is False
        finally:
            # Change back to original directory
            os.chdir(current_dir)

    @patch("docker.from_env")
    def test_check_docker_installed_success(self, mock_docker_client):
        """Test Docker installed check when Docker is available."""
        # Mock the Docker client and ping method
        mock_client = MagicMock()
        mock_docker_client.return_value = mock_client

        result = _check_docker_installed()

        assert result is True
        mock_client.ping.assert_called_once()

    @patch("docker.from_env")
    def test_check_docker_installed_failure(self, mock_docker_client):
        """Test Docker installed check when Docker is not available."""
        # Mock Docker client to raise an exception
        mock_docker_client.side_effect = Exception("Docker not available")

        result = _check_docker_installed()

        assert result is False

    @patch("subprocess.run")
    def test_check_docker_compose_installed_success(self, mock_run):
        """Test Docker Compose installed check when it's available."""
        # Mock successful subprocess run
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        result = _check_docker_compose_installed()

        assert result is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_check_docker_compose_installed_failure(self, mock_run):
        """Test Docker Compose installed check when it's not available."""
        # Mock subprocess to raise an exception
        mock_run.side_effect = FileNotFoundError("docker-compose not found")

        result = _check_docker_compose_installed()

        assert result is False

    @patch("strands_cli.commands.run._copy_ui_template_files")
    @patch("strands_cli.commands.run.render_template")
    def test_generate_docker_compose_config(self, mock_render, mock_copy_ui, tmp_path: Path):
        """Test Docker Compose configuration generation."""
        temp_dir = str(tmp_path)
        port = 8501
        agent_port = 8000
        no_ui = False
        restart = "unless-stopped"
        test_home_dir = "/test/home"

        result = _generate_docker_compose_config(
            temp_dir, port, agent_port, no_ui, restart,
            image_uri=None, aws_profile=None, home_dir=test_home_dir
        )

        # Check that UI template files were copied
        mock_copy_ui.assert_called_once()

        # Check that the Docker Compose file was rendered
        mock_render.assert_called_once()

        # Verify the Docker Compose file path was returned
        assert isinstance(result, str)
        assert "docker-compose.yml" in result

    @patch("strands_cli.commands.run.render_template")
    def test_copy_ui_template_files(self, mock_render, tmp_path: Path):
        """Test copying UI template files."""
        ui_dir = tmp_path

        _copy_ui_template_files(ui_dir)

        # Verify that render_template was called for each UI file
        assert mock_render.call_count == 3

        # Check that all necessary files were created
        file_templates = ["ui/app.py.j2", "ui/Dockerfile.j2", "ui/requirements.txt.j2"]
        output_files = ["app.py", "Dockerfile", "requirements.txt"]

        for i, template in enumerate(file_templates):
            # Extract the args from the call
            args, kwargs = mock_render.call_args_list[i]

            # Check template path
            assert args[0] == template

            # Check output path contains the expected filename
            assert output_files[i] in str(kwargs.get("output_path", ""))

    @patch("strands_cli.commands.run._validate_agent_directory")
    @patch("strands_cli.commands.run._check_docker_installed")
    @patch("strands_cli.commands.run._check_docker_compose_installed")
    @patch("strands_cli.commands.build.build_image")
    @patch("tempfile.TemporaryDirectory")
    @patch("strands_cli.commands.run._generate_docker_compose_config")
    @patch("subprocess.Popen")
    @patch("strands_cli.commands.run._print_access_info")
    def test_run_agent_foreground(
        self, mock_print_access, mock_popen, mock_generate_config,
        mock_temp_dir, mock_build_image, mock_check_compose,
        mock_check_docker, mock_validate_dir
    ):
        """Test running the agent in foreground mode."""
        # Mock directory validation, Docker checks, and build
        mock_validate_dir.return_value = True
        mock_check_docker.return_value = True
        mock_check_compose.return_value = True

        # Mock process and stdout
        mock_process = MagicMock()
        mock_process.stdout = ["Starting containers...", "Containers started"]
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        # Mock temporary directory context
        mock_context = MagicMock()
        mock_temp_dir.return_value.__enter__.return_value = "/tmp/test"

        # Mock Docker Compose config generation
        mock_generate_config.return_value = "/tmp/test/docker-compose.yml"

        # Run the agent
        run_agent(
            port=8501,
            agent_port=8000,
            no_ui=False,
            detach=False,
            build=True,
            restart="unless-stopped",
        )

        # Verify that the process was started and stdout was read
        mock_popen.assert_called_once()
        mock_print_access.assert_called_once()

        # Ensure signal handlers were set up
        assert signal.getsignal(signal.SIGINT) != signal.SIG_DFL
        assert signal.getsignal(signal.SIGTERM) != signal.SIG_DFL

        # Reset signal handlers to defaults
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)

    @patch("strands_cli.commands.run._validate_agent_directory")
    @patch("strands_cli.commands.run._check_docker_installed")
    @patch("strands_cli.commands.run._check_docker_compose_installed")
    @patch("strands_cli.commands.build.build_image")
    @patch("tempfile.TemporaryDirectory")
    @patch("strands_cli.commands.run._generate_docker_compose_config")
    @patch("subprocess.run")
    @patch("strands_cli.commands.run._print_access_info")
    def test_run_agent_detached(
        self, mock_print_access, mock_run, mock_generate_config,
        mock_temp_dir, mock_build_image, mock_check_compose,
        mock_check_docker, mock_validate_dir
    ):
        """Test running the agent in detached mode."""
        # Mock directory validation, Docker checks, and build
        mock_validate_dir.return_value = True
        mock_check_docker.return_value = True
        mock_check_compose.return_value = True

        # Mock temporary directory context
        mock_context = MagicMock()
        mock_temp_dir.return_value.__enter__.return_value = "/tmp/test"

        # Mock Docker Compose config generation
        mock_generate_config.return_value = "/tmp/test/docker-compose.yml"

        # Run the agent in detached mode
        run_agent(
            port=8501,
            agent_port=8000,
            no_ui=False,
            detach=True,
            build=True,
            restart="unless-stopped",
        )

        # Verify that Docker Compose up -d was called
        mock_run.assert_called_once()
        cmd_args = mock_run.call_args[0][0]
        assert "up" in cmd_args
        assert "-d" in cmd_args
        mock_print_access.assert_called_once()

    @patch("strands_cli.commands.run._validate_agent_directory")
    def test_run_agent_invalid_directory(self, mock_validate_dir):
        """Test running the agent in an invalid directory."""
        mock_validate_dir.return_value = False

        with pytest.raises(ValueError, match="not appear to be a valid Strands agent project"):
            run_agent(
                port=8501,
                agent_port=8000,
                no_ui=False,
                detach=False,
                build=True,
                restart="unless-stopped",
            )

    @patch("strands_cli.commands.run._validate_agent_directory")
    @patch("strands_cli.commands.run._check_docker_installed")
    def test_run_agent_no_docker(self, mock_check_docker, mock_validate_dir):
        """Test running the agent without Docker installed."""
        mock_validate_dir.return_value = True
        mock_check_docker.return_value = False

        with pytest.raises(ValueError, match="Docker is not installed"):
            run_agent(
                port=8501,
                agent_port=8000,
                no_ui=False,
                detach=False,
                build=True,
                restart="unless-stopped",
            )

