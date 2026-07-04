#!/usr/bin/env python3
"""Validate study-design-builder MIDA declaration CSV sidecars."""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

def add_factory_contracts_to_path() -> None:
    script_path = Path(__file__).resolve()
    candidates: list[Path] = []
    if env_root := os.environ.get("AI4SS_SKILLS_ROOT"):
        candidates.append(Path(env_root))
    candidates.extend([*script_path.parents, Path("/Users/siyaozheng/Documents/ai4ss-skills")])
    for root in candidates:
        scripts_dir = root / "scripts"
        if (scripts_dir / "ai4ss_factory_contracts").exists():
            sys.path.insert(0, str(scripts_dir))
            return


add_factory_contracts_to_path()

from ai4ss_factory_contracts.sidecars import (
    AI4SS_CHECK_STATUS_WITH_FAIL,
    COMMENSURABILITY_STATUS,
    CSV_LOAD_EXCEPTIONS,
    VAGUE_VALUES,
    ai4ss_model_path_error,
    blank_required_cells,
    duplicate_values,
    exact_field_error,
    fail,
    is_aiss_id,
    is_vague,
    load_rows,
    sidecar_fields,
)
from ai4ss_factory_contracts.workflow import (
    MIDA_COMPONENTS,
    STUDY_TYPES,
    route_enum_error,
    status_route_errors,
)

EXPECTED_FIELDS = sidecar_fields("study_design_declaration")

REQUIRED_COMPONENTS = MIDA_COMPONENTS
ALLOWED_STUDY_TYPES = STUDY_TYPES
ALLOWED_SOURCES = {
    "author_supplied",
    "material_inferred",
    "literature_inferred",
    "agent_proposed",
    "unresolved",
}
ALLOWED_STATUS = {
    "declared",
    "needs_author_decision",
    "needs_data_check",
    "needs_literature_check",
    "needs_methods_review",
    "blocked",
}
ALLOWED_AI4SS_CHECK_STATUS = AI4SS_CHECK_STATUS_WITH_FAIL
ALLOWED_COMMENSURABILITY_STATUS = COMMENSURABILITY_STATUS
DATA_TERMS = re.compile(r"source|sample|sampling|measure|measurement|extract|link|merge|missing|corpus|data", re.I)
ANSWER_TERMS = re.compile(r"estimate|estimator|model|regression|code|coding|classif|synthesis|table|figure|compare|diagnostic|process", re.I)
CAUSAL_TERMS = re.compile(r"effect|estimand|comparison|outcome|treatment|exposure|population|unit|time|scale|对|影响|处理|结果", re.I)


def row_id(row: dict[str, str], index: int) -> str:
    return row.get("declaration_id") or f"row-{index + 1}"


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

    duplicates = duplicate_values(rows, "declaration_id")
    if duplicates:
        return fail(f"{args.csv_path}: duplicate declaration_id values: {', '.join(duplicates[:10])}")
    duplicate_mida_ids = duplicate_values(rows, "mida_id")
    if duplicate_mida_ids:
        return fail(f"{args.csv_path}: duplicate mida_id values: {', '.join(duplicate_mida_ids[:10])}")

    enum_errors: list[str] = []
    logic_errors: list[str] = []
    by_route: dict[str, list[dict[str, str]]] = defaultdict(list)
    study_type_by_route: dict[str, str] = {}

    for i, row in enumerate(rows):
        rid = row_id(row, i)
        by_route[row["route_id"]].append(row)
        if row["route_id"] in study_type_by_route and study_type_by_route[row["route_id"]] != row["study_type"]:
            logic_errors.append(f"{rid}: route_id has mixed study_type values")
        study_type_by_route[row["route_id"]] = row["study_type"]

        if row["study_type"] not in ALLOWED_STUDY_TYPES:
            enum_errors.append(f"{rid}:study_type={row['study_type']}")
        if row["mida_component"] not in REQUIRED_COMPONENTS:
            enum_errors.append(f"{rid}:mida_component={row['mida_component']}")
        if row["declaration_source"] not in ALLOWED_SOURCES:
            enum_errors.append(f"{rid}:declaration_source={row['declaration_source']}")
        if row["status"] not in ALLOWED_STATUS:
            enum_errors.append(f"{rid}:status={row['status']}")
        if error := route_enum_error("study_design_declaration", rid, row["next_skill_route"]):
            enum_errors.append(error)
        if row["ai4ss_check_status"] not in ALLOWED_AI4SS_CHECK_STATUS:
            enum_errors.append(f"{rid}:ai4ss_check_status={row['ai4ss_check_status']}")
        if row["commensurability_status"] not in ALLOWED_COMMENSURABILITY_STATUS:
            enum_errors.append(f"{rid}:commensurability_status={row['commensurability_status']}")

        if not is_aiss_id(row["mida_id"]):
            logic_errors.append(f"{rid}: mida_id must be a stable .aiss mida declaration id")
        if is_vague(row["declaration_text"], min_len=12):
            logic_errors.append(f"{rid}: declaration_text is too vague")
        if is_vague(row["interpretation_boundary"], min_len=12):
            logic_errors.append(f"{rid}: interpretation_boundary is too vague")
        if row["ai4ss_model_path"].startswith("not_applicable:"):
            if row["study_type"] in {"causal", "theory_mapping", "mixed_methods"}:
                logic_errors.append(f"{rid}: {row['study_type']} rows require an ai4ss_model_path or explicit redesign")
        elif error := ai4ss_model_path_error(row["ai4ss_model_path"], rid):
            logic_errors.append(error)
        if row["ai4ss_check_status"] == "fail":
            logic_errors.append(f"{rid}: ai4ss_check_status=fail is not a valid handoff")
        if row["bridge_id"].lower() not in VAGUE_VALUES and not row["bridge_id"].startswith("not_applicable:"):
            if row["commensurability_status"] in {"not_applicable", "unchecked"}:
                logic_errors.append(f"{rid}: bridge_id requires strong weak or mixed commensurability_status")
        logic_errors.extend(
            status_route_errors("study_design_declaration", row["status"], row["next_skill_route"], rid)
        )

    for route_id, route_rows in by_route.items():
        components = [row["mida_component"] for row in route_rows]
        missing = sorted(REQUIRED_COMPONENTS - set(components))
        duplicates_components = sorted({component for component in components if components.count(component) > 1})
        if missing:
            logic_errors.append(f"{route_id}: missing MIDA components: {', '.join(missing)}")
        if duplicates_components:
            logic_errors.append(f"{route_id}: duplicate MIDA components: {', '.join(duplicates_components)}")

        rows_by_component = {row["mida_component"]: row for row in route_rows}
        inquiry = rows_by_component.get("inquiry")
        if inquiry and study_type_by_route[route_id] == "causal" and not CAUSAL_TERMS.search(inquiry["declaration_text"]):
            logic_errors.append(f"{route_id}: causal inquiry must state estimand or target comparison details")
        data_strategy = rows_by_component.get("data_strategy")
        if data_strategy and not DATA_TERMS.search(data_strategy["declaration_text"]):
            logic_errors.append(f"{route_id}: data_strategy must name source/sample/measurement/linkage/missingness")
        answer_strategy = rows_by_component.get("answer_strategy")
        if answer_strategy and not ANSWER_TERMS.search(answer_strategy["declaration_text"]):
            logic_errors.append(f"{route_id}: answer_strategy must name estimator/coding/synthesis/output procedure")
        diagnose = rows_by_component.get("diagnose")
        if diagnose and is_vague(diagnose["diagnosand_or_gate"], min_len=12):
            logic_errors.append(f"{route_id}: diagnose row needs a concrete diagnosand_or_gate")
        redesign = rows_by_component.get("redesign")
        if redesign and is_vague(redesign["redesign_option"], min_len=12):
            logic_errors.append(f"{route_id}: redesign row needs a concrete redesign_option")

    if enum_errors:
        return fail(f"{args.csv_path}: invalid enum values: {', '.join(enum_errors[:10])}")
    if logic_errors:
        return fail(f"{args.csv_path}: declaration logic errors: {', '.join(logic_errors[:10])}")

    print(f"PASS {args.csv_path}: {len(rows)} MIDA declaration rows valid")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
