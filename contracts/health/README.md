# contracts/health

Canonical health status contract for runtime liveness/readiness/startup reporting.

## Status

v0.1 implemented.

## Structure

```
schemas/            # Draft 2020-12 JSON Schema
runtime_validator/  # Schema + runtime invariant checks + canonical types
examples/           # Valid and invalid health status payloads
tests/              # Pytest contract suite
```
