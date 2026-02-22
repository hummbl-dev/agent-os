"""Pure-data fixtures for logging contract tests."""

from __future__ import annotations

VALID_MINIMAL_EVENT = {
    "event_id": "evt-100",
    "timestamp": "2026-02-07T12:00:00Z",
    "task_id": "job-100",
    "trace_id": "trace-100",
    "source": "openclaw",
    "level": "INFO",
    "message": "valid event",
    "event_type": "request",
}

INVALID_TOKENS_IN_ONLY = {
    **VALID_MINIMAL_EVENT,
    "tokens_in": 12,
}

INVALID_COST_WITHOUT_CURRENCY = {
    **VALID_MINIMAL_EVENT,
    "cost_estimate": 0.42,
}

INVALID_DECISION_MISSING_REQUIRED = {
    **VALID_MINIMAL_EVENT,
    "decision": {},
}

INVALID_DECISION_MISSING_ROUTING_LINK = {
    **VALID_MINIMAL_EVENT,
    "event_type": "decision",
    "decision": {
        "action": "ALLOW",
        "reason": "policy permitted request",
    },
}

VALID_DECISION_WITH_EMBEDDED_ROUTING = {
    **VALID_MINIMAL_EVENT,
    "event_type": "decision",
    "decision": {
        "action": "QUEUE",
        "reason": "defer request to preserve latency budget",
        "deferred": True,
    },
    "meta": {
        "routing_decision": {
            "decision_id": "dec-embedded-001",
            "trace_id": "trace-100",
        }
    },
}
