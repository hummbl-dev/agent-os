"""Tests: Runtime invariants for cost_governor.

Covers cross-field invariants that JSON Schema cannot fully express,
enforced by validator.runtime_invariants() and runtime_invariants_dict().
"""

from __future__ import annotations

import pytest

from runtime_validator.types import CostGovernor, OnHardCap, OnSoftCap, QueuePolicy
from runtime_validator.validator import InvariantViolation, runtime_invariants, runtime_invariants_dict
from tests.fixtures import (
    INVALID_SOFT_GT_HARD,
    INVALID_NULL_HARD_NOT_NONE,
    INVALID_DEGRADE_EMPTY_LADDER,
    INVALID_HALT_NONCRITICAL_EMPTY_ALLOWLIST,
    INVALID_QUEUE_MISSING_POLICY,
)


# ── Helpers ──────────────────────────────────────────────────────────


def _make_governor(**overrides) -> CostGovernor:
    """Build a minimal valid CostGovernor with overrides."""
    defaults = {
        "currency": "USD",
        "daily_soft_cap": 4.00,
        "daily_hard_cap": 5.00,
        "on_soft_cap": OnSoftCap.LOG_ONLY,
        "on_hard_cap": OnHardCap.HALT_ALL,
        "model_degrade_ladder": (),
        "allowlist_tasks_under_hard_cap": (),
    }
    defaults.update(overrides)
    return CostGovernor(**defaults)


# ── Valid configs pass clean ─────────────────────────────────────────


class TestValidConfigsPass:
    def test_minimal(self):
        gov = _make_governor()
        runtime_invariants(gov)  # should not raise

    def test_with_degrade(self):
        gov = _make_governor(
            on_soft_cap=OnSoftCap.DEGRADE_MODEL,
            model_degrade_ladder=("gpt-4o-mini", "claude-3-haiku"),
        )
        runtime_invariants(gov)

    def test_with_queue(self):
        gov = _make_governor(
            on_hard_cap=OnHardCap.QUEUE_REQUESTS,
            queue_policy=QueuePolicy(),
        )
        runtime_invariants(gov)

    def test_enterprise(self):
        gov = _make_governor(
            daily_soft_cap=500.0,
            daily_hard_cap=None,
            on_soft_cap=OnSoftCap.NOTIFY_OPS,
            on_hard_cap=OnHardCap.NONE,
        )
        runtime_invariants(gov)


# ── Invariant 1: soft <= hard when hard != null ──────────────────────


class TestSoftLeqHard:
    def test_soft_gt_hard_raises(self):
        gov = _make_governor(daily_soft_cap=30.0, daily_hard_cap=25.0)
        with pytest.raises(InvariantViolation, match="daily_soft_cap.*<=.*daily_hard_cap"):
            runtime_invariants(gov)

    def test_soft_gt_hard_dict(self):
        with pytest.raises(InvariantViolation, match="daily_soft_cap.*<=.*daily_hard_cap"):
            runtime_invariants_dict(INVALID_SOFT_GT_HARD)


# ── Invariant 2: null hard => on_hard_cap == "none" ─────────────────


class TestNullHardImpliesNone:
    def test_null_hard_not_none_raises(self):
        gov = _make_governor(daily_hard_cap=None, on_hard_cap=OnHardCap.HALT_ALL)
        with pytest.raises(InvariantViolation, match="on_hard_cap must be 'none'"):
            runtime_invariants(gov)

    def test_null_hard_not_none_dict(self):
        with pytest.raises(InvariantViolation, match="on_hard_cap must be 'none'"):
            runtime_invariants_dict(INVALID_NULL_HARD_NOT_NONE)


# ── Invariant 3: degrade-model => ladder non-empty ──────────────────


class TestDegradeRequiresLadder:
    def test_degrade_empty_ladder_raises(self):
        gov = _make_governor(
            on_soft_cap=OnSoftCap.DEGRADE_MODEL,
            model_degrade_ladder=(),
        )
        with pytest.raises(InvariantViolation, match="non-empty model_degrade_ladder"):
            runtime_invariants(gov)

    def test_degrade_empty_ladder_dict(self):
        with pytest.raises(InvariantViolation, match="non-empty model_degrade_ladder"):
            runtime_invariants_dict(INVALID_DEGRADE_EMPTY_LADDER)


# ── Invariant 4: halt-noncritical => allowlist non-empty ─────────────


class TestHaltNoncriticalRequiresAllowlist:
    def test_halt_noncritical_empty_allowlist_raises(self):
        gov = _make_governor(
            on_hard_cap=OnHardCap.HALT_NONCRITICAL,
            allowlist_tasks_under_hard_cap=(),
        )
        with pytest.raises(InvariantViolation, match="non-empty allowlist_tasks"):
            runtime_invariants(gov)

    def test_halt_noncritical_empty_allowlist_dict(self):
        with pytest.raises(InvariantViolation, match="non-empty allowlist_tasks"):
            runtime_invariants_dict(INVALID_HALT_NONCRITICAL_EMPTY_ALLOWLIST)


# ── Invariant 6: queue_policy required when queue-* action ──────────


class TestQueuePolicyRequired:
    def test_queue_requests_soft_missing_policy_raises(self):
        gov = _make_governor(on_soft_cap=OnSoftCap.QUEUE_REQUESTS, queue_policy=None)
        with pytest.raises(InvariantViolation, match="queue_policy is required"):
            runtime_invariants(gov)

    def test_queue_requests_hard_missing_policy_raises(self):
        gov = _make_governor(on_hard_cap=OnHardCap.QUEUE_REQUESTS, queue_policy=None)
        with pytest.raises(InvariantViolation, match="queue_policy is required"):
            runtime_invariants(gov)

    def test_queue_requests_defer_missing_policy_raises(self):
        gov = _make_governor(on_hard_cap=OnHardCap.QUEUE_REQUESTS_DEFER, queue_policy=None)
        with pytest.raises(InvariantViolation, match="queue_policy is required"):
            runtime_invariants(gov)

    def test_queue_missing_policy_dict(self):
        with pytest.raises(InvariantViolation, match="queue_policy is required"):
            runtime_invariants_dict(INVALID_QUEUE_MISSING_POLICY)
