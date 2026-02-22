# Cost-Governor Policy-as-Code

This directory contains the canonical Casbin policy model and rules for cost governance enforcement.

- `model.conf`: Casbin model for tiered cost caps (soft/hard/per-request)
- `policy.csv`: Policy table mapping tiers to allowed caps
- `policy_index.py`: Loads and enforces policy in runtime_validator

## Policy Structure
- **Subjects**: tier1, tier2, tier3
- **Objects**: daily, per_request
- **Actions**: soft_cap, hard_cap, cap
- **Value**: Numeric cap (nullable allowed)

## Enforcement
- **Policy is an upper bound**; platform configs must be ≤ policy.
- `null` caps allowed **only** via explicit `*_null_ok` rule (not default).
- Any policy edit requires review + changelog note (tighten/loosen rationale).
- All platform and example configs must not exceed policy caps for their tier.
- Monotonicity across tiers is recommended but not enforced by default.
