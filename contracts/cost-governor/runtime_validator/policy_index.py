import casbin
from pathlib import Path
import json

POLICY_DIR = Path(__file__).parent.parent / "policy"
MODEL_PATH = POLICY_DIR / "model.conf"
POLICY_PATH = POLICY_DIR / "policy.csv"

def load_enforcer():
    return casbin.Enforcer(str(MODEL_PATH), str(POLICY_PATH))

def check_cap(tier, obj, act, val):
    enforcer = load_enforcer()
    # Null/None means no cap, always allowed
    if val is None:
        return True
    return enforcer.enforce(tier, obj, act, val)

def validate_config(config, tier):
    """
    Validate a config dict for a given tier against policy.
    Expects keys: daily_soft_cap, daily_hard_cap, per_request_cap
    """
    errors = []
    if not check_cap(tier, "daily", "soft_cap", config.get("daily_soft_cap")):
        errors.append(f"daily_soft_cap {config.get('daily_soft_cap')} exceeds policy for {tier}")
    if not check_cap(tier, "daily", "hard_cap", config.get("daily_hard_cap")):
        errors.append(f"daily_hard_cap {config.get('daily_hard_cap')} exceeds policy for {tier}")
    if not check_cap(tier, "per_request", "cap", config.get("per_request_cap")):
        errors.append(f"per_request_cap {config.get('per_request_cap')} exceeds policy for {tier}")
    return errors

def validate_file(path, tier):
    with open(path) as f:
        config = json.load(f)
    return validate_config(config, tier)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: policy_index.py <config.json> <tier>")
        exit(1)
    errors = validate_file(sys.argv[1], sys.argv[2])
    if errors:
        print("\n".join(errors))
        exit(1)
    print("Policy check passed.")
