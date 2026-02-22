"""Tests: config hygiene and secret checks for routing_decision."""

from __future__ import annotations

from copy import deepcopy

import pytest

from runtime_validator.validator import InvariantViolation, runtime_invariants
from .fixtures import VALID_MINIMAL_DECISION


def test_no_sk_in_valid_examples(example_files_valid):
    for path in example_files_valid:
        content = path.read_text(encoding="utf-8")
        assert "sk-" not in content, f"Found 'sk-' in {path.name}"


def test_sk_in_reason_codes_raises():
    payload = deepcopy(VALID_MINIMAL_DECISION)
    payload["reason_codes"] = ["sk-fake"]
    with pytest.raises(InvariantViolation, match="sk-"):
        runtime_invariants(payload)


def test_apikey_literal_injection_raises():
    payload = deepcopy(VALID_MINIMAL_DECISION)
    payload["constraints"]["apiKey"] = "literal-value"
    with pytest.raises(InvariantViolation, match="apiKey"):
        runtime_invariants(payload)
