#!/usr/bin/env python3
"""Conformance smoke tests for the unified AISS v0.4 DSL toolchain."""

from __future__ import annotations

from pathlib import Path

from aiss_unified import (
    canonical_json,
    compile_file,
    compile_program,
    compute_machine_state,
    lint_ast,
    parse_source,
    run_ast,
    transition_machine,
)
from compile_evidence import compile_to_aiss, parse_evidence_table


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
MODEL_FIXTURE = REPO / "docs" / "examples" / "research_model.aiss"
EVIDENCE_FIXTURE = ROOT / "test_fixtures" / "ding_evidence.md"


def main() -> None:
    model_ast = compile_file(MODEL_FIXTURE, strict=True)
    assert model_ast["schema"] == "aiss.unified_ast.v0.4"
    assert model_ast["workflow"]["routes"][0]["id"] == "demo.route_r1"
    assert model_ast["workflow"]["mida"]

    lint_report = lint_ast(model_ast, strict=True)
    assert lint_report["ok"], canonical_json(lint_report)

    run_report = run_ast(model_ast)
    assert run_report["workflow_diagnostics"]["selected_routes"] == ["demo.route_r1"]
    assert run_report["machine_state"]["next_skill_route"] == "public-data-sources"
    assert run_report["model_diagnostics"]["diagnosands"]
    assert run_report["model_diagnostics"]["ibe_profiles"][0]["coverage"] == 1.0

    machine_state = compute_machine_state(model_ast)
    assert machine_state["schema"] == "aiss.machine_state.v0.4"
    assert machine_state["selected_route"] == "demo.route_r1"
    assert machine_state["phase"] == "repair_required"
    assert machine_state["actions"][0]["type"] == "dispatch_skill"

    transition = transition_machine(
        model_ast,
        {
            "type": "skill_completed",
            "at": "2026-07-05T00:00:00Z",
            "skill": "public-data-sources",
            "next_skill_route": "research-data-builder",
        },
        now="2026-07-05T00:00:00Z",
    )
    assert transition["schema"] == "aiss.transition_report.v0.4"
    assert transition["event"]["route"] == "demo.route_r1"
    assert transition["after"]["next_skill_route"] == "research-data-builder"

    event_source = MODEL_FIXTURE.read_text(encoding="utf-8") + """

event demo.event_heartbeat_seen {
  type: "heartbeat_seen"
  at: "2026-07-05T00:00:00Z"
  route: "demo.route_r1"
  skill: "public-data-sources"
  phase: "public-data-sources_running"
  source: "goal-cli"
}
"""
    event_ast = compile_program(parse_source(event_source, "<event-fixture>"), strict=True)
    event_lint = lint_ast(event_ast, strict=True)
    assert event_lint["ok"], canonical_json(event_lint)
    event_state = compute_machine_state(event_ast, now="2026-07-05T00:05:00Z")
    assert event_state["phase"] == "skill_running"
    assert event_state["watchdog"]["status"] == "fresh"

    evidence = parse_evidence_table(EVIDENCE_FIXTURE.read_text(encoding="utf-8"))
    generated_source = compile_to_aiss(evidence)
    generated_ast = compile_program(parse_source(generated_source, "<generated>"))
    generated_lint = lint_ast(generated_ast)
    assert generated_ast["schema"] == "aiss.unified_ast.v0.4"
    assert generated_lint["ok"], canonical_json(generated_lint)


if __name__ == "__main__":
    main()
