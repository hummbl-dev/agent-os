---
name: neuro-symbolic-founder
description: founder_mode Integration - ready-to-use neuro-symbolic components for the Morning Briefing stack including briefing validation, service tracking, and cost control.
metadata:
  {
    "openclaw":
      {
        "emoji": "🚀",
        "requires": { "python": ["torch", "ltntorch", "rdflib", "networkx", "numpy"] },
        "install": ["pip install torch ltntorch rdflib networkx numpy"],
      },
  }
---

# neuro-symbolic-founder

Pre-built neuro-symbolic components specifically designed for the founder_mode Morning Briefing stack. These components integrate seamlessly with briefing services, adapters, and cost tracking.

## Components Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    founder_mode Stack                       │
├─────────────────────────────────────────────────────────────┤
│ BriefingQualityValidator  → Validate AI-generated briefings │
│ ServiceDependencyTracker  → Analyze service impact          │
│ CostAwareValidator        → Enforce budget constraints      │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

```python
from neuro_symbolic.founder_mode_integration import (
    BriefingQualityValidator,
    ServiceDependencyTracker,
    CostAwareValidator
)

# All components are pre-configured for founder_mode
validator = BriefingQualityValidator()
tracker = ServiceDependencyTracker()
cost_validator = CostAwareValidator(daily_budget=50.0)
```

### Run the Demo

```bash
cd /Users/others/founder_mode
source .venv-neurosym/bin/activate
python neuro_symbolic/founder_mode_integration.py
```

## 1. BriefingQualityValidator

Validates AI-generated briefings before sending to users.

### Validation Rules

| Rule | Check | Severity |
|------|-------|----------|
| minimum_sections | At least 2 sections | INVALID |
| valid_priority | Priority in {low, medium, high, critical} | INVALID |
| reasonable_cost | Cost ≤ $100 | WARNING |
| urgent_needs_actions | High priority → has action items | WARNING |

### Usage

```python
from neuro_symbolic.founder_mode_integration import BriefingQualityValidator

validator = BriefingQualityValidator()

briefing = {
    "sections": ["github_activity", "calendar_events", "cost_summary"],
    "priority": "high",
    "estimated_cost": 3.50,
    "action_items": ["Review PR #123", "Prepare for standup"]
}

result = validator.validate({}, briefing)

if result["valid"]:
    print("✓ Briefing quality checks passed")
    send_to_user(briefing)
else:
    print("✗ Quality issues found:")
    for violation in result["violations"]:
        print(f"  - {violation['message']}")
```

### Integration with BriefingService

```python
class ValidatedBriefingService:
    def __init__(self):
        self.generator = BriefingGenerator()
        self.validator = BriefingQualityValidator()
    
    def generate_and_validate(self, user_context):
        # Generate briefing
        briefing = self.generator.generate(user_context)
        
        # Validate
        result = self.validator.validate(user_context, briefing)
        
        if result["valid"]:
            return briefing
        elif result["was_corrected"]:
            # Use corrected version if available
            return result["suggested_prediction"]
        else:
            # Cannot auto-correct, raise for review
            raise QualityError(result["violations"])
```

## 2. ServiceDependencyTracker

Analyzes service dependencies and suggests resilience strategies.

### Pre-configured Services

The tracker comes with founder_mode services pre-loaded:

```python
services = {
    "briefing_service": {"type": "core", "criticality": "high"},
    "github_adapter": {"type": "integration", "criticality": "medium"},
    "linear_adapter": {"type": "integration", "criticality": "medium"},
    "calendar_adapter": {"type": "integration", "criticality": "medium"},
    "cost_tracker": {"type": "utility", "criticality": "low"},
    "resilient_briefing": {"type": "wrapper", "criticality": "high"},
    "scheduler": {"type": "core", "criticality": "high"},
}

dependencies = [
    ("briefing_service", "depends_on", "github_adapter"),
    ("briefing_service", "depends_on", "linear_adapter"),
    ("briefing_service", "depends_on", "calendar_adapter"),
    ("briefing_service", "uses", "cost_tracker"),
    ("resilient_briefing", "wraps", "briefing_service"),
    ("scheduler", "triggers", "briefing_service"),
]
```

### Usage

```python
from neuro_symbolic.founder_mode_integration import ServiceDependencyTracker

tracker = ServiceDependencyTracker()

# Analyze impact of service failure
impact = tracker.get_service_impact("github_adapter")

print(f"Service: github_adapter")
print(f"Risk Level: {impact['risk_level']}")  # low, medium, high
print(f"Services Affected: {impact['total_reachable']}")
print(f"Critical Impact: {impact['critical_services_affected']}")
print(f"Similar Services: {[s['service'] for s in impact['functionally_similar']]}")

# Get resilience strategies
strategies = tracker.suggest_resilience_strategy("briefing_service")
for strategy in strategies:
    print(f"• {strategy}")
```

### Output Example

```
Service: briefing_service
Risk Level: HIGH
Services Affected: 6
Critical Services Impacted: ['briefing_service']
Functionally Similar: ['resilient_briefing', 'scheduler', 'linear_adapter']

Suggested Strategies:
  • Implement circuit breaker pattern
  • Add redundant fallback service
  • Consider service mesh for dependency management
```

### Integration with ResilientBriefingService

```python
class ResilientBriefingService:
    def __init__(self):
        self.tracker = ServiceDependencyTracker()
        self.adapters = {
            "github": GitHubAdapter(),
            "linear": LinearAdapter(),
            "calendar": CalendarAdapter()
        }
    
    def health_check(self):
        """Check if critical dependencies are healthy."""
        impact = self.tracker.get_service_impact("briefing_service")
        
        if impact["risk_level"] == "high":
            # Check each critical dependency
            for svc in impact["critical_services_affected"]:
                if not self.check_service_health(svc):
                    self.apply_resilience_strategy(svc)
    
    def apply_resilience_strategy(self, service):
        """Apply suggested resilience strategies."""
        strategies = self.tracker.suggest_resilience_strategy(service)
        
        if "circuit breaker" in str(strategies).lower():
            self.enable_circuit_breaker(service)
        
        if "fallback" in str(strategies).lower():
            self.enable_fallback(service)
```

## 3. CostAwareValidator

Enforces budget constraints on AI operations.

### Validation Rules

| Rule | Check | Severity |
|------|-------|----------|
| single_operation_cost | Cost ≤ $10 | WARNING |
| daily_budget | Daily total ≤ budget | INVALID |
| high_cost_justified | Cost > $5 requires justification | WARNING |

### Usage

```python
from neuro_symbolic.founder_mode_integration import CostAwareValidator

validator = CostAwareValidator(daily_budget=50.0)

# Simulate AI operation cost estimation
operation = {
    "operation": "generate_briefing",
    "cost": 2.50,
    "justification": "Daily morning briefing"
}

result = validator.validate({}, operation)

if result["valid"]:
    validator.record_cost(operation["cost"])
    run_operation(operation)
    
    # Check remaining budget
    status = validator.get_budget_status()
    print(f"Budget remaining: ${status['remaining']:.2f}")
else:
    print(f"Operation rejected: {result['violations'][0]['message']}")
```

### Integration with CostTracker

```python
class CostControlledBriefingGenerator:
    def __init__(self, daily_budget=50.0):
        self.validator = CostAwareValidator(daily_budget)
        self.cost_tracker = CostTracker()
    
    def generate_with_budget_check(self, user_id):
        # Estimate cost before running
        estimated_cost = self.estimate_generation_cost(user_id)
        
        operation = {
            "operation": "briefing_generation",
            "cost": estimated_cost,
            "justification": f"Daily briefing for {user_id}"
        }
        
        result = self.validator.validate({}, operation)
        
        if not result["valid"]:
            if "daily_budget" in result["violations"][0]["message"]:
                # Budget exhausted, use cheaper fallback
                return self.generate_fallback_briefing(user_id)
            else:
                raise BudgetError(result["violations"])
        
        # Run operation
        briefing = self.generate_briefing(user_id)
        
        # Record actual cost
        actual_cost = self.cost_tracker.get_last_operation_cost()
        self.validator.record_cost(actual_cost)
        
        return briefing
    
    def get_budget_report(self):
        """Get current budget status."""
        return self.validator.get_budget_status()
```

## Complete Integration Example

```python
from neuro_symbolic.founder_mode_integration import (
    BriefingQualityValidator,
    ServiceDependencyTracker,
    CostAwareValidator
)

class NeuroSymbolicBriefingPipeline:
    """
    Complete pipeline using all neuro-symbolic components.
    """
    
    def __init__(self):
        self.quality_validator = BriefingQualityValidator()
        self.dependency_tracker = ServiceDependencyTracker()
        self.cost_validator = CostAwareValidator(daily_budget=50.0)
    
    def run_pipeline(self, user_context):
        """
        Run the full pipeline with neuro-symbolic validation.
        """
        print("=" * 60)
        print("Neuro-Symbolic Briefing Pipeline")
        print("=" * 60)
        
        # Step 1: Check service dependencies
        print("\n1. Checking service dependencies...")
        impact = self.dependency_tracker.get_service_impact("briefing_service")
        
        if impact["risk_level"] == "high":
            print(f"   ⚠️  High risk: {impact['critical_services_affected']} affected")
            strategies = self.dependency_tracker.suggest_resilience_strategy("briefing_service")
            print(f"   Suggested: {strategies[0]}")
        else:
            print(f"   ✓ Risk level: {impact['risk_level']}")
        
        # Step 2: Validate cost
        print("\n2. Validating budget...")
        operation = {
            "operation": "briefing_generation",
            "cost": 3.50,
            "justification": "Daily briefing"
        }
        
        cost_result = self.cost_validator.validate({}, operation)
        if cost_result["valid"]:
            print("   ✓ Budget check passed")
            self.cost_validator.record_cost(operation["cost"])
        else:
            print(f"   ✗ Budget check failed: {cost_result['violations'][0]['message']}")
            return None
        
        # Step 3: Generate briefing (simulated)
        print("\n3. Generating briefing...")
        briefing = self.generate_briefing(user_context)
        
        # Step 4: Validate quality
        print("\n4. Validating quality...")
        quality_result = self.quality_validator.validate(user_context, briefing)
        
        if quality_result["valid"]:
            print("   ✓ Quality check passed")
            print("\n" + "=" * 60)
            print("✓ Briefing ready for delivery")
            print("=" * 60)
            return briefing
        else:
            print(f"   ✗ Quality issues:")
            for v in quality_result["violations"]:
                print(f"      - {v['message']}")
            
            if quality_result["was_corrected"]:
                print("\n   ✓ Auto-corrected, using fixed version")
                return quality_result["suggested_prediction"]
            else:
                return None
    
    def generate_briefing(self, context):
        """Simulate briefing generation."""
        return {
            "sections": ["github", "calendar", "costs"],
            "priority": "medium",
            "estimated_cost": 3.50,
            "action_items": ["Review PRs"]
        }

# Usage
pipeline = NeuroSymbolicBriefingPipeline()
briefing = pipeline.run_pipeline({"user": "founder"})
```

## Testing

```bash
# Run all tests
cd /Users/others/founder_mode
source .venv-neurosym/bin/activate
python neuro_symbolic/test_neuro_symbolic.py

# Test specific components
python -c "
from neuro_symbolic.founder_mode_integration import (
    BriefingQualityValidator,
    ServiceDependencyTracker,
    CostAwareValidator
)

# Test validator
v = BriefingQualityValidator()
result = v.validate({}, {'sections': ['s1', 's2'], 'priority': 'high', 'action_items': ['a1']})
assert result['valid'], 'Validator test failed'

# Test tracker
t = ServiceDependencyTracker()
impact = t.get_service_impact('briefing_service')
assert 'risk_level' in impact, 'Tracker test failed'

# Test cost validator
c = CostAwareValidator(daily_budget=10)
result = c.validate({}, {'cost': 5, 'justification': 'test'})
assert result['valid'], 'Cost validator test failed'

print('✓ All founder_mode integration tests passed')
"
```

## Configuration

### Environment Variables

```bash
# Budget settings
export BRIEFING_DAILY_BUDGET=50.0
export BRIEFING_MAX_OPERATION_COST=10.0

# Quality settings
export BRIEFING_MIN_SECTIONS=2
export BRIEFING_MAX_COST=100.0
```

### Custom Rules

```python
# Extend with custom rules
from neuro_symbolic import ValidationRule, ValidationResult

validator = BriefingQualityValidator()

# Add custom rule
validator.add_rule(ValidationRule(
    name="custom_check",
    condition=lambda inp, pred: pred.get("custom_field") is not None,
    message="Custom field required",
    severity=ValidationResult.WARNING
))
```

## See Also

- `neuro-symbolic-overview` - General introduction
- `neuro-symbolic-ltn` - Logic Tensor Networks
- `neuro-symbolic-knowledge-graph` - Knowledge graph reasoning
- `neuro-symbolic-validator` - Rule-based validation
