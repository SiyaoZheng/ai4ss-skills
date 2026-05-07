#!/usr/bin/env python3
"""aiss fact checker — static verification (T1-T8) for .aiss models.

Usage:
    python3 aiss_checker.py model.aiss
    python3 aiss_checker.py model.aiss --json
"""

from __future__ import annotations
import json
import re
import sys
from collections import defaultdict
from itertools import product
from pathlib import Path

from aiss_parser import (
    Program, AttributeNode, ConceptNode, CausalNode,
    BridgeNode, EdgeNode, ModelNode,
    parse_file,
)


class CheckResult:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def error(self, msg: str):
        self.errors.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)


def check_all(prog: Program, filename: str = "<input>") -> CheckResult:
    r = CheckResult()

    # ---- Build lookup tables ----
    attrs: dict[str, AttributeNode] = {a.id: a for a in prog.attributes}
    concepts: dict[str, ConceptNode] = {c.id: c for c in prog.concepts}
    causals: dict[str, CausalNode] = {c.id: c for c in prog.causals}
    bridges: dict[str, BridgeNode] = {b.id: b for b in prog.bridges}
    models: dict[str, ModelNode] = {m.id: m for m in prog.models}
    all_nodes = set(attrs) | set(concepts) | set(bridges) | set(models)

    # Also collect implicit hasAttribute edges from concept.parents
    implicit_edges: list[tuple[str, str, str]] = []
    for c in prog.concepts:
        for p in c.parents:
            implicit_edges.append((c.id, p, "hasAttribute"))

    # Collect all edges (causal + explicit + implicit)
    all_edge_refs: list[tuple[str, str, str]] = []
    for c in prog.causals:
        all_edge_refs.append((c.source, c.target, "causes"))
    for e in prog.edges:
        all_edge_refs.append((e.source, e.target, e.relation))
    all_edge_refs.extend(implicit_edges)

    # ---- T7: ID format ----
    id_pattern = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")
    for node_id in attrs:
        if not id_pattern.match(node_id):
            r.error(f"T7: attribute '{node_id}' does not match pattern {{author}}.{{name}}")
    for node_id in concepts:
        if not id_pattern.match(node_id):
            r.error(f"T7: concept '{node_id}' does not match pattern {{author}}.{{name}}")
    for node_id in causals:
        if not id_pattern.match(node_id):
            r.error(f"T7: causal '{node_id}' does not match pattern {{author}}.{{name}}")
    for node_id in bridges:
        if not id_pattern.match(node_id):
            r.error(f"T7: bridge '{node_id}' does not match pattern {{author}}.{{name}}")

    # ---- T1: θ completeness ----
    for c in prog.concepts:
        if not c.parents:
            continue
        expected_rows = 1
        dim_sizes = []
        for parent_id in c.parents:
            if parent_id in attrs:
                n = len(attrs[parent_id].values)
                dim_sizes.append(n)
                expected_rows *= n
            else:
                r.warn(f"T1: concept '{c.id}' references unknown parent '{parent_id}' (skip θ check)")
        if expected_rows > 1:
            actual_rows = len(c.theta)
            # definitional concepts: sparse θ OK (only C=1 rows listed, rest implicit 0)
            if c.rule == "definitional":
                ones = sum(1 for v in c.theta.values() if v == 1 or v == "1")
                if ones != 1:
                    r.error(
                        f"T1: concept '{c.id}' definitional but has {ones} rows with output=1 (expected exactly 1)"
                    )
                elif actual_rows > expected_rows:
                    r.error(
                        f"T1: concept '{c.id}' θ has {actual_rows} rows but only {expected_rows} combinations exist"
                    )
                # sparse definitional θ with exactly 1 C=1 row is valid
            elif actual_rows != expected_rows:
                r.error(
                    f"T1: concept '{c.id}' θ has {actual_rows} rows, "
                    f"expected {expected_rows} (parent dims: {dim_sizes})"
                )

    # ---- T2: θ-rule consistency ----
    for c in prog.concepts:
        rule = c.rule
        if rule == "undecomposed":
            if c.parents:
                r.error(f"T2: concept '{c.id}' has rule='undecomposed' but has parents")
            if len(c.theta) != 1 or list(c.theta.keys())[0] != "none":
                r.error(f"T2: concept '{c.id}' undecomposed but θ != {{\"none\": 1}}")
        elif rule == "exhaustive_typology":
            outcomes = set(c.theta.values())
            if len(outcomes) != len(c.theta):
                r.error(
                    f"T2: concept '{c.id}' exhaustive_typology but outcomes not all unique "
                    f"({len(outcomes)} unique / {len(c.theta)} rows)"
                )
        elif rule == "definitional":
            ones = sum(1 for v in c.theta.values() if v == 1 or v == "1")
            if ones > 1:
                r.warn(
                    f"T2: concept '{c.id}' definitional but has {ones} rows with output=1 "
                    f"(expected exactly 1)"
                )

    # ---- T3: Reference integrity ----
    # parent_ids must resolve
    for c in prog.concepts:
        for p in c.parents:
            if p not in attrs:
                r.error(f"T3: concept '{c.id}' parent '{p}' not found in attributes")
    # edge sources/targets
    for c in prog.causals:
        if c.source not in concepts:
            r.error(f"T3: causal '{c.id}' source '{c.source}' not found in concepts")
        if c.target not in concepts:
            r.error(f"T3: causal '{c.id}' target '{c.target}' not found in concepts")
    for e in prog.edges:
        if e.source not in (all_nodes):
            r.error(f"T3: edge '{e.relation}' source '{e.source}' not found")
        if e.target not in (all_nodes):
            r.error(f"T3: edge '{e.relation}' target '{e.target}' not found")
    # model members
    for m in prog.models:
        for a_id in m.attributes:
            if a_id not in attrs:
                r.error(f"T3: model '{m.id}' references unknown attribute '{a_id}'")
        for c_id in m.concepts:
            if c_id not in concepts:
                r.error(f"T3: model '{m.id}' references unknown concept '{c_id}'")
        for c_id in m.causal:
            if c_id not in causals:
                r.error(f"T3: model '{m.id}' references unknown causal '{c_id}'")
        for b_id in m.bridges:
            if b_id not in bridges:
                r.error(f"T3: model '{m.id}' references unknown bridge '{b_id}'")
    # bridge references
    for b in prog.bridges:
        if b.concept and b.concept not in concepts:
            r.error(f"T3: bridge '{b.id}' references unknown concept '{b.concept}'")
        if b.implication and b.implication not in causals:
            r.error(f"T3: bridge '{b.id}' references unknown causal '{b.implication}'")

    # ---- T4: Edge domain rules ----
    # hasAttribute (implicit from concept.parents): source=concept, target=attribute
    # Already checked by T3 structural constraints.
    # causes: source/target both concept
    for c in prog.causals:
        if c.source not in concepts:
            r.error(f"T4: causal '{c.id}' source '{c.source}' is not a concept")
        if c.target not in concepts:
            r.error(f"T4: causal '{c.id}' target '{c.target}' is not a concept")

    # ---- T5: Composition value validity ----
    # Not applicable in current DSL: composition_value is not explicit in syntax.
    # hasAttribute edges are derived from concept.parents (which is always valid by construction).

    # ---- T6: No self-loops ----
    for c in prog.causals:
        if c.source == c.target:
            r.error(f"T6: causal '{c.id}' has self-loop ({c.source} -> {c.target})")
    for e in prog.edges:
        if e.source == e.target:
            r.error(f"T6: edge '{e.relation}' has self-loop ({e.source} -> {e.target})")

    # ---- T8: No orphan concepts ----
    for c in prog.concepts:
        is_source = any(c.id == src for src, _, _ in all_edge_refs)
        is_target = any(c.id == tgt for _, tgt, _ in all_edge_refs)
        if not is_source and not is_target and c.rule != "undecomposed":
            r.warn(f"T8: concept '{c.id}' appears in no edges and is not undecomposed")

    # ---- Bridge coverage ----
    bridged_implications = {
        b.implication for b in prog.bridges
        if b.bridge_type == "causal" and b.implication
    }
    for c in prog.causals:
        if c.id not in bridged_implications:
            r.warn(f"bridge: causal '{c.id}' has no empirical bridge")
    for b in prog.bridges:
        if b.bridge_type == "causal" and b.commensurability == "unchecked":
            r.warn(f"commensurability: bridge '{b.id}' is unchecked")

    # ---- T9: Layer semantics (OWL-inspired stratified expressiveness) ----
    # Infer the effective layer from what primitives are used
    has_relations = len(prog.edges) > 0
    has_causals = len(prog.causals) > 0
    has_bridges = len(prog.bridges) > 0
    inferred_layer = 0
    if has_bridges:
        inferred_layer = 3
    elif has_causals:
        inferred_layer = 2
    elif has_relations:
        inferred_layer = 1

    # L0: concept + attribute + θ only. No broader/narrower, no causal, no bridge.
    if has_relations or has_causals or has_bridges:
        layer0_violations = []
        if has_relations:
            layer0_violations.append(f"{len(prog.edges)} broader/narrower edges")
        if has_causals:
            layer0_violations.append(f"{len(prog.causals)} causal relations")
        if has_bridges:
            layer0_violations.append(f"{len(prog.bridges)} bridges")
        if layer0_violations:
            r.warn(f"T9-L0: model uses {', '.join(layer0_violations)} "
                   f"— Layer 0 (description only) is decidable via FCA; "
                   f"Layer 1+ reduces decidability")

    # L2: causal edges exist but bridges are missing
    if has_causals and not has_bridges:
        r.warn(f"T9-L2: model has {len(prog.causals)} causal edges but no bridges "
               f"— causal claims are semi-decidable (SCM-based); "
               f"add bridges to connect theory to empirics")

    # Per-model layer check
    for m in prog.models:
        m_has_causals = len(m.causal) > 0
        m_has_bridges = len(m.bridges) > 0
        if m_has_causals and not m_has_bridges:
            r.warn(f"T9: model '{m.id}' has causal edges but no bridges "
                   f"(Layer 2 — no commensurability assessment possible)")

    return r


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 aiss_checker.py <file.aiss> [--json]", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]
    output_json = "--json" in sys.argv
    prog = parse_file(filepath)
    result = check_all(prog, filepath)

    if output_json:
        print(json.dumps({
            "ok": result.ok,
            "errors": result.errors,
            "warnings": result.warnings,
        }, indent=2))
    else:
        print(f"Checking {filepath}...")
        print(f"  errors:   {len(result.errors)}")
        print(f"  warnings: {len(result.warnings)}")
        for e in result.errors:
            print(f"  ❌ {e}")
        for w in result.warnings:
            print(f"  ⚠️  {w}")
        if result.ok:
            print("  ✓ all checks passed")
        else:
            print(f"  ✗ {len(result.errors)} errors found")

    sys.exit(0 if result.ok else 1)


if __name__ == "__main__":
    main()
