"""Schema validation and runtime invariant checks for cost_governor.

validate_schema()     — validates a raw dict against the Draft 2020-12 JSON Schema.
runtime_invariants()  — enforces cross-field invariants that JSON Schema cannot express.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from runtime_validator.types import CostGovernor, OnHardCap, OnSoftCap

# ── Schema loading ───────────────────────────────────────────────────

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "openclaw.cost_governor.schema.json"
_schema_cache: dict | None = None


def _load_schema() -> dict:
    global _schema_cache
    if _schema_cache is None:
        _schema_cache = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    return _schema_cache


# ── Public API ───────────────────────────────────────────────────────


class InvariantViolation(Exception):
    """Raised when a cost_governor config violates a runtime invariant."""


def validate_schema(data: dict[str, Any]) -> None:
    """Validate a cost_governor dict against the Draft 2020-12 JSON Schema.

    Raises jsonschema.ValidationError on failure.
    """
    schema = _load_schema()
    Draft202012Validator.check_schema(schema)  # meta-validate once
    validator = Draft202012Validator(schema)
    validator.validate(data)


def runtime_invariants(gov: CostGovernor) -> None:
    """Enforce all cross-field runtime invariants.

    Collects all violations, then raises InvariantViolation with all errors.
    """
    errors: list[str] = []

    # 1) daily_soft_cap <= daily_hard_cap when hard cap is set
    if gov.daily_hard_cap is not None:
        if gov.daily_soft_cap > gov.daily_hard_cap:
            errors.append(
                f"daily_soft_cap ({gov.daily_soft_cap}) must be "
                f"<= daily_hard_cap ({gov.daily_hard_cap})"
            )

    # 2) daily_hard_cap == null => on_hard_cap must be "none"
    if gov.daily_hard_cap is None and gov.on_hard_cap != OnHardCap.NONE:
        errors.append(
            f"daily_hard_cap is null so on_hard_cap must be 'none', "
            f"got '{gov.on_hard_cap.value}'"
        )

    # 3) degrade-model => model_degrade_ladder must be non-empty
    if gov.on_soft_cap == OnSoftCap.DEGRADE_MODEL and not gov.model_degrade_ladder:
        errors.append(
            "on_soft_cap='degrade-model' requires a non-empty model_degrade_ladder"
        )

    # 4) halt-noncritical => allowlist_tasks_under_hard_cap must be non-empty
    if gov.on_hard_cap == OnHardCap.HALT_NONCRITICAL and not gov.allowlist_tasks_under_hard_cap:
        errors.append(
            "on_hard_cap='halt-noncritical' requires a non-empty "
            "allowlist_tasks_under_hard_cap"
        )

    # 5) No secrets: recursive scan for "sk-" and bare apiKey literals
    _check_no_secrets(gov, errors)

    # 6) queue_policy required when cap actions use queue-*
    _needs_queue = (
        gov.on_soft_cap == OnSoftCap.QUEUE_REQUESTS
        or gov.on_hard_cap in (OnHardCap.QUEUE_REQUESTS, OnHardCap.QUEUE_REQUESTS_DEFER)
    )
    if _needs_queue and gov.queue_policy is None:
        errors.append(
            "queue_policy is required when on_soft_cap or on_hard_cap "
            "uses a queue-* action"
        )

    if errors:
        raise InvariantViolation(
            "CostGovernor invariant violation(s):\n"
            + "\n".join(f"  • {e}" for e in errors)
        )


def runtime_invariants_dict(data: dict[str, Any]) -> None:
    """Run runtime invariants directly on a raw dict (without constructing CostGovernor).

    Useful for validating JSON-loaded configs before deserialization.
    """
    errors: list[str] = []

    soft = data.get("daily_soft_cap", 0)
    hard = data.get("daily_hard_cap")
    on_soft = data.get("on_soft_cap", "")
    on_hard = data.get("on_hard_cap", "")
    ladder = data.get("model_degrade_ladder", [])
    allowlist = data.get("allowlist_tasks_under_hard_cap", [])
    qp = data.get("queue_policy")

    if hard is not None and soft > hard:
        errors.append(f"daily_soft_cap ({soft}) must be <= daily_hard_cap ({hard})")

    if hard is None and on_hard != "none":
        errors.append(f"daily_hard_cap is null so on_hard_cap must be 'none', got '{on_hard}'")

    if on_soft == "degrade-model" and not ladder:
        errors.append("on_soft_cap='degrade-model' requires a non-empty model_degrade_ladder")

    if on_hard == "halt-noncritical" and not allowlist:
        errors.append(
            "on_hard_cap='halt-noncritical' requires a non-empty allowlist_tasks_under_hard_cap"
        )

    _check_no_secrets_raw(data, errors)

    needs_queue = on_soft == "queue-requests" or on_hard in ("queue-requests", "queue-requests-defer")
    if needs_queue and qp is None:
        errors.append("queue_policy is required when on_soft_cap or on_hard_cap uses a queue-* action")

    if errors:
        raise InvariantViolation(
            "CostGovernor invariant violation(s):\n"
            + "\n".join(f"  • {e}" for e in errors)
        )


# ── Secret scanning ──────────────────────────────────────────────────

_SK_PATTERN = re.compile(r"sk-", re.IGNORECASE)
_API_KEY_PATTERN = re.compile(r"apikey", re.IGNORECASE)


def _check_no_secrets(obj: object, errors: list[str], path: str = "") -> None:
    """Recursively scan all string fields in a dataclass tree for secrets."""
    if isinstance(obj, str):
        if _SK_PATTERN.search(obj):
            errors.append(f"Secret-like 'sk-' pattern found at {path}: '{obj[:30]}'")
        if _API_KEY_PATTERN.search(obj) and not obj.startswith("${"):
            errors.append(f"Bare apiKey literal found at {path}: '{obj[:30]}'")
        return

    if isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            _check_no_secrets(item, errors, path=f"{path}[{i}]")
        return

    if isinstance(obj, enum_base_check := type) and isinstance(obj, str):
        return

    if hasattr(obj, "__dataclass_fields__"):
        from dataclasses import fields as dc_fields

        for f in dc_fields(obj):
            val = getattr(obj, f.name)
            _check_no_secrets(val, errors, path=f"{path}.{f.name}" if path else f.name)
    elif isinstance(obj, (int, float, bool, type(None))):
        return
    elif hasattr(obj, "value") and isinstance(obj.value, str):
        # Enum member
        _check_no_secrets(obj.value, errors, path=path)


def _check_no_secrets_raw(obj: Any, errors: list[str], path: str = "") -> None:
    """Recursively scan a raw dict/list/str tree for secrets."""
    if isinstance(obj, str):
        if _SK_PATTERN.search(obj):
            errors.append(f"Secret-like 'sk-' pattern found at {path}: '{obj[:30]}'")
        if _API_KEY_PATTERN.search(obj) and not obj.startswith("${"):
            errors.append(f"Bare apiKey literal found at {path}: '{obj[:30]}'")
        return

    if isinstance(obj, dict):
        for k, v in obj.items():
            _check_no_secrets_raw(v, errors, path=f"{path}.{k}" if path else k)
        return

    if isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            _check_no_secrets_raw(item, errors, path=f"{path}[{i}]")
        return
