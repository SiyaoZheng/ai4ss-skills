#!/usr/bin/env python3
"""Validate study-design-builder decision-register CSV sidecars."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from ai4ss_factory_contracts.sidecars import (
    CSV_LOAD_EXCEPTIONS,
    blank_required_cells,
    duplicate_values,
    exact_field_error,
    fail,
    is_aiss_id,
    load_rows,
    sidecar_fields,
)
from ai4ss_factory_contracts.workflow import MIDA_COMPONENTS, route_enum_error, status_route_errors

EXPECTED_FIELDS = sidecar_fields("design_decisions")

ALLOWED_MIDA_COMPONENTS = MIDA_COMPONENTS
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


def row_id(row: dict[str, str], index: int) -> str:
    return row.get("decision_id") or f"row-{index + 1}"


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

    duplicates = duplicate_values(rows, "decision_id")
    if duplicates:
        return fail(f"{args.csv_path}: duplicate decision_id values: {', '.join(duplicates[:10])}")
    duplicate_decision_decl_ids = duplicate_values(rows, "decision_decl_id")
    if duplicate_decision_decl_ids:
        return fail(
            f"{args.csv_path}: duplicate decision_decl_id values: {', '.join(duplicate_decision_decl_ids[:10])}"
        )

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
        if error := route_enum_error(
            "design_decisions",
            rid,
            row["downstream_skill_route"],
            field="downstream_skill_route",
        ):
            enum_errors.append(error)

        if not is_aiss_id(row["decision_decl_id"]):
            logic_errors.append(f"{rid}: decision_decl_id must be a stable .aiss decision declaration id")
        logic_errors.extend(
            status_route_errors(
                "design_decisions",
                row["status"],
                row["downstream_skill_route"],
                rid,
                field="downstream_skill_route",
            )
        )
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
