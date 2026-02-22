"""Tests: cross-contract integration between logging and routing contracts."""

from __future__ import annotations

import json

from jsonschema import Draft202012Validator, FormatChecker

from runtime_validator.validator import runtime_invariants, validate_schema
from .conftest import EXAMPLES_DIR, ROOT, load_json

ROUTING_ROOT = ROOT.parent / "routing"
ROUTING_SCHEMA_PATH = ROUTING_ROOT / "schemas" / "openclaw.routing_decision.schema.json"
ROUTING_EXAMPLE_PATH = ROUTING_ROOT / "examples" / "example-minimal.json"
LOGGING_DECISION_EXAMPLE_PATH = EXAMPLES_DIR / "example-with-decision.json"


def test_decision_event_can_reference_routing_decision_id():
    routing_decision = load_json(ROUTING_EXAMPLE_PATH)
    log_event = load_json(LOGGING_DECISION_EXAMPLE_PATH)

    log_event["routing_decision_id"] = routing_decision["decision_id"]
    log_event["trace_id"] = routing_decision["trace_id"]

    validate_schema(log_event)
    runtime_invariants(log_event)


def test_embedded_routing_decision_can_validate_against_routing_schema():
    routing_decision = load_json(ROUTING_EXAMPLE_PATH)
    log_event = load_json(LOGGING_DECISION_EXAMPLE_PATH)

    log_event.pop("routing_decision_id", None)
    log_event["trace_id"] = routing_decision["trace_id"]
    log_event["meta"] = {"routing_decision": routing_decision}

    validate_schema(log_event)
    runtime_invariants(log_event)

    routing_schema = json.loads(ROUTING_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator(routing_schema, format_checker=FormatChecker()).validate(
        log_event["meta"]["routing_decision"]
    )
