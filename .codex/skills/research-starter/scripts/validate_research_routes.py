#!/usr/bin/env python3
"""Validate research-starter route-card CSV sidecars."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


EXPECTED_FIELDS = [
    "route_id",
    "working_title",
    "research_question",
    "phenomenon",
    "model_scope",
    "candidate_inquiry",
    "possible_data_strategy",
    "possible_answer_strategy",
    "study_type",
    "unit_of_analysis",
    "materials_available",
    "materials_gap",
    "first_action",
    "expected_first_output",
    "failure_signal",
    "feasibility_status",
    "stop_reason",
    "researcher_decision_needed",
    "next_skill_route",
]

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
ALLOWED_FEASIBILITY = {
    "try_now",
    "needs_material",
    "needs_author_decision",
    "needs_external_search",
    "not_feasible",
    "handoff_ready",
}
ALLOWED_ROUTES = {
    "study-design-builder",
    "research-data-builder",
    "literature-matrix",
    "methods-reviewer",
    "academic-writing-scaffold",
    "research-slides-builder",
    "reviewer-response",
    "did-expert",
    "ask_author",
    "none",
}
VAGUE_VALUES = {"none", "n/a", "not_applicable", "not applicable", "unknown", "tbd"}
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
    return row.get("route_id") or f"row-{index + 1}"


def contains_forbidden_action(text: str) -> str | None:
    lowered = text.lower()
    for phrase in sorted(FORBIDDEN_ACTION_PHRASES):
        if phrase.lower() in lowered:
            return phrase
    return None


def is_vague(value: str) -> bool:
    return value.strip().lower() in VAGUE_VALUES or len(value.strip()) < 12


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    args = parser.parse_args()

    try:
        fields_list, rows = load_rows(args.csv_path)
    except (OSError, UnicodeDecodeError, csv.Error, ValueError) as exc:
        return fail(f"{args.csv_path}: {exc}")

    if fields_list != EXPECTED_FIELDS:
        return fail(
            f"{args.csv_path}: expected exact columns {', '.join(EXPECTED_FIELDS)}; "
            f"got {', '.join(fields_list)}"
        )

    blank_required = [
        f"{row_id(row, i)}:{column}"
        for i, row in enumerate(rows)
        for column in EXPECTED_FIELDS
        if not row.get(column)
    ]
    if blank_required:
        return fail(f"{args.csv_path}: blank required cells: {', '.join(blank_required[:10])}")

    ids = [row["route_id"] for row in rows]
    duplicates = sorted({route_id for route_id in ids if ids.count(route_id) > 1})
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
        if row["next_skill_route"] not in ALLOWED_ROUTES:
            enum_errors.append(f"{rid}:next_skill_route={row['next_skill_route']}")

        for column in ("model_scope", "candidate_inquiry", "possible_data_strategy", "possible_answer_strategy"):
            if is_vague(row[column]):
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
        if row["feasibility_status"] == "handoff_ready" and row["next_skill_route"] in {"none", "ask_author"}:
            logic_errors.append(f"{rid}: handoff_ready requires a downstream next_skill_route")
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
