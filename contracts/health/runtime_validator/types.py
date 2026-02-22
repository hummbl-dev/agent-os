"""Canonical types for the health contract."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class ProbeType(str, enum.Enum):
    LIVENESS = "liveness"
    READINESS = "readiness"
    STARTUP = "startup"


class HealthState(str, enum.Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class HealthCheckResult:
    name: str
    probe_type: ProbeType
    status: HealthState
    message: str
    duration_ms: float
    timestamp: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HealthSummary:
    total: int
    healthy: int
    degraded: int
    unhealthy: int
    unknown: int


@dataclass(frozen=True, slots=True)
class HealthStatus:
    status: HealthState
    timestamp: str
    service: str
    checks: tuple[HealthCheckResult, ...]
    summary: HealthSummary
    version: str | None = None
    latency_ms: float | None = None
    meta: dict[str, Any] = field(default_factory=dict)
