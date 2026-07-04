#!/usr/bin/env python3
"""Validate literature-to-theory synthesis CSV handoffs."""

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
    is_vague,
    load_rows,
    parse_semicolon_list,
    sidecar_fields,
)
from ai4ss_factory_contracts.workflow import route_enum_error


EXPECTED_FIELDS = sidecar_fields("literature_theory_synthesis")
ALLOWED_SYNTHESIS_TYPES = {
    "concept_cluster",
    "mechanism",
    "boundary_condition",
    "rival_explanation",
    "observable_implication",
    "measurement_link",
    "scope_condition",
}
ALLOWED_EVIDENCE_STRENGTH = {"strong", "mixed", "thin", "conflicting", "unverified"}
VERIFIED_STATUS_MARKERS = {"verified_primary", "verified_local"}


def row_id(row: dict[str, str], index: int) -> str:
    return row.get("synthesis_id") or f"row-{index + 1}"


def has_verified_source(status_summary: str) -> bool:
    normalized = status_summary.lower()
    return any(marker in normalized for marker in VERIFIED_STATUS_MARKERS)


def find_literature_matrix(csv_path: Path, explicit: Path | None) -> Path | None:
    if explicit is not None:
        return explicit
    candidates = [
        csv_path.parent / "literature_matrix.csv",
        csv_path.parent / "valid_literature_matrix.csv",
        Path.cwd() / "docs" / "literature_matrix.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def load_matrix_index(matrix_path: Path | None) -> tuple[dict[str, str], str | None]:
    if matrix_path is None:
        return {}, None
    try:
        fields, rows = load_rows(matrix_path)
    except CSV_LOAD_EXCEPTIONS as exc:
        return {}, f"{matrix_path}: {exc}"
    required = {"paper_id", "verification_level"}
    missing = sorted(required - set(fields))
    if missing:
        return {}, f"{matrix_path}: missing columns: {', '.join(missing)}"
    return {row["paper_id"]: row["verification_level"] for row in rows}, None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--literature-matrix", type=Path)
    args = parser.parse_args()

    try:
        fields, rows = load_rows(args.csv_path)
    except CSV_LOAD_EXCEPTIONS as exc:
        return fail(f"{args.csv_path}: {exc}")

    matrix_index, matrix_error = load_matrix_index(find_literature_matrix(args.csv_path, args.literature_matrix))
    if matrix_error:
        return fail(matrix_error)

    if error := exact_field_error(args.csv_path, fields, EXPECTED_FIELDS):
        return fail(error)

    blank_required = blank_required_cells(rows, EXPECTED_FIELDS, row_id)
    if blank_required:
        return fail(f"{args.csv_path}: blank required cells: {', '.join(blank_required[:10])}")

    duplicates = duplicate_values(rows, "synthesis_id")
    if duplicates:
        return fail(f"{args.csv_path}: duplicate synthesis_id values: {', '.join(duplicates[:10])}")

    enum_errors: list[str] = []
    logic_errors: list[str] = []
    for i, row in enumerate(rows):
        rid = row_id(row, i)
        synthesis_type = row["synthesis_type"]
        evidence_strength = row["evidence_strength"]
        next_route = row["next_skill_route"]
        source_ids = parse_semicolon_list(row["source_paper_ids"])
        proposed_object = row["proposed_aiss_object"]
        model_handoff = not proposed_object.startswith("not_applicable:")

        if synthesis_type not in ALLOWED_SYNTHESIS_TYPES:
            enum_errors.append(f"{rid}:synthesis_type={synthesis_type}")
        if evidence_strength not in ALLOWED_EVIDENCE_STRENGTH:
            enum_errors.append(f"{rid}:evidence_strength={evidence_strength}")
        if error := route_enum_error("literature_theory_synthesis", rid, next_route):
            enum_errors.append(error)

        for column in ("design_source", "target_inquiry"):
            if is_vague(row[column]):
                logic_errors.append(f"{rid}: {column} must bind theory synthesis to a declared design")
        if not source_ids:
            logic_errors.append(f"{rid}: source_paper_ids must name semicolon-separated literature_matrix paper_id values")
        if matrix_index:
            missing_sources = sorted(source_id for source_id in source_ids if source_id not in matrix_index)
            if missing_sources:
                logic_errors.append(f"{rid}: source_paper_ids not found in literature matrix: {', '.join(missing_sources)}")
        if is_vague(row["theory_candidate"], min_len=12):
            logic_errors.append(f"{rid}: theory_candidate is too vague for theory handoff")
        if is_vague(row["observable_implication"], min_len=12):
            logic_errors.append(f"{rid}: observable_implication is too vague")
        if is_vague(row["author_decision_needed"], min_len=12):
            logic_errors.append(f"{rid}: author_decision_needed must preserve researcher judgment")
        if is_vague(row["rival_or_boundary"], min_len=12) and not row["rival_or_boundary"].startswith("not_applicable:"):
            logic_errors.append(f"{rid}: rival_or_boundary must state a rival/boundary or not_applicable:<reason>")
        if evidence_strength == "unverified":
            if model_handoff:
                logic_errors.append(f"{rid}: unverified evidence cannot propose a model-linked .aiss object")
            if next_route != "ask_author":
                logic_errors.append(f"{rid}: unverified evidence must route to ask_author")
        if model_handoff:
            if matrix_index:
                verified = all(matrix_index.get(source_id) in VERIFIED_STATUS_MARKERS for source_id in source_ids)
            else:
                verified = has_verified_source(row["source_status_summary"])
            if not verified:
                logic_errors.append(
                    f"{rid}: proposed_aiss_object requires verified_primary or verified_local source status"
                )
            if next_route != "study-design-builder":
                logic_errors.append(f"{rid}: model-linked theory synthesis must route to study-design-builder")
        elif next_route == "study-design-builder":
            logic_errors.append(f"{rid}: study-design-builder handoff requires proposed_aiss_object")

    if enum_errors:
        return fail(f"{args.csv_path}: invalid enum values: {', '.join(enum_errors[:10])}")
    if logic_errors:
        return fail(f"{args.csv_path}: theory synthesis logic errors: {', '.join(logic_errors[:10])}")

    print(f"PASS {args.csv_path}: {len(rows)} literature-theory synthesis rows valid")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
