"""Canonical types for the logging contract."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class Level(str, enum.Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


class DecisionAction(str, enum.Enum):
    ALLOW = "ALLOW"
    DEGRADE = "DEGRADE"
    QUEUE = "QUEUE"
    BLOCK = "BLOCK"


@dataclass(frozen=True, slots=True)
class Decision:
    action: DecisionAction
    reason: str
    degraded_model: str | None = None
    deferred: bool | None = None
    notify: bool | None = None
    log: bool | None = None


@dataclass(frozen=True, slots=True)
class LogEvent:
    event_id: str
    timestamp: str
    task_id: str
    trace_id: str
    source: str
    level: Level
    message: str
    event_type: str
    provider: str | None = None
    model: str | None = None
    operation: str | None = None
    request_id: str | None = None
    response_id: str | None = None
    routing_decision_id: str | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    cost_estimate: float | None = None
    currency: str | None = None
    decision: Decision | None = None
    meta: dict[str, Any] = field(default_factory=dict)
