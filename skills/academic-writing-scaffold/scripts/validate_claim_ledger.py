#!/usr/bin/env python3
"""Validate an academic-writing-scaffold claim ledger CSV sidecar."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


EXPECTED_FIELDS = [
    "claim_id",
    "claim_text_or_slot",
    "claim_type",
    "target_inquiry",
    "evidence_path",
    "support_level",
    "interpretation_boundary",
    "diagnosed_limit",
    "risk",
    "author_action",
    "author_boundary",
    "artifact_kind",
    "ai4ss_model_path",
    "model_id",
    "concept_id",
    "causal_id",
    "bridge_id",
    "ai4ss_check_status",
    "commensurability_status",
]

ALLOWED_CLAIM_TYPE = {
    "design_fact",
    "estimate",
    "diagnostic",
    "literature_fact",
    "interpretation",
    "speculation",
}
ALLOWED_SUPPORT = {"strong", "partial", "weak", "missing"}
ALLOWED_ACTION = {"revise_target", "cite", "soften", "delete", "add_evidence", "decide"}
ALLOWED_BOUNDARY = {"scaffold_only", "author_draft_audit", "needs_author_decision"}
ALLOWED_ARTIFACT_KIND = {"scaffold_only", "author_draft_audit", "decision_prompt"}
ALLOWED_AI4SS_CHECK_STATUS = {"pass", "warn", "not_run", "not_applicable"}
ALLOWED_COMMENSURABILITY_STATUS = {"strong", "weak", "unchecked", "mixed", "not_applicable"}
DISALLOWED_TEXT = {
    "final_prose",
    "final prose",
    "final manuscript prose",
    "final response prose",
    "ai_drafted_paragraph",
    "ai drafted paragraph",
    "polished paragraph",
    "polished prose",
    "replacement wording",
    "replacement_wording",
    "insert into manuscript",
    "ready to paste",
    "paste into manuscript",
    "submission-ready",
    "submission ready",
    "可直接粘贴",
    "可直接使用",
    "直接写入正文",
    "写入manuscript",
    "最终正文",
    "最终段落",
    "论文段落",
    "摘要",
    "结论",
    "审稿回信正文",
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
    return row.get("claim_id") or f"row-{index + 1}"


def is_vague(value: str) -> bool:
    value = value.strip()
    return value.lower() in VAGUE_VALUES or len(value) < 12


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
        if row["claim_type"] not in ALLOWED_CLAIM_TYPE:
            enum_errors.append(f"{rid}:claim_type={row['claim_type']}")
        if row["support_level"] not in ALLOWED_SUPPORT:
            enum_errors.append(f"{rid}:support_level={row['support_level']}")
        if row["author_action"] not in ALLOWED_ACTION:
            enum_errors.append(f"{rid}:author_action={row['author_action']}")
        if row["author_boundary"] not in ALLOWED_BOUNDARY:
            enum_errors.append(f"{rid}:author_boundary={row['author_boundary']}")
        if row["artifact_kind"] not in ALLOWED_ARTIFACT_KIND:
            enum_errors.append(f"{rid}:artifact_kind={row['artifact_kind']}")
        if row["ai4ss_check_status"] not in ALLOWED_AI4SS_CHECK_STATUS:
            enum_errors.append(f"{rid}:ai4ss_check_status={row['ai4ss_check_status']}")
        if row["commensurability_status"] not in ALLOWED_COMMENSURABILITY_STATUS:
            enum_errors.append(f"{rid}:commensurability_status={row['commensurability_status']}")
        if is_vague(row["target_inquiry"]):
            logic_errors.append(f"{rid}: target_inquiry must name the declared inquiry")
        if is_vague(row["interpretation_boundary"]):
            logic_errors.append(f"{rid}: interpretation_boundary must be concrete")
        if is_vague(row["diagnosed_limit"]):
            logic_errors.append(f"{rid}: diagnosed_limit must be concrete")
        if row["ai4ss_model_path"].startswith("not_applicable:"):
            pass
        elif not row["ai4ss_model_path"].endswith(".aiss"):
            logic_errors.append(f"{rid}: ai4ss_model_path must end with .aiss")
    if enum_errors:
        return fail(f"{args.csv_path}: invalid enum values: {', '.join(enum_errors[:10])}")
    if logic_errors:
        return fail(f"{args.csv_path}: claim-ledger logic errors: {', '.join(logic_errors[:10])}")

    bad_rows = [
        row_id(row, i)
        for i, row in enumerate(rows)
        if any(token in " ".join(row.values()).lower() for token in DISALLOWED_TEXT)
    ]
    if bad_rows:
        return fail(f"{args.csv_path}: disallowed authorship markers: {', '.join(bad_rows[:10])}")

    print(f"PASS {args.csv_path}: {len(rows)} claim-ledger rows valid")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
