#!/usr/bin/env python3
"""Validate analysis-readiness gate CSV sidecars."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


EXPECTED_FIELDS = [
    "check_id",
    "route_id",
    "design_source",
    "target_inquiry",
    "ai4ss_model_path",
    "model_id",
    "bridge_id",
    "analysis_plan_path",
    "data_source",
    "unit_of_analysis",
    "required_variables",
    "available_variables",
    "missing_variables",
    "sample_flow_path",
    "merge_audit_path",
    "variable_provenance_path",
    "row_count",
    "unit_count",
    "time_coverage",
    "key_integrity_status",
    "missingness_status",
    "variation_status",
    "bridge_alignment_status",
    "readiness_status",
    "blocking_issue",
    "validation_command",
    "next_skill_route",
]

ALLOWED_GATE_STATUS = {"pass", "warn", "fail", "not_applicable"}
ALLOWED_BRIDGE_STATUS = {"strong", "weak", "mixed", "unchecked", "fail", "not_applicable"}
ALLOWED_READINESS_STATUS = {"ready", "warn", "blocked"}
ALLOWED_ROUTES = {
    "research-analysis-runner",
    "research-data-builder",
    "study-design-builder",
    "methods-reviewer",
    "ask_author",
}
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
    return row.get("check_id") or f"row-{index + 1}"


def parse_list(value: str) -> list[str]:
    if value.strip().lower() in {"", "none", "not_applicable"}:
        return []
    if value.startswith("not_applicable:"):
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


def is_vague(value: str) -> bool:
    value = value.strip()
    return value.lower() in VAGUE_VALUES or len(value) < 4


def parse_nonnegative_int(value: str, field: str, rid: str) -> tuple[int | None, str | None]:
    if value.startswith("not_applicable:") and field == "unit_count":
        return None, None
    try:
        parsed = int(value)
    except ValueError:
        return None, f"{rid}:{field} must be a nonnegative integer"
    if parsed < 0:
        return None, f"{rid}:{field} must be a nonnegative integer"
    return parsed, None


def resolve_existing_path(path_text: str, csv_path: Path, repo_root: Path) -> Path | None:
    if path_text.startswith("not_applicable:"):
        return None
    raw = Path(path_text)
    candidates = [raw]
    if not raw.is_absolute():
        candidates = [Path.cwd() / raw, repo_root / raw, csv_path.parent / raw]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def inspect_csv_data(path: Path) -> tuple[list[str], int] | None:
    if path.suffix.lower() != ".csv":
        return None
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            return [], 0
        row_count = sum(1 for row in reader if any(cell.strip() for cell in row))
        return [cell.strip() for cell in header], row_count


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

    ids = [row["check_id"] for row in rows]
    duplicates = sorted({check_id for check_id in ids if ids.count(check_id) > 1})
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
        if row["next_skill_route"] not in ALLOWED_ROUTES:
            enum_errors.append(f"{rid}:next_skill_route={row['next_skill_route']}")

        row_count, row_count_error = parse_nonnegative_int(row["row_count"], "row_count", rid)
        if row_count_error:
            logic_errors.append(row_count_error)
        _, unit_count_error = parse_nonnegative_int(row["unit_count"], "unit_count", rid)
        if unit_count_error:
            logic_errors.append(unit_count_error)

        if is_vague(row["target_inquiry"]):
            logic_errors.append(f"{rid}: target_inquiry must bind check to a declared design")
        if is_vague(row["unit_of_analysis"]):
            logic_errors.append(f"{rid}: unit_of_analysis must be concrete")
        if row["ai4ss_model_path"].startswith("not_applicable:"):
            pass
        elif not row["ai4ss_model_path"].endswith(".aiss"):
            logic_errors.append(f"{rid}: ai4ss_model_path must end with .aiss")

        required_variables = set(parse_list(row["required_variables"]))
        available_variables = set(parse_list(row["available_variables"]))
        missing_variables = set(parse_list(row["missing_variables"]))
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
            if row["next_skill_route"] != "research-analysis-runner":
                logic_errors.append(f"{rid}: ready rows must route to research-analysis-runner")
            if row["blocking_issue"].lower() != "none":
                logic_errors.append(f"{rid}: ready rows require blocking_issue=none")
            if "warn" in gate_values:
                logic_errors.append(f"{rid}: ready rows cannot contain warn gate statuses")
            if row["bridge_alignment_status"] in {"unchecked", "fail"}:
                logic_errors.append(f"{rid}: ready rows require checked bridge alignment")
        if row["readiness_status"] == "warn":
            if row["next_skill_route"] not in {"research-analysis-runner", "methods-reviewer"}:
                logic_errors.append(f"{rid}: warn rows must route to analysis or methods review")
            if row["blocking_issue"].lower() == "none":
                logic_errors.append(f"{rid}: warn rows require an explicit warning in blocking_issue")
            if row["bridge_alignment_status"] in {"unchecked", "fail"}:
                logic_errors.append(f"{rid}: warn rows require checked bridge alignment")
        if row["readiness_status"] == "blocked":
            if row["next_skill_route"] == "research-analysis-runner":
                logic_errors.append(f"{rid}: blocked rows cannot route to research-analysis-runner")
            if row["blocking_issue"].lower() == "none":
                logic_errors.append(f"{rid}: blocked rows require a concrete blocking_issue")
            if not row["validation_command"].startswith("not_run_reason:") and "fail" in gate_values:
                logic_errors.append(f"{rid}: blocked fail rows require validation_command=not_run_reason:<reason>")

        data_path = resolve_existing_path(row["data_source"], args.csv_path, args.repo_root)
        if data_path:
            try:
                data_shape = inspect_csv_data(data_path)
            except (OSError, UnicodeDecodeError, csv.Error) as exc:
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
