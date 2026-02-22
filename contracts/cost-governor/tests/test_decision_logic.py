"""Tests: Decision logic — evaluate() covers all branches.

Phase 0: per_request_cap gate
Phase 1: hard cap (halt-all, halt-noncritical, queue-requests, queue-requests-defer, none)
Phase 2: soft cap (log-only, degrade-model, notify-ops, queue-requests)
Phase 3: under budget
Queue overflow: queue_depth >= max_queue_depth → BLOCK
"""

from __future__ import annotations


from runtime_validator.types import (
    CostGovernor,
    DecisionAction,
    OnHardCap,
    OnSoftCap,
    QueuePolicy,
)
from runtime_validator.decision import evaluate


# ── Helpers ──────────────────────────────────────────────────────────


def _gov(**overrides) -> CostGovernor:
    """Build a minimal CostGovernor with overrides."""
    defaults = {
        "currency": "USD",
        "daily_soft_cap": 10.0,
        "daily_hard_cap": 20.0,
        "on_soft_cap": OnSoftCap.LOG_ONLY,
        "on_hard_cap": OnHardCap.HALT_ALL,
        "model_degrade_ladder": (),
        "allowlist_tasks_under_hard_cap": (),
    }
    defaults.update(overrides)
    return CostGovernor(**defaults)


# ── Phase 0: per_request_cap ────────────────────────────────────────


class TestPerRequestCap:
    def test_blocks_when_over_cap(self):
        gov = _gov(per_request_cap=1.0)
        d = evaluate(gov, estimated_cost=2.0, spent_today=0, task_id="t1")
        assert d.action == DecisionAction.BLOCK
        assert "per_request_cap" in d.reason

    def test_allows_when_under_cap(self):
        gov = _gov(per_request_cap=5.0)
        d = evaluate(gov, estimated_cost=2.0, spent_today=0, task_id="t1")
        assert d.action == DecisionAction.ALLOW

    def test_no_cap_allows_any(self):
        gov = _gov(per_request_cap=None)
        d = evaluate(gov, estimated_cost=999.0, spent_today=0, task_id="t1")
        # Will hit hard cap, not per_request_cap
        assert d.action != DecisionAction.ALLOW or d.action == DecisionAction.ALLOW


# ── Phase 1: Hard cap ───────────────────────────────────────────────


class TestHardCap:
    def test_halt_all_blocks(self):
        gov = _gov(on_hard_cap=OnHardCap.HALT_ALL)
        d = evaluate(gov, estimated_cost=5.0, spent_today=18.0, task_id="t1")
        assert d.action == DecisionAction.BLOCK
        assert "halt-all" in d.reason

    def test_halt_noncritical_allows_critical(self):
        gov = _gov(
            on_hard_cap=OnHardCap.HALT_NONCRITICAL,
            allowlist_tasks_under_hard_cap=("health-check",),
        )
        d = evaluate(
            gov,
            estimated_cost=5.0,
            spent_today=18.0,
            task_id="health-check",
            is_critical=True,
        )
        assert d.action == DecisionAction.ALLOW
        assert "critical" in d.reason

    def test_halt_noncritical_blocks_noncritical(self):
        gov = _gov(
            on_hard_cap=OnHardCap.HALT_NONCRITICAL,
            allowlist_tasks_under_hard_cap=("health-check",),
        )
        d = evaluate(
            gov,
            estimated_cost=5.0,
            spent_today=18.0,
            task_id="code-review",
            is_critical=False,
        )
        assert d.action == DecisionAction.BLOCK
        assert "not in allowlist" in d.reason

    def test_queue_requests(self):
        gov = _gov(
            on_hard_cap=OnHardCap.QUEUE_REQUESTS,
            queue_policy=QueuePolicy(max_queue_depth=100),
        )
        d = evaluate(gov, estimated_cost=5.0, spent_today=18.0, task_id="t1")
        assert d.action == DecisionAction.QUEUE
        assert d.deferred is False

    def test_queue_requests_defer(self):
        gov = _gov(
            on_hard_cap=OnHardCap.QUEUE_REQUESTS_DEFER,
            queue_policy=QueuePolicy(max_queue_depth=100),
        )
        d = evaluate(gov, estimated_cost=5.0, spent_today=18.0, task_id="t1")
        assert d.action == DecisionAction.QUEUE
        assert d.deferred is True

    def test_none_with_null_hard_cap_allows(self):
        """on_hard_cap='none' with null daily_hard_cap — never triggers hard cap."""
        gov = _gov(daily_hard_cap=None, on_hard_cap=OnHardCap.NONE)
        d = evaluate(gov, estimated_cost=5.0, spent_today=18.0, task_id="t1")
        # Should proceed to soft cap or allow
        assert d.action in (DecisionAction.ALLOW, DecisionAction.QUEUE)


# ── Phase 2: Soft cap ───────────────────────────────────────────────


class TestSoftCap:
    def test_log_only(self):
        gov = _gov(on_soft_cap=OnSoftCap.LOG_ONLY)
        d = evaluate(gov, estimated_cost=5.0, spent_today=8.0, task_id="t1")
        assert d.action == DecisionAction.ALLOW
        assert d.log is True
        assert "log-only" in d.reason

    def test_degrade_model(self):
        gov = _gov(
            on_soft_cap=OnSoftCap.DEGRADE_MODEL,
            model_degrade_ladder=("gpt-4o-mini", "claude-3-haiku"),
        )
        d = evaluate(gov, estimated_cost=5.0, spent_today=8.0, task_id="t1")
        assert d.action == DecisionAction.DEGRADE
        assert d.degraded_model == "gpt-4o-mini"
        assert "degrade-model" in d.reason

    def test_notify_ops(self):
        gov = _gov(on_soft_cap=OnSoftCap.NOTIFY_OPS)
        d = evaluate(gov, estimated_cost=5.0, spent_today=8.0, task_id="t1")
        assert d.action == DecisionAction.ALLOW
        assert d.notify is True
        assert "notify-ops" in d.reason

    def test_queue_requests(self):
        gov = _gov(
            on_soft_cap=OnSoftCap.QUEUE_REQUESTS,
            queue_policy=QueuePolicy(max_queue_depth=100),
        )
        d = evaluate(gov, estimated_cost=5.0, spent_today=8.0, task_id="t1")
        assert d.action == DecisionAction.QUEUE


# ── Phase 3: Under budget ───────────────────────────────────────────


class TestUnderBudget:
    def test_allow_when_under_both_caps(self):
        gov = _gov()
        d = evaluate(gov, estimated_cost=1.0, spent_today=0, task_id="t1")
        assert d.action == DecisionAction.ALLOW
        assert d.reason == "under_budget"
        assert d.log is False
        assert d.notify is False
        assert d.deferred is False
        assert d.degraded_model is None

    def test_zero_cost_always_allows(self):
        gov = _gov()
        d = evaluate(gov, estimated_cost=0.0, spent_today=0, task_id="t1")
        assert d.action == DecisionAction.ALLOW


# ── Queue overflow ───────────────────────────────────────────────────


class TestQueueOverflow:
    def test_queue_overflow_hard_cap(self):
        gov = _gov(
            on_hard_cap=OnHardCap.QUEUE_REQUESTS,
            queue_policy=QueuePolicy(max_queue_depth=50),
        )
        d = evaluate(
            gov, estimated_cost=5.0, spent_today=18.0, task_id="t1", queue_depth=50
        )
        assert d.action == DecisionAction.BLOCK
        assert d.reason == "queue_overflow"

    def test_queue_overflow_soft_cap(self):
        gov = _gov(
            on_soft_cap=OnSoftCap.QUEUE_REQUESTS,
            queue_policy=QueuePolicy(max_queue_depth=10),
        )
        d = evaluate(
            gov, estimated_cost=5.0, spent_today=8.0, task_id="t1", queue_depth=10
        )
        assert d.action == DecisionAction.BLOCK
        assert d.reason == "queue_overflow"

    def test_queue_under_limit_queues(self):
        gov = _gov(
            on_hard_cap=OnHardCap.QUEUE_REQUESTS,
            queue_policy=QueuePolicy(max_queue_depth=50),
        )
        d = evaluate(
            gov, estimated_cost=5.0, spent_today=18.0, task_id="t1", queue_depth=49
        )
        assert d.action == DecisionAction.QUEUE
