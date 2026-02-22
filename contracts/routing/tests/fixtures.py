"""Pure-data fixtures for routing contract tests."""

from __future__ import annotations

VALID_MINIMAL_DECISION = {
    "decision_id": "dec-900",
    "timestamp": "2026-02-07T12:20:00Z",
    "task_id": "job-route-900",
    "trace_id": "trace-route-900",
    "selected_provider": "openrouter",
    "selected_model": "gpt-4o-mini",
    "fallback_chain": [
        {"provider": "openrouter", "model": "gpt-4o-mini"},
        {"provider": "anthropic", "model": "claude-3-haiku"},
    ],
    "reason_codes": ["COST_SOFT_CAP", "LATENCY_TARGET"],
    "constraints": {
        "privacy_class": "internal",
        "latency_target_ms": 500,
    },
}

INVALID_COST_WITHOUT_CURRENCY = {
    **VALID_MINIMAL_DECISION,
    "cost_estimate": 0.02,
}

INVALID_EMPTY_FALLBACK_CHAIN = {
    **VALID_MINIMAL_DECISION,
    "fallback_chain": [],
}

INVALID_REASON_CODE_FORMAT = {
    **VALID_MINIMAL_DECISION,
    "reason_codes": ["cost_soft_cap"],
}
