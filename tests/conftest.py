"""Shared test fixtures for strands-cli tests."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing.

    Yields:
        Path: Path to the temporary directory.
    """
    temp_dir = Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


@pytest.fixture
def mock_strands_project(temp_dir: Path) -> Generator[Path, None, None]:
    """Create a mock Strands agent project structure.

    Args:
        temp_dir: Temporary directory fixture.

    Yields:
        Path: Path to the mock project directory.
    """
    project_dir = temp_dir / "test-agent"
    project_dir.mkdir()

    # Create basic directory structure
    (project_dir / "agent").mkdir()
    (project_dir / "api").mkdir()
    (project_dir / "deployment").mkdir()
    (project_dir / "deployment" / "docker").mkdir()
    (project_dir / "deployment" / "helm").mkdir()
    (project_dir / "deployment" / "k8s").mkdir()

    # Create a mock Dockerfile
    dockerfile_path = project_dir / "deployment" / "docker" / "Dockerfile"
    dockerfile_path.write_text("FROM python:3.12-slim\n")

    yield project_dir