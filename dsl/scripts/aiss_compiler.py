#!/usr/bin/env python3
"""aiss compiler — AST → graphify-compatible JSON.

Usage:
    python3 aiss_compiler.py model.aiss > graph.json
    python3 aiss_compiler.py model.aiss --stdout
"""

from __future__ import annotations
from dataclasses import asdict
import json
import sys
from pathlib import Path

from aiss_parser import (
    Program, AttributeNode, ConceptNode, CausalNode,
    BridgeNode, EdgeNode, ModelNode, FactNode, CheckNode, DeriveNode,
    parse_file,
)


def compile_to_graphify(prog: Program, source_file: str = "<input>") -> dict:
    """Compile a parsed Program into graphify-compatible JSON."""
    nodes: list[dict] = []
    edges: list[dict] = []

    # Track IDs
    all_ids: set[str] = set()

    def emit_node(id: str, label: str, file_type: str = "concept", **extras):
        if id in all_ids:
            # Duplicate — skip (first definition wins, like graphify)
            return
        all_ids.add(id)
        node = {
            "id": id,
            "label": label,
            "file_type": file_type,
            "source_file": source_file,
            **extras,
        }
        nodes.append(node)

    def emit_edge(source: str, target: str, relation: str,
                  confidence: str = "EXTRACTED", confidence_score: float = 1.0,
                  source_location: str | None = None, **extras):
        edge = {
            "source": source,
            "target": target,
            "relation": relation,
            "confidence": confidence,
            "confidence_score": confidence_score,
            "source_file": source_file,
            **extras,
        }
        if source_location:
            edge["source_location"] = source_location
        edges.append(edge)

    # ---- Attributes ----
    for attr in prog.attributes:
        emit_node(
            attr.id,
            attr.id.split(".")[-1].replace("_", " ").title() if "." in attr.id else attr.id,
            file_type="concept",
            node_type="attribute",
            attribute_type=attr.domain,
            allowed_values=attr.values if attr.values else None,
            scope_note=attr.description,
            source_location=attr.source,
        )

    # ---- Concepts ----
    for c in prog.concepts:
        parents = c.parents or []
        theta = c.theta or ({"none": 1} if not parents else {})

        # Build theta_spec
        theta_spec = {
            "theta_type": "constitutive",
            "theta_domain": c.theta_domain,
            "parent_ids": parents,
            "composition_rule": c.rule,
            "composition_description": c.description or "",
        }

        emit_node(
            c.id,
            c.id.split(".")[-1].replace("_", " ").title() if "." in c.id else c.id,
            file_type="concept",
            node_type="concept",
            author=c.id.split(".")[0] if "." in c.id else None,
            theta=theta,
            theta_domain=c.theta_domain,
            theta_spec=theta_spec,
            operationalization=c.operationalization,
            decomposable=len(parents) > 0,
            proposed_elsst_label=c.elsst_label,
            scope_note=c.description,
            source_location=c.source,
        )

        # Derive hasAttribute edges from parents
        for parent_id in parents:
            emit_edge(
                c.id, parent_id, "hasAttribute",
                confidence="EXTRACTED", confidence_score=1.0,
                source_location=c.source,
            )

    # ---- Causal edges ----
    for causal in prog.causals:
        emit_edge(
            causal.source, causal.target, "causes",
            confidence=causal.textual_support,
            confidence_score=_conf_to_score(causal.textual_support),
            source_location=None,
            direction=causal.direction,
            condition=causal.condition,
            mechanism=causal.mechanism,
        )

    # ---- Explicit edges ----
    for edge in prog.edges:
        emit_edge(
            edge.source, edge.target, edge.relation,
            confidence=edge.confidence,
            confidence_score=_conf_to_score(edge.confidence),
            source_location=edge.source_location,
        )

    # ---- Bridges ----
    for bridge in prog.bridges:
        bridge_node_id = bridge.id
        bridge_label = f"Bridge: {bridge.id}"
        emit_node(
            bridge_node_id, bridge_label,
            file_type="concept",
            node_type="bridge",
            bridge_type=bridge.bridge_type,
            commensurability=bridge.commensurability,
            scope_note=bridge.note,
        )
        if bridge.bridge_type == "measurement" and bridge.concept:
            emit_edge(
                bridge_node_id, bridge.concept, "bridges",
                confidence="EXTRACTED", confidence_score=1.0,
                method=bridge.method,
                validity=bridge.validity,
            )
        elif bridge.bridge_type == "causal" and bridge.implication:
            # Resolve the causal edge to its source/target concepts
            causal = _find_causal(prog, bridge.implication)
            if causal:
                emit_edge(
                    bridge_node_id, causal.source, "bridges",
                    confidence="EXTRACTED", confidence_score=1.0,
                    role="cause",
                    estimand=bridge.estimand,
                )
                emit_edge(
                    bridge_node_id, causal.target, "bridges",
                    confidence="EXTRACTED", confidence_score=1.0,
                    role="effect",
                    estimand=bridge.estimand,
                )

    # ---- Models ----
    for model in prog.models:
        model_id = model.id
        emit_node(
            model_id, f"Model: {model.id}",
            file_type="concept",
            node_type="model",
        )
        # Contains edges (only to entities that exist as nodes)
        for attr_id in model.attributes:
            if attr_id in all_ids:
                emit_edge(model_id, attr_id, "contains", confidence="EXTRACTED")
        for concept_id in model.concepts:
            if concept_id in all_ids:
                emit_edge(model_id, concept_id, "contains", confidence="EXTRACTED")
        for bridge_id in model.bridges:
            if bridge_id in all_ids:
                emit_edge(model_id, bridge_id, "contains", confidence="EXTRACTED")

    # ---- Checks and Derives (metadata, not graph nodes) ----
    checks = [
        {"fact": ch.fact_name, "model": ch.model_id}
        for ch in prog.checks
    ]
    derives = [
        {"what": d.what, "model": d.model_id}
        for d in prog.derives
    ]

    result = {
        "nodes": nodes,
        "edges": edges,
        "hyperedges": [],
    }
    if checks:
        result["checks"] = checks
    if derives:
        result["derives"] = derives

    return result


def _find_causal(prog: Program, causal_id: str) -> CausalNode | None:
    """Find a causal edge by ID."""
    for c in prog.causals:
        if c.id == causal_id:
            return c
    return None


def _conf_to_score(confidence: str) -> float:
    """Map EXTRACTED/INFERRED/AMBIGUOUS to numeric score."""
    return {"EXTRACTED": 1.0, "INFERRED": 0.8, "AMBIGUOUS": 0.3}.get(
        confidence, 0.5
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 aiss_compiler.py <file.aiss>", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]
    prog = parse_file(filepath)
    graph = compile_to_graphify(prog, source_file=filepath)

    json.dump(graph, sys.stdout, indent=2, ensure_ascii=False, default=str)


if __name__ == "__main__":
    main()
