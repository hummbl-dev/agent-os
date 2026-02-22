"""Schema and runtime invariant validation for health status payloads."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "openclaw.health_status.schema.json"
_schema_cache: dict[str, Any] | None = None
_validator_cache: Draft202012Validator | None = None
_API_KEY_FIELDS = {"apiKey", "api_key", "API_KEY"}
_ALLOWED_STATES = {"healthy", "degraded", "unhealthy", "unknown"}


class InvariantViolation(Exception):
    """Raised when a health payload violates runtime invariants."""


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
    """Validate a health status payload against Draft 2020-12 schema."""
    _validator().validate(data)


def runtime_invariants(data: dict[str, Any]) -> None:
    """Enforce cross-field invariants and hygiene checks for health payloads."""
    errors: list[str] = []

    _check_timestamp(data.get("timestamp"), "timestamp", errors)
    _check_service_name(data.get("service"), errors)
    _check_checks(data.get("checks"), errors)
    _check_summary_and_status(data, errors)
    _scan_secrets(data, errors)

    if errors:
        raise InvariantViolation(
            "HealthStatus invariant violation(s):\n" + "\n".join(f"  • {err}" for err in errors)
        )


def _check_timestamp(value: Any, field: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{field} must be a string in RFC3339 format")
        return
    if "T" not in value:
        errors.append(f"{field} must use RFC3339 date-time format")
        return

    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        errors.append(f"{field} is not a valid RFC3339 date-time")
        return

    if parsed.tzinfo is None:
        errors.append(f"{field} must include timezone (Z or +/-HH:MM)")


def _check_service_name(value: Any, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append("service must be a non-empty string")


def _check_checks(checks: Any, errors: list[str]) -> None:
    if not isinstance(checks, list) or not checks:
        errors.append("checks must be a non-empty list")
        return

    seen_names: set[str] = set()
    for idx, check in enumerate(checks):
        path = f"checks[{idx}]"
        if not isinstance(check, dict):
            errors.append(f"{path} must be an object")
            continue

        name = check.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"{path}.name must be a non-empty string")
        elif name in seen_names:
            errors.append(f"duplicate check name: {name}")
        else:
            seen_names.add(name)

        probe_type = check.get("probe_type")
        if probe_type not in {"liveness", "readiness", "startup"}:
            errors.append(f"{path}.probe_type must be one of liveness/readiness/startup")

        status = check.get("status")
        if status not in _ALLOWED_STATES:
            errors.append(f"{path}.status must be one of healthy/degraded/unhealthy/unknown")

        _check_timestamp(check.get("timestamp"), f"{path}.timestamp", errors)


def _check_summary_and_status(data: dict[str, Any], errors: list[str]) -> None:
    checks = data.get("checks")
    summary = data.get("summary")
    if not isinstance(checks, list) or not isinstance(summary, dict):
        return

    computed = {
        "total": len(checks),
        "healthy": sum(1 for item in checks if isinstance(item, dict) and item.get("status") == "healthy"),
        "degraded": sum(1 for item in checks if isinstance(item, dict) and item.get("status") == "degraded"),
        "unhealthy": sum(1 for item in checks if isinstance(item, dict) and item.get("status") == "unhealthy"),
        "unknown": sum(1 for item in checks if isinstance(item, dict) and item.get("status") == "unknown"),
    }

    for key, expected in computed.items():
        actual = summary.get(key)
        if actual != expected:
            errors.append(f"summary.{key} must equal computed value {expected}, got {actual}")

    expected_status = _derive_status(computed)
    actual_status = data.get("status")
    if actual_status != expected_status:
        errors.append(f"status must be '{expected_status}' for current checks/summary, got '{actual_status}'")


def _derive_status(counts: dict[str, int]) -> str:
    if counts["unhealthy"] > 0:
        return "unhealthy"
    if counts["degraded"] > 0:
        return "degraded"
    if counts["healthy"] == counts["total"] and counts["total"] > 0:
        return "healthy"
    return "unknown"


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
