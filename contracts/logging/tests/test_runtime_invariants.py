"""Tests: runtime invariant checks for log_event."""

from __future__ import annotations

import pytest

from runtime_validator.validator import InvariantViolation, runtime_invariants
from .conftest import load_json
from .fixtures import VALID_DECISION_WITH_EMBEDDED_ROUTING


def test_timestamp_parse_failure(example_files_valid):
    data = load_json(example_files_valid[0])
    data["timestamp"] = "not-a-date"
    with pytest.raises(InvariantViolation, match="timestamp"):
        runtime_invariants(data)


def test_degrade_without_degraded_model(example_files_valid):
    decision_example = next(path for path in example_files_valid if path.name == "example-with-decision.json")
    data = load_json(decision_example)
    data["decision"]["action"] = "DEGRADE"
    data["decision"].pop("degraded_model", None)
    with pytest.raises(InvariantViolation, match="degraded_model"):
        runtime_invariants(data)


def test_queue_deferred_reason_missing_defer(example_files_valid):
    data = load_json(example_files_valid[0])
    data["decision"] = {
        "action": "QUEUE",
        "reason": "waiting for downstream worker",
        "deferred": True,
    }
    with pytest.raises(InvariantViolation, match="defer"):
        runtime_invariants(data)


def test_empty_task_id_trace_id_event_id(example_files_valid):
    for field in ("task_id", "trace_id", "event_id"):
        data = load_json(example_files_valid[0])
        data[field] = ""
        with pytest.raises(InvariantViolation, match=field):
            runtime_invariants(data)


def test_decision_event_requires_routing_link(example_files_valid):
    decision_example = next(path for path in example_files_valid if path.name == "example-with-decision.json")
    data = load_json(decision_example)
    data.pop("routing_decision_id", None)
    data.pop("meta", None)
    with pytest.raises(InvariantViolation, match="routing_decision_id"):
        runtime_invariants(data)


def test_decision_event_accepts_embedded_routing_decision():
    runtime_invariants(VALID_DECISION_WITH_EMBEDDED_ROUTING)
