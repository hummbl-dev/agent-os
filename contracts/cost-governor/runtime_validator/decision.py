"""Decision engine for cost_governor.

Deterministic, pure-function evaluation of a single request against
a validated CostGovernor configuration.

Evaluation order:
  Phase 0: per_request_cap gate
  Phase 1: hard cap check
  Phase 2: soft cap check
  Phase 3: under budget → ALLOW
  Queue overflow: if QUEUE and queue_depth >= max_queue_depth → BLOCK
"""

from __future__ import annotations

from runtime_validator.types import (
    CostGovernor,
    Decision,
    DecisionAction,
    OnHardCap,
    OnSoftCap,
)


def evaluate(
    gov: CostGovernor,
    *,
    estimated_cost: float,
    spent_today: float,
    task_id: str,
    is_critical: bool = False,
    queue_depth: int = 0,
) -> Decision:
    """Evaluate a single request against the cost governor.

    Parameters
    ----------
    gov : CostGovernor
        Validated cost governor configuration.
    estimated_cost : float
        Estimated cost of this request.
    spent_today : float
        Total spend so far in the current daily window.
    task_id : str
        The task/operation identifier.
    is_critical : bool
        Whether this task is in the allowlist (derived by caller).
    queue_depth : int
        Current number of requests in the queue.

    Returns
    -------
    Decision
    """

    # ── Phase 0: Per-request cap gate ────────────────────────────────
    if gov.per_request_cap is not None and estimated_cost > gov.per_request_cap:
        return Decision(
            action=DecisionAction.BLOCK,
            reason=(
                f"estimated_cost ({estimated_cost}) exceeds "
                f"per_request_cap ({gov.per_request_cap})"
            ),
        )

    projected = spent_today + estimated_cost

    # ── Phase 1: Hard cap check ──────────────────────────────────────
    if gov.daily_hard_cap is not None and projected > gov.daily_hard_cap:
        match gov.on_hard_cap:
            case OnHardCap.HALT_ALL:
                return Decision(
                    action=DecisionAction.BLOCK,
                    reason="hard_cap_exceeded: halt-all",
                )

            case OnHardCap.HALT_NONCRITICAL:
                if is_critical:
                    return Decision(
                        action=DecisionAction.ALLOW,
                        reason=f"hard_cap_exceeded: halt-noncritical, '{task_id}' is critical",
                    )
                return Decision(
                    action=DecisionAction.BLOCK,
                    reason=f"hard_cap_exceeded: halt-noncritical, '{task_id}' not in allowlist",
                )

            case OnHardCap.QUEUE_REQUESTS:
                decision = Decision(
                    action=DecisionAction.QUEUE,
                    reason="hard_cap_exceeded: queue-requests",
                )
                return _apply_queue_overflow(gov, decision, queue_depth)

            case OnHardCap.QUEUE_REQUESTS_DEFER:
                decision = Decision(
                    action=DecisionAction.QUEUE,
                    reason="hard_cap_exceeded: queue-requests-defer",
                    deferred=True,
                )
                return _apply_queue_overflow(gov, decision, queue_depth)

            case OnHardCap.NONE:
                # Invariant: none is only valid when daily_hard_cap is null.
                # If we got here, daily_hard_cap is not null — invariant violation.
                return Decision(
                    action=DecisionAction.BLOCK,
                    reason="invariant_violation: on_hard_cap='none' with non-null daily_hard_cap",
                )

    # ── Phase 2: Soft cap check ──────────────────────────────────────
    if projected > gov.daily_soft_cap:
        match gov.on_soft_cap:
            case OnSoftCap.LOG_ONLY:
                return Decision(
                    action=DecisionAction.ALLOW,
                    reason="soft_cap_exceeded: log-only",
                    log=True,
                )

            case OnSoftCap.DEGRADE_MODEL:
                degraded = gov.model_degrade_ladder[0] if gov.model_degrade_ladder else None
                return Decision(
                    action=DecisionAction.DEGRADE,
                    reason="soft_cap_exceeded: degrade-model",
                    degraded_model=degraded,
                )

            case OnSoftCap.NOTIFY_OPS:
                return Decision(
                    action=DecisionAction.ALLOW,
                    reason="soft_cap_exceeded: notify-ops",
                    notify=True,
                )

            case OnSoftCap.QUEUE_REQUESTS:
                decision = Decision(
                    action=DecisionAction.QUEUE,
                    reason="soft_cap_exceeded: queue-requests",
                )
                return _apply_queue_overflow(gov, decision, queue_depth)

    # ── Phase 3: Under budget ────────────────────────────────────────
    return Decision(
        action=DecisionAction.ALLOW,
        reason="under_budget",
    )


def _apply_queue_overflow(
    gov: CostGovernor,
    decision: Decision,
    queue_depth: int,
) -> Decision:
    """Check queue overflow and convert QUEUE → BLOCK if full."""
    if gov.queue_policy is not None:
        max_depth = gov.queue_policy.max_queue_depth
        if queue_depth >= max_depth:
            return Decision(
                action=DecisionAction.BLOCK,
                reason="queue_overflow",
            )
    return decision
