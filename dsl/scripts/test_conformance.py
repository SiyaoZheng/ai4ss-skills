#!/usr/bin/env python3
"""Conformance smoke tests for the aiss DSL toolchain."""

from __future__ import annotations

from pathlib import Path

from aiss_bridge import compute_commensurability
from aiss_checker import check_all
from aiss_compiler import compile_to_graphify
from aiss_fca import build_context, concept_extent, concept_is_closed, evaluate_concept
from aiss_parser import Parser, parse_file
from compile_evidence import compile_to_aiss, parse_evidence_table


ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "test_fixtures" / "ding_performative_state.aiss"
EVIDENCE_FIXTURE = ROOT / "test_fixtures" / "ding_evidence.md"


def _concept(prog, concept_id):
    return next(c for c in prog.concepts if c.id == concept_id)


def _edge(graph, source, target, relation):
    return next(
        e for e in graph["edges"]
        if e["source"] == source and e["target"] == target and e["relation"] == relation
    )


def main() -> None:
    prog = parse_file(str(FIXTURE))

    result = check_all(prog, str(FIXTURE))
    assert result.ok, "\n".join(result.errors)

    governance_mode = _concept(prog, "ding.governance_mode")
    assert governance_mode.theta_domain == "categorical"
    assert evaluate_concept(
        governance_mode,
        {
            "ding.state_capacity": "low",
            "ding.public_scrutiny": "high",
        },
        prog,
    ) == "performative"

    ctx = build_context(prog)
    assert len(concept_extent(governance_mode, ctx, prog)) == 4

    performative_governance = _concept(prog, "ding.performative_governance")
    assert performative_governance.theta_domain == "binary"
    assert len(concept_extent(performative_governance, ctx, prog)) == 1
    assert concept_is_closed(performative_governance, ctx, prog)

    graph = compile_to_graphify(prog, str(FIXTURE))
    causal_edge = _edge(
        graph,
        "ding.low_capacity_high_scrutiny",
        "ding.performative_governance",
        "causes",
    )
    assert causal_edge["confidence"] == "EXTRACTED"
    assert "commensurability" not in causal_edge
    assert "evidence" not in causal_edge

    diagnosands = {
        d.causal_id: d for d in compute_commensurability(prog)
    }
    assert diagnosands["ding.lc_hs_to_performative"].declared_commensurability == "weak"
    assert diagnosands["ding.performative_to_perception"].declared_commensurability == "unchecked"

    evidence = parse_evidence_table(EVIDENCE_FIXTURE.read_text(encoding="utf-8"))
    generated = compile_to_aiss(evidence)
    generated_prog = Parser(generated, "<generated>").parse_program()
    generated_result = check_all(generated_prog, "<generated>")
    assert generated_result.ok, "\n".join(generated_result.errors)


if __name__ == "__main__":
    main()
