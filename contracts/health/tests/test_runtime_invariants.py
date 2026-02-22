"""Tests: runtime invariant checks for health status."""

from __future__ import annotations

from copy import deepcopy

import pytest

from runtime_validator.validator import InvariantViolation, runtime_invariants
from .fixtures import INVALID_DUPLICATE_NAMES, INVALID_SUMMARY_TOTAL, VALID_MINIMAL_HEALTH


def test_timestamp_parse_failure():
    payload = deepcopy(VALID_MINIMAL_HEALTH)
    payload["timestamp"] = "not-a-date"
    with pytest.raises(InvariantViolation, match="timestamp"):
        runtime_invariants(payload)


def test_duplicate_check_name_raises():
    with pytest.raises(InvariantViolation, match="duplicate check name"):
        runtime_invariants(INVALID_DUPLICATE_NAMES)


def test_summary_mismatch_raises():
    with pytest.raises(InvariantViolation, match="summary.total"):
        runtime_invariants(INVALID_SUMMARY_TOTAL)


def test_status_must_match_computed_state():
    payload = deepcopy(VALID_MINIMAL_HEALTH)
    payload["checks"][0]["status"] = "unhealthy"
    payload["summary"] = {
        "total": 1,
        "healthy": 0,
        "degraded": 0,
        "unhealthy": 1,
        "unknown": 0,
    }
    payload["status"] = "healthy"
    with pytest.raises(InvariantViolation, match="status must be"):
        runtime_invariants(payload)
