---
name: neuro-symbolic-knowledge-graph
description: Knowledge Graph Reasoner - combine neural embeddings with symbolic graph traversal for explainable entity relationships and inference.
metadata:
  {
    "openclaw":
      {
        "emoji": "🕸️",
        "requires": { "python": ["rdflib", "networkx", "numpy"] },
        "install": ["pip install rdflib networkx numpy"],
      },
  }
---

# neuro-symbolic-knowledge-graph

Knowledge Graph Reasoner combines neural embeddings (for semantic similarity) with symbolic reasoning (for logical inference) to provide explainable entity relationships and multi-hop reasoning.

## Core Concept

### The Hybrid Approach

**Neural Component**: Entity embeddings capture semantic similarity  
**Symbolic Component**: Graph traversal follows explicit relationships  
**Combined**: Similar entities + logical paths = powerful reasoning

```
Neural:    briefing_service ≈ resilient_briefing (similar function)
            ↓
Symbolic:  briefing_service → depends_on → github_adapter
            ↓
Combined:  resilient_briefing likely also depends on github_adapter
```

## Quick Start

### Basic Usage

```python
from neuro_symbolic import KnowledgeGraphReasoner
import numpy as np

kg = KnowledgeGraphReasoner()

# Add entities
kg.add_entity("briefing_service", "Service", {"status": "active"})
kg.add_entity("github_adapter", "Adapter", {"type": "integration"})

# Add relations
kg.add_relation("briefing_service", "depends_on", "github_adapter")

# Add neural embeddings
kg.add_embedding("briefing_service", np.random.randn(10))
kg.add_embedding("github_adapter", np.random.randn(10))

# Combined query
result = kg.neuro_symbolic_query("briefing_service")
```

### Running the Demo

```bash
cd /Users/others/founder_mode
source .venv-neurosym/bin/activate
python neuro_symbolic/knowledge_graph_reasoner.py
```

## API Reference

### Entity Management

```python
# Add entity with properties
kg.add_entity(
    entity_id="service_a",
    entity_type="Service",
    properties={"status": "active", "version": "1.0"}
)

# Add relation
kg.add_relation("service_a", "depends_on", "service_b")
kg.add_relation("service_a", "uses", "database_c")

# Add embedding for neural similarity
kg.add_embedding("service_a", embedding_vector)
```

### Symbolic Reasoning

```python
# Traverse relationships
result = kg.symbolic_reasoning("service_a", depth=2)

# Returns:
{
    "query_entity": "service_a",
    "paths": [
        [("depends_on", "service_b")],
        [("uses", "database_c")],
        [("depends_on", "service_b"), ("uses", "cache_d")]
    ],
    "conclusions": [...],
    "reachable_entities": ["service_a", "service_b", "database_c", ...]
}
```

### Neural Similarity

```python
# Find similar entities
similar = kg.find_similar_entities("service_a", top_k=5)
# Returns: [("service_b", 0.92), ("service_c", 0.85), ...]

# Compute pairwise similarity
score = kg.compute_similarity("service_a", "service_b")
# Returns: 0.92
```

### Combined Neuro-Symbolic Query

```python
result = kg.neuro_symbolic_query("service_a")

# Returns comprehensive analysis:
{
    "entity": "service_a",
    "symbolic_reasoning": {...},
    "neural_similarity": [...],
    "combined_insights": [
        {
            "entity": "service_b",
            "similarity": 0.92,
            "shared_context": [...]
        }
    ]
}
```

## Use Cases

### 1. Service Dependency Analysis

```python
tracker = KnowledgeGraphReasoner()

# Model your architecture
tracker.add_entity("api_gateway", "Service")
tracker.add_entity("auth_service", "Service")
tracker.add_entity("user_db", "Database")

tracker.add_relation("api_gateway", "depends_on", "auth_service")
tracker.add_relation("auth_service", "uses", "user_db")

# Analyze impact of failure
impact = tracker.symbolic_reasoning("auth_service", depth=2)
print(f"Services affected: {len(impact['reachable_entities'])}")
```

### 2. Recommendation System

```python
# Find similar products with reasoning
kg.add_entity("product_a", "Product", {"category": "electronics"})
kg.add_entity("product_b", "Product", {"category": "electronics"})
kg.add_relation("product_a", "similar_to", "product_b")

# Neural finds similar embeddings
# Symbolic validates category compatibility
result = kg.neuro_symbolic_query("product_a")
```

### 3. Root Cause Analysis

```python
# Trace error propagation
kg.symbolic_reasoning("failed_service", depth=5)

# Find all paths from error source
paths = result["paths"]
for path in paths:
    print(" → ".join([f"{rel}:{target}" for rel, target in path]))
```

## SPARQL Queries

### Direct Graph Queries

```python
# Find all services that depend on a database
query = """
    SELECT ?service WHERE {
        ?service <http://foundermode.ai/neurosym#depends_on> <http://foundermode.ai/neurosym#postgres_db>
    }
"""
results = kg.query(query)

# Find all entities of type Service
query = """
    SELECT ?entity WHERE {
        ?entity <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://foundermode.ai/neurosym#Service>
    }
"""
results = kg.query(query)
```

## Advanced Features

### Custom Inference Rules

```python
def transitive_closure(kg, entity, relation, depth=3):
    """Custom transitive reasoning."""
    result = kg.symbolic_reasoning(entity, depth=depth)
    
    # Apply custom rule: if A depends on B and B depends on C,
    # then A indirectly depends on C
    indirect_deps = []
    for path in result["paths"]:
        if len(path) > 1:
            indirect_deps.append(path[-1])
    
    return indirect_deps
```

### Embedding Generation

```python
from sklearn.preprocessing import StandardScaler

def generate_structured_embeddings(kg, entities):
    """Generate embeddings based on graph structure."""
    import networkx as nx
    
    # Convert to NetworkX
    G = nx.DiGraph()
    for s, p, o in kg.graph:
        s_name = str(s).split("#")[-1]
        o_name = str(o).split("#")[-1]
        G.add_edge(s_name, o_name)
    
    # Use node2vec or similar
    embeddings = {}
    for entity in entities:
        if entity in G:
            # Use node degree, centrality as features
            emb = [
                G.degree(entity),
                nx.degree_centrality(G).get(entity, 0),
                nx.closeness_centrality(G).get(entity, 0),
            ]
            embeddings[entity] = np.array(emb)
    
    return embeddings
```

## Integration with founder_mode

### ServiceDependencyTracker

```python
from neuro_symbolic.founder_mode_integration import ServiceDependencyTracker

tracker = ServiceDependencyTracker()

# Pre-loaded with founder_mode services:
# - briefing_service
# - github_adapter, linear_adapter, calendar_adapter
# - cost_tracker, resilient_briefing, scheduler

# Analyze impact
impact = tracker.get_service_impact("github_adapter")
print(f"Risk: {impact['risk_level']}")
print(f"Affected: {impact['total_reachable']}")

# Get resilience strategies
strategies = tracker.suggest_resilience_strategy("briefing_service")
for s in strategies:
    print(f"Strategy: {s}")
```

### Output Example

```
Service: briefing_service
Risk Level: HIGH
Services Affected: 6
Critical Services Impacted: ['briefing_service']

Suggested Strategies:
  • Implement circuit breaker pattern
  • Add redundant fallback service
  • Consider service mesh for dependency management
```

## Persistence

### Save and Load

```python
# Save graph and embeddings
kg.save("/path/to/my_knowledge_graph")

# Creates:
#   my_knowledge_graph.ttl (RDF/Turtle format)
#   my_knowledge_graph_embeddings.json

# Load later
kg = KnowledgeGraphReasoner.load("/path/to/my_knowledge_graph")
```

## Performance Tips

### 1. Limit Search Depth

```python
# Use depth=2 for most queries (faster)
result = kg.symbolic_reasoning(entity, depth=2)

# Use depth=5+ only when needed (slower)
result = kg.symbolic_reasoning(entity, depth=5)
```

### 2. Cache Similarity Computations

```python
# Pre-compute similarity matrix
similarity_cache = {}
for e1 in entities:
    for e2 in entities:
        similarity_cache[(e1, e2)] = kg.compute_similarity(e1, e2)
```

### 3. Batch Entity Addition

```python
# Add multiple entities at once
for entity_data in bulk_data:
    kg.add_entity(**entity_data)

# Then add relations
for relation_data in bulk_relations:
    kg.add_relation(**relation_data)
```

## Troubleshooting

### Slow Queries

```python
# Limit depth
kg.symbolic_reasoning(entity, depth=2)  # Not 10

# Filter by relation type
# (modify symbolic_reasoning to accept relation filter)
```

### Missing Embeddings

```python
# Check if embedding exists
if entity_id not in kg.embeddings:
    # Generate default embedding
    kg.add_embedding(entity_id, np.zeros(10))
```

### Graph Inconsistencies

```python
# Validate graph before reasoning
def validate_graph(kg):
    # Check for orphaned entities
    all_entities = set()
    connected_entities = set()
    
    for s, p, o in kg.graph:
        all_entities.add(str(s))
        all_entities.add(str(o))
        connected_entities.add(str(s))
        connected_entities.add(str(o))
    
    orphaned = all_entities - connected_entities
    if orphaned:
        print(f"Warning: {len(orphaned)} orphaned entities")
```

## See Also

- `neuro-symbolic-overview` - General introduction
- `neuro-symbolic-ltn` - Logic Tensor Networks
- `neuro-symbolic-validator` - Rule-based validation
- `neuro-symbolic-founder` - founder_mode specific
