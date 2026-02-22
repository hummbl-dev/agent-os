# contracts/logging

Structured logging contract — defines the canonical log format for all runtimes.

## Status

v0.1 implemented.

Decision events must include routing context via `routing_decision_id` or `meta.routing_decision`.

## Structure

```
schemas/            # Draft 2020-12 JSON Schema
runtime_validator/  # Schema + runtime invariant checks + canonical types
examples/           # Valid and invalid example events
tests/              # Pytest contract suite
```
