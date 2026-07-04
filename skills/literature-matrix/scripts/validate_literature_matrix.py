#!/usr/bin/env python3
"""Validate a literature-matrix CSV sidecar for required evidence fields."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


EXPECTED_FIELDS = [
    "route_id",
    "design_source",
    "target_inquiry",
    "paper_id",
    "citation",
    "authors",
    "year",
    "status",
    "venue_or_series",
    "doi",
    "url",
    "verification_level",
    "research_question",
    "setting_sample",
    "treatment_or_exposure",
    "outcomes",
    "data_sources",
    "identification_strategy",
    "fixed_effects_controls",
    "validation_checks",
    "main_findings",
    "claim_source_section",
    "claim_source_locator",
    "limitations",
    "relevance_to_project",
    "open_questions",
    "verified_from",
    "access_date",
    "version_used",
    "included_in_synthesis",
    "ai4ss_model_path",
    "model_id",
    "concept_id",
    "causal_id",
    "bridge_id",
    "ai4ss_check_status",
    "evidence_table_path",
    "compiled_ai4ss_path",
    "evidence_compile_status",
    "evidence_compile_command",
]

ALLOWED_STATUS = {
    "journal_article",
    "accepted",
    "working_paper",
    "preprint",
    "conference_paper",
    "book_chapter",
    "report",
    "unverified",
}
ALLOWED_VERIFICATION = {"verified_primary", "verified_local", "secondary_only", "unverified"}
ALLOWED_INCLUDED = {"true", "false", "needs_author"}
ALLOWED_CLAIM_SOURCE_SECTION = {
    "abstract_only",
    "introduction",
    "theory",
    "data",
    "methods",
    "table_figure",
    "results",
    "conclusion",
    "appendix",
    "secondary_summary",
}
ALLOWED_AI4SS_CHECK_STATUS = {"pass", "warn", "not_run", "not_applicable"}
ALLOWED_EVIDENCE_COMPILE_STATUS = {"compiled", "needs_review", "blocked", "not_applicable"}
VAGUE_VALUES = {"none", "n/a", "not_applicable", "not applicable", "unknown", "tbd"}


def fail(message: str) -> int:
    print(f"FAIL {message}")
    return 1


def warn(message: str) -> None:
    print(f"WARN {message}")


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
    return row.get("paper_id") or f"row-{index + 1}"


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
        f"{row_id(row, i)}:{column}"
        for i, row in enumerate(rows)
        for column in EXPECTED_FIELDS
        if not row.get(column)
    ]
    if blank_required:
        return fail(f"{args.csv_path}: blank required cells: {', '.join(blank_required[:10])}")

    enum_errors: list[str] = []
    logic_errors: list[str] = []
    for i, row in enumerate(rows):
        rid = row_id(row, i)
        status = row["status"]
        verification = row["verification_level"]
        included = row["included_in_synthesis"].lower()

        if status not in ALLOWED_STATUS:
            enum_errors.append(f"{rid}:status={status}")
        if verification not in ALLOWED_VERIFICATION:
            enum_errors.append(f"{rid}:verification_level={verification}")
        if included not in ALLOWED_INCLUDED:
            enum_errors.append(f"{rid}:included_in_synthesis={row['included_in_synthesis']}")
        if row["claim_source_section"] not in ALLOWED_CLAIM_SOURCE_SECTION:
            enum_errors.append(f"{rid}:claim_source_section={row['claim_source_section']}")
        if row["ai4ss_check_status"] not in ALLOWED_AI4SS_CHECK_STATUS:
            enum_errors.append(f"{rid}:ai4ss_check_status={row['ai4ss_check_status']}")
        if row["evidence_compile_status"] not in ALLOWED_EVIDENCE_COMPILE_STATUS:
            enum_errors.append(f"{rid}:evidence_compile_status={row['evidence_compile_status']}")
        for column in ("design_source", "target_inquiry"):
            if is_vague(row[column]):
                logic_errors.append(f"{rid}: {column} must bind literature row to a declared design")
        if row["ai4ss_model_path"].startswith("not_applicable:"):
            pass
        elif not row["ai4ss_model_path"].endswith(".aiss"):
            logic_errors.append(f"{rid}: ai4ss_model_path must end with .aiss")
        if row["compiled_ai4ss_path"].startswith("not_applicable:"):
            pass
        elif not row["compiled_ai4ss_path"].endswith(".aiss"):
            logic_errors.append(f"{rid}: compiled_ai4ss_path must end with .aiss")
        if status == "unverified" and verification != "unverified":
            logic_errors.append(f"{rid}: status=unverified requires verification_level=unverified")
        if included == "true" and verification in {"secondary_only", "unverified"}:
            logic_errors.append(f"{rid}: secondary_only/unverified row cannot be synthesis-ready")
        if included == "true" and row["claim_source_section"] in {"abstract_only", "secondary_summary"}:
            logic_errors.append(f"{rid}: abstract_only/secondary_summary row cannot be synthesis-ready")
        model_linked = not row["ai4ss_model_path"].startswith("not_applicable:")
        id_linked = any(
            not row[column].startswith("not_applicable:")
            for column in ("model_id", "concept_id", "causal_id", "bridge_id")
        )
        if included == "true" and model_linked and id_linked:
            if row["evidence_compile_status"] == "not_applicable":
                logic_errors.append(f"{rid}: synthesis-ready model-linked row needs evidence compilation or review status")
        if row["evidence_compile_status"] == "compiled":
            if row["evidence_table_path"].startswith("not_applicable:"):
                logic_errors.append(f"{rid}: compiled evidence requires evidence_table_path")
            if row["compiled_ai4ss_path"].startswith("not_applicable:"):
                logic_errors.append(f"{rid}: compiled evidence requires compiled_ai4ss_path")
            if is_vague(row["evidence_compile_command"]):
                logic_errors.append(f"{rid}: compiled evidence requires evidence_compile_command")
        if row["evidence_compile_status"] == "blocked" and included == "true":
            logic_errors.append(f"{rid}: blocked evidence compilation cannot be synthesis-ready")
        if row["evidence_compile_status"] == "not_applicable":
            if not row["evidence_table_path"].startswith("not_applicable:"):
                logic_errors.append(f"{rid}: not_applicable compile status requires evidence_table_path=not_applicable:<reason>")
            if not row["compiled_ai4ss_path"].startswith("not_applicable:"):
                logic_errors.append(f"{rid}: not_applicable compile status requires compiled_ai4ss_path=not_applicable:<reason>")

    if enum_errors:
        return fail(f"{args.csv_path}: invalid enum values: {', '.join(enum_errors[:10])}")
    if logic_errors:
        return fail(f"{args.csv_path}: matrix logic errors: {', '.join(logic_errors[:10])}")
    print(f"PASS {args.csv_path}: {len(rows)} literature-matrix rows valid")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
