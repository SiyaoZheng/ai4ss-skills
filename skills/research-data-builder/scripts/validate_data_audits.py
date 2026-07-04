#!/usr/bin/env python3
"""Validate research-data-builder audit CSV sidecars."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


EXPECTED_FIELDS = {
    "sample_flow": [
        "route_id",
        "design_source",
        "target_inquiry",
        "step",
        "input_path",
        "output_path",
        "n_before",
        "n_after",
        "units_before",
        "units_after",
        "years_before",
        "years_after",
        "reason",
        "check_status",
        "notes",
        "ai4ss_model_path",
        "model_id",
        "concept_id",
        "causal_id",
        "bridge_id",
        "ai4ss_check_status",
    ],
    "merge_audit": [
        "route_id",
        "design_source",
        "target_inquiry",
        "merge_name",
        "left_path",
        "right_path",
        "keys",
        "left_rows",
        "right_rows",
        "matched_rows",
        "left_only_rows",
        "right_only_rows",
        "duplicate_key_rows",
        "action",
        "review_path",
        "ai4ss_model_path",
        "model_id",
        "concept_id",
        "causal_id",
        "bridge_id",
        "ai4ss_check_status",
    ],
    "variable_provenance": [
        "route_id",
        "design_source",
        "target_inquiry",
        "variable",
        "source_variables",
        "rule",
        "script_path",
        "validation",
        "status",
        "ai4ss_model_path",
        "model_id",
        "concept_id",
        "causal_id",
        "bridge_id",
        "ai4ss_check_status",
    ],
}

NUMERIC = {
    "sample_flow": {"n_before", "n_after", "units_before", "units_after"},
    "merge_audit": {"left_rows", "right_rows", "matched_rows", "left_only_rows", "right_only_rows", "duplicate_key_rows"},
    "variable_provenance": set(),
}
ALLOWED_CHECK_STATUS = {"pass", "warn", "fail"}
ALLOWED_ACTION = {"keep", "drop", "review", "aggregate", "repair"}
ALLOWED_PROVENANCE_STATUS = {"ready", "needs_review", "blocked"}
ALLOWED_AI4SS_CHECK_STATUS = {"pass", "warn", "not_run", "not_applicable"}
VAGUE_VALUES = {"none", "n/a", "not_applicable", "not applicable", "unknown", "tbd"}


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


def row_id(kind: str, row: dict[str, str], index: int) -> str:
    preferred = {
        "sample_flow": "step",
        "merge_audit": "merge_name",
        "variable_provenance": "variable",
    }[kind]
    return row.get(preferred) or f"row-{index + 1}"


def is_nonnegative_integer(value: str) -> bool:
    return value.isdigit()


def is_vague(value: str) -> bool:
    value = value.strip()
    return value.lower() in VAGUE_VALUES or len(value) < 10


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=sorted(EXPECTED_FIELDS))
    parser.add_argument("csv_path", type=Path)
    args = parser.parse_args()

    try:
        fields_list, rows = load_rows(args.csv_path)
    except (OSError, UnicodeDecodeError, csv.Error, ValueError) as exc:
        return fail(f"{args.csv_path}: {exc}")

    expected = EXPECTED_FIELDS[args.kind]
    if fields_list != expected:
        return fail(
            f"{args.csv_path}: expected exact columns {', '.join(expected)}; "
            f"got {', '.join(fields_list)}"
        )

    blank_required = [
        f"{row_id(args.kind, row, i)}:{column}"
        for i, row in enumerate(rows)
        for column in expected
        if not row.get(column)
    ]
    if blank_required:
        return fail(f"{args.csv_path}: blank required cells: {', '.join(blank_required[:10])}")

    numeric_errors = [
        f"{row_id(args.kind, row, i)}:{column}={row[column]}"
        for i, row in enumerate(rows)
        for column in NUMERIC[args.kind]
        if not is_nonnegative_integer(row[column])
    ]
    if numeric_errors:
        return fail(f"{args.csv_path}: count fields must be nonnegative integers: {', '.join(numeric_errors[:10])}")

    enum_errors: list[str] = []
    logic_errors: list[str] = []
    for i, row in enumerate(rows):
        rid = row_id(args.kind, row, i)
        for column in ("design_source", "target_inquiry"):
            if is_vague(row[column]):
                logic_errors.append(f"{rid}: {column} must bind audit row to a declared design")
        if row["ai4ss_check_status"] not in ALLOWED_AI4SS_CHECK_STATUS:
            enum_errors.append(f"{rid}:ai4ss_check_status={row['ai4ss_check_status']}")
        if row["ai4ss_model_path"].startswith("not_applicable:"):
            pass
        elif not row["ai4ss_model_path"].endswith(".aiss"):
            logic_errors.append(f"{rid}: ai4ss_model_path must end with .aiss")
        if args.kind == "sample_flow" and row["check_status"] not in ALLOWED_CHECK_STATUS:
            enum_errors.append(f"{rid}:check_status={row['check_status']}")
        if args.kind == "sample_flow" and row["check_status"] == "fail":
            logic_errors.append(f"{rid}: check_status=fail is not a valid final artifact")
        if args.kind == "merge_audit":
            if row["action"] not in ALLOWED_ACTION:
                enum_errors.append(f"{rid}:action={row['action']}")
            unresolved = sum(int(row[column]) for column in ("left_only_rows", "right_only_rows", "duplicate_key_rows"))
            if unresolved > 0 and row["action"] == "keep":
                logic_errors.append(f"{rid}: unresolved unmatched/duplicate rows cannot use action=keep")
            if unresolved > 0 and row["review_path"].lower().startswith("not_applicable"):
                logic_errors.append(f"{rid}: nonzero unmatched/duplicate rows require review_path")
            if int(row["matched_rows"]) + int(row["left_only_rows"]) + int(row["duplicate_key_rows"]) != int(row["left_rows"]):
                logic_errors.append(f"{rid}: left_rows must equal matched_rows + left_only_rows + duplicate_key_rows")
            if int(row["matched_rows"]) + int(row["right_only_rows"]) + int(row["duplicate_key_rows"]) != int(row["right_rows"]):
                logic_errors.append(f"{rid}: right_rows must equal matched_rows + right_only_rows + duplicate_key_rows")
        if args.kind == "variable_provenance" and row["status"] not in ALLOWED_PROVENANCE_STATUS:
            enum_errors.append(f"{rid}:status={row['status']}")
        if args.kind == "variable_provenance" and row["status"] == "blocked":
            logic_errors.append(f"{rid}: status=blocked is not a valid final artifact")

    if enum_errors:
        return fail(f"{args.csv_path}: invalid enum values: {', '.join(enum_errors[:10])}")
    if logic_errors:
        return fail(f"{args.csv_path}: audit logic errors: {', '.join(logic_errors[:10])}")

    print(f"PASS {args.csv_path}: {len(rows)} {args.kind} rows valid")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
