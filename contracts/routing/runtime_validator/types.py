"""Canonical types for the routing contract."""

from __future__ import annotations

import enum
from dataclasses import dataclass


class PrivacyClass(str, enum.Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    CONFIDENTIAL = "confidential"


@dataclass(frozen=True, slots=True)
class RouteTarget:
    provider: str
    model: str


@dataclass(frozen=True, slots=True)
class ConstraintSnapshot:
    privacy_class: PrivacyClass
    latency_target_ms: int
    cap_action: str | None = None
    per_request_cap: float | None = None
    daily_soft_cap: float | None = None
    daily_hard_cap: float | None = None
    max_tokens: int | None = None


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    decision_id: str
    timestamp: str
    task_id: str
    trace_id: str
    selected_provider: str
    selected_model: str
    fallback_chain: tuple[RouteTarget, ...]
    reason_codes: tuple[str, ...]
    constraints: ConstraintSnapshot
    cost_estimate: float | None = None
    currency: str | None = None
    policy_hash: str | None = None
