#!/usr/bin/env python3
"""v0.4-only conformance tests for the unified AISS toolchain."""

from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys

from aiss_unified import (
    AissError,
    canonical_json,
    compile_file,
    compile_program,
    diff_asts,
    emit_code_manifest,
    lint_ast,
    parse_source,
    render_template,
    run_ast,
)
from compile_evidence import compile_to_aiss, parse_evidence_table


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
FUSED_MODEL = REPO / "docs" / "examples" / "research_model.aiss"
LITERATURE_EVIDENCE_MD = REPO / "skills" / "literature-matrix" / "examples" / "valid_literature_evidence.md"
LITERATURE_EVIDENCE_AISS = REPO / "skills" / "literature-matrix" / "examples" / "valid_literature_evidence.aiss"
LEGACY_SOURCE = 'aiss version "0.3"\n\npaper legacy.paper { title: "Legacy" kind: "article" sources: [] }\n'
CLI = ROOT / "aiss.py"


def assert_raises_aiss_error(source: str, needle: str) -> None:
    try:
        parse_source(source, "<legacy>")
    except AissError as exc:
        assert needle in str(exc), str(exc)
    else:
        raise AssertionError(f"expected AissError containing {needle!r}")


def main() -> None:
    # v0.4 is the only accepted source version for the unified workflow.
    assert_raises_aiss_error(LEGACY_SOURCE, "expected aiss version")

    ast_1 = compile_file(FUSED_MODEL, strict=True)
    ast_2 = compile_file(FUSED_MODEL, strict=True)
    assert canonical_json(ast_1) == canonical_json(ast_2)
    assert ast_1["schema"] == "aiss.unified_ast.v0.4"
    assert ast_1["indices"]["theory"] == [
        "demo.claim_exposure_increases_innovation",
        "demo.exposed_unit",
        "demo.exposure_to_innovation",
        "demo.high_innovation",
        "demo.rel_exposure_to_innovation",
    ]
    assert ast_1["indices"]["model"] == [
        "demo.check_reference_integrity",
        "demo.check_theta_completeness",
        "demo.derive_ibe_profile",
        "demo.innovation_output",
        "demo.platform_exposure",
        "demo.platform_innovation",
    ]
    assert ast_1["indices"]["workflow"] == [
        "demo.decision_r1_identification",
        "demo.mida_r1_answer_strategy",
        "demo.mida_r1_data_strategy",
        "demo.mida_r1_diagnose",
        "demo.mida_r1_inquiry",
        "demo.mida_r1_model",
        "demo.mida_r1_redesign",
        "demo.mida_r1_report_boundary",
        "demo.route_r1",
    ]
    assert ast_1["workflow"]["routes"][0]["status"] == "selected"

    lint_report = lint_ast(ast_1, strict=True)
    assert lint_report["schema"] == "aiss.lint_report.v0.4"
    assert lint_report["ok"], canonical_json(lint_report)

    run_report = run_ast(ast_1)
    assert run_report["schema"] == "aiss.run_report.v0.4"
    assert run_report["workflow_diagnostics"]["selected_routes"] == ["demo.route_r1"]
    assert run_report["workflow_diagnostics"]["route_profiles"][0]["readiness"] == "mida_declared"
    assert run_report["model_diagnostics"]["ibe_profiles"][0]["model_id"] == "demo.platform_innovation"
    assert run_report["coupling_assessments"][0]["status"] == "assessable_via_adapter"
    assert run_report["coupling_assessments"][0]["rule"] == "demo.adapter_design_route_support"

    manifest = emit_code_manifest(ast_1, target="python")
    assert manifest["schema"] == "aiss.code_manifest.v0.4"

    if LITERATURE_EVIDENCE_MD.exists():
        evidence = parse_evidence_table(LITERATURE_EVIDENCE_MD.read_text(encoding="utf-8"))
        generated_source = compile_to_aiss(evidence)
    else:
        generated_source = LITERATURE_EVIDENCE_AISS.read_text(encoding="utf-8")
    generated_ast = compile_file_from_text(generated_source)
    generated_lint = lint_ast(generated_ast)
    assert generated_ast["schema"] == "aiss.unified_ast.v0.4"
    assert generated_lint["ok"], canonical_json(generated_lint)

    diff_report = diff_asts(ast_1, generated_ast)
    assert diff_report["schema"] == "aiss.diff_report.v0.4"
    assert diff_report["operations"]

    template = "# {{ paper.title }}\n\n{% for model in models %}- {{ model.id }}\n{% endfor %}"
    rendered = render_template(ast_1, template)
    assert "City Platform Exposure and Green Innovation" in rendered
    assert "demo.platform_innovation" in rendered

    proc = subprocess.run(
        [sys.executable, str(CLI), "compile", str(FUSED_MODEL), "--strict"],
        check=True,
        capture_output=True,
        text=True,
    )
    cli_ast = json.loads(proc.stdout)
    assert cli_ast["schema"] == "aiss.unified_ast.v0.4"
    assert canonical_json(cli_ast) == canonical_json(ast_1)


def compile_file_from_text(source: str) -> dict:
    return compile_program(parse_source(source, "<generated>"))


if __name__ == "__main__":
    main()
