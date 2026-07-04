#!/usr/bin/env python3
"""Validate methodology foundation matrix for the local AI4SS skillpack."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


EXPECTED_FIELDS = [
    "stage",
    "skill",
    "framework_role",
    "mida_component",
    "declaration_required",
    "diagnosand_or_gate",
    "canonical_artifacts",
    "foundation_status",
    "remaining_gap",
]

REQUIRED_SKILLS = {
    "research-starter",
    "study-design-builder",
    "research-data-builder",
    "literature-matrix",
    "research-analysis-runner",
    "methods-reviewer",
    "academic-writing-scaffold",
    "research-slides-builder",
    "reviewer-response",
}

ALLOWED_STATUS = {"grounded", "partial", "watchlist"}
ALLOWED_COMPONENTS = {
    "Model",
    "Inquiry",
    "Data strategy",
    "Answer strategy",
    "Diagnose",
    "Redesign",
    "Report",
}

REQUIRED_SPINE_TERMS = {
    "research-starter": ("inquiry", "data_strategy", "answer_strategy", "failure_signal"),
    "study-design-builder": ("inquiry", "data_strategy", "answer_strategy", "diagnosands_or_gates"),
    "research-data-builder": ("measurement", "linkage", "provenance"),
    "literature-matrix": ("source_scope", "screening", "synthesis"),
    "research-analysis-runner": ("design_source", "data_source", "interpretation_boundary"),
    "methods-reviewer": ("inquiry", "data_strategy", "answer_strategy", "overclaim"),
    "academic-writing-scaffold": ("support level", "interpretation_boundary", "author_decision"),
    "research-slides-builder": ("source artifact", "privacy", "interpretation_boundary"),
    "reviewer-response": ("MIDA element", "confidentiality", "author decision"),
}

EXPECTED_ARTIFACTS = {
    "research-starter": ("research_route_cards.csv", "research_model.aiss"),
    "study-design-builder": ("study_design_declaration.csv", "design_decision_register.csv", "research_model.aiss"),
    "research-data-builder": ("sample_flow.csv", "merge_audit.csv", "variable_provenance.csv"),
    "literature-matrix": ("literature_candidate_discovery.csv", "literature_matrix.csv", "literature_theory_synthesis.csv"),
    "research-analysis-runner": ("analysis_readiness_check.csv", "analysis_run_manifest.csv"),
    "methods-reviewer": ("issue_table.csv",),
    "academic-writing-scaffold": ("claim_ledger.csv",),
    "research-slides-builder": ("slide_map.csv",),
    "reviewer-response": ("revision_matrix.csv",),
}

SCHEMA_REQUIREMENTS = {
    "research-starter": {
        "references/route-card-schema.md": (
            "route_decl_id",
            "model_scope",
            "candidate_inquiry",
            "possible_data_strategy",
            "possible_answer_strategy",
        ),
        "scripts/validate_research_routes.py": (
            "route_decl_id",
            "model_scope",
            "candidate_inquiry",
            "possible_data_strategy",
            "possible_answer_strategy",
        ),
        "examples/valid_research_route_cards.csv": (
            "route_decl_id",
            "model_scope",
            "candidate_inquiry",
            "possible_data_strategy",
            "possible_answer_strategy",
        ),
    },
    "study-design-builder": {
        "references/design-workflow.md": (
            "theory_mapping",
            "literature_theory_synthesis.csv",
            "theory_rival_map.csv",
            "theory_scope_map.csv",
            "theory_evidence.md",
            "validate_theory_workbench.py",
            "ready_for_aiss",
            "proposed_aiss_object",
            "design_decision_register.csv",
            "decision",
            "concept",
            "causal",
            "bridge",
        ),
        "references/declaration-schema.md": (
            "study_design_declaration.csv",
            "mida_id",
            "mida_component",
            "declaration_text",
            "diagnosand_or_gate",
            "redesign_option",
            "interpretation_boundary",
            "ai4ss_model_path",
            "ai4ss_check_status",
        ),
        "scripts/validate_study_design_declaration.py": (
            "mida_id",
            "mida_component",
            "inquiry",
            "data_strategy",
            "answer_strategy",
            "diagnose",
            "redesign",
            "report_boundary",
            "ai4ss_model_path",
            "ai4ss_check_status",
        ),
        "examples/valid_study_design_declaration.csv": (
            "mida_id",
            "mida_component",
            "declaration_text",
            "diagnosand_or_gate",
            "redesign_option",
            "interpretation_boundary",
            "research_model.aiss",
        ),
        "references/decision-register-schema.md": (
            "decision_decl_id",
            "mida_component",
            "downstream_skill_route",
        ),
        "scripts/validate_design_decisions.py": (
            "decision_decl_id",
            "mida_component",
            "downstream_skill_route",
        ),
        "examples/valid_design_decision_register.csv": (
            "decision_decl_id",
            "mida_component",
            "downstream_skill_route",
        ),
    },
    "research-data-builder": {
        "references/audit-schema.md": ("route_id", "design_source", "target_inquiry", "ai4ss_model_path"),
        "scripts/validate_data_audits.py": ("route_id", "design_source", "target_inquiry", "ai4ss_model_path"),
        "examples/valid_sample_flow.csv": ("route_id", "design_source", "target_inquiry", "research_model.aiss"),
        "examples/valid_merge_audit.csv": ("route_id", "design_source", "target_inquiry", "research_model.aiss"),
        "examples/valid_variable_provenance.csv": ("route_id", "design_source", "target_inquiry", "research_model.aiss"),
    },
    "literature-matrix": {
        "references/candidate-discovery.md": ("route_id", "design_source", "target_inquiry"),
        "references/matrix-schema.md": (
            "route_id",
            "design_source",
            "target_inquiry",
            "evidence_table_path",
            "compiled_ai4ss_path",
            "evidence_compile_status",
        ),
        "references/evidence-compile.md": (
            "compile_evidence.py",
            "evidence_table_path",
            "compiled_ai4ss_path",
            "evidence_compile_status",
        ),
        "references/theory-synthesis.md": (
            "literature_theory_synthesis.csv",
            "theory_rival_map.csv",
            "theory_scope_map.csv",
            "theory_evidence.md",
            "compile_evidence.py",
            "synthesis_type",
            "source_paper_ids",
            "proposed_aiss_object",
            "author_decision_needed",
            "actor:",
            "discriminating_observation",
        ),
        "scripts/validate_literature_discovery.py": ("route_id", "design_source", "target_inquiry"),
        "scripts/validate_literature_matrix.py": (
            "route_id",
            "design_source",
            "target_inquiry",
            "ai4ss_model_path",
            "evidence_table_path",
            "compiled_ai4ss_path",
            "evidence_compile_status",
        ),
        "scripts/validate_literature_evidence_compile.py": (
            "compile_evidence.py",
            "evidence_table_path",
            "compiled_ai4ss_path",
        ),
        "scripts/validate_literature_theory_synthesis.py": (
            "literature_theory_synthesis",
            "synthesis_type",
            "source_paper_ids",
            "proposed_aiss_object",
            "author_decision_needed",
        ),
        "examples/valid_literature_candidate_discovery.csv": ("route_id", "design_source", "target_inquiry"),
        "examples/valid_literature_matrix.csv": (
            "route_id",
            "design_source",
            "target_inquiry",
            "research_model.aiss",
            "evidence_table_path",
            "compiled_ai4ss_path",
            "evidence_compile_status",
        ),
        "examples/valid_literature_theory_synthesis.csv": (
            "route_id",
            "design_source",
            "target_inquiry",
            "synthesis_type",
            "source_paper_ids",
            "proposed_aiss_object",
            "author_decision_needed",
        ),
    },
    "research-analysis-runner": {
        "references/readiness-schema.md": (
            "analysis_readiness_check.csv",
            "analysis_plan_path",
            "required_variables",
            "available_variables",
            "readiness_status",
            "bridge_alignment_status",
            "ai4ss_model_path",
        ),
        "scripts/validate_analysis_readiness.py": (
            "analysis_plan_path",
            "required_variables",
            "available_variables",
            "missing_variables",
            "readiness_status",
            "bridge_alignment_status",
            "ai4ss_model_path",
        ),
        "examples/valid_analysis_readiness_check.csv": (
            "analysis_plan_path",
            "required_variables",
            "available_variables",
            "readiness_status",
            "research_model.aiss",
        ),
        "references/manifest-schema.md": (
            "design_source",
            "target_inquiry",
            "readiness_check_path",
            "readiness_status",
            "interpretation_boundary",
            "ai4ss_model_path",
        ),
        "scripts/validate_analysis_manifest.py": (
            "design_source",
            "target_inquiry",
            "readiness_check_path",
            "readiness_status",
            "interpretation_boundary",
            "ai4ss_model_path",
        ),
        "examples/valid_analysis_run_manifest.csv": (
            "design_source",
            "target_inquiry",
            "readiness_check_path",
            "readiness_status",
            "interpretation_boundary",
            "research_model.aiss",
        ),
    },
    "methods-reviewer": {
        "references/audit-checklist.md": (
            "literature_theory_synthesis.csv",
            "theory_rival_map.csv",
            "theory_scope_map.csv",
            "mechanisms",
            "rival explanation",
            "scope rows",
            "discriminating observable implication",
            "source status",
            "issue table",
        ),
        "references/issue-examples.md": ("route_id", "design_source", "target_inquiry", "mida_component"),
        "scripts/validate_issue_table.py": ("route_id", "design_source", "target_inquiry", "mida_component", "ai4ss_model_path"),
        "examples/valid_issue_table.csv": ("route_id", "design_source", "target_inquiry", "mida_component", "research_model.aiss"),
    },
    "academic-writing-scaffold": {
        "references/author-workbench.md": (
            "theory_workbench.md",
            "literature_theory_synthesis.csv",
            "theory_rival_map.csv",
            "theory_scope_map.csv",
            "final theory prose",
            "author writes",
        ),
        "references/theory_workbench.md": (
            "literature_theory_synthesis.csv",
            "theory_rival_map.csv",
            "theory_scope_map.csv",
            "compile_evidence.py",
            "validate_theory_workbench.py",
            "author must write final prose",
        ),
        "references/claim-audit.md": ("target_inquiry", "interpretation_boundary", "diagnosed_limit"),
        "scripts/validate_claim_ledger.py": ("target_inquiry", "interpretation_boundary", "diagnosed_limit", "ai4ss_model_path"),
        "examples/valid_claim_ledger.csv": ("target_inquiry", "interpretation_boundary", "diagnosed_limit", "research_model.aiss"),
    },
    "research-slides-builder": {
        "references/visual-rules.md": (
            "sample_or_scope",
            "uncertainty_or_caveat",
            "privacy_status",
            "interpretation_boundary",
        ),
        "scripts/validate_slide_map.py": (
            "sample_or_scope",
            "uncertainty_or_caveat",
            "privacy_status",
            "interpretation_boundary",
        ),
        "examples/valid_slide_map.csv": (
            "sample_or_scope",
            "uncertainty_or_caveat",
            "privacy_status",
            "interpretation_boundary",
        ),
    },
    "reviewer-response": {
        "references/revision-matrix.md": ("mida_element_affected",),
        "scripts/validate_revision_matrix.py": ("mida_element_affected",),
        "examples/valid_revision_matrix.csv": ("mida_element_affected",),
    },
}

REPO_REQUIREMENTS = {
    "scripts/validate_theory_workbench.py": (
        "literature_theory_synthesis.csv",
        "theory_rival_map.csv",
        "theory_scope_map.csv",
        "compile_evidence.py",
        "ai4ss_factory_contracts.sidecars",
        "ai4ss_factory_contracts.workflow",
        "ready_for_aiss",
        "author-owned",
    ),
    "dsl/scripts/compile_evidence.py": (
        "Routes",
        "MIDA",
        "Decisions",
        "route",
        "mida",
        "decision",
    ),
}


def fail(message: str) -> int:
    print(f"FAIL {message}")
    return 1


def load_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            raise ValueError("empty file")
        fields = [cell.strip() for cell in header]
        rows: list[dict[str, str]] = []
        for line_no, row in enumerate(reader, start=2):
            if len(row) != len(fields):
                raise ValueError(f"row {line_no}: expected {len(fields)} cells, got {len(row)}")
            if not any(cell.strip() for cell in row):
                raise ValueError(f"row {line_no}: blank data row")
            rows.append({field: row[i].strip() for i, field in enumerate(fields)})
        if not rows:
            raise ValueError("no data rows")
        return fields, rows


def read_schema_enforcement_text(path: Path, repo_root: Path) -> str:
    text = path.read_text(encoding="utf-8-sig").lower()
    contract_paths: list[Path] = []
    if "ai4ss_factory_contracts.sidecars" in text or "sidecar_fields(" in text:
        contract_paths.append(repo_root / "scripts" / "ai4ss_factory_contracts" / "sidecars.py")
    if "ai4ss_factory_contracts.workflow" in text or "route_enum_error" in text or "status_route_errors" in text:
        contract_paths.append(repo_root / "scripts" / "ai4ss_factory_contracts" / "workflow.py")
    for contract_path in contract_paths:
        text += "\n" + contract_path.read_text(encoding="utf-8-sig").lower()
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path, default=Path("docs/methodology_source_matrix.csv"), nargs="?")
    args = parser.parse_args()

    try:
        fields, rows = load_rows(args.csv_path)
    except (OSError, UnicodeDecodeError, csv.Error, ValueError) as exc:
        return fail(f"{args.csv_path}: {exc}")

    if fields != EXPECTED_FIELDS:
        return fail(
            f"{args.csv_path}: expected exact columns {', '.join(EXPECTED_FIELDS)}; got {', '.join(fields)}"
        )

    skills = [row["skill"] for row in rows]
    missing = sorted(REQUIRED_SKILLS - set(skills))
    extra = sorted(set(skills) - REQUIRED_SKILLS)
    duplicates = sorted({skill for skill in skills if skills.count(skill) > 1})
    if missing:
        return fail(f"{args.csv_path}: missing skills: {', '.join(missing)}")
    if extra:
        return fail(f"{args.csv_path}: unexpected skills: {', '.join(extra)}")
    if duplicates:
        return fail(f"{args.csv_path}: duplicate skill rows: {', '.join(duplicates)}")

    errors: list[str] = []
    for row in rows:
        skill = row["skill"]
        for column in EXPECTED_FIELDS:
            if not row[column]:
                errors.append(f"{skill}:{column} is blank")
        if row["foundation_status"] not in ALLOWED_STATUS:
            errors.append(f"{skill}: invalid foundation_status={row['foundation_status']}")
        components = {component.strip() for component in row["mida_component"].split(";")}
        unknown_components = sorted(components - ALLOWED_COMPONENTS)
        if unknown_components:
            errors.append(f"{skill}: unknown mida_component values: {', '.join(unknown_components)}")
        if row["foundation_status"] == "grounded" and len(components) < 1:
            errors.append(f"{skill}: grounded rows need at least one framework component")
        if row["foundation_status"] in {"partial", "watchlist"} and row["remaining_gap"].lower() in {"none", "n/a"}:
            errors.append(f"{skill}: partial/watchlist rows need a concrete remaining_gap")
        searchable = " ".join(row[field] for field in EXPECTED_FIELDS).lower()
        for term in REQUIRED_SPINE_TERMS[skill]:
            if term.lower() not in searchable:
                errors.append(f"{skill}: missing required design-spine term `{term}`")
        for artifact in EXPECTED_ARTIFACTS[skill]:
            if artifact not in row["canonical_artifacts"]:
                errors.append(f"{skill}: canonical_artifacts missing `{artifact}`")

    repo_root = args.csv_path.resolve().parent.parent if args.csv_path.parent.name == "docs" else Path.cwd()
    for skill, required_files in SCHEMA_REQUIREMENTS.items():
        skill_dir = repo_root / ".codex" / "skills" / skill
        for relative_path, required_terms in required_files.items():
            path = skill_dir / relative_path
            if not path.exists():
                errors.append(f"{skill}: missing schema enforcement file {relative_path}")
                continue
            try:
                text = read_schema_enforcement_text(path, repo_root)
            except UnicodeDecodeError as exc:
                errors.append(f"{skill}: cannot read {relative_path}: {exc}")
                continue
            except OSError as exc:
                errors.append(f"{skill}: cannot read schema contract for {relative_path}: {exc}")
                continue
            for term in required_terms:
                if term.lower() not in text:
                    errors.append(f"{skill}: {relative_path} missing `{term}`")

    for relative_path, required_terms in REPO_REQUIREMENTS.items():
        path = repo_root / relative_path
        if not path.exists():
            errors.append(f"repo: missing theory engine contract file {relative_path}")
            continue
        try:
            text = read_schema_enforcement_text(path, repo_root)
        except UnicodeDecodeError as exc:
            errors.append(f"repo: cannot read {relative_path}: {exc}")
            continue
        except OSError as exc:
            errors.append(f"repo: cannot read theory engine contract for {relative_path}: {exc}")
            continue
        for term in required_terms:
            if term.lower() not in text:
                errors.append(f"repo: {relative_path} missing `{term}`")

    if errors:
        return fail(f"{args.csv_path}: {'; '.join(errors)}")

    print(f"PASS {args.csv_path}: {len(rows)} methodology foundation rows valid")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
