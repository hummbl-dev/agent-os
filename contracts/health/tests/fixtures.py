"""Pure-data fixtures for health contract tests."""

from __future__ import annotations

VALID_MINIMAL_HEALTH = {
    "status": "healthy",
    "timestamp": "2026-02-08T04:00:00Z",
    "service": "openclaw-runtime",
    "checks": [
        {
            "name": "runtime_ping",
            "probe_type": "liveness",
            "status": "healthy",
            "message": "runtime alive",
            "duration_ms": 4.2,
            "timestamp": "2026-02-08T04:00:00Z",
        }
    ],
    "summary": {
        "total": 1,
        "healthy": 1,
        "degraded": 0,
        "unhealthy": 0,
        "unknown": 0,
    },
}

INVALID_SUMMARY_TOTAL = {
    **VALID_MINIMAL_HEALTH,
    "summary": {
        "total": 2,
        "healthy": 1,
        "degraded": 0,
        "unhealthy": 0,
        "unknown": 0,
    },
}

INVALID_DUPLICATE_NAMES = {
    **VALID_MINIMAL_HEALTH,
    "checks": [
        {
            "name": "runtime_ping",
            "probe_type": "liveness",
            "status": "healthy",
            "message": "runtime alive",
            "duration_ms": 4.2,
            "timestamp": "2026-02-08T04:00:00Z",
        },
        {
            "name": "runtime_ping",
            "probe_type": "readiness",
            "status": "healthy",
            "message": "runtime ready",
            "duration_ms": 3.3,
            "timestamp": "2026-02-08T04:00:01Z",
        },
    ],
    "summary": {
        "total": 2,
        "healthy": 2,
        "degraded": 0,
        "unhealthy": 0,
        "unknown": 0,
    },
}
