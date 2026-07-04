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

EXPECTED_AISS_DECLARATIONS = {
    "research-starter": ("research_model.aiss", "route declarations", "decision declarations"),
    "study-design-builder": (
        "research_model.aiss",
        "selected route",
        "seven mida declarations",
        "decision declarations",
        "model declarations",
        "check declarations",
    ),
    "research-data-builder": (
        "research_model.aiss",
        "data source declarations",
        "artifact declarations",
        "empirical declarations",
        "observation declarations",
        "coupling declarations",
        "bridge declarations",
        "data checks",
    ),
    "literature-matrix": (
        "research_model.aiss",
        "paper declarations",
        "source declarations",
        "span declarations",
        "claim declarations",
        "relation declarations",
        "concept declarations",
        "causal declarations",
        "bridge declarations",
        "source-status checks",
    ),
    "research-analysis-runner": (
        "research_model.aiss",
        "readiness check declarations",
        "analysis artifact declarations",
        "adapter declarations",
        "derive declarations",
        "observation declarations",
        "bounded claim declarations",
    ),
    "methods-reviewer": (
        "research_model.aiss",
        "diagnostic check declarations",
        "redesign decision declarations",
        "claim-support declarations",
    ),
    "academic-writing-scaffold": (
        "research_model.aiss",
        "bounded claim declarations",
        "report-boundary declarations",
        "citation-gap decisions",
        "author decision declarations",
    ),
    "research-slides-builder": (
        "research_model.aiss",
        "presentation artifact declarations",
        "bounded claim declarations",
        "source-link declarations",
        "privacy check declarations",
    ),
    "reviewer-response": (
        "research_model.aiss",
        "reviewer-request decision declarations",
        "affected MIDA links",
        "evidence artifact declarations",
        "response-boundary declarations",
    ),
}

FORBIDDEN_CANONICAL_ARTIFACTS = (
    "sidecar",
    "research_route_cards.csv",
    "study_design_declaration.csv",
    "design_decision_register.csv",
    "sample_flow.csv",
    "merge_audit.csv",
    "variable_provenance.csv",
    "literature_candidate_discovery.csv",
    "literature_matrix.csv",
    "literature_theory_synthesis.csv",
    "theory_rival_map.csv",
    "theory_scope_map.csv",
    "theory_evidence.md",
    "analysis_readiness_check.csv",
    "analysis_run_manifest.csv",
    "issue_table.csv",
    "claim_ledger.csv",
    "slide_map.csv",
    "revision_matrix.csv",
)


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
        if row["foundation_status"] == "grounded" and not components:
            errors.append(f"{skill}: grounded rows need at least one framework component")
        if row["foundation_status"] in {"partial", "watchlist"} and row["remaining_gap"].lower() in {"none", "n/a"}:
            errors.append(f"{skill}: partial/watchlist rows need a concrete remaining_gap")

        searchable = " ".join(row[field] for field in EXPECTED_FIELDS).lower()
        for term in REQUIRED_SPINE_TERMS[skill]:
            if term.lower() not in searchable:
                errors.append(f"{skill}: missing required design-spine term `{term}`")
        for term in EXPECTED_AISS_DECLARATIONS[skill]:
            if term.lower() not in searchable:
                errors.append(f"{skill}: canonical_artifacts missing `{term}`")
        for forbidden in FORBIDDEN_CANONICAL_ARTIFACTS:
            if forbidden.lower() in row["canonical_artifacts"].lower():
                errors.append(f"{skill}: canonical_artifacts uses forbidden legacy workflow artifact `{forbidden}`")

    repo_root = args.csv_path.resolve().parent.parent if args.csv_path.parent.name == "docs" else Path.cwd()
    required_repo_files = (
        repo_root / "scripts" / "validate_ai4ss_model.py",
        repo_root / "dsl" / "scripts" / "aiss.py",
        repo_root / "docs" / "examples" / "research_model.aiss",
    )
    for path in required_repo_files:
        if not path.exists():
            errors.append(f"repo: missing required AI4SS file {path.relative_to(repo_root)}")

    for skill in REQUIRED_SKILLS:
        skill_md = repo_root / "skills" / skill / "SKILL.md"
        if not skill_md.exists():
            errors.append(f"{skill}: missing SKILL.md")
            continue
        text = skill_md.read_text(encoding="utf-8").lower()
        if "research_model.aiss" not in text:
            errors.append(f"{skill}: SKILL.md must reference research_model.aiss")
        for forbidden in FORBIDDEN_CANONICAL_ARTIFACTS:
            if forbidden.lower() in text:
                errors.append(f"{skill}: SKILL.md uses forbidden legacy workflow artifact `{forbidden}`")

    if errors:
        return fail(f"{args.csv_path}: {'; '.join(errors)}")

    print(f"PASS {args.csv_path}: {len(rows)} methodology foundation rows valid")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
