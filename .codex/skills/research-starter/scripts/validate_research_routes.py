#!/usr/bin/env python3
"""Validate research-starter route-card CSV sidecars."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

from ai4ss_factory_contracts.sidecars import (
    CSV_LOAD_EXCEPTIONS,
    blank_required_cells,
    duplicate_values,
    exact_field_error,
    fail,
    is_aiss_id_or_not_created,
    is_vague,
    load_rows,
    sidecar_fields,
)
from ai4ss_factory_contracts.workflow import STUDY_TYPES, route_enum_error, status_route_errors

EXPECTED_FIELDS = sidecar_fields("research_routes")

ALLOWED_STUDY_TYPES = STUDY_TYPES
ALLOWED_FEASIBILITY = {
    "try_now",
    "needs_material",
    "needs_author_decision",
    "needs_external_search",
    "not_feasible",
    "handoff_ready",
}
DATA_TERMS = re.compile(r"source|sample|sampling|measure|measurement|extract|link|merge|missing|corpus|data", re.I)
ANSWER_TERMS = re.compile(r"estimate|estimator|model|regression|code|coding|classif|synthesis|table|figure|compare|diagnostic|process", re.I)
CAUSAL_TERMS = re.compile(r"effect|estimand|comparison|outcome|treatment|exposure|population|unit|time|scale|对|影响|处理|结果", re.I)
FORBIDDEN_ACTION_PHRASES = {
    "final manuscript",
    "submission-ready",
    "write the paper",
    "write introduction",
    "write literature review",
    "write results prose",
    "polished prose",
    "直接成稿",
    "代写",
    "写完整论文",
    "写引言",
    "写文献综述",
    "写结果段落",
}


def row_id(row: dict[str, str], index: int) -> str:
    return row.get("route_id") or f"row-{index + 1}"


def contains_forbidden_action(text: str) -> str | None:
    lowered = text.lower()
    for phrase in sorted(FORBIDDEN_ACTION_PHRASES):
        if phrase.lower() in lowered:
            return phrase
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    args = parser.parse_args()

    try:
        fields_list, rows = load_rows(args.csv_path)
    except CSV_LOAD_EXCEPTIONS as exc:
        return fail(f"{args.csv_path}: {exc}")

    if error := exact_field_error(args.csv_path, fields_list, EXPECTED_FIELDS):
        return fail(error)

    blank_required = blank_required_cells(rows, EXPECTED_FIELDS, row_id)
    if blank_required:
        return fail(f"{args.csv_path}: blank required cells: {', '.join(blank_required[:10])}")

    duplicates = duplicate_values(rows, "route_id")
    if duplicates:
        return fail(f"{args.csv_path}: duplicate route_id values: {', '.join(duplicates[:10])}")

    enum_errors: list[str] = []
    logic_errors: list[str] = []
    for i, row in enumerate(rows):
        rid = row_id(row, i)
        if row["study_type"] not in ALLOWED_STUDY_TYPES:
            enum_errors.append(f"{rid}:study_type={row['study_type']}")
        if row["feasibility_status"] not in ALLOWED_FEASIBILITY:
            enum_errors.append(f"{rid}:feasibility_status={row['feasibility_status']}")
        if error := route_enum_error("research_routes", rid, row["next_skill_route"]):
            enum_errors.append(error)
        if not is_aiss_id_or_not_created(row["route_decl_id"]):
            logic_errors.append(f"{rid}: route_decl_id must be a stable .aiss route id or not_created:<reason>")

        for column in ("model_scope", "candidate_inquiry", "possible_data_strategy", "possible_answer_strategy"):
            if is_vague(row[column], min_len=12):
                logic_errors.append(f"{rid}: {column} is too vague for a pre-declaration")
        if row["study_type"] == "causal" and not CAUSAL_TERMS.search(row["candidate_inquiry"]):
            logic_errors.append(f"{rid}: causal candidate_inquiry must state estimand or target comparison details")
        if not DATA_TERMS.search(row["possible_data_strategy"]):
            logic_errors.append(f"{rid}: possible_data_strategy must name source/sample/measurement/linkage/missingness")
        if not ANSWER_TERMS.search(row["possible_answer_strategy"]):
            logic_errors.append(f"{rid}: possible_answer_strategy must name estimator/coding/synthesis/output procedure")
        forbidden = contains_forbidden_action(" ".join([row["first_action"], row["expected_first_output"]]))
        if forbidden:
            logic_errors.append(f"{rid}: forbidden final-writing action phrase: {forbidden}")
        logic_errors.extend(
            status_route_errors("research_routes", row["feasibility_status"], row["next_skill_route"], rid)
        )
        if row["next_skill_route"] == "study-design-builder" and row["route_decl_id"].startswith("not_created:"):
            logic_errors.append(f"{rid}: study-design-builder handoff requires a concrete .aiss route declaration")
        if row["feasibility_status"] == "not_feasible" and len(row["failure_signal"]) < 10:
            logic_errors.append(f"{rid}: not_feasible requires a concrete failure_signal")
        if row["stop_reason"].lower() in {"none", "n/a", "not_applicable"}:
            logic_errors.append(f"{rid}: stop_reason must explain why the first loop stops")
        if row["researcher_decision_needed"].lower() in {"none", "n/a", "not_applicable"}:
            logic_errors.append(f"{rid}: researcher_decision_needed cannot be empty or none")

    if len(rows) > 4:
        logic_errors.append("open-ended starter packets should keep route cards to 2-4 routes")
    if not any(row["feasibility_status"] in {"try_now", "handoff_ready"} for row in rows):
        logic_errors.append("at least one route should be try_now or handoff_ready")

    if enum_errors:
        return fail(f"{args.csv_path}: invalid enum values: {', '.join(enum_errors[:10])}")
    if logic_errors:
        return fail(f"{args.csv_path}: route-card logic errors: {', '.join(logic_errors[:10])}")

    print(f"PASS {args.csv_path}: {len(rows)} research route cards valid")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
