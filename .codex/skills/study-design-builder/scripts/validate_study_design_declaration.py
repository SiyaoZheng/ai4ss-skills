#!/usr/bin/env python3
"""Validate study-design-builder MIDA declaration CSV sidecars."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path


EXPECTED_FIELDS = [
    "declaration_id",
    "route_id",
    "study_type",
    "mida_component",
    "declaration_text",
    "declaration_source",
    "status",
    "evidence_source",
    "diagnosand_or_gate",
    "redesign_option",
    "interpretation_boundary",
    "author_decision_needed",
    "ai4ss_model_path",
    "model_id",
    "concept_id",
    "causal_id",
    "bridge_id",
    "ai4ss_check_status",
    "commensurability_status",
    "next_skill_route",
]

REQUIRED_COMPONENTS = {
    "model",
    "inquiry",
    "data_strategy",
    "answer_strategy",
    "diagnose",
    "redesign",
    "report_boundary",
}
ALLOWED_STUDY_TYPES = {
    "descriptive",
    "causal",
    "prediction",
    "text_analysis",
    "case_comparison",
    "qualitative",
    "mixed_methods",
    "theory_mapping",
}
ALLOWED_SOURCES = {
    "author_supplied",
    "material_inferred",
    "literature_inferred",
    "agent_proposed",
    "unresolved",
}
ALLOWED_STATUS = {
    "declared",
    "needs_author_decision",
    "needs_data_check",
    "needs_literature_check",
    "needs_methods_review",
    "blocked",
}
ALLOWED_ROUTES = {
    "research-data-builder",
    "literature-matrix",
    "research-analysis-runner",
    "methods-reviewer",
    "did-expert",
    "ask_author",
    "none",
}
ALLOWED_AI4SS_CHECK_STATUS = {"pass", "warn", "fail", "not_run", "not_applicable"}
ALLOWED_COMMENSURABILITY_STATUS = {"strong", "weak", "unchecked", "mixed", "not_applicable"}
VAGUE_VALUES = {"none", "n/a", "not_applicable", "not applicable", "unknown", "tbd"}
DATA_TERMS = re.compile(r"source|sample|sampling|measure|measurement|extract|link|merge|missing|corpus|data", re.I)
ANSWER_TERMS = re.compile(r"estimate|estimator|model|regression|code|coding|classif|synthesis|table|figure|compare|diagnostic|process", re.I)
CAUSAL_TERMS = re.compile(r"effect|estimand|comparison|outcome|treatment|exposure|population|unit|time|scale|对|影响|处理|结果", re.I)


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
        if any(not field for field in fields):
            raise ValueError("blank header cell")
        duplicates = sorted({field for field in fields if fields.count(field) > 1})
        if duplicates:
            raise ValueError(f"duplicate columns: {', '.join(duplicates)}")
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


def row_id(row: dict[str, str], index: int) -> str:
    return row.get("declaration_id") or f"row-{index + 1}"


def is_vague(value: str) -> bool:
    return value.strip().lower() in VAGUE_VALUES or len(value.strip()) < 12


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    args = parser.parse_args()

    try:
        fields, rows = load_rows(args.csv_path)
    except (OSError, UnicodeDecodeError, csv.Error, ValueError) as exc:
        return fail(f"{args.csv_path}: {exc}")

    if fields != EXPECTED_FIELDS:
        return fail(
            f"{args.csv_path}: expected exact columns {', '.join(EXPECTED_FIELDS)}; got {', '.join(fields)}"
        )

    blank_required = [
        f"{row_id(row, i)}:{column}"
        for i, row in enumerate(rows)
        for column in EXPECTED_FIELDS
        if not row.get(column)
    ]
    if blank_required:
        return fail(f"{args.csv_path}: blank required cells: {', '.join(blank_required[:10])}")

    ids = [row["declaration_id"] for row in rows]
    duplicates = sorted({declaration_id for declaration_id in ids if ids.count(declaration_id) > 1})
    if duplicates:
        return fail(f"{args.csv_path}: duplicate declaration_id values: {', '.join(duplicates[:10])}")

    enum_errors: list[str] = []
    logic_errors: list[str] = []
    by_route: dict[str, list[dict[str, str]]] = defaultdict(list)
    study_type_by_route: dict[str, str] = {}

    for i, row in enumerate(rows):
        rid = row_id(row, i)
        by_route[row["route_id"]].append(row)
        if row["route_id"] in study_type_by_route and study_type_by_route[row["route_id"]] != row["study_type"]:
            logic_errors.append(f"{rid}: route_id has mixed study_type values")
        study_type_by_route[row["route_id"]] = row["study_type"]

        if row["study_type"] not in ALLOWED_STUDY_TYPES:
            enum_errors.append(f"{rid}:study_type={row['study_type']}")
        if row["mida_component"] not in REQUIRED_COMPONENTS:
            enum_errors.append(f"{rid}:mida_component={row['mida_component']}")
        if row["declaration_source"] not in ALLOWED_SOURCES:
            enum_errors.append(f"{rid}:declaration_source={row['declaration_source']}")
        if row["status"] not in ALLOWED_STATUS:
            enum_errors.append(f"{rid}:status={row['status']}")
        if row["next_skill_route"] not in ALLOWED_ROUTES:
            enum_errors.append(f"{rid}:next_skill_route={row['next_skill_route']}")
        if row["ai4ss_check_status"] not in ALLOWED_AI4SS_CHECK_STATUS:
            enum_errors.append(f"{rid}:ai4ss_check_status={row['ai4ss_check_status']}")
        if row["commensurability_status"] not in ALLOWED_COMMENSURABILITY_STATUS:
            enum_errors.append(f"{rid}:commensurability_status={row['commensurability_status']}")

        if is_vague(row["declaration_text"]):
            logic_errors.append(f"{rid}: declaration_text is too vague")
        if is_vague(row["interpretation_boundary"]):
            logic_errors.append(f"{rid}: interpretation_boundary is too vague")
        if row["ai4ss_model_path"].startswith("not_applicable:"):
            if row["study_type"] in {"causal", "theory_mapping", "mixed_methods"}:
                logic_errors.append(f"{rid}: {row['study_type']} rows require an ai4ss_model_path or explicit redesign")
        elif not row["ai4ss_model_path"].endswith(".aiss"):
            logic_errors.append(f"{rid}: ai4ss_model_path must end with .aiss")
        if row["ai4ss_check_status"] == "fail":
            logic_errors.append(f"{rid}: ai4ss_check_status=fail is not a valid handoff")
        if row["bridge_id"].lower() not in VAGUE_VALUES and not row["bridge_id"].startswith("not_applicable:"):
            if row["commensurability_status"] in {"not_applicable", "unchecked"}:
                logic_errors.append(f"{rid}: bridge_id requires strong weak or mixed commensurability_status")
        if row["status"] == "needs_author_decision" and row["next_skill_route"] != "ask_author":
            logic_errors.append(f"{rid}: needs_author_decision should route to ask_author")
        if row["status"] == "needs_data_check" and row["next_skill_route"] != "research-data-builder":
            logic_errors.append(f"{rid}: needs_data_check should route to research-data-builder")
        if row["status"] == "needs_literature_check" and row["next_skill_route"] != "literature-matrix":
            logic_errors.append(f"{rid}: needs_literature_check should route to literature-matrix")
        if row["status"] == "needs_methods_review" and row["next_skill_route"] not in {"methods-reviewer", "did-expert"}:
            logic_errors.append(f"{rid}: needs_methods_review should route to methods-reviewer or did-expert")

    for route_id, route_rows in by_route.items():
        components = [row["mida_component"] for row in route_rows]
        missing = sorted(REQUIRED_COMPONENTS - set(components))
        duplicates_components = sorted({component for component in components if components.count(component) > 1})
        if missing:
            logic_errors.append(f"{route_id}: missing MIDA components: {', '.join(missing)}")
        if duplicates_components:
            logic_errors.append(f"{route_id}: duplicate MIDA components: {', '.join(duplicates_components)}")

        rows_by_component = {row["mida_component"]: row for row in route_rows}
        inquiry = rows_by_component.get("inquiry")
        if inquiry and study_type_by_route[route_id] == "causal" and not CAUSAL_TERMS.search(inquiry["declaration_text"]):
            logic_errors.append(f"{route_id}: causal inquiry must state estimand or target comparison details")
        data_strategy = rows_by_component.get("data_strategy")
        if data_strategy and not DATA_TERMS.search(data_strategy["declaration_text"]):
            logic_errors.append(f"{route_id}: data_strategy must name source/sample/measurement/linkage/missingness")
        answer_strategy = rows_by_component.get("answer_strategy")
        if answer_strategy and not ANSWER_TERMS.search(answer_strategy["declaration_text"]):
            logic_errors.append(f"{route_id}: answer_strategy must name estimator/coding/synthesis/output procedure")
        diagnose = rows_by_component.get("diagnose")
        if diagnose and is_vague(diagnose["diagnosand_or_gate"]):
            logic_errors.append(f"{route_id}: diagnose row needs a concrete diagnosand_or_gate")
        redesign = rows_by_component.get("redesign")
        if redesign and is_vague(redesign["redesign_option"]):
            logic_errors.append(f"{route_id}: redesign row needs a concrete redesign_option")

    if enum_errors:
        return fail(f"{args.csv_path}: invalid enum values: {', '.join(enum_errors[:10])}")
    if logic_errors:
        return fail(f"{args.csv_path}: declaration logic errors: {', '.join(logic_errors[:10])}")

    print(f"PASS {args.csv_path}: {len(rows)} MIDA declaration rows valid")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
