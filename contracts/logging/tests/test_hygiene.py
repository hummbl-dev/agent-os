"""Tests: config hygiene and secret checks for log_event."""

from __future__ import annotations

import pytest

from runtime_validator.validator import InvariantViolation, runtime_invariants
from .conftest import load_json


def test_no_sk_in_valid_examples(example_files_valid):
    for path in example_files_valid:
        content = path.read_text(encoding="utf-8")
        assert "sk-" not in content, f"Found 'sk-' in {path.name}"


def test_sk_in_meta_raises(example_files_valid):
    data = load_json(example_files_valid[0])
    data["meta"] = {"note": "sk-fake"}
    with pytest.raises(InvariantViolation, match="sk-"):
        runtime_invariants(data)


def test_apikey_literal_injection_raises(example_files_valid):
    data = load_json(example_files_valid[0])
    data["meta"] = {"apiKey": "literal-secret-value"}
    with pytest.raises(InvariantViolation, match="apiKey"):
        runtime_invariants(data)
