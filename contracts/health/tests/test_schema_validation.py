"""Tests: JSON Schema validation for health status."""

from __future__ import annotations

import pytest
from jsonschema import ValidationError

from runtime_validator.validator import validate_schema
from .conftest import load_json


def test_valid_examples_schema(example_files_valid):
    for path in example_files_valid:
        validate_schema(load_json(path))


def test_invalid_example_schema(invalid_example_path):
    with pytest.raises(ValidationError):
        validate_schema(load_json(invalid_example_path))
