# This test expects PYTHONPATH to be set to the contract root for all imports:
#   PYTHONPATH=$PWD/contracts/cost-governor pytest -q contracts/cost-governor/tests/test_policy_as_code.py
import os
import glob
import json
import pytest
from runtime_validator.policy_index import validate_file

EXAMPLES = glob.glob(os.path.join(os.path.dirname(__file__), '../examples/*.json'))
PLATFORM_CONFIGS = glob.glob(os.path.join(os.path.dirname(__file__), '../../../platforms/*/cost-governor.json'))

# Map example file names to tiers (customize as needed)
EXAMPLE_TIERS = {
    'example-tier1.json': 'tier1',
    'example-tier2.json': 'tier2',
    'example-tier3.json': 'tier3',
}

@pytest.mark.parametrize("path", EXAMPLES + PLATFORM_CONFIGS)
def test_policy_compliance(path):
    # Infer tier from filename or directory
    import re
    fname = os.path.basename(path)
    tier = None
    # Try to match tierN in filename (tier1..tier5)
    m = re.search(r"tier([1-5])", fname)
    if m:
        tier = f"tier{m.group(1)}"
    else:
        # Try to match tierN in any part of the path
        parts = path.split(os.sep)
        for part in parts:
            m = re.match(r"tier([1-5])", part)
            if m:
                tier = f"tier{m.group(1)}"
                break
    if not tier:
        # Try to infer from JSON content (for platform configs)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "tier" in data:
                tier = data["tier"]
        except (OSError, json.JSONDecodeError, TypeError):
            # Best-effort tier inference from file contents; fallback to path rules below.
            pass
    assert tier, f"Could not infer tier for {path}"
    errors = validate_file(path, tier)
    assert not errors, f"Policy violations in {path}: {errors}"

def test_policy_caps_monotonic_across_tiers() -> None:
    """
    Prevent tier drift: for numeric resources, higher tiers must not have lower caps
    than lower tiers (non-decreasing across tier1..tier5).

    We intentionally EXCLUDE *_null_ok resources from monotonicity, because allowing
    null can be a policy exception rather than a numeric cap.
    """
    import csv
    from pathlib import Path

    policy_csv = Path(__file__).resolve().parents[1] / "policy" / "policy.csv"
    assert policy_csv.exists(), f"missing policy.csv at {policy_csv}"

    # resource -> {tier_int: limit_float}
    caps: dict[str, dict[int, float]] = {}

    with policy_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or row[0].strip().startswith("#"):
                continue
            # Expected: p, tierN, resource, limit, allow
            if len(row) < 5:
                continue
            tag, tier_s, resource, limit_s, eft = [c.strip() for c in row[:5]]
            if tag != "p" or eft != "allow":
                continue
            if resource.endswith("_null_ok"):
                continue
            if not tier_s.startswith("tier"):
                continue
            try:
                tier = int(tier_s.replace("tier", ""))
            except ValueError:
                continue
            try:
                limit = float(limit_s)
            except ValueError:
                # ignore non-numeric limits for monotonicity
                continue

            caps.setdefault(resource, {})[tier] = limit

    # For each resource, check monotonicity across present tiers
    for resource, by_tier in caps.items():
        last_tier = None
        last_limit = None
        for tier in sorted(by_tier.keys()):
            limit = by_tier[tier]
            if last_limit is not None and limit < last_limit:
                raise AssertionError(
                    f"policy not monotonic for {resource}: tier{tier}={limit} < "
                    f"tier{last_tier}={last_limit}"
                )
            last_tier, last_limit = tier, limit

def test_policy_tier_and_resource_naming_is_canonical() -> None:
    """
    Prevent naming drift:
      - tiers must be 'tier1'..'tier5' lowercase
      - resources must match the canonical set (plus *_null_ok)
    """
    import csv
    from pathlib import Path
    import re

    policy_csv = Path(__file__).resolve().parents[1] / "policy" / "policy.csv"
    assert policy_csv.exists(), f"missing policy.csv at {policy_csv}"

    tier_re = re.compile(r"^tier[1-5]$")
    resource_re = re.compile(r"^[a-z0-9_]+$")

    canonical_resources = {
        "usd_daily_soft_cap",
        "usd_daily_hard_cap",
        "usd_per_request_cap",
        "usd_daily_hard_cap_null_ok",
        "usd_per_request_cap_null_ok",
    }

    with policy_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or row[0].strip().startswith("#"):
                continue
            if len(row) < 5:
                continue
            tag, tier_s, resource, limit_s, eft = [c.strip() for c in row[:5]]
            if tag != "p" or eft != "allow":
                continue

            assert tier_re.match(tier_s), f"non-canonical tier '{tier_s}' in policy.csv"
            assert resource_re.match(resource), f"non-canonical resource '{resource}' in policy.csv"
            assert resource in canonical_resources, f"unknown resource '{resource}' in policy.csv"
