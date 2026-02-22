"""Tests: JSON Schema validation for routing_decision."""

from __future__ import annotations

import pytest
from jsonschema import ValidationError

from runtime_validator.validator import validate_schema
from .conftest import load_json
from .fixtures import (
    INVALID_COST_WITHOUT_CURRENCY,
    INVALID_EMPTY_FALLBACK_CHAIN,
    INVALID_REASON_CODE_FORMAT,
)


def test_valid_examples_schema(example_files_valid):
    for path in example_files_valid:
        validate_schema(load_json(path))


def test_invalid_example_schema(invalid_example_path):
    with pytest.raises(ValidationError):
        validate_schema(load_json(invalid_example_path))


@pytest.mark.parametrize(
    "payload",
    [
        INVALID_COST_WITHOUT_CURRENCY,
        INVALID_EMPTY_FALLBACK_CHAIN,
        INVALID_REASON_CODE_FORMAT,
    ],
)
def test_schema_rejects_invalid_payloads(payload):
    with pytest.raises(ValidationError):
        validate_schema(payload)
