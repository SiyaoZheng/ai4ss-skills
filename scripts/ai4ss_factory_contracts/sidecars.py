"""Shared sidecar-schema interface for AI4SS factory validators."""

from __future__ import annotations

import csv
import re
from pathlib import Path


VAGUE_VALUES = {"none", "n/a", "not_applicable", "not applicable", "unknown", "tbd"}
AI4SS_CHECK_STATUS = {"pass", "warn", "not_run", "not_applicable"}
AI4SS_CHECK_STATUS_WITH_FAIL = AI4SS_CHECK_STATUS | {"fail"}
COMMENSURABILITY_STATUS = {"strong", "weak", "unchecked", "mixed", "not_applicable"}
AISS_ID_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*(?:\.[A-Za-z_][A-Za-z0-9_-]*)+$")
CSV_LOAD_EXCEPTIONS = (OSError, UnicodeDecodeError, csv.Error, ValueError)

SIDECAR_FIELD_GROUPS: dict[str, tuple[str, ...]] = {
    "route_identity": ("route_id",),
    "design_source": ("route_id", "design_source", "target_inquiry"),
    "model_link": (
        "ai4ss_model_path",
        "model_id",
        "concept_id",
        "causal_id",
        "bridge_id",
        "ai4ss_check_status",
    ),
    "core_handoff": (
        "route_id",
        "design_source",
        "target_inquiry",
        "ai4ss_model_path",
        "model_id",
        "concept_id",
        "causal_id",
        "bridge_id",
        "ai4ss_check_status",
        "next_skill_route",
    ),
}


SIDECAR_FIELDS: dict[str, tuple[str, ...]] = {
    "research_routes": (
        "route_id",
        "route_decl_id",
        "working_title",
        "research_question",
        "phenomenon",
        "model_scope",
        "candidate_inquiry",
        "possible_data_strategy",
        "possible_answer_strategy",
        "study_type",
        "unit_of_analysis",
        "materials_available",
        "materials_gap",
        "first_action",
        "expected_first_output",
        "failure_signal",
        "feasibility_status",
        "stop_reason",
        "researcher_decision_needed",
        "next_skill_route",
    ),
    "study_design_declaration": (
        "declaration_id",
        "mida_id",
        "route_id",
        "study_type",
        "mida_component",
        "declaration_text",
        "declaration_source",
        "status",
        "evidence_source",
        "diagnosand_or_gate",
        "redesign_option",
        "interpretation_boundary",
        "author_decision_needed",
        "ai4ss_model_path",
        "model_id",
        "concept_id",
        "causal_id",
        "bridge_id",
        "ai4ss_check_status",
        "commensurability_status",
        "next_skill_route",
    ),
    "design_decisions": (
        "decision_id",
        "decision_decl_id",
        "route_id",
        "mida_component",
        "design_component",
        "current_choice",
        "choice_source",
        "status",
        "evidence_needed",
        "risk_if_wrong",
        "author_decision_needed",
        "downstream_skill_route",
    ),
    "sample_flow": (
        "route_id",
        "design_source",
        "target_inquiry",
        "step",
        "input_path",
        "output_path",
        "n_before",
        "n_after",
        "units_before",
        "units_after",
        "years_before",
        "years_after",
        "reason",
        "check_status",
        "notes",
        "ai4ss_model_path",
        "model_id",
        "concept_id",
        "causal_id",
        "bridge_id",
        "ai4ss_check_status",
    ),
    "merge_audit": (
        "route_id",
        "design_source",
        "target_inquiry",
        "merge_name",
        "left_path",
        "right_path",
        "keys",
        "left_rows",
        "right_rows",
        "matched_rows",
        "left_only_rows",
        "right_only_rows",
        "duplicate_key_rows",
        "action",
        "review_path",
        "ai4ss_model_path",
        "model_id",
        "concept_id",
        "causal_id",
        "bridge_id",
        "ai4ss_check_status",
    ),
    "variable_provenance": (
        "route_id",
        "design_source",
        "target_inquiry",
        "variable",
        "source_variables",
        "rule",
        "script_path",
        "validation",
        "status",
        "ai4ss_model_path",
        "model_id",
        "concept_id",
        "causal_id",
        "bridge_id",
        "ai4ss_check_status",
    ),
    "literature_discovery": (
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
    ),
    "literature_matrix": (
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
    ),
    "analysis_readiness": (
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
    ),
    "analysis_manifest": (
        "run_id",
        "route_id",
        "design_source",
        "target_inquiry",
        "data_source",
        "script_path",
        "output_path",
        "output_type",
        "model_or_operation",
        "sample_note",
        "readiness_check_path",
        "readiness_status",
        "status",
        "validation_command",
        "interpretation_boundary",
        "ai4ss_model_path",
        "model_id",
        "concept_id",
        "causal_id",
        "bridge_id",
        "ai4ss_check_status",
        "next_skill_route",
    ),
    "methods_issue_table": (
        "route_id",
        "design_source",
        "target_inquiry",
        "mida_component",
        "severity",
        "issue",
        "evidence",
        "why_it_matters",
        "next_action",
        "status",
        "ai4ss_model_path",
        "model_id",
        "concept_id",
        "causal_id",
        "bridge_id",
        "ai4ss_check_status",
        "commensurability_status",
    ),
    "claim_ledger": (
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
    ),
    "slide_map": (
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
    ),
    "revision_matrix": (
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
    ),
}


def sidecar_fields(name: str) -> list[str]:
    try:
        return list(SIDECAR_FIELDS[name])
    except KeyError as exc:
        raise KeyError(f"unknown AI4SS sidecar: {name}") from exc


def sidecar_field_group(name: str) -> list[str]:
    try:
        return list(SIDECAR_FIELD_GROUPS[name])
    except KeyError as exc:
        raise KeyError(f"unknown AI4SS sidecar field group: {name}") from exc


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


def exact_field_error(csv_path: Path, fields: list[str], expected: list[str]) -> str | None:
    if fields == expected:
        return None
    return f"{csv_path}: expected exact columns {', '.join(expected)}; got {', '.join(fields)}"


def blank_required_cells(
    rows: list[dict[str, str]],
    fields: list[str],
    row_label,
) -> list[str]:
    return [
        f"{row_label(row, i)}:{column}"
        for i, row in enumerate(rows)
        for column in fields
        if not row.get(column)
    ]


def duplicate_values(rows: list[dict[str, str]], field: str) -> list[str]:
    values = [row[field] for row in rows]
    return sorted({value for value in values if values.count(value) > 1})


def is_vague(value: str, *, min_len: int = 10) -> bool:
    value = value.strip()
    return value.lower() in VAGUE_VALUES or len(value) < min_len


def parse_semicolon_list(value: str) -> list[str]:
    if value.strip().lower() in {"", "none", "not_applicable"}:
        return []
    if value.startswith("not_applicable:"):
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


def is_nonnegative_integer(value: str) -> bool:
    return value.isdigit()


def parse_nonnegative_int(
    value: str,
    field: str,
    row_label: str,
    *,
    allow_not_applicable: bool = False,
) -> tuple[int | None, str | None]:
    if allow_not_applicable and value.startswith("not_applicable:"):
        return None, None
    try:
        parsed = int(value)
    except ValueError:
        return None, f"{row_label}:{field} must be a nonnegative integer"
    if parsed < 0:
        return None, f"{row_label}:{field} must be a nonnegative integer"
    return parsed, None


def is_aiss_id(value: str) -> bool:
    return bool(AISS_ID_RE.match(value))


def is_aiss_id_or_not_created(value: str) -> bool:
    return is_aiss_id(value) or value.startswith("not_created:")


def not_applicable(value: str) -> bool:
    return value.startswith("not_applicable:")


def suffix_path_error(value: str, suffix: str, row_label: str, field: str) -> str | None:
    if not_applicable(value):
        return None
    if not value.endswith(suffix):
        return f"{row_label}: {field} must end with {suffix}"
    return None


def ai4ss_model_path_error(value: str, row_label: str, field: str = "ai4ss_model_path") -> str | None:
    return suffix_path_error(value, ".aiss", row_label, field)


def resolve_existing_path(path_text: str, csv_path: Path, repo_root: Path) -> Path | None:
    if not_applicable(path_text):
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
