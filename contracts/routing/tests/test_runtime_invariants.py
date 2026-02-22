"""Tests: runtime invariant checks for routing_decision."""

from __future__ import annotations

from copy import deepcopy

import pytest

from runtime_validator.validator import InvariantViolation, runtime_invariants
from .fixtures import VALID_MINIMAL_DECISION


def test_timestamp_parse_failure():
    payload = deepcopy(VALID_MINIMAL_DECISION)
    payload["timestamp"] = "not-a-date"
    with pytest.raises(InvariantViolation, match="timestamp"):
        runtime_invariants(payload)


def test_selected_must_match_first_fallback():
    payload = deepcopy(VALID_MINIMAL_DECISION)
    payload["selected_model"] = "mismatch-model"
    with pytest.raises(InvariantViolation, match="fallback_chain"):
        runtime_invariants(payload)


def test_reason_codes_sorted_and_unique():
    payload = deepcopy(VALID_MINIMAL_DECISION)
    payload["reason_codes"] = ["Z_LAST", "A_FIRST"]
    with pytest.raises(InvariantViolation, match="sorted"):
        runtime_invariants(payload)

    payload = deepcopy(VALID_MINIMAL_DECISION)
    payload["reason_codes"] = ["DUP", "DUP"]
    with pytest.raises(InvariantViolation, match="duplicates"):
        runtime_invariants(payload)


def test_empty_ids_raise():
    for field in ("decision_id", "task_id", "trace_id"):
        payload = deepcopy(VALID_MINIMAL_DECISION)
        payload[field] = ""
        with pytest.raises(InvariantViolation, match=field):
            runtime_invariants(payload)


def test_constraint_soft_cap_not_above_hard_cap():
    payload = deepcopy(VALID_MINIMAL_DECISION)
    payload["constraints"]["daily_soft_cap"] = 12.0
    payload["constraints"]["daily_hard_cap"] = 9.0
    with pytest.raises(InvariantViolation, match="daily_soft_cap"):
        runtime_invariants(payload)
