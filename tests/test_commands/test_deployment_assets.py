"""Tests for deployment assets generation."""

from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest

from strands_cli.commands.init import create_project
from strands_cli.commands.generate import generate_k8s_manifests


class TestDeploymentAssets:
    """Tests for deployment assets generation."""

    def test_init_does_not_generate_k8s_manifests(self, temp_dir: Path):
        """Test that the init command does not generate Kubernetes manifests or directory."""
        name = "test-agent"
        description = "Test agent"
        template = "default"
        output_dir = str(temp_dir)

        # Create the project
        create_project(name, description, template, output_dir)

        # Verify that deployment directory exists but k8s directory was NOT created
        project_dir = temp_dir / name
        deployment_dir = project_dir / "deployment"
        k8s_dir = deployment_dir / "k8s"

        assert deployment_dir.exists(), "Deployment directory should be created"
        assert not k8s_dir.exists(), "K8s directory should NOT be created by init command"

    @patch("pathlib.Path.write_text")
    @patch("strands_cli.commands.generate.render_template")
    @patch("strands_cli.commands.generate.is_strands_project")
    def test_generate_k8s_with_custom_params(
        self, mock_is_strands_project, mock_render_template, mock_write_text, temp_dir: Path
    ):
        """Test generating k8s manifests with custom parameters."""
        # Mock project validation
        mock_is_strands_project.return_value = True

        # Mock render_template to return a string
        mock_render_template.return_value = "rendered template content"

        # Set up test parameters
        namespace = "test-ns"
        output_dir = str(temp_dir)
        image_uri = "my-registry/my-image"
        image_tag = "v1.0"
        service_account = "my-service-account"

        # Call the function
        generate_k8s_manifests(
            namespace=namespace,
            output_dir=output_dir,
            image_uri=image_uri,
            image_tag=image_tag,
            service_account=service_account
        )

        # Verify that render_template was called with the correct context
        context_calls = [call for call in mock_render_template.call_args_list]

        # Should have been called at least once
        assert len(context_calls) > 0

        # Check that the context contains all our custom values
        for call_args in context_calls:
            # Context is the second argument
            context = call_args[0][1]
            assert context.get("namespace") == namespace
            assert context.get("image_repository") == image_uri
            assert context.get("image_tag") == image_tag
            assert context.get("service_account") == service_account

    @patch("pathlib.Path.write_text")
    @patch("strands_cli.commands.generate.render_template")
    @patch("strands_cli.commands.generate.is_strands_project")
    def test_generate_k8s_default_values(
        self, mock_is_strands_project, mock_render_template, mock_write_text, temp_dir: Path
    ):
        """Test generating k8s manifests with default values."""
        # Mock project validation
        mock_is_strands_project.return_value = True

        # Mock render_template to return a string
        mock_render_template.return_value = "rendered template content"

        # Set up test parameters
        namespace = "test-ns"
        output_dir = str(temp_dir)

        # Call the function without custom parameters
        generate_k8s_manifests(
            namespace=namespace,
            output_dir=output_dir
        )

        # Verify that render_template was called with default context values
        context_calls = [call for call in mock_render_template.call_args_list]

        # Should have been called at least once
        assert len(context_calls) > 0

        # Check that the context contains default values
        for call_args in context_calls:
            # Context is the second argument
            context = call_args[0][1]
            assert context.get("namespace") == namespace
            assert "image_repository" in context
            assert "image_tag" in context
            assert context.get("image_tag") == "latest"
            # Service account should not be explicitly set in context
            assert "service_account" not in context