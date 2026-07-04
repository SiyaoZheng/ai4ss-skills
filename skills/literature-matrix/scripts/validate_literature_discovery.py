#!/usr/bin/env python3
"""Validate candidate-discovery CSVs before literature extraction."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


EXPECTED_FIELDS = [
    "route_id",
    "design_source",
    "target_inquiry",
    "candidate_id",
    "search_stratum",
    "query_or_seed",
    "title",
    "authors",
    "year",
    "source_type",
    "source_url_or_path",
    "source_status",
    "reason",
    "next_action",
    "relevance_axis",
    "found_from",
    "access_date",
]

ALLOWED_STRATA = {
    "concept",
    "method",
    "outcome",
    "setting",
    "anchor_author",
    "backward_chase",
    "forward_chase",
    "database_refresh",
}
ALLOWED_SOURCE_TYPES = {
    "journal_page",
    "doi_record",
    "working_paper_repository",
    "author_page",
    "local_pdf",
    "citation_index",
    "policy_report",
    "secondary_pointer",
}
ALLOWED_STATUS = {
    "ready_for_extraction",
    "needs_primary_source",
    "needs_pdf",
    "needs_version_check",
    "background_only",
    "duplicate_candidate",
    "excluded",
    "unverified",
}
ALLOWED_NEXT_ACTION = {
    "retrieve_pdf",
    "open_primary_page",
    "check_doi",
    "deduplicate",
    "extract_matrix_row",
    "exclude",
    "ask_author",
}
ALLOWED_RELEVANCE = {
    "firm_innovation",
    "public_sector_productivity",
    "digital_government",
    "ai_adoption",
    "concept",
    "mechanism",
    "boundary_condition",
    "rival_explanation",
    "observable_implication",
    "method_anchor",
    "measurement",
    "other",
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
    return row.get("candidate_id") or f"row-{index + 1}"


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

    ids = [row["candidate_id"] for row in rows]
    duplicates = sorted({candidate_id for candidate_id in ids if ids.count(candidate_id) > 1})
    if duplicates:
        return fail(f"{args.csv_path}: duplicate candidate_id values: {', '.join(duplicates[:10])}")

    enum_errors: list[str] = []
    logic_errors: list[str] = []
    for i, row in enumerate(rows):
        rid = row_id(row, i)
        if row["search_stratum"] not in ALLOWED_STRATA:
            enum_errors.append(f"{rid}:search_stratum={row['search_stratum']}")
        if row["source_type"] not in ALLOWED_SOURCE_TYPES:
            enum_errors.append(f"{rid}:source_type={row['source_type']}")
        if row["source_status"] not in ALLOWED_STATUS:
            enum_errors.append(f"{rid}:source_status={row['source_status']}")
        if row["next_action"] not in ALLOWED_NEXT_ACTION:
            enum_errors.append(f"{rid}:next_action={row['next_action']}")
        if row["relevance_axis"] not in ALLOWED_RELEVANCE:
            enum_errors.append(f"{rid}:relevance_axis={row['relevance_axis']}")
        for column in ("design_source", "target_inquiry"):
            if is_vague(row[column]):
                logic_errors.append(f"{rid}: {column} must bind discovery row to a declared design")

        status = row["source_status"]
        action = row["next_action"]
        source_type = row["source_type"]
        if status == "ready_for_extraction" and action != "extract_matrix_row":
            logic_errors.append(f"{rid}: ready_for_extraction requires next_action=extract_matrix_row")
        if status == "excluded" and action != "exclude":
            logic_errors.append(f"{rid}: excluded requires next_action=exclude")
        if source_type in {"citation_index", "secondary_pointer"} and status == "ready_for_extraction":
            logic_errors.append(f"{rid}: citation_index/secondary_pointer cannot be ready_for_extraction")

    strata = {row["search_stratum"] for row in rows}
    if not (strata & {"concept", "outcome"}):
        logic_errors.append("candidate set must include at least one concept or outcome search stratum")
    if not (strata & {"anchor_author", "backward_chase", "forward_chase"}):
        logic_errors.append("candidate set should include an anchor or snowballing stratum")

    if enum_errors:
        return fail(f"{args.csv_path}: invalid enum values: {', '.join(enum_errors[:10])}")
    if logic_errors:
        return fail(f"{args.csv_path}: discovery logic errors: {', '.join(logic_errors[:10])}")

    print(f"PASS {args.csv_path}: {len(rows)} candidate-discovery rows valid")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
