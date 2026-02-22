"""Canonical types for the cost_governor contract.

All field names match the contract schema exactly. No aliases.
Invariant validation lives in validator.py, not here.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Optional


# ── Enums (canonical string values) ─────────────────────────────────


class OnSoftCap(str, enum.Enum):
    """Actions triggered when daily spend crosses daily_soft_cap."""

    LOG_ONLY = "log-only"
    DEGRADE_MODEL = "degrade-model"
    NOTIFY_OPS = "notify-ops"
    QUEUE_REQUESTS = "queue-requests"


class OnHardCap(str, enum.Enum):
    """Actions triggered when daily spend crosses daily_hard_cap."""

    HALT_ALL = "halt-all"
    HALT_NONCRITICAL = "halt-noncritical"
    QUEUE_REQUESTS = "queue-requests"
    QUEUE_REQUESTS_DEFER = "queue-requests-defer"
    NONE = "none"


class DropPolicy(str, enum.Enum):
    """Queue overflow drop policy."""

    DROP_OLDEST = "drop-oldest"
    DROP_NEWEST = "drop-newest"
    DROP_NONCRITICAL_FIRST = "drop-noncritical-first"


class DecisionAction(str, enum.Enum):
    """Possible outcomes from the decision engine."""

    ALLOW = "allow"
    BLOCK = "block"
    QUEUE = "queue"
    DEGRADE = "degrade"


# ── Sub-objects ──────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class ModelDegradeStep:
    """One entry in model_degrade_ladder (just a model identifier string)."""

    model: str


@dataclass(frozen=True, slots=True)
class QueuePolicy:
    """Queue policy configuration."""

    enabled: bool = True
    max_queue_depth: int = 1000
    default_ttl_seconds: int = 3600
    drop_policy: DropPolicy = DropPolicy.DROP_NONCRITICAL_FIRST


@dataclass(frozen=True, slots=True)
class SpendMonitoring:
    """Optional spend monitoring configuration."""

    enabled: bool = True
    alert_emails: tuple[str, ...] = ()
    daily_report: bool = False
    anomaly_detection: bool = False
    alert_threshold_percent: float = 15.0


# ── Root aggregate ───────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class CostGovernor:
    """Canonical cost_governor configuration object.

    Field names match the contract schema exactly.
    All cross-field invariants are enforced in validator.runtime_invariants(),
    NOT in __post_init__.
    """

    currency: str
    daily_soft_cap: float
    daily_hard_cap: Optional[float]
    on_soft_cap: OnSoftCap
    on_hard_cap: OnHardCap
    model_degrade_ladder: tuple[str, ...] = ()
    allowlist_tasks_under_hard_cap: tuple[str, ...] = ()
    per_request_cap: Optional[float] = None
    reset_timezone: str = "UTC"
    queue_policy: Optional[QueuePolicy] = None
    spend_monitoring: Optional[SpendMonitoring] = None


# ── Decision result ──────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class Decision:
    """Result of evaluating a request against a CostGovernor."""

    action: DecisionAction
    reason: str
    deferred: bool = False
    degraded_model: Optional[str] = None
    log: bool = False
    notify: bool = False
