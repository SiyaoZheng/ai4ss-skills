#!/usr/bin/env python3
"""Validate analysis-readiness gate CSV sidecars."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

from ai4ss_factory_contracts.sidecars import (
    CSV_LOAD_EXCEPTIONS,
    ai4ss_model_path_error,
    blank_required_cells,
    duplicate_values,
    exact_field_error,
    fail,
    inspect_csv_data,
    is_vague,
    load_rows,
    parse_nonnegative_int,
    parse_semicolon_list,
    resolve_existing_path,
    sidecar_fields,
)
from ai4ss_factory_contracts.workflow import route_enum_error, status_route_errors

EXPECTED_FIELDS = sidecar_fields("analysis_readiness")

ALLOWED_GATE_STATUS = {"pass", "warn", "fail", "not_applicable"}
ALLOWED_BRIDGE_STATUS = {"strong", "weak", "mixed", "unchecked", "fail", "not_applicable"}
ALLOWED_READINESS_STATUS = {"ready", "warn", "blocked"}


def row_id(row: dict[str, str], index: int) -> str:
    return row.get("check_id") or f"row-{index + 1}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Base directory for resolving relative data_source paths.",
    )
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

    duplicates = duplicate_values(rows, "check_id")
    if duplicates:
        return fail(f"{args.csv_path}: duplicate check_id values: {', '.join(duplicates[:10])}")

    enum_errors: list[str] = []
    logic_errors: list[str] = []
    for i, row in enumerate(rows):
        rid = row_id(row, i)
        for field in ("key_integrity_status", "missingness_status", "variation_status"):
            if row[field] not in ALLOWED_GATE_STATUS:
                enum_errors.append(f"{rid}:{field}={row[field]}")
        if row["bridge_alignment_status"] not in ALLOWED_BRIDGE_STATUS:
            enum_errors.append(f"{rid}:bridge_alignment_status={row['bridge_alignment_status']}")
        if row["readiness_status"] not in ALLOWED_READINESS_STATUS:
            enum_errors.append(f"{rid}:readiness_status={row['readiness_status']}")
        if error := route_enum_error("analysis_readiness", rid, row["next_skill_route"]):
            enum_errors.append(error)

        row_count, row_count_error = parse_nonnegative_int(row["row_count"], "row_count", rid)
        if row_count_error:
            logic_errors.append(row_count_error)
        _, unit_count_error = parse_nonnegative_int(
            row["unit_count"],
            "unit_count",
            rid,
            allow_not_applicable=True,
        )
        if unit_count_error:
            logic_errors.append(unit_count_error)

        if is_vague(row["target_inquiry"], min_len=4):
            logic_errors.append(f"{rid}: target_inquiry must bind check to a declared design")
        if is_vague(row["unit_of_analysis"], min_len=4):
            logic_errors.append(f"{rid}: unit_of_analysis must be concrete")
        if error := ai4ss_model_path_error(row["ai4ss_model_path"], rid):
            logic_errors.append(error)

        required_variables = set(parse_semicolon_list(row["required_variables"]))
        available_variables = set(parse_semicolon_list(row["available_variables"]))
        missing_variables = set(parse_semicolon_list(row["missing_variables"]))
        if not required_variables:
            logic_errors.append(f"{rid}: required_variables must list at least one analysis variable")
        if missing_variables and row["readiness_status"] in {"ready", "warn"}:
            logic_errors.append(f"{rid}: ready or warn rows cannot have missing_variables")
        if required_variables and available_variables:
            missing_from_declared_available = sorted(required_variables - available_variables)
            if missing_from_declared_available:
                logic_errors.append(
                    f"{rid}: required_variables missing from available_variables: "
                    f"{', '.join(missing_from_declared_available)}"
                )

        gate_values = [row["key_integrity_status"], row["missingness_status"], row["variation_status"]]
        if "fail" in gate_values or row["bridge_alignment_status"] == "fail":
            if row["readiness_status"] != "blocked":
                logic_errors.append(f"{rid}: fail gates require readiness_status=blocked")
        if row["readiness_status"] == "ready":
            logic_errors.extend(status_route_errors("analysis_readiness", "ready", row["next_skill_route"], rid))
            if row["blocking_issue"].lower() != "none":
                logic_errors.append(f"{rid}: ready rows require blocking_issue=none")
            if "warn" in gate_values:
                logic_errors.append(f"{rid}: ready rows cannot contain warn gate statuses")
            if row["bridge_alignment_status"] in {"unchecked", "fail"}:
                logic_errors.append(f"{rid}: ready rows require checked bridge alignment")
        if row["readiness_status"] == "warn":
            logic_errors.extend(status_route_errors("analysis_readiness", "warn", row["next_skill_route"], rid))
            if row["blocking_issue"].lower() == "none":
                logic_errors.append(f"{rid}: warn rows require an explicit warning in blocking_issue")
            if row["bridge_alignment_status"] in {"unchecked", "fail"}:
                logic_errors.append(f"{rid}: warn rows require checked bridge alignment")
        if row["readiness_status"] == "blocked":
            logic_errors.extend(status_route_errors("analysis_readiness", "blocked", row["next_skill_route"], rid))
            if row["blocking_issue"].lower() == "none":
                logic_errors.append(f"{rid}: blocked rows require a concrete blocking_issue")
            if not row["validation_command"].startswith("not_run_reason:") and "fail" in gate_values:
                logic_errors.append(f"{rid}: blocked fail rows require validation_command=not_run_reason:<reason>")

        data_path = resolve_existing_path(row["data_source"], args.csv_path, args.repo_root)
        if data_path:
            try:
                data_shape = inspect_csv_data(data_path)
            except CSV_LOAD_EXCEPTIONS as exc:
                logic_errors.append(f"{rid}: could not inspect data_source {data_path}: {exc}")
                data_shape = None
            if data_shape is not None:
                header, actual_rows = data_shape
                header_set = set(header)
                missing_from_header = sorted(required_variables - header_set)
                if missing_from_header:
                    logic_errors.append(
                        f"{rid}: required_variables missing from data_source header: "
                        f"{', '.join(missing_from_header)}"
                    )
                if row_count is not None and row_count != actual_rows:
                    logic_errors.append(f"{rid}: row_count={row_count} but data_source has {actual_rows} rows")
                if not missing_variables and missing_from_header:
                    logic_errors.append(f"{rid}: missing_variables must name missing header variables")

    if enum_errors:
        return fail(f"{args.csv_path}: invalid enum values: {', '.join(enum_errors[:10])}")
    if logic_errors:
        return fail(f"{args.csv_path}: analysis readiness logic errors: {', '.join(logic_errors[:10])}")

    print(f"PASS {args.csv_path}: {len(rows)} analysis readiness rows valid")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
