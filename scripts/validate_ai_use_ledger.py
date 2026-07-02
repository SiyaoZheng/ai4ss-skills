#!/usr/bin/env python3
"""Validate the project AI-use ledger CSV."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


EXPECTED_FIELDS = [
    "tool_model",
    "task",
    "inputs",
    "outputs",
    "human_review",
    "disclosure_location",
    "confidentiality_approval_status",
]
ALLOWED_DISCLOSURE = {
    "manuscript_note",
    "appendix",
    "cover_letter",
    "classroom_note",
    "not_applicable",
}
ALLOWED_CONFIDENTIALITY = {"cleared", "redacted", "needs_approval", "do_not_share"}


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
        f"row-{i + 1}:{column}"
        for i, row in enumerate(rows)
        for column in EXPECTED_FIELDS
        if not row.get(column)
    ]
    if blank_required:
        return fail(f"{args.csv_path}: blank required cells: {', '.join(blank_required[:10])}")

    enum_errors: list[str] = []
    logic_errors: list[str] = []
    for i, row in enumerate(rows):
        rid = f"row-{i + 1}"
        if row["disclosure_location"] not in ALLOWED_DISCLOSURE:
            enum_errors.append(f"{rid}:disclosure_location={row['disclosure_location']}")
        if row["confidentiality_approval_status"] not in ALLOWED_CONFIDENTIALITY:
            enum_errors.append(f"{rid}:confidentiality_approval_status={row['confidentiality_approval_status']}")
        if row["confidentiality_approval_status"] in {"needs_approval", "do_not_share"}:
            logic_errors.append(f"{rid}: artifact is not ready while confidentiality approval is unresolved or denied")
        if row["human_review"].lower().startswith(("none", "not_applicable", "pending")):
            logic_errors.append(f"{rid}: human_review must document completed researcher review")

    if enum_errors:
        return fail(f"{args.csv_path}: invalid enum values: {', '.join(enum_errors[:10])}")
    if logic_errors:
        return fail(f"{args.csv_path}: ledger logic errors: {', '.join(logic_errors[:10])}")

    print(f"PASS {args.csv_path}: {len(rows)} AI-use ledger rows valid")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
