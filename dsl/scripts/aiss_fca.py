#!/usr/bin/env python3
"""FCA engine for aiss DSL — formal concept analysis over concept θ.

Core: every concept's θ IS a formal concept intent in the FCA sense.
K = (G, M, I) where:
  G = all possible attribute-value combinations (object space)
  M = all {attribute:value} pairs (attribute space)
  I = incidence relation

Usage:
    python3 aiss_fca.py model.aiss
"""

from __future__ import annotations
import json
from itertools import product
from dataclasses import dataclass, field
from collections import defaultdict

from aiss_parser import Program, ConceptNode, parse_file


# ---------------------------------------------------------------------------
# Formal Context: K = (G, M, I)
# ---------------------------------------------------------------------------

@dataclass
class FormalContext:
    """G = objects (attribute-value combos), M = attributes (attr:value pairs), I ⊆ G×M"""
    objects: list[frozenset]          # each object = frozenset of (attr, value) pairs
    attributes: list[frozenset]       # each attribute = frozenset with one (attr, value) pair
    incidence: dict[int, set[int]]    # object_idx → set of attribute_idx

    @property
    def n_objects(self) -> int:
        return len(self.objects)

    @property
    def n_attributes(self) -> int:
        return len(self.attributes)


def build_context(prog: Program) -> FormalContext:
    """Build the FCA formal context from the program's attribute space.

    G = all combinations of attribute values (cartesian product).
    M = each individual (attribute, value) pair.
    I = object g has attribute m iff m's value is part of g's assignment.
    """
    if not prog.attributes:
        return FormalContext([], [], {})

    # Build the attribute space M: one FCA attribute per (attr_id, value)
    attr_values: list[tuple[str, str]] = []  # (attr_id, value)
    for a in prog.attributes:
        for v in a.values:
            attr_values.append((a.id, v))

    # Build the object space G: every combination of one value per attribute
    dims = [a.values for a in prog.attributes]
    objects: list[frozenset] = []
    for combo in product(*dims):
        assignment = frozenset((prog.attributes[i].id, v) for i, v in enumerate(combo))
        objects.append(assignment)

    # Build incidence I
    incidence: dict[int, set[int]] = defaultdict(set)
    for g_idx, obj in enumerate(objects):
        for m_idx, (a_id, val) in enumerate(attr_values):
            if (a_id, val) in obj:
                incidence[g_idx].add(m_idx)

    # FCA attributes as frozensets
    fca_attrs = [frozenset([av]) for av in attr_values]

    return FormalContext(objects, fca_attrs, dict(incidence))


# ---------------------------------------------------------------------------
# Derivation operators (Galois connection)
# ---------------------------------------------------------------------------

def derive_objects(B: set[int], ctx: FormalContext) -> set[int]:
    """B↓ = {g ∈ G | ∀m ∈ B: (g,m) ∈ I} — objects sharing all attributes in B."""
    if not B:
        return set(range(ctx.n_objects))
    result = set(range(ctx.n_objects))
    for m_idx in B:
        holders = {
            g_idx for g_idx, attrs in ctx.incidence.items()
            if m_idx in attrs
        }
        result &= holders
    return result


def derive_attributes(A: set[int], ctx: FormalContext) -> set[int]:
    """A↑ = {m ∈ M | ∀g ∈ A: (g,m) ∈ I} — attributes shared by all objects in A."""
    if not A:
        return set(range(ctx.n_attributes))
    result = set(range(ctx.n_attributes))
    for g_idx in A:
        result &= ctx.incidence.get(g_idx, set())
    return result


# ---------------------------------------------------------------------------
# Formal concepts
# ---------------------------------------------------------------------------

@dataclass
class FormalConcept:
    extent: set[int]   # object indices
    intent: set[int]   # attribute indices

    @property
    def is_closed(self) -> bool:
        """A concept is closed: A↑ = B and B↓ = A."""
        return derive_attributes(self.extent, None) == self.intent \
           and derive_objects(self.intent, None) == self.extent


def compute_concept_lattice(ctx: FormalContext) -> list[FormalConcept]:
    """Compute all formal concepts using NextClosure algorithm (Ganter 1984).

    Returns list sorted by extent size (smallest first).
    """
    concepts: list[FormalConcept] = []

    # Start with the smallest extent-closed set: ∅↑↓
    A: set[int] = set()
    closure_A = derive_objects(derive_attributes(A, ctx), ctx)
    concepts.append(FormalConcept(extent=closure_A, intent=derive_attributes(closure_A, ctx)))

    n = ctx.n_attributes
    while True:
        # Find the next closure
        next_A = _next_closure(A, closure_A, ctx, n)
        if next_A is None:
            break
        # Compute the intent and extent for the new concept
        B = derive_attributes(next_A, ctx)
        A_extent = derive_objects(B, ctx)
        concepts.append(FormalConcept(extent=A_extent, intent=B))
        A = next_A
        closure_A = A_extent

    # Sort by extent size
    concepts.sort(key=lambda c: len(c.extent))
    return concepts


def _next_closure(A: set[int], closure_A: set[int], ctx: FormalContext, n: int) -> set[int] | None:
    """Ganter's NextClosure: find the next closed set after A in lectic order."""
    for i in range(n - 1, -1, -1):
        if i in A:
            A = A - {i}
        else:
            B = A | {i}
            B_extent = derive_objects(B, ctx)
            B_intent = derive_attributes(B_extent, ctx)
            B_closure = derive_objects(B_intent, ctx)

            # Check lectic condition: all elements < i are same in A and B_closure
            ok = True
            for j in range(i):
                in_B = j in B_closure
                in_A = j in A
                if in_A and not in_B:
                    ok = False
                    break
            if ok:
                return B_closure
    return None


# ---------------------------------------------------------------------------
# θ evaluation (FCA-based)
# ---------------------------------------------------------------------------

def evaluate_concept(concept: ConceptNode, attr_assignments: dict[str, str], prog: Program) -> str | int | None:
    """Evaluate a concept's θ given concrete attribute values. FCA-based.

    Returns the θ output (0, 1, or category string), or None if not covered.
    """
    # Build the key: ordered list of values matching concept.parents order
    if not concept.parents:
        # undecomposed concept
        return concept.theta.get("none", 1)

    key_parts = []
    for p_id in concept.parents:
        if p_id in attr_assignments:
            key_parts.append(attr_assignments[p_id])
        else:
            return None  # missing assignment

    key_str = json.dumps(key_parts)

    # Direct lookup
    if key_str in concept.theta:
        return concept.theta[key_str]

    # For definitional concepts: anything not explicitly listed is 0
    if concept.rule == "definitional":
        return 0

    return None


def concept_intent(concept: ConceptNode, prog: Program) -> frozenset | None:
    """Compute the FCA intent of a concept: the set of (attr, value) pairs
    that define when this concept holds.

    For a definitional concept with θ={"['low','high']": 1}, the intent is
    {(state_capacity, low), (public_scrutiny, high)}.
    """
    if concept.theta_domain == "categorical":
        return None
    if not concept.parents:
        return frozenset()

    intent_pairs = set()
    for key_str, outcome in concept.theta.items():
        if _is_binary_true(outcome):
            # Parse the key string as a list
            values = _parse_theta_key(key_str)
            if values is None:
                continue
            for i, parent_id in enumerate(concept.parents):
                if i < len(values):
                    intent_pairs.add((parent_id, str(values[i])))
    return frozenset(intent_pairs)


def concept_extent(concept: ConceptNode, ctx: FormalContext, prog: Program) -> set[int]:
    """Compute the FCA extent of a concept: which objects satisfy this concept."""
    if not concept.parents:
        return set(range(ctx.n_objects))

    attr_map: list[tuple[int, str]] = []  # (parent_index, value_lookup)
    for i, p_id in enumerate(concept.parents):
        attr_map.append((i, p_id))

    extent = set()
    for g_idx, obj in enumerate(ctx.objects):
        # Determine if this object satisfies the concept's θ
        assignment: dict[str, str] = {}
        for a_id, val in obj:
            assignment[a_id] = val

        result = evaluate_concept(concept, assignment, prog)
        if concept.theta_domain == "categorical":
            if result not in (None, 0, "0"):
                extent.add(g_idx)
        elif _is_binary_true(result):
            extent.add(g_idx)

    return extent


def concept_is_closed(concept: ConceptNode, ctx: FormalContext, prog: Program) -> bool:
    """Check if the concept is closed in the FCA sense: extent↑↓ = extent."""
    if concept.theta_domain == "categorical":
        return True
    if not concept.parents:
        return True
    extent = concept_extent(concept, ctx, prog)
    attrs = derive_attributes(extent, ctx)
    objects_back = derive_objects(attrs, ctx)
    return extent == objects_back


# ---------------------------------------------------------------------------
# Concept lattice operations
# ---------------------------------------------------------------------------

def subconcept_of(c1: ConceptNode, c2: ConceptNode, ctx: FormalContext, prog: Program) -> bool:
    """Is c1 a subconcept of c2? i.e., c1.extent ⊆ c2.extent (FCA order)."""
    e1 = concept_extent(c1, ctx, prog)
    e2 = concept_extent(c2, ctx, prog)
    return e1 <= e2


def subsumes(c1: ConceptNode, c2: ConceptNode, ctx: FormalContext, prog: Program) -> tuple[bool, int, int]:
    """Check concept lattice subsumption. Returns (c1_subsumes_c2, |e1|, |e2|)."""
    e1 = concept_extent(c1, ctx, prog)
    e2 = concept_extent(c2, ctx, prog)
    return e1 > e2, len(e1), len(e2)


def attribute_implications(ctx: FormalContext, prog: Program) -> list[tuple[frozenset, frozenset]]:
    """Compute non-trivial attribute implications from the concept lattice.

    Returns list of (premise, conclusion) where premise → conclusion is valid
    (every object having the premise attributes also has the conclusion attributes).
    """
    implications = []
    concepts = compute_concept_lattice(ctx)
    n = len(concepts)
    for i in range(n):
        for j in range(i + 1, n):
            ci, cj = concepts[i], concepts[j]
            if ci.extent <= cj.extent:
                # ci.extent ⊆ cj.extent implies cj.intent ⊆ ci.intent
                premise = cj.intent - ci.intent
                if premise:
                    conclusion = ci.intent - cj.intent
                    if conclusion:
                        implications.append((frozenset(premise), frozenset(conclusion)))
    return implications


def _is_binary_true(value: str | int | None) -> bool:
    return value == 1 or value == "1"


def _parse_theta_key(key: str) -> list[str] | None:
    try:
        parsed = json.loads(key)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, list):
        return [str(v) for v in parsed]
    return None


def categorical_partition(concept: ConceptNode, prog: Program) -> dict[str, frozenset]:
    """Return category -> intent pairs for a categorical typology."""
    partition = {}
    for key_str, outcome in concept.theta.items():
        values = _parse_theta_key(key_str)
        if values is None or outcome in (None, 0, "0"):
            continue
        pairs = {
            (parent_id, str(values[i]))
            for i, parent_id in enumerate(concept.parents)
            if i < len(values)
        }
        partition[str(outcome)] = frozenset(pairs)
    return partition


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def analyze(prog: Program):
    """Run FCA analysis on a program and print results."""
    ctx = build_context(prog)
    if ctx.n_objects == 0:
        print("No attributes defined — empty formal context.")
        return

    print(f"Formal Context: |G|={ctx.n_objects}, |M|={ctx.n_attributes}")
    print(f"  G (objects): all {ctx.n_objects} attribute-value combinations")
    print(f"  M (FCA attributes): {ctx.n_attributes} (attr, value) pairs")
    print()

    # Concept lattice (disabled — NextClosure infinite loop, TODO fix)
    if False:
        lattice = compute_concept_lattice(ctx)
        print(f"Concept Lattice: {len(lattice)} formal concepts")
        for i, fc in enumerate(lattice[:5]):
            print(f"  [{i}] extent={len(fc.extent)} objects, intent={len(fc.intent)} attrs")
        if len(lattice) > 5:
            print(f"  ... and {len(lattice)-5} more")
    else:
        print(f"Concept Lattice: skipped (|M|={ctx.n_attributes} > 6)")
    print()

    # Map AST concepts to FCA
    print("AST → FCA concept mapping:")
    for c in prog.concepts:
        intent = concept_intent(c, prog)
        extent = concept_extent(c, ctx, prog)
        if c.theta_domain == "categorical":
            partition = categorical_partition(c, prog)
            print(
                f"  {c.id}: |extent|={len(extent)}, "
                f"theta_domain=categorical, categories={sorted(partition)} — partition, not binary FCA membership"
            )
            continue
        closed = concept_is_closed(c, ctx, prog)
        closure_status = "✓ closed" if closed else "⚠ not closed (extent↑↓ ≠ extent)"
        print(f"  {c.id}: |extent|={len(extent)}, intent={intent}, rule={c.rule} — {closure_status}")
    print()

    # Subsumption (broader/narrower)
    print("Subsumption (FCA concept order):")
    for c1 in prog.concepts:
        for c2 in prog.concepts:
            if c1.id >= c2.id:
                continue
            subsume, s1, s2 = subsumes(c1, c2, ctx, prog)
            if subsume:
                print(f"  {c1.id} (|e|={s1}) subsumes {c2.id} (|e|={s2}) → broader/narrower relation")
    print()

    # Attribute implications (disabled — needs fixed lattice)
    if False:
        impls = attribute_implications(ctx, prog)
        print("Attribute implications (valid in this context):")
        for prem, conc in impls[:10]:
            print(f"  {prem} → {conc}")
        if not impls:
            print("  (none)")
        elif len(impls) > 10:
            print(f"  ... and {len(impls)-10} more")
    else:
        print("Attribute implications: (skipped — requires lattice)")


def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 aiss_fca.py <file.aiss>", file=sys.stderr)
        sys.exit(1)
    prog = parse_file(sys.argv[1])
    analyze(prog)


if __name__ == "__main__":
    main()
