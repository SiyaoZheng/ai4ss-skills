#!/usr/bin/env python3
"""Validate reusable theory-workbench handoffs without creating a new DSL."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

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


REQUIRED_FILES = {
    "literature_theory_synthesis": "literature_theory_synthesis.csv",
    "theory_rival_map": "theory_rival_map.csv",
    "theory_scope_map": "theory_scope_map.csv",
}
ALLOWED_WORKBENCH_STATUS = {
    "ready_for_aiss",
    "needs_redesign",
    "needs_methods_review",
    "blocked",
    "not_applicable",
}
GATE_ONLY_TERMS = {
    "novelty",
    "theoretical contribution",
    "contribution",
    "mechanism strength",
    "claim strength",
}
MECHANISM_PARTS = ("actor:", "action:", "mediating_condition:", "outcome_link:")


def row_label(field: str):
    def label(row: dict[str, str], index: int) -> str:
        return row.get(field) or f"row-{index + 1}"

    return label


def load_sidecar(path: Path, sidecar_name: str, id_field: str) -> tuple[list[dict[str, str]], list[str]]:
    errors: list[str] = []
    try:
        fields, rows = load_rows(path)
    except CSV_LOAD_EXCEPTIONS as exc:
        return [], [f"{path}: {exc}"]
    if error := exact_field_error(path, fields, sidecar_fields(sidecar_name)):
        errors.append(error)
    blanks = blank_required_cells(rows, sidecar_fields(sidecar_name), row_label(id_field))
    if blanks:
        errors.append(f"{path}: blank required cells: {', '.join(blanks[:10])}")
    duplicates = duplicate_values(rows, id_field)
    if duplicates:
        errors.append(f"{path}: duplicate {id_field} values: {', '.join(duplicates[:10])}")
    return rows, errors


def run_literature_validator(workbench_dir: Path) -> list[str]:
    lit_path = workbench_dir / REQUIRED_FILES["literature_theory_synthesis"]
    validator = Path("skills/literature-matrix/scripts/validate_literature_theory_synthesis.py")
    command = [sys.executable, str(validator), str(lit_path)]
    matrix_path = workbench_dir / "literature_matrix.csv"
    if matrix_path.exists():
        command.extend(["--literature-matrix", str(matrix_path)])
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    if result.returncode == 0:
        return []
    detail = (result.stdout + result.stderr).strip()
    return [detail or f"{lit_path}: literature theory synthesis validator failed"]


def contains_gate_only_term(row: dict[str, str]) -> bool:
    text = " ".join(row.values()).lower()
    return any(term in text for term in GATE_ONLY_TERMS)


def is_model_linked(aiss_object: str) -> bool:
    return not aiss_object.startswith("not_applicable:")


def validate_mechanisms(lit_rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    for row in lit_rows:
        if row["synthesis_type"] != "mechanism":
            continue
        text = row["theory_candidate"].lower()
        missing = [part for part in MECHANISM_PARTS if part not in text]
        if missing:
            errors.append(
                f"{row['synthesis_id']}: mechanism must include actor:, action:, "
                f"mediating_condition:, and outcome_link:; missing {', '.join(missing)}"
            )
    return errors


def validate_rivals(
    rival_rows: list[dict[str, str]],
    synthesis_ids: set[str],
    synthesis_rows: dict[str, dict[str, str]],
) -> list[str]:
    errors: list[str] = []
    targets_with_rivals = {row["target_synthesis_id"] for row in rival_rows}
    for row in rival_rows:
        rid = row["rival_id"]
        if row["target_synthesis_id"] not in synthesis_ids:
            errors.append(f"{rid}: target_synthesis_id not found in literature_theory_synthesis.csv")
        if error := route_enum_error("theory_rival_map", rid, row["next_skill_route"]):
            errors.append(f"invalid enum value: {error}")
        if row["status"] not in ALLOWED_WORKBENCH_STATUS:
            errors.append(f"{rid}: invalid status={row['status']}")
        for column in ("rival_claim", "explains_well", "explains_poorly", "discriminating_observation", "evidence_needed"):
            if is_vague(row[column], min_len=12):
                errors.append(f"{rid}: {column} is too vague for theory review")
        if contains_gate_only_term(row) and row["status"] == "ready_for_aiss":
            errors.append(f"{rid}: workflow-gated theory contribution decisions cannot be ready_for_aiss")
        if row["status"] == "ready_for_aiss":
            errors.append(f"{rid}: rival rows diagnose theory risk and must not be ready_for_aiss")

    for sid, lit_row in synthesis_rows.items():
        nontrivial = lit_row["synthesis_type"] in {"concept_cluster", "mechanism", "measurement_link", "scope_condition"}
        has_explicit_not_applicable = lit_row["rival_or_boundary"].startswith("not_applicable:")
        if nontrivial and not has_explicit_not_applicable and sid not in targets_with_rivals:
            errors.append(f"{sid}: nontrivial theory candidate needs a rival_map row or not_applicable:<reason>")
    return errors


def validate_scopes(scope_rows: list[dict[str, str]], synthesis_ids: set[str]) -> list[str]:
    errors: list[str] = []
    for row in scope_rows:
        sid = row["scope_id"]
        if row["target_synthesis_id"] not in synthesis_ids:
            errors.append(f"{sid}: target_synthesis_id not found in literature_theory_synthesis.csv")
        if error := route_enum_error("theory_scope_map", sid, row["next_skill_route"]):
            errors.append(f"invalid enum value: {error}")
        if row["status"] not in ALLOWED_WORKBENCH_STATUS:
            errors.append(f"{sid}: invalid status={row['status']}")
        for column in ("who_where_when", "scope_logic", "boundary_failure_mode", "observable_implication", "required_gate"):
            if is_vague(row[column], min_len=12):
                errors.append(f"{sid}: {column} is too vague for scope mapping")
        source_ids = parse_semicolon_list(row["source_ids"])
        if not source_ids and not row["source_ids"].startswith("not_applicable:"):
            errors.append(f"{sid}: source_ids must list source ids or not_applicable:<reason>")
        if contains_gate_only_term(row) and row["status"] == "ready_for_aiss":
            errors.append(f"{sid}: workflow-gated theory contribution decisions cannot be ready_for_aiss")
    return errors


def validate_evidence_markdown(workbench_dir: Path) -> list[str]:
    path = workbench_dir / "theory_evidence.md"
    if not path.exists():
        return [f"{path}: missing structured evidence markdown for compile_evidence.py reuse path"]
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        return [f"{path}: {exc}"]
    required_sections = ("## Paper Metadata", "## Concepts", "## Causal Relations", "## Bridges", "## Model")
    errors = [f"{path}: missing `{section}` section" for section in required_sections if section not in text]
    lowered = text.lower()
    forbidden = ("final theory prose", "theoretical contribution is established", "novelty is established")
    for phrase in forbidden:
        if phrase in lowered:
            errors.append(f"{path}: contains forbidden final-theory wording `{phrase}`")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workbench_dir", type=Path)
    args = parser.parse_args()
    workbench_dir = args.workbench_dir

    errors: list[str] = []
    if not workbench_dir.exists():
        return fail(f"{workbench_dir}: directory does not exist")

    for filename in REQUIRED_FILES.values():
        if not (workbench_dir / filename).exists():
            errors.append(f"{workbench_dir / filename}: missing required theory workbench sidecar")

    errors.extend(run_literature_validator(workbench_dir))
    lit_rows, lit_errors = load_sidecar(
        workbench_dir / REQUIRED_FILES["literature_theory_synthesis"],
        "literature_theory_synthesis",
        "synthesis_id",
    )
    rival_rows, rival_errors = load_sidecar(
        workbench_dir / REQUIRED_FILES["theory_rival_map"],
        "theory_rival_map",
        "rival_id",
    )
    scope_rows, scope_errors = load_sidecar(
        workbench_dir / REQUIRED_FILES["theory_scope_map"],
        "theory_scope_map",
        "scope_id",
    )
    errors.extend(lit_errors)
    errors.extend(rival_errors)
    errors.extend(scope_errors)

    synthesis_by_id = {row["synthesis_id"]: row for row in lit_rows}
    synthesis_ids = set(synthesis_by_id)
    errors.extend(validate_mechanisms(lit_rows))
    errors.extend(validate_rivals(rival_rows, synthesis_ids, synthesis_by_id))
    errors.extend(validate_scopes(scope_rows, synthesis_ids))
    errors.extend(validate_evidence_markdown(workbench_dir))

    if errors:
        return fail(f"{workbench_dir}: {'; '.join(errors)}")

    print(
        f"PASS {workbench_dir}: {len(lit_rows)} synthesis rows, "
        f"{len(rival_rows)} rival rows, {len(scope_rows)} scope rows valid"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
