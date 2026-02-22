"""Schema and runtime invariant validation for log_event."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "openclaw.log_event.schema.json"
_schema_cache: dict[str, Any] | None = None
_validator_cache: Draft202012Validator | None = None
_API_KEY_FIELDS = {"apiKey", "api_key", "API_KEY"}


class InvariantViolation(Exception):
    """Raised when a log event violates runtime invariants."""


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


def validate_schema(event_dict: dict[str, Any]) -> None:
    """Validate a log event dict against the Draft 2020-12 schema."""
    _validator().validate(event_dict)


def runtime_invariants(event_dict: dict[str, Any]) -> None:
    """Enforce cross-field invariants and secret hygiene checks."""
    errors: list[str] = []

    _check_timestamp(event_dict.get("timestamp"), errors)
    _check_non_empty_ids(event_dict, errors)
    _check_tokens(event_dict, errors)
    _check_decision_link(event_dict, errors)
    _check_decision(event_dict.get("decision"), errors)
    _scan_secrets(event_dict, errors)

    if errors:
        raise InvariantViolation(
            "LogEvent invariant violation(s):\n" + "\n".join(f"  • {err}" for err in errors)
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


def _check_non_empty_ids(event_dict: dict[str, Any], errors: list[str]) -> None:
    for field in ("event_id", "task_id", "trace_id"):
        value = event_dict.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} must be a non-empty string")


def _check_tokens(event_dict: dict[str, Any], errors: list[str]) -> None:
    has_tokens_in = "tokens_in" in event_dict
    has_tokens_out = "tokens_out" in event_dict
    if has_tokens_in != has_tokens_out:
        errors.append("tokens_in and tokens_out must both be present when either is provided")


def _check_decision(decision: Any, errors: list[str]) -> None:
    if not isinstance(decision, dict):
        return

    action = decision.get("action")
    if action == "DEGRADE":
        degraded_model = decision.get("degraded_model")
        if not isinstance(degraded_model, str) or not degraded_model.strip():
            errors.append("decision.degraded_model is required when decision.action == DEGRADE")

    if action == "QUEUE" and decision.get("deferred") is True:
        reason = decision.get("reason")
        if not isinstance(reason, str) or "defer" not in reason.lower():
            errors.append(
                "decision.reason must include 'defer' when decision.action == QUEUE and deferred is true"
            )


def _check_decision_link(event_dict: dict[str, Any], errors: list[str]) -> None:
    if event_dict.get("event_type") != "decision":
        return

    routing_decision_id = event_dict.get("routing_decision_id")
    has_routing_decision_id = isinstance(routing_decision_id, str) and bool(routing_decision_id.strip())

    meta = event_dict.get("meta")
    has_embedded_routing_decision = (
        isinstance(meta, dict) and isinstance(meta.get("routing_decision"), dict)
    )

    if not (has_routing_decision_id or has_embedded_routing_decision):
        errors.append(
            "event_type='decision' requires routing_decision_id or meta.routing_decision"
        )

    if "routing_decision_id" in event_dict and not has_routing_decision_id:
        errors.append("routing_decision_id must be a non-empty string when provided")


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
