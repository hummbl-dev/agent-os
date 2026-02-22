"""Tests: JSON Schema validation of cost_governor configs.

Validates tier example files and invalid payloads against the
Draft 2020-12 JSON Schema.
"""

from __future__ import annotations

import pytest
from jsonschema import ValidationError

from runtime_validator.validator import validate_schema


class TestTierExamplesPassSchema:
    """All tier2-5 cost_governor blocks must validate against schema."""

    def test_tier2_validates(self, tier_configs):
        cg = tier_configs["tier2-minimal.cloud"]["cost_governor"]
        validate_schema(cg)  # should not raise

    def test_tier3_validates(self, tier_configs):
        cg = tier_configs["tier3-balanced.openrouter"]["cost_governor"]
        validate_schema(cg)

    def test_tier4_validates(self, tier_configs):
        cg = tier_configs["tier4-pro.anthropic"]["cost_governor"]
        validate_schema(cg)

    def test_tier5_validates(self, tier_configs):
        cg = tier_configs["tier5-enterprise.autonomous"]["cost_governor"]
        validate_schema(cg)


class TestTier1HasNoGovernor:
    """Tier 1 config must NOT have a cost_governor key."""

    def test_tier1_no_cost_governor(self, tier_configs):
        cfg = tier_configs["tier1-free.local"]
        assert "cost_governor" not in cfg


class TestSchemaRejectsInvalid:
    """Invalid payloads must be rejected by schema validation."""

    def test_missing_currency(self):
        from tests.fixtures import INVALID_MISSING_CURRENCY

        with pytest.raises(ValidationError):
            validate_schema(INVALID_MISSING_CURRENCY)

    def test_bad_soft_cap_enum(self):
        from tests.fixtures import INVALID_BAD_SOFT_CAP_ENUM

        with pytest.raises(ValidationError):
            validate_schema(INVALID_BAD_SOFT_CAP_ENUM)

    def test_queue_policy_null_rejected(self):
        from tests.fixtures import INVALID_QUEUE_POLICY_NULL

        with pytest.raises(ValidationError):
            validate_schema(INVALID_QUEUE_POLICY_NULL)

    def test_sk_in_ladder_rejected(self):
        from tests.fixtures import INVALID_SK_IN_LADDER

        with pytest.raises(ValidationError):
            validate_schema(INVALID_SK_IN_LADDER)

    def test_degrade_empty_ladder_rejected(self):
        """Schema allOf if/then enforces non-empty ladder for degrade-model."""
        from tests.fixtures import INVALID_DEGRADE_EMPTY_LADDER

        with pytest.raises(ValidationError):
            validate_schema(INVALID_DEGRADE_EMPTY_LADDER)

    def test_halt_noncritical_empty_allowlist_rejected(self):
        """Schema allOf if/then enforces non-empty allowlist for halt-noncritical."""
        from tests.fixtures import INVALID_HALT_NONCRITICAL_EMPTY_ALLOWLIST

        with pytest.raises(ValidationError):
            validate_schema(INVALID_HALT_NONCRITICAL_EMPTY_ALLOWLIST)

    def test_queue_action_missing_policy_rejected(self):
        """Schema allOf if/then enforces queue_policy presence for queue-* actions."""
        from tests.fixtures import INVALID_QUEUE_MISSING_POLICY

        with pytest.raises(ValidationError):
            validate_schema(INVALID_QUEUE_MISSING_POLICY)
