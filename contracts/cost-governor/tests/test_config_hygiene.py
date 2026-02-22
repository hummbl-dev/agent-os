"""Tests: Config hygiene — no secrets in configs.

Scans tier example configs and synthetic payloads for:
- "sk-" prefixed strings (API key patterns)
- bare apiKey literals (not wrapped in ${...})
"""

from __future__ import annotations

import pytest

from runtime_validator.validator import InvariantViolation, runtime_invariants, runtime_invariants_dict
from runtime_validator.types import CostGovernor, OnHardCap, OnSoftCap


# ── Scan all tier examples ───────────────────────────────────────────


class TestTierExamplesNoSecrets:
    """All example tier configs must be free of secret-like patterns."""

    def test_no_sk_in_any_example(self, example_files):
        for path in example_files:
            content = path.read_text(encoding="utf-8")
            assert "sk-" not in content, f"Found 'sk-' in {path.name}"

    def test_no_apikey_literal_in_any_example(self, example_files):
        for path in example_files:
            content = path.read_text(encoding="utf-8")
            assert "apikey" not in content.lower(), f"Found 'apikey' in {path.name}"


# ── Secret injection triggers InvariantViolation ─────────────────────


class TestSecretDetection:
    def test_sk_prefix_in_model_ladder(self):
        gov = CostGovernor(
            currency="USD",
            daily_soft_cap=20.0,
            daily_hard_cap=25.0,
            on_soft_cap=OnSoftCap.DEGRADE_MODEL,
            on_hard_cap=OnHardCap.HALT_ALL,
            model_degrade_ladder=("sk-fake-key-12345",),
            allowlist_tasks_under_hard_cap=(),
        )
        with pytest.raises(InvariantViolation, match="sk-"):
            runtime_invariants(gov)

    def test_sk_prefix_in_allowlist(self):
        gov = CostGovernor(
            currency="USD",
            daily_soft_cap=20.0,
            daily_hard_cap=25.0,
            on_soft_cap=OnSoftCap.LOG_ONLY,
            on_hard_cap=OnHardCap.HALT_NONCRITICAL,
            model_degrade_ladder=(),
            allowlist_tasks_under_hard_cap=("sk-secret-task",),
        )
        with pytest.raises(InvariantViolation, match="sk-"):
            runtime_invariants(gov)

    def test_apikey_literal_in_ladder(self):
        gov = CostGovernor(
            currency="USD",
            daily_soft_cap=20.0,
            daily_hard_cap=25.0,
            on_soft_cap=OnSoftCap.DEGRADE_MODEL,
            on_hard_cap=OnHardCap.HALT_ALL,
            model_degrade_ladder=("apiKey-literal-value",),
            allowlist_tasks_under_hard_cap=(),
        )
        with pytest.raises(InvariantViolation, match="apiKey"):
            runtime_invariants(gov)

    def test_sk_prefix_in_dict(self):
        data = {
            "currency": "USD",
            "daily_soft_cap": 20.0,
            "daily_hard_cap": 25.0,
            "on_soft_cap": "degrade-model",
            "on_hard_cap": "halt-all",
            "model_degrade_ladder": ["sk-injected-key"],
            "allowlist_tasks_under_hard_cap": [],
        }
        with pytest.raises(InvariantViolation, match="sk-"):
            runtime_invariants_dict(data)

    def test_env_var_reference_passes(self):
        """Values wrapped in ${...} should NOT trigger the apiKey check."""
        gov = CostGovernor(
            currency="USD",
            daily_soft_cap=4.0,
            daily_hard_cap=5.0,
            on_soft_cap=OnSoftCap.LOG_ONLY,
            on_hard_cap=OnHardCap.HALT_ALL,
            model_degrade_ladder=(),
            allowlist_tasks_under_hard_cap=(),
            reset_timezone="${TZ_VAR}",
        )
        # Should not raise — env var reference is allowed
        runtime_invariants(gov)
