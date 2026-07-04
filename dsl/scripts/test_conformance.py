#!/usr/bin/env python3
"""Conformance smoke tests for the unified AISS v0.4 DSL toolchain."""

from __future__ import annotations

from pathlib import Path

from aiss_unified import canonical_json, compile_file, compile_program, lint_ast, parse_source, run_ast
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
    assert run_report["model_diagnostics"]["diagnosands"]
    assert run_report["model_diagnostics"]["ibe_profiles"][0]["coverage"] == 1.0

    evidence = parse_evidence_table(EVIDENCE_FIXTURE.read_text(encoding="utf-8"))
    generated_source = compile_to_aiss(evidence)
    generated_ast = compile_program(parse_source(generated_source, "<generated>"))
    generated_lint = lint_ast(generated_ast)
    assert generated_ast["schema"] == "aiss.unified_ast.v0.4"
    assert generated_lint["ok"], canonical_json(generated_lint)


if __name__ == "__main__":
    main()
