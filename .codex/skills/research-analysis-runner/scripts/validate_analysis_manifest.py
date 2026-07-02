#!/usr/bin/env python3
"""Validate research-analysis-runner manifest CSV sidecars."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


EXPECTED_FIELDS = [
    "run_id",
    "route_id",
    "design_source",
    "target_inquiry",
    "data_source",
    "script_path",
    "output_path",
    "output_type",
    "model_or_operation",
    "sample_note",
    "readiness_check_path",
    "readiness_status",
    "status",
    "validation_command",
    "interpretation_boundary",
    "ai4ss_model_path",
    "model_id",
    "concept_id",
    "causal_id",
    "bridge_id",
    "ai4ss_check_status",
    "next_skill_route",
]

ALLOWED_OUTPUT_TYPES = {"table", "figure", "model", "coded_data", "log", "diagnostic"}
ALLOWED_READINESS_STATUS = {"ready", "warn", "blocked"}
ALLOWED_STATUS = {"ready_for_review", "needs_review", "warning", "blocked"}
ALLOWED_ROUTES = {
    "methods-reviewer",
    "academic-writing-scaffold",
    "research-slides-builder",
    "study-design-builder",
    "research-data-builder",
    "ask_author",
    "none",
}
ALLOWED_AI4SS_CHECK_STATUS = {"pass", "warn", "not_run", "not_applicable"}

FORBIDDEN_BOUNDARY = {"none", "n/a", "not_applicable", "final claim", "final_claim"}
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


def row_id(row: dict[str, str], index: int) -> str:
    return row.get("run_id") or f"row-{index + 1}"


def is_vague(value: str) -> bool:
    value = value.strip()
    return value.lower() in VAGUE_VALUES or len(value) < 10


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

    ids = [row["run_id"] for row in rows]
    duplicates = sorted({run_id for run_id in ids if ids.count(run_id) > 1})
    if duplicates:
        return fail(f"{args.csv_path}: duplicate run_id values: {', '.join(duplicates[:10])}")

    enum_errors: list[str] = []
    logic_errors: list[str] = []
    for i, row in enumerate(rows):
        rid = row_id(row, i)
        if row["output_type"] not in ALLOWED_OUTPUT_TYPES:
            enum_errors.append(f"{rid}:output_type={row['output_type']}")
        if row["readiness_status"] not in ALLOWED_READINESS_STATUS:
            enum_errors.append(f"{rid}:readiness_status={row['readiness_status']}")
        if row["status"] not in ALLOWED_STATUS:
            enum_errors.append(f"{rid}:status={row['status']}")
        if row["next_skill_route"] not in ALLOWED_ROUTES:
            enum_errors.append(f"{rid}:next_skill_route={row['next_skill_route']}")
        if row["ai4ss_check_status"] not in ALLOWED_AI4SS_CHECK_STATUS:
            enum_errors.append(f"{rid}:ai4ss_check_status={row['ai4ss_check_status']}")

        if row["status"] == "blocked" and not row["validation_command"].startswith("not_run_reason:"):
            logic_errors.append(f"{rid}: blocked runs require validation_command=not_run_reason:<reason>")
        if row["readiness_status"] == "blocked" and row["status"] != "blocked":
            logic_errors.append(f"{rid}: blocked readiness cannot produce reviewable outputs")
        if row["status"] == "ready_for_review" and row["readiness_status"] == "warn":
            logic_errors.append(f"{rid}: warning readiness can produce needs_review or warning, not ready_for_review")
        if row["status"] in {"ready_for_review", "needs_review"} and row["next_skill_route"] == "none":
            logic_errors.append(f"{rid}: reviewable outputs require a next_skill_route")
        if row["next_skill_route"] == "academic-writing-scaffold" and row["status"] != "ready_for_review":
            logic_errors.append(f"{rid}: writing scaffold requires ready_for_review status")
        if is_vague(row["target_inquiry"]):
            logic_errors.append(f"{rid}: target_inquiry must bind run to a declared design")
        if not row["readiness_check_path"].endswith("analysis_readiness_check.csv"):
            logic_errors.append(f"{rid}: readiness_check_path must point to analysis_readiness_check.csv")
        if row["interpretation_boundary"].strip().lower() in FORBIDDEN_BOUNDARY:
            logic_errors.append(f"{rid}: interpretation_boundary must be concrete")
        if row["ai4ss_model_path"].startswith("not_applicable:"):
            pass
        elif not row["ai4ss_model_path"].endswith(".aiss"):
            logic_errors.append(f"{rid}: ai4ss_model_path must end with .aiss")

    if enum_errors:
        return fail(f"{args.csv_path}: invalid enum values: {', '.join(enum_errors[:10])}")
    if logic_errors:
        return fail(f"{args.csv_path}: analysis manifest logic errors: {', '.join(logic_errors[:10])}")

    print(f"PASS {args.csv_path}: {len(rows)} analysis manifest rows valid")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
