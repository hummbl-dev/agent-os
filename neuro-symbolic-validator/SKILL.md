---
name: neuro-symbolic-validator
description: Rule-Based Validator - validate and correct neural predictions using symbolic rules for runtime safety and domain constraint enforcement.
metadata:
  {
    "openclaw":
      {
        "emoji": "✅",
        "requires": { "python": [] },
        "install": [],
      },
  }
---

# neuro-symbolic-validator

Rule-Based Validator wraps machine learning models with symbolic rules to validate predictions, enforce domain constraints, and auto-correct violations at runtime.

## Core Concept

### The Safety Layer

```
Input → Neural Model → Prediction → Validator → Validated Output
                                              ↓
                                         (Auto-correct if invalid)
```

**Neural Network**: Fast, pattern-based predictions  
**Rule Validator**: Ensures predictions respect business logic, safety constraints, and domain rules

## Quick Start

### Basic Usage

```python
from neuro_symbolic import RuleBasedValidator, ValidationRule, ValidationResult

# Create validator
validator = RuleBasedValidator("my_validator")

# Add rules
validator.add_rule(ValidationRule(
    name="positive_value",
    condition=lambda inp, pred: pred > 0,
    message="Value must be positive",
    severity=ValidationResult.INVALID,
    auto_correct=lambda p: abs(p)  # Fix negative values
))

# Validate prediction
result = validator.validate(input_data, prediction)

if result["valid"]:
    print("✓ Prediction is valid")
else:
    print(f"✗ Issues: {result['violations']}")
    print(f"Suggested: {result['suggested_prediction']}")
```

### Running the Demo

```bash
cd /Users/others/founder_mode
source .venv-neurosym/bin/activate
python neuro_symbolic/rule_validator.py
```

## API Reference

### ValidationRule

```python
from dataclasses import dataclass
from typing import Callable, Optional

@dataclass
class ValidationRule:
    name: str                           # Rule identifier
    condition: Callable                 # Function(input, prediction) -> bool
    message: str                        # Error message if violated
    severity: ValidationResult          # WARNING or INVALID
    auto_correct: Optional[Callable]    # Function to fix violations
```

### RuleBasedValidator

```python
validator = RuleBasedValidator(name="validator")

# Add rules
validator.add_rule(rule)

# Validate single prediction
result = validator.validate(input_data, prediction, context={})

# Validate batch
results = validator.validate_batch(inputs, predictions, contexts)

# Get statistics
stats = validator.get_validation_stats()
# Returns: {total, valid, invalid, warning, validity_rate, correction_rate}
```

### ValidatedModel Wrapper

```python
from neuro_symbolic import ValidatedModel

# Wrap any ML model
validated_model = ValidatedModel(
    model=my_neural_network,
    validator=validator,
    auto_correct=True  # Automatically apply corrections
)

# Predictions are automatically validated
result = validated_model.predict(input_data)

# Returns:
{
    "prediction": final_prediction,          # Possibly corrected
    "raw_prediction": original_prediction,
    "validation": validation_report,
    "is_validated": True/False,
    "was_corrected": True/False
}
```

## Pre-built Validators

### 1. Generic Validator

```python
from neuro_symbolic import create_generic_validator

validator = create_generic_validator(
    min_value=0,
    max_value=100,
    allowed_values={"low", "medium", "high"}
)
```

### 2. Software Domain Validator

```python
from neuro_symbolic import create_software_validator

validator = create_software_validator()

# Enforces:
# - Valid priorities: low, medium, high, critical
# - Positive estimates
# - Capacity checks
```

### 3. Healthcare Validator

```python
from neuro_symbolic import create_healthcare_validator

validator = create_healthcare_validator()

# Enforces:
# - Minimum confidence thresholds
# - Age-diagnosis consistency
# - Valid vital sign ranges
```

### 4. Finance Validator

```python
from neuro_symbolic import create_finance_validator

validator = create_finance_validator()

# Enforces:
# - Positive transaction amounts
# - Risk scores in [0, 1]
# - Regulatory limits
```

## Use Cases

### 1. ML Model Safety Guardrails

```python
# Wrap a high-stakes model
class RiskModel:
    def predict(self, transaction):
        # Neural prediction
        return {"risk_score": 0.85, "flag": True}

validator = create_finance_validator()
validated_model = ValidatedModel(RiskModel(), validator)

# Invalid prediction gets corrected
result = validated_model.predict({"amount": -500})
# Raw: -500 (invalid)
# Corrected: 500 (valid)
```

### 2. API Response Validation

```python
def validate_api_response(response):
    validator = RuleBasedValidator("api")
    
    validator.add_rule(ValidationRule(
        name="required_fields",
        condition=lambda inp, pred: all(k in pred for k in ["id", "status"]),
        message="Missing required fields",
        severity=ValidationResult.INVALID
    ))
    
    result = validator.validate({}, response)
    return result["valid"]
```

### 3. Configuration Validation

```python
validator = RuleBasedValidator("config")

# Ensure config values are reasonable
validator.add_rule(ValidationRule(
    name="timeout_reasonable",
    condition=lambda inp, pred: 0 < pred.get("timeout", 30) < 300,
    message="Timeout should be between 1-300 seconds",
    severity=ValidationResult.WARNING,
    auto_correct=lambda p: {**p, "timeout": max(1, min(300, p.get("timeout", 30)))}
))

config = {"timeout": 500}  # Too high
result = validator.validate({}, config)
# Corrected to: {"timeout": 300}
```

## Advanced Patterns

### Conditional Rules

```python
def urgent_needs_actions(inp, pred):
    """High priority items must have action items."""
    if pred.get("priority") in {"high", "critical"}:
        return len(pred.get("action_items", [])) > 0
    return True

validator.add_rule(ValidationRule(
    name="urgent_requires_actions",
    condition=urgent_needs_actions,
    message="High priority items must have action items",
    severity=ValidationResult.WARNING
))
```

### Context-Aware Validation

```python
def validate_with_context(input_data, prediction):
    context = {
        "user_tier": input_data.get("tier", "free"),
        "time_of_day": datetime.now().hour
    }
    
    # Different rules for different user tiers
    if context["user_tier"] == "free":
        # Stricter limits for free users
        return prediction["cost"] <= 10
    else:
        return prediction["cost"] <= 100

validator.add_rule(ValidationRule(
    name="tier_based_limits",
    condition=validate_with_context,
    message="Cost exceeds tier limit"
))
```

### Multi-Stage Validation

```python
# Stage 1: Syntax validation
syntax_validator = RuleBasedValidator("syntax")
syntax_validator.add_rule(...)

# Stage 2: Semantic validation
semantic_validator = RuleBasedValidator("semantic")
semantic_validator.add_rule(...)

# Stage 3: Business rule validation
business_validator = RuleBasedValidator("business")
business_validator.add_rule(...)

def full_validation(input_data, prediction):
    for validator in [syntax_validator, semantic_validator, business_validator]:
        result = validator.validate(input_data, prediction)
        if not result["valid"]:
            return result
    return {"valid": True}
```

## ValidationResult Types

```python
from neuro_symbolic import ValidationResult

ValidationResult.VALID    # Passed all rules
ValidationResult.WARNING  # Minor issues, proceed with caution
ValidationResult.INVALID  # Critical issues, must fix
```

## Integration with founder_mode

### BriefingQualityValidator

```python
from neuro_symbolic.founder_mode_integration import BriefingQualityValidator

validator = BriefingQualityValidator()

briefing = {
    "sections": ["github", "calendar", "linear"],
    "priority": "high",
    "estimated_cost": 2.50,
    "action_items": ["Review PRs"]
}

result = validator.validate({}, briefing)

if result["valid"]:
    send_to_user(briefing)
else:
    # Fix issues before sending
    for violation in result["violations"]:
        log_issue(violation["message"])
```

### CostAwareValidator

```python
from neuro_symbolic.founder_mode_integration import CostAwareValidator

validator = CostAwareValidator(daily_budget=50.0)

# Check before expensive operation
operation = {"type": "analysis", "cost": 15.0, "justification": "Weekly report"}
result = validator.validate({}, operation)

if result["valid"]:
    validator.record_cost(operation["cost"])
    run_analysis()
else:
    print("Operation rejected:", result["violations"][0]["message"])
    # Budget exceeded or missing justification

# Check budget status
status = validator.get_budget_status()
print(f"Remaining: ${status['remaining']:.2f}")
```

## Validation Report Structure

```python
result = validator.validate(input_data, prediction)

{
    "status": "valid" | "warning" | "invalid",
    "valid": True | False,
    "violations": [
        {
            "rule": "rule_name",
            "message": "Human-readable error",
            "severity": "warning" | "invalid",
            "prediction": {...}  # The prediction that failed
        }
    ],
    "corrections": [
        {
            "rule": "rule_name",
            "original": {...},
            "corrected": {...}
        }
    ],
    "original_prediction": {...},
    "suggested_prediction": {...}  # With corrections applied
}
```

## Best Practices

### 1. Rule Ordering

```python
# Order rules by severity: INVALID first, then WARNING
validator.add_rule(ValidationRule(..., severity=ValidationResult.INVALID))
validator.add_rule(ValidationRule(..., severity=ValidationResult.INVALID))
validator.add_rule(ValidationRule(..., severity=ValidationResult.WARNING))
```

### 2. Auto-Correction Guidelines

```python
# Good: Safe, conservative corrections
auto_correct=lambda p: max(0, p)  # Clamp to positive

# Bad: Aggressive corrections that change meaning
auto_correct=lambda p: 0  # Always returns 0 (too aggressive)
```

### 3. Error Messages

```python
# Good: Clear, actionable
message="Risk score must be between 0 and 1. Current: {value}"

# Bad: Vague
message="Invalid value"
```

### 4. Testing Rules

```python
def test_validation_rules():
    validator = create_software_validator()
    
    # Test valid case
    valid = {"priority": "high", "estimated_hours": 5}
    assert validator.validate({}, valid)["valid"]
    
    # Test invalid case
    invalid = {"priority": "unknown", "estimated_hours": 5}
    assert not validator.validate({}, invalid)["valid"]
    
    # Test auto-correction
    corrected = {"priority": "unknown"}
    result = validator.validate({}, corrected)
    assert result["was_corrected"]
    assert result["prediction"]["priority"] == "medium"
```

## Troubleshooting

### Rules Not Firing

```python
# Check rule condition function signature
def wrong_condition(pred):  # Missing input parameter
    return pred > 0

def correct_condition(inp, pred):  # Correct signature
    return pred > 0
```

### Performance Issues

```python
# Batch validation is faster
results = validator.validate_batch(inputs, predictions)

# Not:
for inp, pred in zip(inputs, predictions):
    result = validator.validate(inp, pred)  # Slow
```

### False Positives

```python
# Make conditions specific
def too_broad(inp, pred):  # Catches too much
    return isinstance(pred, dict)

def specific(inp, pred):  # Checks actual constraint
    return 0 <= pred.get("score", 0) <= 1
```

## See Also

- `neuro-symbolic-overview` - General introduction
- `neuro-symbolic-ltn` - Logic Tensor Networks
- `neuro-symbolic-knowledge-graph` - Knowledge graph reasoning
- `neuro-symbolic-founder` - founder_mode specific
