#!/usr/bin/env python3
"""v0.4-only conformance tests for the unified AISS toolchain."""

from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys

from aiss_unified import (
    AissError,
    PAPER_ARTIFACT_SEQUENCE,
    canonical_json,
    compile_file,
    compile_program,
    compute_transition_plan,
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
VALID_RELAY = REPO / "docs" / "evals" / "factory-relay" / "fixtures" / "valid_relay.aiss"
LITERATURE_EVIDENCE = REPO / ".codex" / "skills" / "literature-matrix" / "examples" / "valid_literature_evidence.md"
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
    assert run_report["coupling_assessments"][0]["status"] == "not_assessable"

    transition_plan = compute_transition_plan(ast_1, strict=True)
    assert transition_plan["schema"] == "aiss.transition_plan.v0.4"
    assert "allowed_next_actions" not in transition_plan
    assert transition_plan["current_state"]["workflow_diagnostics"]["selected_routes"] == ["demo.route_r1"]
    assert transition_plan["blocked_reasons"][0]["code"] == "open_workflow_gate"
    assert transition_plan["required_artifacts"]
    assert "last_skill" in {artifact["next_skill_route"] for artifact in transition_plan["required_artifacts"]}
    assert transition_plan["full_paper_goal"]["target_artifact"] == "full_paper.pdf"
    assert not transition_plan["terminal"]
    assert transition_plan["next_paper_artifact"]["artifact_slug"] == "title_research_question"
    assert "full_paper_pdf" in {gap["artifact_slug"] for gap in transition_plan["paper_artifact_gaps"]}

    relay_ast = compile_file(VALID_RELAY, strict=True)
    relay_plan = compute_transition_plan(relay_ast, strict=True)
    assert "allowed_next_actions" not in relay_plan
    relay_routes = {artifact["next_skill_route"] for artifact in relay_plan["required_artifacts"]}
    assert "public-data-sources" in relay_routes
    assert not relay_plan["blocked_reasons"], canonical_json(relay_plan["blocked_reasons"])
    assert relay_plan["next_paper_artifact"]["artifact_slug"] == "title_research_question"

    writing_source = dict(ast_1)
    writing_source["workflow"] = dict(ast_1["workflow"])
    writing_source["workflow"]["routes"] = [
        {**route, "next_skill_route": "academic-writing-scaffold"}
        for route in ast_1["workflow"]["routes"]
    ]
    writing_source["workflow"]["decisions"] = [
        {**decision, "status": "resolved"}
        for decision in ast_1["workflow"]["decisions"]
    ]
    writing_plan = compute_transition_plan(writing_source, strict=True)
    writing_artifact_names = {artifact["name"] for artifact in writing_plan["required_artifacts"]}
    assert "full_paper.pdf" in writing_artifact_names

    blocked_body_source = dict(writing_source)
    blocked_body_source["workflow"] = dict(writing_source["workflow"])
    blocked_body_source["workflow"]["mida"] = [
        {**row, "status": "declared"}
        for row in writing_source["workflow"]["mida"]
    ]
    blocked_body_source["objects"] = [
        record
        for record in writing_source["objects"]
        if record.get("decl_type") != "claim"
    ] + [
        {
            "category": "empirical",
            "decl_type": "artifact",
            "id": f"demo.paper_{slug}",
            "kind": slug,
            "media_type": "text/markdown",
            "uri": f"paper/{slug}.md",
            "checksum": f"sha256:paper-{slug}",
        }
        for slug in (
            "title_research_question",
            "introduction_problem_contribution",
            "theory_literature_section",
            "research_design_section",
            "references_bibliography",
        )
    ]
    blocked_body_plan = compute_transition_plan(blocked_body_source, strict=True)
    assert blocked_body_plan["next_paper_artifact"]["artifact_slug"] == "data_sample_section"
    assert blocked_body_plan["next_paper_artifact"]["status"] == "missing_blocked"
    assert "public-data-sources" in {
        artifact["next_skill_route"]
        for artifact in blocked_body_plan["required_artifacts"]
        if artifact["blocking"]
    }

    complete_paper_source = dict(writing_source)
    complete_paper_source["workflow"] = dict(writing_source["workflow"])
    complete_paper_source["workflow"]["mida"] = [
        {**row, "status": "declared"}
        for row in writing_source["workflow"]["mida"]
    ]
    complete_paper_source["objects"] = list(writing_source["objects"]) + [
        {
            "category": "empirical",
            "decl_type": "artifact",
            "id": f"demo.paper_{item['slug']}",
            "kind": item["slug"],
            "media_type": "application/pdf" if item["slug"] == "full_paper_pdf" else "text/markdown",
            "uri": "output/full_paper.pdf" if item["slug"] == "full_paper_pdf" else f"paper/{item['slug']}.md",
            "checksum": f"sha256:paper-{item['slug']}",
        }
        for item in PAPER_ARTIFACT_SEQUENCE
    ] + [
        {
            "category": "empirical",
            "decl_type": "artifact",
            "id": "demo.public_data_source_route",
            "kind": "source_route",
            "media_type": "text/markdown",
            "uri": "paper/source_route.md",
            "checksum": "sha256:source-route",
        },
        {
            "category": "empirical",
            "decl_type": "artifact",
            "id": "demo.public_data_access_class",
            "kind": "access_class",
            "media_type": "text/markdown",
            "uri": "paper/access_class.md",
            "checksum": "sha256:access-class",
        },
        {
            "category": "empirical",
            "decl_type": "artifact",
            "id": "demo.public_data_source_provenance",
            "kind": "source_provenance",
            "media_type": "text/markdown",
            "uri": "paper/source_provenance.md",
            "checksum": "sha256:source-provenance",
        },
        {
            "category": "empirical",
            "decl_type": "artifact",
            "id": "demo.public_data_cached_source_artifact",
            "kind": "cached_source_artifact",
            "media_type": "application/x-ndjson",
            "uri": "data/raw/source.jsonl",
            "checksum": "sha256:source-jsonl",
        },
        {
            "category": "empirical",
            "decl_type": "artifact",
            "id": "demo.analysis_dataset_csv",
            "kind": "analysis_dataset_csv",
            "media_type": "text/csv",
            "uri": "data/analysis/sample.csv",
            "checksum": "sha256:analysis-csv",
        },
        {
            "category": "empirical",
            "decl_type": "artifact",
            "id": "demo.analysis_dataset_dta",
            "kind": "analysis_dataset_dta",
            "media_type": "application/x-stata",
            "uri": "data/analysis/sample.dta",
            "checksum": "sha256:analysis-dta",
        },
        {
            "category": "empirical",
            "decl_type": "artifact",
            "id": "demo.sample_flow",
            "kind": "sample_flow",
            "media_type": "text/csv",
            "uri": "paper/sample_flow.csv",
            "checksum": "sha256:sample-flow",
        },
        {
            "category": "empirical",
            "decl_type": "artifact",
            "id": "demo.variable_provenance",
            "kind": "variable_provenance",
            "media_type": "text/csv",
            "uri": "paper/variable_provenance.csv",
            "checksum": "sha256:variable-provenance",
        },
        {
            "category": "model",
            "decl_type": "artifact",
            "id": "demo.analysis_readiness",
            "kind": "analysis_readiness",
            "media_type": "text/csv",
            "uri": "output/analysis_readiness.csv",
            "checksum": "sha256:analysis-readiness",
        },
        {
            "category": "model",
            "decl_type": "artifact",
            "id": "demo.analysis_manifest",
            "kind": "analysis_manifest",
            "media_type": "text/csv",
            "uri": "output/analysis_manifest.csv",
            "checksum": "sha256:analysis-manifest",
        },
        {
            "category": "model",
            "decl_type": "artifact",
            "id": "demo.methods_review",
            "kind": "methods_review",
            "media_type": "text/markdown",
            "uri": "paper/methods_review.md",
            "checksum": "sha256:methods-review",
        },
        {
            "category": "model",
            "decl_type": "artifact",
            "id": "demo.figure_bundle",
            "kind": "figure_table_bundle",
            "media_type": "text/markdown",
            "uri": "paper/figures_tables.md",
            "checksum": "sha256:figures-tables",
        },
    ]
    complete_plan = compute_transition_plan(complete_paper_source, strict=True)
    assert complete_plan["terminal"], canonical_json(complete_plan)
    assert complete_plan["full_paper_goal"]["completed"]
    assert complete_plan["paper_artifact_gaps"] == []
    assert complete_plan["next_paper_artifact"] is None
    assert "allowed_next_actions" not in complete_plan
    assert complete_plan["required_artifacts"] == []

    manifest = emit_code_manifest(ast_1, target="python")
    assert manifest["schema"] == "aiss.code_manifest.v0.4"

    evidence = parse_evidence_table(LITERATURE_EVIDENCE.read_text(encoding="utf-8"))
    generated_source = compile_to_aiss(evidence)
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

    proc = subprocess.run(
        [sys.executable, str(CLI), "transition", str(VALID_RELAY), "--strict"],
        check=True,
        capture_output=True,
        text=True,
    )
    cli_transition = json.loads(proc.stdout)
    assert cli_transition["schema"] == "aiss.transition_plan.v0.4"
    assert "allowed_next_actions" not in cli_transition
    assert "public-data-sources" in {artifact["next_skill_route"] for artifact in cli_transition["required_artifacts"]}


def compile_file_from_text(source: str) -> dict:
    return compile_program(parse_source(source, "<generated>"))


if __name__ == "__main__":
    main()
