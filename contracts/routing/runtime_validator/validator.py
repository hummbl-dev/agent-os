"""Schema and runtime invariant validation for routing_decision."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "openclaw.routing_decision.schema.json"
_schema_cache: dict[str, Any] | None = None
_validator_cache: Draft202012Validator | None = None
_API_KEY_FIELDS = {"apiKey", "api_key", "API_KEY"}


class InvariantViolation(Exception):
    """Raised when a routing decision violates runtime invariants."""


def _load_schema() -> dict[str, Any]:
    global _schema_cache
    if _schema_cache is None:
        _schema_cache = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    return _schema_cache


def _validator() -> Draft202012Validator:
    global _validator_cache
    if _validator_cache is None:
        schema = _load_schema()
        Draft202012Validator.check_schema(schema)
        _validator_cache = Draft202012Validator(schema, format_checker=FormatChecker())
    return _validator_cache


def validate_schema(data: dict[str, Any]) -> None:
    """Validate a routing decision dict against the Draft 2020-12 schema."""
    _validator().validate(data)


def runtime_invariants(data: dict[str, Any]) -> None:
    """Enforce routing invariants that complement schema checks."""
    errors: list[str] = []

    _check_timestamp(data.get("timestamp"), errors)
    _check_non_empty_ids(data, errors)
    _check_selected_matches_fallback(data, errors)
    _check_reason_codes(data.get("reason_codes"), errors)
    _check_cost_currency_pair(data, errors)
    _check_constraint_caps(data.get("constraints"), errors)
    _scan_secrets(data, errors)

    if errors:
        raise InvariantViolation(
            "RoutingDecision invariant violation(s):\n" + "\n".join(f"  • {err}" for err in errors)
        )


def _check_timestamp(value: Any, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append("timestamp must be a string in RFC3339 format")
        return
    if "T" not in value:
        errors.append("timestamp must use RFC3339 date-time format")
        return

    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        errors.append("timestamp is not a valid RFC3339 date-time")
        return

    if parsed.tzinfo is None:
        errors.append("timestamp must include timezone (Z or +/-HH:MM)")


def _check_non_empty_ids(data: dict[str, Any], errors: list[str]) -> None:
    for field in ("decision_id", "task_id", "trace_id"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} must be a non-empty string")


def _check_selected_matches_fallback(data: dict[str, Any], errors: list[str]) -> None:
    fallback_chain = data.get("fallback_chain")
    if not isinstance(fallback_chain, list) or not fallback_chain:
        errors.append("fallback_chain must be a non-empty list")
        return

    first = fallback_chain[0]
    if not isinstance(first, dict):
        errors.append("fallback_chain[0] must be an object")
        return

    selected_provider = data.get("selected_provider")
    selected_model = data.get("selected_model")
    if first.get("provider") != selected_provider or first.get("model") != selected_model:
        errors.append(
            "selected_provider/selected_model must match fallback_chain[0].provider/model"
        )


def _check_reason_codes(reason_codes: Any, errors: list[str]) -> None:
    if not isinstance(reason_codes, list) or not reason_codes:
        errors.append("reason_codes must be a non-empty list")
        return

    if any(not isinstance(code, str) or not code.strip() for code in reason_codes):
        errors.append("reason_codes entries must be non-empty strings")
        return

    if len(reason_codes) != len(set(reason_codes)):
        errors.append("reason_codes must not contain duplicates")

    if reason_codes != sorted(reason_codes):
        errors.append("reason_codes must be sorted for deterministic ordering")


def _check_cost_currency_pair(data: dict[str, Any], errors: list[str]) -> None:
    if "cost_estimate" in data and "currency" not in data:
        errors.append("currency is required when cost_estimate is present")


def _check_constraint_caps(constraints: Any, errors: list[str]) -> None:
    if not isinstance(constraints, dict):
        return

    soft = constraints.get("daily_soft_cap")
    hard = constraints.get("daily_hard_cap")
    if soft is not None and hard is not None and soft > hard:
        errors.append("constraints.daily_soft_cap must be <= constraints.daily_hard_cap")


def _scan_secrets(obj: Any, errors: list[str], path: str = "$") -> None:
    if isinstance(obj, str):
        if "sk-" in obj:
            errors.append(f"secret-like 'sk-' substring found at {path}")
        return

    if isinstance(obj, dict):
        for key, value in obj.items():
            key_path = f"{path}.{key}"
            if isinstance(key, str) and "sk-" in key:
                errors.append(f"secret-like 'sk-' substring found in key at {key_path}")

            if key in _API_KEY_FIELDS:
                if not isinstance(value, str) or not value.startswith("${"):
                    errors.append(f"literal {key} detected at {key_path}; use ${{ENV_VAR}}")

            _scan_secrets(value, errors, key_path)
        return

    if isinstance(obj, list):
        for idx, item in enumerate(obj):
            _scan_secrets(item, errors, f"{path}[{idx}]")
