"""Tests for the main CLI entry point."""

from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from strands_cli.cli import cli, init_command, build_command, generate_helm_command, generate_k8s_command


class TestCli:
    """Tests for the main CLI entry point."""

    def test_cli_help(self):
        """Test the CLI help output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Strands CLI tool" in result.output

    @patch("strands_cli.commands.init.create_project")
    def test_init_command(self, mock_create_project):
        """Test the init command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "test-agent", "--description", "Test agent"])
        assert result.exit_code == 0
        mock_create_project.assert_called_once_with(
            "test-agent", "Test agent", "default", "."
        )

    @patch("strands_cli.commands.init.create_project")
    def test_init_command_error(self, mock_create_project):
        """Test the init command with error."""
        mock_create_project.side_effect = ValueError("Error message")
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "test-agent"])
        assert result.exit_code == 1
        assert "Error creating project" in result.output

    @patch("strands_cli.commands.build.build_image")
    def test_build_command(self, mock_build_image):
        """Test the build command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["build", "--tag", "test"])
        assert result.exit_code == 0
        mock_build_image.assert_called_once_with(
            push=False,
            registry=None,
            tag="test",
            multi_arch=False,
            platforms=None
        )

    @patch("strands_cli.commands.build.build_image")
    def test_build_command_error(self, mock_build_image):
        """Test the build command with error."""
        mock_build_image.side_effect = ValueError("Error message")
        runner = CliRunner()
        result = runner.invoke(cli, ["build"])
        assert result.exit_code == 1
        assert "Error building image" in result.output

    @patch("strands_cli.commands.generate.generate_helm_chart")
    def test_generate_helm_command(self, mock_generate_helm_chart):
        """Test the generate helm command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["generate", "helm", "--set", "key1=value1", "--values-file", "values.yaml"])
        assert result.exit_code == 0
        mock_generate_helm_chart.assert_called_once_with(("key1=value1",), "values.yaml")

    @patch("strands_cli.commands.generate.generate_helm_chart")
    def test_generate_helm_command_with_set_flags(self, mock_generate_helm_chart):
        """Test the generate helm command with --set flags following Helm conventions."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "generate", "helm",
            "--set", "image.repository=my-registry/my-image",
            "--set", "image.tag=v1.0",
            "--set", "serviceAccount.name=bedrock-sa"
        ])
        assert result.exit_code == 0
        mock_generate_helm_chart.assert_called_once_with(
            ("image.repository=my-registry/my-image", "image.tag=v1.0", "serviceAccount.name=bedrock-sa"), None
        )

    @patch("strands_cli.commands.generate.generate_helm_chart")
    def test_generate_helm_command_error(self, mock_generate_helm_chart):
        """Test the generate helm command with error."""
        mock_generate_helm_chart.side_effect = ValueError("Error message")
        runner = CliRunner()
        result = runner.invoke(cli, ["generate", "helm"])
        assert result.exit_code == 1
        assert "Error generating Helm chart" in result.output

    @patch("strands_cli.commands.generate.generate_k8s_manifests")
    def test_generate_k8s_command(self, mock_generate_k8s_manifests):
        """Test the generate k8s command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["generate", "k8s", "--namespace", "test", "--output-dir", "k8s"])
        assert result.exit_code == 0
        mock_generate_k8s_manifests.assert_called_once_with("test", "k8s", None, None, None)

    @patch("strands_cli.commands.generate.generate_k8s_manifests")
    def test_generate_k8s_command_with_new_flags(self, mock_generate_k8s_manifests):
        """Test the generate k8s command with the new flags."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "generate", "k8s",
            "--namespace", "test",
            "--output-dir", "k8s",
            "--image-uri", "my-registry/my-image",
            "--image-tag", "v1.0",
            "--service-account", "my-service-account"
        ])
        assert result.exit_code == 0
        mock_generate_k8s_manifests.assert_called_once_with(
            "test", "k8s", "my-registry/my-image", "v1.0", "my-service-account"
        )

    @patch("strands_cli.commands.generate.generate_k8s_manifests")
    def test_generate_k8s_command_error(self, mock_generate_k8s_manifests):
        """Test the generate k8s command with error."""
        mock_generate_k8s_manifests.side_effect = ValueError("Error message")
        runner = CliRunner()
        result = runner.invoke(cli, ["generate", "k8s"])
        assert result.exit_code == 1
        assert "Error generating Kubernetes manifests" in result.output