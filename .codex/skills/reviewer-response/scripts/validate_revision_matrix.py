#!/usr/bin/env python3
"""Validate reviewer-response revision matrix CSV sidecar."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


EXPECTED_FIELDS = [
    "comment_id",
    "reviewer_text",
    "request_type",
    "mida_element_affected",
    "severity",
    "status",
    "planned_action",
    "evidence_needed",
    "file_or_section",
    "owner",
    "done_evidence",
    "response_summary",
    "author_position_status",
    "confidentiality_status",
    "open_question",
]
ALLOWED_STATUS = {"accept", "partial", "clarify", "rebut", "cannot_do", "needs_author"}
ALLOWED_REQUEST_TYPE = {
    "contribution",
    "conceptual",
    "identification",
    "data",
    "measurement",
    "model",
    "inference",
    "methods",
    "robustness",
    "heterogeneity",
    "literature",
    "writing",
    "formatting",
    "scope",
}
ALLOWED_MIDA_ELEMENT = {
    "model",
    "inquiry",
    "data_strategy",
    "answer_strategy",
    "diagnose",
    "redesign",
    "report",
    "not_applicable",
}
ALLOWED_SEVERITY = {"high", "medium", "low"}
ALLOWED_OWNER = {"author", "agent"}
ALLOWED_AUTHOR_POSITION = {"author_decided", "needs_author", "not_applicable"}
ALLOWED_CONFIDENTIALITY = {"cleared", "redacted", "needs_approval", "do_not_share"}
EXTERNAL_ACTION_MARKERS = {"external", "llm", "model", "upload", "send to", "外部", "上传", "模型"}
AUTHOR_OWNED_MARKERS = {
    "write",
    "rewrite",
    "revise text",
    "manuscript wording",
    "response prose",
    "final prose",
    "cover letter",
    "写正文",
    "改正文",
    "回信正文",
    "最终回信",
}


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
    return row.get("comment_id") or f"row-{index + 1}"


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
        if row["request_type"] not in ALLOWED_REQUEST_TYPE:
            enum_errors.append(f"{rid}:request_type={row['request_type']}")
        if row["mida_element_affected"] not in ALLOWED_MIDA_ELEMENT:
            enum_errors.append(f"{rid}:mida_element_affected={row['mida_element_affected']}")
        if row["severity"] not in ALLOWED_SEVERITY:
            enum_errors.append(f"{rid}:severity={row['severity']}")
        if row["status"] not in ALLOWED_STATUS:
            enum_errors.append(f"{rid}:status={row['status']}")
        if row["owner"] not in ALLOWED_OWNER:
            enum_errors.append(f"{rid}:owner={row['owner']}")
        if row["author_position_status"] not in ALLOWED_AUTHOR_POSITION:
            enum_errors.append(f"{rid}:author_position_status={row['author_position_status']}")
        if row["confidentiality_status"] not in ALLOWED_CONFIDENTIALITY:
            enum_errors.append(f"{rid}:confidentiality_status={row['confidentiality_status']}")

        action_text = " ".join(
            row.get(column, "").lower()
            for column in ("planned_action", "evidence_needed", "file_or_section", "response_summary")
        )
        if row["status"] in {"accept", "partial"} and row["done_evidence"].lower().startswith(("pending", "not_applicable")):
            logic_errors.append(f"{rid}: accept/partial requires completed done_evidence")
        if row["status"] in {"rebut", "cannot_do"} and row["response_summary"].lower() in {"none", "not_applicable"}:
            logic_errors.append(f"{rid}: rebut/cannot_do requires response_summary reason")
        if row["status"] == "needs_author" and row["author_position_status"] != "needs_author":
            logic_errors.append(f"{rid}: needs_author status must use author_position_status=needs_author")
        if row["owner"] == "agent" and row["confidentiality_status"] not in {"cleared", "redacted"}:
            logic_errors.append(f"{rid}: agent-owned work requires confidentiality_status=cleared or redacted")
        if any(marker in action_text for marker in EXTERNAL_ACTION_MARKERS) and row["confidentiality_status"] not in {"cleared", "redacted"}:
            logic_errors.append(f"{rid}: external-tool actions require confidentiality_status=cleared or redacted")
        if row["request_type"] == "writing" and row["owner"] != "author":
            logic_errors.append(f"{rid}: writing rows must use owner=author")
        if row["request_type"] not in {"writing", "formatting"} and row["mida_element_affected"] == "not_applicable":
            logic_errors.append(f"{rid}: substantive requests must name a MIDA element")
        if row["owner"] == "agent" and any(marker in action_text for marker in AUTHOR_OWNED_MARKERS):
            logic_errors.append(f"{rid}: manuscript/response prose actions must be author-owned")

    if enum_errors:
        return fail(f"{args.csv_path}: invalid enum values: {', '.join(enum_errors[:10])}")
    if logic_errors:
        return fail(f"{args.csv_path}: matrix logic errors: {', '.join(logic_errors[:10])}")

    print(f"PASS {args.csv_path}: {len(rows)} revision-matrix rows valid")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
