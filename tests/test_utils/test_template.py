"""Tests for the template utility module."""

import os
import tempfile
from pathlib import Path
from typing import Dict

import pytest
import yaml

from strands_cli.utils.template import (
    parse_set_values,
    load_values_file,
    get_template_environment,
)


class TestTemplateUtils:
    """Tests for template utilities."""

    def test_parse_set_values_empty(self):
        """Test parsing empty set values."""
        assert parse_set_values(tuple()) == {}

    def test_parse_set_values_simple(self):
        """Test parsing simple set values."""
        result = parse_set_values(("key=value",))
        assert result == {"key": "value"}

    def test_parse_set_values_multiple(self):
        """Test parsing multiple set values."""
        result = parse_set_values(("key1=value1", "key2=value2"))
        assert result == {"key1": "value1", "key2": "value2"}

    def test_parse_set_values_comma_separated(self):
        """Test parsing comma-separated set values."""
        result = parse_set_values(("key1=value1,key2=value2",))
        assert result == {"key1": "value1", "key2": "value2"}

    def test_parse_set_values_mixed(self):
        """Test parsing mixed set values."""
        result = parse_set_values(("key1=value1,key2=value2", "key3=value3"))
        assert result == {"key1": "value1", "key2": "value2", "key3": "value3"}

    def test_parse_set_values_nested(self):
        """Test parsing nested set values."""
        result = parse_set_values(("image.repository=my-registry/my-image",))
        assert result == {"image": {"repository": "my-registry/my-image"}}

    def test_parse_set_values_deeply_nested(self):
        """Test parsing deeply nested set values."""
        result = parse_set_values(("a.b.c.d=value",))
        assert result == {"a": {"b": {"c": {"d": "value"}}}}

    def test_parse_set_values_bool_true(self):
        """Test parsing boolean true values."""
        result = parse_set_values(("enabled=true",))
        assert result == {"enabled": True}

    def test_parse_set_values_bool_false(self):
        """Test parsing boolean false values."""
        result = parse_set_values(("enabled=false",))
        assert result == {"enabled": False}

    def test_parse_set_values_int(self):
        """Test parsing integer values."""
        result = parse_set_values(("count=123",))
        assert result == {"count": 123}

    def test_parse_set_values_float(self):
        """Test parsing float values."""
        result = parse_set_values(("value=123.45",))
        assert result == {"value": 123.45}

    def test_parse_set_values_invalid(self):
        """Test parsing invalid set values (missing equals sign)."""
        result = parse_set_values(("invalid",))
        assert result == {}

    def test_load_values_file(self, temp_dir: Path):
        """Test loading values from a YAML file."""
        values = {
            "key1": "value1",
            "key2": 123,
            "nested": {
                "key3": True,
                "key4": "value4",
            },
        }

        # Write values to a temporary file
        values_file = temp_dir / "values.yaml"
        with open(values_file, "w") as f:
            yaml.dump(values, f)

        # Load the values
        loaded_values = load_values_file(values_file)

        assert loaded_values == values

    def test_load_values_file_empty(self, temp_dir: Path):
        """Test loading values from an empty YAML file."""
        values_file = temp_dir / "empty.yaml"
        values_file.touch()

        # Load the values
        loaded_values = load_values_file(values_file)

        assert loaded_values == {}

    def test_get_template_environment(self):
        """Test getting the template environment."""
        env = get_template_environment()
        assert env is not None
        assert hasattr(env, "get_template")