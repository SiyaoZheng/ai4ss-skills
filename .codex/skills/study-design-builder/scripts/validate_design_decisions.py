#!/usr/bin/env python3
"""Validate study-design-builder decision-register CSV sidecars."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


EXPECTED_FIELDS = [
    "decision_id",
    "route_id",
    "mida_component",
    "design_component",
    "current_choice",
    "choice_source",
    "status",
    "evidence_needed",
    "risk_if_wrong",
    "author_decision_needed",
    "downstream_skill_route",
]

ALLOWED_MIDA_COMPONENTS = {
    "model",
    "inquiry",
    "data_strategy",
    "answer_strategy",
    "diagnose",
    "redesign",
    "report_boundary",
}
ALLOWED_SOURCES = {
    "author_supplied",
    "material_inferred",
    "literature_inferred",
    "agent_proposed",
    "unresolved",
}
ALLOWED_STATUS = {
    "proposed",
    "needs_author_decision",
    "needs_data_check",
    "needs_literature_check",
    "ready_for_handoff",
    "rejected",
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
    return row.get("decision_id") or f"row-{index + 1}"


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
            f"{args.csv_path}: expected exact columns {', '.join(EXPECTED_FIELDS)}; "
            f"got {', '.join(fields)}"
        )

    blank_required = [
        f"{row_id(row, i)}:{column}"
        for i, row in enumerate(rows)
        for column in EXPECTED_FIELDS
        if not row.get(column)
    ]
    if blank_required:
        return fail(f"{args.csv_path}: blank required cells: {', '.join(blank_required[:10])}")

    ids = [row["decision_id"] for row in rows]
    duplicates = sorted({decision_id for decision_id in ids if ids.count(decision_id) > 1})
    if duplicates:
        return fail(f"{args.csv_path}: duplicate decision_id values: {', '.join(duplicates[:10])}")

    enum_errors: list[str] = []
    logic_errors: list[str] = []
    for i, row in enumerate(rows):
        rid = row_id(row, i)
        if row["mida_component"] not in ALLOWED_MIDA_COMPONENTS:
            enum_errors.append(f"{rid}:mida_component={row['mida_component']}")
        if row["choice_source"] not in ALLOWED_SOURCES:
            enum_errors.append(f"{rid}:choice_source={row['choice_source']}")
        if row["status"] not in ALLOWED_STATUS:
            enum_errors.append(f"{rid}:status={row['status']}")
        if row["downstream_skill_route"] not in ALLOWED_ROUTES:
            enum_errors.append(f"{rid}:downstream_skill_route={row['downstream_skill_route']}")

        if row["status"] == "ready_for_handoff" and row["downstream_skill_route"] in {"none", "ask_author"}:
            logic_errors.append(f"{rid}: ready_for_handoff requires a downstream skill")
        if row["status"] == "needs_author_decision" and row["downstream_skill_route"] != "ask_author":
            logic_errors.append(f"{rid}: needs_author_decision should route to ask_author")
        if row["status"] == "needs_data_check" and row["downstream_skill_route"] != "research-data-builder":
            logic_errors.append(f"{rid}: needs_data_check should route to research-data-builder")
        if row["status"] == "needs_literature_check" and row["downstream_skill_route"] != "literature-matrix":
            logic_errors.append(f"{rid}: needs_literature_check should route to literature-matrix")
        if row["status"] == "rejected" and len(row["risk_if_wrong"]) < 10:
            logic_errors.append(f"{rid}: rejected decisions need a concrete risk_if_wrong")

    if enum_errors:
        return fail(f"{args.csv_path}: invalid enum values: {', '.join(enum_errors[:10])}")
    if logic_errors:
        return fail(f"{args.csv_path}: decision-register logic errors: {', '.join(logic_errors[:10])}")

    print(f"PASS {args.csv_path}: {len(rows)} design decision rows valid")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
