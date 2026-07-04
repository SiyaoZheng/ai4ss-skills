#!/usr/bin/env python3
"""Validate methods-reviewer issue table CSV sidecar."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


EXPECTED_FIELDS = [
    "route_id",
    "design_source",
    "target_inquiry",
    "mida_component",
    "severity",
    "issue",
    "evidence",
    "why_it_matters",
    "next_action",
    "status",
    "ai4ss_model_path",
    "model_id",
    "concept_id",
    "causal_id",
    "bridge_id",
    "ai4ss_check_status",
    "commensurability_status",
]
ALLOWED_SEVERITY = {"P0", "P1", "P2", "P3"}
ALLOWED_STATUS = {"confirmed_bug", "serious_risk", "reporting_gap", "overclaim", "needs_author", "resolved", "not_an_issue"}
ALLOWED_MIDA_COMPONENT = {
    "model",
    "inquiry",
    "data_strategy",
    "answer_strategy",
    "diagnose",
    "redesign",
    "report",
}
ALLOWED_AI4SS_CHECK_STATUS = {"pass", "warn", "not_run", "not_applicable"}
ALLOWED_COMMENSURABILITY_STATUS = {"strong", "weak", "unchecked", "mixed", "not_applicable"}
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


def is_vague(value: str) -> bool:
    value = value.strip()
    return value.lower() in VAGUE_VALUES or len(value) < 10


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
        f"row-{i + 1}:{column}"
        for i, row in enumerate(rows)
        for column in EXPECTED_FIELDS
        if not row.get(column)
    ]
    if blank_required:
        return fail(f"{args.csv_path}: blank required cells: {', '.join(blank_required[:10])}")

    enum_errors = [
        f"row-{i + 1}:severity={row['severity']}"
        for i, row in enumerate(rows)
        if row["severity"] not in ALLOWED_SEVERITY
    ]
    enum_errors.extend(
        f"row-{i + 1}:status={row['status']}"
        for i, row in enumerate(rows)
        if row["status"] not in ALLOWED_STATUS
    )
    enum_errors.extend(
        f"row-{i + 1}:mida_component={row['mida_component']}"
        for i, row in enumerate(rows)
        if row["mida_component"] not in ALLOWED_MIDA_COMPONENT
    )
    enum_errors.extend(
        f"row-{i + 1}:ai4ss_check_status={row['ai4ss_check_status']}"
        for i, row in enumerate(rows)
        if row["ai4ss_check_status"] not in ALLOWED_AI4SS_CHECK_STATUS
    )
    enum_errors.extend(
        f"row-{i + 1}:commensurability_status={row['commensurability_status']}"
        for i, row in enumerate(rows)
        if row["commensurability_status"] not in ALLOWED_COMMENSURABILITY_STATUS
    )
    if enum_errors:
        return fail(f"{args.csv_path}: invalid enum values: {', '.join(enum_errors[:10])}")

    logic_errors = [
        f"row-{i + 1}:{column} must bind issue to a declared design"
        for i, row in enumerate(rows)
        for column in ("design_source", "target_inquiry")
        if is_vague(row[column])
    ]
    if logic_errors:
        return fail(f"{args.csv_path}: issue-table logic errors: {', '.join(logic_errors[:10])}")

    model_path_errors = [
        f"row-{i + 1}: ai4ss_model_path must end with .aiss"
        for i, row in enumerate(rows)
        if not row["ai4ss_model_path"].startswith("not_applicable:")
        and not row["ai4ss_model_path"].endswith(".aiss")
    ]
    if model_path_errors:
        return fail(f"{args.csv_path}: issue-table logic errors: {', '.join(model_path_errors[:10])}")

    print(f"PASS {args.csv_path}: {len(rows)} methods issue rows valid")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
