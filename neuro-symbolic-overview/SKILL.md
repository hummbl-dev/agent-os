---
name: neuro-symbolic-overview
description: Overview and getting started guide for neuro-symbolic AI - combining neural networks with symbolic reasoning for explainable AI systems.
metadata:
  {
    "openclaw":
      {
        "emoji": "🧠",
        "requires": { "python": ["torch", "ltntorch", "rdflib", "networkx", "numpy"] },
        "install": ["pip install torch ltntorch rdflib networkx numpy"],
      },
  }
---

# neuro-symbolic-overview

Neuro-symbolic AI combines neural networks (pattern recognition, learning from data) with symbolic AI (logic, rules, knowledge graphs) to create explainable, robust AI systems.

## What is Neuro-Symbolic AI?

### The Two Paradigms

| Neural (System 1) | Symbolic (System 2) | Neuro-Symbolic |
|-------------------|---------------------|----------------|
| Pattern recognition | Logical reasoning | Both capabilities |
| Learning from data | Rule-based inference | Learning + reasoning |
| Black box decisions | Explainable steps | Interpretable learning |
| Needs lots of data | Data efficient | Efficient + scalable |
| Handles noise | Brittle | Robust + reliable |

### Key Benefits

1. **Explainability**: Decisions come with logical justifications
2. **Data Efficiency**: Works with less training data
3. **Safety**: Domain constraints are guaranteed to be satisfied
4. **Trust**: Auditable reasoning chains
5. **Robustness**: Combines pattern recognition with logical constraints

## Three Main Approaches

### 1. Logic Tensor Networks (LTN)

Train neural networks with logical constraints using fuzzy logic.

```python
# Neural loss + Logical constraint loss
total_loss = neural_loss + λ * logical_constraint_loss
```

**Use when:**
- You have domain knowledge to inject
- Need guaranteed logical consistency
- Training data is limited

### 2. Knowledge Graph Reasoning

Combine neural embeddings with symbolic graph traversal.

```python
# Neural: Similarity between entities
similarity = cosine_similarity(entity_a_embedding, entity_b_embedding)

# Symbolic: Traverse relationships
reachable = graph.bfs(start_entity, relation="depends_on")
```

**Use when:**
- You have structured relationships
- Need explainable entity connections
- Combining multiple data sources

### 3. Rule-Based Validation

Validate and correct neural predictions using symbolic rules.

```python
# Post-processing validation
if not rule_checker.validate(prediction):
    prediction = auto_correct(prediction)
```

**Use when:**
- Runtime safety is critical
- Need to enforce business rules
- Catching model errors before deployment

## Quick Start

### Installation

```bash
cd /Users/others/founder_mode
source .venv-neurosym/bin/activate

# Already installed in founder_mode
echo "Neuro-symbolic module ready"
```

### Run Demos

```bash
# All demos
python neuro_symbolic/demo.py

# Individual approaches
python neuro_symbolic/ltn_example.py
python neuro_symbolic/knowledge_graph_reasoner.py
python neuro_symbolic/rule_validator.py
```

### Basic Usage

```python
# Import the module
from neuro_symbolic import (
    KnowledgeGraphReasoner,
    RuleBasedValidator,
    ValidationRule
)

# Knowledge Graph
kg = KnowledgeGraphReasoner()
kg.add_entity("service_a", "Service")
kg.add_relation("service_a", "depends_on", "service_b")
result = kg.neuro_symbolic_query("service_a")

# Rule Validator
validator = RuleBasedValidator()
validator.add_rule(ValidationRule(
    name="max_cost",
    condition=lambda inp, pred: pred["cost"] <= 100,
    message="Cost exceeds budget"
))
result = validator.validate(input_data, prediction)
```

## Architecture Patterns

### Pattern 1: Neural → Symbolic (Pipeline)

```
Input → Neural Network → Symbolic Validator → Output
```

**Best for:** Runtime validation, safety constraints

### Pattern 2: Symbolic → Neural (Guided)

```
Knowledge Base → Constrained Training → Neural Model
```

**Best for:** Training with domain knowledge

### Pattern 3: Bidirectional Integration

```
         ┌─────────────┐
Input →  │   Neural    │ → Embeddings
         └──────┬──────┘
                ↓
         ┌─────────────┐
         │  Symbolic   │ → Reasoning
         └──────┬──────┘
                ↓
              Output
```

**Best for:** Full integration, complex reasoning

## founder_mode Integration

### Components Available

```python
from neuro_symbolic.founder_mode_integration import (
    BriefingQualityValidator,    # Validate AI briefings
    ServiceDependencyTracker,     # Analyze service impact
    CostAwareValidator,           # Enforce budgets
)
```

### Example: Briefing Validation

```python
validator = BriefingQualityValidator()

briefing = {
    "sections": ["github", "calendar", "costs"],
    "priority": "high",
    "action_items": ["Review PRs"]
}

result = validator.validate({}, briefing)
if result["valid"]:
    send_briefing(briefing)
else:
    print("Quality issues:", result["violations"])
```

### Example: Service Impact Analysis

```python
tracker = ServiceDependencyTracker()
impact = tracker.get_service_impact("briefing_service")

print(f"Risk: {impact['risk_level']}")
print(f"Services affected: {impact['total_reachable']}")

for strategy in tracker.suggest_resilience_strategy("briefing_service"):
    print(f"Strategy: {strategy}")
```

## When to Use Neuro-Symbolic AI

### Good Candidates

✅ Need explainable decisions  
✅ Have domain expertise/rules  
✅ Limited training data  
✅ Safety-critical applications  
✅ Complex relational reasoning  
✅ Need audit trails  

### Skip For

❌ Pure pattern recognition (images, audio)  
❌ Massive unstructured datasets  
❌ Real-time requirements (<10ms latency)  
❌ No domain knowledge available  

## Performance Characteristics

| Aspect | Pure Neural | Neuro-Symbolic | Symbolic |
|--------|-------------|----------------|----------|
| Training time | Fast | Slower (constraints) | N/A |
| Inference time | Fast | Fast-Medium | Medium |
| Data needed | Lots (10k+) | Moderate (1k+) | None |
| Explainability | Low | High | Very High |
| Flexibility | High | Medium | Low |
| Safety | Low | High | Very High |

## Related Skills

- `neuro-symbolic-ltn` - Logic Tensor Networks deep dive
- `neuro-symbolic-knowledge-graph` - Knowledge graph reasoning
- `neuro-symbolic-validator` - Rule-based validation
- `neuro-symbolic-founder` - founder_mode specific integrations

## Resources

- **Paper**: "Logic Tensor Networks" (Badreddine et al., 2022)
- **Survey**: "Neuro-Symbolic AI: The 3rd Wave" (Garcez & Lamb)
- **Code**: `/Users/others/founder_mode/neuro_symbolic/`
- **Tests**: `python neuro_symbolic/test_neuro_symbolic.py`

## Troubleshooting

### Import Errors

```bash
# Ensure virtual environment
source /Users/others/founder_mode/.venv-neurosym/bin/activate

# Verify installation
python -c "from neuro_symbolic import KnowledgeGraphReasoner; print('OK')"
```

### Performance Issues

```python
# Use caching for embeddings
embedding_cache = {}

# Batch validation
results = validator.validate_batch(inputs, predictions)

# Limit graph depth
tracker.kg.symbolic_reasoning(entity, depth=2)  # Not 10
```

### Debugging Rules

```python
# Enable verbose mode
validator = RuleBasedValidator("debug")
result = validator.validate(input, prediction)
print(result["violations"])  # See all failures
```
