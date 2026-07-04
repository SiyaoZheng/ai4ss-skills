#!/usr/bin/env python3
"""Validate research-analysis-runner manifest CSV sidecars."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

from ai4ss_factory_contracts.sidecars import (
    AI4SS_CHECK_STATUS,
    CSV_LOAD_EXCEPTIONS,
    ai4ss_model_path_error,
    blank_required_cells,
    duplicate_values,
    exact_field_error,
    fail,
    is_vague,
    load_rows,
    sidecar_fields,
)
from ai4ss_factory_contracts.workflow import route_enum_error, status_route_errors

EXPECTED_FIELDS = sidecar_fields("analysis_manifest")

ALLOWED_OUTPUT_TYPES = {"table", "figure", "model", "coded_data", "log", "diagnostic"}
ALLOWED_READINESS_STATUS = {"ready", "warn", "blocked"}
ALLOWED_STATUS = {"ready_for_review", "needs_review", "warning", "blocked"}
ALLOWED_AI4SS_CHECK_STATUS = AI4SS_CHECK_STATUS

FORBIDDEN_BOUNDARY = {"none", "n/a", "not_applicable", "final claim", "final_claim"}


def row_id(row: dict[str, str], index: int) -> str:
    return row.get("run_id") or f"row-{index + 1}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    args = parser.parse_args()

    try:
        fields, rows = load_rows(args.csv_path)
    except CSV_LOAD_EXCEPTIONS as exc:
        return fail(f"{args.csv_path}: {exc}")

    if error := exact_field_error(args.csv_path, fields, EXPECTED_FIELDS):
        return fail(error)

    blank_required = blank_required_cells(rows, EXPECTED_FIELDS, row_id)
    if blank_required:
        return fail(f"{args.csv_path}: blank required cells: {', '.join(blank_required[:10])}")

    duplicates = duplicate_values(rows, "run_id")
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
        if error := route_enum_error("analysis_manifest", rid, row["next_skill_route"]):
            enum_errors.append(error)
        if row["ai4ss_check_status"] not in ALLOWED_AI4SS_CHECK_STATUS:
            enum_errors.append(f"{rid}:ai4ss_check_status={row['ai4ss_check_status']}")

        if row["status"] == "blocked" and not row["validation_command"].startswith("not_run_reason:"):
            logic_errors.append(f"{rid}: blocked runs require validation_command=not_run_reason:<reason>")
        if row["readiness_status"] == "blocked" and row["status"] != "blocked":
            logic_errors.append(f"{rid}: blocked readiness cannot produce reviewable outputs")
        if row["status"] == "ready_for_review" and row["readiness_status"] == "warn":
            logic_errors.append(f"{rid}: warning readiness can produce needs_review or warning, not ready_for_review")
        logic_errors.extend(status_route_errors("analysis_manifest", row["status"], row["next_skill_route"], rid))
        if is_vague(row["target_inquiry"], min_len=10):
            logic_errors.append(f"{rid}: target_inquiry must bind run to a declared design")
        if not row["readiness_check_path"].endswith("analysis_readiness_check.csv"):
            logic_errors.append(f"{rid}: readiness_check_path must point to analysis_readiness_check.csv")
        if row["interpretation_boundary"].strip().lower() in FORBIDDEN_BOUNDARY:
            logic_errors.append(f"{rid}: interpretation_boundary must be concrete")
        if error := ai4ss_model_path_error(row["ai4ss_model_path"], rid):
            logic_errors.append(error)

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
