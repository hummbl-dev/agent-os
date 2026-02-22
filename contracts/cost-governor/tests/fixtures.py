"""Pure-data test fixtures for cost-governor tests.

Golden payloads (valid and invalid) for use in tests.
No pytest dependency — this module is plain data.
"""

from __future__ import annotations

# ── Valid cost_governor dicts (matching canonical schema) ────────────

VALID_MINIMAL = {
    "currency": "USD",
    "daily_soft_cap": 4.00,
    "daily_hard_cap": 5.00,
    "on_soft_cap": "log-only",
    "on_hard_cap": "halt-all",
    "model_degrade_ladder": [],
    "allowlist_tasks_under_hard_cap": [],
}

VALID_WITH_DEGRADE = {
    "currency": "USD",
    "daily_soft_cap": 20.00,
    "daily_hard_cap": 25.00,
    "on_soft_cap": "degrade-model",
    "on_hard_cap": "halt-noncritical",
    "model_degrade_ladder": ["gpt-4o-mini", "claude-3-haiku"],
    "allowlist_tasks_under_hard_cap": ["health-check", "billing-webhook"],
}

VALID_WITH_QUEUE = {
    "currency": "USD",
    "daily_soft_cap": 80.00,
    "daily_hard_cap": 100.00,
    "on_soft_cap": "notify-ops",
    "on_hard_cap": "queue-requests",
    "model_degrade_ladder": [],
    "allowlist_tasks_under_hard_cap": [],
    "queue_policy": {
        "enabled": True,
        "max_queue_depth": 200,
        "default_ttl_seconds": 300,
        "drop_policy": "drop-noncritical-first",
    },
}

VALID_ENTERPRISE = {
    "currency": "USD",
    "daily_soft_cap": 500.00,
    "daily_hard_cap": None,
    "on_soft_cap": "notify-ops",
    "on_hard_cap": "none",
    "model_degrade_ladder": [],
    "allowlist_tasks_under_hard_cap": [],
}

# ── Invalid cost_governor dicts ──────────────────────────────────────

INVALID_MISSING_CURRENCY = {
    # Missing "currency"
    "daily_soft_cap": 4.00,
    "daily_hard_cap": 5.00,
    "on_soft_cap": "log-only",
    "on_hard_cap": "halt-all",
    "model_degrade_ladder": [],
    "allowlist_tasks_under_hard_cap": [],
}

INVALID_BAD_SOFT_CAP_ENUM = {
    "currency": "USD",
    "daily_soft_cap": 4.00,
    "daily_hard_cap": 5.00,
    "on_soft_cap": "explode",  # not a valid enum value
    "on_hard_cap": "halt-all",
    "model_degrade_ladder": [],
    "allowlist_tasks_under_hard_cap": [],
}

INVALID_QUEUE_POLICY_NULL = {
    "currency": "USD",
    "daily_soft_cap": 80.00,
    "daily_hard_cap": 100.00,
    "on_soft_cap": "notify-ops",
    "on_hard_cap": "queue-requests",
    "model_degrade_ladder": [],
    "allowlist_tasks_under_hard_cap": [],
    "queue_policy": None,  # must be object, not null
}

INVALID_SK_IN_LADDER = {
    "currency": "USD",
    "daily_soft_cap": 20.00,
    "daily_hard_cap": 25.00,
    "on_soft_cap": "degrade-model",
    "on_hard_cap": "halt-all",
    "model_degrade_ladder": ["sk-secret-model-key"],
    "allowlist_tasks_under_hard_cap": [],
}

INVALID_DEGRADE_EMPTY_LADDER = {
    "currency": "USD",
    "daily_soft_cap": 20.00,
    "daily_hard_cap": 25.00,
    "on_soft_cap": "degrade-model",
    "on_hard_cap": "halt-all",
    "model_degrade_ladder": [],  # must be non-empty when degrade-model
    "allowlist_tasks_under_hard_cap": [],
}

INVALID_HALT_NONCRITICAL_EMPTY_ALLOWLIST = {
    "currency": "USD",
    "daily_soft_cap": 20.00,
    "daily_hard_cap": 25.00,
    "on_soft_cap": "log-only",
    "on_hard_cap": "halt-noncritical",
    "model_degrade_ladder": [],
    "allowlist_tasks_under_hard_cap": [],  # must be non-empty when halt-noncritical
}

INVALID_SOFT_GT_HARD = {
    "currency": "USD",
    "daily_soft_cap": 30.00,
    "daily_hard_cap": 25.00,  # soft > hard
    "on_soft_cap": "log-only",
    "on_hard_cap": "halt-all",
    "model_degrade_ladder": [],
    "allowlist_tasks_under_hard_cap": [],
}

INVALID_NULL_HARD_NOT_NONE = {
    "currency": "USD",
    "daily_soft_cap": 500.00,
    "daily_hard_cap": None,
    "on_soft_cap": "notify-ops",
    "on_hard_cap": "halt-all",  # must be "none" when hard_cap is null
    "model_degrade_ladder": [],
    "allowlist_tasks_under_hard_cap": [],
}

INVALID_QUEUE_MISSING_POLICY = {
    "currency": "USD",
    "daily_soft_cap": 80.00,
    "daily_hard_cap": 100.00,
    "on_soft_cap": "queue-requests",
    "on_hard_cap": "halt-all",
    "model_degrade_ladder": [],
    "allowlist_tasks_under_hard_cap": [],
    # Missing queue_policy — required when on_soft_cap == queue-requests
}

INVALID_SECRET_APIKEY = {
    "currency": "USD",
    "daily_soft_cap": 4.00,
    "daily_hard_cap": 5.00,
    "on_soft_cap": "log-only",
    "on_hard_cap": "halt-all",
    "model_degrade_ladder": ["apiKey-literal-value"],
    "allowlist_tasks_under_hard_cap": [],
}
