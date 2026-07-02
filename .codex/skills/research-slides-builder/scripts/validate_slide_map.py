#!/usr/bin/env python3
"""Validate research-slides-builder slide map CSV sidecar."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


EXPECTED_FIELDS = [
    "slide_id",
    "role",
    "claim",
    "source_artifact",
    "sample_or_scope",
    "uncertainty_or_caveat",
    "privacy_status",
    "visual",
    "interpretation_boundary",
    "risk",
    "action",
]
ALLOWED_ROLE = {
    "title",
    "agenda",
    "motivation",
    "question",
    "data",
    "design",
    "result",
    "mechanism",
    "robustness",
    "limitation",
    "discussion",
    "boundary",
}
ALLOWED_SOURCELESS_ROLES = {"title", "discussion", "agenda"}
ALLOWED_ACTION = {"create", "revise", "split", "delete", "verify"}
ALLOWED_PRIVACY = {"cleared", "redacted", "needs_approval", "do_not_share", "not_applicable"}
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
    return row.get("slide_id") or f"row-{index + 1}"


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
        if row["role"] not in ALLOWED_ROLE:
            enum_errors.append(f"{rid}:role={row['role']}")
        if row["action"] not in ALLOWED_ACTION:
            enum_errors.append(f"{rid}:action={row['action']}")
        if row["privacy_status"] not in ALLOWED_PRIVACY:
            enum_errors.append(f"{rid}:privacy_status={row['privacy_status']}")
        if row["role"] not in ALLOWED_SOURCELESS_ROLES:
            for column in ("sample_or_scope", "uncertainty_or_caveat", "interpretation_boundary"):
                if is_vague(row[column]):
                    logic_errors.append(f"{rid}: {column} must be concrete for evidence slides")
    if enum_errors:
        return fail(f"{args.csv_path}: invalid enum values: {', '.join(enum_errors[:10])}")
    if logic_errors:
        return fail(f"{args.csv_path}: slide-map logic errors: {', '.join(logic_errors[:10])}")

    unsupported = [
        row_id(row, i)
        for i, row in enumerate(rows)
        if row["source_artifact"].lower().startswith("not_applicable") and row["role"] not in ALLOWED_SOURCELESS_ROLES
    ]
    if unsupported:
        return fail(f"{args.csv_path}: non-agenda slides without source artifact: {', '.join(unsupported[:10])}")

    print(f"PASS {args.csv_path}: {len(rows)} slide-map rows valid")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
