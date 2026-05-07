# concept-dag v0.2 Schema

Fuses three primitives:
- **DeclareDesign**: theory as executable simulation (M/I/D/A separation, pipeline composition)
- **Integrated Inferences**: theory as causal model hierarchy (nodal types θ, lower→higher implication)
- **concept-dag v0.1**: attribute/composition_rule/lineageFrom (labels only)

## Core Insight

A **concept** is a node whose value is determined by its parent nodes (attributes or other concepts)
through a **θ function** (theta function) — a non-parametric encoding of all possible ways the node
can respond to its parents.

For a concept C with n binary attributes, there are 2^(2^n) possible θ types.
The composition_rule SELECTS which subset of these types are valid definitions of the concept.

This makes concepts **executable**: given attribute values for a case, you can evaluate
whether the concept applies under a given composition rule.

## 1. θ (theta) — The First-Class Primitive

θ is a **node-level truth table**. For a concept C with parent attributes [A1, A2, ..., An],
θ_C encodes how C responds to EVERY combination of parent values. This is the nodal type
from Humphreys & Jacobs (2023) — the non-parametric, executable encoding of a concept definition.

```
θ is the truth table itself (on the concept node).
theta_spec is METADATA about θ: which attributes are parents, how θ is constrained.
composition_rule is a LABEL for the pattern in θ's truth table.
```

### Two kinds of θ

| θ_type | Direction | Meaning | Extracted by |
|---|---|---|---|
| `constitutive` | attribute → concept | How attributes COMPOSE to define the concept | Skill 1 (concept-dag) |
| `causal` | concept → concept | How one concept CAUSALLY affects another | Skill 2 (future) |

This skill extracts **constitutive θ only**.

### θ as truth table

```json
// One parent, categorical values
"theta": { "one": 1, "few": 0, "many": 0 }

// Two binary parents — keys encode (A1_value, A2_value)
"theta": { "00": 0, "01": 0, "10": 0, "11": 1 }

// Undecomposed concept (no parent attributes)
"theta": { "none": 1 }
```

### theta_spec: metadata about θ

```json
"theta_spec": {
  "theta_type": "constitutive",
  "parent_ids": ["aristotle.num_rulers"],
  "composition_rule": "definitional",
  "composition_description": "monarchy exists iff exactly one person rules"
}
```

### Composition rules as θ patterns

| composition_rule | Pattern in θ's truth table |
|---|---|
| `necessary_conjunction` | C=1 iff ALL parents are at their designated values |
| `sufficient_conjunction` | C=1 if ANY parent is at its designated value |
| `aggregative` | C = monotonic function of Σ parent values |
| `threshold` | C=1 when Σ parent_values ≥ k |
| `family_resemblance` | C=1 when majority of parents are satisfied |
| `definitional` | a single row in θ's truth table gives C=1 |
| `undecomposed` | no parent attributes; θ = {"none": 1}

## 2. MIDA Separation for Concepts

Every concept can carry four linked but distinct components,
mirroring DeclareDesign's separation:

```
concept = {
  definition (M):          theta_spec — the attributes and composition rule
  inquiry (I):             what question we ask about this concept
  operationalization (D):  how attributes are measured/observed in practice
  estimation (A):          how measurements are combined to determine concept membership
}
```

### Schema extension

```json
{
  "concept": {
    "id": "vw.legislative_effectiveness",
    "label": "Legislative Effectiveness",
    "theta_spec": { ... },

    "inquiry": {
      "target": "which legislators are effective?",
      "scope": "US House 1973-2017",
      "inquiry_type": "classification | ranking | comparison"
    },

    "operationalization": {
      "attributes_measured": {
        "bill_progress": "15-stage bill progress score",
        "bill_significance": "commemorative=1, substantive=5, substantive+significant=10",
        "lagged_expectations": "relative to benchmark SLES for same term, chamber, party"
      },
      "scoring_formula": "score_i = Σ (bill_progress × bill_significance) / benchmark",
      "measurement_error": "assumed_none | estimated_variance"
    },

    "estimation": {
      "method": "weighted sum with benchmark normalization",
      "links_to_inquiry": "score_i > 1.0 → 'above expectations'",
      "diagnosands": ["reliability_across_sessions", "rank_stability"]
    }
  }
}
```

This allows **diagnosis**: if the `definition` (M) says the concept depends on attributes {A1, A2, A3}
with a threshold rule, but the `operationalization` (D) measures only {A1, A2} and adds noise to A1,
the gap between M and D is the measurement error diagnostically recoverable.

## 3. lineageFrom as Model Implication

`lineageFrom` is no longer just "cited by". It is a formal relationship
between two θ specifications:

```
lineageFrom(C_child, C_parent):
  C_parent's θ types are a PROJECTION of C_child's θ types
  onto a coarser parent space.

  If C_child has parents {A1, A2, A3} and C_parent has parents {A1, A2},
  then θ_parent is implied by marginalizing θ_child over A3.
```

### lineageFrom schema extension

```json
{
  "source": "vw.legislative_effectiveness_by_score",
  "target": "schlesinger.ambition_driven_selection",
  "relation": "lineageFrom",
  "lineage": {
    "implication_type": "projection | refinement | counterexample",
    "child_theta_spec_id": "vw.les_theta",
    "parent_theta_spec_id": "schlesinger.ambition_theta",
    "marginalized_attribute": "policy_impact_track_record",
    "consistency": "consistent | subset | contradicts",
    "lineage_note": "VW operationalize what Schlesinger only asserted: effectiveness score replaces binary ambition variable"
  }
}
```

`implication_type`:
- **projection**: child concept has MORE attributes; parent is a projection onto fewer attributes
- **refinement**: child uses same attributes but stricter composition rule
- **counterexample**: child's θ types are a subset of what parent's rule would predict — empirical narrowing

## 4. Attribute Types (v0.1, kept)

```json
{
  "attribute_type": "categorical | scalar | binary | continuous",
  "allowed_values": ["one", "few", "many"],
  "range": [0, 100],
  "unit": "bill count"
}
```

## 5. Graph-Level MIDA

The entire DAG can be viewed through the MIDA lens:

- **M (Model)**: all concept θ specifications + their attribute parent edges → the theory graph
- **I (Inquiry)**: the set of inquiry nodes → what scholars want to discover
- **D (Data Strategy)**: operationalization edges → how constructs are measured
- **A (Answer Strategy)**: estimation edges → how measurements produce answers

Diagnosing the whole graph means: for each inquiry, trace the path
M → I ← D → A and check for gaps, inconsistencies, under-determination.

## 6. Execution & Simulation

A concept definition with a complete theta_spec is **executable**:

```python
def evaluate_concept(concept_id, attribute_values, graph):
    """Given attribute values for a case, determine concept membership."""
    concept = graph.nodes[concept_id]
    theta = concept.theta_spec
    parent_values = [attribute_values[p] for p in theta.parent_ids]
    return theta.composition_function(parent_values)

def simulate_concept(concept_id, graph, n_cases=1000):
    """Generate cases from the concept's theta distribution and evaluate."""
    for each case:
        draw attribute values from prior/empirical distribution
        concept_value = evaluate_concept(concept_id, attributes, graph)
    return distribution of concept values
```

This turns the concept DAG from a static knowledge graph into
a **theory simulation engine** — exactly what DeclareDesign does for
research designs, but applied to concept definitions.

## 7. Migration from v0.1

| v0.1 field | v0.2 |
|---|---|
| `composition_rule: "aggregative"` | `theta_spec.composition_rule: "aggregative"` + `theta_spec.valid_types: [...]` |
| (none) | `theta_spec.composition_function: "..."` |
| (none) | `inquiry: {...}` |
| (none) | `operationalization: {...}` |
| (none) | `estimation: {...}` |
| `lineage_note: "VW built on Schlesinger"` | `lineage.implication_type: "refinement"` + `lineage.consistency: "consistent"` |
| `hasAttribute` (flat edge) | `hasAttribute` edge + `theta_spec.parent_ids` includes this attribute |
| `contrastsWith` (flat edge) | `contrastsWith` + `contrast.theta_divergence: "same_attributes_different_rule"` |

Backward compatible: v0.1 nodes without theta_spec are treated as `undecomposed`
(all θ types possible — the black-box case).
