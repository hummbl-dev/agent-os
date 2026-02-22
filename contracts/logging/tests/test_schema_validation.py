"""Tests: JSON Schema validation for log_event."""

from __future__ import annotations

import pytest
from jsonschema import ValidationError

from runtime_validator.validator import validate_schema
from .conftest import load_json
from .fixtures import (
    INVALID_COST_WITHOUT_CURRENCY,
    INVALID_DECISION_MISSING_ROUTING_LINK,
    INVALID_DECISION_MISSING_REQUIRED,
    INVALID_TOKENS_IN_ONLY,
    VALID_DECISION_WITH_EMBEDDED_ROUTING,
)


def test_valid_examples_schema(example_files_valid):
    for path in example_files_valid:
        validate_schema(load_json(path))


def test_invalid_example_schema(invalid_example_path):
    with pytest.raises(ValidationError):
        validate_schema(load_json(invalid_example_path))


def test_tokens_in_without_tokens_out():
    with pytest.raises(ValidationError):
        validate_schema(INVALID_TOKENS_IN_ONLY)


def test_cost_estimate_without_currency():
    with pytest.raises(ValidationError):
        validate_schema(INVALID_COST_WITHOUT_CURRENCY)


def test_decision_without_required_fields():
    with pytest.raises(ValidationError):
        validate_schema(INVALID_DECISION_MISSING_REQUIRED)


def test_decision_event_requires_routing_link():
    with pytest.raises(ValidationError):
        validate_schema(INVALID_DECISION_MISSING_ROUTING_LINK)


def test_decision_event_accepts_embedded_routing_decision():
    validate_schema(VALID_DECISION_WITH_EMBEDDED_ROUTING)
